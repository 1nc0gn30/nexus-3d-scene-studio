# Nexus 3D Scene Studio - Production Reference Examples

Welcome to the examples hub for **Nexus 3D Scene Studio**. This directory contains end-to-end production examples, standalone interactive 3D viewers, procedural shape galleries, and AI agent Model Context Protocol (MCP) integrations.

---

## 📁 Directory Structure

```
examples/
├── procedural-shapes/       # 7 Procedural shape generators & sample OBJ/STL models
│   ├── generate_gallery.py  # Standalone gallery generation script
│   ├── *.obj, *.stl         # Pre-generated 3D meshes ready for Blender / Three.js
│   └── README.md            # Catalog & parameters guide
├── standalone-viewers/      # Zero-dependency, offline-ready single-file 3D viewers
│   ├── tesseract_viewer.html# 4D Hypercube Tesseract interactive viewer
│   ├── torus_knot_viewer.html # Parametric Torus Knot interactive viewer
│   └── README.md            # Embedding and standalone usage guide
├── mcp-clients/             # Model Context Protocol (MCP) configs for AI agents
│   ├── claude_desktop_config.json # Claude Desktop configuration snippet
│   ├── cursor_mcp.json      # Cursor IDE configuration
│   ├── cline_mcp.json       # Cline (VSCode) configuration
│   ├── zed_settings.json    # Zed Editor context server settings
│   └── README.md            # MCP client setup walkthrough
└── README.md                # This file
```

---

## ⚡ Quick Navigation

### 1. [Procedural Shapes Gallery](./procedural-shapes/)
Generates and demonstrates 7 mathematical 3D meshes:
- **4D Hypercube Tesseract**: 4D-to-3D stereographic rotation projection
- **Parametric $(p, q)$ Torus Knot**: Swept tube with Frenet frame
- **Superquadric Ellipsoid**: Generalized trigonometric surfaces
- **Fibonacci Golden Spiral Sphere**: Optimal spherical point distribution
- **Buckyball C60**: Truncated icosahedron molecular mesh
- **Möbius Strip Ribbon**: Parametric surface with half-twist topology
- **Procedural Fractal Terrain**: Multi-octave fBm heightmap elevation grid

Run the generator:
```bash
python examples/procedural-shapes/generate_gallery.py
```

### 2. [Standalone 3D Viewers](./standalone-viewers/)
Self-contained HTML5 / WebGL viewers styled with Material 3 (design influenced by Material 3).
- No node build step, no web server required.
- Double click to launch in your browser.

### 3. [MCP AI Agent Clients](./mcp-clients/)
Connect Claude Desktop, Cursor, Cline, or Zed directly to the Nexus 3D engine to allow AI models to generate, inspect, and export 3D scenes autonomously.
