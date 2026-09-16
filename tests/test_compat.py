"""Unit tests for nexus_3d_scene_studio.compat module."""

import os
import pathlib
import sys
import tempfile
import unittest
from pathlib import Path

from nexus_3d_scene_studio.compat import (
    PlatformInfo,
    atomic_write_bytes,
    atomic_write_text,
    ensure_utf8,
    get_platform_info,
    get_system_diagnostics,
    is_linux,
    is_macos,
    is_termux,
    is_windows,
    normalize_path,
    open_in_browser,
    setup_utf8_console,
    to_posix_path,
)


class TestCompat(unittest.TestCase):
    """Test suite for cross-platform compatibility abstractions."""

    def test_platform_detection(self) -> None:
        """Verify platform detection functions return consistent booleans."""
        lin = is_linux()
        mac = is_macos()
        win = is_windows()
        term = is_termux()

        self.assertIsInstance(lin, bool)
        self.assertIsInstance(mac, bool)
        self.assertIsInstance(win, bool)
        self.assertIsInstance(term, bool)

        info = get_platform_info()
        self.assertIsInstance(info, PlatformInfo)
        self.assertTrue(len(info.os_name) > 0)
        self.assertTrue(len(info.architecture) > 0)
        self.assertTrue(len(info.python_version) > 0)
        d = info.to_dict()
        self.assertIn("is_linux", d)
        self.assertIn("is_64bit", d)

    def test_setup_utf8_console(self) -> None:
        """Verify UTF-8 console configuration executes cleanly."""
        res = setup_utf8_console()
        self.assertIsInstance(res, bool)

    def test_ensure_utf8(self) -> None:
        """Test Unicode string conversion and byte decoding."""
        raw_str = "Nexus 3D Studio 🚀 \u03c0 \u221e"
        self.assertEqual(ensure_utf8(raw_str), raw_str)

        raw_bytes = "Hypercube 4D 📐".encode("utf-8")
        self.assertEqual(ensure_utf8(raw_bytes), "Hypercube 4D 📐")

        invalid_bytes = b"Test \xff\xfe invalid"
        decoded = ensure_utf8(invalid_bytes)
        self.assertIn("Test", decoded)

    def test_to_posix_path(self) -> None:
        """Verify path normalization to POSIX forward slashes."""
        win_path = r"C:\Users\Developer\nexus\scene.obj"
        posix_out = to_posix_path(win_path)
        self.assertEqual(posix_out, "C:/Users/Developer/nexus/scene.obj")

        p = Path("src/nexus_3d_scene_studio/compat.py")
        self.assertNotIn("\\", to_posix_path(p))

    def test_normalize_path(self) -> None:
        """Test path resolution and expansion."""
        p = normalize_path(".")
        self.assertTrue(p.is_absolute())
        self.assertTrue(p.exists())

    def test_atomic_write_text(self) -> None:
        """Verify atomic text file writing and parent directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "subfolder" / "atomic_test.txt"
            content = "Nexus Geometry Engine v1.0.0\nLine 2 \u2728"

            written_path = atomic_write_text(target, content)
            self.assertTrue(written_path.exists())
            self.assertEqual(written_path.read_text(encoding="utf-8"), content)

            # Test atomic overwrite
            new_content = "Overwritten content safely"
            atomic_write_text(target, new_content)
            self.assertEqual(target.read_text(encoding="utf-8"), new_content)

    def test_atomic_write_bytes(self) -> None:
        """Verify atomic binary file writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "binary_data.bin"
            data = b"\x00\x01\x02\x03\x04\xfe\xff"

            written_path = atomic_write_bytes(target, data)
            self.assertTrue(written_path.exists())
            self.assertEqual(written_path.read_bytes(), data)

    def test_open_in_browser(self) -> None:
        """Verify browser opening helper function signature and safe invocation."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            f.write(b"<html><body>Test</body></html>")
            f_path = f.name

        try:
            # We don't want to actually pop up a window in automated tests unless supported,
            # but testing the function executes without unhandled exceptions
            res = open_in_browser(f_path, background=True)
            self.assertIsInstance(res, bool)
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)

    def test_get_system_diagnostics(self) -> None:
        """Verify runtime diagnostics dictionary metrics."""
        diag = get_system_diagnostics()
        self.assertIn("platform", diag)
        self.assertIn("cpu_count", diag)
        self.assertIn("working_directory", diag)
        self.assertIn("temp_directory", diag)
        self.assertIn("stdio_encoding", diag)
        self.assertGreaterEqual(diag["cpu_count"], 1)


if __name__ == "__main__":
    unittest.main()
