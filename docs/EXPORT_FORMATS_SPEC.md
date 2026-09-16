# 3D Mesh Export Formats Specification

This document details the file format specifications, data layouts, schemas, and coordinate system conventions supported by **Nexus 3D Scene Studio** exporters.

---

## 1. Supported Formats Overview

| Format | Extension | Type | Normals | UVs | Colors | 3D Printing Ready |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Wavefront OBJ** | `.obj` | Text / ASCII | ✅ | ✅ | ❌ | ✅ |
| **Material Template Library** | `.mtl` | Text / ASCII | N/A | N/A | ✅ (Kd/Ks) | N/A |
| **Stereolithography (ASCII)** | `.stl` | Text / ASCII | ✅ (Facet) | ❌ | ❌ | ✅ (Industry Std) |
| **Stereolithography (Binary)** | `.stl` | Binary (Little Endian) | ✅ (Facet) | ❌ | ❌ | ✅ |
| **Polygon File Format** | `.ply` | ASCII / Binary | ✅ | ✅ | ✅ (RGBA) | ✅ |
| **Three.js BufferGeometry** | `.json` | JSON Schema v4 | ✅ | ✅ | ✅ | ❌ (Web Only) |
| **Standalone HTML Viewer** | `.html` | Single-File Bundle | ✅ | ✅ | ✅ | ❌ (Interactive) |

---

## 2. Wavefront OBJ & MTL Specification

### 2.1 Coordinate System
- Right-handed coordinate system ($+X$ right, $+Y$ up, $+Z$ forward towards viewer).
- Floating-point vertex coordinates formatted to 6 decimal places.
- 1-based indexing for vertices, texture coordinates, and normals.

### 2.2 OBJ Syntax Example
```obj
# Nexus 3D Scene Studio - Wavefront OBJ Exporter v1.0.0
# Mesh Name: Parametric_Torus_Knot_p3_q5
# Vertices: 1920 | Faces: 1920 | Triangles: 3840
mtllib scene_material.mtl
o TorusKnot_p3_q5

# Vertices (v x y z)
v 1.250000 0.000000 0.850000
v 1.221532 0.124501 0.842011

# Vertex Normals (vn nx ny nz)
vn 0.854210 0.125489 0.504218
vn 0.841029 0.201452 0.501230

# Smoothing group & Material
usemtl Material_GoogleBlue
s 1

# Face definitions (f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3 ...)
f 1//1 2//2 3//3 4//4
```

### 2.3 Companion MTL Syntax
```mtl
# Material Template Library
newmtl Material_GoogleBlue
Ka 0.100000 0.100000 0.100000
Kd 0.101961 0.450980 0.909804
Ks 0.500000 0.500000 0.500000
Ns 64.000000
d 1.000000
illum 2
```

---

## 3. STL (Stereolithography) Format

### 3.1 ASCII STL Format
ASCII STL represents triangular facets with outward-pointing surface normal vectors:

```stl
solid TorusKnot_p3_q5
  facet normal 8.542100e-01 1.254890e-01 5.042180e-01
    outer loop
      vertex 1.250000e+00 0.000000e+00 8.500000e-01
      vertex 1.221532e+00 1.245010e-01 8.420110e-01
      vertex 1.189021e+00 2.450120e-01 8.120540e-01
    endloop
  endfacet
endsolid TorusKnot_p3_q5
```

### 3.2 Binary STL Format (Little-Endian)
- **Header**: 80-byte ASCII description string.
- **Triangle Count**: 4-byte unsigned 32-bit integer (`uint32`).
- **Facet Records**: $N \times 50$ bytes where each facet contains:
  * 3 $\times$ `float32` (12 bytes) — Facet Normal $(n_x, n_y, n_z)$
  * 3 $\times$ `float32` (12 bytes) — Vertex 1 $(v_{1x}, v_{1y}, v_{1z})$
  * 3 $\times$ `float32` (12 bytes) — Vertex 2 $(v_{2x}, v_{2y}, v_{2z})$
  * 3 $\times$ `float32` (12 bytes) — Vertex 3 $(v_{3x}, v_{3y}, v_{3z})$
  * 1 $\times$ `uint16` (2 bytes) — Attribute byte count (usually $0$).

---

## 4. Three.js JSON Geometry Schema

Nexus 3D exports modern `BufferGeometry` Object JSON:

```json
{
  "metadata": {
    "version": 4.5,
    "type": "BufferGeometry",
    "generator": "Nexus3DSceneStudio"
  },
  "uuid": "4c9e8a71-6789-4d2b-9e12-890abcdef012",
  "type": "BufferGeometry",
  "data": {
    "attributes": {
      "position": {
        "itemSize": 3,
        "type": "Float32Array",
        "array": [1.25, 0.0, 0.85, 1.22, 0.12, 0.84],
        "normalized": false
      },
      "normal": {
        "itemSize": 3,
        "type": "Float32Array",
        "array": [0.85, 0.12, 0.50, 0.84, 0.20, 0.50],
        "normalized": false
      }
    },
    "index": {
      "type": "Uint32Array",
      "array": [0, 1, 2, 0, 2, 3]
    },
    "boundingSphere": {
      "center": [0, 0, 0],
      "radius": 2.85
    }
  }
}
```

---

## 5. Standalone Self-Contained HTML Viewer Bundle

When exporting to `.html`, the engine embeds:
1. **Inlined Mesh Buffers**: Flat Float32 vertex and normal arrays.
2. **WebGL Rendering Pipeline**: Pure WebGL 2.0 / Three.js lightweight canvas.
3. **Google Material 3 Responsive HUD**: Orbit controls, camera presets, wireframe/solid toggle, performance metrics.
4. **Zero Network Requirement**: Works 100% offline with zero dependencies.
