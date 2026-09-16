"""Comprehensive Unit Tests for Nexus 3D Scene Studio CLI."""

from __future__ import annotations

import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

from nexus_3d_scene_studio.cli import (
    _parse_params_arg,
    _resolve_shape,
    build_parser,
    handle_audit,
    handle_generate,
    handle_mcp,
    handle_platform,
    main,
)


class TestCLI(unittest.TestCase):
    """Test suite for Nexus 3D CLI subcommands, arguments, and utilities."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = pathlib.Path(self.temp_dir.name)

    def test_parse_params_arg(self) -> None:
        """Test parameter string parser for JSON and key=value pairs."""
        # JSON syntax
        p1 = _parse_params_arg('{"p": 2, "q": 5, "scale": 1.5, "flag": true}')
        self.assertEqual(p1, {"p": 2, "q": 5, "scale": 1.5, "flag": True})

        # Key=value comma syntax
        p2 = _parse_params_arg("p=3,q=7,major_radius=2.5,wireframe=false")
        self.assertEqual(p2, {"p": 3, "q": 7, "major_radius": 2.5, "wireframe": False})

        # Empty / None
        self.assertEqual(_parse_params_arg(None), {})
        self.assertEqual(_parse_params_arg(""), {})

    def test_resolve_shape(self) -> None:
        """Test shape generator resolution for all supported procedural types."""
        shapes = [
            ("tesseract", {"size": 2.0}),
            ("torus_knot", {"p": 2, "q": 3}),
            ("superquadric", {"s1": 0.5, "s2": 0.5}),
            ("solid", {"solid_type": "octahedron"}),
            ("icosahedron", {"radius": 1.5}),
            ("buckyball", {"radius": 2.0}),
            ("terrain", {"grid_size": 16}),
            ("mobius", {"twists": 1}),
            ("fibonacci", {"count": 100}),
        ]
        for shape_name, params in shapes:
            mesh = _resolve_shape(shape_name, params)
            self.assertIsNotNone(mesh)
            self.assertGreater(len(mesh.vertices), 0)

        with self.assertRaises(ValueError):
            _resolve_shape("invalid_shape_name", {})

    def test_cli_generate_to_file(self) -> None:
        """Test `generate` command writing OBJ, STL, JSON, and HTML to files."""
        # 1. OBJ
        obj_file = self.temp_path / "model.obj"
        exit_code = main(["generate", "torus_knot", "-o", str(obj_file), "-f", "obj", "-p", "p=2,q=3"])
        self.assertEqual(exit_code, 0)
        self.assertTrue(obj_file.exists())
        content = obj_file.read_text(encoding="utf-8")
        self.assertIn("v ", content)
        self.assertIn("f ", content)

        # 2. STL
        stl_file = self.temp_path / "model.stl"
        exit_code = main(["generate", "icosahedron", "-o", str(stl_file), "-f", "stl"])
        self.assertEqual(exit_code, 0)
        self.assertTrue(stl_file.exists())
        content = stl_file.read_text(encoding="utf-8")
        self.assertIn("solid ", content)

        # 3. JSON
        json_file = self.temp_path / "model.json"
        exit_code = main(["generate", "tesseract", "-o", str(json_file), "-f", "json"])
        self.assertEqual(exit_code, 0)
        self.assertTrue(json_file.exists())
        json_data = json.loads(json_file.read_text(encoding="utf-8"))
        self.assertIn("data", json_data)

        # 4. HTML
        html_file = self.temp_path / "model.html"
        exit_code = main(["generate", "terrain", "-o", str(html_file), "-f", "html"])
        self.assertEqual(exit_code, 0)
        self.assertTrue(html_file.exists())
        content = html_file.read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", content)

    def test_cli_generate_stdout(self) -> None:
        """Test `generate` command printing to stdout when -o omitted."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main(["generate", "tetrahedron", "-f", "obj"])
        self.assertEqual(exit_code, 0)
        output = stdout_capture.getvalue()
        self.assertIn("v ", output)
        self.assertIn("f ", output)

    def test_cli_audit_named_shape(self) -> None:
        """Test `audit` command on recognized procedural shape name."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main(["audit", "buckyball"])
        self.assertEqual(exit_code, 0)
        output = stdout_capture.getvalue()
        self.assertIn("Performance Grade", output)
        self.assertIn("Estimated VRAM", output)

    def test_cli_audit_json_flag(self) -> None:
        """Test `audit --json` command produces valid JSON output."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main(["audit", "superquadric", "--json"])
        self.assertEqual(exit_code, 0)
        output = stdout_capture.getvalue()
        parsed = json.loads(output)
        self.assertIn("performance_grade", parsed)
        self.assertIn("vram_bytes", parsed)

    def test_cli_audit_file(self) -> None:
        """Test `audit` on generated OBJ file on disk."""
        obj_file = self.temp_path / "test_knot.obj"
        main(["generate", "torus_knot", "-o", str(obj_file), "-f", "obj"])

        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main(["audit", str(obj_file)])
        self.assertEqual(exit_code, 0)
        output = stdout_capture.getvalue()
        self.assertIn("test_knot", output)
        self.assertIn("Vertices", output)

    def test_cli_mcp_tools_and_config(self) -> None:
        """Test `mcp --tools` and `mcp --config <target>` outputs."""
        # 1. --tools
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main(["mcp", "--tools"])
        self.assertEqual(exit_code, 0)
        tools = json.loads(stdout_capture.getvalue())
        self.assertIsInstance(tools, list)
        self.assertGreaterEqual(len(tools), 8)

        # 2. --config claude
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main(["mcp", "--config", "claude"])
        self.assertEqual(exit_code, 0)
        cfg = json.loads(stdout_capture.getvalue())
        self.assertIn("mcpServers", cfg)

        # 3. --config cursor
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main(["mcp", "--config", "cursor"])
        self.assertEqual(exit_code, 0)
        cfg = json.loads(stdout_capture.getvalue())
        self.assertIn("mcpServers", cfg)

    def test_cli_platform_diagnostics(self) -> None:
        """Test `platform` command."""
        # Text format
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main(["platform"])
        self.assertEqual(exit_code, 0)
        output = stdout_capture.getvalue()
        self.assertIn("OS Platform", output)
        self.assertIn("Python Version", output)

        # JSON format
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main(["platform", "--json"])
        self.assertEqual(exit_code, 0)
        diag = json.loads(stdout_capture.getvalue())
        self.assertIn("platform", diag)
        self.assertIn("cpu_count", diag)

    def test_cli_parser_help_and_version(self) -> None:
        """Test parser creation and help/version flags."""
        parser = build_parser()
        self.assertIsNotNone(parser)

        # main without args prints help and returns 0
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            exit_code = main([])
        self.assertEqual(exit_code, 0)
        self.assertIn("Nexus 3D Scene Studio", stdout_capture.getvalue())


if __name__ == "__main__":
    unittest.main()
