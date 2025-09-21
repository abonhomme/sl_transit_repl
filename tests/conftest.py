"""Pytest configuration and shared fixtures."""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

from sl_transit_repl.main import SLTransitREPL


@pytest.fixture
def temp_app_dir():
    """Create a temporary application directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_sites_data():
    """Sample sites data for testing."""
    return {
        "1002": {
            "id": 1002,
            "name": "Odenplan",
            "alias": ["Odenplan T-bana"],
            "abbreviation": "ODE",
            "lat": 59.342874,
            "lon": 18.049292,
        },
        "9001": {
            "id": 9001,
            "name": "Centralen",
            "alias": ["Stockholm Central", "T-Centralen"],
            "abbreviation": "CEN",
            "lat": 59.331134,
            "lon": 18.058120,
        },
        "9180": {
            "id": 9180,
            "name": "Södermalm",
            "alias": [],
            "abbreviation": "SÖD",
            "lat": 59.317049,
            "lon": 18.073440,
        },
    }


@pytest.fixture
def sample_cache_data(sample_sites_data):
    """Sample cache data with metadata."""
    return {
        "metadata": {
            "fetch_date": datetime.now().isoformat(),
            "version": "1.0",
        },
        "sites": sample_sites_data,
    }


@pytest.fixture
def stale_cache_data(sample_sites_data):
    """Cache data that is older than 24 hours."""
    old_date = datetime.now() - timedelta(hours=25)
    return {
        "metadata": {
            "fetch_date": old_date.isoformat(),
            "version": "1.0",
        },
        "sites": sample_sites_data,
    }


@pytest.fixture
def sample_departures_data():
    """Sample departures API response with current datetime."""
    from datetime import datetime, timedelta

    # Use current time plus a few minutes to avoid past times
    base_time = datetime.now(UTC) + timedelta(minutes=5)
    scheduled_time = base_time.isoformat()
    expected_time = (base_time + timedelta(minutes=2)).isoformat()

    return {
        "departures": [
            {
                "line": {"id": 17, "designation": "17", "transport_mode": "METRO"},
                "direction": "Åkeshov",
                "direction_code": 1,
                "scheduled": scheduled_time,
                "expected": expected_time,
                "state": "EXPECTED",
                "stop_point": {"designation": "2"},
            },
            {
                "line": {"id": 17, "designation": "17", "transport_mode": "METRO"},
                "direction": "Skarpnäck",
                "direction_code": 2,
                "scheduled": scheduled_time,
                "expected": scheduled_time,
                "state": "ATSTOP",
                "stop_point": {"designation": "1"},
            },
        ],
        "stop_deviations": [{"message": "Slower traffic due to signal problems"}],
    }


@pytest.fixture
def future_datetime_str():
    """Generate a future datetime string for testing."""
    from datetime import datetime, timedelta

    future_time = datetime.now(UTC) + timedelta(minutes=10)
    return future_time.isoformat()


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for API calls."""
    return Mock()


@pytest.fixture
def repl_with_temp_dir(temp_app_dir, sample_sites_data):
    """Create a SLTransitREPL instance with temporary directory and sample data."""
    # Create the instance
    repl = SLTransitREPL(app_dir=temp_app_dir)

    # Manually set sites data to avoid API calls
    repl.sites = sample_sites_data
    repl._build_search_indices()

    return repl
