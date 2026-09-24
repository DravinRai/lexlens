# ⚖️ LexLens — AI-Powered Legal Document Assistant

> **Hackathon Vertical:** AI for Legal Assistance & Access
>
> LexLens informs and assists — it **never claims to replace a licensed attorney**, and it never asserts jurisdiction-specific legal conclusions with more confidence than it can actually back up.

---

## What It Does

Upload a legal document (lease, employment contract, NDA, terms of service, freelance agreement) and LexLens will:

1. **Classify** the document type automatically
2. **Ask for your jurisdiction** (country + state/province) — a first-class step, not an afterthought
3. **Analyze the document** in two clearly separated tiers:
   - **Tier A (Document Facts):** What the document actually says — plain-language summary, extracted clauses, obligations, deadlines, parties
   - **Tier B (Jurisdictional Context):** How this region typically treats these kinds of clauses — sourced **only** from curated reference files, never invented
4. **Risk-tag each clause** (low/medium/high) with a rationale — using icons + text labels, not color alone
5. **Generate a tailored checklist** of next steps and "questions to ask a lawyer"
6. **Support document comparison** — upload two documents and see clause-by-clause differences with party-favor indicators
7. **Provide grounded Q&A chat** — answers only from the document and reference data, cites sections, refuses legal opinions

---

## Architecture

```
┌─────────────────────────────────┐      ┌────────────────────┐
│  Frontend (React + Vite)        │ ←──→ │  Backend (FastAPI)  │
│  - Upload, Jurisdiction Select  │      │  - Session Store    │
│  - Tier A / Tier B Display      │      │  - Doc Processor    │
│  - Risk Cards, Checklist        │      │  - Gemini LLM       │
│  - Chat, Compare Views          │      │  - Jurisdiction Mgr  │
│  - Disclaimers (global + Tier B)│      │  - Taxonomy Loader  │
└─────────────────────────────────┘      └────────┬───────────┘
                                                  │
                                    ┌─────────────┴────────────┐
                                    │  Curated Data (JSON)      │
                                    │  prompts/taxonomies/*.json │
                                    │  prompts/jurisdictions/    │
                                    │    IN-lease.json           │
                                    │    US-CA-lease.json        │
                                    └───────────────────────────┘
```

### Context-Aware Branching: Document Type × Jurisdiction

This is the core design pattern. When a user uploads a document:

```
Upload → Classify doc type → Select jurisdiction
                                    │
                    ┌───────────────┴───────────────┐
                    │ Resolve jurisdiction file:     │
                    │ prompts/jurisdictions/          │
                    │   {region_code}-{doc_type}.json │
                    └───────────────┬───────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                           │
        FILE EXISTS                                 FILE MISSING
              │                                           │
    Load concepts[]                          Set jurisdiction_supported = false
    Inject into Tier B prompt                Tier B → honest fallback message:
    Generate grounded context                "I don't have verified reference
                                             data for this region"
              │                                           │
              └─────────────────────┬─────────────────────┘
                                    │
                    Load taxonomy for doc type
                    Extract clauses + risk-tag
                    Generate checklist (adjusted)
```

**Example — supported jurisdiction:**
- Document: lease | Jurisdiction: India
- Loads `IN-lease.json` → Tier B shows security deposit norms, notice periods, MTA guidance
- Checklist includes India-specific verification items

**Example — unsupported jurisdiction:**
- Document: lease | Jurisdiction: Germany
- No `DE-lease.json` exists → Tier B shows: "I don't have verified reference data for this region for this document type"
- Checklist adds: "Confirm which jurisdiction's law governs this document"

---

## Supported Jurisdictions & Document Types

### Jurisdictions with Reference Data

| Region | Document Type | File |
|--------|---------------|------|
| India | Lease | `prompts/jurisdictions/IN-lease.json` |
| US — California | Lease | `prompts/jurisdictions/US-CA-lease.json` |

### Document Types with Taxonomies

| Type | Taxonomy File |
|------|---------------|
| Lease | `prompts/taxonomies/lease.json` |
| Employment | `prompts/taxonomies/employment.json` |
| NDA | `prompts/taxonomies/nda.json` |
| Terms of Service | `prompts/taxonomies/tos.json` |
| Freelance/Services | `prompts/taxonomies/freelance.json` |
| Other (fallback) | `prompts/taxonomies/other.json` |

> **Any jurisdiction/doc-type combination not listed above will trigger the honest fallback.** This is deliberate — we only surface jurisdictional claims that come from curated reference files.

---

## Security & Privacy

- **No data persistence.** Uploaded documents are processed entirely in memory. Nothing is written to disk or a database. Document text is held in an in-memory session store keyed by a random UUID and auto-expired after 30 minutes of inactivity.
- **No secrets in repo.** API keys are loaded from `.env` (gitignored). See `.env.example` for required variables.
- **Session cleanup.** Expired sessions are garbage-collected on access. Sessions can also be explicitly deleted via the API.

This is a deliberate design choice for a hackathon demo. A production system would need encryption-at-rest, audit logging, and compliance review.

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey))

### Backend

```bash
cd LexLens
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r backend/requirements.txt

# Create .env from template
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the backend
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and the backend on `http://localhost:8000`.

### Run Tests

```bash
# From project root, with venv activated
pytest tests/ -v
```

---

## Assumptions

- Users are seeking informational context and not formal legal representation.
- Uploaded documents are standard, text-based files (PDF, DOCX) typically under 50 pages.
- English is the primary language for uploaded documents and system interaction.

---

## Design Decisions

### Why no vector database?
At the scale of individual legal documents (typically 5-50 pages), simple in-memory chunking with paragraph-boundary splitting is sufficient. A vector DB would add complexity, a dependency, and a persistence layer — all unnecessary for this use case. The chunking strategy is documented in `backend/document_processor.py`.

### Why curated reference files instead of free-generation?
LLMs will confidently generate plausible-sounding but potentially incorrect legal information from training data. By constraining Tier B output to only quote/paraphrase from structured reference files, we make the system's knowledge boundary explicit and auditable. When no reference file exists, the system says so honestly rather than guessing.

### Why separate Tier A and Tier B?
Reading what a document says (Tier A) is a fundamentally different task from asserting what the law says about it (Tier B). Tier A can be stated with normal confidence. Tier B requires careful calibration, sourcing, and disclaimers. Mixing them would mislead users about the system's actual confidence level.

### Why jurisdiction as a first-class step?
Legal documents mean very different things in different jurisdictions. A security deposit clause that's standard in one state may violate a cap in another. Making jurisdiction selection a required, visible step ensures the user and the system are aligned on context before any analysis happens.

---

## Dependencies

### Backend
| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115.12 | Web framework |
| uvicorn | 0.34.2 | ASGI server |
| python-multipart | 0.0.20 | File upload parsing |
| google-genai | 1.14.0 | Gemini LLM client |
| python-dotenv | 1.1.0 | Env var loading |
| PyPDF2 | 3.0.1 | PDF text extraction |
| python-docx | 1.1.2 | DOCX text extraction |
| pytest | 8.3.5 | Testing |
| httpx | 0.28.1 | Async HTTP client (tests) |
| pytest-asyncio | 0.25.3 | Async test support |

### Frontend
| Package | Purpose |
|---------|---------|
| react + react-dom | UI framework |
| react-markdown | Render markdown in chat |
| lucide-react | Icons |
| axios | HTTP client |

---

## Limitations

> **⚠️ This is not legal advice.**

- LexLens is an informational tool. It does not provide legal advice and cannot replace a licensed attorney.
- Reference data is **illustrative and non-exhaustive** — it covers a small number of high-frequency concepts for select jurisdictions, not comprehensive legal coverage.
- Classification is prompt-based, not a trained classifier. It may misclassify unusual documents.
- Risk assessments are heuristic-based and may not capture all relevant factors.
- Accuracy is not guaranteed. Always verify with a qualified legal professional.
- No data persistence — session data is lost on server restart.
- The system explicitly refuses to provide definitive legal opinions or conclusions.

---

## License

MIT
