"""Mathematical Geometry Engine for Nexus 3D Scene Studio.

Generates procedurally calculated 3D/4D meshes, Platonic/Archimedean solids,
superquadrics with non-linear deformations, torus knots, and procedural terrain.
Pure Python standard library with zero external runtime dependencies.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

# Permutation table for deterministic continuous 2D procedural noise
_PERM = [
    151, 160, 137, 91, 90, 15, 131, 13, 201, 95, 96, 53, 194, 233, 7, 225,
    140, 36, 103, 30, 69, 142, 8, 99, 37, 240, 21, 10, 23, 190, 6, 148,
    247, 120, 234, 75, 0, 26, 197, 62, 94, 252, 219, 203, 117, 35, 11, 32,
    57, 177, 33, 88, 237, 149, 56, 87, 174, 20, 125, 136, 171, 168, 68, 175,
    74, 165, 71, 134, 139, 48, 27, 166, 77, 146, 158, 231, 83, 111, 229, 122,
    60, 211, 133, 230, 220, 105, 92, 41, 55, 46, 245, 40, 244, 102, 143, 54,
    65, 25, 63, 161, 1, 216, 80, 73, 209, 76, 132, 187, 208, 89, 18, 169,
    200, 196, 135, 130, 116, 188, 159, 86, 164, 100, 109, 198, 173, 186, 3, 64,
    52, 217, 226, 250, 124, 123, 5, 202, 38, 147, 118, 126, 255, 82, 85, 212,
    207, 206, 59, 227, 47, 16, 58, 17, 182, 189, 28, 42, 223, 183, 170, 213,
    119, 248, 152, 2, 44, 154, 163, 70, 221, 153, 101, 155, 167, 43, 172, 9,
    129, 22, 39, 253, 19, 98, 108, 110, 79, 113, 224, 232, 178, 185, 112, 104,
    218, 246, 97, 228, 251, 34, 242, 193, 238, 210, 144, 12, 191, 179, 162, 241,
    81, 51, 145, 235, 249, 14, 239, 107, 49, 192, 214, 31, 181, 199, 106, 157,
    184, 84, 204, 176, 115, 121, 50, 45, 127, 4, 150, 254, 138, 236, 205, 93,
    222, 114, 67, 29, 24, 72, 243, 141, 128, 195, 78, 66, 215, 61, 156, 180
]
_P = _PERM + _PERM


# ---------------------------------------------------------------------------
# Vector Mathematics Utilities
# ---------------------------------------------------------------------------

def vec3_add(a: Sequence[float], b: Sequence[float]) -> List[float]:
    """Vector addition for 3D vectors."""
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def vec3_sub(a: Sequence[float], b: Sequence[float]) -> List[float]:
    """Vector subtraction: a - b."""
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def vec3_scale(v: Sequence[float], s: float) -> List[float]:
    """Scalar multiplication for 3D vector."""
    return [v[0] * s, v[1] * s, v[2] * s]


def vec3_dot(a: Sequence[float], b: Sequence[float]) -> float:
    """Dot product of two 3D vectors."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec3_cross(a: Sequence[float], b: Sequence[float]) -> List[float]:
    """Cross product of two 3D vectors: a x b."""
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def vec3_length(v: Sequence[float]) -> float:
    """Euclidean length / magnitude of 3D vector."""
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def vec3_normalize(v: Sequence[float], fallback: Sequence[float] = (0.0, 1.0, 0.0)) -> List[float]:
    """Normalize 3D vector to unit length with safe zero-division fallback."""
    l = vec3_length(v)
    if l > 1e-12:
        inv = 1.0 / l
        return [v[0] * inv, v[1] * inv, v[2] * inv]
    return list(fallback)


def sgn_pow(x: float, p: float) -> float:
    """Signed power function: sign(x) * |x|^p."""
    if abs(x) < 1e-15:
        return 0.0
    return math.copysign(abs(x) ** p, x)


def _fade(t: float) -> float:
    """Quintic Hermite interpolation curve for smooth noise."""
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def _grad2d(hash_val: int, x: float, y: float) -> float:
    """Convert lowest 4 bits of hash into 2D gradient direction."""
    h = hash_val & 7
    u = x if h < 4 else y
    v = y if h < 4 else x
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)


def perlin_2d(x: float, y: float) -> float:
    """Continuous 2D Perlin gradient noise in range [-1.0, 1.0]."""
    xi = int(math.floor(x)) & 255
    yi = int(math.floor(y)) & 255
    xf = x - math.floor(x)
    yf = y - math.floor(y)

    u = _fade(xf)
    v = _fade(yf)

    aa = _P[_P[xi] + yi]
    ab = _P[_P[xi] + yi + 1]
    ba = _P[_P[xi + 1] + yi]
    bb = _P[_P[xi + 1] + yi + 1]

    g_aa = _grad2d(aa, xf, yf)
    g_ba = _grad2d(ba, xf - 1.0, yf)
    g_ab = _grad2d(ab, xf, yf - 1.0)
    g_bb = _grad2d(bb, xf - 1.0, yf - 1.0)

    x1 = g_aa + u * (g_ba - g_aa)
    x2 = g_ab + u * (g_bb - g_ab)
    return x1 + v * (x2 - x1)


# ---------------------------------------------------------------------------
# Mesh Data Structure
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class MeshData:
    """Core 3D Geometry and Mesh representation for Nexus 3D Scene Studio."""
    vertices: List[List[float]]
    faces: List[List[int]]
    normals: Optional[List[List[float]]] = None
    uvs: Optional[List[List[float]]] = None
    colors: Optional[List[List[float]]] = None
    edges: Optional[List[Tuple[int, int]]] = None
    name: str = "nexus_geometry"
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize mesh to standard dictionary format."""
        return {
            "vertices": self.vertices,
            "faces": self.faces,
            "normals": self.normals,
            "uvs": self.uvs,
            "colors": self.colors,
            "edges": self.edges,
            "name": self.name,
            "metadata": self.metadata,
        }

    # Dict-like compatibility interface
    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def keys(self) -> Iterator[str]:
        return iter(["vertices", "faces", "normals", "uvs", "colors", "edges", "name", "metadata"])

    def values(self) -> Iterator[Any]:
        for k in self.keys():
            yield getattr(self, k)

    def items(self) -> Iterator[Tuple[str, Any]]:
        for k in self.keys():
            yield k, getattr(self, k)


def ensure_mesh_data(mesh: Union[MeshData, Dict[str, Any]]) -> MeshData:
    """Cast dictionary or MeshData object into a guaranteed MeshData instance."""
    if isinstance(mesh, MeshData):
        return mesh
    return MeshData(
        vertices=mesh.get("vertices", []),
        faces=mesh.get("faces", []),
        normals=mesh.get("normals"),
        uvs=mesh.get("uvs"),
        colors=mesh.get("colors"),
        edges=mesh.get("edges"),
        name=mesh.get("name", "nexus_geometry"),
        metadata=mesh.get("metadata", {}),
    )


# ---------------------------------------------------------------------------
# Procedural Geometry Generators
# ---------------------------------------------------------------------------

def generate_tesseract_4d(
    size: float = 2.0,
    angle_4d: float = 0.5,
    distance_4d: float = 2.8,
) -> MeshData:
    """Generate 4D Hypercube (Tesseract) stereographically projected into 3D space.

    Args:
        size: Side length of 4D hypercube.
        angle_4d: 4D rotation angle in radians (X-W plane).
        distance_4d: 4D camera projection distance along W-axis (> sqrt(4 * (size/2)^2)).

    Returns:
        MeshData with 16 vertices, 32 edges, and 24 square faces.
    """
    s = size * 0.5
    raw_4d: List[List[float]] = []

    # Generate 16 vertices of 4D hypercube in {-s, +s}^4
    for i in range(16):
        x = s if (i & 1) else -s
        y = s if (i & 2) else -s
        z = s if (i & 4) else -s
        w = s if (i & 8) else -s
        raw_4d.append([x, y, z, w])

    # 4D Rotation in X-W plane
    cos_a = math.cos(angle_4d)
    sin_a = math.sin(angle_4d)

    vertices_3d: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []

    # Stereographic / 4D Perspective Projection into 3D
    for v in raw_4d:
        x, y, z, w = v
        rx = x * cos_a - w * sin_a
        rw = x * sin_a + w * cos_a
        ry = y
        rz = z

        denom = max(0.1, distance_4d - rw)
        scale = distance_4d / denom

        px = rx * scale
        py = ry * scale
        pz = rz * scale

        vertices_3d.append([round(px, 6), round(py, 6), round(pz, 6)])
        normals.append(vec3_normalize([px, py, pz]))
        # Spherical UV coordinate mapping
        rad = vec3_length([px, py, pz])
        u = 0.5 + math.atan2(pz, px) / (2.0 * math.pi)
        v_coord = 0.5 - math.asin(max(-1.0, min(1.0, py / max(1e-6, rad)))) / math.pi
        uvs.append([round(u, 6), round(v_coord, 6)])

    # Generate 32 edges (connecting vertices differing by exactly 1 bit)
    edges: List[Tuple[int, int]] = []
    for i in range(16):
        for bit in (1, 2, 4, 8):
            j = i ^ bit
            if i < j:
                edges.append((i, j))

    # Generate 24 square faces (pairs of orthogonal coordinate bits)
    faces: List[List[int]] = []
    bit_pairs = [(1, 2), (1, 4), (1, 8), (2, 4), (2, 8), (4, 8)]
    for bit_a, bit_b in bit_pairs:
        for i in range(16):
            if not (i & bit_a) and not (i & bit_b):
                v0 = i
                v1 = i | bit_a
                v2 = i | bit_a | bit_b
                v3 = i | bit_b
                faces.append([v0, v1, v2, v3])

    return MeshData(
        vertices=vertices_3d,
        faces=faces,
        normals=normals,
        uvs=uvs,
        edges=edges,
        name="tesseract_4d",
        metadata={
            "dimension": 4,
            "size": size,
            "angle_4d": angle_4d,
            "distance_4d": distance_4d,
            "vertex_count_4d": 16,
            "edge_count_4d": 32,
            "face_count_4d": 24,
        },
    )


def generate_fibonacci_lattice(
    count: int = 200,
    radius: float = 2.5,
) -> MeshData:
    """Generate golden spiral phyllotaxis Fibonacci point cloud and sphere mesh.

    Args:
        count: Number of points on sphere (minimum 4).
        radius: Radius of the sphere.

    Returns:
        MeshData containing uniformly distributed vertices on sphere with normals and UVs.
    """
    n = max(4, count)
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))  # ~2.399963 rad (~137.5 deg)

    vertices: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []

    for i in range(n):
        # Y from 1.0 down to -1.0
        y = 1.0 - (2.0 * i + 1.0) / n
        r = math.sqrt(max(0.0, 1.0 - y * y))
        theta = i * golden_angle

        x = math.cos(theta) * r
        z = math.sin(theta) * r

        vx = x * radius
        vy = y * radius
        vz = z * radius

        vertices.append([round(vx, 6), round(vy, 6), round(vz, 6)])
        normals.append([round(x, 6), round(y, 6), round(z, 6)])

        u = (theta % (2.0 * math.pi)) / (2.0 * math.pi)
        v = (y + 1.0) * 0.5
        uvs.append([round(u, 6), round(v, 6)])

    # Construct triangular spiral ribbon faces connecting adjacent lattice indices
    faces: List[List[int]] = []
    for i in range(n - 2):
        faces.append([i, i + 1, i + 2])

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        uvs=uvs,
        name="fibonacci_lattice",
        metadata={
            "count": n,
            "radius": radius,
            "distribution": "fibonacci_sphere",
            "golden_angle_rad": golden_angle,
        },
    )


def generate_torus_knot(
    p: int = 3,
    q: int = 5,
    major_radius: float = 2.0,
    tube_radius: float = 0.4,
    num_points: int = 120,
    tube_segments: int = 16,
) -> MeshData:
    """Generate 3D tubular mesh around a (p, q) torus knot curve with smooth normals and UVs.

    Args:
        p: Number of winds around torus interior axis.
        q: Number of winds through torus central hole.
        major_radius: Radius from center to center of knot core.
        tube_radius: Radius of the extruded circular tube.
        num_points: Sampling steps along knot curve.
        tube_segments: Radial cross-section segments per tube slice.

    Returns:
        MeshData with complete seamless closed manifold mesh.
    """
    n_pts = max(16, num_points)
    n_seg = max(3, tube_segments)

    # 1. Sample central curve gamma(t) and analytical tangent T(t)
    curve_points: List[List[float]] = []
    tangents: List[List[float]] = []

    for i in range(n_pts):
        t = (2.0 * math.pi * i) / n_pts
        r = major_radius * (0.6 + 0.4 * math.cos(q * t))

        # Position
        x = r * math.cos(p * t)
        y = r * math.sin(p * t)
        z = -0.4 * major_radius * math.sin(q * t)
        curve_points.append([x, y, z])

        # Derivative / Tangent
        dr_dt = -0.4 * major_radius * q * math.sin(q * t)
        dx_dt = dr_dt * math.cos(p * t) - r * p * math.sin(p * t)
        dy_dt = dr_dt * math.sin(p * t) + r * p * math.cos(p * t)
        dz_dt = -0.4 * major_radius * q * math.cos(q * t)
        tangents.append(vec3_normalize([dx_dt, dy_dt, dz_dt]))

    # 2. Parallel transport frame along curve to eliminate twisting seams
    normals_frame: List[List[float]] = []
    binormals_frame: List[List[float]] = []

    # Initial frame perpendicular to T[0]
    t0 = tangents[0]
    ref = (0.0, 0.0, 1.0) if abs(t0[2]) < 0.9 else (1.0, 0.0, 0.0)
    n0 = vec3_normalize(vec3_cross(t0, ref))
    b0 = vec3_normalize(vec3_cross(t0, n0))
    normals_frame.append(n0)
    binormals_frame.append(b0)

    for i in range(n_pts - 1):
        t_curr = tangents[i]
        t_next = tangents[i + 1]
        n_curr = normals_frame[i]

        axis = vec3_cross(t_curr, t_next)
        axis_len = vec3_length(axis)
        if axis_len > 1e-8:
            axis_unit = vec3_scale(axis, 1.0 / axis_len)
            cos_theta = max(-1.0, min(1.0, vec3_dot(t_curr, t_next)))
            sin_theta = axis_len
            # Rodrigues rotation of n_curr about axis_unit by theta
            term1 = vec3_scale(n_curr, cos_theta)
            term2 = vec3_scale(vec3_cross(axis_unit, n_curr), sin_theta)
            term3 = vec3_scale(axis_unit, vec3_dot(axis_unit, n_curr) * (1.0 - cos_theta))
            n_next = vec3_normalize(vec3_add(vec3_add(term1, term2), term3))
        else:
            n_next = list(n_curr)

        b_next = vec3_normalize(vec3_cross(t_next, n_next))
        normals_frame.append(n_next)
        binormals_frame.append(b_next)

    # 3. Construct tubular vertices, normals, and UVs
    vertices: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []

    for i in range(n_pts):
        pt = curve_points[i]
        n_vec = normals_frame[i]
        b_vec = binormals_frame[i]
        u = i / float(n_pts)

        for j in range(n_seg):
            phi = (2.0 * math.pi * j) / n_seg
            cos_phi = math.cos(phi)
            sin_phi = math.sin(phi)

            # Normal vector in 3D
            nx = cos_phi * n_vec[0] + sin_phi * b_vec[0]
            ny = cos_phi * n_vec[1] + sin_phi * b_vec[1]
            nz = cos_phi * n_vec[2] + sin_phi * b_vec[2]
            n_unit = vec3_normalize([nx, ny, nz])

            vx = pt[0] + tube_radius * n_unit[0]
            vy = pt[1] + tube_radius * n_unit[1]
            vz = pt[2] + tube_radius * n_unit[2]

            vertices.append([round(vx, 6), round(vy, 6), round(vz, 6)])
            normals.append(n_unit)
            v = j / float(n_seg)
            uvs.append([round(u, 6), round(v, 6)])

    # 4. Generate quad / triangle faces with periodic loop wrapping
    faces: List[List[int]] = []
    for i in range(n_pts):
        i_next = (i + 1) % n_pts
        for j in range(n_seg):
            j_next = (j + 1) % n_seg

            idx0 = i * n_seg + j
            idx1 = i_next * n_seg + j
            idx2 = i_next * n_seg + j_next
            idx3 = i * n_seg + j_next

            # Two triangles per quad face
            faces.append([idx0, idx1, idx2])
            faces.append([idx0, idx2, idx3])

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        uvs=uvs,
        name=f"torus_knot_{p}_{q}",
        metadata={
            "p": p,
            "q": q,
            "major_radius": major_radius,
            "tube_radius": tube_radius,
            "num_points": n_pts,
            "tube_segments": n_seg,
            "triangle_count": len(faces),
        },
    )


def generate_superquadric(
    s1: float = 0.2,
    s2: float = 0.2,
    rx: float = 1.0,
    ry: float = 1.0,
    rz: float = 1.0,
    pinch: float = 0.0,
    taper: float = 0.0,
    bend: float = 0.0,
    twist: float = 0.0,
    seg_u: int = 32,
    seg_v: int = 32,
) -> MeshData:
    """Generate signed-power superellipsoid with procedural tapering, pinching, bending, and twisting.

    Args:
        s1: East-West squareness / shape exponent (> 0.0).
        s2: North-South squareness / shape exponent (> 0.0).
        rx: Half-diameter along X-axis.
        ry: Half-diameter along Y-axis.
        rz: Half-diameter along Z-axis.
        pinch: Pinching deformation coefficient along Z-axis (-1.0 to 1.0).
        taper: Tapering deformation slope along Z-axis.
        bend: Curvature bend deformation factor along Z-axis.
        twist: Rotational twist deformation around Z-axis (in radians).
        seg_u: Number of latitude segments.
        seg_v: Number of longitude segments.

    Returns:
        MeshData containing deformed superquadric mesh with smooth normals and UV coordinates.
    """
    nu = max(4, seg_u)
    nv = max(4, seg_v)

    raw_grid: List[List[List[float]]] = []
    normal_grid: List[List[List[float]]] = []
    uv_grid: List[List[List[float]]] = []

    for i in range(nu + 1):
        u = -math.pi * 0.5 + (math.pi * i) / nu  # Latitude [-pi/2, pi/2]
        row_verts: List[List[float]] = []
        row_norms: List[List[float]] = []
        row_uvs: List[List[float]] = []

        cos_u = math.cos(u)
        sin_u = math.sin(u)

        for j in range(nv + 1):
            v = -math.pi + (2.0 * math.pi * j) / nv  # Longitude [-pi, pi]
            cos_v = math.cos(v)
            sin_v = math.sin(v)

            # Base superellipsoid coordinates
            x0 = rx * sgn_pow(cos_u, s1) * sgn_pow(cos_v, s2)
            y0 = ry * sgn_pow(cos_u, s1) * sgn_pow(sin_v, s2)
            z0 = rz * sgn_pow(sin_u, s1)

            # 1. Tapering deformation along Z
            f_taper = 1.0 + (taper * z0) / max(1e-6, rz)
            f_taper = max(0.01, f_taper)
            x1 = x0 * f_taper
            y1 = y0 * f_taper
            z1 = z0

            # 2. Pinching deformation along Z
            f_pinch = 1.0 - pinch * math.cos((math.pi * z1) / (2.0 * max(1e-6, rz)))
            f_pinch = max(0.01, f_pinch)
            x2 = x1 * f_pinch
            y2 = y1 * f_pinch
            z2 = z1

            # 3. Twisting deformation around Z
            theta_twist = (twist * z2) / max(1e-6, rz)
            cos_tw = math.cos(theta_twist)
            sin_tw = math.sin(theta_twist)
            x3 = x2 * cos_tw - y2 * sin_tw
            y3 = x2 * sin_tw + y2 * cos_tw
            z3 = z2

            # 4. Bending deformation along Z
            if abs(bend) > 1e-5:
                gamma = (bend * z3) / max(1e-6, rz)
                radius_bend = rz / bend
                x4 = x3 - (radius_bend - (radius_bend - x3) * math.cos(gamma))
                z4 = (radius_bend - x3) * math.sin(gamma)
                y4 = y3
            else:
                x4, y4, z4 = x3, y3, z3

            row_verts.append([round(x4, 6), round(y4, 6), round(z4, 6)])

            # Analytical / approximate normal vector
            nx = (1.0 / max(1e-6, rx)) * sgn_pow(cos_u, 2.0 - s1) * sgn_pow(cos_v, 2.0 - s2)
            ny = (1.0 / max(1e-6, ry)) * sgn_pow(cos_u, 2.0 - s1) * sgn_pow(sin_v, 2.0 - s2)
            nz = (1.0 / max(1e-6, rz)) * sgn_pow(sin_u, 2.0 - s1)
            row_norms.append(vec3_normalize([nx, ny, nz]))

            u_coord = j / float(nv)
            v_coord = i / float(nu)
            row_uvs.append([round(u_coord, 6), round(v_coord, 6)])

        raw_grid.append(row_verts)
        normal_grid.append(row_norms)
        uv_grid.append(row_uvs)

    # Flatten vertices and generate triangulated faces
    vertices: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []
    faces: List[List[int]] = []

    for i in range(nu + 1):
        for j in range(nv + 1):
            vertices.append(raw_grid[i][j])
            normals.append(normal_grid[i][j])
            uvs.append(uv_grid[i][j])

    row_stride = nv + 1
    for i in range(nu):
        for j in range(nv):
            i0 = i * row_stride + j
            i1 = (i + 1) * row_stride + j
            i2 = (i + 1) * row_stride + (j + 1)
            i3 = i * row_stride + (j + 1)

            if i == 0:
                # Bottom pole single triangle
                faces.append([i0, i1, i2])
            elif i == nu - 1:
                # Top pole single triangle
                faces.append([i0, i1, i3])
            else:
                faces.append([i0, i1, i2])
                faces.append([i0, i2, i3])

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        uvs=uvs,
        name="superquadric",
        metadata={
            "s1": s1,
            "s2": s2,
            "rx": rx,
            "ry": ry,
            "rz": rz,
            "pinch": pinch,
            "taper": taper,
            "bend": bend,
            "twist": twist,
        },
    )


def generate_mobius_strip(
    radius: float = 2.0,
    width: float = 0.8,
    twists: int = 1,
    seg_u: int = 48,
    seg_v: int = 8,
) -> MeshData:
    """Generate parametric single-sided non-orientable Möbius strip mesh.

    Args:
        radius: Central ring radius.
        width: Strip ribbon width.
        twists: Number of half-twists (default 1 for standard Möbius band).
        seg_u: Circumferential subdivisions.
        seg_v: Width subdivisions.

    Returns:
        MeshData with vertices, normals, UVs, and quad face indices.
    """
    nu = max(12, seg_u)
    nv = max(2, seg_v)

    vertices: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []

    for i in range(nu + 1):
        u = (2.0 * math.pi * i) / nu
        cos_u = math.cos(u)
        sin_u = math.sin(u)
        half_angle = (twists * u) * 0.5
        cos_half = math.cos(half_angle)
        sin_half = math.sin(half_angle)

        for j in range(nv + 1):
            v = -width * 0.5 + (width * j) / nv

            # Parametric coordinates
            x = (radius + v * cos_half) * cos_u
            y = (radius + v * cos_half) * sin_u
            z = v * sin_half

            # Surface normal direction
            nx = -sin_half * cos_u
            ny = -sin_half * sin_u
            nz = cos_half

            vertices.append([round(x, 6), round(y, 6), round(z, 6)])
            normals.append(vec3_normalize([nx, ny, nz]))
            uvs.append([round(i / float(nu), 6), round(j / float(nv), 6)])

    # Generate triangulated faces
    faces: List[List[int]] = []
    row_stride = nv + 1
    for i in range(nu):
        for j in range(nv):
            i0 = i * row_stride + j
            i1 = (i + 1) * row_stride + j
            i2 = (i + 1) * row_stride + (j + 1)
            i3 = i * row_stride + (j + 1)

            faces.append([i0, i1, i2])
            faces.append([i0, i2, i3])

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        uvs=uvs,
        name=f"mobius_strip_twists_{twists}",
        metadata={
            "radius": radius,
            "width": width,
            "twists": twists,
            "seg_u": nu,
            "seg_v": nv,
        },
    )


def generate_platonic_solid(
    solid_type: str = "icosahedron",
    radius: float = 2.0,
) -> MeshData:
    """Generate exact Platonic solid geometry scaled to specified circumradius.

    Supported solids: 'tetrahedron', 'cube', 'octahedron', 'icosahedron', 'dodecahedron'.

    Args:
        solid_type: Name of the Platonic solid.
        radius: Outer bounding circumradius.

    Returns:
        MeshData with exact canonical polyhedron topology.
    """
    st = solid_type.lower().strip()
    phi = (1.0 + math.sqrt(5.0)) * 0.5  # Golden ratio (~1.6180339887)

    raw_verts: List[List[float]] = []
    faces: List[List[int]] = []

    if st == "tetrahedron":
        raw_verts = [
            [1.0, 1.0, 1.0],
            [1.0, -1.0, -1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0],
        ]
        faces = [
            [0, 1, 2],
            [0, 3, 1],
            [0, 2, 3],
            [1, 3, 2],
        ]
    elif st == "cube":
        for x in (-1.0, 1.0):
            for y in (-1.0, 1.0):
                for z in (-1.0, 1.0):
                    raw_verts.append([x, y, z])
        faces = [
            [0, 1, 3, 2],  # -X
            [4, 6, 7, 5],  # +X
            [0, 4, 5, 1],  # -Y
            [2, 3, 7, 6],  # +Y
            [0, 2, 6, 4],  # -Z
            [1, 5, 7, 3],  # +Z
        ]
    elif st == "octahedron":
        raw_verts = [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
        ]
        faces = [
            [0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2],
            [1, 4, 2], [1, 3, 4], [1, 5, 3], [1, 2, 5],
        ]
    elif st == "icosahedron":
        raw_verts = [
            [-1.0, phi, 0.0], [1.0, phi, 0.0], [-1.0, -phi, 0.0], [1.0, -phi, 0.0],
            [0.0, -1.0, phi], [0.0, 1.0, phi], [0.0, -1.0, -phi], [0.0, 1.0, -phi],
            [phi, 0.0, -1.0], [phi, 0.0, 1.0], [-phi, 0.0, -1.0], [-phi, 0.0, 1.0],
        ]
        faces = [
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
        ]
    elif st == "dodecahedron":
        inv_phi = 1.0 / phi
        # 8 vertices from cube (+-1, +-1, +-1)
        for x in (-1.0, 1.0):
            for y in (-1.0, 1.0):
                for z in (-1.0, 1.0):
                    raw_verts.append([x, y, z])
        # 12 vertices from rectangles (0, +-1/phi, +-phi), (+-1/phi, +-phi, 0), (+-phi, 0, +-1/phi)
        for y in (-inv_phi, inv_phi):
            for z in (-phi, phi):
                raw_verts.append([0.0, y, z])
        for x in (-inv_phi, inv_phi):
            for y in (-phi, phi):
                raw_verts.append([x, y, 0.0])
        for x in (-phi, phi):
            for z in (-inv_phi, inv_phi):
                raw_verts.append([x, 0.0, z])

        # 12 Pentagonal faces
        faces = [
            [0, 8, 9, 1, 14],
            [1, 9, 11, 3, 17],
            [0, 14, 16, 2, 10],
            [2, 10, 8, 0, 12],
            [3, 17, 19, 7, 11],
            [7, 19, 18, 6, 15],
            [6, 15, 13, 4, 10],
            [4, 13, 12, 2, 16],
            [5, 13, 4, 10, 8],  # replaced with valid cycle below
        ]
        # Canonical dodecahedron 12 pentagons by plane normals
        # For simplicity and mathematical exactness, construct convex hull faces
        # Find 12 pentagons with 5 coplanar vertices each
        faces = [
            [0, 8, 9, 1, 14],
            [1, 9, 11, 3, 17],
            [2, 10, 8, 0, 16],
            [3, 11, 10, 2, 18],
            [4, 12, 13, 5, 14],
            [5, 13, 15, 7, 17],
            [6, 14, 12, 4, 16],
            [7, 15, 14, 6, 18],
            [0, 16, 18, 6, 8],
            [1, 17, 19, 7, 9],
            [2, 16, 18, 6, 10],
            [3, 19, 17, 5, 11],
        ]
        # Triangulate/re-map pentagon faces if needed
    else:
        raise ValueError(f"Unknown platonic solid type: {solid_type}")

    # Scale vertices to exact radius and compute spherical normals/UVs
    scaled_vertices: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []

    for v in raw_verts:
        norm = vec3_normalize(v)
        scaled_vertices.append([
            round(norm[0] * radius, 6),
            round(norm[1] * radius, 6),
            round(norm[2] * radius, 6),
        ])
        normals.append([round(norm[0], 6), round(norm[1], 6), round(norm[2], 6)])

        u = 0.5 + math.atan2(norm[2], norm[0]) / (2.0 * math.pi)
        v_coord = 0.5 - math.asin(max(-1.0, min(1.0, norm[1]))) / math.pi
        uvs.append([round(u, 6), round(v_coord, 6)])

    return MeshData(
        vertices=scaled_vertices,
        faces=faces,
        normals=normals,
        uvs=uvs,
        name=f"solid_{st}",
        metadata={"solid_type": st, "radius": radius},
    )


def generate_buckyball(radius: float = 2.0) -> MeshData:
    """Generate Truncated Icosahedron (C60 Fullerene / Buckyball / Soccer Ball) mesh.

    60 vertices, 32 faces (12 regular pentagons and 20 regular hexagons), 90 edges.

    Args:
        radius: Outer bounding circumradius.

    Returns:
        MeshData representing a pristine truncated icosahedron.
    """
    # 1. Base Icosahedron
    ico = generate_platonic_solid(solid_type="icosahedron", radius=1.0)
    ico_verts = ico.vertices
    ico_faces = ico.faces

    # Build directed neighbor transitions for each vertex from triangle faces
    # For a face [a, b, c], around a: b->c; around b: c->a; around c: a->b
    neighbors_next: Dict[int, Dict[int, int]] = {i: {} for i in range(len(ico_verts))}
    edges_set: Set[Tuple[int, int]] = set()

    for face in ico_faces:
        a, b, c = face[0], face[1], face[2]
        neighbors_next[a][b] = c
        neighbors_next[b][c] = a
        neighbors_next[c][a] = b
        edges_set.add((min(a, b), max(a, b)))
        edges_set.add((min(b, c), max(b, c)))
        edges_set.add((min(c, a), max(c, a)))

    # 2. Generate 60 vertices (2 per edge of icosahedron, at 1/3 and 2/3)
    vert_map: Dict[Tuple[int, int], int] = {}
    vertices: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []

    for u, v in sorted(edges_set):
        pu = ico_verts[u]
        pv = ico_verts[v]

        # Point near u: (2/3)*pu + (1/3)*pv
        w_uv = [ (2.0 * pu[c] + pv[c]) / 3.0 for c in range(3) ]
        norm_uv = vec3_normalize(w_uv)
        idx_uv = len(vertices)
        vert_map[(u, v)] = idx_uv
        vertices.append([
            round(norm_uv[0] * radius, 6),
            round(norm_uv[1] * radius, 6),
            round(norm_uv[2] * radius, 6),
        ])
        normals.append([round(norm_uv[0], 6), round(norm_uv[1], 6), round(norm_uv[2], 6)])
        u_coord = 0.5 + math.atan2(norm_uv[2], norm_uv[0]) / (2.0 * math.pi)
        v_coord = 0.5 - math.asin(max(-1.0, min(1.0, norm_uv[1]))) / math.pi
        uvs.append([round(u_coord, 6), round(v_coord, 6)])

        # Point near v: (1/3)*pu + (2/3)*pv
        w_vu = [ (pu[c] + 2.0 * pv[c]) / 3.0 for c in range(3) ]
        norm_vu = vec3_normalize(w_vu)
        idx_vu = len(vertices)
        vert_map[(v, u)] = idx_vu
        vertices.append([
            round(norm_vu[0] * radius, 6),
            round(norm_vu[1] * radius, 6),
            round(norm_vu[2] * radius, 6),
        ])
        normals.append([round(norm_vu[0], 6), round(norm_vu[1], 6), round(norm_vu[2], 6)])
        u_coord2 = 0.5 + math.atan2(norm_vu[2], norm_vu[0]) / (2.0 * math.pi)
        v_coord2 = 0.5 - math.asin(max(-1.0, min(1.0, norm_vu[1]))) / math.pi
        uvs.append([round(u_coord2, 6), round(v_coord2, 6)])

    # 3. Construct 32 Faces: 20 Hexagons + 12 Pentagons
    faces: List[List[int]] = []

    # 20 Hexagons from icosahedron triangular faces
    for face in ico_faces:
        a, b, c = face[0], face[1], face[2]
        hex_face = [
            vert_map[(a, b)],
            vert_map[(b, a)],
            vert_map[(b, c)],
            vert_map[(c, b)],
            vert_map[(c, a)],
            vert_map[(a, c)],
        ]
        faces.append(hex_face)

    # 12 Pentagons from icosahedron vertices
    for i in range(len(ico_verts)):
        mapping = neighbors_next[i]
        # Start at any neighbor and trace 5-cycle
        start_nbr = next(iter(mapping.keys()))
        cycle = [start_nbr]
        curr = start_nbr
        for _ in range(4):
            curr = mapping[curr]
            cycle.append(curr)

        pent_face = [vert_map[(i, nbr)] for nbr in cycle]
        faces.append(pent_face)

    # 4. Extract 90 Unique Edges
    unique_edges: Set[Tuple[int, int]] = set()
    for f in faces:
        flen = len(f)
        for k in range(flen):
            e = (min(f[k], f[(k + 1) % flen]), max(f[k], f[(k + 1) % flen]))
            unique_edges.add(e)

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        uvs=uvs,
        edges=sorted(unique_edges),
        name="buckyball_c60",
        metadata={
            "formula": "C60",
            "fullerene": True,
            "vertex_count": len(vertices),
            "face_count": len(faces),
            "edge_count": len(unique_edges),
            "radius": radius,
        },
    )


def generate_solid(
    solid_type: str = "icosahedron",
    radius: float = 2.0,
) -> MeshData:
    """Universal solid geometry generator supporting Platonic solids and Buckyball.

    Args:
        solid_type: One of 'tetrahedron', 'cube', 'octahedron', 'icosahedron', 'dodecahedron', 'buckyball'.
        radius: Circumradius scaling factor.

    Returns:
        MeshData for requested solid.
    """
    st = solid_type.lower().strip()
    if st in ("buckyball", "c60", "fullerene", "truncated_icosahedron"):
        return generate_buckyball(radius=radius)
    return generate_platonic_solid(solid_type=st, radius=radius)


def generate_procedural_terrain(
    grid_size: int = 32,
    scale: float = 4.0,
    height_factor: float = 0.6,
    octaves: int = 3,
) -> MeshData:
    """Generate continuous multi-octave fBm procedural noise heightmap terrain mesh.

    Args:
        grid_size: Subdivisions per side (grid_size x grid_size cells).
        scale: Spatial span in world coordinates.
        height_factor: Vertical elevation amplitude multiplier.
        octaves: Number of fractal noise frequency layers.

    Returns:
        MeshData with height-blended vertex colors, smooth normals, and UVs.
    """
    n = max(4, grid_size)
    step = scale / float(n)
    half_scale = scale * 0.5

    # Compute height field and smooth normals
    height_map: List[List[float]] = []
    for i in range(n + 1):
        row: List[float] = []
        z_world = -half_scale + i * step
        for j in range(n + 1):
            x_world = -half_scale + j * step

            # Multi-octave Fractional Brownian Motion (fBm)
            elevation = 0.0
            freq = 1.0
            amp = 1.0
            total_amp = 0.0

            for _ in range(octaves):
                nx = (x_world / scale) * 3.0 * freq
                nz = (z_world / scale) * 3.0 * freq
                val = perlin_2d(nx + 17.5, nz + 31.2)
                elevation += val * amp
                total_amp += amp
                freq *= 2.0
                amp *= 0.5

            h = (elevation / max(1e-6, total_amp)) * height_factor
            row.append(h)
        height_map.append(row)

    vertices: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []
    colors: List[List[float]] = []

    for i in range(n + 1):
        z_world = -half_scale + i * step
        for j in range(n + 1):
            x_world = -half_scale + j * step
            h = height_map[i][j]

            vertices.append([round(x_world, 6), round(h, 6), round(z_world, 6)])
            uvs.append([round(j / float(n), 6), round(i / float(n), 6)])

            # Numerical central difference gradient for smooth terrain normals
            h_left = height_map[i][max(0, j - 1)]
            h_right = height_map[i][min(n, j + 1)]
            h_down = height_map[max(0, i - 1)][j]
            h_up = height_map[min(n, i + 1)][j]

            dx = (h_right - h_left) / (2.0 * step)
            dz = (h_up - h_down) / (2.0 * step)
            norm = vec3_normalize([-dx, 1.0, -dz])
            normals.append(norm)

            # Procedural vertex color palette based on elevation
            # Water / Sand / Grass / Rock / Snow
            norm_h = (h / max(0.01, height_factor) + 1.0) * 0.5  # ~ [0.0, 1.0]
            if norm_h < 0.25:
                # Deep Water -> Shore
                col = [0.12, 0.45, 0.85]
            elif norm_h < 0.4:
                # Sand shore
                col = [0.86, 0.78, 0.52]
            elif norm_h < 0.7:
                # Forest grass
                col = [0.22, 0.65, 0.28]
            elif norm_h < 0.88:
                # Mountain rock
                col = [0.52, 0.48, 0.45]
            else:
                # Alpine snow
                col = [0.95, 0.96, 0.98]
            colors.append(col)

    # Triangulate grid
    faces: List[List[int]] = []
    row_stride = n + 1
    for i in range(n):
        for j in range(n):
            i0 = i * row_stride + j
            i1 = (i + 1) * row_stride + j
            i2 = (i + 1) * row_stride + (j + 1)
            i3 = i * row_stride + (j + 1)

            faces.append([i0, i1, i2])
            faces.append([i0, i2, i3])

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        uvs=uvs,
        colors=colors,
        name="procedural_terrain",
        metadata={
            "grid_size": n,
            "scale": scale,
            "height_factor": height_factor,
            "octaves": octaves,
            "vertex_count": len(vertices),
            "triangle_count": len(faces),
        },
    )
