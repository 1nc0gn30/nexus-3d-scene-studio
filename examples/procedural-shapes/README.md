# Procedural Shapes Gallery

This directory contains reference implementations and pre-generated 3D models for the 7 mathematical procedural shapes supported by **Nexus 3D Scene Studio**.

---

## 📐 Gallery Shape Catalog

| Identifier | Shape Name | Math Formula / Geometry Technique | Vertices | Faces | Triangles | Files |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `tesseract_4d` | **4D Hypercube Tesseract** | 4D Euler rotation ($XW, YW$) + Stereographic perspective projection $\mathbf{p}_{3D} = \frac{\mathbf{p}_{4D}}{d - w}$ | 16 | 24 | 48 | [`tesseract_4d.obj`](./tesseract_4d.obj)<br>[`tesseract_4d.stl`](./tesseract_4d.stl) |
| `torus_knot` | **Parametric $(p, q)$ Torus Knot** | Helical space curve $r = \cos(qu) + 2$ with Frenet-Serret tube extrusion | 1,920 | 1,920 | 3,840 | [`torus_knot.obj`](./torus_knot.obj)<br>[`torus_knot.stl`](./torus_knot.stl) |
| `superquadric` | **Superquadric Ellipsoid** | Signed trigonometric powers $C(\theta, s) = \text{sgn}(\cos\theta)\|\cos\theta\|^s$ with $s_1=0.5, s_2=0.5$ | 1,056 | 1,024 | 2,048 | [`superquadric.obj`](./superquadric.obj)<br>[`superquadric.stl`](./superquadric.stl) |
| `fibonacci_sphere` | **Fibonacci Spiral Lattice** | Golden angle $\theta = \pi(3-\sqrt{5}) \approx 137.5^\circ$ spherical distribution | 250 | 250 | 500 | [`fibonacci_sphere.obj`](./fibonacci_sphere.obj)<br>[`fibonacci_sphere.stl`](./fibonacci_sphere.stl) |
| `buckyball` | **Buckyball (Fullerene C60)** | Truncated icosahedron with 12 pentagonal + 20 hexagonal faces | 60 | 32 | 116 | [`buckyball.obj`](./buckyball.obj)<br>[`buckyball.stl`](./buckyball.stl) |
| `mobius_strip` | **Möbius Strip Ribbon** | Non-orientable surface with parametric half-twist: $z = v \sin(u/2)$ | 540 | 480 | 960 | [`mobius_strip.obj`](./mobius_strip.obj)<br>[`mobius_strip.stl`](./mobius_strip.stl) |
| `terrain_heightmap` | **Fractal Terrain** | Multi-octave fractional Brownian Motion (fBm) elevation field | 1,024 | 1,922 | 1,922 | [`terrain_heightmap.obj`](./terrain_heightmap.obj)<br>[`terrain_heightmap.stl`](./terrain_heightmap.stl) |

---

## 🚀 Running the Gallery Generator

You can regenerate all sample files or export to a custom directory using the Python script:

```bash
# Generate all shapes into current directory
python generate_gallery.py

# Export into a custom directory
python generate_gallery.py --output-dir ./output
```

### Programmatic Python Usage

```python
from nexus_3d_scene_studio.geometry_engine import (
    generate_tesseract_4d,
    generate_torus_knot,
    generate_superquadric,
    generate_fibonacci_lattice,
    generate_buckyball,
    generate_mobius_strip,
    generate_procedural_terrain,
)
from nexus_3d_scene_studio.mesh_exporter import MeshExporter

# Generate a (3, 5) Torus Knot
mesh = generate_torus_knot(p=3, q=5, tubular_segments=160, radial_segments=24)

# Export to OBJ with Normals
MeshExporter.export_obj(mesh, "my_torus_knot.obj")

# Export to ASCII or Binary STL for 3D Printing
MeshExporter.export_stl(mesh, "my_torus_knot.stl")
```

---

## 🛠️ Inspecting Generated Meshes

All generated `.obj` and `.stl` files are 100% compliant with standard 3D software:
- **Blender**: `File -> Import -> Wavefront (.obj)` or `STL (.stl)`
- **Three.js**: `OBJLoader` or `STLLoader`
- **MeshLab / FreeCAD**: Open directly
- **PrusaSlicer / Cura**: Ready for additive manufacturing (3D printing)
