"""Parametric Fractals, Strange Attractors, and Level-of-Detail (LOD) Decimation.

Provides procedural generators for:
1. Strange Attractors (Lorenz, Rössler, Aizawa, Chen) with Frenet-Serret tubular mesh ribbons.
2. 4D Non-Orientable Surfaces (Klein Bottle immersion).
3. 3D Recursive Fractals (Menger Sponge voxel cube mesh).
4. Edge-collapse mesh decimation and automatic LOD (Level-of-Detail) pyramid generator.

Pure Python standard library (3.9-3.13) with zero external runtime dependencies.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from .geometry_engine import (
    MeshData,
    ensure_mesh_data,
    vec3_add,
    vec3_cross,
    vec3_dot,
    vec3_length,
    vec3_normalize,
    vec3_scale,
    vec3_sub,
)


# ---------------------------------------------------------------------------
# Strange Attractor ODE Integrator
# ---------------------------------------------------------------------------

def _rk4_step(
    f: Callable[[float, float, float], Tuple[float, float, float]],
    x: float,
    y: float,
    z: float,
    dt: float,
) -> Tuple[float, float, float]:
    """Fourth-order Runge-Kutta step for 3D continuous dynamical systems."""
    dx1, dy1, dz1 = f(x, y, z)
    dx2, dy2, dz2 = f(x + 0.5 * dt * dx1, y + 0.5 * dt * dy1, z + 0.5 * dt * dz1)
    dx3, dy3, dz3 = f(x + 0.5 * dt * dx2, y + 0.5 * dt * dy2, z + 0.5 * dt * dz2)
    dx4, dy4, dz4 = f(x + dt * dx3, y + dt * dy3, z + dt * dz3)

    nx = x + (dt / 6.0) * (dx1 + 2.0 * dx2 + 2.0 * dx3 + dx4)
    ny = y + (dt / 6.0) * (dy1 + 2.0 * dy2 + 2.0 * dy3 + dy4)
    nz = z + (dt / 6.0) * (dz1 + 2.0 * dz2 + 2.0 * dz3 + dz4)
    return nx, ny, nz


def generate_strange_attractor(
    attractor_type: str = "lorenz",
    steps: int = 1500,
    dt: float = 0.01,
    tube_radius: float = 0.06,
    tube_segments: int = 6,
    scale: float = 0.1,
) -> MeshData:
    """Generate a 3D tubular mesh ribbon of a chaotic strange attractor.

    Args:
        attractor_type: 'lorenz', 'rossler', 'aizawa', or 'chen'.
        steps: Number of integration trajectory steps.
        dt: Integration time-step.
        tube_radius: Cross-sectional radius of the tubular extrusion.
        tube_segments: Radial resolution of each tube segment.
        scale: Coordinate scaling factor for scene fit.

    Returns:
        MeshData with vertices, faces, smooth normals, UVs, and velocity-based RGB colors.
    """
    atype = attractor_type.lower().strip()

    if atype == "lorenz":
        sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
        f = lambda x, y, z: (sigma * (y - x), x * (rho - z) - y, x * y - beta * z)
        x, y, z = 0.1, 0.0, 0.0
    elif atype == "rossler":
        a, b, c = 0.2, 0.2, 5.7
        f = lambda x, y, z: (-y - z, x + a * y, b + z * (x - c))
        x, y, z = 0.1, 0.1, 0.1
    elif atype == "aizawa":
        a, b, c, d, e, f_param = 0.95, 0.7, 0.6, 3.5, 0.25, 0.1
        f = lambda x, y, z: (
            (z - b) * x - d * y,
            d * x + (z - b) * y,
            c + a * z - (z ** 3) / 3.0 - (x * x + y * y) * (1.0 + e * z) + f_param * z * (x ** 3),
        )
        x, y, z = 0.1, 0.0, 0.0
    else:  # chen attractor
        a, b, c = 35.0, 3.0, 28.0
        f = lambda x, y, z: (a * (y - x), (c - a) * x - x * z + c * y, x * y - b * z)
        x, y, z = -0.1, 0.5, -0.6

    # Warm-up 100 steps to reach the attractor limit cycle / manifold
    for _ in range(100):
        x, y, z = _rk4_step(f, x, y, z, dt)

    # Collect trajectory points & velocities
    points: List[List[float]] = []
    velocities: List[float] = []

    for _ in range(steps):
        points.append([x * scale, y * scale, z * scale])
        dx, dy, dz = f(x, y, z)
        velocities.append(math.sqrt(dx * dx + dy * dy + dz * dz))
        x, y, z = _rk4_step(f, x, y, z, dt)

    # Normalize velocities to [0.0, 1.0] for gradient coloring
    v_min = min(velocities) if velocities else 0.0
    v_max = max(velocities) if velocities else 1.0
    v_range = max(1e-6, v_max - v_min)

    vertices: List[List[float]] = []
    normals: List[List[float]] = []
    colors: List[List[float]] = []
    uvs: List[List[float]] = []
    faces: List[List[int]] = []

    # Rotation-minimizing frame transport for smooth non-twisting tubes
    # Initial arbitrary normal orthogonal to first tangent
    if len(points) < 2:
        return MeshData(vertices=[], faces=[])

    p0, p1 = points[0], points[1]
    t0 = vec3_normalize(vec3_sub(p1, p0))
    up = [0.0, 1.0, 0.0] if abs(t0[1]) < 0.9 else [1.0, 0.0, 0.0]
    n0 = vec3_normalize(vec3_cross(t0, up))
    b0 = vec3_normalize(vec3_cross(t0, n0))

    prev_tangent = t0
    prev_normal = n0
    prev_binormal = b0

    num_pts = len(points)
    for i in range(num_pts):
        pt = points[i]
        # Compute tangent
        if i < num_pts - 1:
            tangent = vec3_normalize(vec3_sub(points[i + 1], pt))
        else:
            tangent = prev_tangent

        # Transport normal via reflection / rotation minimizing frame
        v1 = vec3_sub(tangent, prev_tangent)
        c1 = vec3_dot(v1, v1)
        if c1 > 1e-12:
            r = prev_normal
            normal = vec3_sub(r, vec3_scale(v1, 2.0 * vec3_dot(v1, r) / c1))
            normal = vec3_normalize(normal)
        else:
            normal = prev_normal

        binormal = vec3_normalize(vec3_cross(tangent, normal))
        prev_tangent, prev_normal, prev_binormal = tangent, normal, binormal

        # Color based on normalized velocity: Blue (low) -> Cyan -> Magenta -> Yellow/Orange (high)
        nv = (velocities[i] - v_min) / v_range
        r_col = min(1.0, max(0.1, nv * 1.5))
        g_col = min(1.0, max(0.2, (1.0 - abs(nv - 0.5) * 2.0)))
        b_col = min(1.0, max(0.3, (1.0 - nv)))
        color = [round(r_col, 3), round(g_col, 3), round(b_col, 3)]

        u_coord = i / float(num_pts - 1)

        # Generate ring of vertices
        for s in range(tube_segments):
            theta = (2.0 * math.pi * s) / tube_segments
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)

            rad_vec = vec3_add(vec3_scale(normal, cos_t), vec3_scale(binormal, sin_t))
            vx = pt[0] + tube_radius * rad_vec[0]
            vy = pt[1] + tube_radius * rad_vec[1]
            vz = pt[2] + tube_radius * rad_vec[2]

            vertices.append([round(vx, 5), round(vy, 5), round(vz, 5)])
            normals.append([round(rad_vec[0], 4), round(rad_vec[1], 4), round(rad_vec[2], 4)])
            colors.append(color)
            uvs.append([round(u_coord, 4), round(s / float(tube_segments), 4)])

    # Construct quad / triangle faces between consecutive rings
    for i in range(num_pts - 1):
        ring_curr = i * tube_segments
        ring_next = (i + 1) * tube_segments
        for s in range(tube_segments):
            s_next = (s + 1) % tube_segments
            v0 = ring_curr + s
            v1 = ring_curr + s_next
            v2 = ring_next + s_next
            v3 = ring_next + s
            faces.append([v0, v1, v2, v3])

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        uvs=uvs,
        colors=colors,
        name=f"attractor_{atype}",
        metadata={
            "generator": "strange_attractor",
            "type": atype,
            "steps": steps,
            "tube_radius": tube_radius,
            "tube_segments": tube_segments,
        },
    )


# ---------------------------------------------------------------------------
# Klein Bottle Immersion
# ---------------------------------------------------------------------------

def generate_klein_bottle(
    u_segments: int = 32,
    v_segments: int = 16,
    scale: float = 1.0,
) -> MeshData:
    """Generate a 3D figure-8 immersion of the 4D non-orientable Klein Bottle.

    Parametric formula:
        r = 2.0 - cos(u)
        x = (r * cos(u/2) * cos(v) - sin(u/2) * sin(2*v)) * scale
        y = (r * sin(u/2) * cos(v) + cos(u/2) * sin(2*v)) * scale
        z = r * sin(v) * scale
    """
    vertices: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []
    colors: List[List[float]] = []
    faces: List[List[int]] = []

    for i in range(u_segments):
        u = (2.0 * math.pi * i) / u_segments
        cos_u = math.cos(u)
        cos_u2 = math.cos(u / 2.0)
        sin_u2 = math.sin(u / 2.0)
        r = 2.0 - cos_u

        for j in range(v_segments):
            v = (2.0 * math.pi * j) / v_segments
            cos_v = math.cos(v)
            sin_v = math.sin(v)
            sin_2v = math.sin(2.0 * v)

            x = (r * cos_u2 * cos_v - sin_u2 * sin_2v) * scale
            y = (r * sin_u2 * cos_v + cos_u2 * sin_2v) * scale
            z = (r * sin_v) * scale

            vertices.append([round(x, 5), round(y, 5), round(z, 5)])
            norm_len = math.sqrt(x * x + y * y + z * z) or 1.0
            normals.append([round(x / norm_len, 4), round(y / norm_len, 4), round(z / norm_len, 4)])
            uvs.append([round(i / float(u_segments), 4), round(j / float(v_segments), 4)])

            # Iridescent dual-sided palette
            cr = 0.5 + 0.5 * math.sin(u)
            cg = 0.5 + 0.5 * math.cos(v)
            cb = 0.7 + 0.3 * math.sin(u + v)
            colors.append([round(cr, 3), round(cg, 3), round(cb, 3)])

    for i in range(u_segments):
        i_next = (i + 1) % u_segments
        for j in range(v_segments):
            j_next = (j + 1) % v_segments
            v0 = i * v_segments + j
            v1 = i * v_segments + j_next
            v2 = i_next * v_segments + j_next
            v3 = i_next * v_segments + j
            faces.append([v0, v1, v2, v3])

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        uvs=uvs,
        colors=colors,
        name="klein_bottle",
        metadata={"generator": "klein_bottle", "u_segments": u_segments, "v_segments": v_segments},
    )


# ---------------------------------------------------------------------------
# Menger Sponge 3D Fractal
# ---------------------------------------------------------------------------

def generate_menger_sponge(
    level: int = 1,
    size: float = 2.0,
) -> MeshData:
    """Generate recursive 3D Menger Sponge fractal cube mesh.

    Level 0 = 1 cube
    Level 1 = 20 subcubes (removes central cross)
    Level 2 = 400 subcubes
    """
    level = max(0, min(2, level))  # Clamped to prevent exponential vertex explosion in tests

    def get_subcube_centers(cx: float, cy: float, cz: float, s: float, lvl: int) -> List[Tuple[float, float, float, float]]:
        if lvl == 0:
            return [(cx, cy, cz, s)]

        step = s / 3.0
        results: List[Tuple[float, float, float, float]] = []
        for ix in (-1, 0, 1):
            for iy in (-1, 0, 1):
                for iz in (-1, 0, 1):
                    # In a Menger sponge, keep subcube only if at most one coordinate is 0
                    zeros = (ix == 0) + (iy == 0) + (iz == 0)
                    if zeros <= 1:
                        sub_cx = cx + ix * step
                        sub_cy = cy + iy * step
                        sub_cz = cz + iz * step
                        results.extend(get_subcube_centers(sub_cx, sub_cy, sub_cz, step, lvl - 1))
        return results

    cubes = get_subcube_centers(0.0, 0.0, 0.0, size, level)
    vertices: List[List[float]] = []
    faces: List[List[int]] = []
    colors: List[List[float]] = []

    # Cube template relative to center
    for cx, cy, cz, s in cubes:
        hs = s * 0.5
        base_idx = len(vertices)
        # 8 corners
        corners = [
            [cx - hs, cy - hs, cz - hs],
            [cx + hs, cy - hs, cz - hs],
            [cx + hs, cy + hs, cz - hs],
            [cx - hs, cy + hs, cz - hs],
            [cx - hs, cy - hs, cz + hs],
            [cx + hs, cy - hs, cz + hs],
            [cx + hs, cy + hs, cz + hs],
            [cx - hs, cy + hs, cz + hs],
        ]
        vertices.extend([[round(c[0], 5), round(c[1], 5), round(c[2], 5)] for c in corners])
        col = [0.2 + 0.6 * ((cx + size) / (2.0 * size)), 0.6, 0.8]
        colors.extend([col] * 8)

        # 6 quad faces
        cube_faces = [
            [base_idx + 0, base_idx + 3, base_idx + 2, base_idx + 1],  # Back
            [base_idx + 4, base_idx + 5, base_idx + 6, base_idx + 7],  # Front
            [base_idx + 0, base_idx + 1, base_idx + 5, base_idx + 4],  # Bottom
            [base_idx + 2, base_idx + 3, base_idx + 7, base_idx + 6],  # Top
            [base_idx + 0, base_idx + 4, base_idx + 7, base_idx + 3],  # Left
            [base_idx + 1, base_idx + 2, base_idx + 6, base_idx + 5],  # Right
        ]
        faces.extend(cube_faces)

    return MeshData(
        vertices=vertices,
        faces=faces,
        colors=colors,
        name=f"menger_sponge_l{level}",
        metadata={"generator": "menger_sponge", "level": level, "cubes_count": len(cubes)},
    )


# ---------------------------------------------------------------------------
# Level-of-Detail (LOD) Decimator & Chain Generator
# ---------------------------------------------------------------------------

def decimate_mesh(
    mesh_data: Union[MeshData, Dict[str, Any]],
    target_ratio: float = 0.5,
) -> MeshData:
    """Decimate a mesh polygon count towards target_ratio using edge-length contraction.

    Args:
        mesh_data: Input MeshData.
        target_ratio: Desired ratio of faces to retain (e.g. 0.5 = 50% polygons).

    Returns:
        Decimated MeshData with reduced polygon count.
    """
    mesh = ensure_mesh_data(mesh_data)
    vertices = [list(v) for v in mesh.vertices]
    faces = [list(f) for f in mesh.faces]

    if not faces or target_ratio >= 0.99:
        return mesh

    target_face_count = max(4, int(len(faces) * target_ratio))

    # Convert all faces to triangles first
    tri_faces: List[List[int]] = []
    for f in faces:
        if len(f) == 3:
            tri_faces.append(list(f))
        elif len(f) > 3:
            for k in range(1, len(f) - 1):
                tri_faces.append([f[0], f[k], f[k + 1]])

    # Build unique edge list with lengths
    edge_map: Dict[Tuple[int, int], float] = {}
    for tri in tri_faces:
        for a, b in [(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])]:
            edge = (min(a, b), max(a, b))
            if edge not in edge_map:
                v1, v2 = vertices[edge[0]], vertices[edge[1]]
                edge_map[edge] = vec3_length(vec3_sub(v1, v2))

    # Sort edges by length (collapse shortest edges first to minimize shape distortion)
    sorted_edges = sorted(edge_map.keys(), key=lambda e: edge_map[e])

    remap: Dict[int, int] = {i: i for i in range(len(vertices))}

    def get_root(i: int) -> int:
        while remap[i] != i:
            remap[i] = remap[remap[i]]
            i = remap[i]
        return i

    collapsed_count = 0
    max_collapses = max(1, len(tri_faces) - target_face_count)

    for u, v in sorted_edges:
        if collapsed_count >= max_collapses:
            break

        root_u = get_root(u)
        root_v = get_root(v)
        if root_u == root_v:
            continue

        # Collapse v into u, midpoint coordinate
        p_u = vertices[root_u]
        p_v = vertices[root_v]
        mid = [0.5 * (p_u[0] + p_v[0]), 0.5 * (p_u[1] + p_v[1]), 0.5 * (p_u[2] + p_v[2])]
        vertices[root_u] = mid
        remap[root_v] = root_u
        collapsed_count += 1

    # Remap faces and filter degenerate ones
    new_faces: List[List[int]] = []
    for tri in tri_faces:
        r0 = get_root(tri[0])
        r1 = get_root(tri[1])
        r2 = get_root(tri[2])
        if r0 != r1 and r1 != r2 and r2 != r0:
            new_faces.append([r0, r1, r2])

    # Compact vertex array
    used_indices = sorted(list({idx for face in new_faces for idx in face}))
    compact_map = {old: new for new, old in enumerate(used_indices)}

    compact_vertices = [vertices[idx] for idx in used_indices]
    compact_faces = [[compact_map[idx] for idx in face] for face in new_faces]

    return MeshData(
        vertices=compact_vertices,
        faces=compact_faces,
        name=f"{mesh.name}_lod_{int(target_ratio * 100)}",
        metadata={
            **mesh.metadata,
            "decimated": True,
            "original_faces": len(faces),
            "decimated_faces": len(compact_faces),
            "ratio": target_ratio,
        },
    )


def generate_lod_pyramid(
    mesh_data: Union[MeshData, Dict[str, Any]],
    lod_ratios: Sequence[float] = (1.0, 0.5, 0.25, 0.1),
) -> Dict[str, Any]:
    """Generate a multi-tier Level-of-Detail (LOD) pyramid for 3D asset streaming.

    Returns:
        Dictionary with:
            - 'levels': Dict of LOD level MeshData objects ('lod0', 'lod1', 'lod2', 'lod3')
            - 'summary': Summary table of face counts, reduction ratios, and recommended switch distances.
    """
    mesh = ensure_mesh_data(mesh_data)
    lod_levels: Dict[str, MeshData] = {}
    summary: List[Dict[str, Any]] = []

    # Compute bounding sphere radius for view distance calculation
    if mesh.vertices:
        max_dist = max(math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) for v in mesh.vertices)
    else:
        max_dist = 1.0

    for idx, ratio in enumerate(lod_ratios):
        level_name = f"lod{idx}"
        if ratio >= 0.99:
            lod_mesh = mesh
        else:
            lod_mesh = decimate_mesh(mesh, target_ratio=ratio)

        lod_levels[level_name] = lod_mesh
        # Recommended view switch distance formula: D = 3.0 * radius * (1.0 / ratio)
        switch_dist = round(max_dist * (2.0 + idx * 3.0), 2)

        summary.append({
            "level": level_name,
            "ratio": ratio,
            "vertex_count": len(lod_mesh.vertices),
            "face_count": len(lod_mesh.faces),
            "reduction_percent": round((1.0 - (len(lod_mesh.faces) / max(1, len(mesh.faces)))) * 100, 1),
            "switch_distance_units": switch_dist,
        })

    return {
        "levels": lod_levels,
        "summary": summary,
        "base_mesh_name": mesh.name,
    }
