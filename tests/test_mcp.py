"""Comprehensive Unit Tests for Nexus 3D Scene Studio MCP Server."""

from __future__ import annotations

import json
import os
import unittest
from typing import Any, Dict

from nexus_3d_scene_studio.mcp_server import (
    MCP_PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    MCPServer,
    generate_mcp_client_config,
)


class TestMCPServer(unittest.TestCase):
    """Test suite for MCP Server tool registration, execution, and JSON-RPC protocol handling."""

    def setUp(self) -> None:
        self.server = MCPServer()

    def test_registered_tools_catalog(self) -> None:
        """Verify all required MCP tools are properly registered with input schemas."""
        tools = self.server.list_tools()
        self.assertGreaterEqual(len(tools), 8)

        tool_names = {t["name"] for t in tools}
        expected_tools = {
            "nexus_generate_tesseract",
            "nexus_generate_torus_knot",
            "nexus_generate_superquadric",
            "nexus_generate_solid",
            "nexus_generate_terrain",
            "nexus_export_mesh",
            "nexus_audit_mesh",
            "nexus_get_diagnostics",
        }
        for expected in expected_tools:
            self.assertIn(expected, tool_names, f"Missing MCP tool: {expected}")

        for tool in tools:
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)
            self.assertEqual(tool["inputSchema"].get("type"), "object")

    def test_generate_tesseract_tool(self) -> None:
        """Test nexus_generate_tesseract tool execution across formats."""
        res_dict = self.server.call_tool("nexus_generate_tesseract", {"size": 2.5, "angle_4d": 0.8, "format": "dict"})
        self.assertIsInstance(res_dict, dict)
        self.assertEqual(len(res_dict["vertices"]), 16)
        self.assertEqual(len(res_dict["edges"]), 32)
        self.assertEqual(len(res_dict["faces"]), 24)

        res_obj = self.server.call_tool("nexus_generate_tesseract", {"format": "obj"})
        self.assertIsInstance(res_obj, str)
        self.assertTrue(res_obj.startswith("# Nexus 3D Scene Studio OBJ Exporter"))

        res_json = self.server.call_tool("nexus_generate_tesseract", {"format": "json"})
        self.assertIsInstance(res_json, dict)
        self.assertIn("data", res_json)
        self.assertIn("attributes", res_json["data"])

    def test_generate_torus_knot_tool(self) -> None:
        """Test nexus_generate_torus_knot tool execution."""
        res = self.server.call_tool("nexus_generate_torus_knot", {
            "p": 2,
            "q": 3,
            "major_radius": 2.0,
            "tube_radius": 0.4,
            "num_points": 60,
            "tube_segments": 12,
            "format": "dict",
        })
        self.assertIsInstance(res, dict)
        self.assertGreater(len(res["vertices"]), 500)
        self.assertGreater(len(res["faces"]), 500)
        self.assertIsNotNone(res.get("normals"))
        self.assertIsNotNone(res.get("uvs"))

    def test_generate_superquadric_tool(self) -> None:
        """Test nexus_generate_superquadric tool with deformations."""
        res = self.server.call_tool("nexus_generate_superquadric", {
            "s1": 0.5,
            "s2": 0.5,
            "rx": 1.5,
            "ry": 1.2,
            "rz": 1.0,
            "pinch": 0.3,
            "taper": 0.2,
            "bend": 0.1,
            "twist": 0.5,
            "seg_u": 16,
            "seg_v": 16,
            "format": "dict",
        })
        self.assertIsInstance(res, dict)
        self.assertEqual(res["name"], "superquadric")
        self.assertGreater(len(res["vertices"]), 100)

    def test_generate_solid_tool(self) -> None:
        """Test nexus_generate_solid tool for Platonic solids and Buckyball."""
        solids = ["tetrahedron", "cube", "octahedron", "dodecahedron", "icosahedron", "buckyball"]
        for s in solids:
            res = self.server.call_tool("nexus_generate_solid", {"solid_type": s, "radius": 2.0, "format": "dict"})
            self.assertIsInstance(res, dict)
            self.assertGreater(len(res["vertices"]), 0)
            self.assertGreater(len(res["faces"]), 0)

    def test_generate_terrain_tool(self) -> None:
        """Test nexus_generate_terrain tool."""
        res = self.server.call_tool("nexus_generate_terrain", {
            "grid_size": 16,
            "scale": 3.0,
            "height_factor": 0.5,
            "octaves": 2,
            "format": "dict",
        })
        self.assertIsInstance(res, dict)
        self.assertEqual(res["name"], "procedural_terrain")
        self.assertEqual(len(res["vertices"]), 17 * 17)
        self.assertIsNotNone(res.get("colors"))

    def test_export_mesh_tool(self) -> None:
        """Test nexus_export_mesh tool for OBJ, STL, JSON, and HTML."""
        # 1. OBJ export
        obj_res = self.server.call_tool("nexus_export_mesh", {
            "format": "obj",
            "shape_type": "icosahedron",
            "shape_params": {"radius": 1.5},
        })
        self.assertEqual(obj_res["format"], "obj")
        self.assertIn("v ", obj_res["content"])
        self.assertIn("f ", obj_res["content"])

        # 2. STL export
        stl_res = self.server.call_tool("nexus_export_mesh", {
            "format": "stl",
            "shape_type": "octahedron",
        })
        self.assertEqual(stl_res["format"], "stl")
        self.assertIn("solid ", stl_res["content"])
        self.assertIn("facet normal", stl_res["content"])

        # 3. HTML export
        html_res = self.server.call_tool("nexus_export_mesh", {
            "format": "html",
            "shape_type": "torus_knot",
            "title": "My Custom Knot",
        })
        self.assertEqual(html_res["format"], "html")
        self.assertIn("<!DOCTYPE html>", html_res["content"])
        self.assertIn("My Custom Knot", html_res["content"])

        # 4. JSON export
        json_res = self.server.call_tool("nexus_export_mesh", {
            "format": "json",
            "shape_type": "tesseract",
        })
        self.assertEqual(json_res["format"], "json")
        self.assertIn("data", json_res["data"])

    def test_audit_mesh_tool(self) -> None:
        """Test nexus_audit_mesh tool."""
        audit = self.server.call_tool("nexus_audit_mesh", {
            "shape_type": "torus_knot",
            "shape_params": {"p": 2, "q": 3, "num_points": 60, "tube_segments": 12},
        })
        self.assertIn("vertex_count", audit)
        self.assertIn("face_count", audit)
        self.assertIn("triangle_count", audit)
        self.assertIn("vram_bytes", audit)
        self.assertIn("performance_grade", audit)
        self.assertIn(audit["performance_grade"], ["A+", "A", "B", "C", "D"])
        self.assertIn("bounding_box", audit)
        self.assertIn("dimensions", audit)

    def test_get_diagnostics_tool(self) -> None:
        """Test nexus_get_diagnostics tool."""
        diag = self.server.call_tool("nexus_get_diagnostics", {})
        self.assertIn("platform", diag)
        self.assertIn("cpu_count", diag)
        self.assertIn("mcp_server", diag)
        self.assertEqual(diag["mcp_server"]["name"], SERVER_NAME)
        self.assertEqual(diag["mcp_server"]["version"], SERVER_VERSION)

    # -----------------------------------------------------------------------
    # JSON-RPC 2.0 Protocol Tests
    # -----------------------------------------------------------------------

    def test_rpc_initialize(self) -> None:
        """Test JSON-RPC initialize request."""
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res.get("jsonrpc"), "2.0")
        self.assertEqual(res.get("id"), 1)
        self.assertIn("result", res)
        result = res["result"]
        self.assertEqual(result.get("protocolVersion"), MCP_PROTOCOL_VERSION)
        self.assertEqual(result.get("serverInfo", {}).get("name"), SERVER_NAME)
        self.assertIn("tools", result.get("capabilities", {}))

    def test_rpc_ping(self) -> None:
        """Test JSON-RPC ping request."""
        req = {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "ping",
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res.get("id"), 42)
        self.assertEqual(res.get("result"), {})

    def test_rpc_tools_list(self) -> None:
        """Test JSON-RPC tools/list request."""
        req = {
            "jsonrpc": "2.0",
            "id": "list-1",
            "method": "tools/list",
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res.get("id"), "list-1")
        tools = res.get("result", {}).get("tools", [])
        self.assertGreaterEqual(len(tools), 8)

    def test_rpc_tools_call_success(self) -> None:
        """Test JSON-RPC tools/call request execution."""
        req = {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {
                "name": "nexus_generate_tesseract",
                "arguments": {"size": 2.0, "format": "dict"},
            },
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res.get("id"), 100)
        self.assertIn("result", res)
        self.assertFalse(res["result"].get("isError"))
        content = res["result"].get("content", [])
        self.assertGreaterEqual(len(content), 1)
        self.assertEqual(content[0].get("type"), "text")
        parsed_output = json.loads(content[0]["text"])
        self.assertIn("vertices", parsed_output)
        self.assertEqual(len(parsed_output["vertices"]), 16)

    def test_rpc_tools_call_unknown_tool(self) -> None:
        """Test JSON-RPC tools/call with unknown tool name returns error."""
        req = {
            "jsonrpc": "2.0",
            "id": 101,
            "method": "tools/call",
            "params": {
                "name": "non_existent_tool",
                "arguments": {},
            },
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertIn("error", res)
        self.assertEqual(res["error"]["code"], -32601)

    def test_rpc_unknown_method(self) -> None:
        """Test JSON-RPC request with unknown method returns -32601."""
        req = {
            "jsonrpc": "2.0",
            "id": 102,
            "method": "custom/unknown_method",
        }
        res = self.server.handle_request(req)
        self.assertIsNotNone(res)
        self.assertIn("error", res)
        self.assertEqual(res["error"]["code"], -32601)

    def test_rpc_notification_ignored(self) -> None:
        """Test JSON-RPC notification (no id) returns None."""
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        res = self.server.handle_request(notif)
        self.assertIsNone(res)

    # -----------------------------------------------------------------------
    # Client Config Generation Tests
    # -----------------------------------------------------------------------

    def test_client_config_generation(self) -> None:
        """Test MCP client configuration generation across all supported targets."""
        clients = ["claude", "cursor", "cline", "zed", "generic"]
        for c in clients:
            cfg = generate_mcp_client_config(client_name=c, python_path="/usr/bin/python3", project_root="/workspace/repo")
            self.assertIsInstance(cfg, dict)
            if c in ("claude", "cursor", "cline"):
                self.assertIn("mcpServers", cfg)
                self.assertIn(SERVER_NAME, cfg["mcpServers"])
                self.assertEqual(cfg["mcpServers"][SERVER_NAME]["command"], "/usr/bin/python3")
            elif c == "zed":
                self.assertIn("context_servers", cfg)
                self.assertIn(SERVER_NAME, cfg["context_servers"])
            elif c == "generic":
                self.assertEqual(cfg["name"], SERVER_NAME)
                self.assertEqual(cfg["transport"], "stdio")


if __name__ == "__main__":
    unittest.main()
