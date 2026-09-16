"""Model Context Protocol (MCP) Server for Nexus 3D Scene Studio.

JSON-RPC 2.0 stdio server providing procedural 3D geometry generation,
mesh auditing, file format export (OBJ, STL, Three.js, Standalone HTML),
and cross-platform runtime diagnostics.
Pure Python standard library with zero external runtime dependencies.
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from .compat import get_platform_info, get_system_diagnostics, setup_utf8_console
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
from .mesh_exporter import MeshExporter
from .scene_optimizer import SceneOptimizer

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "nexus-3d-scene-studio"
SERVER_VERSION = "1.0.0"


@dataclasses.dataclass
class MCPTool:
    """Definition of an MCP Tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Any]


def generate_mcp_client_config(
    client_name: str,
    python_path: str = "python3",
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate configuration snippet for various MCP clients.

    Supported clients: 'claude', 'cursor', 'cline', 'zed', 'generic'.

    Args:
        client_name: Target client identifier.
        python_path: Path to Python executable.
        project_root: Optional root directory path.

    Returns:
        Structured JSON-compatible dictionary configuration.
    """
    c_name = client_name.lower().strip()
    root = project_root or os.getcwd()
    exec_path = python_path or sys.executable

    server_args = ["-m", "nexus_3d_scene_studio.mcp_server"]

    if c_name in ("claude", "claude_desktop", "claude-desktop"):
        return {
            "mcpServers": {
                SERVER_NAME: {
                    "command": exec_path,
                    "args": server_args,
                    "cwd": root,
                    "env": {
                        "PYTHONUNBUFFERED": "1",
                    },
                }
            }
        }
    elif c_name == "cursor":
        return {
            "mcpServers": {
                SERVER_NAME: {
                    "command": exec_path,
                    "args": server_args,
                    "cwd": root,
                }
            }
        }
    elif c_name == "cline":
        return {
            "mcpServers": {
                SERVER_NAME: {
                    "command": exec_path,
                    "args": server_args,
                    "cwd": root,
                    "disabled": False,
                    "autoApprove": [],
                }
            }
        }
    elif c_name == "zed":
        return {
            "context_servers": {
                SERVER_NAME: {
                    "command": {
                        "path": exec_path,
                        "args": server_args,
                    }
                }
            }
        }
    else:  # Generic fallback
        return {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
            "protocol_version": MCP_PROTOCOL_VERSION,
            "transport": "stdio",
            "command": exec_path,
            "args": server_args,
            "cwd": root,
            "description": "Pure Python stdlib 3D graphics studio and parametric geometry MCP server",
            "capabilities": {
                "tools": True,
                "resources": False,
                "prompts": False,
            },
        }


class MCPServer:
    """JSON-RPC 2.0 Model Context Protocol stdio server."""

    def __init__(self) -> None:
        self.tools: Dict[str, MCPTool] = {}
        self._register_builtins()

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """Register a new tool handler on the MCP server."""
        self.tools[name] = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return MCP tools/list format descriptions."""
        tool_list = []
        for tool in self.tools.values():
            tool_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            })
        return tool_list

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Execute registered tool by name with arguments."""
        if name not in self.tools:
            raise KeyError(f"Tool not found: '{name}'")
        args = arguments or {}
        return self.tools[name].handler(args)

    def _register_builtins(self) -> None:
        """Register the standard Nexus 3D Studio MCP tools."""

        # 1. nexus_generate_tesseract
        self.register_tool(
            name="nexus_generate_tesseract",
            description="Generate 4D Hypercube (Tesseract) stereographically projected into 3D mesh vertices, edges, and faces.",
            input_schema={
                "type": "object",
                "properties": {
                    "size": {"type": "number", "description": "Side length of 4D hypercube", "default": 2.0},
                    "angle_4d": {"type": "number", "description": "4D rotation angle in radians (X-W plane)", "default": 0.5},
                    "distance_4d": {"type": "number", "description": "4D camera projection distance along W-axis", "default": 2.8},
                    "format": {"type": "string", "enum": ["dict", "obj", "stl", "json", "html"], "default": "dict"},
                },
            },
            handler=self._handle_generate_tesseract,
        )

        # 2. nexus_generate_torus_knot
        self.register_tool(
            name="nexus_generate_torus_knot",
            description="Generate parametric (p, q) torus knot 3D tubular mesh with smooth normal vectors and UV coordinates.",
            input_schema={
                "type": "object",
                "properties": {
                    "p": {"type": "integer", "description": "Windings around interior torus axis", "default": 3},
                    "q": {"type": "integer", "description": "Windings through torus central hole", "default": 5},
                    "major_radius": {"type": "number", "description": "Major radius of knot", "default": 2.0},
                    "tube_radius": {"type": "number", "description": "Radius of cross-section tube", "default": 0.4},
                    "num_points": {"type": "integer", "description": "Curve sample points", "default": 120},
                    "tube_segments": {"type": "integer", "description": "Radial tube segments", "default": 16},
                    "format": {"type": "string", "enum": ["dict", "obj", "stl", "json", "html"], "default": "dict"},
                },
            },
            handler=self._handle_generate_torus_knot,
        )

        # 3. nexus_generate_superquadric
        self.register_tool(
            name="nexus_generate_superquadric",
            description="Generate superquadric 3D mesh with shape exponents e (east-west), n (north-south) and taper/pinch/bend/twist deformations.",
            input_schema={
                "type": "object",
                "properties": {
                    "s1": {"type": "number", "description": "East-West shape exponent (0.1=box, 1.0=sphere, 2.0=star)", "default": 0.2},
                    "s2": {"type": "number", "description": "North-South shape exponent", "default": 0.2},
                    "rx": {"type": "number", "description": "X half-diameter", "default": 1.0},
                    "ry": {"type": "number", "description": "Y half-diameter", "default": 1.0},
                    "rz": {"type": "number", "description": "Z half-diameter", "default": 1.0},
                    "pinch": {"type": "number", "description": "Z-axis pinch deformation coefficient", "default": 0.0},
                    "taper": {"type": "number", "description": "Z-axis linear taper coefficient", "default": 0.0},
                    "bend": {"type": "number", "description": "Z-axis curvature bend factor", "default": 0.0},
                    "twist": {"type": "number", "description": "Z-axis axial twist in radians", "default": 0.0},
                    "seg_u": {"type": "integer", "description": "Latitude segments", "default": 32},
                    "seg_v": {"type": "integer", "description": "Longitude segments", "default": 32},
                    "format": {"type": "string", "enum": ["dict", "obj", "stl", "json", "html"], "default": "dict"},
                },
            },
            handler=self._handle_generate_superquadric,
        )

        # 4. nexus_generate_solid
        self.register_tool(
            name="nexus_generate_solid",
            description="Generate exact Platonic solid (tetrahedron, cube, octahedron, dodecahedron, icosahedron) or Buckyball (C60 Fullerene).",
            input_schema={
                "type": "object",
                "properties": {
                    "solid_type": {
                        "type": "string",
                        "enum": ["tetrahedron", "cube", "octahedron", "dodecahedron", "icosahedron", "buckyball", "c60"],
                        "default": "icosahedron",
                    },
                    "radius": {"type": "number", "description": "Circumradius of solid", "default": 2.0},
                    "format": {"type": "string", "enum": ["dict", "obj", "stl", "json", "html"], "default": "dict"},
                },
            },
            handler=self._handle_generate_solid,
        )

        # 5. nexus_generate_terrain
        self.register_tool(
            name="nexus_generate_terrain",
            description="Generate procedural multi-octave coherent noise heightmap terrain mesh with vertex elevation coloring.",
            input_schema={
                "type": "object",
                "properties": {
                    "grid_size": {"type": "integer", "description": "Grid subdivisions per axis", "default": 32},
                    "scale": {"type": "number", "description": "Spatial span in world coordinates", "default": 4.0},
                    "height_factor": {"type": "number", "description": "Vertical elevation amplitude", "default": 0.6},
                    "octaves": {"type": "integer", "description": "Fractal noise frequency layers", "default": 3},
                    "format": {"type": "string", "enum": ["dict", "obj", "stl", "json", "html"], "default": "dict"},
                },
            },
            handler=self._handle_generate_terrain,
        )

        # 6. nexus_export_mesh
        self.register_tool(
            name="nexus_export_mesh",
            description="Convert procedural shape or mesh into Wavefront OBJ, STL, Three.js JSON, or Standalone interactive WebGL HTML.",
            input_schema={
                "type": "object",
                "properties": {
                    "format": {"type": "string", "enum": ["obj", "stl", "json", "html"], "default": "obj"},
                    "shape_type": {"type": "string", "description": "Preset shape name (e.g. tesseract, torus_knot, superquadric, icosahedron, terrain, buckyball)"},
                    "shape_params": {"type": "object", "description": "Parameters for procedural shape generator", "default": {}},
                    "mesh_data": {"type": "object", "description": "Raw mesh data dictionary with vertices and faces"},
                    "title": {"type": "string", "description": "Document title for HTML viewer export", "default": "Nexus 3D Viewer"},
                    "theme": {"type": "string", "enum": ["dark", "light"], "default": "dark"},
                },
                "required": ["format"],
            },
            handler=self._handle_export_mesh,
        )

        # 7. nexus_audit_mesh
        self.register_tool(
            name="nexus_audit_mesh",
            description="Analyze mesh complexity, polygon budget, bounding box, memory footprint, surface area, and WebGL performance grade (A+ to D).",
            input_schema={
                "type": "object",
                "properties": {
                    "shape_type": {"type": "string", "description": "Preset shape name to audit"},
                    "shape_params": {"type": "object", "description": "Parameters for shape generation", "default": {}},
                    "mesh_data": {"type": "object", "description": "Raw mesh data dictionary to audit"},
                },
            },
            handler=self._handle_audit_mesh,
        )

        # 8. nexus_get_diagnostics
        self.register_tool(
            name="nexus_get_diagnostics",
            description="Return multi-OS graphics, hardware, Python runtime, and MCP server diagnostics.",
            input_schema={
                "type": "object",
                "properties": {
                    "include_env": {"type": "boolean", "default": False},
                },
            },
            handler=self._handle_get_diagnostics,
        )

    # -----------------------------------------------------------------------
    # Built-in Tool Handlers
    # -----------------------------------------------------------------------

    def _format_mesh_output(self, mesh: MeshData, fmt: str) -> Any:
        fmt_clean = fmt.lower().strip()
        if fmt_clean == "obj":
            return MeshExporter.export_obj(mesh, object_name=mesh.name)
        elif fmt_clean == "stl":
            return MeshExporter.export_ascii_stl(mesh, solid_name=mesh.name)
        elif fmt_clean in ("json", "threejs"):
            return MeshExporter.export_threejs_json(mesh)
        elif fmt_clean == "html":
            return MeshExporter.export_standalone_html(mesh, title=mesh.name)
        return mesh.to_dict()

    def _generate_mesh_from_params(self, shape_type: str, params: Dict[str, Any]) -> MeshData:
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
        else:
            raise ValueError(f"Unsupported shape type: '{shape_type}'")

    def _handle_generate_tesseract(self, args: Dict[str, Any]) -> Any:
        size = float(args.get("size", 2.0))
        angle_4d = float(args.get("angle_4d", 0.5))
        distance_4d = float(args.get("distance_4d", 2.8))
        mesh = generate_tesseract_4d(size=size, angle_4d=angle_4d, distance_4d=distance_4d)
        fmt = args.get("format", "dict")
        return self._format_mesh_output(mesh, fmt)

    def _handle_generate_torus_knot(self, args: Dict[str, Any]) -> Any:
        mesh = generate_torus_knot(
            p=int(args.get("p", 3)),
            q=int(args.get("q", 5)),
            major_radius=float(args.get("major_radius", 2.0)),
            tube_radius=float(args.get("tube_radius", 0.4)),
            num_points=int(args.get("num_points", 120)),
            tube_segments=int(args.get("tube_segments", 16)),
        )
        fmt = args.get("format", "dict")
        return self._format_mesh_output(mesh, fmt)

    def _handle_generate_superquadric(self, args: Dict[str, Any]) -> Any:
        mesh = generate_superquadric(
            s1=float(args.get("s1", 0.2)),
            s2=float(args.get("s2", 0.2)),
            rx=float(args.get("rx", 1.0)),
            ry=float(args.get("ry", 1.0)),
            rz=float(args.get("rz", 1.0)),
            pinch=float(args.get("pinch", 0.0)),
            taper=float(args.get("taper", 0.0)),
            bend=float(args.get("bend", 0.0)),
            twist=float(args.get("twist", 0.0)),
            seg_u=int(args.get("seg_u", 32)),
            seg_v=int(args.get("seg_v", 32)),
        )
        fmt = args.get("format", "dict")
        return self._format_mesh_output(mesh, fmt)

    def _handle_generate_solid(self, args: Dict[str, Any]) -> Any:
        st = args.get("solid_type", "icosahedron")
        radius = float(args.get("radius", 2.0))
        mesh = generate_solid(solid_type=st, radius=radius)
        fmt = args.get("format", "dict")
        return self._format_mesh_output(mesh, fmt)

    def _handle_generate_terrain(self, args: Dict[str, Any]) -> Any:
        mesh = generate_procedural_terrain(
            grid_size=int(args.get("grid_size", 32)),
            scale=float(args.get("scale", 4.0)),
            height_factor=float(args.get("height_factor", 0.6)),
            octaves=int(args.get("octaves", 3)),
        )
        fmt = args.get("format", "dict")
        return self._format_mesh_output(mesh, fmt)

    def _handle_export_mesh(self, args: Dict[str, Any]) -> Any:
        fmt = args.get("format", "obj")
        raw_mesh = args.get("mesh_data")
        shape_type = args.get("shape_type")
        params = args.get("shape_params", {})
        title = args.get("title", "Nexus 3D Viewer")
        theme = args.get("theme", "dark")

        if raw_mesh:
            mesh = ensure_mesh_data(raw_mesh)
        elif shape_type:
            mesh = self._generate_mesh_from_params(shape_type, params)
        else:
            # Default to torus knot
            mesh = generate_torus_knot()

        fmt_clean = fmt.lower().strip()
        if fmt_clean == "obj":
            return {
                "format": "obj",
                "filename": f"{mesh.name}.obj",
                "content": MeshExporter.export_obj(mesh, object_name=mesh.name),
                "mime_type": "text/plain",
            }
        elif fmt_clean == "stl":
            return {
                "format": "stl",
                "filename": f"{mesh.name}.stl",
                "content": MeshExporter.export_ascii_stl(mesh, solid_name=mesh.name),
                "mime_type": "application/sla",
            }
        elif fmt_clean in ("json", "threejs"):
            return {
                "format": "json",
                "filename": f"{mesh.name}.json",
                "data": MeshExporter.export_threejs_json(mesh),
                "mime_type": "application/json",
            }
        elif fmt_clean == "html":
            return {
                "format": "html",
                "filename": f"{mesh.name}.html",
                "content": MeshExporter.export_standalone_html(mesh, title=title, theme=theme),
                "mime_type": "text/html",
            }
        else:
            raise ValueError(f"Unknown export format: '{fmt}'")

    def _handle_audit_mesh(self, args: Dict[str, Any]) -> Dict[str, Any]:
        raw_mesh = args.get("mesh_data")
        shape_type = args.get("shape_type")
        params = args.get("shape_params", {})

        if raw_mesh:
            mesh = ensure_mesh_data(raw_mesh)
        elif shape_type:
            mesh = self._generate_mesh_from_params(shape_type, params)
        else:
            mesh = generate_torus_knot()

        audit_res = SceneOptimizer.audit_mesh_budget(mesh)
        audit_res["mesh_name"] = mesh.name
        return audit_res

    def _handle_get_diagnostics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        diag = get_system_diagnostics()
        diag["mcp_server"] = {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
            "protocol_version": MCP_PROTOCOL_VERSION,
            "registered_tools_count": len(self.tools),
            "registered_tools": list(self.tools.keys()),
        }
        if not args.get("include_env", False):
            diag.pop("environment_variables", None)
        return diag

    # -----------------------------------------------------------------------
    # JSON-RPC 2.0 Dispatch & Protocol Handler
    # -----------------------------------------------------------------------

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single JSON-RPC 2.0 request or notification dictionary."""
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Notifications (no id)
        if req_id is None and method:
            # notifications/initialized or cancelled
            return None

        # 1. initialize
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {
                            "listChanged": False,
                        },
                        "resources": {},
                        "prompts": {},
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            }

        # 2. ping
        if method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            }

        # 3. tools/list
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": self.list_tools(),
                },
            }

        # 4. tools/call
        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32602,
                        "message": "Invalid params: 'name' is required in tools/call",
                    },
                }

            if tool_name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: '{tool_name}'",
                    },
                }

            try:
                res = self.call_tool(tool_name, tool_args)
                # MCP tools/call standard response format
                content_text = json.dumps(res, indent=2) if isinstance(res, (dict, list)) else str(res)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": content_text,
                            }
                        ],
                        "isError": False,
                    },
                }
            except Exception as e:
                err_text = f"Tool execution error in '{tool_name}': {str(e)}\n{traceback.format_exc()}"
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": err_text,
                            }
                        ],
                        "isError": True,
                    },
                }

        # 5. Unknown method
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: '{method}'",
            },
        }

    def run_stdio(self) -> None:
        """Execute stdio communication loop processing JSON-RPC lines."""
        setup_utf8_console()

        # Unbuffered binary or text reader from stdin
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                line_stripped = line.strip()
                if not line_stripped:
                    continue

                # Support Content-Length LSP/MCP header framing if present
                if line_stripped.lower().startswith("content-length:"):
                    parts = line_stripped.split(":", 1)
                    length = int(parts[1].strip())
                    # Consume empty line separator
                    empty_line = sys.stdin.readline()
                    payload = sys.stdin.read(length)
                    req_obj = json.loads(payload)
                else:
                    req_obj = json.loads(line_stripped)

                if isinstance(req_obj, dict):
                    response = self.handle_request(req_obj)
                    if response is not None:
                        out_line = json.dumps(response, separators=(",", ":"))
                        sys.stdout.write(out_line + "\n")
                        sys.stdout.flush()
                elif isinstance(req_obj, list):
                    # Batch request handling
                    batch_responses = []
                    for single_req in req_obj:
                        if isinstance(single_req, dict):
                            resp = self.handle_request(single_req)
                            if resp is not None:
                                batch_responses.append(resp)
                    if batch_responses:
                        out_line = json.dumps(batch_responses, separators=(",", ":"))
                        sys.stdout.write(out_line + "\n")
                        sys.stdout.flush()

            except (KeyboardInterrupt, SystemExit):
                break
            except json.JSONDecodeError as jde:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: invalid JSON - {str(jde)}",
                    },
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
            except Exception as ex:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal RPC server error: {str(ex)}",
                    },
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


def run_mcp_server() -> None:
    """Run the Nexus 3D Studio MCP server over stdio."""
    server = MCPServer()
    server.run_stdio()


if __name__ == "__main__":
    run_mcp_server()
