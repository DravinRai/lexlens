"""
LexLens LLM Client — Gemini Wrapper

All LLM calls go through this module. Handles:
- Client initialization with API key from env
- System prompt construction per document type
- Injecting jurisdiction reference data (or the "no data" signal)
- Structured output parsing (JSON extraction from responses)
"""

import json
import os
import re
from typing import Any

from google import genai
from google.genai import types

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


def _get_client() -> genai.Client:
    """Get or create a Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)


def _get_model() -> str:
    """Get the configured model name."""
    return os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def _extract_json(text: str) -> dict | list:
    """Extract JSON from an LLM response that might contain markdown fences."""
    # Try direct parse first
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


async def _generate_with_retry(client, model, contents, config):
    import asyncio
    for attempt in range(5):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as e:
            if attempt < 4:
                print(f"LLM API error (attempt {attempt + 1}): {e}")
                await asyncio.sleep(20)
            else:
                raise


async def classify_document(document_text: str) -> dict[str, Any]:
    """
    Classify document type using Gemini.

    Returns: {"doc_type": str, "confidence": str, "reasoning": str}
    """
    client = _get_client()

    # Use first ~4000 chars for classification (enough to identify type)
    truncated = document_text[:4000]

    prompt = CLASSIFY_PROMPT.format(document_text=truncated)

    response = await _generate_with_retry(
        client=client,
        model=_get_model(),
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
            temperature=0.1,  # Low temp for classification
        ),
    )

    return _extract_json(response.text)


async def extract_and_risk_tag(
    document_text: str, taxonomy: dict
) -> dict[str, Any]:
    """
    Extract clauses from document and assign risk tags.

    Returns Tier A data: clauses, summary, dates, parties.
    """
    client = _get_client()
    taxonomy_text = format_taxonomy_for_prompt(taxonomy)

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

    return _extract_json(response.text)


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


async def grounded_qa(
    question: str,
    document_text: str,
    jurisdiction_ref: dict | None,
    chat_history: list[dict],
) -> dict[str, Any]:
    """
    Answer a question grounded ONLY in the uploaded document and
    (if available) the jurisdictional reference data.

    Never draws on general model knowledge about law.
    Cites sections. Refuses definitive legal opinions.
    """
    client = _get_client()

    # Build jurisdiction section
    if jurisdiction_ref is not None:
        jurisdiction_section = QA_JURISDICTION_SECTION.format(
            jurisdiction_text=format_reference_for_prompt(jurisdiction_ref)
        )
    else:
        jurisdiction_section = QA_NO_JURISDICTION_SECTION

    # Format chat history
    history_str = ""
    for msg in chat_history[-10:]:  # Keep last 10 messages for context
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_str += f"{role.upper()}: {content}\n"

    system_prompt = QA_SYSTEM_PROMPT.format(
        document_text=document_text,
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
