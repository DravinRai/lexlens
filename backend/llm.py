"""
LexLens LLM Client — Gemini Wrapper

All LLM calls go through this module. Handles:
- Client initialization with API key from env (singleton, not re-created per call)
- System prompt construction per document type
- Injecting jurisdiction reference data (or the "no data" signal)
- Structured output parsing (JSON extraction from responses)
- Response caching to avoid redundant API calls
- Async API calls to avoid blocking the event loop
"""

import asyncio
import hashlib
import json
import logging
import os
import re
from typing import Any

from google import genai
from google.genai import types

try:
    from .prompts import (
        GLOBAL_SYSTEM_INSTRUCTION,
        CLASSIFY_PROMPT,
        EXTRACT_AND_RISK_PROMPT,
        TIER_B_PROMPT,
        TIER_B_NO_DATA_RESPONSE,
        CHECKLIST_PROMPT,
        COMPARE_PROMPT,
        QA_SYSTEM_PROMPT,
        QA_JURISDICTION_SECTION,
        QA_NO_JURISDICTION_SECTION,
    )
    from .jurisdiction import format_reference_for_prompt
    from .taxonomy import format_taxonomy_for_prompt
except ImportError:
    from prompts import (
        GLOBAL_SYSTEM_INSTRUCTION,
        CLASSIFY_PROMPT,
        EXTRACT_AND_RISK_PROMPT,
        TIER_B_PROMPT,
        TIER_B_NO_DATA_RESPONSE,
        CHECKLIST_PROMPT,
        COMPARE_PROMPT,
        QA_SYSTEM_PROMPT,
        QA_JURISDICTION_SECTION,
        QA_NO_JURISDICTION_SECTION,
    )
    from jurisdiction import format_reference_for_prompt
    from taxonomy import format_taxonomy_for_prompt

logger = logging.getLogger(__name__)

# ─── Singleton Client ──────────────────────────────────────
# Avoids creating a new genai.Client() on every LLM call.
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Get or create a singleton Gemini client."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        _client = genai.Client(api_key=api_key)
    return _client


def _get_model() -> str:
    """Get the configured model name."""
    return os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


# ─── Response Cache ────────────────────────────────────────
# Simple hash-based cache to avoid duplicate LLM calls for the same input.
# Bounded to prevent unbounded memory growth.
_response_cache: dict[str, Any] = {}
_CACHE_MAX_SIZE = 50


def _cache_key(prefix: str, *args: str) -> str:
    """Generate a deterministic cache key from prefix + content hashes."""
    hasher = hashlib.sha256()
    hasher.update(prefix.encode())
    for arg in args:
        hasher.update(arg.encode())
    return hasher.hexdigest()


def _cache_get(key: str) -> Any | None:
    """Retrieve a cached response, or None if not found."""
    return _response_cache.get(key)


def _cache_set(key: str, value: Any) -> None:
    """Store a response in the cache, evicting oldest if full."""
    if len(_response_cache) >= _CACHE_MAX_SIZE:
        # Evict the first (oldest) entry
        oldest_key = next(iter(_response_cache))
        del _response_cache[oldest_key]
    _response_cache[key] = value


def clear_cache() -> None:
    """Clear the entire response cache (e.g., on session cleanup)."""
    _response_cache.clear()


# ─── JSON Extraction ───────────────────────────────────────

def _extract_json(text: str) -> dict | list:
    """Extract JSON from an LLM response that might contain markdown fences."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding JSON object/array boundaries
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]}...")


# ─── Core LLM Call (async, with retry) ─────────────────────

async def _generate_with_retry(client, model, contents, config):
    """
    Call the Gemini API with automatic retry on transient failures.

    Uses the async API (client.aio.models.generate_content) to avoid
    blocking the FastAPI event loop during LLM inference.
    """
    for attempt in range(3):
        try:
            return await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as e:
            if attempt < 2:
                logger.warning("LLM API error (attempt %d/3): %s", attempt + 1, e)
                await asyncio.sleep(2)
            else:
                raise


# ─── Public API ────────────────────────────────────────────

async def classify_document(document_text: str) -> dict[str, Any]:
    """
    Classify document type using Gemini.

    Returns: {"doc_type": str, "confidence": str, "reasoning": str}

    Results are cached by document content hash to avoid re-classifying
    the same document.
    """
    # Use first ~4000 chars for classification (enough to identify type)
    truncated = document_text[:4000]

    # Check cache
    key = _cache_key("classify", truncated)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    client = _get_client()
    prompt = CLASSIFY_PROMPT.format(document_text=truncated)

    response = await _generate_with_retry(
        client=client,
        model=_get_model(),
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
            temperature=0.1,
        ),
    )

    result = _extract_json(response.text)
    _cache_set(key, result)
    return result


async def extract_and_risk_tag(
    document_text: str, taxonomy: dict
) -> dict[str, Any]:
    """
    Extract clauses from document and assign risk tags.

    Returns Tier A data: clauses, summary, dates, parties.

    Results are cached by (document content + taxonomy) hash.
    """
    taxonomy_text = format_taxonomy_for_prompt(taxonomy)

    # Check cache
    key = _cache_key("extract", document_text, taxonomy_text)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    client = _get_client()
    prompt = EXTRACT_AND_RISK_PROMPT.format(
        taxonomy_text=taxonomy_text,
        document_text=document_text,
    )

    response = await _generate_with_retry(
        client=client,
        model=_get_model(),
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
            temperature=0.2,
        ),
    )

    result = _extract_json(response.text)
    _cache_set(key, result)
    return result


async def generate_tier_b(
    jurisdiction_ref: dict | None,
    jurisdiction_name: str,
    clauses_json: str,
) -> dict[str, Any]:
    """
    Generate Tier B jurisdictional context.

    If jurisdiction_ref is None, returns the honest fallback response
    (no reference data available) — this is a real branch, not a disclaimer.
    """
    if jurisdiction_ref is None:
        return {
            **TIER_B_NO_DATA_RESPONSE,
            "jurisdiction": jurisdiction_name,
        }

    client = _get_client()
    jurisdiction_text = format_reference_for_prompt(jurisdiction_ref)

    prompt = TIER_B_PROMPT.format(
        jurisdiction_text=jurisdiction_text,
        clauses_json=clauses_json,
        jurisdiction_name=jurisdiction_name,
    )

    response = await _generate_with_retry(
        client=client,
        model=_get_model(),
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
            temperature=0.2,
        ),
    )

    return _extract_json(response.text)


async def generate_checklist(
    doc_type: str,
    jurisdiction: str,
    jurisdiction_ref: dict | None,
    clauses_json: str,
) -> dict[str, Any]:
    """
    Generate tailored next-steps checklist and questions-for-lawyer list.

    Adjusted by document type AND jurisdiction availability.
    """
    client = _get_client()

    if jurisdiction_ref is not None:
        jurisdiction_context = (
            f"Jurisdiction: {jurisdiction} (verified reference data available)\n"
            f"Reference data summary:\n{format_reference_for_prompt(jurisdiction_ref)}"
        )
    else:
        jurisdiction_context = (
            f"Jurisdiction: {jurisdiction} (NO verified reference data available — "
            f"include 'Confirm which jurisdiction's law governs this document' as a priority item)"
        )

    prompt = CHECKLIST_PROMPT.format(
        doc_type=doc_type,
        jurisdiction=jurisdiction,
        jurisdiction_context=jurisdiction_context,
        clauses_json=clauses_json,
    )

    response = await _generate_with_retry(
        client=client,
        model=_get_model(),
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
            temperature=0.3,
        ),
    )

    return _extract_json(response.text)


async def run_full_analysis(
    document_text: str,
    taxonomy: dict,
    jurisdiction_ref: dict | None,
    jurisdiction_name: str,
    doc_type: str,
) -> dict[str, Any]:
    """
    Run the complete analysis pipeline: Tier A → (Tier B + Checklist in parallel).

    This replaces three sequential awaits in the /api/analyze endpoint with
    a two-phase approach:
    1. Tier A (extract_and_risk_tag) runs first — its output feeds into phase 2.
    2. Tier B and Checklist run concurrently via asyncio.gather since they're
       independent of each other (both only need Tier A output).

    Net effect: ~33% wall-clock reduction on the analysis endpoint.
    """
    # Phase 1: Tier A (must complete first — Tier B and Checklist need its output)
    tier_a = await extract_and_risk_tag(document_text, taxonomy)
    clauses_json = json.dumps(tier_a.get("clauses", []), indent=2)

    # Phase 2: Tier B + Checklist in parallel
    tier_b_task = generate_tier_b(
        jurisdiction_ref=jurisdiction_ref,
        jurisdiction_name=jurisdiction_name,
        clauses_json=clauses_json,
    )
    checklist_task = generate_checklist(
        doc_type=doc_type,
        jurisdiction=jurisdiction_name,
        jurisdiction_ref=jurisdiction_ref,
        clauses_json=clauses_json,
    )
    tier_b, checklist = await asyncio.gather(tier_b_task, checklist_task)

    return {
        "tier_a": tier_a,
        "tier_b": tier_b,
        "checklist": checklist,
    }


async def compare_documents(
    doc_a_text: str,
    doc_b_text: str,
    taxonomy: dict,
) -> dict[str, Any]:
    """
    Compare two documents clause-by-clause.

    Returns material differences and party-favor indicators.
    """
    client = _get_client()
    taxonomy_text = format_taxonomy_for_prompt(taxonomy)

    prompt = COMPARE_PROMPT.format(
        document_a_text=doc_a_text,
        document_b_text=doc_b_text,
        taxonomy_text=taxonomy_text,
    )

    response = await _generate_with_retry(
        client=client,
        model=_get_model(),
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
            temperature=0.2,
        ),
    )

    return _extract_json(response.text)


def _select_relevant_chunks(
    question: str,
    chunks: list[dict],
    max_chunks: int = 5,
) -> str:
    """
    Select the most relevant chunks for a Q&A question using keyword overlap.

    This is a lightweight retrieval step that avoids sending the entire document
    on every chat message. For documents within the context window, this reduces
    prompt token usage significantly while preserving answer quality.
    """
    if not chunks:
        return ""

    # If the document is small enough (≤ max_chunks), use all chunks
    if len(chunks) <= max_chunks:
        return "\n\n".join(c["text"] for c in chunks)

    # Simple keyword-overlap scoring
    question_words = set(question.lower().split())
    scored = []
    for chunk in chunks:
        chunk_words = set(chunk["text"].lower().split())
        overlap = len(question_words & chunk_words)
        scored.append((overlap, chunk["index"], chunk["text"]))

    # Sort by relevance (overlap), break ties by position (earlier first)
    scored.sort(key=lambda x: (-x[0], x[1]))
    selected = scored[:max_chunks]
    # Re-sort by original position for coherent reading order
    selected.sort(key=lambda x: x[1])

    return "\n\n".join(text for _, _, text in selected)


async def grounded_qa(
    question: str,
    document_text: str,
    jurisdiction_ref: dict | None,
    chat_history: list[dict],
    chunks: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Answer a question grounded ONLY in the uploaded document and
    (if available) the jurisdictional reference data.

    Never draws on general model knowledge about law.
    Cites sections. Refuses definitive legal opinions.

    When chunks are provided, uses keyword-based retrieval to select
    relevant chunks instead of sending the full document text every time.
    """
    client = _get_client()

    # Use chunk-based retrieval if chunks are available
    if chunks:
        context_text = _select_relevant_chunks(question, chunks)
    else:
        context_text = document_text

    # Build jurisdiction section
    if jurisdiction_ref is not None:
        jurisdiction_section = QA_JURISDICTION_SECTION.format(
            jurisdiction_text=format_reference_for_prompt(jurisdiction_ref)
        )
    else:
        jurisdiction_section = QA_NO_JURISDICTION_SECTION

    # Format chat history (keep last 10 messages for context)
    history_str = ""
    for msg in chat_history[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_str += f"{role.upper()}: {content}\n"

    system_prompt = QA_SYSTEM_PROMPT.format(
        document_text=context_text,
        jurisdiction_section=jurisdiction_section,
        chat_history=history_str,
    )

    response = await _generate_with_retry(
        client=client,
        model=_get_model(),
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
        ),
    )

    return {
        "answer": response.text,
        "grounded": True,
    }
