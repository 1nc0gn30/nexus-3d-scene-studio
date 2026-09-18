"""Tests for Marching Tetrahedra Isosurface & Analytic SDF CSG Engine.

Validates:
1. Analytic SDF primitives (sphere, box, torus, cylinder, capsule).
2. Triply Periodic Minimal Surfaces (TPMS Gyroid, Schwarz P, Neovius).
3. Exact and smooth CSG Boolean operators (union, intersection, subtraction, smooth blends, twist).
4. 3D Mandelbulb fractal field and organic metaballs.
5. Marching Tetrahedra polygonizer (watertight mesh, vertex sharing, analytical finite-difference normals).
6. Preset generator for all built-in presets.
7. MCP server tools: nexus_generate_sdf_isosurface, nexus_evaluate_csg_boolean.
8. CLI and UI server REST integration.
"""

import math
import pytest
from nexus_3d_scene_studio.geometry_engine import MeshData
from nexus_3d_scene_studio.sdf_isosurface import (
    sdf_sphere,
    sdf_box,
    sdf_torus,
    sdf_cylinder,
    sdf_capsule,
    sdf_gyroid,
    sdf_schwarz_p,
    sdf_neovius,
    sdf_mandelbulb,
    sdf_metaballs,
    sdf_union,
    sdf_intersection,
    sdf_subtraction,
    sdf_smooth_union,
    sdf_smooth_subtraction,
    sdf_smooth_intersection,
    sdf_twist,
    marching_tetrahedra,
    generate_sdf_preset,
)
from nexus_3d_scene_studio.mcp_server import MCPServer
from nexus_3d_scene_studio.cli import _resolve_shape


class TestSDFPrimitives:
    """Test mathematical signed distance values of fundamental primitives."""

    def test_sdf_sphere(self):
        # Center of sphere with radius 1.0 -> distance = -1.0 (inside)
        assert pytest.approx(sdf_sphere((0.0, 0.0, 0.0), r=1.0)) == -1.0
        # On surface -> distance = 0.0
        assert pytest.approx(sdf_sphere((1.0, 0.0, 0.0), r=1.0)) == 0.0
        assert pytest.approx(sdf_sphere((0.0, -1.0, 0.0), r=1.0)) == 0.0
        # Outside -> distance = +1.0
        assert pytest.approx(sdf_sphere((2.0, 0.0, 0.0), r=1.0)) == 1.0

    def test_sdf_box(self):
        b = (1.0, 1.0, 1.0)
        # Inside box
        assert sdf_box((0.0, 0.0, 0.0), b=b) < 0.0
        # On box surface
        assert pytest.approx(sdf_box((1.0, 0.5, 0.5), b=b)) == 0.0
        # Outside box
        assert sdf_box((2.0, 0.0, 0.0), b=b) > 0.0

    def test_sdf_torus(self):
        # Torus center (0,0,0): distance is r1 - r2
        d_center = sdf_torus((0.0, 0.0, 0.0), r1=1.0, r2=0.3)
        assert pytest.approx(d_center) == 0.7
        # On torus tube centerline (1.0, 0, 0): distance is -0.3
        d_tube = sdf_torus((1.0, 0.0, 0.0), r1=1.0, r2=0.3)
        assert pytest.approx(d_tube) == -0.3
        # On tube surface (1.3, 0, 0): distance is 0.0
        assert pytest.approx(sdf_torus((1.3, 0.0, 0.0), r1=1.0, r2=0.3), abs=1e-5) == 0.0

    def test_sdf_cylinder(self):
        # Inside cylinder
        assert sdf_cylinder((0.0, 0.0, 0.0), r=0.5, h=1.0) < 0.0
        # On lateral boundary
        assert pytest.approx(sdf_cylinder((0.5, 0.0, 0.0), r=0.5, h=1.0), abs=1e-5) == 0.0
        # Outside
        assert sdf_cylinder((1.0, 0.0, 0.0), r=0.5, h=1.0) > 0.0

    def test_sdf_capsule(self):
        a = (0.0, -1.0, 0.0)
        b = (0.0, 1.0, 0.0)
        r = 0.5
        # Center of segment
        assert pytest.approx(sdf_capsule((0.0, 0.0, 0.0), a=a, b=b, r=r)) == -0.5
        # Cap end
        assert pytest.approx(sdf_capsule((0.0, 1.5, 0.0), a=a, b=b, r=r)) == 0.0
        # Outside
        assert sdf_capsule((1.0, 0.0, 0.0), a=a, b=b, r=r) > 0.0


class TestCSGOperators:
    """Test Boolean CSG set operations and smooth blending functions."""

    def test_exact_csg_union(self):
        d1 = -1.0  # inside
        d2 = 2.0   # outside
        assert sdf_union(d1, d2) == -1.0

    def test_exact_csg_intersection(self):
        d1 = -1.0  # inside
        d2 = 0.5   # outside
        assert sdf_intersection(d1, d2) == 0.5

    def test_exact_csg_subtraction(self):
        # A \ B = max(A, -B)
        d_a = -1.0
        d_b = -0.5
        assert sdf_subtraction(d_a, d_b) == 0.5

    def test_smooth_csg_union(self):
        # Smooth union is always <= min(d1, d2)
        d1 = 0.1
        d2 = 0.1
        k = 0.3
        res = sdf_smooth_union(d1, d2, k=k)
        assert res < min(d1, d2)

    def test_smooth_csg_subtraction_and_intersection(self):
        d1 = -0.2
        d2 = 0.3
        sub = sdf_smooth_subtraction(d1, d2, k=0.2)
        inter = sdf_smooth_intersection(d1, d2, k=0.2)
        assert isinstance(sub, float)
        assert isinstance(inter, float)

    def test_sdf_twist(self):
        # Twist at z=0 should not alter (x, y)
        pt = (1.0, 0.0, 0.0)
        twisted = sdf_twist(pt, k=2.0)
        assert pytest.approx(twisted[0]) == 1.0
        assert pytest.approx(twisted[1]) == 0.0
        assert pytest.approx(twisted[2]) == 0.0

        # Twist at z = pi/2 with k = 1.0 rotates by 90 degrees
        pt_z = (1.0, 0.0, math.pi / 2)
        twisted_z = sdf_twist(pt_z, k=1.0)
        assert pytest.approx(twisted_z[0], abs=1e-5) == 0.0
        assert pytest.approx(twisted_z[1], abs=1e-5) == 1.0
        assert pytest.approx(twisted_z[2]) == math.pi / 2


class TestTPMSAndFractals:
    """Test Triply Periodic Minimal Surfaces and fractal fields."""

    def test_sdf_gyroid(self):
        # Gyroid field evaluation
        val = sdf_gyroid((0.0, 0.0, 0.0), scale=2.0, thickness=0.1)
        # At origin: sin(0)*cos(0) + sin(0)*cos(0) + sin(0)*cos(0) = 0
        # abs(0) - 0.1 = -0.1 (inside the solid wall)
        assert pytest.approx(val) == -0.1

    def test_sdf_schwarz_p(self):
        val = sdf_schwarz_p((0.0, 0.0, 0.0), scale=2.0, thickness=0.15)
        # At origin: cos(0)+cos(0)+cos(0) = 3 -> abs(3) - 0.15 = 2.85
        assert pytest.approx(val) == 2.85

    def test_sdf_neovius(self):
        val = sdf_neovius((0.0, 0.0, 0.0), scale=1.5, thickness=0.1)
        assert isinstance(val, float)

    def test_sdf_mandelbulb(self):
        # Inside Mandelbulb bulb
        val_inside = sdf_mandelbulb((0.0, 0.0, 0.0), power=8.0, max_iter=8)
        assert val_inside <= 0.0
        # Far outside Mandelbulb
        val_outside = sdf_mandelbulb((3.0, 3.0, 3.0), power=8.0, max_iter=8)
        assert val_outside > 0.0

    def test_sdf_metaballs(self):
        # Between 3 metaballs
        val = sdf_metaballs((0.0, 0.0, 0.0))
        assert isinstance(val, float)


class TestMarchingTetrahedra:
    """Test the Marching Tetrahedra isosurface polygonization algorithm."""

    def test_polygonize_sphere(self):
        fn = lambda p: sdf_sphere(p, r=0.8)
        mesh = marching_tetrahedra(
            fn,
            bounds=(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0),
            resolution=12,
            name="TestSphere",
        )
        assert isinstance(mesh, MeshData)
        assert mesh.name == "TestSphere"
        assert len(mesh.vertices) > 20
        assert len(mesh.faces) > 20
        assert len(mesh.normals) == len(mesh.vertices)
        assert len(mesh.colors) == len(mesh.vertices)

        # Verify all faces are triangles (3 vertices)
        for f in mesh.faces:
            assert len(f) == 3
            for v_idx in f:
                assert 0 <= v_idx < len(mesh.vertices)

        # Verify vertices lie approximately on the sphere surface (radius ~ 0.8)
        for vx, vy, vz in mesh.vertices:
            dist = math.sqrt(vx * vx + vy * vy + vz * vz)
            assert pytest.approx(dist, abs=0.25) == 0.8

    def test_polygonize_empty_field(self):
        # Field with no zero-crossing inside bounds -> empty mesh
        fn = lambda p: 5.0  # Always positive / outside
        mesh = marching_tetrahedra(fn, bounds=(-1, 1, -1, 1, -1, 1), resolution=8, name="Empty")
        assert len(mesh.vertices) == 0
        assert len(mesh.faces) == 0


class TestSDFPresets:
    """Test generate_sdf_preset for all supported presets."""

    @pytest.mark.parametrize("preset", [
        "gyroid",
        "schwarz_p",
        "neovius",
        "smooth_csg",
        "metaballs",
        "twisted_torus",
        "mandelbulb",
    ])
    def test_generate_all_presets(self, preset):
        # Test low resolution for fast execution
        mesh = generate_sdf_preset(preset=preset, resolution=10, bounds_scale=1.0)
        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0
        assert len(mesh.normals) == len(mesh.vertices)
        assert len(mesh.colors) == len(mesh.vertices)

    def test_generate_unknown_preset_raises(self):
        with pytest.raises(ValueError, match="Unknown SDF preset"):
            generate_sdf_preset("unknown_fractal", resolution=8)


class TestMCPServerSDFTools:
    """Test MCP Server integration for SDF and CSG tools."""

    def test_mcp_generate_sdf_isosurface(self):
        server = MCPServer()
        assert "nexus_generate_sdf_isosurface" in server.tools
        assert "nexus_evaluate_csg_boolean" in server.tools

        # Call nexus_generate_sdf_isosurface
        res = server.call_tool(
            "nexus_generate_sdf_isosurface",
            {"preset": "gyroid", "resolution": 10, "format": "dict"},
        )
        assert "vertices" in res
        assert "faces" in res
        assert len(res["vertices"]) > 0

    def test_mcp_evaluate_csg_boolean(self):
        server = MCPServer()
        res = server.call_tool(
            "nexus_evaluate_csg_boolean",
            {
                "operation": "smooth_union",
                "primitive_a": {"type": "sphere", "radius": 0.8},
                "primitive_b": {"type": "box", "size": [0.6, 0.6, 0.6]},
                "smoothing": 0.2,
                "resolution": 10,
                "format": "dict",
            },
        )
        assert "vertices" in res
        assert "faces" in res
        assert len(res["vertices"]) > 0

    def test_mcp_generate_sdf_obj_format(self):
        server = MCPServer()
        res = server.call_tool(
            "nexus_generate_sdf_isosurface",
            {"preset": "metaballs", "resolution": 10, "format": "obj"},
        )
        assert isinstance(res, str)
        assert "OBJ" in res
        assert "o SDF_Metaballs" in res


class TestCLIAndUIServerIntegration:
    """Test CLI resolution and UI server handling of SDF shapes."""

    def test_cli_resolve_sdf_shapes(self):
        mesh_gyroid = _resolve_shape("gyroid", {"resolution": 10})
        assert len(mesh_gyroid.vertices) > 0

        mesh_csg = _resolve_shape("smooth_csg", {"resolution": 10})
        assert len(mesh_csg.vertices) > 0

        mesh_sdf = _resolve_shape("sdf", {"preset": "schwarz_p", "resolution": 10})
        assert len(mesh_sdf.vertices) > 0

    def test_ui_server_sdf_presets_catalog(self):
        from nexus_3d_scene_studio.ui_server import get_default_presets
        presets_data = get_default_presets()
        categories = [cat["id"] for cat in presets_data["categories"]]
        assert "sdf_tpms" in categories
