# Nexus 3D Model Context Protocol (MCP) Integration Guide

This guide details how to integrate **Nexus 3D Scene Studio** with LLM agents (Claude Desktop, Cursor IDE, Cline, Zed, and custom autonomous agents) via the standard **Model Context Protocol (MCP)** over STDIO or JSON-RPC.

---

## 1. Overview & Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 AI Agent / LLM Host                         │
│   (Claude Desktop / Cursor / Cline / Zed / AutoGen / LangChain)│
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON-RPC 2.0 over STDIO
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Nexus 3D MCP Server (Python FastMCP)            │
│              `nexus_3d_scene_studio.mcp_server`             │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
       ┌───────▼────────┐             ┌───────▼────────┐
       │ GeometryEngine │             │  MeshExporter  │
       │ (7 Primitives) │             │(OBJ/STL/HTML/..)│
       └────────────────┘             └────────────────┘
```

---

## 2. MCP Tools Reference

### Tool 1: `generate_mesh`
Generates procedural 3D geometric meshes with mathematical parameter tuning.

#### Parameters:
- `primitive` (string, required): One of `"tesseract"`, `"torus_knot"`, `"superquadric"`, `"fibonacci_sphere"`, `"buckyball"`, `"mobius_strip"`, `"terrain"`.
- `params` (object, optional): Key-value parameters:
  * For `"tesseract"`: `scale` (float), `rotation_4d` (float), `distance` (float).
  * For `"torus_knot"`: `p` (int), `q` (int), `tube_radius` (float), `tubular_segments` (int), `radial_segments` (int).
  * For `"superquadric"`: `s1` (float), `s2` (float), `rx` (float), `ry` (float), `rz` (float).
  * For `"fibonacci_sphere"`: `num_points` (int), `radius` (float).
  * For `"buckyball"`: `radius` (float).
  * For `"mobius_strip"`: `radius` (float), `width` (float), `twists` (int).
  * For `"terrain"`: `grid_size` (int), `scale` (float), `height_scale` (float), `octaves` (int).

#### JSON-RPC Example:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "generate_mesh",
    "arguments": {
      "primitive": "torus_knot",
      "params": {
        "p": 3,
        "q": 7,
        "tube_radius": 0.35,
        "tubular_segments": 160
      }
    }
  }
}
```

---

### Tool 2: `export_scene`
Exports the current mesh or scene to a disk file.

#### Parameters:
- `mesh_id` (string, optional): Name or ID of the mesh to export.
- `format` (string, required): `"obj"`, `"stl_ascii"`, `"stl_binary"`, `"ply"`, `"threejs_json"`, `"html_viewer"`.
- `output_path` (string, required): Destination filepath.

#### JSON-RPC Example:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "export_scene",
    "arguments": {
      "format": "obj",
      "output_path": "./models/my_torus_knot.obj"
    }
  }
}
```

---

### Tool 3: `inspect_geometry`
Retrieves live geometric telemetry, topology invariants, bounding box dimensions, and surface area calculations.

#### JSON-RPC Response Example:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "primitive": "torus_knot",
    "vertex_count": 1920,
    "face_count": 1920,
    "triangle_count": 3840,
    "bounding_box": {
      "min": [-2.45, -2.45, -1.35],
      "max": [2.45, 2.45, 1.35],
      "dimensions": [4.9, 4.9, 2.7]
    },
    "surface_area": 154.596,
    "genus": 1,
    "euler_characteristic": 0,
    "coprime_check": {
      "p": 3,
      "q": 7,
      "gcd": 1,
      "is_valid_single_knot": true
    }
  }
}
```

---

### Tool 4: `transform_mesh`
Applies affine transformations (translation, rotation, scale) or non-linear deformations (taper, twist, bend) to a mesh.

---

### Tool 5: `list_primitives`
Lists all available procedural shapes, valid parameter ranges, default values, and mathematical descriptions.

---

## 3. Client Installation Guides

### Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "nexus3d": {
      "command": "python",
      "args": ["-m", "nexus_3d_scene_studio.mcp_server"],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

### Cursor IDE
Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "nexus-3d-scene-studio": {
      "command": "python",
      "args": ["-m", "nexus_3d_scene_studio.mcp_server"],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

---

## 4. Agentic Prompting Examples

Here are effective system prompt instructions for autonomous agents using Nexus 3D:

> **Agent Prompt:**
> "You have access to the `nexus3d` tool suite. When asked to create 3D assets:
> 1. Use `nexus3d.list_primitives` to inspect mathematical shape options.
> 2. Call `nexus3d.generate_mesh` with customized parameters.
> 3. Verify mesh topology using `nexus3d.inspect_geometry` to ensure triangle count and bounding box meet constraints.
> 4. Export the finalized asset using `nexus3d.export_scene` to `.obj` or standalone `.html` viewer."
