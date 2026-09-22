"""
Tests for jurisdiction reference file loading.

Validates:
- Existing reference files load correctly
- Missing files return None (honest fallback, not an error)
- Region code normalization works
- Prompt formatting is correct
"""

import json
from pathlib import Path

from backend.jurisdiction import (
    load_reference,
    normalize_region_code,
    get_supported_jurisdictions,
    format_reference_for_prompt,
    JURISDICTIONS_DIR,
)


class TestLoadReference:
    """Test jurisdiction reference file loading."""

    def test_load_existing_india_lease(self):
        """IN-lease.json should load successfully."""
        ref = load_reference("IN", "lease")
        assert ref is not None
        assert ref["jurisdiction"] == "India"
        assert ref["document_type"] == "lease"
        assert "concepts" in ref
        assert len(ref["concepts"]) > 0

    def test_load_existing_us_ca_lease(self):
        """US-CA-lease.json should load successfully."""
        ref = load_reference("US-CA", "lease")
        assert ref is not None
        assert ref["jurisdiction"] == "United States - California"
        assert ref["document_type"] == "lease"
        assert "concepts" in ref

    def test_load_missing_jurisdiction_returns_none(self):
        """Missing jurisdiction should return None, not raise an error."""
        ref = load_reference("DE", "lease")
        assert ref is None

    def test_load_missing_doc_type_returns_none(self):
        """Existing region but missing doc type should return None."""
        ref = load_reference("IN", "employment")
        assert ref is None

    def test_load_completely_unknown_returns_none(self):
        """Totally unknown combination returns None."""
        ref = load_reference("XX-YY", "unknown_type")
        assert ref is None

    def test_none_is_not_an_error(self):
        """Verify that None return is intentional honest-fallback behavior."""
        # This test exists to document that returning None is the DESIGN,
        # not a bug — it triggers the "no verified data" message
        result = load_reference("FR", "nda")
        assert result is None, (
            "Unsupported jurisdictions MUST return None to trigger "
            "the honest 'no verified data' fallback message"
        )


class TestNormalizeRegionCode:
    """Test region code normalization."""

    def test_direct_code(self):
        assert normalize_region_code("IN") == "IN"
        assert normalize_region_code("US-CA") == "US-CA"

    def test_friendly_name(self):
        assert normalize_region_code("India") == "IN"
        assert normalize_region_code("California") == "US-CA"
        assert normalize_region_code("United Kingdom") == "UK"

    def test_case_insensitive(self):
        assert normalize_region_code("india") == "IN"
        assert normalize_region_code("INDIA") == "IN"

    def test_unknown_passthrough(self):
        """Unknown input should be uppercased and returned as-is."""
        result = normalize_region_code("Germany")
        assert result == "GERMANY"

    def test_whitespace_handling(self):
        assert normalize_region_code("  IN  ") == "IN"


class TestSupportedJurisdictions:
    """Test discovery of supported jurisdiction files."""

    def test_returns_list(self):
        supported = get_supported_jurisdictions()
        assert isinstance(supported, list)

    def test_includes_india_lease(self):
        supported = get_supported_jurisdictions()
        matches = [s for s in supported if s["region_code"] == "IN" and s["doc_type"] == "lease"]
        assert len(matches) == 1

    def test_includes_us_ca_lease(self):
        supported = get_supported_jurisdictions()
        matches = [s for s in supported if s["region_code"] == "US-CA" and s["doc_type"] == "lease"]
        assert len(matches) == 1


class TestFormatReferenceForPrompt:
    """Test prompt formatting of reference data."""

    def test_formats_india_lease(self):
        ref = load_reference("IN", "lease")
        formatted = format_reference_for_prompt(ref)
        assert "India" in formatted
        assert "lease" in formatted
        assert "security_deposit" in formatted.lower() or "Security deposit" in formatted

    def test_includes_coverage_note(self):
        ref = load_reference("US-CA", "lease")
        formatted = format_reference_for_prompt(ref)
        assert "California" in formatted
        assert "COVERAGE NOTE" in formatted

    def test_empty_returns_empty_string(self):
        assert format_reference_for_prompt(None) == ""
        assert format_reference_for_prompt({}) == ""

    def test_concepts_details_included(self):
        """Verify that concept details are in the formatted output."""
        ref = load_reference("IN", "lease")
        formatted = format_reference_for_prompt(ref)
        # Check that at least one detail from the reference file appears
        assert "Model Tenancy Act" in formatted

    def test_confidence_included(self):
        """Verify confidence levels are passed through."""
        ref = load_reference("US-CA", "lease")
        formatted = format_reference_for_prompt(ref)
        assert "Confidence" in formatted or "confidence" in formatted


class TestReferenceFileStructure:
    """Validate the structure of existing reference files."""

    def test_india_lease_structure(self):
        ref = load_reference("IN", "lease")
        assert "jurisdiction" in ref
        assert "region_code" in ref
        assert "document_type" in ref
        assert "concepts" in ref
        assert "always_recommend_verifying" in ref
        for concept in ref["concepts"]:
            assert "concept_id" in concept
            assert "summary" in concept
            assert "details" in concept
            assert isinstance(concept["details"], list)
            assert len(concept["details"]) > 0

    def test_us_ca_lease_structure(self):
        ref = load_reference("US-CA", "lease")
        assert ref["region_code"] == "US-CA"
        for concept in ref["concepts"]:
            assert "concept_id" in concept
            assert "details" in concept
            assert len(concept["details"]) > 0
