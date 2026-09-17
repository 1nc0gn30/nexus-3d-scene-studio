# 🌟 Nexus 3D Scene Studio

<div align="center">

![Nexus 3D Header](https://img.shields.io/badge/Material%203-Studio%20UI-1a73e8?style=for-the-badge)
![Python 3.9+](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MCP Protocol](https://img.shields.io/badge/Model%20Context%20Protocol-MCP%20Ready-1e8e3e?style=for-the-badge)
![Zero Dependencies](https://img.shields.io/badge/Core%20Engine-100%25%20Stdlib-f9ab00?style=for-the-badge)
![License MIT](https://img.shields.io/badge/License-MIT-d93025?style=for-the-badge)

**A pure Python 3D mathematical geometry engine, WebGL Material 3 studio (design influenced by Material 3), and Model Context Protocol (MCP) server for generative 3D modeling and autonomous AI agents.**

[Live Studio Web UI](#-interactive-web-studio) • [Procedural Primitives](#-procedural-primitives-catalog) • [MCP Integration](#-ai-agent--mcp-server) • [Python API](#-python-api-quickstart) • [CLI Commands](#-cli-interface)

</div>

---

## 💎 Highlights & Capabilities

- 🎨 **Material 3 Light Mode Studio**: Interactive WebGL 3D canvas (design influenced by Material 3), system fonts, smooth OrbitControls, wireframe/solid shading, lighting rigs, and real-time geometry telemetry HUD.
- 🔮 **4D Hypercube (Tesseract) Engine**: Real-time 4D rotation matrices in $SO(4)$ Lie group projected into 3D space via stereographic projection.
- 🌀 **Parametric Space Curves & Surfaces**: Torus knots $(p, q)$ with Frenet-Serret tube framing, Superquadrics with taper/twist/bend deformations, Fibonacci golden spiral spherical lattices, Buckyballs (Fullerene C60), and Möbius ribbons.
- 🏔️ **Procedural Fractal Terrain**: Multi-octave Fractional Brownian Motion (fBm) elevation heightfields with analytical normal gradient calculations.
- 💾 **1-Click Multi-Format Exporters**: Wavefront `.obj` + `.mtl`, ASCII & Binary `.stl` (3D printing ready), `.ply`, Three.js BufferGeometry `.json`, and single-file standalone `.html` viewers.
- 🤖 **Model Context Protocol (MCP) Server**: Native stdio / JSON-RPC 2.0 interface for Claude Desktop, Cursor IDE, Cline, Zed, and autonomous AI coding agents.
- ⚡ **Pure Standard Library Core**: 100% Python standard library geometry computation without NumPy/SciPy dependency requirements.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 NEXUS 3D SCENE STUDIO                                  │
├──────────────────────────────┬──────────────────────────┬──────────────────────────────┤
│      🎨 Web Studio HUD       │   🤖 AI Agent / MCP Hub   │      💻 CLI Interface        │
│   (Material 3 Studio UI)     │  (FastMCP / JSON-RPC 2)  │    (`nexus3d` commands)      │
└──────────────┬───────────────┴────────────┬─────────────┴──────────────┬───────────────┘
               │                            │                            │
               ▼                            ▼                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             CORE MATHEMATICAL ENGINE                                   │
├──────────────────────────────┬──────────────────────────┬──────────────────────────────┤
│  🔮 4D Stereographic Proj    │  🌀 (p,q) Torus Knots    │  💎 Superquadrics + Deform   │
│  🌻 Fibonacci Spiral Lattice │  ⚽ Buckyball C60 Mesh   │  ♾️ Möbius Strip Ribbon      │
│  🏔️ Multi-Octave fBm Terrain │  📐 Platonic Solids      │  📊 Mesh Telemetry & VRAM    │
└──────────────────────────────┴────────────┬─────────────┴──────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              EXPORT & PACKAGING PIPELINE                               │
│     • Wavefront OBJ + MTL    • ASCII / Binary STL       • Three.js BufferGeometry JSON │
│     • Standalone HTML Viewer • PLY Point Cloud & Mesh   • GLTF 2.0 / GLB Layout        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Procedural Primitives Catalog

| Primitive | Mathematical Formula / Algorithm | Key Parameters |
| :--- | :--- | :--- |
| **4D Tesseract** | $\mathbf{p}_{3D} = \frac{s}{d - w} R_{yw}(\phi) R_{xw}(\theta) \mathbf{v}_{4D}$ | `scale`, `rotation_4d`, `distance` |
| **$(p, q)$ Torus Knot** | $r = \cos(qu) + 2$, $\mathbf{r} = (r\cos pu, r\sin pu, -\sin qu)$ with Frenet framing | `p`, `q`, `tube_radius`, `tubular_segments` |
| **Superquadric** | $\mathbf{S}(\eta, \omega) = (a_1 C(\eta, s_1)C(\omega, s_2), a_2 C(\eta, s_1)S(\omega, s_2), a_3 S(\eta, s_1))$ | `s1`, `s2`, `rx`, `ry`, `rz`, `taper`, `twist` |
| **Fibonacci Sphere** | $z_i = 1 - \frac{2i}{N-1}$, $\phi_i = i \cdot \pi(3-\sqrt{5})$, $r_i = \sqrt{1-z_i^2}$ | `num_points`, `radius` |
| **Buckyball C60** | Truncated regular icosahedron ($\chi = 60 - 90 + 32 = 2$) | `radius`, `truncation_factor` |
| **Möbius Strip** | $\mathbf{S}(u, v) = ((R + v\cos\frac{nu}{2})\cos u, (R + v\cos\frac{nu}{2})\sin u, v\sin\frac{nu}{2})$ | `radius`, `width`, `twists` |
| **Fractal Terrain** | $h(x, z) = \sum_{k=0}^{M-1} A \rho^k \mathcal{N}(f \lambda^k x, f \lambda^k z)$ | `grid_size`, `scale`, `octaves`, `height_scale` |

Detailed mathematical derivations and proofs are documented in [docs/PROCEDURAL_GEOMETRY_MATH.md](docs/PROCEDURAL_GEOMETRY_MATH.md).

---

## 🚀 Quickstart

### Installation
```bash
# Clone the repository
git clone https://github.com/nexus-3d/nexus-3d-scene-studio.git
cd nexus-3d-scene-studio

# Install in editable mode
pip install -e .
```

### Python API Quickstart
```python
from nexus_3d_scene_studio.geometry_engine import (
    generate_torus_knot,
    generate_tesseract_4d,
    generate_superquadric,
)
from nexus_3d_scene_studio.mesh_exporter import MeshExporter

# 1. Generate a Parametric (3, 7) Torus Knot
mesh = generate_torus_knot(p=3, q=7, tubular_segments=180, radial_segments=24)

# 2. Inspect Mesh Telemetry
print(f"Vertices: {mesh.vertex_count}")
print(f"Triangles: {mesh.triangle_count}")
print(f"Surface Area: {mesh.compute_surface_area():.3f}")

# 3. Export to Wavefront OBJ with Normals
MeshExporter.export_obj(mesh, "torus_knot_3_7.obj")

# 4. Export to 3D-Printing ASCII STL
MeshExporter.export_stl(mesh, "torus_knot_3_7.stl")

# 5. Export to Standalone Offline HTML 3D Viewer
MeshExporter.export_html_viewer(mesh, "torus_knot_viewer.html")
```

---

## 💻 CLI Interface

```bash
# Generate and export a 4D Hypercube Tesseract
nexus3d generate tesseract --rotation-4d 0.8 --export tesseract.obj

# Generate a Parametric Torus Knot
nexus3d generate torus-knot --p 3 --q 5 --tube-radius 0.4 --export knot.stl

# Launch the interactive Nexus 3D Studio Web UI
nexus3d serve --port 8080

# Inspect geometry telemetry of any OBJ file
nexus3d inspect knot.obj
```

---

## 🤖 AI Agent & MCP Server

Nexus 3D Scene Studio implements the **Model Context Protocol (MCP)**, allowing AI agents to generate, inspect, and export 3D scenes autonomously.

### Available MCP Tools:
1. `generate_mesh`: Generates any of the 7 procedural primitives with custom math parameters.
2. `export_scene`: Exports scenes to OBJ, MTL, STL, PLY, Three.js JSON, or Standalone HTML.
3. `transform_mesh`: Applies translation, rotation, scale, taper, twist, and bend deformations.
4. `inspect_geometry`: Returns live vertex counts, face counts, bounding box, surface area, and Euler characteristic.
5. `list_primitives`: Returns available primitives and parameter schema.

### Claude Desktop Integration
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "nexus3d": {
      "command": "python",
      "args": ["-m", "nexus_3d_scene_studio.mcp_server"],
      "env": { "PYTHONPATH": "src" }
    }
  }
}
```

Full setup guides for Cursor, Cline, and Zed are available in [docs/MCP_GUIDE.md](docs/MCP_GUIDE.md).

---

## 🧪 Testing

Run the comprehensive unit test suite:
```bash
PYTHONPATH=src pytest tests/ -v
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
