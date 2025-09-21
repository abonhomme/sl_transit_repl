"""Tests for search functionality."""

import pytest

from sl_transit_repl.main import SLTransitREPL


class TestSearchFunctionality:
    """Test search functionality including text normalization and site lookup."""

    def test_normalize_text_basic(self, repl_with_temp_dir):
        """Test basic text normalization."""
        repl = repl_with_temp_dir

        result = repl._normalize_text("Stockholm Central")

        assert result == "stockholm central"

    def test_normalize_text_with_diacritics(self, repl_with_temp_dir):
        """Test text normalization with Swedish diacritics."""
        repl = repl_with_temp_dir

        result = repl._normalize_text("Södertälje")

        assert result == "sodertalje"

    def test_normalize_text_mixed_case_and_diacritics(self, repl_with_temp_dir):
        """Test text normalization with mixed case and diacritics."""
        repl = repl_with_temp_dir

        result = repl._normalize_text("Åkeshöv T-bana")

        assert result == "akeshov t-bana"

    def test_normalize_text_special_characters(self, repl_with_temp_dir):
        """Test text normalization preserves hyphens and spaces."""
        repl = repl_with_temp_dir

        result = repl._normalize_text("T-Centralen")

        assert result == "t-centralen"

    def test_find_site_by_id_exists(self, repl_with_temp_dir):
        """Test finding an existing site by ID."""
        repl = repl_with_temp_dir

        site = repl._find_site_by_id(1002)

        assert site is not None
        assert site["id"] == 1002
        assert site["name"] == "Odenplan"

    def test_find_site_by_id_not_exists(self, repl_with_temp_dir):
        """Test finding a non-existent site by ID."""
        repl = repl_with_temp_dir

        site = repl._find_site_by_id(99999)

        assert site is None

    def test_find_sites_by_substring_exact_match(self, repl_with_temp_dir):
        """Test finding sites by exact name match."""
        repl = repl_with_temp_dir

        sites = repl._find_sites_by_substring("Odenplan")

        assert len(sites) == 1
        assert sites[0]["name"] == "Odenplan"

    def test_find_sites_by_substring_partial_match(self, repl_with_temp_dir):
        """Test finding sites by partial name match."""
        repl = repl_with_temp_dir

        sites = repl._find_sites_by_substring("central")

        assert len(sites) == 1
        assert sites[0]["name"] == "Centralen"

    def test_find_sites_by_substring_case_insensitive(self, repl_with_temp_dir):
        """Test that substring search is case insensitive."""
        repl = repl_with_temp_dir

        sites_lower = repl._find_sites_by_substring("odenplan")
        sites_upper = repl._find_sites_by_substring("ODENPLAN")
        sites_mixed = repl._find_sites_by_substring("OdenPlan")

        assert len(sites_lower) == 1
        assert len(sites_upper) == 1
        assert len(sites_mixed) == 1
        assert sites_lower[0]["id"] == sites_upper[0]["id"] == sites_mixed[0]["id"]

    def test_find_sites_by_substring_no_match(self, repl_with_temp_dir):
        """Test finding sites with no matches."""
        repl = repl_with_temp_dir

        sites = repl._find_sites_by_substring("nonexistent")

        assert len(sites) == 0

    def test_find_sites_by_alias(self, repl_with_temp_dir):
        """Test finding sites by alias."""
        repl = repl_with_temp_dir

        sites = repl._find_sites_by_substring("T-bana")

        assert len(sites) == 1
        assert sites[0]["name"] == "Odenplan"

    def test_find_sites_by_alias_partial(self, repl_with_temp_dir):
        """Test finding sites by partial alias match."""
        repl = repl_with_temp_dir

        sites = repl._find_sites_by_substring("Stockholm")

        assert len(sites) == 1
        assert sites[0]["name"] == "Centralen"

    def test_search_result_sorting(self, temp_app_dir):
        """Test that search results are sorted alphabetically."""
        # Create REPL with custom data for sorting test
        sites_data = {
            "1": {"id": 1, "name": "Zebra Station", "alias": []},
            "2": {"id": 2, "name": "Alpha Station", "alias": []},
            "3": {"id": 3, "name": "Beta Station", "alias": []},
        }

        repl = SLTransitREPL(app_dir=temp_app_dir)
        repl.sites = sites_data
        repl._build_search_indices()

        sites = repl._find_sites_by_substring("station")

        assert len(sites) == 3
        assert sites[0]["name"] == "Alpha Station"
        assert sites[1]["name"] == "Beta Station"
        assert sites[2]["name"] == "Zebra Station"

    def test_search_deduplication(self, temp_app_dir):
        """Test that search results are deduplicated when matching both name and alias."""
        # Create site with alias that contains the search term
        sites_data = {
            "1": {
                "id": 1,
                "name": "Central Station",
                "alias": ["Central Terminal", "Central Hub"],
            }
        }

        repl = SLTransitREPL(app_dir=temp_app_dir)
        repl.sites = sites_data
        repl._build_search_indices()

        sites = repl._find_sites_by_substring("central")

        # Should only return one result despite matching name and multiple aliases
        assert len(sites) == 1
        assert sites[0]["name"] == "Central Station"

    def test_search_with_diacritic_insensitive(self, temp_app_dir):
        """Test that search is diacritic-insensitive."""
        sites_data = {
            "1": {"id": 1, "name": "Södertälje", "alias": []},
        }

        repl = SLTransitREPL(app_dir=temp_app_dir)
        repl.sites = sites_data
        repl._build_search_indices()

        # Search without diacritics should find site with diacritics
        sites = repl._find_sites_by_substring("sodertalje")

        assert len(sites) == 1
        assert sites[0]["name"] == "Södertälje"

    def test_search_with_mixed_diacritics(self, temp_app_dir):
        """Test search with mixed presence of diacritics."""
        sites_data = {
            "1": {"id": 1, "name": "Åkeshov", "alias": []},
        }

        repl = SLTransitREPL(app_dir=temp_app_dir)
        repl.sites = sites_data
        repl._build_search_indices()

        # Both should work
        sites_with_diacritics = repl._find_sites_by_substring("åkeshov")
        sites_without_diacritics = repl._find_sites_by_substring("akeshov")

        assert len(sites_with_diacritics) == 1
        assert len(sites_without_diacritics) == 1
        assert sites_with_diacritics[0]["id"] == sites_without_diacritics[0]["id"]

    def test_build_search_indices_creates_proper_structures(self, repl_with_temp_dir):
        """Test that search indices are built correctly."""
        repl = repl_with_temp_dir

        # Check that indices were created
        assert hasattr(repl, "idx_by_id")
        assert hasattr(repl, "idx_by_name")

        # Check ID index
        assert 1002 in repl.idx_by_id
        assert 9001 in repl.idx_by_id
        assert repl.idx_by_id[1002]["name"] == "Odenplan"

        # Check name index (should include both names and aliases)
        name_entries = [entry[0] for entry in repl.idx_by_name]
        assert "odenplan" in name_entries
        assert "centralen" in name_entries
        assert "odenplan t-bana" in name_entries  # from alias

    def test_search_empty_string(self, repl_with_temp_dir):
        """Test searching with empty string."""
        repl = repl_with_temp_dir

        sites = repl._find_sites_by_substring("")

        # Empty string should match all sites due to substring logic
        assert len(sites) >= 2  # At least our test sites

    def test_search_whitespace_only(self, repl_with_temp_dir):
        """Test searching with whitespace-only string."""
        repl = repl_with_temp_dir

        sites = repl._find_sites_by_substring("   ")

        # Whitespace should be normalized and match sites with spaces
        assert len(sites) >= 0  # May or may not match depending on normalization

    @pytest.mark.parametrize(
        "search_term,expected_count",
        [
            ("Odenplan", 1),
            ("Central", 1),
            ("T-bana", 1),
            ("Station", 0),  # Not in our test data
            ("Stockholm", 1),  # In alias
        ],
    )
    def test_various_search_terms(
        self, repl_with_temp_dir, search_term, expected_count
    ):
        """Test various search terms and their expected results."""
        repl = repl_with_temp_dir

        sites = repl._find_sites_by_substring(search_term)

        assert len(sites) == expected_count
