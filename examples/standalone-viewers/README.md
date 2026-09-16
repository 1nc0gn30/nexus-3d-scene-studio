# Standalone 3D HTML Viewers

This directory contains lightweight, zero-dependency, self-contained single-file HTML 3D viewers.

Each viewer provides an interactive WebGL 3D canvas styled with **Google Material 3**, real-time mathematical parameter sliders, live geometry telemetry, and 1-click Wavefront OBJ exporter.

---

## 📂 Viewer Catalog

| File | Shape / Demonstration | Key Features & Controls |
| :--- | :--- | :--- |
| [`tesseract_viewer.html`](./tesseract_viewer.html) | **🔮 4D Hypercube Tesseract** | Real-time 4D stereographic projection $\mathbb{R}^4 \to \mathbb{R}^3$, 4D rotation speed slider, projection distance $d$ slider, node spheres toggle, solid + wireframe hybrid shading. |
| [`torus_knot_viewer.html`](./torus_knot_viewer.html) | **🌀 Parametric $(p, q)$ Torus Knot** | Live $p$ and $q$ winding sliders, tube radius, tubular segment resolution, Normal RGB shader, Coprime GCD check, VRAM buffer telemetry. |

---

## 🌟 Architecture & Key Features

- **Google Material 3 Light Mode UI**: Styled with clean Google Blue (`#1a73e8`), emerald green (`#1e8e3e`), amber (`#f9ab00`), and Google 4-dots branding.
- **Pure Client-Side Execution**: Zero backend or Node server required. Double-click to open in any web browser (Chrome, Firefox, Safari, Edge).
- **Responsive Orbit & Touch Controls**: Mouse drag to orbit, scroll to zoom, right-click to pan. Full touch support for mobile and tablets.
- **Export On Demand**: Export the currently viewed parameter configuration directly to `.obj` with 1 click.
- **Offline Ready**: Uses system fonts and standard WebGL context.

---

## 🚀 How to Run or Embed

### 1. Direct Browser Opening
Simply double-click either HTML file in your file explorer, or launch via Python's built-in HTTP server:

```bash
python -m http.server 8000 --directory examples/standalone-viewers
# Open http://localhost:8000/tesseract_viewer.html
```

### 2. IFrame Embedding in Web Apps or Documentation
Embed seamlessly into docs, blogs, or dashboards:

```html
<iframe
  src="./tesseract_viewer.html"
  width="100%"
  height="600px"
  style="border: 1px solid #dadce0; border-radius: 16px;"
></iframe>
```

### 3. Programmatic Generation via Nexus 3D CLI

You can generate custom standalone HTML viewers for any mesh via Python:

```python
from nexus_3d_scene_studio.geometry_engine import generate_superquadric
from nexus_3d_scene_studio.mesh_exporter import MeshExporter

mesh = generate_superquadric(s1=0.3, s2=0.3)
MeshExporter.export_html_viewer(mesh, "superquadric_viewer.html")
```
