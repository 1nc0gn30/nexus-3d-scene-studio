"""HTTP UI and REST API Server for Nexus 3D Scene Studio.

Provides ThreadingHTTPServer serving web assets and JSON REST APIs for 3D procedural
mesh generation, format export (OBJ, STL, Three.js, HTML, ZIP), budget auditing,
presets catalog, and MCP configuration.
Pure Python standard library with zero external runtime dependencies.
"""

from __future__ import annotations

import base64
import datetime
import io
import json
import mimetypes
import os
import pathlib
import sys
import time
import urllib.parse
import zipfile
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple, Union

from .compat import (
    get_platform_info,
    get_system_diagnostics,
    normalize_path,
    open_in_browser,
    setup_utf8_console,
    to_posix_path,
)
from .geometry_engine import (
    MeshData,
    ensure_mesh_data,
    generate_buckyball,
    generate_fibonacci_lattice,
    generate_mobius_strip,
    generate_platonic_solid,
    generate_procedural_terrain,
    generate_solid,
    generate_superquadric,
    generate_tesseract_4d,
    generate_torus_knot,
)
from .mcp_server import SERVER_NAME, SERVER_VERSION, generate_mcp_client_config
from .mesh_exporter import MeshExporter
from .scene_optimizer import SceneOptimizer

_SERVER_START_TIME = time.time()


def get_default_presets() -> Dict[str, Any]:
    """Return catalog of built-in shape presets and configuration parameters."""
    return {
        "categories": [
            {
                "id": "tesseract",
                "name": "4D Hypercube (Tesseract)",
                "description": "4-dimensional hypercube projected into 3D via stereographic perspective.",
                "presets": [
                    {"id": "tess_default", "name": "Standard Projection", "params": {"size": 2.0, "angle_4d": 0.5, "distance_4d": 2.8}},
                    {"id": "tess_deep", "name": "Deep 4D Perspective", "params": {"size": 2.2, "angle_4d": 1.1, "distance_4d": 2.4}},
                    {"id": "tess_ortho", "name": "Orthogonal Slice", "params": {"size": 2.0, "angle_4d": 0.0, "distance_4d": 3.5}},
                ],
            },
            {
                "id": "torus_knot",
                "name": "Torus Knot",
                "description": "Parametric closed curve wrapped (p, q) times around a torus core.",
                "presets": [
                    {"id": "trefoil", "name": "Trefoil Knot (2, 3)", "params": {"p": 2, "q": 3, "major_radius": 2.0, "tube_radius": 0.45, "num_points": 140, "tube_segments": 16}},
                    {"id": "cinquefoil", "name": "Cinquefoil Knot (2, 5)", "params": {"p": 2, "q": 5, "major_radius": 2.0, "tube_radius": 0.35, "num_points": 160, "tube_segments": 16}},
                    {"id": "septafoil", "name": "Septafoil Knot (2, 7)", "params": {"p": 2, "q": 7, "major_radius": 2.2, "tube_radius": 0.28, "num_points": 180, "tube_segments": 16}},
                    {"id": "dense_coil", "name": "Dense Coil (3, 7)", "params": {"p": 3, "q": 7, "major_radius": 2.0, "tube_radius": 0.25, "num_points": 200, "tube_segments": 16}},
                ],
            },
            {
                "id": "superquadric",
                "name": "Superquadric",
                "description": "Deformable superellipsoid with pinching, tapering, bending, and twisting.",
                "presets": [
                    {"id": "rounded_cube", "name": "Rounded Box", "params": {"s1": 0.2, "s2": 0.2, "rx": 1.2, "ry": 1.2, "rz": 1.2, "pinch": 0.0, "taper": 0.0, "bend": 0.0, "twist": 0.0}},
                    {"id": "star_octahedron", "name": "Star Octahedron", "params": {"s1": 2.0, "s2": 2.0, "rx": 1.4, "ry": 1.4, "rz": 1.4, "pinch": 0.0, "taper": 0.0, "bend": 0.0, "twist": 0.0}},
                    {"id": "twisted_spindle", "name": "Twisted Spindle", "params": {"s1": 1.0, "s2": 0.4, "rx": 1.0, "ry": 1.0, "rz": 1.6, "pinch": 0.4, "taper": 0.0, "bend": 0.0, "twist": 1.5}},
                    {"id": "tapered_horn", "name": "Tapered Horn", "params": {"s1": 0.8, "s2": 0.8, "rx": 1.0, "ry": 1.0, "rz": 1.8, "pinch": 0.0, "taper": -0.6, "bend": 0.4, "twist": 0.8}},
                ],
            },
            {
                "id": "solid",
                "name": "Platonic Solids & Fullerene",
                "description": "Exact geometric polyhedra and Archimedean C60 fullerene buckyball.",
                "presets": [
                    {"id": "icosahedron", "name": "Icosahedron (20 Faces)", "params": {"solid_type": "icosahedron", "radius": 2.0}},
                    {"id": "dodecahedron", "name": "Dodecahedron (12 Pentagons)", "params": {"solid_type": "dodecahedron", "radius": 2.0}},
                    {"id": "octahedron", "name": "Octahedron (8 Triangles)", "params": {"solid_type": "octahedron", "radius": 2.0}},
                    {"id": "buckyball", "name": "Buckyball (C60 Soccer Ball)", "params": {"solid_type": "buckyball", "radius": 2.2}},
                ],
            },
            {
                "id": "terrain",
                "name": "Procedural Terrain",
                "description": "Coherent multi-octave noise heightmap terrain with elevation biomes.",
                "presets": [
                    {"id": "alpine_peaks", "name": "Alpine Peaks", "params": {"grid_size": 40, "scale": 5.0, "height_factor": 1.2, "octaves": 4}},
                    {"id": "rolling_hills", "name": "Rolling Hills", "params": {"grid_size": 32, "scale": 4.0, "height_factor": 0.5, "octaves": 3}},
                    {"id": "dunes", "name": "Desert Dunes", "params": {"grid_size": 36, "scale": 4.5, "height_factor": 0.4, "octaves": 2}},
                ],
            },
            {
                "id": "mobius",
                "name": "Möbius Strip",
                "description": "Single-sided non-orientable topological ribbon.",
                "presets": [
                    {"id": "mobius_standard", "name": "Single Half-Twist", "params": {"radius": 2.0, "width": 0.8, "twists": 1, "seg_u": 48, "seg_v": 8}},
                    {"id": "mobius_triple", "name": "Triple Twist Band", "params": {"radius": 2.2, "width": 0.7, "twists": 3, "seg_u": 64, "seg_v": 8}},
                ],
            },
            {
                "id": "fibonacci",
                "name": "Fibonacci Sphere Lattice",
                "description": "Golden spiral phyllotaxis point lattice and sphere mesh.",
                "presets": [
                    {"id": "fibo_200", "name": "200-Node Lattice", "params": {"count": 200, "radius": 2.2}},
                    {"id": "fibo_500", "name": "500-Node Dense Lattice", "params": {"count": 500, "radius": 2.5}},
                ],
            },
            {
                "id": "sdf_tpms",
                "name": "SDF & TPMS Isosurfaces",
                "description": "Marching Tetrahedra polygonized implicit fields: TPMS gyroid, Schwarz P, Neovius, Mandelbulb fractal, metaballs, smooth CSG.",
                "presets": [
                    {"id": "gyroid", "name": "TPMS Gyroid Infill", "params": {"preset": "gyroid", "resolution": 20, "bounds_scale": 1.2}},
                    {"id": "schwarz_p", "name": "Schwarz P Minimal Surface", "params": {"preset": "schwarz_p", "resolution": 20, "bounds_scale": 1.2}},
                    {"id": "neovius", "name": "Neovius Minimal Surface", "params": {"preset": "neovius", "resolution": 20, "bounds_scale": 1.2}},
                    {"id": "smooth_csg", "name": "Smooth CSG Blend", "params": {"preset": "smooth_csg", "resolution": 20, "bounds_scale": 1.2}},
                    {"id": "metaballs", "name": "Organic Metaballs", "params": {"preset": "metaballs", "resolution": 20, "bounds_scale": 1.2}},
                    {"id": "mandelbulb", "name": "3D Mandelbulb Fractal", "params": {"preset": "mandelbulb", "resolution": 20, "bounds_scale": 1.2}},
                    {"id": "twisted_torus", "name": "Twisted SDF Torus", "params": {"preset": "twisted_torus", "resolution": 20, "bounds_scale": 1.2}},
                ],
            },
        ]
    }


class NexusStudioRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP Request Handler serving static web studio assets and JSON REST APIs."""

    def __init__(self, *args: Any, directory: Optional[str] = None, **kwargs: Any) -> None:
        if directory is None:
            # Locate public directory
            base_pkg_dir = pathlib.Path(__file__).resolve().parent.parent.parent
            pub_dir = base_pkg_dir / "public"
            if not pub_dir.exists():
                pub_dir = pathlib.Path.cwd() / "public"
            directory = str(pub_dir) if pub_dir.exists() else str(pathlib.Path.cwd())
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet HTTP request logging."""
        # Suppress standard noisy logging unless debug
        if os.environ.get("NEXUS_DEBUG") == "1":
            sys.stderr.write(f"[HTTP] {format % args}\n")

    def _send_cors_headers(self) -> None:
        """Send standard Cross-Origin Resource Sharing headers."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")

    def _send_json_response(self, data: Any, status: int = 200) -> None:
        """Serialize and send a JSON payload with standard status code and CORS."""
        body = json.dumps(data, indent=2 if os.environ.get("NEXUS_DEBUG") == "1" else None)
        body_bytes = body.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body_bytes)

    def _read_json_body(self) -> Dict[str, Any]:
        """Read and parse JSON request body."""
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        raw_body = self.rfile.read(content_len).decode("utf-8", errors="replace")
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight OPTIONS request."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        """Route GET requests to API endpoints or static file handler."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # 1. API: Health Check
        if path == "/api/health":
            uptime = round(time.time() - _SERVER_START_TIME, 2)
            diag = get_platform_info().to_dict()
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            self._send_json_response({
                "status": "ok",
                "service": SERVER_NAME,
                "version": SERVER_VERSION,
                "uptime_seconds": uptime,
                "timestamp": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "platform": diag,
            })
            return

        # 2. API: Presets Catalog
        if path == "/api/presets":
            self._send_json_response(get_default_presets())
            return

        # 3. API: MCP Client Config
        if path == "/api/mcp/config":
            client = query_params.get("client", ["generic"])[0]
            config = generate_mcp_client_config(client_name=client)
            self._send_json_response(config)
            return

        # 4. API: System Diagnostics
        if path == "/api/diagnostics":
            diag = get_system_diagnostics()
            self._send_json_response(diag)
            return

        # 5. API: SDF Presets
        if path == "/api/sdf/presets":
            self._send_json_response({
                "presets": ["gyroid", "schwarz_p", "neovius", "smooth_csg", "metaballs", "mandelbulb", "twisted_torus"],
                "default_resolution": 20,
                "default_bounds_scale": 1.2,
            })
            return

        # 6. Static File or Embedded UI Fallback
        # If root requested and public/index.html does not exist, return rich embedded viewer
        if path in ("/", "/index.html"):
            target_index = pathlib.Path(self.directory) / "index.html"
            if not target_index.exists():
                self._serve_embedded_ui()
                return

        # Default static file serving via superclass
        super().do_GET()

    def do_POST(self) -> None:
        """Route POST requests to procedural generators, exporters, and auditors."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        req_data = self._read_json_body()

        # 1. API: Generate Shape
        if path == "/api/generate":
            try:
                shape_type = req_data.get("shape", req_data.get("shape_type", "torus_knot"))
                params = req_data.get("params", {})
                mesh = self._generate_mesh(shape_type, params)

                threejs_dict = MeshExporter.export_threejs_json(mesh)
                audit_dict = SceneOptimizer.audit_mesh_budget(mesh)

                self._send_json_response({
                    "status": "success",
                    "shape": shape_type,
                    "mesh": mesh.to_dict(),
                    "threejs": threejs_dict,
                    "audit": audit_dict,
                })
            except Exception as e:
                self._send_json_response({"status": "error", "message": str(e)}, status=400)
            return

        # 2. API: Generate SDF Isosurface
        if path == "/api/sdf/generate":
            try:
                preset = req_data.get("preset", "gyroid")
                resolution = int(req_data.get("resolution", 20))
                bounds_scale = float(req_data.get("bounds_scale", 1.2))
                from .sdf_isosurface import generate_sdf_preset
                mesh = generate_sdf_preset(preset=preset, resolution=resolution, bounds_scale=bounds_scale)
                threejs_dict = MeshExporter.export_threejs_json(mesh)
                audit_dict = SceneOptimizer.audit_mesh_budget(mesh)
                self._send_json_response({
                    "status": "success",
                    "preset": preset,
                    "mesh": mesh.to_dict(),
                    "threejs": threejs_dict,
                    "audit": audit_dict,
                })
            except Exception as e:
                self._send_json_response({"status": "error", "message": str(e)}, status=400)
            return

        # 3. API: Export Shape (OBJ, STL, Three.js, HTML)
        if path == "/api/export":
            try:
                fmt = req_data.get("format", "obj").lower().strip()
                raw_mesh = req_data.get("mesh_data")
                shape_type = req_data.get("shape", req_data.get("shape_type"))
                params = req_data.get("params", {})
                title = req_data.get("title", "Nexus 3D Model")
                theme = req_data.get("theme", "dark")

                if raw_mesh:
                    mesh = ensure_mesh_data(raw_mesh)
                elif shape_type:
                    mesh = self._generate_mesh(shape_type, params)
                else:
                    mesh = generate_torus_knot()

                if fmt == "obj":
                    content = MeshExporter.export_obj(mesh, object_name=mesh.name)
                    self._send_json_response({
                        "status": "success",
                        "format": "obj",
                        "filename": f"{mesh.name}.obj",
                        "content": content,
                        "mime_type": "text/plain",
                    })
                elif fmt == "stl":
                    content = MeshExporter.export_ascii_stl(mesh, solid_name=mesh.name)
                    self._send_json_response({
                        "status": "success",
                        "format": "stl",
                        "filename": f"{mesh.name}.stl",
                        "content": content,
                        "mime_type": "application/sla",
                    })
                elif fmt in ("json", "threejs"):
                    data = MeshExporter.export_threejs_json(mesh)
                    self._send_json_response({
                        "status": "success",
                        "format": "json",
                        "filename": f"{mesh.name}.json",
                        "data": data,
                        "mime_type": "application/json",
                    })
                elif fmt == "html":
                    content = MeshExporter.export_standalone_html(mesh, title=title, theme=theme)
                    self._send_json_response({
                        "status": "success",
                        "format": "html",
                        "filename": f"{mesh.name}.html",
                        "content": content,
                        "mime_type": "text/html",
                    })
                elif fmt in ("gltf", "glb"):
                    content = MeshExporter.export_gltf(mesh, object_name=mesh.name)
                    self._send_json_response({
                        "status": "success",
                        "format": "gltf",
                        "filename": f"{mesh.name}.gltf",
                        "content": content,
                        "mime_type": "model/gltf+json",
                    })
                elif fmt == "ply":
                    content = MeshExporter.export_ply(mesh, object_name=mesh.name)
                    self._send_json_response({
                        "status": "success",
                        "format": "ply",
                        "filename": f"{mesh.name}.ply",
                        "content": content,
                        "mime_type": "text/plain",
                    })
                else:
                    self._send_json_response({"status": "error", "message": f"Unsupported format: '{fmt}'"}, status=400)
            except Exception as e:
                self._send_json_response({"status": "error", "message": str(e)}, status=400)
            return

        # 3. API: Audit Mesh
        if path == "/api/audit":
            try:
                raw_mesh = req_data.get("mesh_data")
                shape_type = req_data.get("shape", req_data.get("shape_type"))
                params = req_data.get("params", {})

                if raw_mesh:
                    mesh = ensure_mesh_data(raw_mesh)
                elif shape_type:
                    mesh = self._generate_mesh(shape_type, params)
                else:
                    mesh = generate_torus_knot()

                audit_res = SceneOptimizer.audit_mesh_budget(mesh)
                audit_res["mesh_name"] = mesh.name
                self._send_json_response({"status": "success", "audit": audit_res})
            except Exception as e:
                self._send_json_response({"status": "error", "message": str(e)}, status=400)
            return

        # 4. API: Export Complete ZIP Archive
        if path == "/api/export-zip":
            try:
                raw_mesh = req_data.get("mesh_data")
                shape_type = req_data.get("shape", req_data.get("shape_type"))
                params = req_data.get("params", {})

                if raw_mesh:
                    mesh = ensure_mesh_data(raw_mesh)
                elif shape_type:
                    mesh = self._generate_mesh(shape_type, params)
                else:
                    mesh = generate_torus_knot()

                # Generate files for ZIP
                obj_content = MeshExporter.export_obj(mesh, object_name=mesh.name)
                mtl_content = MeshExporter.export_mtl(material_name=f"{mesh.name}_mat")
                stl_content = MeshExporter.export_ascii_stl(mesh, solid_name=mesh.name)
                threejs_dict = MeshExporter.export_threejs_json(mesh)
                gltf_content = MeshExporter.export_gltf(mesh, object_name=mesh.name)
                ply_content = MeshExporter.export_ply(mesh, object_name=mesh.name)
                html_content = MeshExporter.export_standalone_html(mesh, title=mesh.name)
                audit_dict = SceneOptimizer.audit_mesh_budget(mesh)

                now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                readme_content = f"""# {mesh.name} - 3D Scene Asset Bundle

Generated by **Nexus 3D Scene Studio** on {now_str}.

## Mesh Information
- **Vertex Count:** {len(mesh.vertices)}
- **Face Count:** {len(mesh.faces)}
- **Performance Grade:** {audit_dict.get('performance_grade', 'A+')}
- **Estimated VRAM:** {audit_dict.get('vram_bytes', 0)} bytes

## Included Files
1. `model.obj`: Wavefront 3D model geometry with vertices, normals, and UVs.
2. `material.mtl`: Companion Wavefront material library.
3. `model.stl`: Standard 3D printable stereolithography mesh.
4. `model.gltf`: glTF 2.0 ASCII scene specification with embedded PBR materials and base64 buffers.
5. `model.ply`: Stanford Triangle Format (ASCII PLY) polygon mesh.
6. `model.json`: Three.js BufferGeometry format for WebGL integration.
7. `viewer.html`: Self-contained interactive 3D WebGL viewer with OrbitControls.
8. `audit.json`: Polygon budget, bounding box, and diagnostic metrics.
"""

                # Build ZIP archive in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr("model.obj", obj_content)
                    zf.writestr("material.mtl", mtl_content)
                    zf.writestr("model.stl", stl_content)
                    zf.writestr("model.gltf", gltf_content)
                    zf.writestr("model.ply", ply_content)
                    zf.writestr("model.json", json.dumps(threejs_dict, indent=2))
                    zf.writestr("viewer.html", html_content)
                    zf.writestr("audit.json", json.dumps(audit_dict, indent=2))
                    zf.writestr("README.md", readme_content)

                zip_bytes = zip_buffer.getvalue()

                # If Accept header contains application/zip, return raw binary
                accept_hdr = self.headers.get("Accept", "")
                if "application/zip" in accept_hdr:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Disposition", f'attachment; filename="{mesh.name}.zip"')
                    self.send_header("Content-Length", str(len(zip_bytes)))
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(zip_bytes)
                else:
                    # Return base64 payload in JSON response
                    b64_zip = base64.b64encode(zip_bytes).decode("ascii")
                    self._send_json_response({
                        "status": "success",
                        "filename": f"{mesh.name}.zip",
                        "mime_type": "application/zip",
                        "size_bytes": len(zip_bytes),
                        "data_base64": b64_zip,
                    })
            except Exception as e:
                self._send_json_response({"status": "error", "message": str(e)}, status=400)
            return

        # Unknown POST endpoint
        self._send_json_response({"status": "error", "message": f"Endpoint not found: '{path}'"}, status=404)

    def _generate_mesh(self, shape_type: str, params: Dict[str, Any]) -> MeshData:
        """Helper to dispatch procedural shape generators."""
        st = shape_type.lower().strip()
        if st in ("tesseract", "tesseract_4d", "4d"):
            return generate_tesseract_4d(
                size=float(params.get("size", 2.0)),
                angle_4d=float(params.get("angle_4d", 0.5)),
                distance_4d=float(params.get("distance_4d", 2.8)),
            )
        elif st in ("torus_knot", "knot"):
            return generate_torus_knot(
                p=int(params.get("p", 3)),
                q=int(params.get("q", 5)),
                major_radius=float(params.get("major_radius", 2.0)),
                tube_radius=float(params.get("tube_radius", 0.4)),
                num_points=int(params.get("num_points", 120)),
                tube_segments=int(params.get("tube_segments", 16)),
            )
        elif st in ("superquadric", "superellipsoid"):
            return generate_superquadric(
                s1=float(params.get("s1", 0.2)),
                s2=float(params.get("s2", 0.2)),
                rx=float(params.get("rx", 1.0)),
                ry=float(params.get("ry", 1.0)),
                rz=float(params.get("rz", 1.0)),
                pinch=float(params.get("pinch", 0.0)),
                taper=float(params.get("taper", 0.0)),
                bend=float(params.get("bend", 0.0)),
                twist=float(params.get("twist", 0.0)),
                seg_u=int(params.get("seg_u", 32)),
                seg_v=int(params.get("seg_v", 32)),
            )
        elif st in ("solid", "platonic", "tetrahedron", "cube", "octahedron", "dodecahedron", "icosahedron", "buckyball", "c60"):
            solid_kind = params.get("solid_type", st)
            return generate_solid(
                solid_type=solid_kind,
                radius=float(params.get("radius", 2.0)),
            )
        elif st in ("terrain", "procedural_terrain"):
            return generate_procedural_terrain(
                grid_size=int(params.get("grid_size", 32)),
                scale=float(params.get("scale", 4.0)),
                height_factor=float(params.get("height_factor", 0.6)),
                octaves=int(params.get("octaves", 3)),
            )
        elif st in ("mobius", "mobius_strip"):
            return generate_mobius_strip(
                radius=float(params.get("radius", 2.0)),
                width=float(params.get("width", 0.8)),
                twists=int(params.get("twists", 1)),
            )
        elif st in ("fibonacci", "fibonacci_lattice"):
            return generate_fibonacci_lattice(
                count=int(params.get("count", 200)),
                radius=float(params.get("radius", 2.5)),
            )
        elif st in ("sdf", "gyroid", "schwarz_p", "neovius", "mandelbulb", "smooth_csg", "metaballs", "twisted_torus"):
            from .sdf_isosurface import generate_sdf_preset
            preset = st if st != "sdf" else params.get("preset", "gyroid")
            resolution = int(params.get("resolution", 20))
            bounds_scale = float(params.get("bounds_scale", 1.2))
            return generate_sdf_preset(preset=preset, resolution=resolution, bounds_scale=bounds_scale)
        else:
            raise ValueError(f"Unsupported shape type: '{shape_type}'")

    def _serve_embedded_ui(self) -> None:
        """Serve rich self-contained Material Design 3 fallback interface."""
        initial_mesh = generate_torus_knot(p=3, q=5)
        html_content = MeshExporter.export_standalone_html(
            initial_mesh,
            title="Nexus 3D Scene Studio - Procedural Geometry Studio",
            theme="dark",
        )
        body_bytes = html_content.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body_bytes)


def start_ui_server(
    host: str = "0.0.0.0",
    port: int = 8092,
    public_dir: Optional[str] = None,
    open_browser: bool = False,
) -> ThreadingHTTPServer:
    """Start the ThreadingHTTPServer instance for Nexus 3D Scene Studio.

    Args:
        host: Interface binding address.
        port: Listening TCP port.
        public_dir: Optional path to static web assets directory.
        open_browser: If True, launch default browser upon startup.

    Returns:
        Running ThreadingHTTPServer instance.
    """
    setup_utf8_console()

    handler_factory = lambda *args, **kwargs: NexusStudioRequestHandler(
        *args,
        directory=public_dir,
        **kwargs,
    )

    server = ThreadingHTTPServer((host, port), handler_factory)

    display_host = "localhost" if host in ("0.0.0.0", "127.0.0.1", "") else host
    url = f"http://{display_host}:{port}"
    print(f"[Nexus 3D Studio] Server started at {url}")
    print(f"[Nexus 3D Studio] Serving public assets from: {public_dir or 'auto-resolved'}")
    print(f"[Nexus 3D Studio] Press Ctrl+C to stop.")

    if open_browser:
        open_in_browser(url)

    return server


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nexus 3D Scene Studio UI Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8092, help="Port to listen on (default: 8092)")
    parser.add_argument("--public", default=None, help="Directory containing static web assets")
    parser.add_argument("--open", action="store_true", help="Automatically open browser")

    args = parser.parse_args()

    httpd = start_ui_server(
        host=args.host,
        port=args.port,
        public_dir=args.public,
        open_browser=args.open,
    )

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Nexus 3D Studio] Shutting down server...")
        httpd.server_close()
