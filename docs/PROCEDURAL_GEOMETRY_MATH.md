# Procedural Geometry Mathematics & Algorithm Specification

This document provides a formal mathematical specification of all procedural primitives, 4D-to-3D projection algorithms, space curves, superquadric deformation transforms, and fractal heightfield synthesis engines implemented in **Nexus 3D Scene Studio**.

---

## Table of Contents
1. [4D Hypercube (Tesseract) Projection](#1-4d-hypercube-tesseract-projection)
2. [Parametric $(p, q)$ Torus Knot & Frenet Framing](#2-parametric-p-q-torus-knot--frenet-framing)
3. [Superquadrics & Non-Linear Deformations](#3-superquadrics--non-linear-deformations)
4. [Fibonacci Golden Spiral Spherical Lattice](#4-fibonacci-golden-spiral-spherical-lattice)
5. [Buckyball (Truncated Icosahedron / Fullerene C60)](#5-buckyball-truncated-icosahedron--fullerene-c60)
6. [Möbius Strip & Non-Orientable Topologies](#6-möbius-strip--non-orientable-topologies)
7. [Procedural Fractal Terrain (fBm Heightmap)](#7-procedural-fractal-terrain-fbm-heightmap)
8. [Summary Complexity Matrix](#8-summary-complexity-matrix)

---

## 1. 4D Hypercube (Tesseract) Projection

### 1.1 Mathematical Definition
A standard 4-dimensional hypercube (tesseract) in Euclidean space $\mathbb{R}^4$ is defined as the convex hull of the 16 vertices:

$$V_{4D} = \left\{ (\pm 1, \pm 1, \pm 1, \pm 1) \right\} \subset \mathbb{R}^4$$

It possesses:
- **16 Vertices**
- **32 Edges** (connecting vertices with Hamming distance $d_H(v_i, v_j) = 1$)
- **24 2-Faces (Squares)**
- **8 3-Cells (Cubes)**

### 1.2 4D SO(4) Rotation Matrices
Rigid rotations in $\mathbb{R}^4$ are members of the Lie group $\mathrm{SO}(4)$. The group has 6 independent principal planes of rotation: $XY, XZ, YZ, XW, YW, ZW$.

For rotation in the $XW$ plane by angle $\theta_{xw}$ and $YW$ plane by angle $\theta_{yw}$:

$$R_{xw}(\theta) = \begin{pmatrix} \cos\theta & 0 & 0 & -\sin\theta \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 1 & 0 \\ \sin\theta & 0 & 0 & \cos\theta \end{pmatrix}, \quad R_{yw}(\phi) = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 0 & \cos\phi & 0 & -\sin\phi \\ 0 & 0 & 1 & 0 \\ 0 & \sin\phi & 0 & \cos\phi \end{pmatrix}$$

The rotated coordinate vector $\mathbf{v}' = (x', y', z', w')^T$ is obtained by:

$$\mathbf{v}' = R_{yw}(\phi) \cdot R_{xw}(\theta) \cdot \mathbf{v}$$

### 1.3 Stereographic $\mathbb{R}^4 \to \mathbb{R}^3$ Projection
To project the 4D object onto a 3D viewing hyperplane at projection focal distance $d > \max(w')$:

$$\mathbf{p}_{3D} = \begin{pmatrix} x_{3D} \\ y_{3D} \\ z_{3D} \end{pmatrix} = \frac{s}{d - w'} \begin{pmatrix} x' \\ y' \\ z' \end{pmatrix}$$

where $s$ is a global scaling factor.

---

## 2. Parametric $(p, q)$ Torus Knot & Frenet Framing

### 2.1 Space Curve Parametrization
A $(p, q)$ torus knot lies on the surface of a standard torus in $\mathbb{R}^3$ and winds $p$ times around the rotational axis of the torus while passing $q$ times through the hole inside the torus.

The core space curve $\mathbf{r}(u)$ for $u \in [0, 2\pi)$ is defined by:

$$\begin{aligned}
r(u) &= \cos(q u) + R_0 \\
x(u) &= r(u) \cos(p u) \\
y(u) &= r(u) \sin(p u) \\
z(u) &= -\sin(q u)
\end{aligned}$$

where $R_0 \ge 2.0$ ensures the curve remains self-avoiding.

> **Theorem (Knot Topology):** The curve forms a single continuous closed non-self-intersecting knot if and only if $p$ and $q$ are **coprime**:
> $$\gcd(p, q) = 1$$
> If $\gcd(p, q) = k > 1$, the curve decomposes into a $k$-component link.

### 2.2 Frenet-Serret Tube Extrusion
To sweep a solid tubular surface of radius $r_{\text{tube}}$ along the trajectory $\mathbf{r}(u)$, we establish the local orthonormal Frenet-Serret frame:

$$\mathbf{T}(u) = \frac{\mathbf{r}'(u)}{\|\mathbf{r}'(u)\|}, \quad \mathbf{N}(u) = \frac{\mathbf{T}'(u)}{\|\mathbf{T}'(u)\|}, \quad \mathbf{B}(u) = \mathbf{T}(u) \times \mathbf{N}(u)$$

The tubular boundary surface $\mathbf{S}(u, v)$ for $v \in [0, 2\pi)$ is given by:

$$\mathbf{S}(u, v) = \mathbf{r}(u) + r_{\text{tube}} \Big( \cos v \cdot \mathbf{N}(u) + \sin v \cdot \mathbf{B}(u) \Big)$$

---

## 3. Superquadrics & Non-Linear Deformations

### 3.1 Parametric Surface Definition
Superquadrics (Barr, 1981) generalize quadric surfaces using signed exponential powers of trigonometric functions:

$$C(\theta, \epsilon) = \operatorname{sgn}(\cos\theta) |\cos\theta|^\epsilon, \quad S(\theta, \epsilon) = \operatorname{sgn}(\sin\theta) |\sin\theta|^\epsilon$$

The parametric superellipsoid $\mathbf{S}(\eta, \omega)$ for latitude $\eta \in [-\pi/2, \pi/2]$ and longitude $\omega \in [-\pi, \pi)$ is:

$$\mathbf{S}(\eta, \omega) = \begin{pmatrix} a_1 C(\eta, s_1) C(\omega, s_2) \\ a_2 C(\eta, s_1) S(\omega, s_2) \\ a_3 S(\eta, s_1) \end{pmatrix}$$

- $s_1 \to 0, s_2 \to 0$: Square block / cuboid
- $s_1 = 1, s_2 = 1$: Standard sphere / ellipsoid
- $s_1 = 2, s_2 = 2$: Octahedron / bipyramid
- $s_1 < 1, s_2 = 1$: Rounded cylinder

### 3.2 Non-Linear Global Deformations
1. **Tapering along Z-axis:**
   $$f(z) = \frac{k_t}{a_3} z + 1, \quad X = f(z) x, \quad Y = f(z) y, \quad Z = z$$
2. **Twisting along Z-axis:**
   $$\theta = k_w z, \quad X = x \cos\theta - y \sin\theta, \quad Y = x \sin\theta + y \cos\theta, \quad Z = z$$
3. **Bending along Y-axis:**
   With radius of curvature $R$ and bending angle $\gamma = k_b y$:
   $$X = x, \quad Y = -\left(R - z\right) \sin\gamma, \quad Z = \left(R - z\right) \cos\gamma - R$$

---

## 4. Fibonacci Golden Spiral Spherical Lattice

### 4.1 Golden Spiral Formulation
To distribute $N$ points quasi-uniformly on a unit sphere $S^2 \subset \mathbb{R}^3$ without polar clustering, we use the golden angle:

$$\theta_g = \pi \left(3 - \sqrt{5}\right) \approx 2.399963229728653 \text{ rad } \left(\approx 137.507764^\circ\right)$$

For each sample index $i \in \{0, 1, \dots, N-1\}$:

$$\begin{aligned}
z_i &= 1 - \frac{2i}{N - 1} \\
r_i &= \sqrt{\max(0, 1 - z_i^2)} \\
\phi_i &= i \cdot \theta_g \\
x_i &= r_i \cos\phi_i \\
y_i &= r_i \sin\phi_i
\end{aligned}$$

$$\mathbf{p}_i = R \cdot (x_i, z_i, y_i)^T$$

### 4.2 Triangulation & Delaunay Dual
The point set is connected into a manifold mesh by constructing the spherical Delaunay triangulation or nearest-neighbor Voronoi dual graph, ensuring optimal area preservation across all latitude bands.

---

## 5. Buckyball (Truncated Icosahedron / Fullerene C60)

### 5.1 Regular Icosahedron Generator
Let $\phi = \frac{1 + \sqrt{5}}{2} \approx 1.6180339887$ be the golden ratio. The 12 vertices of a regular icosahedron are given by all cyclic permutations of:

$$(0, \pm 1, \pm \phi)$$

### 5.2 Edge Truncation Algorithm
Every vertex of the icosahedron meets 5 triangular faces. Truncating each of the 12 vertices at distance $t = 1/3$ along each of the 5 connected edges produces:
- **60 Vertices**
- **32 Total Faces**: 12 regular pentagons and 20 regular hexagons
- **90 Edges**

### 5.3 Topological Invariants
Euler characteristic calculation:

$$\chi = V - E + F = 60 - 90 + 32 = 2$$

Since $\chi = 2(1 - g)$, the genus $g = 0$ confirms topological equivalence to the 2-sphere $S^2$.

---

## 6. Möbius Strip & Non-Orientable Topologies

### 6.1 Parametric Equation
A Möbius strip with radius $R$, width $w$, and $n$ half-twists ($n=1$ for standard single-sided Möbius band) is parametrized by $u \in [0, 2\pi)$ and $v \in [-w/2, w/2]$:

$$\begin{aligned}
x(u, v) &= \left(R + v \cos\frac{n u}{2}\right) \cos u \\
y(u, v) &= \left(R + v \cos\frac{n u}{2}\right) \sin u \\
z(u, v) &= v \sin\frac{n u}{2}
\end{aligned}$$

### 6.2 Topological Properties
- **Non-Orientability**: Travelling once around the loop ($u \to u + 2\pi$) flips the normal orientation: $\mathbf{n}(u + 2\pi, v) = -\mathbf{n}(u, v)$.
- **Single Continuous Boundary**: The boundary curve is a single knot of length $\approx 4\pi R$.

---

## 7. Procedural Fractal Terrain (fBm Heightmap)

### 7.1 Fractional Brownian Motion (fBm)
Terrain elevation $h(x, z)$ is modeled as a 2D multi-octave spectral summation of pseudo-random basis functions:

$$h(x, z) = \sum_{k=0}^{M-1} A_0 \cdot \rho^k \cdot \mathcal{N}\left(f_0 \cdot \lambda^k x, \; f_0 \cdot \lambda^k z\right)$$

where:
- $M$: Number of octaves (typically $4 \le M \le 8$)
- $\rho \in (0, 1)$: Persistence (gain per octave, default $\rho = 0.5$)
- $\lambda \ge 2.0$: Lacunarity (frequency multiplier per octave, default $\lambda = 2.0$)
- $H$: Hurst roughness exponent, related via $\rho = \lambda^{-H}$
- $\mathcal{N}(u, v)$: Gradient / Perlin / Simplex noise basis

### 7.2 Analytical Surface Normals
For a heightfield surface $\mathbf{r}(x, z) = (x, h(x, z), z)^T$, the unnormalized surface normal $\mathbf{n}$ is obtained directly from partial derivatives:

$$\mathbf{n} = \frac{\partial \mathbf{r}}{\partial x} \times \frac{\partial \mathbf{r}}{\partial z} = \begin{pmatrix} 1 \\ \frac{\partial h}{\partial x} \\ 0 \end{pmatrix} \times \begin{pmatrix} 0 \\ \frac{\partial h}{\partial z} \\ 1 \end{pmatrix} = \begin{pmatrix} -\frac{\partial h}{\partial x} \\ 1 \\ -\frac{\partial h}{\partial z} \end{pmatrix}$$

$$\mathbf{\hat{n}}(x, z) = \frac{\mathbf{n}}{\|\mathbf{n}\|} = \frac{1}{\sqrt{1 + \left(\frac{\partial h}{\partial x}\right)^2 + \left(\frac{\partial h}{\partial z}\right)^2}} \begin{pmatrix} -\frac{\partial h}{\partial x} \\ 1 \\ -\frac{\partial h}{\partial z} \end{pmatrix}$$

---

## 8. Summary Complexity Matrix

| Primitive | Parametric Variables | Vertex Formula Complexity | Triangles (Resolution $N$) | Genus $g$ | Euler $\chi$ |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **4D Tesseract** | $\theta_{xw}, \theta_{yw}, d, s$ | $\mathcal{O}(1)$ (16 vertices) | 48 | 0 (per cell) | 2 |
| **Torus Knot** | $p, q, r_{\text{tube}}, R_0$ | $\mathcal{O}(N_{\text{tube}} \cdot N_{\text{rad}})$ | $2 N_{\text{tube}} N_{\text{rad}}$ | 1 | 0 |
| **Superquadric** | $s_1, s_2, k_t, k_w, k_b$ | $\mathcal{O}(N_\eta \cdot N_\omega)$ | $2 N_\eta N_\omega$ | 0 | 2 |
| **Fibonacci Sphere** | $N, R, \theta_g$ | $\mathcal{O}(N)$ | $\sim 2N - 4$ | 0 | 2 |
| **Buckyball** | $\phi, t=1/3$ | $\mathcal{O}(1)$ (60 vertices) | 116 | 0 | 2 |
| **Möbius Strip** | $R, w, n=1$ | $\mathcal{O}(N_u \cdot N_v)$ | $2 N_u N_v$ | Non-orientable | 0 |
| **Fractal Terrain** | $M, \rho, \lambda, H$ | $\mathcal{O}(N_x \cdot N_z \cdot M)$ | $2 (N_x-1)(N_z-1)$ | 0 | 1 (open) |
