"""
LexLens — FastAPI Application

Main entry point for the backend API. Handles:
- Document upload and text extraction (in-memory only, no persistence)
- Document type classification via Gemini
- Clause extraction, risk tagging, and Tier A/B analysis
- Jurisdiction-aware checklist and Q&A
- Document comparison
"""

import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .session_store import SessionStore
    from .document_processor import extract_text, chunk_text, validate_file
    from .jurisdiction import (
        load_reference,
        normalize_region_code,
        get_supported_jurisdictions,
    )
    from .taxonomy import load_taxonomy
    from . import llm
except ImportError:
    from session_store import SessionStore
    from document_processor import extract_text, chunk_text, validate_file
    from jurisdiction import (
        load_reference,
        normalize_region_code,
        get_supported_jurisdictions,
    )
    from taxonomy import load_taxonomy
    import llm

load_dotenv()

app = FastAPI(
    title="LexLens API",
    description="GenAI Legal Document Assistant — informs and assists, never replaces a licensed attorney.",
    version="1.0.0",
)

# Build CORS allowed origins list
_cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
# Allow the deployed frontend origin (set via FRONTEND_URL env var on Vercel)
_frontend_url = os.getenv("FRONTEND_URL")
if _frontend_url:
    _cors_origins.append(_frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store — no disk persistence (privacy by design)
session_ttl_str = os.getenv("SESSION_TTL")
session_ttl = int(session_ttl_str) if session_ttl_str else 1800

max_upload_str = os.getenv("MAX_UPLOAD_SIZE")
max_upload_size = int(max_upload_str) if max_upload_str else 2 * 1024 * 1024

sessions = SessionStore(ttl_seconds=session_ttl)


# ─── Request/Response Models ───────────────────────────────

class JurisdictionRequest(BaseModel):
    session_id: str
    country: str
    state: str = ""


class AnalyzeRequest(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class CompareRequest(BaseModel):
    session_id: str


# ─── Health Check ──────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "active_sessions": sessions.active_count(),
        "disclaimer": "LexLens is an informational tool, not a substitute for licensed legal advice.",
    }


# ─── Upload ────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    slot: str = Form(default="a"),  # "a" for primary doc, "b" for comparison doc
):
    """
    Upload a document for analysis. Extracts text in memory — no disk persistence.

    slot="a" for the primary document, slot="b" for a comparison document.
    """
    file_bytes = await file.read()

    # Validate
    error = validate_file(file.filename, len(file_bytes), max_upload_size)
    if error:
        raise HTTPException(status_code=400, detail=error)

    # Extract text
    try:
        text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text content could be extracted from this file.")

    chunks = chunk_text(text)

    # Create or reuse session
    # For slot "a", always create new session
    # For slot "b", expect session_id in form data — but for simplicity,
    # we'll handle it via a separate endpoint
    session_id = sessions.create_session()

    if slot == "a":
        sessions.update(session_id, text=text, chunks=chunks)
    else:
        sessions.update(session_id, text_b=text, chunks_b=chunks)

    return {
        "session_id": session_id,
        "filename": file.filename,
        "text_length": len(text),
        "chunk_count": len(chunks),
        "slot": slot,
    }


@app.post("/api/upload-compare")
async def upload_comparison_document(
    file: UploadFile = File(...),
    session_id: str = Form(...),
):
    """Upload a second document for comparison into an existing session."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    file_bytes = await file.read()
    error = validate_file(file.filename, len(file_bytes), max_upload_size)
    if error:
        raise HTTPException(status_code=400, detail=error)

    try:
        text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text content could be extracted from this file.")

    chunks = chunk_text(text)
    sessions.update(session_id, text_b=text, chunks_b=chunks)

    return {
        "session_id": session_id,
        "filename": file.filename,
        "text_length": len(text),
        "chunk_count": len(chunks),
        "slot": "b",
    }


# ─── Classification ────────────────────────────────────────

@app.post("/api/classify")
async def classify_document(request: AnalyzeRequest):
    """Classify the uploaded document's type via LLM."""
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if not session["text"]:
        raise HTTPException(status_code=400, detail="No document uploaded in this session.")

    result = await llm.classify_document(session["text"])
    sessions.update(request.session_id, doc_type=result.get("doc_type", "other"))

    return result


# ─── Jurisdiction Selection ─────────────────────────────────

@app.post("/api/set-jurisdiction")
async def set_jurisdiction(request: JurisdictionRequest):
    """
    Set the jurisdiction for analysis. This is a FIRST-CLASS step —
    it determines whether Tier B data is available and shapes all
    subsequent output.
    """
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    # Build region code from country + state
    if request.state:
        jurisdiction_input = f"{request.country}-{request.state}"
    else:
        jurisdiction_input = request.country

    region_code = normalize_region_code(jurisdiction_input)
    doc_type = session.get("doc_type", "other")

    # Load jurisdiction reference — None is a valid, intentional result
    ref_data = load_reference(region_code, doc_type)

    sessions.update(
        request.session_id,
        jurisdiction=jurisdiction_input,
        jurisdiction_ref=ref_data,
    )

    return {
        "region_code": region_code,
        "doc_type": doc_type,
        "has_reference_data": ref_data is not None,
        "jurisdiction_display": jurisdiction_input,
        "message": (
            f"Verified reference data loaded for {jurisdiction_input} ({doc_type})."
            if ref_data
            else f"No verified reference data available for {jurisdiction_input} ({doc_type}). "
            f"Tier A analysis (document-grounded facts) will still be provided, but "
            f"jurisdiction-specific context cannot be reliably generated."
        ),
    }


# ─── Full Analysis ──────────────────────────────────────────

@app.post("/api/analyze")
async def analyze_document(request: AnalyzeRequest):
    """
    Full document analysis: clause extraction, risk tagging,
    Tier A summary, Tier B jurisdictional context, and checklist.

    Requires prior classification and jurisdiction selection.
    """
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if not session["text"]:
        raise HTTPException(status_code=400, detail="No document uploaded.")
    if not session["doc_type"]:
        raise HTTPException(status_code=400, detail="Document not yet classified. Call /api/classify first.")

    doc_type = session["doc_type"]
    jurisdiction = session.get("jurisdiction", "Unknown")
    jurisdiction_ref = session.get("jurisdiction_ref")

    # Load taxonomy for this document type
    taxonomy = load_taxonomy(doc_type)

    # Tier A: Extract clauses and risk-tag them
    tier_a = await llm.extract_and_risk_tag(session["text"], taxonomy)

    # Tier B: Jurisdictional context (real branch: ref data or honest fallback)
    tier_b = await llm.generate_tier_b(
        jurisdiction_ref=jurisdiction_ref,
        jurisdiction_name=jurisdiction,
        clauses_json=json.dumps(tier_a.get("clauses", []), indent=2),
    )

    # Checklist: tailored by doc type + jurisdiction availability
    checklist = await llm.generate_checklist(
        doc_type=doc_type,
        jurisdiction=jurisdiction,
        jurisdiction_ref=jurisdiction_ref,
        clauses_json=json.dumps(tier_a.get("clauses", []), indent=2),
    )

    # Store analysis in session for Q&A grounding
    analysis = {
        "tier_a": tier_a,
        "tier_b": tier_b,
        "checklist": checklist,
    }
    sessions.update(request.session_id, analysis=analysis)

    return analysis


# ─── Document Comparison ────────────────────────────────────

@app.post("/api/compare")
async def compare_documents(request: CompareRequest):
    """
    Compare two uploaded documents clause-by-clause.
    Requires both documents uploaded in the same session.
    """
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if not session["text"]:
        raise HTTPException(status_code=400, detail="Primary document (A) not uploaded.")
    if not session["text_b"]:
        raise HTTPException(status_code=400, detail="Comparison document (B) not uploaded. Use /api/upload-compare.")

    doc_type = session.get("doc_type", "other")
    taxonomy = load_taxonomy(doc_type)

    result = await llm.compare_documents(
        doc_a_text=session["text"],
        doc_b_text=session["text_b"],
        taxonomy=taxonomy,
    )

    return result


# ─── Grounded Q&A Chat ─────────────────────────────────────

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Grounded Q&A: answers ONLY from document + jurisdiction reference.
    Never from general model knowledge. Cites sections. Refuses legal opinions.
    """
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if not session["text"]:
        raise HTTPException(status_code=400, detail="No document uploaded.")

    chat_history = session.get("chat_history", [])

    result = await llm.grounded_qa(
        question=request.message,
        document_text=session["text"],
        jurisdiction_ref=session.get("jurisdiction_ref"),
        chat_history=chat_history,
    )

    # Update chat history in session
    chat_history.append({"role": "user", "content": request.message})
    chat_history.append({"role": "assistant", "content": result["answer"]})
    sessions.update(request.session_id, chat_history=chat_history)

    return result


# ─── Metadata / Utility ────────────────────────────────────

@app.get("/api/supported-jurisdictions")
async def supported_jurisdictions():
    """Return list of (region, doc_type) pairs with verified reference data."""
    return {
        "supported": get_supported_jurisdictions(),
        "note": "Only these jurisdiction/document-type combinations have curated reference data. "
        "All others will receive Tier A (document-grounded) analysis only.",
    }


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Explicitly delete a session and all associated in-memory data."""
    sessions.delete(session_id)
    return {"status": "deleted"}
