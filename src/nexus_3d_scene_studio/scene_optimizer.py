"""Scene Optimizer and Geometry Budget Auditor for Nexus 3D Scene Studio.

Provides polygon budget auditing, WebGL VRAM estimations, performance grading (A+ to D),
automatic smooth/flat normal recomputation, vertex welding, and mesh triangulation.
Pure Python standard library with zero external runtime dependencies.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple, Union

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


class SceneOptimizer:
    """Scene and Mesh optimization toolkit for 3D assets and WebGL runtimes."""

    @staticmethod
    def audit_mesh_budget(
        mesh_data: Union[MeshData, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Perform comprehensive polygon budget, geometry analysis, and VRAM audit.

        Args:
            mesh_data: Input MeshData or dictionary representation.

        Returns:
            Dictionary containing metrics: vertex_count, face_count, triangle_count,
            edge_count, bounding_box [min_x, max_x, min_y, max_y, min_z, max_z],
            dimensions [dx, dy, dz], center_of_mass [cx, cy, cz], surface_area,
            volume, vram_bytes, performance_grade ('A+', 'A', 'B', 'C', 'D'),
            and diagnostics list.
        """
        mesh = ensure_mesh_data(mesh_data)
        vertices = mesh.vertices
        faces = mesh.faces

        vertex_count = len(vertices)
        face_count = len(faces)

        if vertex_count == 0:
            return {
                "vertex_count": 0,
                "face_count": 0,
                "triangle_count": 0,
                "edge_count": 0,
                "bounding_box": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "dimensions": [0.0, 0.0, 0.0],
                "center_of_mass": [0.0, 0.0, 0.0],
                "surface_area": 0.0,
                "volume": 0.0,
                "vram_bytes": 0,
                "performance_grade": "A+",
                "diagnostics": ["Empty mesh: zero vertices."],
            }

        # 1. Bounding Box & Center of Mass
        min_x = min(v[0] for v in vertices)
        max_x = max(v[0] for v in vertices)
        min_y = min(v[1] for v in vertices)
        max_y = max(v[1] for v in vertices)
        min_z = min(v[2] for v in vertices)
        max_z = max(v[2] for v in vertices)

        bounding_box = [
            round(min_x, 6),
            round(max_x, 6),
            round(min_y, 6),
            round(max_y, 6),
            round(min_z, 6),
            round(max_z, 6),
        ]
        dimensions = [
            round(max_x - min_x, 6),
            round(max_y - min_y, 6),
            round(max_z - min_z, 6),
        ]

        sum_x = sum(v[0] for v in vertices)
        sum_y = sum(v[1] for v in vertices)
        sum_z = sum(v[2] for v in vertices)
        center_of_mass = [
            round(sum_x / vertex_count, 6),
            round(sum_y / vertex_count, 6),
            round(sum_z / vertex_count, 6),
        ]

        # 2. Triangles, Edges, Surface Area, and Volume
        triangle_count = 0
        surface_area = 0.0
        signed_volume = 0.0
        unique_edges: Set[Tuple[int, int]] = set()
        zero_area_faces = 0

        for face in faces:
            flen = len(face)
            if flen < 3:
                continue

            # Accumulate edges
            for i in range(flen):
                i0 = face[i]
                i1 = face[(i + 1) % flen]
                edge = (min(i0, i1), max(i0, i1))
                unique_edges.add(edge)

            # Triangulate face (fan)
            for k in range(1, flen - 1):
                triangle_count += 1
                i0 = face[0]
                i1 = face[k]
                i2 = face[k + 1]

                if i0 < vertex_count and i1 < vertex_count and i2 < vertex_count:
                    v0 = vertices[i0]
                    v1 = vertices[i1]
                    v2 = vertices[i2]

                    # Triangle Area: 0.5 * ||(v1 - v0) x (v2 - v0)||
                    e1 = vec3_sub(v1, v0)
                    e2 = vec3_sub(v2, v0)
                    cross = vec3_cross(e1, e2)
                    c_len = vec3_length(cross)
                    tri_area = 0.5 * c_len
                    surface_area += tri_area

                    if tri_area < 1e-9:
                        zero_area_faces += 1

                    # Signed Tetrahedron Volume: (v0 . (v1 x v2)) / 6.0
                    signed_volume += vec3_dot(v0, vec3_cross(v1, v2)) / 6.0

        if mesh.edges and len(mesh.edges) > len(unique_edges):
            edge_count = len(mesh.edges)
        else:
            edge_count = len(unique_edges)

        volume = round(abs(signed_volume), 6)
        surface_area = round(surface_area, 6)

        # 3. VRAM Memory Consumption Estimation (in bytes)
        # Position: 3 floats (4 bytes each) per vertex = 12 bytes
        pos_bytes = vertex_count * 3 * 4
        # Normal: 3 floats (4 bytes each) per vertex = 12 bytes
        norm_bytes = vertex_count * 3 * 4 if mesh.normals else 0
        # UV: 2 floats (4 bytes each) per vertex = 8 bytes
        uv_bytes = vertex_count * 2 * 4 if mesh.uvs else 0
        # Color: 3 floats (4 bytes each) per vertex = 12 bytes
        col_bytes = vertex_count * 3 * 4 if mesh.colors else 0
        # Index Buffer: 3 ints (4 bytes each) per triangle = 12 bytes
        index_bytes = triangle_count * 3 * 4
        vram_bytes = pos_bytes + norm_bytes + uv_bytes + col_bytes + index_bytes

        # 4. Performance Grading (<10k = A+, 10k-50k = A, 50k-150k = B, 150k-500k = C, >500k = D)
        if triangle_count < 10000:
            grade = "A+"
        elif triangle_count < 50000:
            grade = "A"
        elif triangle_count < 150000:
            grade = "B"
        elif triangle_count < 500000:
            grade = "C"
        else:
            grade = "D"

        # 5. Diagnostics
        diagnostics: List[str] = []
        if mesh.normals is None or len(mesh.normals) != vertex_count:
            diagnostics.append("Missing or incomplete vertex normals (recommended: run recompute_normals).")
        if mesh.uvs is None or len(mesh.uvs) != vertex_count:
            diagnostics.append("Missing UV texture coordinates.")
        if zero_area_faces > 0:
            diagnostics.append(f"Found {zero_area_faces} degenerate / zero-area triangles.")
        if triangle_count > 150000:
            diagnostics.append("High polygon count may reduce frame rates on mobile/embedded WebGL devices.")

        return {
            "vertex_count": vertex_count,
            "face_count": face_count,
            "triangle_count": triangle_count,
            "edge_count": edge_count,
            "bounding_box": bounding_box,
            "dimensions": dimensions,
            "center_of_mass": center_of_mass,
            "surface_area": surface_area,
            "volume": volume,
            "vram_bytes": vram_bytes,
            "performance_grade": grade,
            "diagnostics": diagnostics,
        }

    @staticmethod
    def recompute_normals(
        mesh_data: Union[MeshData, Dict[str, Any]],
        smooth: bool = True,
    ) -> MeshData:
        """Recompute vertex normals via cross-product facet averaging or flat shading.

        Args:
            mesh_data: Input MeshData or dictionary.
            smooth: If True, computes area-weighted smooth vertex normals.
                    If False, computes flat facet normals duplicated per face.

        Returns:
            New MeshData instance with updated unit-length normals.
        """
        mesh = ensure_mesh_data(mesh_data)
        vertices = mesh.vertices
        faces = mesh.faces
        vertex_count = len(vertices)

        if vertex_count == 0 or not faces:
            return MeshData(
                vertices=list(vertices),
                faces=list(faces),
                normals=[[0.0, 1.0, 0.0] for _ in range(vertex_count)],
                uvs=mesh.uvs,
                colors=mesh.colors,
                edges=mesh.edges,
                name=mesh.name,
                metadata=dict(mesh.metadata),
            )

        if not smooth:
            # Flat normals: compute each face normal and assign uniformly
            vert_normals = [[0.0, 0.0, 0.0] for _ in range(vertex_count)]
            vert_counts = [0] * vertex_count

            for face in faces:
                if len(face) < 3:
                    continue
                v0 = vertices[face[0]]
                v1 = vertices[face[1]]
                v2 = vertices[face[2]]
                fn = vec3_cross(vec3_sub(v1, v0), vec3_sub(v2, v0))
                fn_unit = vec3_normalize(fn)
                for vi in face:
                    vert_normals[vi] = vec3_add(vert_normals[vi], fn_unit)
                    vert_counts[vi] += 1

            final_normals = [
                vec3_normalize(vert_normals[i]) if vert_counts[i] > 0 else [0.0, 1.0, 0.0]
                for i in range(vertex_count)
            ]
        else:
            # Smooth area-weighted facet normal accumulation
            vert_normals = [[0.0, 0.0, 0.0] for _ in range(vertex_count)]

            for face in faces:
                flen = len(face)
                if flen < 3:
                    continue
                for k in range(1, flen - 1):
                    i0 = face[0]
                    i1 = face[k]
                    i2 = face[k + 1]

                    v0 = vertices[i0]
                    v1 = vertices[i1]
                    v2 = vertices[i2]

                    # Face cross product magnitude is proportional to triangle area
                    fn = vec3_cross(vec3_sub(v1, v0), vec3_sub(v2, v0))
                    vert_normals[i0] = vec3_add(vert_normals[i0], fn)
                    vert_normals[i1] = vec3_add(vert_normals[i1], fn)
                    vert_normals[i2] = vec3_add(vert_normals[i2], fn)

            final_normals = [
                vec3_normalize(vn, fallback=[0.0, 1.0, 0.0])
                for vn in vert_normals
            ]

        # Round for precision consistency
        rounded_normals = [
            [round(n[0], 6), round(n[1], 6), round(n[2], 6)]
            for n in final_normals
        ]

        return MeshData(
            vertices=list(vertices),
            faces=list(faces),
            normals=rounded_normals,
            uvs=mesh.uvs,
            colors=mesh.colors,
            edges=mesh.edges,
            name=mesh.name,
            metadata=dict(mesh.metadata),
        )

    @staticmethod
    def weld_vertices(
        mesh_data: Union[MeshData, Dict[str, Any]],
        tolerance: float = 1e-5,
    ) -> MeshData:
        """Deduplicate close vertices within spatial tolerance and remap face indices.

        Args:
            mesh_data: Input MeshData or dictionary.
            tolerance: Spatial proximity threshold.

        Returns:
            Optimized MeshData with deduplicated vertices and updated face indices.
        """
        mesh = ensure_mesh_data(mesh_data)
        vertices = mesh.vertices
        faces = mesh.faces

        new_vertices: List[List[float]] = []
        old_to_new: Dict[int, int] = {}

        # Spatial grid hashing for O(N) deduplication
        grid: Dict[Tuple[int, int, int], List[int]] = {}
        inv_tol = 1.0 / max(1e-8, tolerance)

        for old_idx, v in enumerate(vertices):
            gx = int(math.floor(v[0] * inv_tol))
            gy = int(math.floor(v[1] * inv_tol))
            gz = int(math.floor(v[2] * inv_tol))

            found_idx: Optional[int] = None
            # Check adjacent 27 neighborhood cells
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        cell_key = (gx + dx, gy + dy, gz + dz)
                        if cell_key in grid:
                            for candidate_new_idx in grid[cell_key]:
                                cv = new_vertices[candidate_new_idx]
                                dist = vec3_length(vec3_sub(v, cv))
                                if dist <= tolerance:
                                    found_idx = candidate_new_idx
                                    break
                        if found_idx is not None:
                            break
                    if found_idx is not None:
                        break
                if found_idx is not None:
                    break

            if found_idx is not None:
                old_to_new[old_idx] = found_idx
            else:
                new_idx = len(new_vertices)
                new_vertices.append(list(v))
                old_to_new[old_idx] = new_idx
                cell_key = (gx, gy, gz)
                if cell_key not in grid:
                    grid[cell_key] = []
                grid[cell_key].append(new_idx)

        # Remap faces and eliminate degenerate faces
        new_faces: List[List[int]] = []
        for face in faces:
            remapped = [old_to_new[vi] for vi in face]
            # Remove consecutive duplicates in face loop
            dedup_face: List[int] = []
            for vi in remapped:
                if not dedup_face or dedup_face[-1] != vi:
                    dedup_face.append(vi)
            if len(dedup_face) > 1 and dedup_face[0] == dedup_face[-1]:
                dedup_face.pop()

            if len(dedup_face) >= 3 and len(set(dedup_face)) >= 3:
                new_faces.append(dedup_face)

        # Update normals and UVs if present
        new_normals: Optional[List[List[float]]] = None
        if mesh.normals:
            temp_mesh = MeshData(vertices=new_vertices, faces=new_faces)
            recomputed = SceneOptimizer.recompute_normals(temp_mesh, smooth=True)
            new_normals = recomputed.normals

        return MeshData(
            vertices=new_vertices,
            faces=new_faces,
            normals=new_normals,
            uvs=None,  # UVs are disconnected per-vertex across seams
            colors=None,
            name=mesh.name,
            metadata={
                **mesh.metadata,
                "welded": True,
                "original_vertices": len(vertices),
                "welded_vertices": len(new_vertices),
            },
        )

    @staticmethod
    def triangulate_mesh(
        mesh_data: Union[MeshData, Dict[str, Any]],
    ) -> MeshData:
        """Convert all polygon faces in mesh to pure triangles.

        Args:
            mesh_data: Input MeshData or dictionary.

        Returns:
            MeshData containing only 3-vertex triangular faces.
        """
        mesh = ensure_mesh_data(mesh_data)
        tri_faces: List[List[int]] = []

        for face in mesh.faces:
            if len(face) == 3:
                tri_faces.append(list(face))
            elif len(face) > 3:
                for k in range(1, len(face) - 1):
                    tri_faces.append([face[0], face[k], face[k + 1]])

        return MeshData(
            vertices=list(mesh.vertices),
            faces=tri_faces,
            normals=list(mesh.normals) if mesh.normals else None,
            uvs=list(mesh.uvs) if mesh.uvs else None,
            colors=list(mesh.colors) if mesh.colors else None,
            edges=mesh.edges,
            name=mesh.name,
            metadata=dict(mesh.metadata),
        )

    @staticmethod
    def scale_mesh(
        mesh_data: Union[MeshData, Dict[str, Any]],
        factor: float = 1.0,
    ) -> MeshData:
        """Uniformly scale all vertex positions by factor."""
        mesh = ensure_mesh_data(mesh_data)
        scaled_verts = [
            [round(v[0] * factor, 6), round(v[1] * factor, 6), round(v[2] * factor, 6)]
            for v in mesh.vertices
        ]
        return MeshData(
            vertices=scaled_verts,
            faces=list(mesh.faces),
            normals=list(mesh.normals) if mesh.normals else None,
            uvs=list(mesh.uvs) if mesh.uvs else None,
            colors=list(mesh.colors) if mesh.colors else None,
            edges=mesh.edges,
            name=mesh.name,
            metadata={**mesh.metadata, "scale_factor": factor},
        )

    @staticmethod
    def center_mesh(
        mesh_data: Union[MeshData, Dict[str, Any]],
    ) -> MeshData:
        """Offset all vertex coordinates so the bounding box centroid lies exactly at the origin (0, 0, 0)."""
        mesh = ensure_mesh_data(mesh_data)
        if not mesh.vertices:
            return mesh

        min_x = min(v[0] for v in mesh.vertices)
        max_x = max(v[0] for v in mesh.vertices)
        min_y = min(v[1] for v in mesh.vertices)
        max_y = max(v[1] for v in mesh.vertices)
        min_z = min(v[2] for v in mesh.vertices)
        max_z = max(v[2] for v in mesh.vertices)

        cx = (min_x + max_x) * 0.5
        cy = (min_y + max_y) * 0.5
        cz = (min_z + max_z) * 0.5

        centered_verts = [
            [round(v[0] - cx, 6), round(v[1] - cy, 6), round(v[2] - cz, 6)]
            for v in mesh.vertices
        ]
        return MeshData(
            vertices=centered_verts,
            faces=list(mesh.faces),
            normals=list(mesh.normals) if mesh.normals else None,
            uvs=list(mesh.uvs) if mesh.uvs else None,
            colors=list(mesh.colors) if mesh.colors else None,
            edges=mesh.edges,
            name=mesh.name,
            metadata={**mesh.metadata, "centered": True, "offset": [cx, cy, cz]},
        )

    @staticmethod
    def decimate_mesh(
        mesh_data: Union[MeshData, Dict[str, Any]],
        target_ratio: float = 0.5,
    ) -> MeshData:
        """Decimate mesh polygon count towards target_ratio using edge-length contraction."""
        from .procedural_fractals import decimate_mesh as _decimate
        return _decimate(mesh_data, target_ratio=target_ratio)

    @staticmethod
    def generate_lod_pyramid(
        mesh_data: Union[MeshData, Dict[str, Any]],
        lod_ratios: Sequence[float] = (1.0, 0.5, 0.25, 0.1),
    ) -> Dict[str, Any]:
        """Generate a multi-tier Level-of-Detail (LOD) pyramid for 3D streaming and performance scaling."""
        from .procedural_fractals import generate_lod_pyramid as _gen_lod
        return _gen_lod(mesh_data, lod_ratios=lod_ratios)

