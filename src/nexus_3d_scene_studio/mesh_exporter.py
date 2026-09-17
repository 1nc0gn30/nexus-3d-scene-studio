"""Mesh Exporter for Nexus 3D Scene Studio.

Exports geometry to Wavefront OBJ + MTL, standard ASCII STL, Three.js BufferGeometry JSON,
and self-contained interactive 3D WebGL HTML applications.
Pure Python standard library with zero external runtime dependencies.
"""

from __future__ import annotations

import base64
import json
import math
import struct
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from .geometry_engine import MeshData, ensure_mesh_data, vec3_cross, vec3_normalize, vec3_sub


class MeshExporter:
    """Universal 3D Mesh Exporter for Nexus 3D Scene Studio."""

    @staticmethod
    def export_obj(
        mesh_data: Union[MeshData, Dict[str, Any]],
        object_name: str = "nexus_geometry",
    ) -> str:
        """Export geometry to Wavefront OBJ format string.

        Args:
            mesh_data: Input MeshData or dictionary.
            object_name: Geometry name in OBJ header.

        Returns:
            Wavefront OBJ formatted string.
        """
        mesh = ensure_mesh_data(mesh_data)
        lines: List[str] = [
            f"# Nexus 3D Scene Studio OBJ Exporter",
            f"# Object Name: {object_name}",
            f"# Vertices: {len(mesh.vertices)} | Faces: {len(mesh.faces)}",
            f"o {object_name}",
            "",
        ]

        # 1. Vertices (v x y z [r g b])
        has_colors = bool(mesh.colors and len(mesh.colors) == len(mesh.vertices))
        for idx, v in enumerate(mesh.vertices):
            if has_colors and mesh.colors:
                c = mesh.colors[idx]
                lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f} {c[0]:.4f} {c[1]:.4f} {c[2]:.4f}")
            else:
                lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")

        # 2. Texture Coordinates (vt u v)
        has_uvs = bool(mesh.uvs and len(mesh.uvs) == len(mesh.vertices))
        if has_uvs and mesh.uvs:
            lines.append("")
            for uv in mesh.uvs:
                lines.append(f"vt {uv[0]:.6f} {uv[1]:.6f}")

        # 3. Vertex Normals (vn nx ny nz)
        has_normals = bool(mesh.normals and len(mesh.normals) == len(mesh.vertices))
        if has_normals and mesh.normals:
            lines.append("")
            for n in mesh.normals:
                lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")

        # 4. Faces (f v/vt/vn)
        lines.append("")
        for face in mesh.faces:
            face_tokens: List[str] = []
            for v_idx in face:
                # 1-indexed in OBJ specification
                v_num = v_idx + 1
                if has_uvs and has_normals:
                    face_tokens.append(f"{v_num}/{v_num}/{v_num}")
                elif has_uvs and not has_normals:
                    face_tokens.append(f"{v_num}/{v_num}")
                elif not has_uvs and has_normals:
                    face_tokens.append(f"{v_num}//{v_num}")
                else:
                    face_tokens.append(f"{v_num}")
            lines.append(f"f {' '.join(face_tokens)}")

        return "\n".join(lines) + "\n"

    @staticmethod
    def export_mtl(
        material_name: str = "nexus_mat",
        diffuse: Tuple[float, float, float] = (0.1, 0.45, 0.91),
        specular: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        roughness: float = 0.2,
    ) -> str:
        """Export companion Wavefront Material Library (.mtl) string.

        Args:
            material_name: Identifier for material definition.
            diffuse: RGB diffuse color tuple in [0.0, 1.0].
            specular: RGB specular highlight color tuple in [0.0, 1.0].
            roughness: Surface roughness parameter [0.0, 1.0].

        Returns:
            MTL formatted string.
        """
        # Convert roughness to specular exponent (shininess) Ns in [0, 1000]
        clamped_r = max(0.01, min(1.0, roughness))
        ns = max(1.0, min(1000.0, (1.0 - clamped_r) * 1000.0))

        lines = [
            f"# Nexus 3D Scene Studio MTL Material Exporter",
            f"newmtl {material_name}",
            f"Ka 0.200000 0.200000 0.200000",
            f"Kd {diffuse[0]:.6f} {diffuse[1]:.6f} {diffuse[2]:.6f}",
            f"Ks {specular[0]:.6f} {specular[1]:.6f} {specular[2]:.6f}",
            f"Ns {ns:.2f}",
            f"d 1.000000",
            f"illum 2",
        ]
        return "\n".join(lines) + "\n"

    @staticmethod
    def export_ascii_stl(
        mesh_data: Union[MeshData, Dict[str, Any]],
        solid_name: str = "nexus_solid",
    ) -> str:
        """Export geometry to standard ASCII STL format string with facet normal triplets.

        Args:
            mesh_data: Input MeshData or dictionary.
            solid_name: Identifier name for solid block.

        Returns:
            Standard ASCII STL string.
        """
        mesh = ensure_mesh_data(mesh_data)
        safe_name = solid_name.replace(" ", "_")
        lines: List[str] = [f"solid {safe_name}"]

        verts = mesh.vertices

        for face in mesh.faces:
            if len(face) < 3:
                continue

            # Triangulate face if quad or n-gon (triangle fan)
            triangles: List[Tuple[int, int, int]] = []
            if len(face) == 3:
                triangles.append((face[0], face[1], face[2]))
            else:
                for k in range(1, len(face) - 1):
                    triangles.append((face[0], face[k], face[k + 1]))

            for i0, i1, i2 in triangles:
                v0 = verts[i0]
                v1 = verts[i1]
                v2 = verts[i2]

                # Compute face normal
                e1 = vec3_sub(v1, v0)
                e2 = vec3_sub(v2, v0)
                n = vec3_normalize(vec3_cross(e1, e2))

                lines.append(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}")
                lines.append("    outer loop")
                lines.append(f"      vertex {v0[0]:.6e} {v0[1]:.6e} {v0[2]:.6e}")
                lines.append(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}")
                lines.append(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}")
                lines.append("    endloop")
                lines.append("  endfacet")

        lines.append(f"endsolid {safe_name}\n")
        return "\n".join(lines)

    @staticmethod
    def export_threejs_json(
        mesh_data: Union[MeshData, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Export geometry into Three.js standard BufferGeometry JSON structure.

        Args:
            mesh_data: Input MeshData or dictionary.

        Returns:
            Dictionary matching Three.js BufferGeometry JSON specification.
        """
        mesh = ensure_mesh_data(mesh_data)

        # Flatten vertex positions
        pos_array: List[float] = []
        for v in mesh.vertices:
            pos_array.extend([round(v[0], 6), round(v[1], 6), round(v[2], 6)])

        attributes: Dict[str, Any] = {
            "position": {
                "itemSize": 3,
                "type": "Float32Array",
                "array": pos_array,
            }
        }

        # Normals
        if mesh.normals and len(mesh.normals) == len(mesh.vertices):
            norm_array: List[float] = []
            for n in mesh.normals:
                norm_array.extend([round(n[0], 6), round(n[1], 6), round(n[2], 6)])
            attributes["normal"] = {
                "itemSize": 3,
                "type": "Float32Array",
                "array": norm_array,
            }

        # UVs
        if mesh.uvs and len(mesh.uvs) == len(mesh.vertices):
            uv_array: List[float] = []
            for uv in mesh.uvs:
                uv_array.extend([round(uv[0], 6), round(uv[1], 6)])
            attributes["uv"] = {
                "itemSize": 2,
                "type": "Float32Array",
                "array": uv_array,
            }

        # Colors
        if mesh.colors and len(mesh.colors) == len(mesh.vertices):
            col_array: List[float] = []
            for c in mesh.colors:
                col_array.extend([round(c[0], 4), round(c[1], 4), round(c[2], 4)])
            attributes["color"] = {
                "itemSize": 3,
                "type": "Float32Array",
                "array": col_array,
            }

        # Triangulated Index Array
        index_array: List[int] = []
        for face in mesh.faces:
            if len(face) == 3:
                index_array.extend(face)
            elif len(face) > 3:
                # Fan triangulation
                for k in range(1, len(face) - 1):
                    index_array.extend([face[0], face[k], face[k + 1]])

        data_obj: Dict[str, Any] = {"attributes": attributes}
        if index_array:
            data_obj["index"] = {
                "type": "Uint32Array",
                "array": index_array,
            }

        return {
            "metadata": {
                "version": 4.5,
                "type": "BufferGeometry",
                "generator": "Nexus3DSceneStudio",
            },
            "data": data_obj,
        }

    @staticmethod
    def export_standalone_html(
        mesh_data: Union[MeshData, Dict[str, Any]],
        title: str = "Nexus 3D Viewer",
        theme: str = "dark",
    ) -> str:
        """Export standalone self-contained WebGL 3D Interactive Viewer HTML page.

        Includes Three.js scene setup, dynamic lighting, OrbitControls, wireframe/shading toggles,
        performance statistics HUD, and responsive viewport sizing.

        Args:
            mesh_data: Input MeshData or dictionary.
            title: HTML title banner.
            theme: Default visual theme ('dark' or 'light').

        Returns:
            Complete executable HTML document as a string.
        """
        mesh = ensure_mesh_data(mesh_data)
        threejs_dict = MeshExporter.export_threejs_json(mesh)
        threejs_json_str = json.dumps(threejs_dict)

        bg_color = "#0b0f19" if theme == "dark" else "#f8fafc"
        text_color = "#f1f5f9" if theme == "dark" else "#0f172a"
        panel_bg = "rgba(15, 23, 42, 0.85)" if theme == "dark" else "rgba(255, 255, 255, 0.9)"
        border_color = "rgba(255, 255, 255, 0.12)" if theme == "dark" else "rgba(0, 0, 0, 0.1)"

        vertex_count = len(mesh.vertices)
        face_count = len(mesh.faces)
        has_colors = bool(mesh.colors)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
    }}
    body, html {{
      width: 100%;
      height: 100%;
      overflow: hidden;
      background-color: {bg_color};
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: {text_color};
    }}
    #webgl-canvas {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      display: block;
      z-index: 1;
    }}
    .hud-panel {{
      position: absolute;
      z-index: 10;
      background: {panel_bg};
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid {border_color};
      border-radius: 12px;
      padding: 16px 20px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      font-size: 13px;
      line-height: 1.5;
    }}
    .top-left {{
      top: 20px;
      left: 20px;
      max-width: 320px;
    }}
    .top-right {{
      top: 20px;
      right: 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .title {{
      font-size: 16px;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-bottom: 6px;
      color: #38bdf8;
    }}
    .stat-row {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
      color: #94a3b8;
    }}
    .stat-val {{
      font-weight: 600;
      color: #f8fafc;
    }}
    .btn {{
      background: #1e293b;
      color: #f8fafc;
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 8px;
      padding: 8px 14px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}
    .btn:hover {{
      background: #334155;
      border-color: #38bdf8;
      transform: translateY(-1px);
    }}
    .btn.active {{
      background: #0284c7;
      border-color: #38bdf8;
    }}
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
  <div class="hud-panel top-left">
    <div class="title">{title}</div>
    <div class="stat-row"><span>Mesh:</span> <span class="stat-val">{mesh.name}</span></div>
    <div class="stat-row"><span>Vertices:</span> <span class="stat-val">{vertex_count:,}</span></div>
    <div class="stat-row"><span>Faces:</span> <span class="stat-val">{face_count:,}</span></div>
    <div class="stat-row"><span>Colors:</span> <span class="stat-val">{'Vertex RGB' if has_colors else 'Standard PBR'}</span></div>
  </div>

  <div class="hud-panel top-right">
    <button class="btn" id="btn-wireframe">Toggle Wireframe</button>
    <button class="btn active" id="btn-rotate">Auto-Rotation: ON</button>
    <button class="btn" id="btn-theme">Toggle Lighting</button>
    <button class="btn" id="btn-reset">Reset Camera</button>
  </div>

  <canvas id="webgl-canvas"></canvas>

  <script>
    const geometryData = {threejs_json_str};

    let scene, camera, renderer, controls, meshObj, wireframeMesh;
    let autoRotate = true;
    let lightMode = 0;

    function init() {{
      const canvas = document.getElementById('webgl-canvas');
      scene = new THREE.Scene();
      scene.background = new THREE.Color('{bg_color}');

      camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
      camera.position.set(0, 3, 6);

      renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: false }});
      renderer.setPixelRatio(window.devicePixelRatio || 1);
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;

      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;

      // Lights
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
      scene.add(ambientLight);

      const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
      dirLight1.position.set(5, 10, 7);
      dirLight1.castShadow = true;
      scene.add(dirLight1);

      const dirLight2 = new THREE.DirectionalLight(0x38bdf8, 0.4);
      dirLight2.position.set(-5, -5, -5);
      scene.add(dirLight2);

      // Load Geometry
      const loader = new THREE.BufferGeometryLoader();
      const geometry = loader.parse(geometryData);
      geometry.computeVertexNormals();
      geometry.center();

      const hasVertexColors = !!geometry.attributes.color;

      const material = new THREE.MeshStandardMaterial({{
        color: hasVertexColors ? 0xffffff : 0x0284c7,
        vertexColors: hasVertexColors,
        roughness: 0.25,
        metalness: 0.15,
        side: THREE.DoubleSide
      }});

      meshObj = new THREE.Mesh(geometry, material);
      meshObj.castShadow = true;
      meshObj.receiveShadow = true;
      scene.add(meshObj);

      const wireMaterial = new THREE.MeshBasicMaterial({{
        color: 0x38bdf8,
        wireframe: true,
        transparent: true,
        opacity: 0.3
      }});
      wireframeMesh = new THREE.Mesh(geometry, wireMaterial);
      wireframeMesh.visible = false;
      scene.add(wireframeMesh);

      // Event Listeners
      window.addEventListener('resize', onResize);
      document.getElementById('btn-wireframe').addEventListener('click', () => {{
        wireframeMesh.visible = !wireframeMesh.visible;
        document.getElementById('btn-wireframe').classList.toggle('active', wireframeMesh.visible);
      }});

      document.getElementById('btn-rotate').addEventListener('click', (e) => {{
        autoRotate = !autoRotate;
        e.target.textContent = 'Auto-Rotation: ' + (autoRotate ? 'ON' : 'OFF');
        e.target.classList.toggle('active', autoRotate);
      }});

      document.getElementById('btn-theme').addEventListener('click', () => {{
        lightMode = (lightMode + 1) % 3;
        if (lightMode === 0) {{
          scene.background.set('{bg_color}');
          dirLight1.color.set(0xffffff);
          dirLight2.color.set(0x38bdf8);
        }} else if (lightMode === 1) {{
          scene.background.set(0x180a2a);
          dirLight1.color.set(0xf43f5e);
          dirLight2.color.set(0x818cf8);
        }} else {{
          scene.background.set(0x022c22);
          dirLight1.color.set(0x10b981);
          dirLight2.color.set(0xf59e0b);
        }}
      }});

      document.getElementById('btn-reset').addEventListener('click', () => {{
        camera.position.set(0, 3, 6);
        controls.target.set(0, 0, 0);
        controls.update();
      }});

      animate();
    }}

    function onResize() {{
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }}

    function animate() {{
      requestAnimationFrame(animate);
      if (autoRotate && meshObj) {{
        meshObj.rotation.y += 0.005;
        if (wireframeMesh) wireframeMesh.rotation.y = meshObj.rotation.y;
      }}
      controls.update();
      renderer.render(scene, camera);
    }}

    window.onload = init;
  </script>
</body>
</html>
"""
        return html_template

    @staticmethod
    def export_gltf_dict(
        mesh_data: Union[MeshData, Dict[str, Any]],
        object_name: str = "nexus_geometry",
        material_name: str = "nexus_pbr_material",
        metallic: float = 0.15,
        roughness: float = 0.35,
        color: Tuple[float, float, float, float] = (0.1, 0.45, 0.91, 1.0),
    ) -> Dict[str, Any]:
        """Export geometry into standard glTF 2.0 ASCII scene specification dictionary.

        Embeds all binary buffer data (vertices, triangulated indices, normals, UVs, colors)
        as an inline Base64 data URI buffer with standard PBR metallic-roughness material.

        Args:
            mesh_data: Input MeshData or dictionary.
            object_name: Mesh / Node identifier.
            material_name: PBR material identifier.
            metallic: Surface metallic factor in [0.0, 1.0].
            roughness: Surface roughness factor in [0.0, 1.0].
            color: Base RGBA diffuse color tuple in [0.0, 1.0].

        Returns:
            Dictionary matching official glTF 2.0 schema.
        """
        mesh = ensure_mesh_data(mesh_data)
        verts = mesh.vertices
        if not verts:
            raise ValueError("Cannot export empty mesh with 0 vertices to glTF")

        # 1. Triangulate faces
        indices: List[int] = []
        for face in mesh.faces:
            if len(face) == 3:
                indices.extend(face)
            elif len(face) > 3:
                for k in range(1, len(face) - 1):
                    indices.extend([face[0], face[k], face[k + 1]])

        # 2. Pack binary buffers
        raw_buffer = bytearray()
        buffer_views: List[Dict[str, Any]] = []
        accessors: List[Dict[str, Any]] = []
        attributes: Dict[str, int] = {}

        # 2a. Position Accessor (FLOAT, VEC3)
        pos_offset = len(raw_buffer)
        min_x = min(v[0] for v in verts)
        max_x = max(v[0] for v in verts)
        min_y = min(v[1] for v in verts)
        max_y = max(v[1] for v in verts)
        min_z = min(v[2] for v in verts)
        max_z = max(v[2] for v in verts)

        for v in verts:
            raw_buffer.extend(struct.pack("<fff", float(v[0]), float(v[1]), float(v[2])))

        pos_len = len(raw_buffer) - pos_offset
        buffer_views.append({
            "buffer": 0,
            "byteOffset": pos_offset,
            "byteLength": pos_len,
            "target": 34962,  # ARRAY_BUFFER
        })
        accessors.append({
            "bufferView": len(buffer_views) - 1,
            "byteOffset": 0,
            "componentType": 5126,  # FLOAT
            "count": len(verts),
            "type": "VEC3",
            "min": [round(min_x, 6), round(min_y, 6), round(min_z, 6)],
            "max": [round(max_x, 6), round(max_y, 6), round(max_z, 6)],
        })
        attributes["POSITION"] = 0

        # 2b. Indices Accessor
        if indices:
            pad = (4 - (len(raw_buffer) % 4)) % 4
            raw_buffer.extend(b"\x00" * pad)

            idx_offset = len(raw_buffer)
            use_uint32 = max(indices) >= 65536
            idx_component = 5125 if use_uint32 else 5123
            pack_fmt = "<I" if use_uint32 else "<H"

            for idx in indices:
                raw_buffer.extend(struct.pack(pack_fmt, int(idx)))

            idx_len = len(raw_buffer) - idx_offset
            buffer_views.append({
                "buffer": 0,
                "byteOffset": idx_offset,
                "byteLength": idx_len,
                "target": 34963,  # ELEMENT_ARRAY_BUFFER
            })
            accessors.append({
                "bufferView": len(buffer_views) - 1,
                "byteOffset": 0,
                "componentType": idx_component,
                "count": len(indices),
                "type": "SCALAR",
                "min": [min(indices)],
                "max": [max(indices)],
            })
            indices_accessor_idx: Optional[int] = len(accessors) - 1
        else:
            indices_accessor_idx = None

        # 2c. Normals Accessor (optional)
        if mesh.normals and len(mesh.normals) == len(verts):
            pad = (4 - (len(raw_buffer) % 4)) % 4
            raw_buffer.extend(b"\x00" * pad)
            norm_offset = len(raw_buffer)
            for n in mesh.normals:
                raw_buffer.extend(struct.pack("<fff", float(n[0]), float(n[1]), float(n[2])))
            norm_len = len(raw_buffer) - norm_offset
            buffer_views.append({
                "buffer": 0,
                "byteOffset": norm_offset,
                "byteLength": norm_len,
                "target": 34962,
            })
            accessors.append({
                "bufferView": len(buffer_views) - 1,
                "byteOffset": 0,
                "componentType": 5126,
                "count": len(verts),
                "type": "VEC3",
            })
            attributes["NORMAL"] = len(accessors) - 1

        # 2d. UVs Accessor (optional)
        if mesh.uvs and len(mesh.uvs) == len(verts):
            pad = (4 - (len(raw_buffer) % 4)) % 4
            raw_buffer.extend(b"\x00" * pad)
            uv_offset = len(raw_buffer)
            for uv in mesh.uvs:
                raw_buffer.extend(struct.pack("<ff", float(uv[0]), float(uv[1])))
            uv_len = len(raw_buffer) - uv_offset
            buffer_views.append({
                "buffer": 0,
                "byteOffset": uv_offset,
                "byteLength": uv_len,
                "target": 34962,
            })
            accessors.append({
                "bufferView": len(buffer_views) - 1,
                "byteOffset": 0,
                "componentType": 5126,
                "count": len(verts),
                "type": "VEC2",
            })
            attributes["TEXCOORD_0"] = len(accessors) - 1

        # 2e. Vertex Colors Accessor (optional)
        if mesh.colors and len(mesh.colors) == len(verts):
            pad = (4 - (len(raw_buffer) % 4)) % 4
            raw_buffer.extend(b"\x00" * pad)
            col_offset = len(raw_buffer)
            for c in mesh.colors:
                raw_buffer.extend(struct.pack("<fff", float(c[0]), float(c[1]), float(c[2])))
            col_len = len(raw_buffer) - col_offset
            buffer_views.append({
                "buffer": 0,
                "byteOffset": col_offset,
                "byteLength": col_len,
                "target": 34962,
            })
            accessors.append({
                "bufferView": len(buffer_views) - 1,
                "byteOffset": 0,
                "componentType": 5126,
                "count": len(verts),
                "type": "VEC3",
            })
            attributes["COLOR_0"] = len(accessors) - 1

        # Base64 data URI buffer
        b64_buffer = base64.b64encode(raw_buffer).decode("ascii")

        primitive_dict: Dict[str, Any] = {
            "attributes": attributes,
            "material": 0,
            "mode": 4,  # TRIANGLES
        }
        if indices_accessor_idx is not None:
            primitive_dict["indices"] = indices_accessor_idx

        gltf_doc: Dict[str, Any] = {
            "asset": {
                "version": "2.0",
                "generator": "Nexus 3D Scene Studio glTF Exporter (Pure Python)",
                "copyright": "Design influenced by Material 3 tokens",
            },
            "scene": 0,
            "scenes": [
                {
                    "name": "DefaultScene",
                    "nodes": [0],
                }
            ],
            "nodes": [
                {
                    "name": object_name,
                    "mesh": 0,
                }
            ],
            "materials": [
                {
                    "name": material_name,
                    "pbrMetallicRoughness": {
                        "baseColorFactor": [float(color[0]), float(color[1]), float(color[2]), float(color[3]) if len(color) > 3 else 1.0],
                        "metallicFactor": float(max(0.0, min(1.0, metallic))),
                        "roughnessFactor": float(max(0.0, min(1.0, roughness))),
                    },
                    "doubleSided": True,
                }
            ],
            "meshes": [
                {
                    "name": object_name,
                    "primitives": [primitive_dict],
                }
            ],
            "accessors": accessors,
            "bufferViews": buffer_views,
            "buffers": [
                {
                    "byteLength": len(raw_buffer),
                    "uri": f"data:application/octet-stream;base64,{b64_buffer}",
                }
            ],
        }
        return gltf_doc

    @staticmethod
    def export_gltf(
        mesh_data: Union[MeshData, Dict[str, Any]],
        object_name: str = "nexus_geometry",
        material_name: str = "nexus_pbr_material",
        metallic: float = 0.15,
        roughness: float = 0.35,
        color: Tuple[float, float, float, float] = (0.1, 0.45, 0.91, 1.0),
        indent: int = 2,
    ) -> str:
        """Export geometry to glTF 2.0 ASCII formatted JSON string."""
        gltf_dict = MeshExporter.export_gltf_dict(
            mesh_data=mesh_data,
            object_name=object_name,
            material_name=material_name,
            metallic=metallic,
            roughness=roughness,
            color=color,
        )
        return json.dumps(gltf_dict, indent=indent)

    @staticmethod
    def export_ply(
        mesh_data: Union[MeshData, Dict[str, Any]],
        object_name: str = "nexus_mesh",
    ) -> str:
        """Export geometry to Stanford ASCII PLY (Polygon File Format) string.

        Args:
            mesh_data: Input MeshData or dictionary.
            object_name: Header comment identifier.

        Returns:
            Standard ASCII PLY string.
        """
        mesh = ensure_mesh_data(mesh_data)
        verts = mesh.vertices
        faces = mesh.faces

        has_normals = bool(mesh.normals and len(mesh.normals) == len(verts))
        has_colors = bool(mesh.colors and len(mesh.colors) == len(verts))

        lines: List[str] = [
            "ply",
            "format ascii 1.0",
            f"comment Nexus 3D Scene Studio PLY Exporter - {object_name}",
            "comment Design influenced by Material 3 tokens",
            f"element vertex {len(verts)}",
            "property float x",
            "property float y",
            "property float z",
        ]

        if has_normals:
            lines.extend([
                "property float nx",
                "property float ny",
                "property float nz",
            ])

        if has_colors:
            lines.extend([
                "property uchar red",
                "property uchar green",
                "property uchar blue",
            ])

        lines.extend([
            f"element face {len(faces)}",
            "property list uchar int vertex_indices",
            "end_header",
        ])

        for idx, v in enumerate(verts):
            parts = [f"{v[0]:.6f}", f"{v[1]:.6f}", f"{v[2]:.6f}"]
            if has_normals and mesh.normals:
                n = mesh.normals[idx]
                parts.extend([f"{n[0]:.6f}", f"{n[1]:.6f}", f"{n[2]:.6f}"])
            if has_colors and mesh.colors:
                c = mesh.colors[idx]
                r = int(max(0, min(255, round(c[0] * 255))))
                g = int(max(0, min(255, round(c[1] * 255))))
                b = int(max(0, min(255, round(c[2] * 255))))
                parts.extend([str(r), str(g), str(b)])
            lines.append(" ".join(parts))

        for face in faces:
            parts = [str(len(face))] + [str(v_idx) for v_idx in face]
            lines.append(" ".join(parts))

        return "\n".join(lines) + "\n"
