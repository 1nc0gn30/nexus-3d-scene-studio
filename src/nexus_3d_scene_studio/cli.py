"""Command Line Interface (CLI) for Nexus 3D Scene Studio.

Provides command line tools for procedural 3D shape generation, polygon budget auditing,
stdio MCP server running, Nexus 3D Studio Web UI server (design influenced by Material 3), and platform diagnostics.
Pure Python standard library with zero external runtime dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import Any, Dict, List, Optional, Sequence

from .compat import (
    atomic_write_text,
    ensure_utf8,
    get_platform_info,
    get_system_diagnostics,
    normalize_path,
    open_in_browser,
    setup_utf8_console,
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
from .mcp_server import (
    MCPServer,
    SERVER_NAME,
    SERVER_VERSION,
    generate_mcp_client_config,
    run_mcp_server,
)
from .mesh_exporter import MeshExporter
from .scene_optimizer import SceneOptimizer
from .ui_server import start_ui_server

# ANSI Color formatting utilities (fallback safely if not interactive TTY)
_IS_TTY = sys.stdout.isatty() and sys.platform != "win32" or ("COLORTERM" in os.environ)


def _colorize(text: str, color_code: str) -> str:
    if not _IS_TTY:
        return text
    return f"\033[{color_code}m{text}\033[0m"


def _bold(text: str) -> str:
    return _colorize(text, "1")


def _cyan(text: str) -> str:
    return _colorize(text, "36")


def _green(text: str) -> str:
    return _colorize(text, "32")


def _yellow(text: str) -> str:
    return _colorize(text, "33")


def _magenta(text: str) -> str:
    return _colorize(text, "35")


def _red(text: str) -> str:
    return _colorize(text, "31")


def _parse_params_arg(param_str: Optional[str]) -> Dict[str, Any]:
    """Parse JSON string or comma-separated key=value pairs into dictionary."""
    if not param_str:
        return {}
    param_str = param_str.strip()
    if not param_str:
        return {}

    # Try JSON parsing first
    if param_str.startswith("{") and param_str.endswith("}"):
        try:
            return json.loads(param_str)
        except json.JSONDecodeError:
            pass

    # Parse key=value,key2=value2
    result: Dict[str, Any] = {}
    for part in param_str.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            k = k.strip()
            v = v.strip()
            # Try type casting
            try:
                if "." in v:
                    result[k] = float(v)
                else:
                    result[k] = int(v)
            except ValueError:
                if v.lower() == "true":
                    result[k] = True
                elif v.lower() == "false":
                    result[k] = False
                else:
                    result[k] = v
    return result


def _resolve_shape(shape_name: str, params: Dict[str, Any]) -> MeshData:
    """Generate MeshData from shape name and parameter dictionary."""
    st = shape_name.lower().strip()
    if st in ("tesseract", "tesseract_4d", "4d", "hypercube"):
        return generate_tesseract_4d(
            size=float(params.get("size", 2.0)),
            angle_4d=float(params.get("angle_4d", 0.5)),
            distance_4d=float(params.get("distance_4d", 2.8)),
        )
    elif st in ("torus_knot", "knot", "trefoil", "cinquefoil"):
        return generate_torus_knot(
            p=int(params.get("p", 3)),
            q=int(params.get("q", 5)),
            major_radius=float(params.get("major_radius", 2.0)),
            tube_radius=float(params.get("tube_radius", 0.4)),
            num_points=int(params.get("num_points", 120)),
            tube_segments=int(params.get("tube_segments", 16)),
        )
    elif st in ("superquadric", "superellipsoid", "spindle"):
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
        solid_type = params.get("solid_type", st)
        return generate_solid(
            solid_type=solid_type,
            radius=float(params.get("radius", 2.0)),
        )
    elif st in ("terrain", "procedural_terrain", "heightmap"):
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
    elif st in ("fibonacci", "fibonacci_lattice", "lattice"):
        return generate_fibonacci_lattice(
            count=int(params.get("count", 200)),
            radius=float(params.get("radius", 2.5)),
        )
    else:
        raise ValueError(
            f"Unknown procedural shape: '{shape_name}'. "
            f"Supported shapes: tesseract, torus_knot, superquadric, solid, tetrahedron, "
            f"cube, octahedron, dodecahedron, icosahedron, buckyball, terrain, mobius, fibonacci."
        )


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------

def handle_generate(args: argparse.Namespace) -> int:
    """Handle `generate` subcommand."""
    try:
        params = _parse_params_arg(args.params)
        mesh = _resolve_shape(args.shape, params)

        fmt = args.format.lower().strip()
        output_content: str = ""

        if fmt == "obj":
            output_content = MeshExporter.export_obj(mesh, object_name=mesh.name)
        elif fmt == "stl":
            output_content = MeshExporter.export_ascii_stl(mesh, solid_name=mesh.name)
        elif fmt in ("json", "threejs"):
            threejs_dict = MeshExporter.export_threejs_json(mesh)
            output_content = json.dumps(threejs_dict, indent=2)
        elif fmt == "html":
            output_content = MeshExporter.export_standalone_html(
                mesh,
                title=f"{mesh.name} - Nexus 3D Studio",
                theme=getattr(args, "theme", "dark"),
            )
        else:
            sys.stderr.write(f"Error: Unsupported output format '{fmt}'\n")
            return 1

        if args.output:
            out_path = pathlib.Path(args.output).resolve()
            atomic_write_text(out_path, output_content)
            print(f"{_green('✓ Generated')} {mesh.name} ({len(mesh.vertices)} vertices, {len(mesh.faces)} faces) -> {out_path}")
        else:
            sys.stdout.write(output_content)

        return 0
    except Exception as e:
        sys.stderr.write(f"Error during shape generation: {str(e)}\n")
        return 1


def handle_audit(args: argparse.Namespace) -> int:
    """Handle `audit` subcommand."""
    target = args.target.strip()
    target_path = pathlib.Path(target)

    mesh: Optional[MeshData] = None

    # Check if target is a file on disk
    if target_path.exists() and target_path.is_file():
        try:
            content = target_path.read_text(encoding="utf-8", errors="replace")
            # Determine format
            if target_path.suffix.lower() == ".obj":
                # Basic OBJ parser
                vertices = []
                faces = []
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("v "):
                        parts = line.split()[1:4]
                        vertices.append([float(p) for p in parts])
                    elif line.startswith("f "):
                        face_indices = []
                        for token in line.split()[1:]:
                            v_idx = int(token.split("/")[0]) - 1
                            face_indices.append(v_idx)
                        if len(face_indices) >= 3:
                            faces.append(face_indices)
                mesh = MeshData(vertices=vertices, faces=faces, name=target_path.stem)
            elif target_path.suffix.lower() == ".json":
                json_data = json.loads(content)
                if "data" in json_data and "attributes" in json_data["data"]:
                    # Three.js BufferGeometry format
                    pos = json_data["data"]["attributes"]["position"]["array"]
                    verts = [[pos[i], pos[i + 1], pos[i + 2]] for i in range(0, len(pos), 3)]
                    indices = json_data["data"].get("index", {}).get("array", [])
                    faces = [[indices[i], indices[i + 1], indices[i + 2]] for i in range(0, len(indices), 3)] if indices else []
                    mesh = MeshData(vertices=verts, faces=faces, name=target_path.stem)
                else:
                    mesh = ensure_mesh_data(json_data)
            else:
                sys.stderr.write(f"Unsupported file format for audit: '{target_path.suffix}'\n")
                return 1
        except Exception as ex:
            sys.stderr.write(f"Error reading file '{target}': {str(ex)}\n")
            return 1
    else:
        # Treat as procedural shape name
        try:
            params = _parse_params_arg(getattr(args, "params", None))
            mesh = _resolve_shape(target, params)
        except ValueError:
            sys.stderr.write(f"Error: Target '{target}' is neither an existing file nor a recognized shape name.\n")
            return 1

    if mesh is None:
        sys.stderr.write("Error: Failed to construct mesh for audit.\n")
        return 1

    audit_res = SceneOptimizer.audit_mesh_budget(mesh)

    if getattr(args, "json", False):
        print(json.dumps(audit_res, indent=2))
        return 0

    # Print clean formatted ASCII report
    grade = audit_res.get("performance_grade", "A+")
    grade_color = _green if grade in ("A+", "A") else (_yellow if grade == "B" else _red)

    print("\n" + _bold(_cyan("═" * 60)))
    print(_bold(f"  Nexus 3D Mesh Audit Report: {_cyan(mesh.name)}"))
    print(_bold(_cyan("═" * 60)))
    print(f"  {_bold('Performance Grade:')}   {grade_color(_bold(f'[{grade}]'))}")
    print(f"  {_bold('Vertices:')}            {audit_res['vertex_count']:,}")
    print(f"  {_bold('Faces:')}               {audit_res['face_count']:,}")
    print(f"  {_bold('Triangles:')}           {audit_res['triangle_count']:,}")
    print(f"  {_bold('Edges:')}               {audit_res['edge_count']:,}")
    print(f"  {_bold('Estimated VRAM:')}      {audit_res['vram_bytes']:,} bytes ({audit_res['vram_bytes'] / 1024:.2f} KB)")
    print(f"  {_bold('Surface Area:')}        {audit_res['surface_area']:.4f}")
    print(f"  {_bold('Enclosed Volume:')}     {audit_res['volume']:.4f}")
    bb = audit_res['bounding_box']
    print(f"  {_bold('Bounding Box:')}        X:[{bb[0]:.2f}, {bb[1]:.2f}] Y:[{bb[2]:.2f}, {bb[3]:.2f}] Z:[{bb[4]:.2f}, {bb[5]:.2f}]")
    dim = audit_res['dimensions']
    print(f"  {_bold('Dimensions (dx,dy,dz):')} {dim[0]:.2f} x {dim[1]:.2f} x {dim[2]:.2f}")

    diags = audit_res.get("diagnostics", [])
    if diags:
        print(f"\n  {_bold('Recommendations & Diagnostics:')}")
        for d in diags:
            print(f"    • {d}")
    print(_bold(_cyan("═" * 60)) + "\n")

    return 0


def handle_mcp(args: argparse.Namespace) -> int:
    """Handle `mcp` subcommand."""
    if args.tools:
        server = MCPServer()
        print(json.dumps(server.list_tools(), indent=2))
        return 0

    if args.config:
        config = generate_mcp_client_config(client_name=args.config)
        print(json.dumps(config, indent=2))
        return 0

    # Start Stdio MCP JSON-RPC Server
    run_mcp_server()
    return 0


def handle_serve(args: argparse.Namespace) -> int:
    """Handle `serve` subcommand."""
    port = int(args.port)
    host = str(args.host)
    open_browser_flag = bool(args.open)

    httpd = start_ui_server(
        host=host,
        port=port,
        public_dir=getattr(args, "public", None),
        open_browser=open_browser_flag,
    )

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Nexus 3D Studio] Server stopped.")
        httpd.server_close()
    return 0


def handle_platform(args: argparse.Namespace) -> int:
    """Handle `platform` subcommand."""
    diag = get_system_diagnostics()

    if getattr(args, "json", False):
        print(json.dumps(diag, indent=2))
        return 0

    pinfo = diag["platform"]
    print("\n" + _bold(_cyan("═" * 60)))
    print(_bold("  Nexus 3D Scene Studio - Runtime Diagnostics"))
    print(_bold(_cyan("═" * 60)))
    print(f"  {_bold('OS Platform:')}          {pinfo['system']} {pinfo['release']} ({pinfo['architecture']})")
    print(f"  {_bold('Operating System:')}     {pinfo['os_name'].capitalize()} (64-bit: {pinfo['is_64bit']})")
    print(f"  {_bold('Python Version:')}       {pinfo['python_version']} ({diag['python_executable']})")
    print(f"  {_bold('CPU Cores:')}            {diag['cpu_count']}")
    if diag.get("total_ram_mb"):
        print(f"  {_bold('Total RAM:')}            {diag['total_ram_mb']:.1f} MB")
    if diag.get("disk_free_gb"):
        print(f"  {_bold('Free Disk Space:')}      {diag['disk_free_gb']:.2f} GB / {diag.get('disk_total_gb', 0):.2f} GB")
    print(f"  {_bold('Working Directory:')}    {diag['working_directory']}")
    print(f"  {_bold('Temp Directory:')}       {diag['temp_directory']}")
    print(f"  {_bold('Stdio Encoding:')}       stdout={diag['stdio_encoding']['stdout']}, stderr={diag['stdio_encoding']['stderr']}")
    print(f"  {_bold('Dependencies:')}         Zero external runtime dependencies (pure stdlib)")
    print(_bold(_cyan("═" * 60)) + "\n")
    return 0


def handle_test(args: argparse.Namespace) -> int:
    """Handle `test` / `--test` command running internal engine validation suite."""
    setup_utf8_console()
    print(_bold("Running Nexus 3D Scene Studio self-test suite..."))

    # Try running pytest if available in environment
    try:
        import pytest
        test_dir = str(pathlib.Path(__file__).resolve().parent.parent.parent / "tests")
        return pytest.main(["-v", test_dir])
    except ImportError:
        # Fallback to pure stdlib unittest discovery
        import unittest
        loader = unittest.TestLoader()
        test_dir = str(pathlib.Path(__file__).resolve().parent.parent.parent / "tests")
        suite = loader.discover(start_dir=test_dir, pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1


# ---------------------------------------------------------------------------
# CLI Argument Parser & Entry Point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="nexus-3d",
        description="Nexus 3D Scene Studio - Procedural 3D Geometry Studio, MCP Server, and WebGL Exporter.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{SERVER_NAME} {SERVER_VERSION}",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run internal unit test suite",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. generate
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate procedural 3D shapes (tesseract, torus_knot, superquadric, solid, terrain, mobius, fibonacci)",
    )
    gen_parser.add_argument(
        "shape",
        help="Shape name: tesseract, torus_knot, superquadric, solid, icosahedron, buckyball, terrain, mobius, fibonacci",
    )
    gen_parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output destination file path (e.g. model.obj, model.stl, model.html)",
    )
    gen_parser.add_argument(
        "-f", "--format",
        default="obj",
        choices=["obj", "stl", "json", "html"],
        help="Export format (default: obj)",
    )
    gen_parser.add_argument(
        "-p", "--params",
        default=None,
        help="Generator parameters as JSON string or key=val pairs (e.g. 'p=3,q=5' or '{\"p\": 3, \"q\": 5}')",
    )
    gen_parser.add_argument(
        "--theme",
        default="dark",
        choices=["dark", "light"],
        help="Visual theme for HTML exports (default: dark)",
    )

    # 2. audit
    audit_parser = subparsers.add_parser(
        "audit",
        help="Analyze 3D mesh polygon budget, memory size, bounding box, and WebGL grade",
    )
    audit_parser.add_argument(
        "target",
        help="File path to 3D mesh (.obj, .json) or recognized procedural shape name (e.g. torus_knot)",
    )
    audit_parser.add_argument(
        "-p", "--params",
        default=None,
        help="Shape generator parameters if auditing procedural shape",
    )
    audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Output audit result as JSON",
    )

    # 3. mcp
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Run Stdio Model Context Protocol (MCP) server or export client configurations",
    )
    mcp_parser.add_argument(
        "--tools",
        action="store_true",
        help="List available MCP tools in JSON format",
    )
    mcp_parser.add_argument(
        "--config",
        choices=["claude", "cursor", "cline", "zed", "generic"],
        default=None,
        help="Generate MCP client configuration snippet",
    )

    # 4. serve
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start Nexus 3D Studio Web UI server (design influenced by Material 3)",
    )
    serve_parser.add_argument(
        "-p", "--port",
        type=int,
        default=8092,
        help="HTTP port to listen on (default: 8092)",
    )
    serve_parser.add_argument(
        "-H", "--host",
        default="0.0.0.0",
        help="Host address to bind (default: 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--public",
        default=None,
        help="Custom public assets directory path",
    )
    serve_parser.add_argument(
        "--open",
        action="store_true",
        help="Open Web Studio in default browser upon launch",
    )

    # 5. platform
    platform_parser = subparsers.add_parser(
        "platform",
        help="Display cross-platform runtime and graphics diagnostics",
    )
    platform_parser.add_argument(
        "--json",
        action="store_true",
        help="Output diagnostics as JSON",
    )

    # 6. test
    test_parser = subparsers.add_parser(
        "test",
        help="Run internal test suite",
    )

    return parser


def main(args: Optional[Sequence[str]] = None) -> int:
    """Main CLI entry point."""
    setup_utf8_console()
    parser = build_parser()
    parsed = parser.parse_args(args)

    if parsed.test or parsed.command == "test":
        return handle_test(parsed)

    if parsed.command == "generate":
        return handle_generate(parsed)
    elif parsed.command == "audit":
        return handle_audit(parsed)
    elif parsed.command == "mcp":
        return handle_mcp(parsed)
    elif parsed.command == "serve":
        return handle_serve(parsed)
    elif parsed.command == "platform":
        return handle_platform(parsed)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
