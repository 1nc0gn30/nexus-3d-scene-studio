"""Unit tests for Procedural Fractals, Strange Attractors, and LOD Decimation."""

import pytest
from nexus_3d_scene_studio.geometry_engine import generate_torus_knot
from nexus_3d_scene_studio.procedural_fractals import (
    decimate_mesh,
    generate_klein_bottle,
    generate_lod_pyramid,
    generate_menger_sponge,
    generate_strange_attractor,
)
from nexus_3d_scene_studio.scene_optimizer import SceneOptimizer
from nexus_3d_scene_studio.mcp_server import MCPServer
from nexus_3d_scene_studio.cli import _resolve_shape


class TestStrangeAttractorGenerator:
    def test_lorenz_attractor_generation(self):
        mesh = generate_strange_attractor(attractor_type="lorenz", steps=200, tube_segments=6)
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0
        assert mesh.normals is not None
        assert mesh.colors is not None
        assert mesh.uvs is not None
        assert len(mesh.vertices) == len(mesh.normals) == len(mesh.colors)

    def test_rossler_and_aizawa_attractors(self):
        mesh_r = generate_strange_attractor(attractor_type="rossler", steps=150, tube_segments=4)
        assert len(mesh_r.vertices) > 0
        assert len(mesh_r.faces) > 0

        mesh_a = generate_strange_attractor(attractor_type="aizawa", steps=150, tube_segments=4)
        assert len(mesh_a.vertices) > 0
        assert len(mesh_a.faces) > 0


class TestKleinBottleAndMengerSponge:
    def test_klein_bottle_immersion(self):
        mesh = generate_klein_bottle(u_segments=16, v_segments=8)
        assert len(mesh.vertices) == 16 * 8
        assert len(mesh.faces) == 16 * 8
        assert mesh.normals is not None
        assert mesh.colors is not None

    def test_menger_sponge_level_0_and_1(self):
        m0 = generate_menger_sponge(level=0)
        assert len(m0.faces) == 6

        m1 = generate_menger_sponge(level=1)
        assert m1.metadata["cubes_count"] == 20
        assert len(m1.faces) == 20 * 6


class TestLODDecimationAndPyramid:
    def test_mesh_decimation(self):
        knot = generate_torus_knot(num_points=40, tube_segments=8)
        original_faces = len(knot.faces)
        decimated = decimate_mesh(knot, target_ratio=0.5)
        assert len(decimated.faces) < original_faces
        assert len(decimated.vertices) < len(knot.vertices)
        assert decimated.metadata["decimated"] is True

    def test_lod_pyramid_generation(self):
        knot = generate_torus_knot(num_points=50, tube_segments=8)
        lod_data = SceneOptimizer.generate_lod_pyramid(knot, lod_ratios=(1.0, 0.5, 0.2))

        assert "levels" in lod_data
        assert "summary" in lod_data
        assert len(lod_data["summary"]) == 3

        # Verify descending face count progression
        f_counts = [s["face_count"] for s in lod_data["summary"]]
        assert f_counts[0] >= f_counts[1] >= f_counts[2]

        # Verify increasing switch distances
        dist = [s["switch_distance_units"] for s in lod_data["summary"]]
        assert dist[0] <= dist[1] <= dist[2]


class TestMCPServerFractalAndLODTools:
    def test_mcp_generate_fractal_tool(self):
        server = MCPServer()
        res = server.call_tool("nexus_generate_fractal", {"fractal_type": "lorenz", "steps": 100})
        assert "vertices" in res
        assert "faces" in res

    def test_mcp_generate_lod_pyramid_tool(self):
        server = MCPServer()
        res = server.call_tool("nexus_generate_lod_pyramid", {"shape_type": "torus_knot"})
        assert "summary" in res
        assert "levels" in res
        assert "lod0" in res["levels"]


class TestCLIFractalResolution:
    def test_resolve_fractal_shapes(self):
        m_lorenz = _resolve_shape("lorenz", {"steps": 100})
        assert "attractor" in m_lorenz.name

        m_klein = _resolve_shape("klein", {})
        assert m_klein.name == "klein_bottle"

        m_menger = _resolve_shape("menger", {"level": 1})
        assert "menger" in m_menger.name
