"""Tests for Nexus 3D Scene Studio production examples, viewers, MCP configs, and docs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

# Repository Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
PROCEDURAL_DIR = EXAMPLES_DIR / "procedural-shapes"
VIEWERS_DIR = EXAMPLES_DIR / "standalone-viewers"
MCP_DIR = EXAMPLES_DIR / "mcp-clients"
DOCS_DIR = REPO_ROOT / "docs"
PUBLIC_DIR = REPO_ROOT / "public"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


class TestProceduralGallery:
    """Test suite for procedural geometry generators and gallery export."""

    def test_gallery_script_execution(self, tmp_path):
        """Test that generate_gallery.py runs successfully and exports all 7 shapes."""
        script_path = PROCEDURAL_DIR / "generate_gallery.py"
        assert script_path.is_file(), f"Gallery script missing at {script_path}"

        cmd = [sys.executable, str(script_path), "--output-dir", str(tmp_path)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"Script failed with stderr:\n{res.stderr}\nstdout:\n{res.stdout}"

        expected_shapes = [
            "tesseract_4d",
            "torus_knot",
            "superquadric",
            "fibonacci_sphere",
            "buckyball",
            "mobius_strip",
            "terrain_heightmap",
        ]

        for shape in expected_shapes:
            obj_file = tmp_path / f"{shape}.obj"
            stl_file = tmp_path / f"{shape}.stl"

            assert obj_file.is_file(), f"Missing expected OBJ file: {obj_file}"
            assert obj_file.stat().st_size > 100, f"OBJ file too small: {obj_file}"

            assert stl_file.is_file(), f"Missing expected STL file: {stl_file}"
            assert stl_file.stat().st_size > 100, f"STL file too small: {stl_file}"

    def test_pregenerated_sample_files_exist(self):
        """Verify pre-generated sample OBJ and STL models are present in examples/."""
        expected_shapes = [
            "tesseract_4d",
            "torus_knot",
            "superquadric",
            "fibonacci_sphere",
            "buckyball",
            "mobius_strip",
            "terrain_heightmap",
        ]
        for shape in expected_shapes:
            obj = PROCEDURAL_DIR / f"{shape}.obj"
            stl = PROCEDURAL_DIR / f"{shape}.stl"
            assert obj.is_file(), f"Sample model {obj.name} missing"
            assert stl.is_file(), f"Sample model {stl.name} missing"

    def test_obj_file_syntax_and_integrity(self):
        """Verify OBJ files comply with Wavefront OBJ 3D standard."""
        torus_obj = PROCEDURAL_DIR / "torus_knot.obj"
        assert torus_obj.is_file()
        content = torus_obj.read_text(encoding="utf-8")

        lines = content.splitlines()
        v_lines = [l for l in lines if l.startswith("v ")]
        vn_lines = [l for l in lines if l.startswith("vn ")]
        f_lines = [l for l in lines if l.startswith("f ")]

        assert len(v_lines) > 500, "Torus knot should have over 500 vertices"
        assert len(f_lines) > 500, "Torus knot should have over 500 faces"

        # Check vertex format
        for v in v_lines[:20]:
            parts = v.split()
            assert len(parts) == 4
            float(parts[1]), float(parts[2]), float(parts[3])

    def test_stl_file_syntax_and_integrity(self):
        """Verify STL files comply with ASCII stereolithography standard."""
        bucky_stl = PROCEDURAL_DIR / "buckyball.stl"
        assert bucky_stl.is_file()
        content = bucky_stl.read_text(encoding="utf-8")

        lines = [l.strip() for l in content.splitlines() if l.strip()]
        assert lines[0].startswith("solid"), "STL must start with 'solid'"
        assert lines[-1].startswith("endsolid"), "STL must end with 'endsolid'"

        facet_count = sum(1 for l in lines if l.startswith("facet normal"))
        vertex_count = sum(1 for l in lines if l.startswith("vertex"))
        assert facet_count > 0, "STL must contain facets"
        assert vertex_count == facet_count * 3, "Each facet must have exactly 3 vertices"


class TestStandaloneViewers:
    """Test suite for standalone HTML 3D viewers."""

    def test_tesseract_viewer_html(self):
        """Verify 4D Tesseract viewer HTML structure and WebGL components."""
        viewer = VIEWERS_DIR / "tesseract_viewer.html"
        assert viewer.is_file(), "Tesseract viewer HTML is missing"
        html = viewer.read_text(encoding="utf-8")

        assert "<!DOCTYPE html>" in html
        assert "<canvas" in html
        assert "three.js" in html.lower() or "three.min.js" in html.lower()
        assert "Tesseract" in html
        assert "Google Material" in html or "google-blue" in html or "Google" in html

    def test_torus_knot_viewer_html(self):
        """Verify Torus Knot viewer HTML structure and WebGL components."""
        viewer = VIEWERS_DIR / "torus_knot_viewer.html"
        assert viewer.is_file(), "Torus knot viewer HTML is missing"
        html = viewer.read_text(encoding="utf-8")

        assert "<!DOCTYPE html>" in html
        assert "<canvas" in html
        assert "TorusKnot" in html or "Torus Knot" in html
        assert "telemetry" in html.lower()


class TestMcpClientConfigs:
    """Test suite for MCP client presets."""

    def test_claude_desktop_config(self):
        """Verify Claude Desktop MCP configuration JSON validity."""
        cfg_path = MCP_DIR / "claude_desktop_config.json"
        assert cfg_path.is_file()
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert "mcpServers" in data
        assert "nexus3d" in data["mcpServers"]
        assert "command" in data["mcpServers"]["nexus3d"]
        assert "args" in data["mcpServers"]["nexus3d"]

    def test_cursor_mcp_config(self):
        """Verify Cursor MCP configuration JSON validity."""
        cfg_path = MCP_DIR / "cursor_mcp.json"
        assert cfg_path.is_file()
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert "mcpServers" in data
        assert "nexus-3d-scene-studio" in data["mcpServers"]

    def test_cline_mcp_config(self):
        """Verify Cline MCP configuration JSON validity."""
        cfg_path = MCP_DIR / "cline_mcp.json"
        assert cfg_path.is_file()
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert "mcpServers" in data
        assert "nexus-3d-studio" in data["mcpServers"]

    def test_zed_settings_config(self):
        """Verify Zed MCP configuration JSON validity."""
        cfg_path = MCP_DIR / "zed_settings.json"
        assert cfg_path.is_file()
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert "context_servers" in data
        assert "nexus-3d" in data["context_servers"]


class TestStudioPublicApp:
    """Test suite for public/index.html Nexus 3D Studio app."""

    def test_public_index_html_structure(self):
        """Verify Nexus 3D Studio web application."""
        index_file = PUBLIC_DIR / "index.html"
        assert index_file.is_file(), "public/index.html is missing"
        html = index_file.read_text(encoding="utf-8")

        # Check MD3 branding & tokens
        assert "Nexus 3D Studio" in html
        assert "#1a73e8" in html # Material Blue
        assert "google-dots" in html # 4-dots accent branding
        assert "studio-canvas" in html # 3D WebGL Canvas

        # Check Primitives
        assert "Tesseract" in html
        assert "Torus Knot" in html
        assert "Superquadric" in html
        assert "Fibonacci" in html
        assert "Buckyball" in html
        assert "Möbius" in html or "Mobius" in html
        assert "Terrain" in html

        # Check MCP and Exporters
        assert "modal-mcp" in html
        assert "exportOBJ" in html
        assert "exportSTL" in html


class TestDocumentationAndWorkflows:
    """Test suite verifying documentation and CI/CD pipelines."""

    def test_docs_exist_and_populated(self):
        """Verify mathematical and MCP documentation are complete."""
        math_doc = DOCS_DIR / "PROCEDURAL_GEOMETRY_MATH.md"
        export_doc = DOCS_DIR / "EXPORT_FORMATS_SPEC.md"
        mcp_doc = DOCS_DIR / "MCP_GUIDE.md"
        readme = REPO_ROOT / "README.md"

        for doc in [math_doc, export_doc, mcp_doc, readme]:
            assert doc.is_file(), f"Documentation file {doc.name} missing"
            assert doc.stat().st_size > 1000, f"Documentation file {doc.name} is too brief"

    def test_github_workflows_exist(self):
        """Verify GitHub Actions CI and Release workflows."""
        ci_yml = WORKFLOWS_DIR / "ci.yml"
        release_yml = WORKFLOWS_DIR / "release.yml"

        assert ci_yml.is_file(), "CI workflow missing"
        assert release_yml.is_file(), "Release workflow missing"

        ci_content = ci_yml.read_text(encoding="utf-8")
        assert "matrix:" in ci_content
        assert "ubuntu-latest" in ci_content
        assert "macos-latest" in ci_content
        assert "windows-latest" in ci_content
        assert "3.13" in ci_content
