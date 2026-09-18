"""Signed Distance Function (SDF) Volumetric Isosurface & CSG Engine.

Provides pure Python standard library volumetric isosurface extraction,
Triply Periodic Minimal Surfaces (TPMS Gyroid, Schwarz P, Neovius),
Constructive Solid Geometry (CSG) Boolean operators, 3D Mandelbulb fractal fields,
and Marching Tetrahedra polygonization with analytical gradient surface normals.

Zero external runtime dependencies (100% Python standard library).
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from nexus_3d_scene_studio.geometry_engine import (
    MeshData,
    vec3_add,
    vec3_cross,
    vec3_dot,
    vec3_length,
    vec3_normalize,
    vec3_scale,
    vec3_sub,
)


# ---------------------------------------------------------------------------
# Signed Distance Functions (SDF) Primitives
# ---------------------------------------------------------------------------

def sdf_sphere(p: Sequence[float], radius: float = 1.0, r: Optional[float] = None) -> float:
    """Signed distance to a sphere centered at origin."""
    rad = r if r is not None else radius
    return math.sqrt(p[0] * p[0] + p[1] * p[1] + p[2] * p[2]) - rad


def sdf_box(p: Sequence[float], size: Sequence[float] = (1.0, 1.0, 1.0), b: Optional[Sequence[float]] = None) -> float:
    """Signed distance to a 3D box centered at origin with half-extents."""
    s = b if b is not None else size
    dx = abs(p[0]) - s[0]
    dy = abs(p[1]) - s[1]
    dz = abs(p[2]) - s[2]

    outside_x = max(dx, 0.0)
    outside_y = max(dy, 0.0)
    outside_z = max(dz, 0.0)
    outside_dist = math.sqrt(outside_x * outside_x + outside_y * outside_y + outside_z * outside_z)
    inside_dist = min(max(dx, dy, dz), 0.0)
    return outside_dist + inside_dist


def sdf_torus(
    p: Sequence[float],
    r_major: float = 1.0,
    r_minor: float = 0.35,
    r1: Optional[float] = None,
    r2: Optional[float] = None,
) -> float:
    """Signed distance to a torus oriented in XZ plane."""
    rmaj = r1 if r1 is not None else r_major
    rmin = r2 if r2 is not None else r_minor
    q_x = math.sqrt(p[0] * p[0] + p[2] * p[2]) - rmaj
    q_y = p[1]
    return math.sqrt(q_x * q_x + q_y * q_y) - rmin


def sdf_cylinder(
    p: Sequence[float],
    radius: float = 0.5,
    height: float = 1.0,
    r: Optional[float] = None,
    h: Optional[float] = None,
) -> float:
    """Signed distance to a cylinder oriented along the Y axis."""
    rad = r if r is not None else radius
    hei = h if h is not None else height
    radial_dist = math.sqrt(p[0] * p[0] + p[2] * p[2]) - rad
    axial_dist = abs(p[1]) - hei * 0.5
    outside = math.sqrt(max(radial_dist, 0.0) ** 2 + max(axial_dist, 0.0) ** 2)
    inside = min(max(radial_dist, axial_dist), 0.0)
    return outside + inside


def sdf_capsule(
    p: Sequence[float],
    a: Sequence[float] = (-0.5, 0.0, 0.0),
    b: Sequence[float] = (0.5, 0.0, 0.0),
    radius: float = 0.3,
    r: Optional[float] = None,
) -> float:
    """Signed distance to a 3D capsule line segment between a and b."""
    rad = r if r is not None else radius
    pa = [p[0] - a[0], p[1] - a[1], p[2] - a[2]]
    ba = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]
    baba = ba[0] * ba[0] + ba[1] * ba[1] + ba[2] * ba[2]
    if baba < 1e-12:
        return math.sqrt(pa[0] * pa[0] + pa[1] * pa[1] + pa[2] * pa[2]) - rad

    paba = pa[0] * ba[0] + pa[1] * ba[1] + pa[2] * ba[2]
    h_param = max(0.0, min(1.0, paba / baba))
    dx = pa[0] - ba[0] * h_param
    dy = pa[1] - ba[1] * h_param
    dz = pa[2] - ba[2] * h_param
    return math.sqrt(dx * dx + dy * dy + dz * dz) - rad


# ---------------------------------------------------------------------------
# Triply Periodic Minimal Surfaces (TPMS)
# ---------------------------------------------------------------------------

def sdf_gyroid(p: Sequence[float], scale: float = 2.0, thickness: float = 0.1) -> float:
    """SDF for Triply Periodic Minimal Surface (TPMS) Gyroid infill scaffold."""
    x = p[0] * scale
    y = p[1] * scale
    z = p[2] * scale
    val = math.cos(x) * math.sin(y) + math.cos(y) * math.sin(z) + math.cos(z) * math.sin(x)
    return abs(val) - thickness


def sdf_schwarz_p(p: Sequence[float], scale: float = 2.0, thickness: float = 0.15) -> float:
    """SDF for Schwarz P Triply Periodic Minimal Surface."""
    x = p[0] * scale
    y = p[1] * scale
    z = p[2] * scale
    val = math.cos(x) + math.cos(y) + math.cos(z)
    return abs(val) - thickness


def sdf_neovius(p: Sequence[float], scale: float = 2.0, thickness: float = 0.2) -> float:
    """SDF for Neovius Triply Periodic Minimal Surface."""
    x = p[0] * scale
    y = p[1] * scale
    z = p[2] * scale
    cx = math.cos(x)
    cy = math.cos(y)
    cz = math.cos(z)
    val = 3.0 * (cx + cy + cz) + 4.0 * cx * cy * cz
    return abs(val) - thickness


# ---------------------------------------------------------------------------
# 3D Mandelbulb Fractal & Metaballs
# ---------------------------------------------------------------------------

def sdf_mandelbulb(p: Sequence[float], power: float = 8.0, max_iter: int = 8) -> float:
    """Distance estimator for 3D Mandelbulb fractal field."""
    w = list(p)
    dz = 1.0
    r = 0.0

    for _ in range(max_iter):
        r = math.sqrt(w[0] * w[0] + w[1] * w[1] + w[2] * w[2])
        if r > 2.5:
            break

        # Spherical coordinates
        theta = math.acos(max(-1.0, min(1.0, w[2] / (r + 1e-12))))
        phi = math.atan2(w[1], w[0])
        dz = (r ** (power - 1.0)) * power * dz + 1.0

        # Scale and rotate
        zr = r ** power
        theta = theta * power
        phi = phi * power

        # Convert back to Cartesian
        w[0] = zr * math.sin(theta) * math.cos(phi) + p[0]
        w[1] = zr * math.sin(theta) * math.sin(phi) + p[1]
        w[2] = zr * math.cos(theta) + p[2]

    return 0.5 * math.log(max(r, 1e-12)) * r / (dz + 1e-12)


def sdf_metaballs(
    p: Sequence[float],
    centers: Optional[List[Sequence[float]]] = None,
    radii: Optional[List[float]] = None,
    k: float = 0.4,
) -> float:
    """SDF for cluster of organically blended metaballs."""
    if centers is None:
        centers = [(-0.4, 0.0, 0.0), (0.4, 0.0, 0.0), (0.0, 0.4, 0.0)]
    if radii is None:
        radii = [0.45, 0.45, 0.35]

    d = sdf_sphere([p[0] - centers[0][0], p[1] - centers[0][1], p[2] - centers[0][2]], radii[0])
    for i in range(1, len(centers)):
        c = centers[i]
        r = radii[i] if i < len(radii) else 0.4
        d_next = sdf_sphere([p[0] - c[0], p[1] - c[1], p[2] - c[2]], r)
        d = sdf_smooth_union(d, d_next, k=k)
    return d


# ---------------------------------------------------------------------------
# Constructive Solid Geometry (CSG) & Blending Operators
# ---------------------------------------------------------------------------

def sdf_union(d1: float, d2: float) -> float:
    """Exact CSG Boolean Union: min(d1, d2)."""
    return min(d1, d2)


def sdf_intersection(d1: float, d2: float) -> float:
    """Exact CSG Boolean Intersection: max(d1, d2)."""
    return max(d1, d2)


def sdf_subtraction(d1: float, d2: float) -> float:
    """Exact CSG Boolean Subtraction: max(d1, -d2) (cuts d2 from d1)."""
    return max(d1, -d2)


def sdf_smooth_union(d1: float, d2: float, k: float = 0.15) -> float:
    """Smooth polynomial Boolean union."""
    h = max(0.0, min(1.0, 0.5 + 0.5 * (d2 - d1) / (k + 1e-12)))
    return d2 + (d1 - d2) * h - k * h * (1.0 - h)


def sdf_smooth_subtraction(d1: float, d2: float, k: float = 0.15) -> float:
    """Smooth polynomial Boolean subtraction (carves d2 from d1)."""
    h = max(0.0, min(1.0, 0.5 - 0.5 * (d1 + d2) / (k + 1e-12)))
    return d1 + (-d2 - d1) * h + k * h * (1.0 - h)


def sdf_smooth_intersection(d1: float, d2: float, k: float = 0.15) -> float:
    """Smooth polynomial Boolean intersection."""
    h = max(0.0, min(1.0, 0.5 - 0.5 * (d2 - d1) / (k + 1e-12)))
    return d2 + (d1 - d2) * h + k * h * (1.0 - h)


def sdf_twist(p: Sequence[float], k: float = 1.0, axis: str = "z") -> List[float]:
    """Non-linear spatial twist deformer. Supports 'z' (around Z axis) and 'y' (around Y axis)."""
    if axis.lower() == "y":
        c = math.cos(k * p[1])
        s = math.sin(k * p[1])
        return [c * p[0] - s * p[2], p[1], s * p[0] + c * p[2]]
    else:
        c = math.cos(k * p[2])
        s = math.sin(k * p[2])
        return [c * p[0] - s * p[1], s * p[0] + c * p[1], p[2]]


# ---------------------------------------------------------------------------
# Analytical Normal Estimation via Finite Difference Gradient
# ---------------------------------------------------------------------------

def calculate_sdf_normal(
    sdf_fn: Callable[[Sequence[float]], float],
    p: Sequence[float],
    eps: float = 0.005,
) -> List[float]:
    """Calculate normalized gradient normal vector of an SDF field at point p."""
    x, y, z = p[0], p[1], p[2]
    dx = sdf_fn([x + eps, y, z]) - sdf_fn([x - eps, y, z])
    dy = sdf_fn([x, y + eps, z]) - sdf_fn([x, y - eps, z])
    dz = sdf_fn([x, y, z + eps]) - sdf_fn([x, y, z - eps])
    return vec3_normalize([dx, dy, dz], fallback=(0.0, 1.0, 0.0))


# ---------------------------------------------------------------------------
# Marching Tetrahedra Isosurface Polygonizer
# ---------------------------------------------------------------------------

# 16-entry lookup table for Marching Tetrahedra
# Each entry maps 4-bit vertex sign mask to list of triangles (each triangle has 3 edge indices)
# Tetrahedron vertices: 0, 1, 2, 3
# Edges: 0:(0-1), 1:(1-2), 2:(2-0), 3:(0-3), 4:(1-3), 5:(2-3)
_TETRAHEDRON_EDGE_PAIRS = [
    (0, 1),  # Edge 0
    (1, 2),  # Edge 1
    (2, 0),  # Edge 2
    (0, 3),  # Edge 3
    (1, 3),  # Edge 4
    (2, 3),  # Edge 5
]
_TETRA_EDGES = _TETRAHEDRON_EDGE_PAIRS

# Canonical 16 cases of marching tetrahedra:
_TETRA_TRIANGLES: Dict[int, List[Tuple[int, int, int]]] = {
    0:  [],                          # All outside
    15: [],                          # All inside
    1:  [(0, 3, 2)],                 # v0 inside
    14: [(0, 2, 3)],                 # v0 outside
    2:  [(0, 1, 4)],                 # v1 inside
    13: [(0, 4, 1)],                 # v1 outside
    4:  [(1, 2, 5)],                 # v2 inside
    11: [(1, 5, 2)],                 # v2 outside
    8:  [(3, 5, 4)],                 # v3 inside
    7:  [(3, 4, 5)],                 # v3 outside
    3:  [(1, 4, 2), (2, 4, 3)],     # v0, v1 inside
    12: [(1, 2, 4), (2, 3, 4)],     # v2, v3 inside
    5:  [(0, 3, 1), (1, 3, 5)],     # v0, v2 inside
    10: [(0, 1, 3), (1, 5, 3)],     # v1, v3 inside
    6:  [(0, 4, 1), (1, 4, 5)],     # v1, v2 inside
    9:  [(0, 1, 4), (1, 5, 4)],     # v0, v3 inside
}


def marching_tetrahedra(
    sdf_fn: Callable[[Sequence[float]], float],
    bounds: Sequence[float] = (-1.2, 1.2, -1.2, 1.2, -1.2, 1.2),
    resolution: Union[int, Sequence[int]] = (20, 20, 20),
    isovalue: float = 0.0,
    compute_normals: bool = True,
    compute_colors: bool = True,
    name: str = "Isosurface",
) -> MeshData:
    """Extract an isosurface mesh from a 3D scalar/SDF field via Marching Tetrahedra.

    Args:
        sdf_fn: Signed distance function taking [x, y, z] -> float.
        bounds: Tuple of (min_x, max_x, min_y, max_y, min_z, max_z).
        resolution: Grid resolution (nx, ny, nz) or integer per-axis count.
        isovalue: Surface threshold value (0.0 for standard SDF boundary).
        compute_normals: Recompute accurate analytical gradient surface normals.
        compute_colors: Compute continuous RGB normal-map coloring for vertices.
        name: Identifier name for the generated mesh.

    Returns:
        Clean, manifold MeshData instance.
    """
    min_x, max_x, min_y, max_y, min_z, max_z = bounds
    if isinstance(resolution, (int, float)):
        nx = ny = nz = int(resolution)
    else:
        nx, ny, nz = resolution
    nx = max(4, int(nx))
    ny = max(4, int(ny))
    nz = max(4, int(nz))

    dx = (max_x - min_x) / (nx - 1)
    dy = (max_y - min_y) / (ny - 1)
    dz = (max_z - min_z) / (nz - 1)

    # 1. Sample 3D grid points and scalar field values
    grid_coords: List[List[float]] = []
    grid_values: List[float] = []

    for ix in range(nx):
        x = min_x + ix * dx
        for iy in range(ny):
            y = min_y + iy * dy
            for iz in range(nz):
                z = min_z + iz * dz
                p = [x, y, z]
                grid_coords.append(p)
                grid_values.append(sdf_fn(p))

    def node_index(ix: int, iy: int, iz: int) -> int:
        return ix * (ny * nz) + iy * nz + iz

    # 2. Polygonize each cube by subdividing into 6 tetrahedra
    edge_vertex_cache: Dict[Tuple[int, int], int] = {}
    mesh_vertices: List[List[float]] = []
    mesh_normals: List[List[float]] = []
    mesh_colors: List[List[float]] = []
    mesh_faces: List[List[int]] = []

    def get_edge_vertex(idx_a: int, idx_b: int) -> int:
        key = (min(idx_a, idx_b), max(idx_a, idx_b))
        if key in edge_vertex_cache:
            return edge_vertex_cache[key]

        pa = grid_coords[idx_a]
        pb = grid_coords[idx_b]
        va = grid_values[idx_a]
        vb = grid_values[idx_b]

        # Linear interpolation of zero-crossing point
        denom = vb - va
        t = (isovalue - va) / denom if abs(denom) > 1e-12 else 0.5
        t = max(0.0, min(1.0, t))

        pos = [
            pa[0] + t * (pb[0] - pa[0]),
            pa[1] + t * (pb[1] - pa[1]),
            pa[2] + t * (pb[2] - pa[2]),
        ]

        v_idx = len(mesh_vertices)
        mesh_vertices.append(pos)

        if compute_normals:
            norm = calculate_sdf_normal(sdf_fn, pos)
            mesh_normals.append(norm)
            if compute_colors:
                # Normal-mapped RGB color: (N + 1) / 2
                col = [
                    round((norm[0] + 1.0) * 0.5, 3),
                    round((norm[1] + 1.0) * 0.5, 3),
                    round((norm[2] + 1.0) * 0.5, 3),
                ]
                mesh_colors.append(col)

        edge_vertex_cache[key] = v_idx
        return v_idx

    for ix in range(nx - 1):
        for iy in range(ny - 1):
            for iz in range(nz - 1):
                # 8 corners of the cube
                c0 = node_index(ix, iy, iz)
                c1 = node_index(ix + 1, iy, iz)
                c2 = node_index(ix, iy + 1, iz)
                c3 = node_index(ix + 1, iy + 1, iz)
                c4 = node_index(ix, iy, iz + 1)
                c5 = node_index(ix + 1, iy, iz + 1)
                c6 = node_index(ix, iy + 1, iz + 1)
                c7 = node_index(ix + 1, iy + 1, iz + 1)

                # 6 tetrahedra decomposition of the cube
                cube_tets = [
                    (c0, c1, c3, c7),
                    (c0, c3, c2, c7),
                    (c0, c1, c5, c7),
                    (c0, c5, c4, c7),
                    (c0, c2, c6, c7),
                    (c0, c6, c4, c7),
                ]

                for tet in cube_tets:
                    t_nodes = list(tet)
                    t_vals = [grid_values[n] for n in t_nodes]

                    # 4-bit mask of vertices inside isovalue
                    mask = 0
                    for i_v in range(4):
                        if t_vals[i_v] < isovalue:
                            mask |= (1 << i_v)

                    tri_edge_triplets = _TETRA_TRIANGLES.get(mask, [])
                    for e_tri in tri_edge_triplets:
                        # Find corresponding global grid node pairs
                        e0_a, e0_b = t_nodes[_TETRA_EDGES[e_tri[0]][0]], t_nodes[_TETRA_EDGES[e_tri[0]][1]]
                        e1_a, e1_b = t_nodes[_TETRA_EDGES[e_tri[1]][0]], t_nodes[_TETRA_EDGES[e_tri[1]][1]]
                        e2_a, e2_b = t_nodes[_TETRA_EDGES[e_tri[2]][0]], t_nodes[_TETRA_EDGES[e_tri[2]][1]]

                        v0 = get_edge_vertex(e0_a, e0_b)
                        v1 = get_edge_vertex(e1_a, e1_b)
                        v2 = get_edge_vertex(e2_a, e2_b)

                        if v0 != v1 and v1 != v2 and v0 != v2:
                            mesh_faces.append([v0, v1, v2])

    return MeshData(
        vertices=mesh_vertices,
        faces=mesh_faces,
        normals=mesh_normals if compute_normals else None,
        colors=mesh_colors if compute_colors else None,
        name=name,
        metadata={
            "generator": "marching_tetrahedra",
            "resolution": [nx, ny, nz],
            "bounds": list(bounds),
            "isovalue": float(isovalue),
            "vertex_count": len(mesh_vertices),
            "face_count": len(mesh_faces),
        },
    )


# ---------------------------------------------------------------------------
# High-Level Procedural Presets
# ---------------------------------------------------------------------------

def generate_sdf_preset(
    preset_name: Optional[str] = None,
    resolution: int = 22,
    bounds_scale: float = 1.2,
    preset: Optional[str] = None,
    name: Optional[str] = None,
    **kwargs: Any,
) -> MeshData:
    """Generate a high-fidelity 3D mesh from built-in procedural SDF presets.

    Supported Presets:
    - 'gyroid' / 'gyroid_tpms': Triply Periodic Minimal Surface Gyroid infill scaffold
    - 'schwarz_p': Schwarz P Minimal Surface crystal
    - 'neovius': Neovius Minimal Surface porous structure
    - 'mandelbulb': 3D Mandelbulb fractal isosurface
    - 'smooth_csg': Sphere with smoothly subtracted box and cylinder core
    - 'metaballs': Organically merged triple-center metaball cluster
    - 'twisted_torus': Torus with continuous non-linear spatial twist
    """
    effective_name = (preset or preset_name or name or "gyroid").lower().strip()
    r = max(8, int(resolution))
    b = float(bounds_scale)
    bounds = (-b, b, -b, b, -b, b)

    if effective_name in ("gyroid", "gyroid_tpms", "tpms"):
        scale = float(kwargs.get("scale", 3.14159))
        thickness = float(kwargs.get("thickness", 0.15))
        def fn(p):
            # Clip to a bounding sphere/box so edges look clean
            envelope = sdf_sphere(p, radius=b * 0.95)
            gyroid = sdf_gyroid(p, scale=scale, thickness=thickness)
            return sdf_intersection(envelope, gyroid)

    elif effective_name in ("schwarz_p", "schwarz"):
        scale = float(kwargs.get("scale", 3.14159))
        thickness = float(kwargs.get("thickness", 0.2))
        def fn(p):
            envelope = sdf_box(p, size=(b * 0.9, b * 0.9, b * 0.9))
            schwarz = sdf_schwarz_p(p, scale=scale, thickness=thickness)
            return sdf_intersection(envelope, schwarz)

    elif effective_name in ("neovius", "neovius_tpms"):
        scale = float(kwargs.get("scale", 3.14159))
        thickness = float(kwargs.get("thickness", 0.25))
        def fn(p):
            envelope = sdf_box(p, size=(b * 0.9, b * 0.9, b * 0.9))
            neovius = sdf_neovius(p, scale=scale, thickness=thickness)
            return sdf_intersection(envelope, neovius)

    elif effective_name in ("mandelbulb", "mandelbulb_3d", "fractal_bulb"):
        power = float(kwargs.get("power", 8.0))
        max_iter = int(kwargs.get("max_iter", 6))
        def fn(p):
            return sdf_mandelbulb(p, power=power, max_iter=max_iter)

    elif effective_name in ("smooth_csg", "csg_hollow", "csg"):
        k = float(kwargs.get("k", 0.2))
        def fn(p):
            sphere = sdf_sphere(p, radius=1.0)
            box = sdf_box(p, size=(0.7, 0.7, 0.7))
            cyl = sdf_cylinder(p, radius=0.35, height=2.2)
            carved = sdf_smooth_subtraction(sphere, box, k=k)
            return sdf_smooth_subtraction(carved, cyl, k=k)

    elif effective_name in ("metaballs", "organic_blobs", "blobs"):
        k = float(kwargs.get("k", 0.45))
        def fn(p):
            return sdf_metaballs(p, k=k)

    elif effective_name in ("twisted_torus", "twist"):
        twist_k = float(kwargs.get("twist_k", 1.8))
        def fn(p):
            p_twisted = sdf_twist(p, k=twist_k, axis="y")
            return sdf_torus(p_twisted, r_major=0.7, r_minor=0.28)

    else:
        raise ValueError(
            f"Unknown SDF preset: '{effective_name}'. Available: 'gyroid', 'schwarz_p', "
            "'neovius', 'mandelbulb', 'smooth_csg', 'metaballs', 'twisted_torus'."
        )

    mesh = marching_tetrahedra(
        sdf_fn=fn,
        bounds=bounds,
        resolution=(r, r, r),
        isovalue=0.0,
        compute_normals=True,
        compute_colors=True,
        name=f"SDF_{effective_name.capitalize()}",
    )
    mesh.metadata["preset"] = effective_name
    return mesh
