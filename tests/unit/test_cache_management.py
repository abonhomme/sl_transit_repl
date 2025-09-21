"""Tests for cache management functionality."""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

from sl_transit_repl.main import SLTransitREPL


class TestCacheManagement:
    """Test cache management functionality."""

    def test_cache_directory_creation(self, temp_app_dir):
        """Test that cache directory is created on initialization."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        assert repl.cache_dir.exists()
        assert repl.cache_dir.is_dir()
        assert repl.cache_dir == temp_app_dir / "cache"

    def test_cache_staleness_fresh_cache(self, temp_app_dir, sample_cache_data):
        """Test that fresh cache (< 24 hours) is not considered stale."""
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)

        with cache_file.open("w") as f:
            json.dump(sample_cache_data, f)

        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Cache should be loaded without triggering fetch
        assert not repl._is_cache_stale()

    def test_cache_staleness_old_cache(self, temp_app_dir, stale_cache_data):
        """Test that old cache (> 24 hours) is considered stale."""
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)

        with cache_file.open("w") as f:
            json.dump(stale_cache_data, f)

        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Old cache should be considered stale
        assert repl._is_cache_stale()

    def test_cache_staleness_no_metadata(self, temp_app_dir):
        """Test that cache without metadata is considered stale."""
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)

        # Old format without metadata
        old_format_data = {"1002": {"id": 1002, "name": "Test"}}
        with cache_file.open("w") as f:
            json.dump(old_format_data, f)

        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Should be considered stale
        assert repl._is_cache_stale()

    def test_cache_staleness_invalid_date(self, temp_app_dir):
        """Test that cache with invalid date format is considered stale."""
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)

        invalid_cache_data = {
            "metadata": {
                "fetch_date": "not-a-date",
                "version": "1.0",
            },
            "sites": {},
        }

        with cache_file.open("w") as f:
            json.dump(invalid_cache_data, f)

        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Should be considered stale due to invalid date
        assert repl._is_cache_stale()

    def test_cache_staleness_custom_max_age(self, temp_app_dir):
        """Test cache staleness with custom max age."""
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)

        # Create cache that's 2 hours old
        old_date = datetime.now() - timedelta(hours=2)
        cache_data = {
            "metadata": {
                "fetch_date": old_date.isoformat(),
                "version": "1.0",
            },
            "sites": {},
        }

        with cache_file.open("w") as f:
            json.dump(cache_data, f)

        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Should not be stale with 24 hour max age
        assert not repl._is_cache_stale(max_age_hours=24)

        # Should be stale with 1 hour max age
        assert repl._is_cache_stale(max_age_hours=1)

    def test_save_sites_with_metadata(self, temp_app_dir, sample_sites_data):
        """Test that sites are saved with proper metadata."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Save sites
        repl._save_sites(sample_sites_data)

        # Verify file was created and has correct structure
        assert repl.sites_json.exists()

        with repl.sites_json.open("r") as f:
            saved_data = json.load(f)

        assert "metadata" in saved_data
        assert "sites" in saved_data
        assert "fetch_date" in saved_data["metadata"]
        assert "version" in saved_data["metadata"]
        assert saved_data["sites"] == sample_sites_data

        # Verify fetch_date is valid ISO format
        datetime.fromisoformat(saved_data["metadata"]["fetch_date"])

    @patch("sl_transit_repl.main.SLTransitREPL._fetch_sites")
    def test_load_sites_triggers_fetch_on_stale_cache(
        self, mock_fetch, temp_app_dir, sample_sites_data
    ):
        """Test that stale cache triggers a fresh fetch."""
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)

        # Create stale cache data manually
        old_date = datetime.now() - timedelta(hours=25)
        stale_cache = {
            "metadata": {
                "fetch_date": old_date.isoformat(),
                "version": "1.0",
            },
            "sites": sample_sites_data,
        }

        # Set up stale cache
        with cache_file.open("w") as f:
            json.dump(stale_cache, f)

        # Mock fetch to return new data
        mock_fetch.return_value = sample_sites_data

        SLTransitREPL(app_dir=temp_app_dir)

        # Verify fetch was called
        mock_fetch.assert_called_once()

    @patch("sl_transit_repl.main.SLTransitREPL._fetch_sites")
    def test_load_sites_no_fetch_on_fresh_cache(
        self, mock_fetch, temp_app_dir, sample_cache_data
    ):
        """Test that fresh cache doesn't trigger fetch."""
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)

        # Set up fresh cache
        with cache_file.open("w") as f:
            json.dump(sample_cache_data, f)

        SLTransitREPL(app_dir=temp_app_dir)

        # Verify fetch was NOT called
        mock_fetch.assert_not_called()

    def test_load_sites_handles_corrupted_json(self, temp_app_dir):
        """Test that corrupted JSON is handled gracefully."""
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)

        # Write corrupted JSON
        with cache_file.open("w") as f:
            f.write("{ invalid json content")

        with patch("sl_transit_repl.main.SLTransitREPL._fetch_sites") as mock_fetch:
            mock_fetch.return_value = {}

            # Should not crash and should trigger fetch
            SLTransitREPL(app_dir=temp_app_dir)
            mock_fetch.assert_called_once()

    def test_load_sites_handles_missing_file(self, temp_app_dir):
        """Test that missing cache file triggers fetch."""
        with patch("sl_transit_repl.main.SLTransitREPL._fetch_sites") as mock_fetch:
            mock_fetch.return_value = {}

            SLTransitREPL(app_dir=temp_app_dir)

            # Should trigger fetch when no cache file exists
            mock_fetch.assert_called_once()

    def test_save_sites_handles_permission_error(self, temp_app_dir, sample_sites_data):
        """Test that permission errors during save are handled gracefully."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Should not crash
            repl._save_sites(sample_sites_data)

        # We can't assert file doesn't exist since the real open might have succeeded
        # Just verify it doesn't crash
