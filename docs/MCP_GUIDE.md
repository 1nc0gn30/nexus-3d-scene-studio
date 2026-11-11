# Nexus 3D Model Context Protocol (MCP) Integration Guide

This guide documents integrating **Nexus 3D Scene Studio** (`nexus_3d_scene_studio.mcp_server`) with MCP clients over JSON-RPC 2.0 `stdio` (`protocolVersion: 2024-11-05`).

## Overview

Launch the MCP server directly or generate a client snippet via the CLI:

```bash
nexus-3d mcp
nexus-3d mcp --tools
nexus-3d mcp --config claude
```

## Registered MCP Tools (12)

1. `nexus_generate_tesseract` — Stereographic projection of a 4D hypercube (`size`, `angle_4d`, `distance_4d`, `format`).
2. `nexus_generate_torus_knot` — Parametric `(p, q)` torus knot tubular mesh with normals and UVs.
3. `nexus_generate_superquadric` — Superquadric surface with exponents `s1`, `s2` and `pinch`, `taper`, `bend`, `twist` deformations.
4. `nexus_generate_solid` — Platonic solids (`tetrahedron`, `cube`, `octahedron`, `dodecahedron`, `icosahedron`) and `buckyball` (`c60`).
5. `nexus_generate_terrain` — Multi-octave coherent heightmap terrain mesh (`grid_size`, `scale`, `height_factor`, `octaves`).
6. `nexus_export_mesh` — Export procedural or raw mesh geometry to `obj`, `stl`, `json` (Three.js), `html`, `gltf`, or `ply`.
7. `nexus_audit_mesh` — Compute polygon budget, bounding box, surface area, estimated VRAM bytes, and WebGL performance grade.
8. `nexus_get_diagnostics` — Return platform, Python runtime, and MCP server diagnostics.
9. `nexus_generate_fractal` — Strange attractors (`lorenz`, `rossler`, `aizawa`, `chen`), `klein_bottle`, and `menger_sponge`.
10. `nexus_generate_lod_pyramid` — Multi-tier edge-decimated Level-of-Detail (LOD) pyramid with distance switch thresholds.
11. `nexus_generate_sdf_isosurface` — Marching Tetrahedra polygonization of volumetric SDF/TPMS presets (`gyroid`, `schwarz_p`, `neovius`, `mandelbulb`, `smooth_csg`, `metaballs`, `twisted_torus`).
12. `nexus_evaluate_csg_boolean` — Analytic CSG boolean evaluation (`union`, `difference`, `intersection`, `smooth_union`, `smooth_difference`, `smooth_intersection`) polygonized via Marching Tetrahedra.

## JSON-RPC 2.0 Example

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "nexus_generate_torus_knot",
    "arguments": {
      "p": 3,
      "q": 5,
      "major_radius": 2.0,
      "tube_radius": 0.4,
      "format": "obj"
    }
  }
}
```

## Client Configuration

Generate ready-to-paste configurations for Claude Desktop, Cursor, Cline, or Zed:

```bash
nexus-3d mcp --config cursor
```

```json
{
  "mcpServers": {
    "nexus-3d-scene-studio": {
      "command": "python3",
      "args": ["-m", "nexus_3d_scene_studio.mcp_server"]
    }
  }
}
```
