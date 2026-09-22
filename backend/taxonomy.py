"""
LexLens Taxonomy Loader

Loads document-type-specific clause taxonomies from prompts/taxonomies/.
Each taxonomy defines what clauses to look for and what "risky" means
for that document type.
"""

import json
from pathlib import Path
from typing import Any


TAXONOMIES_DIR = Path(__file__).parent.parent / "prompts" / "taxonomies"


def load_taxonomy(doc_type: str) -> dict[str, Any]:
    """
    Load the clause taxonomy for a given document type.

    Falls back to 'other.json' if no specific taxonomy exists.
    """
    filename = f"{doc_type}.json"
    filepath = TAXONOMIES_DIR / filename

    if not filepath.exists():
        # Fall back to generic taxonomy
        filepath = TAXONOMIES_DIR / "other.json"
        if not filepath.exists():
            return _default_taxonomy()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return _default_taxonomy()


def format_taxonomy_for_prompt(taxonomy: dict) -> str:
    """
    Format taxonomy data for injection into an LLM extraction prompt.
    Tells the model what clauses to look for and how to assess risk.
    """
    lines = []
    lines.append(f"DOCUMENT TYPE: {taxonomy.get('document_type', 'Unknown')}")
    lines.append(f"DESCRIPTION: {taxonomy.get('description', '')}")
    lines.append("")
    lines.append("CLAUSES TO EXTRACT (look for each of these in the document):")

    for clause in taxonomy.get("clauses", []):
        lines.append(f"\n  CLAUSE: {clause.get('name', 'Unknown')}")
        lines.append(f"  Description: {clause.get('description', '')}")
        risk_factors = clause.get("risk_factors", {})
        if risk_factors.get("high"):
            lines.append(f"  HIGH RISK if: {'; '.join(risk_factors['high'])}")
        if risk_factors.get("medium"):
            lines.append(f"  MEDIUM RISK if: {'; '.join(risk_factors['medium'])}")
        if risk_factors.get("low"):
            lines.append(f"  LOW RISK if: {'; '.join(risk_factors['low'])}")

    return "\n".join(lines)


def get_available_taxonomies() -> list[str]:
    """Return list of available document types that have taxonomies."""
    if not TAXONOMIES_DIR.exists():
        return []
    return [f.stem for f in TAXONOMIES_DIR.glob("*.json")]


def _default_taxonomy() -> dict:
    """Minimal fallback taxonomy when no file is available."""
    return {
        "document_type": "other",
        "description": "Generic legal document",
        "clauses": [
            {
                "name": "Parties",
                "description": "Who are the parties to this agreement",
                "risk_factors": {"high": [], "medium": [], "low": []}
            },
            {
                "name": "Obligations",
                "description": "Key obligations of each party",
                "risk_factors": {"high": ["One-sided obligations"], "medium": [], "low": []}
            },
            {
                "name": "Term and Termination",
                "description": "Duration and how to end the agreement",
                "risk_factors": {"high": ["Auto-renewal with no opt-out"], "medium": [], "low": []}
            },
            {
                "name": "Liability",
                "description": "Limitations on liability",
                "risk_factors": {"high": ["Unlimited liability for one party"], "medium": [], "low": []}
            },
            {
                "name": "Dispute Resolution",
                "description": "How disputes are handled",
                "risk_factors": {"high": ["Mandatory arbitration in distant jurisdiction"], "medium": [], "low": []}
            },
            {
                "name": "Governing Law",
                "description": "Which jurisdiction's laws apply",
                "risk_factors": {"high": [], "medium": ["Unfamiliar jurisdiction"], "low": []}
            },
        ],
    }
