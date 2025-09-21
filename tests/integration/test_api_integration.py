"""Integration tests for API functionality."""

from unittest.mock import Mock, patch

import pytest
import requests

from sl_transit_repl.main import SLTransitREPL


class TestAPIIntegration:
    """Test API integration functionality."""

    @patch("requests.get")
    def test_fetch_sites_success(self, mock_get, temp_app_dir):
        """Test successful sites fetching from API."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"id": 1002, "name": "Odenplan", "lat": 59.342874, "lon": 18.049292},
            {"id": 9001, "name": "Centralen", "lat": 59.331134, "lon": 18.058120},
        ]
        mock_get.return_value = mock_response

        repl = SLTransitREPL(app_dir=temp_app_dir)
        # _fetch_sites is already called during initialization, so sites are loaded
        sites = repl.sites

        # Verify API was called during initialization
        mock_get.assert_called_with(f"{SLTransitREPL.BASE_URL}/sites")

        # Verify response transformation
        assert "1002" in sites
        assert "9001" in sites
        assert sites["1002"]["name"] == "Odenplan"
        assert sites["9001"]["name"] == "Centralen"

    @patch("requests.get")
    def test_fetch_sites_network_error(self, mock_get, temp_app_dir):
        """Test handling of network errors during sites fetch."""
        # Mock network error
        mock_get.side_effect = requests.ConnectionError("Network error")

        repl = SLTransitREPL(app_dir=temp_app_dir)
        sites = repl._fetch_sites()

        # Should return empty dict on error
        assert sites == {}

    @patch("requests.get")
    def test_fetch_sites_http_error(self, mock_get, temp_app_dir):
        """Test handling of HTTP errors during sites fetch."""
        # Mock HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        repl = SLTransitREPL(app_dir=temp_app_dir)
        sites = repl._fetch_sites()

        # Should return empty dict on error
        assert sites == {}

    @patch("requests.get")
    def test_get_departures_success(
        self, mock_get, repl_with_temp_dir, sample_departures_data
    ):
        """Test successful departures fetch."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = sample_departures_data
        mock_get.return_value = mock_response

        repl = repl_with_temp_dir
        site_info = repl.sites["1002"]

        # This method prints to console, so we're mainly testing it doesn't crash
        repl._get_departures(site_id=1002, params={"forecast": 60}, site_info=site_info)

        # Verify API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert f"{SLTransitREPL.BASE_URL}/sites/1002/departures" in call_args[0]

    @patch("requests.get")
    def test_get_departures_with_parameters(
        self, mock_get, repl_with_temp_dir, sample_departures_data
    ):
        """Test departures fetch with additional parameters."""
        mock_response = Mock()
        mock_response.json.return_value = sample_departures_data
        mock_get.return_value = mock_response

        repl = repl_with_temp_dir
        site_info = repl.sites["1002"]

        params = {"forecast": 30, "line": "17", "direction": "1", "transport": "METRO"}

        repl._get_departures(site_id=1002, params=params, site_info=site_info)

        # Verify parameters were passed correctly
        call_args = mock_get.call_args
        assert call_args[1]["params"]["forecast"] == 30
        assert call_args[1]["params"]["line"] == "17"
        assert call_args[1]["params"]["direction"] == "1"
        assert call_args[1]["params"]["transport"] == "METRO"

    @patch("requests.get")
    def test_get_departures_with_custom_headers(
        self, mock_get, repl_with_temp_dir, sample_departures_data
    ):
        """Test departures fetch with custom headers."""
        mock_response = Mock()
        mock_response.json.return_value = sample_departures_data
        mock_get.return_value = mock_response

        repl = repl_with_temp_dir
        site_info = repl.sites["1002"]

        params = {
            "forecast": 60,
            "_custom_header": "test_value",
            "_user_agent": "test_agent",
        }

        repl._get_departures(site_id=1002, params=params, site_info=site_info)

        # Verify headers were set correctly
        call_args = mock_get.call_args
        assert call_args[1]["headers"]["custom-header"] == "test_value"
        assert call_args[1]["headers"]["user-agent"] == "test_agent"

    @patch("requests.get")
    def test_get_departures_cache_busting(
        self, mock_get, repl_with_temp_dir, sample_departures_data
    ):
        """Test that cache busting timestamp is added."""
        mock_response = Mock()
        mock_response.json.return_value = sample_departures_data
        mock_get.return_value = mock_response

        repl = repl_with_temp_dir
        site_info = repl.sites["1002"]

        repl._get_departures(site_id=1002, params={"forecast": 60}, site_info=site_info)

        # Verify cache busting parameter was added
        call_args = mock_get.call_args
        assert "_t" in call_args[1]["params"]
        # Should be a timestamp (numeric string)
        assert call_args[1]["params"]["_t"].isdigit()

    @patch("requests.get")
    def test_get_departures_no_results(self, mock_get, repl_with_temp_dir):
        """Test handling of API response with no departures."""
        # Mock response with no departures
        mock_response = Mock()
        mock_response.json.return_value = {"departures": []}
        mock_get.return_value = mock_response

        repl = repl_with_temp_dir
        site_info = repl.sites["1002"]

        # Should not crash when no departures are found
        repl._get_departures(site_id=1002, params={"forecast": 60}, site_info=site_info)

    @patch("requests.get")
    def test_get_departures_with_deviations(self, mock_get, repl_with_temp_dir):
        """Test handling of departures with service deviations."""
        # Mock response with deviations
        response_data = {
            "departures": [
                {
                    "line": {"id": 17, "designation": "17", "transport_mode": "METRO"},
                    "direction": "Åkeshov",
                    "scheduled": "2024-09-21T14:30:00+02:00",
                    "expected": "2024-09-21T14:32:00+02:00",
                    "state": "EXPECTED",
                    "stop_point": {"designation": "2"},
                }
            ],
            "stop_deviations": [
                {"message": "Slower traffic due to signal problems"},
                {"message": "Alternative route in use"},
            ],
        }

        mock_response = Mock()
        mock_response.json.return_value = response_data
        mock_get.return_value = mock_response

        repl = repl_with_temp_dir
        site_info = repl.sites["1002"]

        # Should handle deviations without crashing
        repl._get_departures(site_id=1002, params={"forecast": 60}, site_info=site_info)

    @patch("requests.get")
    def test_get_departures_network_error(self, mock_get, repl_with_temp_dir):
        """Test handling of network errors during departures fetch."""
        # Mock network error
        mock_get.side_effect = requests.ConnectionError("Network error")

        repl = repl_with_temp_dir
        site_info = repl.sites["1002"]

        # Should not crash on network error
        repl._get_departures(site_id=1002, params={"forecast": 60}, site_info=site_info)

    @patch("requests.get")
    def test_get_departures_debug_mode(
        self, mock_get, repl_with_temp_dir, sample_departures_data
    ):
        """Test that debug mode displays headers."""
        mock_response = Mock()
        mock_response.json.return_value = sample_departures_data
        mock_response.headers = {
            "Content-Type": "application/json",
            "X-Rate-Limit": "100",
        }
        mock_get.return_value = mock_response

        repl = repl_with_temp_dir
        site_info = repl.sites["1002"]

        # Test with debug enabled
        repl._get_departures(
            site_id=1002,
            params={"forecast": 60, "_test_header": "test_value"},
            debug=True,
            site_info=site_info,
        )

        # Debug mode should show headers (we can't easily test console output,
        # but we can verify it doesn't crash)

    @patch("requests.get")
    def test_departures_parameter_filtering(
        self, mock_get, repl_with_temp_dir, sample_departures_data
    ):
        """Test that show_numbers parameter is filtered from API params."""
        mock_response = Mock()
        mock_response.json.return_value = sample_departures_data
        mock_get.return_value = mock_response

        repl = repl_with_temp_dir
        site_info = repl.sites["1002"]

        params = {
            "forecast": 60,
            "show_numbers": "true",  # Should be filtered out
            "line": "17",  # Should be kept
        }

        repl._get_departures(site_id=1002, params=params, site_info=site_info)

        # Verify show_numbers was not passed to API
        call_args = mock_get.call_args
        api_params = call_args[1]["params"]
        assert "show_numbers" not in api_params
        assert "line" in api_params
        assert api_params["line"] == "17"

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access - enable for manual testing")
    def test_real_api_sites_fetch(self, temp_app_dir):
        """Test actual API call to fetch sites (skipped by default)."""
        repl = SLTransitREPL(app_dir=temp_app_dir)
        sites = repl._fetch_sites()

        # Basic validation of real API response
        assert isinstance(sites, dict)
        if sites:  # If API is available
            # Check structure of first site
            first_site = next(iter(sites.values()))
            assert "id" in first_site
            assert "name" in first_site
            assert "lat" in first_site
            assert "lon" in first_site

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires network access - enable for manual testing")
    def test_real_api_departures_fetch(self, temp_app_dir):
        """Test actual API call to fetch departures (skipped by default)."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Use a well-known site ID (T-Centralen)
        site_id = 9001
        params = {"forecast": 60}

        # This will make a real API call
        repl._get_departures(site_id=site_id, params=params)
