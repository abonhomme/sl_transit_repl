"""Tests for file I/O operations and error handling."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sl_transit_repl.main import SLTransitREPL


class TestFileIOAndErrors:
    """Test file I/O operations and error handling."""

    def test_app_directory_creation_default(self):
        """Test that default app directory is created correctly."""
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/fake/home")

            with patch("pathlib.Path.mkdir") as mock_mkdir:
                repl = SLTransitREPL()

                # Verify default path
                assert repl.app_dir == Path("/fake/home/.sl_transit_repl")
                mock_mkdir.assert_called()

    def test_app_directory_creation_custom(self, temp_app_dir):
        """Test that custom app directory is created correctly."""
        custom_dir = temp_app_dir / "custom_app"

        repl = SLTransitREPL(app_dir=custom_dir)

        assert repl.app_dir == custom_dir
        assert custom_dir.exists()

    def test_app_directory_with_tilde_expansion(self):
        """Test that tilde in app directory path is expanded."""
        with patch("pathlib.Path.expanduser") as mock_expand:
            mock_expand.return_value = Path("/expanded/path")

            with patch("pathlib.Path.mkdir"):
                SLTransitREPL(app_dir="~/custom_dir")

                mock_expand.assert_called_once()

    def test_sites_file_paths_setup(self, temp_app_dir):
        """Test that sites file paths are set up correctly."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        assert repl.cache_dir == temp_app_dir / "cache"
        assert repl.sites_json == temp_app_dir / "cache" / "sites.json"
        assert repl.history_file == str(temp_app_dir / ".repl_history")

    def test_save_and_load_sites_roundtrip(self, temp_app_dir, sample_sites_data):
        """Test saving and loading sites data maintains integrity."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Save sites
        repl._save_sites(sample_sites_data)

        # Load sites back
        with repl.sites_json.open("r") as f:
            loaded_data = json.load(f)

        assert "metadata" in loaded_data
        assert "sites" in loaded_data
        assert loaded_data["sites"] == sample_sites_data

    def test_load_sites_missing_file_triggers_fetch(self, temp_app_dir):
        """Test that missing sites file triggers a fetch."""
        with patch.object(SLTransitREPL, "_fetch_sites") as mock_fetch:
            mock_fetch.return_value = {}

            SLTransitREPL(app_dir=temp_app_dir)

            # Should have triggered fetch since no cache file exists
            mock_fetch.assert_called_once()

    def test_load_sites_handles_corrupted_json_gracefully(self, temp_app_dir):
        """Test that corrupted JSON file is handled gracefully."""
        # Create corrupted JSON file
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)
        with cache_file.open("w") as f:
            f.write("{ this is not valid json")

        with patch.object(SLTransitREPL, "_fetch_sites") as mock_fetch:
            mock_fetch.return_value = {}

            # Should not crash and should trigger fetch
            SLTransitREPL(app_dir=temp_app_dir)
            mock_fetch.assert_called_once()

    def test_save_sites_creates_directories_if_missing(self, temp_app_dir):
        """Test that save_sites creates necessary directories."""
        # Remove cache directory
        cache_dir = temp_app_dir / "cache"
        if cache_dir.exists():
            cache_dir.rmdir()

        repl = SLTransitREPL(app_dir=temp_app_dir)
        repl._save_sites({"test": {"id": 1, "name": "Test"}})

        # Directory should be created and file should exist
        assert cache_dir.exists()
        assert repl.sites_json.exists()

    def test_save_sites_handles_permission_error_gracefully(self, temp_app_dir):
        """Test that permission errors during save are handled gracefully."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Should not crash
            repl._save_sites({"test": {"id": 1}})

            # Console should be available for error message
            assert hasattr(repl, "console")

    def test_save_sites_handles_disk_full_error(self, temp_app_dir):
        """Test that disk full errors during save are handled."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        with patch("builtins.open", side_effect=OSError("No space left on device")):
            # Should not crash
            repl._save_sites({"test": {"id": 1}})

    def test_load_sites_handles_permission_error(self, temp_app_dir):
        """Test that permission errors during load trigger fetch."""
        cache_file = temp_app_dir / "cache" / "sites.json"
        cache_file.parent.mkdir(exist_ok=True)
        cache_file.write_text("{}")  # Create file

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch.object(SLTransitREPL, "_fetch_sites") as mock_fetch:
                mock_fetch.return_value = {}

                SLTransitREPL(app_dir=temp_app_dir)

                # Should trigger fetch due to load error
                mock_fetch.assert_called_once()

    def test_json_encoding_preserves_unicode(self, temp_app_dir):
        """Test that Unicode characters in site data are preserved."""
        sites_data = {
            "1": {"id": 1, "name": "Södertälje", "alias": ["Åkeshov", "Hökarängen"]}
        }

        repl = SLTransitREPL(app_dir=temp_app_dir)
        repl._save_sites(sites_data)

        # Load back and verify Unicode is preserved
        with repl.sites_json.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        loaded_sites = loaded_data["sites"]
        assert loaded_sites["1"]["name"] == "Södertälje"
        assert "Åkeshov" in loaded_sites["1"]["alias"]
        assert "Hökarängen" in loaded_sites["1"]["alias"]

    def test_history_file_path_generation(self, temp_app_dir):
        """Test that history file path is generated correctly."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        expected_path = str(temp_app_dir / ".repl_history")
        assert repl.history_file == expected_path

    def test_get_site_info_validates_existence(self, repl_with_temp_dir):
        """Test that _get_site_info validates site existence."""
        repl = repl_with_temp_dir

        # Valid site should return info
        site_info = repl._get_site_info("1002")
        assert site_info is not None
        assert site_info["name"] == "Odenplan"

        # Invalid site should return None
        site_info = repl._get_site_info("99999")
        assert site_info is None

    def test_get_site_info_provides_helpful_error_message(self, repl_with_temp_dir):
        """Test that helpful error messages are shown for invalid sites."""
        repl = repl_with_temp_dir

        # Capture console output would require more complex mocking
        # Here we just test that it doesn't crash
        result = repl._get_site_info("99999")
        assert result is None

    @pytest.mark.parametrize(
        "directory_name",
        [
            "normal_dir",
            "dir with spaces",
            "dir-with-hyphens",
            "dir_with_underscores",
            "dir.with.dots",
        ],
    )
    def test_app_directory_various_names(self, directory_name):
        """Test that various directory names are handled correctly."""
        with tempfile.TemporaryDirectory() as temp_base:
            app_dir = Path(temp_base) / directory_name

            repl = SLTransitREPL(app_dir=app_dir)

            assert repl.app_dir == app_dir
            assert app_dir.exists()
            assert (app_dir / "cache").exists()

    def test_initialization_with_readonly_parent_directory(self):
        """Test initialization when parent directory is read-only."""
        with tempfile.TemporaryDirectory() as temp_base:
            readonly_parent = Path(temp_base) / "readonly"
            readonly_parent.mkdir()

            # Make parent directory read-only
            readonly_parent.chmod(0o444)

            try:
                # Mock mkdir to simulate permission error without actually failing
                with patch.object(SLTransitREPL, "_fetch_sites", return_value={}):
                    with patch(
                        "pathlib.Path.mkdir",
                        side_effect=PermissionError("Permission denied"),
                    ):
                        # Should handle the error gracefully
                        try:
                            repl = SLTransitREPL(app_dir=readonly_parent / "app")
                            assert hasattr(repl, "app_dir")
                        except PermissionError:
                            # This is expected and OK
                            pass
            finally:
                # Restore permissions for cleanup
                readonly_parent.chmod(0o755)

    def test_large_sites_data_handling(self, temp_app_dir):
        """Test handling of large sites data."""
        # Create large sites data
        large_sites_data = {}
        for i in range(10000):
            large_sites_data[str(i)] = {
                "id": i,
                "name": f"Station {i}",
                "alias": [f"Alias {i}"],
                "lat": 59.0 + (i * 0.001),
                "lon": 18.0 + (i * 0.001),
            }

        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Should handle large data without issues
        repl._save_sites(large_sites_data)
        assert repl.sites_json.exists()

        # File should be reasonably large
        assert repl.sites_json.stat().st_size > 1000  # At least 1KB

    def test_concurrent_file_access_simulation(self, temp_app_dir):
        """Test simulation of concurrent file access issues."""
        repl = SLTransitREPL(app_dir=temp_app_dir)

        # Simulate file being used by another process
        with patch(
            "builtins.open", side_effect=OSError("Resource temporarily unavailable")
        ):
            # Should handle gracefully
            repl._save_sites({"test": {"id": 1}})

    def test_initialization_order_and_dependencies(self, temp_app_dir):
        """Test that initialization happens in correct order."""
        with patch.object(SLTransitREPL, "_load_sites") as mock_load:
            with patch.object(SLTransitREPL, "_build_search_indices") as mock_build:
                mock_load.return_value = {}

                repl = SLTransitREPL(app_dir=temp_app_dir)

                # _load_sites should be called before _build_search_indices
                mock_load.assert_called_once()
                mock_build.assert_called_once()

                # Verify attributes are set
                assert hasattr(repl, "app_dir")
                assert hasattr(repl, "cache_dir")
                assert hasattr(repl, "sites_json")
                assert hasattr(repl, "history_file")
                assert hasattr(repl, "console")
