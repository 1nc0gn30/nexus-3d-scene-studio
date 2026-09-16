"""Unit tests for nexus_3d_scene_studio.scene_optimizer module."""

import unittest

from nexus_3d_scene_studio.geometry_engine import (
    MeshData,
    generate_platonic_solid,
    generate_procedural_terrain,
    generate_torus_knot,
)
from nexus_3d_scene_studio.scene_optimizer import SceneOptimizer


class TestSceneOptimizer(unittest.TestCase):
    """Test suite for SceneOptimizer mesh auditing, VRAM profiling, and normal generation."""

    def setUp(self) -> None:
        """Set up test meshes."""
        self.cube = generate_platonic_solid(solid_type="cube", radius=2.0)
        self.terrain = generate_procedural_terrain(grid_size=16, scale=4.0, height_factor=0.6)

    def test_audit_empty_mesh(self) -> None:
        """Verify auditing handles empty meshes gracefully without crashing."""
        empty = MeshData(vertices=[], faces=[])
        audit = SceneOptimizer.audit_mesh_budget(empty)
        self.assertEqual(audit["vertex_count"], 0)
        self.assertEqual(audit["face_count"], 0)
        self.assertEqual(audit["triangle_count"], 0)
        self.assertEqual(audit["performance_grade"], "A+")

    def test_audit_cube_budget(self) -> None:
        """Verify geometrical budget calculations on standard cube mesh."""
        audit = SceneOptimizer.audit_mesh_budget(self.cube)

        self.assertEqual(audit["vertex_count"], 8)
        self.assertEqual(audit["face_count"], 6)
        self.assertEqual(audit["triangle_count"], 12)
        self.assertEqual(audit["edge_count"], 12)

        # Bounding box & dimensions
        bb = audit["bounding_box"]
        self.assertEqual(len(bb), 6)
        dims = audit["dimensions"]
        self.assertEqual(len(dims), 3)
        for d in dims:
            self.assertGreater(d, 0.0)

        # Center of mass should be at origin
        com = audit["center_of_mass"]
        self.assertAlmostEqual(com[0], 0.0, places=4)
        self.assertAlmostEqual(com[1], 0.0, places=4)
        self.assertAlmostEqual(com[2], 0.0, places=4)

        # Surface area and volume
        self.assertGreater(audit["surface_area"], 0.0)
        self.assertGreater(audit["volume"], 0.0)
        self.assertGreater(audit["vram_bytes"], 0)
        self.assertEqual(audit["performance_grade"], "A+")

    def test_performance_grades(self) -> None:
        """Verify performance grading tiers (A+, A, B, C, D)."""
        # Create dummy meshes with specific triangle counts
        def make_dummy(tri_count: int) -> MeshData:
            verts = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
            faces = [[0, 1, 2]] * tri_count
            return MeshData(vertices=verts, faces=faces)

        self.assertEqual(SceneOptimizer.audit_mesh_budget(make_dummy(5000))["performance_grade"], "A+")
        self.assertEqual(SceneOptimizer.audit_mesh_budget(make_dummy(25000))["performance_grade"], "A")
        self.assertEqual(SceneOptimizer.audit_mesh_budget(make_dummy(80000))["performance_grade"], "B")
        self.assertEqual(SceneOptimizer.audit_mesh_budget(make_dummy(200000))["performance_grade"], "C")
        self.assertEqual(SceneOptimizer.audit_mesh_budget(make_dummy(600000))["performance_grade"], "D")

    def test_recompute_normals_smooth_and_flat(self) -> None:
        """Verify smooth and flat vertex normal recomputation."""
        # Cube without normals
        cube_no_norm = MeshData(vertices=self.cube.vertices, faces=self.cube.faces)

        # Smooth normals
        smooth_mesh = SceneOptimizer.recompute_normals(cube_no_norm, smooth=True)
        self.assertIsNotNone(smooth_mesh.normals)
        self.assertEqual(len(smooth_mesh.normals or []), len(self.cube.vertices))

        # Check unit lengths
        for n in smooth_mesh.normals or []:
            l = (n[0]**2 + n[1]**2 + n[2]**2) ** 0.5
            self.assertAlmostEqual(l, 1.0, places=4)

        # Flat normals
        flat_mesh = SceneOptimizer.recompute_normals(cube_no_norm, smooth=False)
        self.assertIsNotNone(flat_mesh.normals)
        self.assertEqual(len(flat_mesh.normals or []), len(self.cube.vertices))

    def test_weld_vertices(self) -> None:
        """Verify spatial vertex welding deduplication."""
        # Mesh with duplicated vertices
        duplicate_verts = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.000001],  # Duplicate of 0
            [1.0, 0.0, 0.000001],  # Duplicate of 1
            [1.0, 1.0, 0.0],
        ]
        faces = [[0, 1, 2], [3, 4, 5]]
        dirty_mesh = MeshData(vertices=duplicate_verts, faces=faces)

        welded = SceneOptimizer.weld_vertices(dirty_mesh, tolerance=1e-4)
        self.assertEqual(len(welded.vertices), 4)
        self.assertEqual(len(welded.faces), 2)
        self.assertTrue(welded.metadata.get("welded"))

    def test_triangulate_mesh(self) -> None:
        """Verify conversion of quad and polygon faces into pure triangles."""
        triangulated = SceneOptimizer.triangulate_mesh(self.cube)
        self.assertEqual(len(triangulated.faces), 12)
        for face in triangulated.faces:
            self.assertEqual(len(face), 3)

    def test_scale_and_center_mesh(self) -> None:
        """Verify scale_mesh and center_mesh spatial transformations."""
        # Scale
        scaled = SceneOptimizer.scale_mesh(self.cube, factor=2.5)
        self.assertAlmostEqual(scaled.vertices[0][0], self.cube.vertices[0][0] * 2.5, places=4)

        # Translate off-center then center
        offset_verts = [[v[0] + 10.0, v[1] + 5.0, v[2] - 8.0] for v in self.cube.vertices]
        offset_mesh = MeshData(vertices=offset_verts, faces=self.cube.faces)
        centered = SceneOptimizer.center_mesh(offset_mesh)

        audit = SceneOptimizer.audit_mesh_budget(centered)
        com = audit["center_of_mass"]
        self.assertAlmostEqual(com[0], 0.0, places=4)
        self.assertAlmostEqual(com[1], 0.0, places=4)
        self.assertAlmostEqual(com[2], 0.0, places=4)


    def test_degenerate_triangle_diagnostics(self) -> None:
        """Verify audit flags degenerate zero-area triangles in diagnostics."""
        degenerate_mesh = MeshData(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]], # Collinear
            faces=[[0, 1, 2]],
        )
        audit = SceneOptimizer.audit_mesh_budget(degenerate_mesh)
        self.assertAlmostEqual(audit["surface_area"], 0.0)
        self.assertTrue(any("degenerate" in diag for diag in audit["diagnostics"]))

    def test_tetrahedron_volume_and_area(self) -> None:
        """Verify volume and surface area of regular tetrahedron."""
        from nexus_3d_scene_studio.geometry_engine import generate_platonic_solid
        tet = generate_platonic_solid(solid_type="tetrahedron", radius=1.0)
        audit = SceneOptimizer.audit_mesh_budget(tet)
        self.assertGreater(audit["volume"], 0.0)
        self.assertGreater(audit["surface_area"], 0.0)
        self.assertEqual(audit["triangle_count"], 4)


if __name__ == "__main__":
    unittest.main()

