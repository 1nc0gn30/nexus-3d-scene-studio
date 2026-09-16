"""Unit tests for nexus_3d_scene_studio.geometry_engine module."""

import math
import unittest

from nexus_3d_scene_studio.geometry_engine import (
    MeshData,
    generate_buckyball,
    generate_fibonacci_lattice,
    generate_mobius_strip,
    generate_platonic_solid,
    generate_procedural_terrain,
    generate_solid,
    generate_superquadric,
    generate_tesseract_4d,
    generate_torus_knot,
    perlin_2d,
    sgn_pow,
    vec3_add,
    vec3_cross,
    vec3_dot,
    vec3_length,
    vec3_normalize,
    vec3_scale,
    vec3_sub,
)


class TestGeometryEngine(unittest.TestCase):
    """Test suite for mathematical procedural geometry generation."""

    def test_vector_math_utilities(self) -> None:
        """Verify 3D vector arithmetic functions."""
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]

        self.assertEqual(vec3_add(a, b), [5.0, 7.0, 9.0])
        self.assertEqual(vec3_sub(b, a), [3.0, 3.0, 3.0])
        self.assertEqual(vec3_scale(a, 2.0), [2.0, 4.0, 6.0])
        self.assertAlmostEqual(vec3_dot(a, b), 32.0)

        cross = vec3_cross([1.0, 0.0, 0.0], [0.0, 1.0, 0.0])
        self.assertEqual(cross, [0.0, 0.0, 1.0])

        self.assertAlmostEqual(vec3_length([0.0, 3.0, 4.0]), 5.0)
        norm = vec3_normalize([0.0, 3.0, 4.0])
        self.assertAlmostEqual(vec3_length(norm), 1.0)
        self.assertAlmostEqual(norm[1], 0.6)
        self.assertAlmostEqual(norm[2], 0.8)

        # Zero-vector safe normalize
        zero_norm = vec3_normalize([0.0, 0.0, 0.0], fallback=[1.0, 0.0, 0.0])
        self.assertEqual(zero_norm, [1.0, 0.0, 0.0])

    def test_sgn_pow_and_noise(self) -> None:
        """Verify signed power function and continuous 2D procedural noise."""
        self.assertAlmostEqual(sgn_pow(2.0, 2.0), 4.0)
        self.assertAlmostEqual(sgn_pow(-2.0, 2.0), -4.0)
        self.assertEqual(sgn_pow(0.0, 2.0), 0.0)

        # Perlin noise determinism and bounds
        n1 = perlin_2d(1.5, 2.5)
        n2 = perlin_2d(1.5, 2.5)
        self.assertEqual(n1, n2)
        self.assertGreaterEqual(n1, -1.5)
        self.assertLessEqual(n1, 1.5)

    def test_mesh_data_interface(self) -> None:
        """Verify MeshData dictionary compatibility and serialization."""
        mesh = MeshData(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            faces=[[0, 1, 2]],
            name="test_triangle",
        )
        self.assertEqual(mesh["name"], "test_triangle")
        self.assertEqual(len(mesh["vertices"]), 3)
        self.assertEqual(mesh.get("faces"), [[0, 1, 2]])
        self.assertIn("vertices", mesh)

        d = mesh.to_dict()
        self.assertEqual(d["name"], "test_triangle")
        self.assertEqual(len(d["vertices"]), 3)

    def test_generate_tesseract_4d(self) -> None:
        """Verify 4D Hypercube stereographic projection mesh generation."""
        mesh = generate_tesseract_4d(size=2.0, angle_4d=0.5, distance_4d=2.8)
        self.assertEqual(len(mesh.vertices), 16)
        self.assertIsNotNone(mesh.edges)
        self.assertEqual(len(mesh.edges or []), 32)
        self.assertEqual(len(mesh.faces), 24)
        self.assertEqual(len(mesh.normals or []), 16)
        self.assertEqual(len(mesh.uvs or []), 16)
        self.assertEqual(mesh.name, "tesseract_4d")

        # Verify all projected vertices are finite 3D coordinates
        for v in mesh.vertices:
            self.assertEqual(len(v), 3)
            for coord in v:
                self.assertTrue(math.isfinite(coord))

    def test_generate_fibonacci_lattice(self) -> None:
        """Verify spherical Fibonacci phyllotaxis point cloud generation."""
        count = 150
        radius = 3.0
        mesh = generate_fibonacci_lattice(count=count, radius=radius)

        self.assertEqual(len(mesh.vertices), count)
        self.assertEqual(len(mesh.normals or []), count)
        self.assertEqual(len(mesh.uvs or []), count)

        # Check all vertices lie exactly on sphere of radius
        for v in mesh.vertices:
            dist = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
            self.assertAlmostEqual(dist, radius, places=4)

        # Check outward unit normals
        for n in mesh.normals or []:
            l = vec3_length(n)
            self.assertAlmostEqual(l, 1.0, places=4)

    def test_generate_torus_knot(self) -> None:
        """Verify parametric (p, q) torus knot tubular mesh generation."""
        p = 3
        q = 5
        num_points = 80
        tube_segments = 12
        mesh = generate_torus_knot(
            p=p,
            q=q,
            major_radius=2.0,
            tube_radius=0.3,
            num_points=num_points,
            tube_segments=tube_segments,
        )

        expected_vertices = num_points * tube_segments
        expected_triangles = num_points * tube_segments * 2

        self.assertEqual(len(mesh.vertices), expected_vertices)
        self.assertEqual(len(mesh.faces), expected_triangles)
        self.assertEqual(len(mesh.normals or []), expected_vertices)
        self.assertEqual(len(mesh.uvs or []), expected_vertices)

        # Check valid index bounds in faces
        for face in mesh.faces:
            self.assertEqual(len(face), 3)
            for idx in face:
                self.assertGreaterEqual(idx, 0)
                self.assertLess(idx, expected_vertices)

    def test_generate_superquadric(self) -> None:
        """Verify deformed superquadric mesh generation."""
        mesh = generate_superquadric(
            s1=0.2,
            s2=0.2,
            rx=1.5,
            ry=1.2,
            rz=1.0,
            pinch=0.2,
            taper=0.3,
            bend=0.1,
            twist=0.5,
            seg_u=16,
            seg_v=16,
        )

        expected_verts = (16 + 1) * (16 + 1)
        self.assertEqual(len(mesh.vertices), expected_verts)
        self.assertGreater(len(mesh.faces), 0)
        self.assertEqual(len(mesh.normals or []), expected_verts)
        self.assertEqual(len(mesh.uvs or []), expected_verts)

    def test_generate_mobius_strip(self) -> None:
        """Verify parametric single-sided Möbius strip generation."""
        mesh = generate_mobius_strip(radius=2.0, width=0.8, twists=1, seg_u=24, seg_v=6)
        expected_verts = (24 + 1) * (6 + 1)
        self.assertEqual(len(mesh.vertices), expected_verts)
        self.assertEqual(len(mesh.faces), 24 * 6 * 2)

    def test_generate_platonic_solids(self) -> None:
        """Verify all canonical Platonic solid polyhedra."""
        solids_spec = {
            "tetrahedron": 4,
            "cube": 8,
            "octahedron": 6,
            "icosahedron": 12,
            "dodecahedron": 20,
        }

        for stype, expected_vcount in solids_spec.items():
            mesh = generate_platonic_solid(solid_type=stype, radius=2.5)
            self.assertEqual(len(mesh.vertices), expected_vcount)
            self.assertGreater(len(mesh.faces), 0)
            # Verify circumradius
            for v in mesh.vertices:
                rad = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
                self.assertAlmostEqual(rad, 2.5, places=4)

    def test_generate_buckyball_and_solid_alias(self) -> None:
        """Verify C60 Fullerene truncated icosahedron solid generation."""
        mesh = generate_solid(solid_type="buckyball", radius=3.0)
        self.assertEqual(len(mesh.vertices), 60)
        self.assertGreater(len(mesh.faces), 0)
        self.assertEqual(mesh.metadata.get("formula"), "C60")

        # Verify circumradius
        for v in mesh.vertices:
            rad = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
            self.assertAlmostEqual(rad, 3.0, places=4)

    def test_generate_procedural_terrain(self) -> None:
        """Verify procedural fBm terrain heightmap generation."""
        grid_size = 16
        scale = 5.0
        mesh = generate_procedural_terrain(
            grid_size=grid_size,
            scale=scale,
            height_factor=0.8,
            octaves=3,
        )

        expected_verts = (grid_size + 1) * (grid_size + 1)
        expected_triangles = grid_size * grid_size * 2

        self.assertEqual(len(mesh.vertices), expected_verts)
        self.assertEqual(len(mesh.faces), expected_triangles)
        self.assertEqual(len(mesh.normals or []), expected_verts)
        self.assertEqual(len(mesh.uvs or []), expected_verts)
        self.assertEqual(len(mesh.colors or []), expected_verts)

        # Check vertex color values within [0.0, 1.0]
        for c in mesh.colors or []:
            self.assertEqual(len(c), 3)
            for channel in c:
                self.assertGreaterEqual(channel, 0.0)
                self.assertLessEqual(channel, 1.0)


    def test_unknown_solid_raises_value_error(self) -> None:
        """Verify invalid solid name raises ValueError."""
        with self.assertRaises(ValueError):
            generate_platonic_solid("non_existent_solid")

    def test_mobius_strip_twists_variations(self) -> None:
        """Verify Möbius strip generator with multiple twist configurations."""
        for twists in (0, 1, 2, 3, 5):
            mesh = generate_mobius_strip(radius=2.0, width=0.5, twists=twists, seg_u=16, seg_v=4)
            self.assertEqual(len(mesh.vertices), 17 * 5)
            self.assertEqual(len(mesh.faces), 16 * 4 * 2)
            self.assertEqual(mesh.metadata.get("twists"), twists)

    def test_superquadric_sphere_and_box(self) -> None:
        """Verify superquadric parameterizes both spheres (s1=s2=1.0) and rounded boxes (s1=s2=0.1)."""
        sphere = generate_superquadric(s1=1.0, s2=1.0, rx=1.0, ry=1.0, rz=1.0, seg_u=8, seg_v=8)
        self.assertGreater(len(sphere.vertices), 0)
        box = generate_superquadric(s1=0.1, s2=0.1, rx=2.0, ry=2.0, rz=2.0, seg_u=8, seg_v=8)
        self.assertGreater(len(box.vertices), 0)

    def test_tesseract_4d_projections(self) -> None:
        """Verify tesseract projection across multiple 4D angles."""
        for angle in (0.0, math.pi / 4, math.pi / 2, math.pi):
            tess = generate_tesseract_4d(size=1.0, angle_4d=angle, distance_4d=3.0)
            self.assertEqual(len(tess.vertices), 16)
            self.assertEqual(len(tess.edges or []), 32)
            self.assertEqual(len(tess.faces), 24)


if __name__ == "__main__":
    unittest.main()

