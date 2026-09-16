"""Unit tests for nexus_3d_scene_studio.mesh_exporter module."""

import json
import unittest

from nexus_3d_scene_studio.geometry_engine import (
    MeshData,
    generate_platonic_solid,
    generate_procedural_terrain,
    generate_torus_knot,
)
from nexus_3d_scene_studio.mesh_exporter import MeshExporter


class TestMeshExporter(unittest.TestCase):
    """Test suite for 3D mesh exporters (OBJ, MTL, STL, Three.js JSON, Standalone HTML)."""

    def setUp(self) -> None:
        """Set up test meshes."""
        self.cube_mesh = generate_platonic_solid(solid_type="cube", radius=2.0)
        self.knot_mesh = generate_torus_knot(
            p=2, q=3, major_radius=1.5, tube_radius=0.3, num_points=32, tube_segments=8
        )
        self.terrain_mesh = generate_procedural_terrain(grid_size=8, scale=3.0, height_factor=0.5)

    def test_export_obj(self) -> None:
        """Verify Wavefront OBJ string generation."""
        obj_text = MeshExporter.export_obj(self.cube_mesh, object_name="test_cube")

        self.assertIn("# Nexus 3D Scene Studio OBJ Exporter", obj_text)
        self.assertIn("o test_cube", obj_text)
        self.assertIn("v ", obj_text)
        self.assertIn("f ", obj_text)

        # Test terrain with vertex colors
        terrain_obj = MeshExporter.export_obj(self.terrain_mesh, object_name="terrain")
        self.assertIn("o terrain", terrain_obj)
        self.assertIn("vt ", terrain_obj)
        self.assertIn("vn ", terrain_obj)

        # Verify 1-based indexing in faces (no 0 indices)
        for line in terrain_obj.splitlines():
            if line.startswith("f "):
                tokens = line.split()[1:]
                for token in tokens:
                    v_idx = int(token.split("/")[0])
                    self.assertGreater(v_idx, 0)

    def test_export_mtl(self) -> None:
        """Verify MTL material definitions."""
        mtl_text = MeshExporter.export_mtl(
            material_name="cyber_gold",
            diffuse=(0.95, 0.75, 0.2),
            specular=(1.0, 1.0, 0.9),
            roughness=0.15,
        )

        self.assertIn("newmtl cyber_gold", mtl_text)
        self.assertIn("Kd 0.950000 0.750000 0.200000", mtl_text)
        self.assertIn("Ks 1.000000 1.000000 0.900000", mtl_text)
        self.assertIn("Ns ", mtl_text)
        self.assertIn("illum 2", mtl_text)

    def test_export_ascii_stl(self) -> None:
        """Verify ASCII STL solid syntax and triangulation."""
        stl_text = MeshExporter.export_ascii_stl(self.cube_mesh, solid_name="nexus_cube")

        self.assertTrue(stl_text.startswith("solid nexus_cube"))
        self.assertIn("facet normal", stl_text)
        self.assertIn("outer loop", stl_text)
        self.assertIn("vertex", stl_text)
        self.assertIn("endloop", stl_text)
        self.assertIn("endfacet", stl_text)
        self.assertTrue(stl_text.strip().endswith("endsolid nexus_cube"))

        # Test knot STL
        knot_stl = MeshExporter.export_ascii_stl(self.knot_mesh, solid_name="torus_knot")
        self.assertIn("solid torus_knot", knot_stl)

    def test_export_threejs_json(self) -> None:
        """Verify Three.js BufferGeometry JSON structure."""
        three_dict = MeshExporter.export_threejs_json(self.terrain_mesh)

        self.assertIn("metadata", three_dict)
        self.assertEqual(three_dict["metadata"]["type"], "BufferGeometry")
        self.assertIn("data", three_dict)
        self.assertIn("attributes", three_dict["data"])

        attrs = three_dict["data"]["attributes"]
        self.assertIn("position", attrs)
        self.assertEqual(attrs["position"]["itemSize"], 3)
        self.assertIn("normal", attrs)
        self.assertIn("uv", attrs)
        self.assertIn("color", attrs)

        self.assertIn("index", three_dict["data"])
        self.assertGreater(len(three_dict["data"]["index"]["array"]), 0)

        # Verify valid JSON serializability
        json_str = json.dumps(three_dict)
        self.assertIsInstance(json_str, str)
        self.assertGreater(len(json_str), 100)

    def test_export_standalone_html(self) -> None:
        """Verify self-contained 3D WebGL HTML application export."""
        html_doc = MeshExporter.export_standalone_html(
            self.knot_mesh,
            title="Nexus Torus Knot Viewer",
            theme="dark",
        )

        self.assertIn("<!DOCTYPE html>", html_doc)
        self.assertIn("<title>Nexus Torus Knot Viewer</title>", html_doc)
        self.assertIn("three.min.js", html_doc)
        self.assertIn("OrbitControls.js", html_doc)
        self.assertIn("webgl-canvas", html_doc)
        self.assertIn("btn-wireframe", html_doc)
        self.assertIn("btn-rotate", html_doc)
        self.assertIn("btn-theme", html_doc)
        self.assertIn("btn-reset", html_doc)
        self.assertIn("BufferGeometryLoader", html_doc)

        # Light theme test
        light_html = MeshExporter.export_standalone_html(
            self.cube_mesh,
            title="Nexus Light Viewer",
            theme="light",
        )
        self.assertIn("#f8fafc", light_html)


    def test_export_obj_bare_mesh(self) -> None:
        """Verify OBJ export when mesh lacks normals, uvs, or colors."""
        bare_mesh = MeshData(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            faces=[[0, 1, 2]],
            name="bare_triangle",
        )
        obj_text = MeshExporter.export_obj(bare_mesh, object_name="bare")
        self.assertIn("o bare", obj_text)
        self.assertIn("f 1 2 3", obj_text)
        self.assertNotIn("vt", obj_text)
        self.assertNotIn("vn", obj_text)

    def test_export_ascii_stl_with_ngons(self) -> None:
        """Verify STL export triangulates pentagons and hexagons properly."""
        from nexus_3d_scene_studio.geometry_engine import generate_buckyball
        bucky = generate_buckyball(radius=2.0)
        stl_text = MeshExporter.export_ascii_stl(bucky, solid_name="buckyball")
        self.assertTrue(stl_text.startswith("solid buckyball"))
        # 12 pentagons * 3 tris + 20 hexagons * 4 tris = 36 + 80 = 116 triangles
        facet_count = stl_text.count("facet normal")
        self.assertEqual(facet_count, 116)
        self.assertTrue(stl_text.strip().endswith("endsolid buckyball"))


if __name__ == "__main__":
    unittest.main()

