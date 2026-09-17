"""Nexus 3D Scene Studio - Mathematical Geometry Engine, MCP Server & Scene Optimizer.

Pure Python stdlib 3D graphics studio, parametric geometry engine, Model Context Protocol
(MCP) server, and WebGL scene exporter with zero external runtime dependencies.
"""

from .compat import (
    PlatformInfo,
    atomic_write_bytes,
    atomic_write_text,
    ensure_utf8,
    get_platform_info,
    get_system_diagnostics,
    is_linux,
    is_macos,
    is_termux,
    is_windows,
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
from .procedural_fractals import (
    decimate_mesh,
    generate_klein_bottle,
    generate_lod_pyramid,
    generate_menger_sponge,
    generate_strange_attractor,
)
from .mesh_exporter import MeshExporter
from .scene_optimizer import SceneOptimizer
from .mcp_server import (
    MCPServer,
    MCPTool,
    MCP_PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    generate_mcp_client_config,
    run_mcp_server,
)
from .cli import build_parser, main
from .ui_server import NexusStudioRequestHandler, get_default_presets, start_ui_server

__version__ = "1.0.0"

__all__ = [
    "PlatformInfo",
    "is_linux",
    "is_macos",
    "is_windows",
    "is_termux",
    "get_platform_info",
    "setup_utf8_console",
    "ensure_utf8",
    "atomic_write_text",
    "atomic_write_bytes",
    "to_posix_path",
    "normalize_path",
    "open_in_browser",
    "get_system_diagnostics",
    "MeshData",
    "ensure_mesh_data",
    "generate_tesseract_4d",
    "generate_fibonacci_lattice",
    "generate_torus_knot",
    "generate_superquadric",
    "generate_mobius_strip",
    "generate_solid",
    "generate_platonic_solid",
    "generate_buckyball",
    "generate_procedural_terrain",
    "generate_strange_attractor",
    "generate_klein_bottle",
    "generate_menger_sponge",
    "decimate_mesh",
    "generate_lod_pyramid",
    "MeshExporter",
    "SceneOptimizer",
    "MCPServer",
    "MCPTool",
    "MCP_PROTOCOL_VERSION",
    "SERVER_NAME",
    "SERVER_VERSION",
    "generate_mcp_client_config",
    "run_mcp_server",
    "main",
    "build_parser",
    "NexusStudioRequestHandler",
    "get_default_presets",
    "start_ui_server",
]
