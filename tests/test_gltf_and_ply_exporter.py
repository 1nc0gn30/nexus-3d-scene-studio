"""Unit tests for glTF 2.0 and ASCII PLY mesh exporters in nexus_3d_scene_studio."""

from __future__ import annotations

import base64
import json
import struct
import unittest
from typing import Any, Dict

from nexus_3d_scene_studio.geometry_engine import (
    MeshData,
    generate_platonic_solid,
    generate_torus_knot,
    generate_procedural_terrain,
)
from nexus_3d_scene_studio.mesh_exporter import MeshExporter
from nexus_3d_scene_studio.mcp_server import MCPServer
from nexus_3d_scene_studio.cli import main


class TestGltfAndPlyExporter(unittest.TestCase):
    """Test suite for glTF 2.0 and ASCII PLY generation and integrity."""

    def setUp(self) -> None:
        self.cube = generate_platonic_solid("cube", radius=2.0)
        self.torus = generate_torus_knot(p=2, q=3, num_points=32, tube_segments=8)
        self.terrain = generate_procedural_terrain(grid_size=8, scale=4.0)

    def test_export_gltf_dict_structure(self) -> None:
        """Verify glTF 2.0 dictionary adheres to official glTF 2.0 schema."""
        gltf = MeshExporter.export_gltf_dict(
            self.cube,
            object_name="test_cube",
            material_name="cube_material",
            metallic=0.2,
            roughness=0.8,
            color=(0.2, 0.6, 0.9, 1.0),
        )

        self.assertIsInstance(gltf, dict)
        self.assertEqual(gltf["asset"]["version"], "2.0")
        self.assertIn("Nexus 3D Scene Studio", gltf["asset"]["generator"])
        self.assertIn("Material 3", gltf["asset"]["copyright"])

        # Hierarchy
        self.assertEqual(gltf["scene"], 0)
        self.assertEqual(len(gltf["scenes"]), 1)
        self.assertEqual(gltf["scenes"][0]["nodes"], [0])
        self.assertEqual(gltf["nodes"][0]["name"], "test_cube")
        self.assertEqual(gltf["nodes"][0]["mesh"], 0)

        # Mesh and Primitives
        mesh_entry = gltf["meshes"][0]
        self.assertEqual(mesh_entry["name"], "test_cube")
        self.assertEqual(len(mesh_entry["primitives"]), 1)
        prim = mesh_entry["primitives"][0]
        self.assertEqual(prim["mode"], 4)  # TRIANGLES
        self.assertIn("POSITION", prim["attributes"])
        self.assertIn("indices", prim)
        self.assertEqual(prim["material"], 0)

        # Material PBR
        mat = gltf["materials"][0]
        self.assertEqual(mat["name"], "cube_material")
        pbr = mat["pbrMetallicRoughness"]
        self.assertAlmostEqual(pbr["metallicFactor"], 0.2)
        self.assertAlmostEqual(pbr["roughnessFactor"], 0.8)
        self.assertEqual(pbr["baseColorFactor"], [0.2, 0.6, 0.9, 1.0])
        self.assertTrue(mat["doubleSided"])

        # Accessors & BufferViews
        accessors = gltf["accessors"]
        pos_acc = accessors[prim["attributes"]["POSITION"]]
        self.assertEqual(pos_acc["type"], "VEC3")
        self.assertEqual(pos_acc["componentType"], 5126)  # FLOAT
        self.assertEqual(pos_acc["count"], len(self.cube.vertices))
        self.assertEqual(len(pos_acc["min"]), 3)
        self.assertEqual(len(pos_acc["max"]), 3)

        idx_acc = accessors[prim["indices"]]
        self.assertEqual(idx_acc["type"], "SCALAR")
        self.assertIn(idx_acc["componentType"], (5123, 5125))  # UNSIGNED_SHORT or UNSIGNED_INT

        # Buffers and Base64 Data URI
        buffers = gltf["buffers"]
        self.assertEqual(len(buffers), 1)
        uri = buffers[0]["uri"]
        self.assertTrue(uri.startswith("data:application/octet-stream;base64,"))
        b64_data = uri.split(",", 1)[1]
        raw_bytes = base64.b64decode(b64_data)
        self.assertEqual(len(raw_bytes), buffers[0]["byteLength"])

    def test_export_gltf_json_string(self) -> None:
        """Test serialized glTF JSON output."""
        json_str = MeshExporter.export_gltf(self.torus, object_name="torus_knot")
        self.assertIsInstance(json_str, str)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["asset"]["version"], "2.0")
        self.assertEqual(parsed["meshes"][0]["name"], "torus_knot")

    def test_export_gltf_with_normals_uvs_and_colors(self) -> None:
        """Test glTF with normals, texture coordinates and vertex colors."""
        mesh = MeshData(
            name="colored_tri",
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            faces=[[0, 1, 2]],
            normals=[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]],
            uvs=[[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
            colors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        )
        gltf = MeshExporter.export_gltf_dict(mesh)
        prim = gltf["meshes"][0]["primitives"][0]
        attrs = prim["attributes"]

        self.assertIn("POSITION", attrs)
        self.assertIn("NORMAL", attrs)
        self.assertIn("TEXCOORD_0", attrs)
        self.assertIn("COLOR_0", attrs)

    def test_export_gltf_empty_mesh_raises(self) -> None:
        """Test exporting an empty mesh raises ValueError."""
        empty_mesh = MeshData(name="empty", vertices=[], faces=[])
        with self.assertRaises(ValueError):
            MeshExporter.export_gltf(empty_mesh)

    def test_export_ply_ascii_structure(self) -> None:
        """Test Stanford ASCII PLY export header and body."""
        ply_str = MeshExporter.export_ply(self.cube, object_name="my_cube")
        self.assertTrue(ply_str.startswith("ply\nformat ascii 1.0\n"))
        self.assertIn("comment Nexus 3D Scene Studio PLY Exporter - my_cube", ply_str)
        self.assertIn(f"element vertex {len(self.cube.vertices)}", ply_str)
        self.assertIn(f"element face {len(self.cube.faces)}", ply_str)
        self.assertIn("property float x\nproperty float y\nproperty float z", ply_str)
        self.assertIn("end_header\n", ply_str)

        lines = ply_str.strip().split("\n")
        end_header_idx = lines.index("end_header")
        data_lines = lines[end_header_idx + 1:]
        self.assertEqual(len(data_lines), len(self.cube.vertices) + len(self.cube.faces))

    def test_export_ply_with_colors_and_normals(self) -> None:
        """Test PLY format includes uchar RGB properties when colors are present."""
        mesh = MeshData(
            name="colored_poly",
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            faces=[[0, 1, 2]],
            normals=[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]],
            colors=[[1.0, 0.5, 0.0], [0.0, 1.0, 0.5], [0.5, 0.0, 1.0]],
        )
        ply_str = MeshExporter.export_ply(mesh)
        self.assertIn("property float nx", ply_str)
        self.assertIn("property uchar red", ply_str)
        self.assertIn("property uchar green", ply_str)
        self.assertIn("property uchar blue", ply_str)

    def test_mcp_server_gltf_and_ply_export(self) -> None:
        """Test MCP Server export_mesh tool with gltf and ply formats."""
        server = MCPServer()
        # 1. glTF via MCP
        res_gltf = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "nexus_export_mesh",
                "arguments": {
                    "shape_type": "tetrahedron",
                    "format": "gltf",
                },
            },
        })
        self.assertNotIn("error", res_gltf)
        gltf_content = res_gltf["result"]["content"][0]["text"]
        gltf_dict = json.loads(gltf_content)
        self.assertEqual(gltf_dict["format"], "gltf")
        self.assertIn("asset", gltf_dict["data"])

        # 2. PLY via MCP
        res_ply = server.handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "nexus_export_mesh",
                "arguments": {
                    "shape_type": "octahedron",
                    "format": "ply",
                },
            },
        })
        self.assertNotIn("error", res_ply)
        ply_content = res_ply["result"]["content"][0]["text"]
        ply_dict = json.loads(ply_content)
        self.assertEqual(ply_dict["format"], "ply")
        self.assertTrue(ply_dict["content"].startswith("ply\n"))

    def test_cli_gltf_and_ply_help_and_export(self) -> None:
        """Test CLI generate command with gltf and ply formats."""
        # Check CLI parser accepts gltf and ply
        from nexus_3d_scene_studio.cli import build_parser
        parser = build_parser()
        args_gltf = parser.parse_args(["generate", "cube", "-f", "gltf"])
        self.assertEqual(args_gltf.format, "gltf")

        args_ply = parser.parse_args(["generate", "cube", "-f", "ply"])
        self.assertEqual(args_ply.format, "ply")


if __name__ == "__main__":
    unittest.main()
