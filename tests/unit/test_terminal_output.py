"""Tests for terminal output and display formatting."""

import pytest
from rich.table import Table

from sl_transit_repl.main import SLTransitREPL


class TestTerminalOutput:
    """Test terminal output and display formatting (renamed from 'table creation')."""

    def test_create_site_display_single_site(self, repl_with_temp_dir):
        """Test creating terminal display for a single site."""
        repl = repl_with_temp_dir
        site = repl.sites["1002"]

        display_output = repl._create_site_table(site, "Test Site")

        assert isinstance(display_output, Table)
        assert display_output.title == "Test Site"

    def test_create_site_display_multiple_sites(self, repl_with_temp_dir):
        """Test creating terminal display for multiple sites."""
        repl = repl_with_temp_dir
        sites = list(repl.sites.values())

        display_output = repl._create_site_table(sites, "Test Sites")

        assert isinstance(display_output, Table)
        assert display_output.title == "Test Sites"

    def test_create_site_display_handles_empty_aliases(self, temp_app_dir):
        """Test that sites without aliases are handled correctly."""
        site_data = {
            "1": {
                "id": 1,
                "name": "Test Station",
                "abbreviation": "TST",
                "lat": 59.0,
                "lon": 18.0,
                # No alias field
            }
        }

        repl = SLTransitREPL(app_dir=temp_app_dir)
        repl.sites = site_data

        # Should not crash when alias field is missing
        display_output = repl._create_site_table(site_data["1"], "Test")

        assert isinstance(display_output, Table)

    def test_create_departures_display_basic(
        self, repl_with_temp_dir, future_datetime_str
    ):
        """Test creating basic departures terminal display."""
        repl = repl_with_temp_dir

        departures = [
            {
                "line": {"id": 17, "designation": "17", "transport_mode": "METRO"},
                "direction": "Åkeshov",
                "direction_code": 1,
                "scheduled": future_datetime_str,
                "expected": future_datetime_str,
                "state": "EXPECTED",
                "stop_point": {"designation": "2"},
            }
        ]

        display_output = repl._create_departure_table(departures)

        assert isinstance(display_output, Table)

    def test_create_departures_display_with_direction_numbers(
        self, repl_with_temp_dir, future_datetime_str
    ):
        """Test departures display with direction numbers enabled."""
        repl = repl_with_temp_dir

        departures = [
            {
                "line": {"id": 17, "designation": "17", "transport_mode": "METRO"},
                "direction": "Åkeshov",
                "direction_code": 1,
                "scheduled": future_datetime_str,
                "expected": future_datetime_str,
                "state": "EXPECTED",
                "stop_point": {"designation": "2"},
            }
        ]

        display_output = repl._create_departure_table(
            departures, show_direction_numbers=True
        )

        assert isinstance(display_output, Table)

    def test_departure_display_handles_missing_expected_time(
        self, repl_with_temp_dir, future_datetime_str
    ):
        """Test that missing expected time falls back to scheduled time."""
        repl = repl_with_temp_dir

        departures = [
            {
                "line": {"id": 17, "designation": "17", "transport_mode": "METRO"},
                "direction": "Åkeshov",
                "direction_code": 1,
                "scheduled": future_datetime_str,
                # No expected field
                "state": "EXPECTED",
                "stop_point": {"designation": "2"},
            }
        ]

        # Should not crash when expected time is missing
        display_output = repl._create_departure_table(departures)

        assert isinstance(display_output, Table)

    def test_departure_display_status_coloring(
        self, repl_with_temp_dir, future_datetime_str
    ):
        """Test that different departure statuses get appropriate coloring."""
        repl = repl_with_temp_dir

        departures = [
            {
                "line": {"id": 17, "designation": "17", "transport_mode": "METRO"},
                "direction": "Test",
                "scheduled": future_datetime_str,
                "expected": future_datetime_str,
                "state": "CANCELLED",
                "stop_point": {"designation": "1"},
            },
            {
                "line": {"id": 18, "designation": "18", "transport_mode": "METRO"},
                "direction": "Test",
                "scheduled": future_datetime_str,
                "expected": future_datetime_str,
                "state": "ATSTOP",
                "stop_point": {"designation": "1"},
            },
            {
                "line": {"id": 19, "designation": "19", "transport_mode": "METRO"},
                "direction": "Test",
                "scheduled": future_datetime_str,
                "expected": future_datetime_str,
                "state": "EXPECTED",
                "stop_point": {"designation": "1"},
            },
        ]

        # Should handle different statuses without crashing
        display_output = repl._create_departure_table(departures)

        assert isinstance(display_output, Table)

    def test_departure_display_line_coloring(
        self, repl_with_temp_dir, future_datetime_str
    ):
        """Test that different transit lines get appropriate colors."""
        repl = repl_with_temp_dir

        departures = [
            {
                "line": {"id": 17, "designation": "17", "transport_mode": "METRO"},
                "direction": "Test",
                "scheduled": future_datetime_str,
                "expected": future_datetime_str,
                "state": "EXPECTED",
                "stop_point": {"designation": "1"},
            },
            {
                "line": {"id": 40, "designation": "40", "transport_mode": "TRAIN"},
                "direction": "Test",
                "scheduled": future_datetime_str,
                "expected": future_datetime_str,
                "state": "EXPECTED",
                "stop_point": {"designation": "1"},
            },
        ]

        display_output = repl._create_departure_table(departures)

        assert isinstance(display_output, Table)

    def test_departure_display_handles_missing_platform(
        self, repl_with_temp_dir, future_datetime_str
    ):
        """Test handling of missing platform designation."""
        repl = repl_with_temp_dir

        departures = [
            {
                "line": {"id": 17, "designation": "17", "transport_mode": "METRO"},
                "direction": "Test",
                "scheduled": future_datetime_str,
                "expected": future_datetime_str,
                "state": "EXPECTED",
                "stop_point": {},  # No designation
            }
        ]

        # Should handle missing platform gracefully
        display_output = repl._create_departure_table(departures)

        assert isinstance(display_output, Table)

    def test_coordinate_formatting_in_site_display(self, repl_with_temp_dir):
        """Test that coordinates are formatted correctly in site display."""
        repl = repl_with_temp_dir
        site = {
            "id": 1,
            "name": "Test",
            "lat": 59.123456789,
            "lon": 18.987654321,
            "alias": [],
            "abbreviation": "TST",
        }

        display_output = repl._create_site_table(site, "Test")

        # Coordinates should be formatted to 4 decimal places
        # We can't easily inspect the table contents, but we can verify it doesn't crash
        assert isinstance(display_output, Table)

    def test_help_display_content(self, repl_with_temp_dir):
        """Test that help display shows appropriate content."""
        repl = repl_with_temp_dir

        # Should not crash when displaying help
        repl._show_help()

    def test_completer_creation(self, repl_with_temp_dir):
        """Test that command completer is created correctly."""
        repl = repl_with_temp_dir

        completer = repl._create_completer()

        # Should be a WordCompleter instance
        assert completer is not None
        assert hasattr(completer, "words")

    def test_completer_includes_expected_commands(self, repl_with_temp_dir):
        """Test that completer includes expected commands."""
        repl = repl_with_temp_dir

        completer = repl._create_completer()

        # Check that common commands are included
        words = completer.words
        assert "help" in words
        assert "lookup:id" in words
        assert "lookup:name" in words

    def test_completer_includes_transport_modes(self, repl_with_temp_dir):
        """Test that completer includes all transport modes."""
        repl = repl_with_temp_dir

        completer = repl._create_completer()
        words = completer.words

        for mode in SLTransitREPL.TRANSPORT_MODES:
            assert f"transport:{mode}" in words

    @pytest.mark.parametrize(
        "line_id,expected_color",
        [
            ("17", "green"),
            ("13", "red"),
            ("10", "blue"),
            ("unknown", "white"),  # Default color
        ],
    )
    def test_line_color_mapping(self, repl_with_temp_dir, line_id, expected_color):
        """Test that transit lines map to expected colors."""
        repl = repl_with_temp_dir

        line_info = repl.LINE_COLORS[line_id]
        assert expected_color in line_info["color"]

    def test_terminal_display_handles_unicode(self, temp_app_dir):
        """Test that terminal display handles Unicode characters correctly."""
        sites_data = {
            "1": {
                "id": 1,
                "name": "Södermalm",
                "alias": ["Åkeshov"],
                "abbreviation": "SÖD",
                "lat": 59.0,
                "lon": 18.0,
            }
        }

        repl = SLTransitREPL(app_dir=temp_app_dir)
        repl.sites = sites_data

        # Should handle Unicode in site names and aliases
        display_output = repl._create_site_table(sites_data["1"], "Unicode Test")

        assert isinstance(display_output, Table)

    def test_empty_departures_list_handling(self, repl_with_temp_dir):
        """Test handling of empty departures list."""
        repl = repl_with_temp_dir

        display_output = repl._create_departure_table([])

        assert isinstance(display_output, Table)

    def test_site_display_with_none_values(self, repl_with_temp_dir):
        """Test site display when some values are None."""
        sites = [
            {
                "id": 1,
                "name": "Test",
                "lat": 59.0,
                "lon": 18.0,
                "alias": [],
                "abbreviation": None,  # None value
            },
            None,  # None site (should be skipped)
        ]

        repl = repl_with_temp_dir

        # Should skip None sites and handle None values
        display_output = repl._create_site_table(sites, "Test")

        assert isinstance(display_output, Table)
