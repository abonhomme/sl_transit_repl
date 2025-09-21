"""Tests for query parsing functionality."""

import pytest


class TestQueryParsing:
    """Test query parsing functionality."""

    def test_parse_simple_site_id(self, repl_with_temp_dir):
        """Test parsing a simple site ID query."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002")

        assert valid is True
        assert result["site"] == "1002"

    def test_parse_site_with_line_parameter(self, repl_with_temp_dir):
        """Test parsing site ID with line parameter."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002 line:17")

        assert valid is True
        assert result["site"] == "1002"
        assert result["line"] == "17"

    def test_parse_site_with_multiple_parameters(self, repl_with_temp_dir):
        """Test parsing site ID with multiple parameters."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002 line:17 direction:1 forecast:30")

        assert valid is True
        assert result["site"] == "1002"
        assert result["line"] == "17"
        assert result["direction"] == "1"
        assert result["forecast"] == "30"

    def test_parse_explicit_site_parameter(self, repl_with_temp_dir):
        """Test parsing with explicit site parameter."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("site:1002 line:17")

        assert valid is True
        assert result["site"] == "1002"
        assert result["line"] == "17"

    def test_parse_help_command(self, repl_with_temp_dir):
        """Test parsing help command."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("help")

        assert valid is True
        assert result["command"] == "help"

    def test_parse_lookup_id_command(self, repl_with_temp_dir):
        """Test parsing lookup by ID command."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("lookup:id 1002")

        assert valid is True
        assert result["command"] == "lookup"
        assert result["lookup_type"] == "id"
        assert result["search_term"] == "1002"

    def test_parse_lookup_name_command(self, repl_with_temp_dir):
        """Test parsing lookup by name command."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("lookup:name odenplan")

        assert valid is True
        assert result["command"] == "lookup"
        assert result["lookup_type"] == "name"
        assert result["search_term"] == "odenplan"

    def test_parse_lookup_name_multi_word(self, repl_with_temp_dir):
        """Test parsing lookup by name with multiple words."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("lookup:name stockholm central")

        assert valid is True
        assert result["command"] == "lookup"
        assert result["lookup_type"] == "name"
        assert result["search_term"] == "stockholm central"

    def test_parse_transport_mode_case_handling(self, repl_with_temp_dir):
        """Test that transport modes are converted to uppercase."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002 transport:metro")

        assert valid is True
        assert result["transport"] == "METRO"

    def test_parse_boolean_parameters(self, repl_with_temp_dir):
        """Test parsing boolean parameters."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002 show_numbers:true debug:false")

        assert valid is True
        assert result["show_numbers"] == "true"
        assert result["debug"] == "false"

    def test_parse_underscore_prefixed_parameters(self, repl_with_temp_dir):
        """Test that underscore-prefixed parameters bypass validation."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002 _custom_header:value")

        assert valid is True
        assert result["_custom_header"] == "value"

    def test_parse_invalid_site_id_non_numeric(self, repl_with_temp_dir):
        """Test parsing fails for non-numeric site ID."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("abc")

        assert valid is False
        assert "Invalid site ID" in result["error"]

    def test_parse_invalid_site_id_empty(self, repl_with_temp_dir):
        """Test parsing fails for empty query."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("")

        assert valid is False
        assert result["error"] == ""

    def test_parse_invalid_parameter_format(self, repl_with_temp_dir):
        """Test parsing fails for invalid parameter format."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002 invalid_param")

        assert valid is False
        assert "Invalid parameter format" in result["error"]

    def test_parse_invalid_parameter_name(self, repl_with_temp_dir):
        """Test parsing fails for invalid parameter name."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002 invalid:value")

        assert valid is False
        assert "Invalid parameter name" in result["error"]

    def test_parse_invalid_parameter_value(self, repl_with_temp_dir):
        """Test parsing fails for invalid parameter value."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002 direction:3")

        assert valid is False
        assert "Invalid value for direction" in result["error"]

    def test_parse_invalid_transport_mode(self, repl_with_temp_dir):
        """Test parsing fails for invalid transport mode."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("1002 transport:INVALID")

        assert valid is False
        assert "Invalid value for transport" in result["error"]

    def test_parse_invalid_lookup_type(self, repl_with_temp_dir):
        """Test parsing fails for invalid lookup type."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("lookup:invalid term")

        assert valid is False
        assert "Invalid lookup type" in result["error"]

    def test_parse_lookup_missing_search_term(self, repl_with_temp_dir):
        """Test parsing fails for lookup without search term."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("lookup:id")

        assert valid is False
        assert "requires a search term" in result["error"]

    def test_parse_missing_site_for_labeled_params(self, repl_with_temp_dir):
        """Test parsing fails when only labeled parameters are provided without site."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query("line:17")

        assert valid is False
        assert "Site ID is required" in result["error"]

    @pytest.mark.parametrize(
        "query,expected_site",
        [
            ("1002", "1002"),
            ("9001", "9001"),
            ("123456", "123456"),
        ],
    )
    def test_parse_various_site_ids(self, repl_with_temp_dir, query, expected_site):
        """Test parsing various valid site IDs."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query(query)

        assert valid is True
        assert result["site"] == expected_site

    @pytest.mark.parametrize(
        "transport_mode", ["BUS", "TRAM", "METRO", "TRAIN", "FERRY", "SHIP", "TAXI"]
    )
    def test_parse_all_transport_modes(self, repl_with_temp_dir, transport_mode):
        """Test parsing all valid transport modes."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query(f"1002 transport:{transport_mode.lower()}")

        assert valid is True
        assert result["transport"] == transport_mode

    @pytest.mark.parametrize("direction", ["1", "2"])
    def test_parse_valid_directions(self, repl_with_temp_dir, direction):
        """Test parsing valid direction values."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query(f"1002 direction:{direction}")

        assert valid is True
        assert result["direction"] == direction

    @pytest.mark.parametrize("boolean_val", ["true", "false", "TRUE", "FALSE"])
    def test_parse_boolean_values(self, repl_with_temp_dir, boolean_val):
        """Test parsing valid boolean values."""
        repl = repl_with_temp_dir

        valid, result = repl._parse_query(f"1002 debug:{boolean_val}")

        assert valid is True
        assert result["debug"] == boolean_val.lower()
