"""Tests for command line interface functionality."""

import sys
from unittest.mock import MagicMock, patch


class TestCommandLineInterface:
    """Test command line argument parsing and execution."""

    def test_execute_query_departure_success(self, repl_with_temp_dir):
        """Test execute_query with valid departure query."""
        repl = repl_with_temp_dir

        # Mock the _get_site_info and _get_departures methods
        with (
            patch.object(repl, "_get_site_info", return_value={"name": "Test Site"}),
            patch.object(repl, "_get_departures") as mock_get_departures,
        ):
            result = repl.execute_query("1002 line:17")

            assert result is True
            mock_get_departures.assert_called_once()
            args, kwargs = mock_get_departures.call_args
            assert args[0] == 1002  # site_id
            assert args[1]["line"] == "17"

    def test_execute_query_lookup_id_success(self, repl_with_temp_dir):
        """Test execute_query with valid lookup:id query."""
        repl = repl_with_temp_dir

        # Mock the _find_site_by_id method
        mock_site = {"id": 1002, "name": "Test Site"}
        with (
            patch.object(repl, "_find_site_by_id", return_value=mock_site),
            patch.object(repl, "_create_site_table") as mock_create_table,
            patch.object(repl.console, "print") as mock_print,
        ):
            result = repl.execute_query("lookup:id 1002")

            assert result is True
            mock_create_table.assert_called_once_with(mock_site, "Site with ID 1002")
            mock_print.assert_called()

    def test_execute_query_lookup_name_success(self, repl_with_temp_dir):
        """Test execute_query with valid lookup:name query."""
        repl = repl_with_temp_dir

        # Mock the _find_sites_by_substring method
        mock_sites = [{"id": 1002, "name": "Central Station"}]
        with (
            patch.object(repl, "_find_sites_by_substring", return_value=mock_sites),
            patch.object(repl, "_create_site_table") as mock_create_table,
            patch.object(repl.console, "print") as mock_print,
        ):
            result = repl.execute_query("lookup:name central")

            assert result is True
            mock_create_table.assert_called_once_with(
                mock_sites, "Sites matching 'central'"
            )
            mock_print.assert_called()

    def test_execute_query_help_command(self, repl_with_temp_dir):
        """Test execute_query with help command."""
        repl = repl_with_temp_dir

        with patch.object(repl, "_show_help") as mock_show_help:
            result = repl.execute_query("help")

            assert result is True
            mock_show_help.assert_called_once()

    def test_execute_query_invalid_query(self, repl_with_temp_dir):
        """Test execute_query with invalid query."""
        repl = repl_with_temp_dir

        with patch.object(repl.console, "print") as mock_print:
            result = repl.execute_query("invalid query format")

            assert result is False
            mock_print.assert_called()
            # Check that error message was printed
            call_args = mock_print.call_args[0][0]
            assert "[red]" in call_args

    def test_execute_query_site_not_found(self, repl_with_temp_dir):
        """Test execute_query when site is not found."""
        repl = repl_with_temp_dir

        with patch.object(repl, "_get_site_info", return_value=None):
            result = repl.execute_query("9999")

            assert result is False

    def test_execute_query_lookup_id_not_found(self, repl_with_temp_dir):
        """Test execute_query with lookup:id for non-existent site."""
        repl = repl_with_temp_dir

        with (
            patch.object(repl, "_find_site_by_id", return_value=None),
            patch.object(repl.console, "print") as mock_print,
        ):
            result = repl.execute_query("lookup:id 9999")

            assert result is False
            mock_print.assert_called()
            # Check that error message was printed
            call_args = mock_print.call_args[0][0]
            assert "No site found with ID" in call_args

    def test_execute_query_lookup_name_not_found(self, repl_with_temp_dir):
        """Test execute_query with lookup:name for non-existent name."""
        repl = repl_with_temp_dir

        with (
            patch.object(repl, "_find_sites_by_substring", return_value=[]),
            patch.object(repl.console, "print") as mock_print,
        ):
            result = repl.execute_query("lookup:name nonexistent")

            assert result is False
            mock_print.assert_called()
            # Check that error message was printed
            call_args = mock_print.call_args[0][0]
            assert "No sites found containing" in call_args

    def test_execute_query_lookup_invalid_id_format(self, repl_with_temp_dir):
        """Test execute_query with lookup:id with invalid ID format."""
        repl = repl_with_temp_dir

        with patch.object(repl.console, "print") as mock_print:
            result = repl.execute_query("lookup:id abc")

            assert result is False
            mock_print.assert_called()
            # Check that error message was printed
            call_args = mock_print.call_args[0][0]
            assert "Invalid ID format" in call_args

    def test_execute_query_with_parameters(self, repl_with_temp_dir):
        """Test execute_query with multiple parameters."""
        repl = repl_with_temp_dir

        with (
            patch.object(repl, "_get_site_info", return_value={"name": "Test Site"}),
            patch.object(repl, "_get_departures") as mock_get_departures,
        ):
            result = repl.execute_query(
                "1002 line:17 direction:1 forecast:30 show_numbers:true debug:true"
            )

            assert result is True
            mock_get_departures.assert_called_once()
            args, kwargs = mock_get_departures.call_args
            assert args[0] == 1002  # site_id
            assert args[1]["line"] == "17"
            assert args[1]["direction"] == "1"
            assert args[1]["forecast"] == "30"
            assert args[2] is True  # show_direction_numbers
            assert args[3] is True  # debug


class TestMainFunctionCommandLineParsing:
    """Test the main() function command line parsing."""

    def test_main_no_arguments_interactive_mode(self):
        """Test main() with no arguments starts interactive mode."""
        from src.sl_transit_repl.main import main

        # Mock sys.argv to simulate no arguments
        with (
            patch.object(sys, "argv", ["script_name"]),
            patch("src.sl_transit_repl.main.SLTransitREPL") as mock_repl_class,
            patch.object(sys, "exit") as mock_exit,
        ):
            mock_repl = MagicMock()
            mock_repl_class.return_value = mock_repl

            main()

            mock_repl_class.assert_called_once_with(app_dir=None)
            mock_repl.run.assert_called_once()
            mock_exit.assert_not_called()

    def test_main_with_query_argument(self):
        """Test main() with query argument executes single query."""
        from src.sl_transit_repl.main import main

        # Mock sys.argv to simulate query argument
        with (
            patch.object(sys, "argv", ["script_name", "1002"]),
            patch("src.sl_transit_repl.main.SLTransitREPL") as mock_repl_class,
            patch.object(sys, "exit") as mock_exit,
        ):
            mock_repl = MagicMock()
            mock_repl.execute_query.return_value = True
            mock_repl_class.return_value = mock_repl

            main()

            mock_repl_class.assert_called_once_with(app_dir=None)
            mock_repl.execute_query.assert_called_once_with("1002")
            mock_repl.run.assert_not_called()
            mock_exit.assert_called_once_with(0)

    def test_main_with_query_argument_failure(self):
        """Test main() with query argument that fails."""
        from src.sl_transit_repl.main import main

        # Mock sys.argv to simulate query argument
        with (
            patch.object(sys, "argv", ["script_name", "invalid"]),
            patch("src.sl_transit_repl.main.SLTransitREPL") as mock_repl_class,
            patch.object(sys, "exit") as mock_exit,
        ):
            mock_repl = MagicMock()
            mock_repl.execute_query.return_value = False
            mock_repl_class.return_value = mock_repl

            main()

            mock_repl_class.assert_called_once_with(app_dir=None)
            mock_repl.execute_query.assert_called_once_with("invalid")
            mock_repl.run.assert_not_called()
            mock_exit.assert_called_once_with(1)

    def test_main_with_app_dir_argument(self):
        """Test main() with app-dir argument."""
        from src.sl_transit_repl.main import main

        # Mock sys.argv to simulate app-dir argument
        with (
            patch.object(sys, "argv", ["script_name", "--app-dir", "/custom/path"]),
            patch("src.sl_transit_repl.main.SLTransitREPL") as mock_repl_class,
            patch.object(sys, "exit") as mock_exit,
        ):
            mock_repl = MagicMock()
            mock_repl_class.return_value = mock_repl

            main()

            mock_repl_class.assert_called_once_with(app_dir="/custom/path")
            mock_repl.run.assert_called_once()
            mock_exit.assert_not_called()

    def test_main_with_both_arguments(self):
        """Test main() with both app-dir and query arguments."""
        from src.sl_transit_repl.main import main

        # Mock sys.argv to simulate both arguments
        with (
            patch.object(
                sys, "argv", ["script_name", "--app-dir", "/custom/path", "1002"]
            ),
            patch("src.sl_transit_repl.main.SLTransitREPL") as mock_repl_class,
            patch.object(sys, "exit") as mock_exit,
        ):
            mock_repl = MagicMock()
            mock_repl.execute_query.return_value = True
            mock_repl_class.return_value = mock_repl

            main()

            mock_repl_class.assert_called_once_with(app_dir="/custom/path")
            mock_repl.execute_query.assert_called_once_with("1002")
            mock_repl.run.assert_not_called()
            mock_exit.assert_called_once_with(0)

    def test_main_keyboard_interrupt(self):
        """Test main() handles KeyboardInterrupt gracefully."""
        from src.sl_transit_repl.main import main

        # Mock sys.argv to simulate no arguments
        with (
            patch.object(sys, "argv", ["script_name"]),
            patch("src.sl_transit_repl.main.SLTransitREPL") as mock_repl_class,
            patch.object(sys, "exit") as mock_exit,
        ):
            mock_repl = MagicMock()
            mock_repl.run.side_effect = KeyboardInterrupt()
            mock_repl_class.return_value = mock_repl

            main()

            mock_repl_class.assert_called_once_with(app_dir=None)
            mock_repl.run.assert_called_once()
            mock_exit.assert_called_once_with(0)

    def test_argument_parser_help_message(self):
        """Test that argument parser provides correct help message."""
        from src.sl_transit_repl.main import main

        # Test that --help argument works correctly
        with (
            patch.object(sys, "argv", ["script_name", "--help"]),
            patch(
                "src.sl_transit_repl.main.argparse.ArgumentParser.print_help"
            ) as mock_print_help,
            patch.object(sys, "exit"),
        ):
            try:
                main()
            except SystemExit:
                pass  # argparse calls sys.exit after printing help

            mock_print_help.assert_called_once()

    def test_argument_parser_handles_complex_queries(self):
        """Test that argument parser correctly handles complex queries with spaces."""
        from src.sl_transit_repl.main import main

        complex_query = "lookup:name stockholm central"

        with (
            patch.object(sys, "argv", ["script_name", complex_query]),
            patch("src.sl_transit_repl.main.SLTransitREPL") as mock_repl_class,
            patch.object(sys, "exit"),
        ):
            mock_repl = MagicMock()
            mock_repl.execute_query.return_value = True
            mock_repl_class.return_value = mock_repl

            main()

            mock_repl.execute_query.assert_called_once_with(complex_query)
