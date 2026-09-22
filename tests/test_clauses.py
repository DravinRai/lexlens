"""
Tests for clause taxonomy loading and structure validation.

Validates:
- All expected taxonomy files load correctly
- Taxonomy structure is valid (document_type, clauses, risk_factors)
- Fallback to 'other' taxonomy works
- Prompt formatting is correct
"""

from backend.taxonomy import load_taxonomy, format_taxonomy_for_prompt, get_available_taxonomies


EXPECTED_DOC_TYPES = ["lease", "employment", "nda", "tos", "freelance", "other"]


class TestLoadTaxonomy:
    """Test taxonomy file loading."""

    def test_load_lease_taxonomy(self):
        tax = load_taxonomy("lease")
        assert tax["document_type"] == "lease"
        assert len(tax["clauses"]) > 0

    def test_load_employment_taxonomy(self):
        tax = load_taxonomy("employment")
        assert tax["document_type"] == "employment"

    def test_load_nda_taxonomy(self):
        tax = load_taxonomy("nda")
        assert tax["document_type"] == "nda"

    def test_load_tos_taxonomy(self):
        tax = load_taxonomy("tos")
        assert tax["document_type"] == "tos"

    def test_load_freelance_taxonomy(self):
        tax = load_taxonomy("freelance")
        assert tax["document_type"] == "freelance"

    def test_load_other_taxonomy(self):
        tax = load_taxonomy("other")
        assert tax["document_type"] == "other"

    def test_unknown_falls_back_to_other(self):
        """Unknown doc type should fall back to 'other' taxonomy."""
        tax = load_taxonomy("completely_unknown_type")
        assert tax["document_type"] == "other"


class TestTaxonomyStructure:
    """Validate that all taxonomies follow the expected schema."""

    def test_all_taxonomies_have_required_fields(self):
        for doc_type in EXPECTED_DOC_TYPES:
            tax = load_taxonomy(doc_type)
            assert "document_type" in tax, f"{doc_type} missing document_type"
            assert "description" in tax, f"{doc_type} missing description"
            assert "clauses" in tax, f"{doc_type} missing clauses"
            assert isinstance(tax["clauses"], list), f"{doc_type} clauses not a list"
            assert len(tax["clauses"]) > 0, f"{doc_type} has empty clauses"

    def test_all_clauses_have_required_fields(self):
        for doc_type in EXPECTED_DOC_TYPES:
            tax = load_taxonomy(doc_type)
            for clause in tax["clauses"]:
                assert "name" in clause, f"{doc_type}/{clause}: missing name"
                assert "description" in clause, f"{doc_type}/{clause}: missing description"
                assert "risk_factors" in clause, f"{doc_type}/{clause}: missing risk_factors"

    def test_risk_factors_have_all_levels(self):
        for doc_type in EXPECTED_DOC_TYPES:
            tax = load_taxonomy(doc_type)
            for clause in tax["clauses"]:
                rf = clause["risk_factors"]
                assert "high" in rf, f"{doc_type}/{clause['name']}: missing high risk factors"
                assert "medium" in rf, f"{doc_type}/{clause['name']}: missing medium risk factors"
                assert "low" in rf, f"{doc_type}/{clause['name']}: missing low risk factors"
                assert isinstance(rf["high"], list)
                assert isinstance(rf["medium"], list)
                assert isinstance(rf["low"], list)

    def test_lease_has_key_clauses(self):
        tax = load_taxonomy("lease")
        clause_names = [c["name"] for c in tax["clauses"]]
        assert any("rent" in n.lower() for n in clause_names), "Lease should have rent clause"
        assert any("deposit" in n.lower() for n in clause_names), "Lease should have deposit clause"
        assert any("termination" in n.lower() or "notice" in n.lower() for n in clause_names), "Lease should have termination clause"

    def test_employment_has_key_clauses(self):
        tax = load_taxonomy("employment")
        clause_names = [c["name"].lower() for c in tax["clauses"]]
        assert any("compens" in n or "salary" in n for n in clause_names), "Employment should have compensation clause"
        assert any("non-compete" in n or "noncompete" in n for n in clause_names), "Employment should have non-compete clause"

    def test_nda_has_key_clauses(self):
        tax = load_taxonomy("nda")
        clause_names = [c["name"].lower() for c in tax["clauses"]]
        assert any("confidential" in n for n in clause_names), "NDA should have confidential info definition"


class TestTaxonomyFormatting:
    """Test prompt formatting."""

    def test_format_includes_doc_type(self):
        tax = load_taxonomy("lease")
        formatted = format_taxonomy_for_prompt(tax)
        assert "lease" in formatted.lower()

    def test_format_includes_clause_names(self):
        tax = load_taxonomy("lease")
        formatted = format_taxonomy_for_prompt(tax)
        for clause in tax["clauses"]:
            assert clause["name"] in formatted

    def test_format_includes_risk_factors(self):
        tax = load_taxonomy("lease")
        formatted = format_taxonomy_for_prompt(tax)
        assert "HIGH RISK" in formatted
        assert "MEDIUM RISK" in formatted or "LOW RISK" in formatted


class TestAvailableTaxonomies:
    """Test taxonomy discovery."""

    def test_all_expected_types_available(self):
        available = get_available_taxonomies()
        for dt in EXPECTED_DOC_TYPES:
            assert dt in available, f"{dt} taxonomy should be available"
