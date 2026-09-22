"""
LexLens Prompt Templates

All LLM prompt templates, centralized. Each prompt is carefully designed to:
- Enforce the Tier A (document-grounded) vs Tier B (jurisdiction-grounded) separation
- Prevent the model from inventing jurisdictional facts
- Require honest refusal when asked for definitive legal opinions
- Maintain calibrated confidence throughout
"""

GLOBAL_SYSTEM_INSTRUCTION = """You are LexLens, a legal document analysis assistant. You INFORM and ASSIST — you NEVER claim to replace a licensed attorney, and you NEVER assert jurisdiction-specific legal conclusions with more confidence than you can actually back up.

CRITICAL RULES:
1. You may ONLY state jurisdictional information that is explicitly provided to you in the JURISDICTIONAL REFERENCE DATA section below. Do NOT generate, infer, or recall jurisdictional legal facts from your training data.
2. If no jurisdictional reference data is provided, you must explicitly say "I don't have verified reference data for this region for this document type" — do NOT guess.
3. Always distinguish between what the DOCUMENT says (Tier A — high confidence) and what the JURISDICTION typically does (Tier B — informational only, requires verification).
4. Never phrase jurisdictional information as a definitive legal conclusion about the user's specific situation.
5. Always end jurisdiction-related statements with a recommendation to verify with a licensed professional.
6. You are NOT a lawyer. You are a document analysis tool."""

# ─────────────────────────────────────────────────────────────
# CLASSIFICATION
# ─────────────────────────────────────────────────────────────
CLASSIFY_PROMPT = """Classify this legal document into exactly ONE of these categories:
- lease (residential or commercial rental/lease agreement)
- employment (employment offer letter, employment contract, or employment agreement)
- nda (non-disclosure agreement, confidentiality agreement)
- tos (terms of service, terms of use, privacy policy)
- freelance (freelance agreement, independent contractor agreement, services agreement)
- other (anything that doesn't clearly fit the above)

Respond with ONLY a JSON object in this exact format:
{
  "doc_type": "<category>",
  "confidence": "<high|medium|low>",
  "reasoning": "<one sentence explaining why>"
}

DOCUMENT TEXT:
---
{document_text}
---"""

# ─────────────────────────────────────────────────────────────
# CLAUSE EXTRACTION + RISK TAGGING
# ─────────────────────────────────────────────────────────────
EXTRACT_AND_RISK_PROMPT = """Analyze this legal document and extract clauses based on the taxonomy below.

{taxonomy_text}

For EACH clause you find in the document:
1. Extract the relevant text (quote or closely paraphrase from the document)
2. Write a plain-language summary (1-2 sentences, accessible to a non-lawyer)
3. Assign a risk tag: "low", "medium", or "high" based on the risk factors in the taxonomy
4. Provide a one-line rationale for the risk tag
5. Note the approximate location in the document (section name or page if available)

For clauses in the taxonomy that are NOT found in the document, include them with found=false — missing important clauses can itself be a risk signal.

Respond with ONLY a JSON object:
{{
  "clauses": [
    {{
      "name": "<clause name from taxonomy>",
      "found": true,
      "extracted_text": "<quoted or closely paraphrased text from document>",
      "plain_summary": "<1-2 sentence plain-language explanation>",
      "risk_level": "<low|medium|high>",
      "risk_rationale": "<one line explaining the risk assessment>",
      "location": "<section/page reference if available>"
    }}
  ],
  "document_summary": "<3-5 sentence plain-language summary of the entire document>",
  "key_dates_and_deadlines": [
    {{
      "description": "<what the date/deadline is for>",
      "date_or_period": "<the actual date or time period mentioned>"
    }}
  ],
  "parties": [
    {{
      "role": "<e.g. landlord, tenant, employer, employee>",
      "name": "<party name if mentioned>"
    }}
  ]
}}

DOCUMENT TEXT:
---
{document_text}
---"""

# ─────────────────────────────────────────────────────────────
# TIER B — JURISDICTIONAL CONTEXT (only when reference data exists)
# ─────────────────────────────────────────────────────────────
TIER_B_PROMPT = """Based ONLY on the jurisdictional reference data provided below, provide general informational context about how this jurisdiction typically treats the clauses found in this document.

CRITICAL INSTRUCTIONS:
- You may ONLY reference information explicitly present in the JURISDICTIONAL REFERENCE DATA below.
- Do NOT generate, infer, or recall any legal facts from your training data.
- Frame everything as general information ("In [region], clauses like this are commonly..."), NEVER as a definitive legal conclusion about this specific document or situation.
- Include the confidence level from the reference data.
- End each point with a note to verify with a licensed professional in that jurisdiction.
- If a clause in the document has no corresponding concept in the reference data, say so explicitly rather than improvising.

JURISDICTIONAL REFERENCE DATA:
---
{jurisdiction_text}
---

EXTRACTED CLAUSES FROM DOCUMENT:
---
{clauses_json}
---

Respond with ONLY a JSON object:
{{
  "jurisdiction": "{jurisdiction_name}",
  "has_reference_data": true,
  "coverage_note": "<coverage note from reference data>",
  "clause_context": [
    {{
      "clause_name": "<name of clause from extraction>",
      "has_jurisdiction_info": true,
      "general_context": "<informational context from reference data ONLY>",
      "confidence": "<confidence level from reference data>",
      "verification_note": "<what specifically should be verified with a local professional>"
    }}
  ],
  "items_to_verify": ["<list from always_recommend_verifying in reference data>"]
}}"""

# ─────────────────────────────────────────────────────────────
# TIER B — NO REFERENCE DATA (honest fallback)
# ─────────────────────────────────────────────────────────────
TIER_B_NO_DATA_RESPONSE = {
    "has_reference_data": False,
    "message": "I don't have verified reference data for this region for this document type. I can only provide Tier A analysis (what the document itself says) without jurisdiction-specific context.",
    "recommendation": "We strongly recommend consulting a licensed legal professional familiar with this jurisdiction to understand how local laws may affect the terms in this document.",
    "checklist_addition": "Confirm which jurisdiction's law governs this document and consult a local legal professional.",
}

# ─────────────────────────────────────────────────────────────
# CHECKLIST GENERATION
# ─────────────────────────────────────────────────────────────
CHECKLIST_PROMPT = """Based on the document analysis and jurisdictional context below, generate:
1. A checklist of recommended next steps for the person reviewing this document
2. A list of specific questions they should ask a lawyer

Tailor both lists to:
- The document type ({doc_type})
- The jurisdiction ({jurisdiction}) — if jurisdiction is unknown or unsupported, include "Confirm which jurisdiction's law governs this document" as the FIRST checklist item
- The specific risk areas identified in the clause analysis

{jurisdiction_context}

CLAUSE ANALYSIS:
---
{clauses_json}
---

Respond with ONLY a JSON object:
{{
  "next_steps": [
    {{
      "item": "<action item>",
      "priority": "<high|medium|low>",
      "reason": "<why this matters>"
    }}
  ],
  "questions_for_lawyer": [
    {{
      "question": "<specific question to ask>",
      "related_clause": "<which clause this relates to>",
      "why_important": "<brief explanation>"
    }}
  ]
}}"""

# ─────────────────────────────────────────────────────────────
# DOCUMENT COMPARISON
# ─────────────────────────────────────────────────────────────
COMPARE_PROMPT = """Compare these two legal documents clause by clause. For each clause that appears in either document:

1. Identify whether it exists in Document A only, Document B only, or both
2. If in both, highlight material differences
3. For each material difference, indicate which party the change favors (or if neutral)
4. Provide a plain-language explanation of the impact

DOCUMENT A:
---
{document_a_text}
---

DOCUMENT B:
---
{document_b_text}
---

{taxonomy_text}

Respond with ONLY a JSON object:
{{
  "comparison_summary": "<2-3 sentence overview of key differences>",
  "clause_comparisons": [
    {{
      "clause_name": "<clause name>",
      "in_doc_a": true,
      "in_doc_b": true,
      "has_material_difference": true,
      "doc_a_text": "<relevant text from doc A>",
      "doc_b_text": "<relevant text from doc B>",
      "difference_description": "<plain-language explanation of the difference>",
      "favors": "<party_a|party_b|neutral|unclear>",
      "impact": "<brief explanation of practical impact>"
    }}
  ]
}}"""

# ─────────────────────────────────────────────────────────────
# GROUNDED Q&A
# ─────────────────────────────────────────────────────────────
QA_SYSTEM_PROMPT = """You are LexLens Q&A, answering questions about a specific uploaded legal document.

STRICT RULES:
1. Answer ONLY from the document content provided below and, if available, the jurisdictional reference data. NEVER draw on your general training knowledge about law.
2. For every factual claim, cite the specific section, clause, or page of the document it comes from (e.g., "According to Section 5 of your document...").
3. If the jurisdictional reference data is available, you may reference it — but frame it as general information, not a definitive legal conclusion about this specific document.
4. If a question asks about something NOT covered in the document or reference data, say explicitly: "This question is outside the scope of what's covered in your document [and the reference data I have for this jurisdiction]. I'd recommend consulting a licensed legal professional for guidance on this."
5. If asked for a definitive legal opinion or advice (e.g., "should I sign this?", "is this legal?", "will this hold up in court?"), respond: "I can help you understand what this document says and flag potential concerns, but I cannot provide legal advice or opinions. For a definitive assessment of your specific situation, please consult a licensed attorney."
6. Keep answers clear, concise, and accessible to non-lawyers.

DOCUMENT CONTENT:
---
{document_text}
---

{jurisdiction_section}

CONVERSATION HISTORY:
{chat_history}"""

QA_JURISDICTION_SECTION = """JURISDICTIONAL REFERENCE DATA (use ONLY this for jurisdiction-related information, do not invent):
---
{jurisdiction_text}
---"""

QA_NO_JURISDICTION_SECTION = """NOTE: No verified jurisdictional reference data is available for this document's jurisdiction. If asked about jurisdiction-specific legal matters, explicitly state that you don't have verified reference data and recommend consulting a local professional."""
