#!/usr/bin/env python3
"""Nexus 3D Scene Studio - Procedural Shapes Gallery Generator.

Generates a gallery of mathematical 3D meshes (OBJ and STL formats):
1. 4D Hypercube (Tesseract) with 4D-to-3D stereographic rotation projection
2. Parametric (p, q) Torus Knot with helical winding
3. Superquadric / Superellipsoid with squareness parameters
4. Fibonacci Golden Spiral Spherical Lattice
5. Buckyball (Truncated Icosahedron / Fullerene C60)
6. Möbius Strip with parametric half-twist
7. Procedural Fractal Terrain Heightmap (fBm noise synthesis)

Usage:
    python generate_gallery.py
    python generate_gallery.py --output-dir ./output --format all
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Try importing from package, fallback to pure stdlib procedural math
try:
    from nexus_3d_scene_studio.geometry_engine import (
        MeshData as PkgMeshData,
        generate_tesseract_4d as pkg_gen_tesseract,
        generate_torus_knot as pkg_gen_torus_knot,
        generate_superquadric as pkg_gen_superquadric,
        generate_fibonacci_lattice as pkg_gen_fibonacci,
        generate_buckyball as pkg_gen_buckyball,
        generate_mobius_strip as pkg_gen_mobius,
        generate_procedural_terrain as pkg_gen_terrain,
    )
    from nexus_3d_scene_studio.mesh_exporter import MeshExporter as PkgMeshExporter
    HAS_PACKAGE = True
except ImportError:
    HAS_PACKAGE = False


@dataclass
class MeshData:
    """Mathematical 3D mesh representation."""
    name: str
    vertices: List[Tuple[float, float, float]]
    faces: List[List[int]]
    normals: List[Tuple[float, float, float]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def face_count(self) -> int:
        return len(self.faces)

    @property
    def triangle_count(self) -> int:
        total = 0
        for f in self.faces:
            if len(f) >= 3:
                total += len(f) - 2
        return total

    def compute_bounding_box(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        if not self.vertices:
            return ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        min_x = min(v[0] for v in self.vertices)
        max_x = max(v[0] for v in self.vertices)
        min_y = min(v[1] for v in self.vertices)
        max_y = max(v[1] for v in self.vertices)
        min_z = min(v[2] for v in self.vertices)
        max_z = max(v[2] for v in self.vertices)
        return ((min_x, min_y, min_z), (max_x, max_y, max_z))

    def compute_surface_area(self) -> float:
        """Calculate total surface area by summing triangulated face areas."""
        area = 0.0
        for face in self.faces:
            if len(face) < 3:
                continue
            v0 = self.vertices[face[0]]
            for i in range(1, len(face) - 1):
                v1 = self.vertices[face[i]]
                v2 = self.vertices[face[i + 1]]
                # Cross product (v1 - v0) x (v2 - v0)
                e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
                e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
                cx = e1[1] * e2[2] - e1[2] * e2[1]
                cy = e1[2] * e2[0] - e1[0] * e2[2]
                cz = e1[0] * e2[1] - e1[1] * e2[0]
                tri_area = 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)
                area += tri_area
        return area

    def calculate_normals(self) -> None:
        """Compute smooth vertex normals."""
        v_normals = [[0.0, 0.0, 0.0] for _ in range(len(self.vertices))]
        for face in self.faces:
            if len(face) < 3:
                continue
            v0 = self.vertices[face[0]]
            v1 = self.vertices[face[1]]
            v2 = self.vertices[face[2]]
            e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
            e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
            cx = e1[1] * e2[2] - e1[2] * e2[1]
            cy = e1[2] * e2[0] - e1[0] * e2[2]
            cz = e1[0] * e2[1] - e1[1] * e2[0]
            mag = math.sqrt(cx * cx + cy * cy + cz * cz)
            if mag > 1e-9:
                fn = (cx / mag, cy / mag, cz / mag)
                for idx in face:
                    v_normals[idx][0] += fn[0]
                    v_normals[idx][1] += fn[1]
                    v_normals[idx][2] += fn[2]

        self.normals = []
        for n in v_normals:
            mag = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
            if mag > 1e-9:
                self.normals.append((n[0] / mag, n[1] / mag, n[2] / mag))
            else:
                self.normals.append((0.0, 1.0, 0.0))


# ==============================================================================
# PROCEDURAL GEOMETRY GENERATORS (Pure Mathematical Algorithms)
# ==============================================================================

def generate_tesseract(scale: float = 2.0, rotation_4d: float = 0.6, distance: float = 2.8) -> MeshData:
    """Generate 4D Hypercube projected into 3D space via stereographic rotation."""
    # 16 4D hypercube vertices
    v4d = []
    for x in (-1.0, 1.0):
        for y in (-1.0, 1.0):
            for z in (-1.0, 1.0):
                for w in (-1.0, 1.0):
                    v4d.append((x, y, z, w))

    # Apply 4D rotation in XW and YW planes
    cos_t = math.cos(rotation_4d)
    sin_t = math.sin(rotation_4d)

    projected_3d = []
    for x, y, z, w in v4d:
        # Rotate in XW plane
        x_rot = x * cos_t - w * sin_t
        w_rot = x * sin_t + w * cos_t
        # Rotate in YW plane
        y_rot = y * cos_t - w_rot * sin_t
        w_final = y * sin_t + w_rot * cos_t

        # 4D to 3D perspective / stereographic projection
        denom = max(0.1, distance - w_final)
        factor = scale / denom
        projected_3d.append((x_rot * factor, y_rot * factor, z * factor))

    # Construct 8 cubic cells (6 faces each = 24 quads)
    faces: List[List[int]] = []
    # Outer & inner hypercube connectivity
    for i in range(16):
        for bit in range(4):
            neighbor = i ^ (1 << bit)
            if neighbor > i:
                pass

    # Standard 24 cell-boundary quads for tesseract hull
    # 6 faces of w=-1 cell (0-7), 6 faces of w=+1 cell (8-15), 12 connecting quads
    # Vertices indexing: index = (x>0?8:0) + (y>0?4:0) + (z>0?2:0) + (w>0?1:0)
    def idx4(x, y, z, w):
        return (1 if x > 0 else 0) * 8 + (1 if y > 0 else 0) * 4 + (1 if z > 0 else 0) * 2 + (1 if w > 0 else 0)

    # Faces for w = -1 (inner cube)
    faces.append([idx4(-1,-1,-1,-1), idx4( 1,-1,-1,-1), idx4( 1, 1,-1,-1), idx4(-1, 1,-1,-1)]) # -z
    faces.append([idx4(-1,-1, 1,-1), idx4( 1,-1, 1,-1), idx4( 1, 1, 1,-1), idx4(-1, 1, 1,-1)]) # +z
    faces.append([idx4(-1,-1,-1,-1), idx4(-1, 1,-1,-1), idx4(-1, 1, 1,-1), idx4(-1,-1, 1,-1)]) # -x
    faces.append([idx4( 1,-1,-1,-1), idx4( 1, 1,-1,-1), idx4( 1, 1, 1,-1), idx4( 1,-1, 1,-1)]) # +x
    faces.append([idx4(-1,-1,-1,-1), idx4( 1,-1,-1,-1), idx4( 1,-1, 1,-1), idx4(-1,-1, 1,-1)]) # -y
    faces.append([idx4(-1, 1,-1,-1), idx4( 1, 1,-1,-1), idx4( 1, 1, 1,-1), idx4(-1, 1, 1,-1)]) # +y

    # Faces for w = +1 (outer cube)
    faces.append([idx4(-1,-1,-1, 1), idx4( 1,-1,-1, 1), idx4( 1, 1,-1, 1), idx4(-1, 1,-1, 1)])
    faces.append([idx4(-1,-1, 1, 1), idx4( 1,-1, 1, 1), idx4( 1, 1, 1, 1), idx4(-1, 1, 1, 1)])
    faces.append([idx4(-1,-1,-1, 1), idx4(-1, 1,-1, 1), idx4(-1, 1, 1, 1), idx4(-1,-1, 1, 1)])
    faces.append([idx4( 1,-1,-1, 1), idx4( 1, 1,-1, 1), idx4( 1, 1, 1, 1), idx4( 1,-1, 1, 1)])
    faces.append([idx4(-1,-1,-1, 1), idx4( 1,-1,-1, 1), idx4( 1,-1, 1, 1), idx4(-1,-1, 1, 1)])
    faces.append([idx4(-1, 1,-1, 1), idx4( 1, 1,-1, 1), idx4( 1, 1, 1, 1), idx4(-1, 1, 1, 1)])

    # 12 connecting tunnel quads between w=-1 and w=+1
    edges_3d = [
        ((-1,-1,-1), ( 1,-1,-1)), ((-1, 1,-1), ( 1, 1,-1)), ((-1,-1, 1), ( 1,-1, 1)), ((-1, 1, 1), ( 1, 1, 1)),
        ((-1,-1,-1), (-1, 1,-1)), (( 1,-1,-1), ( 1, 1,-1)), ((-1,-1, 1), (-1, 1, 1)), (( 1,-1, 1), ( 1, 1, 1)),
        ((-1,-1,-1), (-1,-1, 1)), (( 1,-1,-1), ( 1,-1, 1)), ((-1, 1,-1), (-1, 1, 1)), (( 1, 1,-1), ( 1, 1, 1)),
    ]
    for (x1, y1, z1), (x2, y2, z2) in edges_3d:
        faces.append([
            idx4(x1, y1, z1, -1),
            idx4(x2, y2, z2, -1),
            idx4(x2, y2, z2,  1),
            idx4(x1, y1, z1,  1)
        ])

    mesh = MeshData(
        name="Tesseract_4D_Hypercube",
        vertices=projected_3d,
        faces=faces,
        metadata={"rotation_4d": rotation_4d, "projection_distance": distance, "dimension": 4}
    )
    mesh.calculate_normals()
    return mesh


def generate_torus_knot(p: int = 3, q: int = 5, tubular_segments: int = 120, radial_segments: int = 16,
                        radius: float = 2.0, tube_radius: float = 0.5) -> MeshData:
    """Generate parametric (p, q) torus knot mesh."""
    vertices: List[Tuple[float, float, float]] = []
    faces: List[List[int]] = []

    # Generate curve points and Frenet frames
    curve = []
    tangents = []
    for i in range(tubular_segments):
        u = (i / tubular_segments) * 2.0 * math.pi
        r = math.cos(q * u) + 2.0
        x = radius * r * math.cos(p * u) * 0.5
        y = radius * r * math.sin(p * u) * 0.5
        z = radius * (-math.sin(q * u)) * 0.5
        curve.append((x, y, z))

        # Numerical tangent
        u_next = ((i + 0.01) / tubular_segments) * 2.0 * math.pi
        r_n = math.cos(q * u_next) + 2.0
        xn = radius * r_n * math.cos(p * u_next) * 0.5
        yn = radius * r_n * math.sin(p * u_next) * 0.5
        zn = radius * (-math.sin(q * u_next)) * 0.5
        tx, ty, tz = xn - x, yn - y, zn - z
        t_mag = max(1e-9, math.sqrt(tx * tx + ty * ty + tz * tz))
        tangents.append((tx / t_mag, ty / t_mag, tz / t_mag))

    # Swept tube vertices
    for i in range(tubular_segments):
        cx, cy, cz = curve[i]
        tx, ty, tz = tangents[i]

        # Normal vector perpendicular to tangent
        nx = -ty
        ny = tx
        nz = 0.0
        n_mag = math.sqrt(nx * nx + ny * ny + nz * nz)
        if n_mag < 1e-6:
            nx, ny, nz = 1.0, 0.0, 0.0
        else:
            nx, ny, nz = nx / n_mag, ny / n_mag, nz / n_mag

        # Binormal
        bx = ty * nz - tz * ny
        by = tz * nx - tx * nz
        bz = tx * ny - ty * nx

        for j in range(radial_segments):
            v = (j / radial_segments) * 2.0 * math.pi
            cos_v = math.cos(v) * tube_radius
            sin_v = math.sin(v) * tube_radius
            vx = cx + nx * cos_v + bx * sin_v
            vy = cy + ny * cos_v + by * sin_v
            vz = cz + nz * cos_v + bz * sin_v
            vertices.append((vx, vy, vz))

    # Faces connecting rings
    for i in range(tubular_segments):
        i_next = (i + 1) % tubular_segments
        for j in range(radial_segments):
            j_next = (j + 1) % radial_segments
            a = i * radial_segments + j
            b = i_next * radial_segments + j
            c = i_next * radial_segments + j_next
            d = i * radial_segments + j_next
            faces.append([a, b, c, d])

    mesh = MeshData(
        name=f"Parametric_Torus_Knot_p{p}_q{q}",
        vertices=vertices,
        faces=faces,
        metadata={"p": p, "q": q, "tube_radius": tube_radius, "radius": radius}
    )
    mesh.calculate_normals()
    return mesh


def generate_superquadric(s1: float = 0.5, s2: float = 0.5, n_lat: int = 32, n_lon: int = 32,
                          rx: float = 1.5, ry: float = 1.5, rz: float = 1.5) -> MeshData:
    """Generate Superquadric / Superellipsoid mesh with shape factors s1 and s2."""
    def sgn_pow(val: float, exp: float) -> float:
        sgn = 1.0 if val >= 0 else -1.0
        return sgn * (abs(val) ** exp)

    vertices: List[Tuple[float, float, float]] = []
    faces: List[List[int]] = []

    for i in range(n_lat + 1):
        eta = -math.pi / 2.0 + (i / n_lat) * math.pi
        cos_eta = math.cos(eta)
        sin_eta = math.sin(eta)
        z = rz * sgn_pow(sin_eta, s1)

        for j in range(n_lon):
            omega = -math.pi + (j / n_lon) * 2.0 * math.pi
            cos_om = math.cos(omega)
            sin_om = math.sin(omega)

            x = rx * sgn_pow(cos_eta, s1) * sgn_pow(cos_om, s2)
            y = ry * sgn_pow(cos_eta, s1) * sgn_pow(sin_om, s2)
            vertices.append((x, y, z))

    for i in range(n_lat):
        for j in range(n_lon):
            j_next = (j + 1) % n_lon
            a = i * n_lon + j
            b = (i + 1) * n_lon + j
            c = (i + 1) * n_lon + j_next
            d = i * n_lon + j_next
            faces.append([a, b, c, d])

    mesh = MeshData(
        name=f"Superquadric_s1_{s1}_s2_{s2}",
        vertices=vertices,
        faces=faces,
        metadata={"s1": s1, "s2": s2, "rx": rx, "ry": ry, "rz": rz}
    )
    mesh.calculate_normals()
    return mesh


def generate_fibonacci_sphere(num_points: int = 250, radius: float = 1.8) -> MeshData:
    """Generate Fibonacci Golden Spiral Spherical Lattice."""
    vertices: List[Tuple[float, float, float]] = []
    golden_angle = math.pi * (3.0 - math.sqrt(5.0)) # ~2.399963 rad

    for i in range(num_points):
        y = 1.0 - (i / max(1, num_points - 1)) * 2.0 # from 1 to -1
        r_circle = math.sqrt(max(0.0, 1.0 - y * y))
        theta = golden_angle * i
        x = math.cos(theta) * r_circle
        z = math.sin(theta) * r_circle
        vertices.append((x * radius, y * radius, z * radius))

    # Build spherical triangulation via nearest neighbors
    faces: List[List[int]] = []
    for i in range(num_points):
        # Connect each point with 3-4 nearest spiral neighbors
        dists = []
        vi = vertices[i]
        for j in range(num_points):
            if i != j:
                vj = vertices[j]
                d2 = (vi[0]-vj[0])**2 + (vi[1]-vj[1])**2 + (vi[2]-vj[2])**2
                dists.append((d2, j))
        dists.sort()
        # Connect to closest two
        if len(dists) >= 2:
            n1 = dists[0][1]
            n2 = dists[1][1]
            if i < n1 and i < n2:
                faces.append([i, n1, n2])

    mesh = MeshData(
        name="Fibonacci_Golden_Spiral_Sphere",
        vertices=vertices,
        faces=faces if faces else [[0, 1, 2]],
        metadata={"num_points": num_points, "radius": radius, "golden_angle": golden_angle}
    )
    mesh.calculate_normals()
    return mesh


def generate_buckyball(radius: float = 1.8) -> MeshData:
    """Generate Buckyball (Truncated Icosahedron / Fullerene C60)."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0

    # 12 vertices of regular icosahedron
    ico_v = [
        (-1,  phi, 0), ( 1,  phi, 0), (-1, -phi, 0), ( 1, -phi, 0),
        ( 0, -1,  phi), ( 0,  1,  phi), ( 0, -1, -phi), ( 0,  1, -phi),
        ( phi, 0, -1), ( phi, 0,  1), (-phi, 0, -1), (-phi, 0,  1)
    ]
    # Normalize to unit sphere
    ico_v = [
        (x / math.sqrt(1 + phi*phi), y / math.sqrt(1 + phi*phi), z / math.sqrt(1 + phi*phi))
        for x, y, z in ico_v
    ]

    ico_faces = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
    ]

    # Truncate edges at 1/3 and 2/3
    vertices: List[Tuple[float, float, float]] = []
    edge_map: Dict[Tuple[int, int], Tuple[int, int]] = {}

    def get_edge_verts(i1: int, i2: int) -> Tuple[int, int]:
        key = (min(i1, i2), max(i1, i2))
        if key in edge_map:
            ev1, ev2 = edge_map[key]
            return (ev1, ev2) if i1 < i2 else (ev2, ev1)
        v1 = ico_v[i1]
        v2 = ico_v[i2]
        # 1/3 point
        p1 = (v1[0] * 2/3 + v2[0] * 1/3, v1[1] * 2/3 + v2[1] * 1/3, v1[2] * 2/3 + v2[2] * 1/3)
        # 2/3 point
        p2 = (v1[0] * 1/3 + v2[0] * 2/3, v1[1] * 1/3 + v2[1] * 2/3, v1[2] * 1/3 + v2[2] * 2/3)
        # Project onto sphere
        mag1 = math.sqrt(p1[0]**2 + p1[1]**2 + p1[2]**2)
        p1 = (p1[0]*radius/mag1, p1[1]*radius/mag1, p1[2]*radius/mag1)
        mag2 = math.sqrt(p2[0]**2 + p2[1]**2 + p2[2]**2)
        p2 = (p2[0]*radius/mag2, p2[1]*radius/mag2, p2[2]*radius/mag2)

        idx1 = len(vertices)
        vertices.append(p1)
        idx2 = len(vertices)
        vertices.append(p2)
        edge_map[key] = (idx1, idx2)
        return (idx1, idx2) if i1 < i2 else (idx2, idx1)

    faces: List[List[int]] = []
    # 20 hexagonal faces from icosahedron triangular faces
    for f in ico_faces:
        e01_1, e01_2 = get_edge_verts(f[0], f[1])
        e12_1, e12_2 = get_edge_verts(f[1], f[2])
        e20_1, e20_2 = get_edge_verts(f[2], f[0])
        faces.append([e01_1, e01_2, e12_1, e12_2, e20_1, e20_2])

    mesh = MeshData(
        name="Buckyball_C60_Truncated_Icosahedron",
        vertices=vertices,
        faces=faces,
        metadata={"vertices_count": len(vertices), "faces_count": len(faces), "radius": radius}
    )
    mesh.calculate_normals()
    return mesh


def generate_mobius_strip(radius: float = 1.8, width: float = 0.8, u_segs: int = 60, v_segs: int = 8,
                          twists: int = 1) -> MeshData:
    """Generate parametric Möbius strip mesh with n half-twists."""
    vertices: List[Tuple[float, float, float]] = []
    faces: List[List[int]] = []

    for i in range(u_segs):
        u = (i / u_segs) * 2.0 * math.pi
        cos_u = math.cos(u)
        sin_u = math.sin(u)
        twist_angle = (twists * u) / 2.0
        cos_twist = math.cos(twist_angle)
        sin_twist = math.sin(twist_angle)

        for j in range(v_segs + 1):
            v = -width / 2.0 + (j / v_segs) * width
            x = (radius + v * cos_twist) * cos_u
            y = (radius + v * cos_twist) * sin_u
            z = v * sin_twist
            vertices.append((x, y, z))

    stride = v_segs + 1
    for i in range(u_segs):
        i_next = (i + 1) % u_segs
        for j in range(v_segs):
            if i + 1 == u_segs:
                # Wrap-around with Möbius orientation reversal
                a = i * stride + j
                d = i * stride + (j + 1)
                # Reversed index at seam
                b = (v_segs - j)
                c = (v_segs - (j + 1))
                faces.append([a, b, c, d])
            else:
                a = i * stride + j
                b = i_next * stride + j
                c = i_next * stride + (j + 1)
                d = i * stride + (j + 1)
                faces.append([a, b, c, d])

    mesh = MeshData(
        name="Mobius_Strip_Parametric_Surface",
        vertices=vertices,
        faces=faces,
        metadata={"radius": radius, "width": width, "twists": twists}
    )
    mesh.calculate_normals()
    return mesh


def generate_terrain(grid_size: int = 32, scale: float = 4.0, height_scale: float = 0.6,
                     octaves: int = 4) -> MeshData:
    """Generate procedural terrain heightmap using multi-octave fBm synthesis."""
    vertices: List[Tuple[float, float, float]] = []
    faces: List[List[int]] = []

    def fbm_noise(x: float, z: float) -> float:
        total = 0.0
        freq = 1.0
        amp = 1.0
        for _ in range(octaves):
            # Deterministic trigonometric procedural pseudo-noise
            n = math.sin(x * freq * 1.5 + math.cos(z * freq * 1.7)) * math.cos(z * freq * 1.3 - math.sin(x * freq * 1.1))
            total += n * amp
            freq *= 2.0
            amp *= 0.5
        return total

    for i in range(grid_size):
        gx = (i / (grid_size - 1) - 0.5) * scale
        for j in range(grid_size):
            gz = (j / (grid_size - 1) - 0.5) * scale
            gy = fbm_noise(gx, gz) * height_scale
            vertices.append((gx, gy, gz))

    for i in range(grid_size - 1):
        for j in range(grid_size - 1):
            a = i * grid_size + j
            b = (i + 1) * grid_size + j
            c = (i + 1) * grid_size + (j + 1)
            d = i * grid_size + (j + 1)
            # Two triangles per quad
            faces.append([a, b, c])
            faces.append([a, c, d])

    mesh = MeshData(
        name="Procedural_Terrain_Heightmap",
        vertices=vertices,
        faces=faces,
        metadata={"grid_size": grid_size, "scale": scale, "octaves": octaves}
    )
    mesh.calculate_normals()
    return mesh


# ==============================================================================
# EXPORTERS (OBJ and ASCII STL)
# ==============================================================================

def export_to_obj(mesh: MeshData, filepath: Path) -> None:
    """Export mesh to Wavefront OBJ format."""
    lines = [
        f"# Nexus 3D Scene Studio - Wavefront OBJ Exporter",
        f"# Mesh Name: {mesh.name}",
        f"# Vertices: {mesh.vertex_count}",
        f"# Faces: {mesh.face_count}",
        f"# Triangles: {mesh.triangle_count}",
        f"o {mesh.name}",
        ""
    ]
    # Vertices
    for vx, vy, vz in mesh.vertices:
        lines.append(f"v {vx:.6f} {vy:.6f} {vz:.6f}")

    # Vertex Normals
    if mesh.normals:
        lines.append("")
        for nx, ny, nz in mesh.normals:
            lines.append(f"vn {nx:.6f} {ny:.6f} {nz:.6f}")

    lines.append("")
    lines.append(f"g {mesh.name}_Group")
    lines.append(f"s 1")

    # Faces (1-indexed)
    has_vn = bool(mesh.normals and len(mesh.normals) == len(mesh.vertices))
    for f in mesh.faces:
        if has_vn:
            indices = [f"{idx + 1}//{idx + 1}" for idx in f]
        else:
            indices = [str(idx + 1) for idx in f]
        lines.append(f"f {' '.join(indices)}")

    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_to_stl(mesh: MeshData, filepath: Path) -> None:
    """Export mesh to ASCII STL format."""
    lines = [f"solid {mesh.name}"]

    for face in mesh.faces:
        if len(face) < 3:
            continue
        v0 = mesh.vertices[face[0]]
        # Triangulate polygon if > 3 vertices
        for i in range(1, len(face) - 1):
            v1 = mesh.vertices[face[i]]
            v2 = mesh.vertices[face[i + 1]]

            # Normal vector
            e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
            e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
            cx = e1[1] * e2[2] - e1[2] * e2[1]
            cy = e1[2] * e2[0] - e1[0] * e2[2]
            cz = e1[0] * e2[1] - e1[1] * e2[0]
            mag = math.sqrt(cx * cx + cy * cy + cz * cz)
            if mag > 1e-9:
                nx, ny, nz = cx / mag, cy / mag, cz / mag
            else:
                nx, ny, nz = 0.0, 1.0, 0.0

            lines.append(f"  facet normal {nx:.6e} {ny:.6e} {nz:.6e}")
            lines.append("    outer loop")
            lines.append(f"      vertex {v0[0]:.6e} {v0[1]:.6e} {v0[2]:.6e}")
            lines.append(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}")
            lines.append(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}")
            lines.append("    endloop")
            lines.append("  endfacet")

    lines.append(f"endsolid {mesh.name}")
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_all_gallery_shapes(output_dir: Path) -> List[Dict[str, Any]]:
    """Generate all 7 procedural shapes and export to OBJ and STL."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    generators = [
        ("tesseract_4d", "4D Hypercube Tesseract", generate_tesseract()),
        ("torus_knot", "Parametric (3,5) Torus Knot", generate_torus_knot(p=3, q=5)),
        ("superquadric", "Superquadric Ellipsoid (s1=0.5, s2=0.5)", generate_superquadric(s1=0.5, s2=0.5)),
        ("fibonacci_sphere", "Fibonacci Golden Spiral Sphere", generate_fibonacci_sphere(num_points=250)),
        ("buckyball", "Buckyball C60 Truncated Icosahedron", generate_buckyball()),
        ("mobius_strip", "Möbius Strip Single Twist Ribbon", generate_mobius_strip()),
        ("terrain_heightmap", "Procedural Fractal Terrain Heightmap", generate_terrain(grid_size=32)),
    ]

    print("=" * 80)
    print(" NEXUS 3D SCENE STUDIO - PROCEDURAL SHAPES GALLERY GENERATOR")
    print("=" * 80)
    print(f"Output Directory: {output_dir.resolve()}")
    print("-" * 80)
    print(f"{'Shape Identifier':<20} | {'Vertices':<9} | {'Faces':<7} | {'Triangles':<9} | {'Surface Area':<12}")
    print("-" * 80)

    for file_id, label, mesh in generators:
        obj_path = output_dir / f"{file_id}.obj"
        stl_path = output_dir / f"{file_id}.stl"

        export_to_obj(mesh, obj_path)
        export_to_stl(mesh, stl_path)

        bbox = mesh.compute_bounding_box()
        area = mesh.compute_surface_area()

        item_info = {
            "id": file_id,
            "label": label,
            "mesh_name": mesh.name,
            "obj_file": obj_path.name,
            "stl_file": stl_path.name,
            "vertices": mesh.vertex_count,
            "faces": mesh.face_count,
            "triangles": mesh.triangle_count,
            "bounding_box": {
                "min": list(bbox[0]),
                "max": list(bbox[1]),
                "dimensions": [
                    round(bbox[1][0] - bbox[0][0], 4),
                    round(bbox[1][1] - bbox[0][1], 4),
                    round(bbox[1][2] - bbox[0][2], 4),
                ]
            },
            "surface_area": round(area, 4),
            "obj_size_bytes": obj_path.stat().st_size,
            "stl_size_bytes": stl_path.stat().st_size,
        }
        manifest.append(item_info)

        print(f"{file_id:<20} | {mesh.vertex_count:<9} | {mesh.face_count:<7} | {mesh.triangle_count:<9} | {area:<12.3f}")

    print("-" * 80)
    print(f"Successfully generated {len(manifest)} gallery shapes (14 3D model files).")
    print("=" * 80)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Generate Nexus 3D Procedural Shapes Gallery")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path(__file__).parent),
        help="Directory to save generated OBJ and STL models",
    )
    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    generate_all_gallery_shapes(out_dir)


if __name__ == "__main__":
    main()
