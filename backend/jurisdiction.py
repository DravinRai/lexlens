"""
LexLens Jurisdiction Reference Loader

Loads curated jurisdictional reference files from prompts/jurisdictions/.
Returns None (not an error) when no file exists for a given (region, doc_type)
pair — this is the honest-fallback trigger, not a failure state.
"""

import json
import os
from pathlib import Path
from typing import Any


# Resolve path relative to project root (one level up from backend/)
JURISDICTIONS_DIR = Path(__file__).parent.parent / "prompts" / "jurisdictions"

# Known jurisdiction mappings: user-friendly name → region code
JURISDICTION_MAP = {
    # India
    "India": "IN",
    "IN": "IN",
    # United States
    "US-CA": "US-CA",
    "California": "US-CA",
    "United States - California": "US-CA",
    # United Kingdom
    "UK": "UK",
    "United Kingdom": "UK",
    # Generic US (no state)
    "US": "US",
    "United States": "US",
}


def normalize_region_code(jurisdiction_input: str) -> str:
    """
    Normalize a user-provided jurisdiction string to a region code.
    Falls back to the input itself (uppercased, trimmed) if not in the map.
    """
    cleaned = jurisdiction_input.strip()
    if cleaned in JURISDICTION_MAP:
        return JURISDICTION_MAP[cleaned]
    # Try case-insensitive match
    for key, code in JURISDICTION_MAP.items():
        if key.lower() == cleaned.lower():
            return code
    # Fallback: return cleaned input as-is
    return cleaned.upper().replace(" ", "-")


def load_reference(region_code: str, doc_type: str) -> dict[str, Any] | None:
    """
    Load the jurisdictional reference file for a (region, doc_type) pair.

    Returns the parsed JSON dict if the file exists, or None if it doesn't.
    Returning None is INTENTIONAL — it triggers the honest fallback message:
    "I don't have verified reference data for this region for this document type."

    This is a real branch in the logic, not a vague disclaimer.
    """
    filename = f"{region_code}-{doc_type}.json"
    filepath = JURISDICTIONS_DIR / filename

    if not filepath.exists():
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, OSError):
        # Corrupted file — treat as unavailable rather than crashing
        return None


def get_supported_jurisdictions() -> list[dict]:
    """
    Scan the jurisdictions directory and return a list of supported
    (region_code, doc_type) pairs. Used by the frontend to show
    which jurisdictions have verified reference data.
    """
    supported = []
    if not JURISDICTIONS_DIR.exists():
        return supported

    for filepath in JURISDICTIONS_DIR.glob("*.json"):
        name = filepath.stem  # e.g. "IN-lease" or "US-CA-lease"
        parts = name.rsplit("-", 1)
        if len(parts) == 2:
            region_code, doc_type = parts
            supported.append({
                "region_code": region_code,
                "doc_type": doc_type,
                "filename": filepath.name,
            })
        # Handle codes like US-CA-lease (region has a dash)
        elif len(parts) == 1:
            # Try splitting differently for compound region codes
            pass
        else:
            # Fallback: try to parse the full filename
            pass

    # Re-parse with smarter logic for compound codes like US-CA-lease
    supported = _parse_jurisdiction_files()
    return supported


def _parse_jurisdiction_files() -> list[dict]:
    """Parse jurisdiction filenames, handling compound region codes."""
    supported = []
    if not JURISDICTIONS_DIR.exists():
        return supported

    # Known doc types to split on
    known_doc_types = {"lease", "employment", "nda", "tos", "freelance", "other"}

    for filepath in JURISDICTIONS_DIR.glob("*.json"):
        name = filepath.stem
        # Try each known doc type as a suffix
        for dt in known_doc_types:
            if name.endswith(f"-{dt}"):
                region_code = name[: -(len(dt) + 1)]
                supported.append({
                    "region_code": region_code,
                    "doc_type": dt,
                    "filename": filepath.name,
                })
                break

    return supported


def format_reference_for_prompt(ref_data: dict) -> str:
    """
    Format a jurisdictional reference file's content into a string
    suitable for injection into an LLM prompt.

    Only includes data from the concepts[].details arrays —
    the model must quote/paraphrase from these, never invent content.
    """
    if not ref_data:
        return ""

    lines = []
    lines.append(f"JURISDICTION: {ref_data.get('jurisdiction', 'Unknown')}")
    lines.append(f"DOCUMENT TYPE: {ref_data.get('document_type', 'Unknown')}")
    lines.append(f"LAST REVIEWED: {ref_data.get('last_reviewed', 'Unknown')}")
    lines.append("")

    coverage = ref_data.get("coverage_note", "")
    if coverage:
        lines.append(f"COVERAGE NOTE: {coverage}")
        lines.append("")

    misinfo = ref_data.get("known_misinformation_warning", "")
    if misinfo:
        lines.append(f"MISINFORMATION WARNING: {misinfo}")
        lines.append("")

    concepts = ref_data.get("concepts", [])
    for concept in concepts:
        lines.append(f"### {concept.get('summary', concept.get('concept_id', 'Unknown'))}")
        for detail in concept.get("details", []):
            lines.append(f"  - {detail}")
        confidence = concept.get("confidence", "")
        if confidence:
            lines.append(f"  Confidence: {confidence}")
        lines.append("")

    verify_items = ref_data.get("always_recommend_verifying", [])
    if verify_items:
        lines.append("ALWAYS RECOMMEND VERIFYING:")
        for item in verify_items:
            lines.append(f"  - {item}")

    return "\n".join(lines)
