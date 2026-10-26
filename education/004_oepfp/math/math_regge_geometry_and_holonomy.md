---
documentation_contract: symbol-game-documentation/v1
title: 'Application Note: Discrete 4D Regge Calculus and Non-Abelian Holonomy Foundations'
kind: application-reference
audience:
- researchers
- physics-engineers
- coding-agents
status: active
maturity: emerging
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - simplicial_hinge_deficit_angle
    - cayley_menger_volume_metric
    - non_abelian_regge_holonomy
    - geometric_regge_bianchi_holonomy
  prose_theorems:
    - linear_nilpotence_distinguished_from_geometric_bianchi
    - basepoint_parallel_transport_bianchi_identity
  lean_theorems: []
  finite_computations: []
  declared_policies: []
  applications:
    - discrete_simplicial_spacetime_geometry
  open_conjectures: []
coefficient_domain: "ℚ[√·] / ℝ"
runtime_dependency: "Chapter 02 (Cochain Complexes, Repairs, and Quotients)"
governance_dependency: "None"
---

# Application Note: Discrete 4D Regge Calculus and Non-Abelian Holonomy Foundations

**Status:** Downstream Mathematical Application
**Context:** Rigorous formulation of discrete 4D simplicial geometry, deficit angles, non-Abelian parallel transport, and the geometric Regge Bianchi identity, distinguishing linear cochain nilpotence ($d_2 \circ d_1 = 0$) from nonlinear holonomy closure in $\mathrm{SO}(4)$.
**Authority:** None. Discrete simplicial differential geometry.

---

## 1. Discrete 4D Simplicial Geometry & Deficit Angles

In discrete 4D Regge calculus, spacetime is triangulated by an oriented 4-dimensional Euclidean simplicial manifold $K$. The metric data is carried entirely by squared edge lengths $l_{ij}^2 \in \mathbb{Q}_{>0}$ (or certified real algebraic extensions).

### 1.1 Simplex Nondegeneracy: Signed Cayley-Menger Determinants
For a $k$-simplex $\sigma = (v_0, \ldots, v_k)$ ($1 \le k \le 4$), the $(k+2) \times (k+2)$ Cayley-Menger matrix is:
$$CM_k = \begin{pmatrix} 0 & 1 & 1 & \cdots & 1 \\ 1 & 0 & l_{01}^2 & \cdots & l_{0k}^2 \\ 1 & l_{10}^2 & 0 & \cdots & l_{1k}^2 \\ \vdots & \vdots & \vdots & \ddots & \vdots \\ 1 & l_{k0}^2 & l_{k1}^2 & \cdots & 0 \end{pmatrix}$$

Under the conventional volume formula, a nondegenerate Euclidean simplex satisfies:
$$\det CM_k = (-1)^{k+1} 2^k (k!)^2 \operatorname{Vol}_k^2$$

Consequently, raw determinants are strictly negative in even simplex dimensions ($k=2, 4$):
- Unit 1-simplex (segment): raw determinant $= +2 > 0$
- Unit 2-simplex (triangle): raw determinant $= -3 < 0$
- Unit 3-simplex (tetrahedron): raw determinant $= +4 > 0$
- Unit 4-simplex (pentatope): raw determinant $= -5 < 0$

Requiring raw determinant positivity incorrectly rejects valid Euclidean triangles and 4-simplices. Geometric nondegeneracy requires **signed positivity**:
$$\boxed{(-1)^{k+1} \det CM_k > 0 \quad \text{for all } 1 \le k \le 4}$$
Equivalently, the edge Gram matrix $G_{ij} = \frac{l_{0i}^2 + l_{0j}^2 - l_{ij}^2}{2}$ ($1 \le i, j \le k$) must be strictly positive definite ($G \succ 0$).

### 1.2 Dihedral Angles via Signed Cofactors
Inside a 4-simplex $\sigma = (v_0, v_1, v_2, v_3, v_4)$, let $CM_4(\sigma)$ be the $6 \times 6$ Cayley-Menger matrix with row/column 0 as border and $1..5$ corresponding to vertices $v_0..v_4$. Let $\tau_i = \sigma \setminus \{v_i\}$ and $\tau_j = \sigma \setminus \{v_j\}$ be two tetrahedral faces intersecting at triangular hinge $h = \sigma \setminus \{v_i, v_j\}$. The internal dihedral angle $\theta_{ij}(\sigma)$ between $\tau_i$ and $\tau_j$ inside $\sigma$ is uniquely determined by the signed cofactors $\operatorname{Cof}(CM_4)_{a,b}$:
$$\cos \theta_{ij}(\sigma) = -\frac{\operatorname{Cof}(CM_4)_{i+1, j+1}}{\sqrt{\operatorname{Cof}(CM_4)_{i+1, i+1} \operatorname{Cof}(CM_4)_{j+1, j+1}}}$$

*Worked check (2026-10-20):* for the regular unit 4-simplex the diagonal cofactors are $4$ and the off-diagonal cofactor is $-1$, so $\cos\theta = 1/4$, the known dihedral angle $\arccos(1/4)$ of the regular 4-simplex. The formula as written relies on the diagonal cofactors being positive, which holds for $CM_4$; for a tetrahedron ($CM_3$) they are negative ($-3$ for the unit case) and the sign must be adjusted. The unit determinants listed in Section 1.1 ($2, -3, 4, -5$) were recomputed with exact rationals.

### 1.3 Simplicial Deficit Angles: Interior vs. Boundary Hinges
Curvature is concentrated on triangular hinges $h \in K^{(2)}$:
- **Interior Hinges:** For an interior hinge $h \in K^{(2)} \setminus \partial K$, the star of 4-simplices $\mathrm{Star}(h)$ forms a closed cyclic fan around $h$. The deficit angle measures the conical defect relative to full $2\pi$ Euclidean closure:
  $$\varepsilon_h := 2\pi - \sum_{\sigma \supset h} \theta_h(\sigma)$$
  When $\varepsilon_h = 0$, the metric geometry in the star of $h$ is locally isometric to flat $\mathbb{R}^4$.
- **Boundary Hinges:** For a boundary hinge $h \in \partial K^{(2)}$, where the star terminates at boundary tetrahedra, the deficit angle relative to flat half-space is:
  $$\varepsilon_h := \pi - \sum_{\sigma \supset h} \theta_h(\sigma)$$

---

## 2. Non-Abelian Parallel Transport and Hinge Holonomy

Because the rotation group $\mathrm{SO}(4)$ is non-Abelian, defining curvature holonomy requires declaring an explicit local frame, basepoint, and path conventions.

### 2.1 The Dual Graph and Basepoint Frame
1. **Simplicial Dual Graph:** Let $K^*$ denote the 1-skeleton of the Poincaré dual cell complex. Each node of $K^*$ corresponds to a 4-simplex $\sigma_a \in K^{(4)}$. Each directed dual edge $e^*_{ab} = (\sigma_a, \sigma_b)$ corresponds to a shared 3-simplex (tetrahedron) $\tau = \sigma_a \cap \sigma_b$.
2. **Declared Basepoint Frame:** Choose an arbitrary reference 4-simplex $\sigma_0 \in K^{(4)}$ and fix an orthonormal frame $e_{\mu}^{(0)}$ on $\sigma_0$.
3. **Face Transports:** Across each shared tetrahedron $\tau = \sigma_a \cap \sigma_b$, rigid face-matching induces a transition rotation $T_{ba} \in \mathrm{SO}(4)$ aligning the orthonormal coordinates of $\sigma_a$ with those of $\sigma_b$.
4. **Path Transport:** For any path $\gamma = (\sigma_0, \sigma_1, \ldots, \sigma_m)$ in the dual graph $K^*$, the total parallel transport is the ordered product:
   $$U(\gamma) = T_{m, m-1} \cdots T_{2, 1} T_{1, 0} \in \mathrm{SO}(4)$$

### 2.2 Local Hinge Rotation
Let $h$ be a triangular hinge. The star $\mathrm{Star}(h)$ consists of a sequence of 4-simplices $(\sigma_1, \sigma_2, \ldots, \sigma_p)$ ordered cyclically around $h$.
Around the minimal dual loop $\gamma_h = (\sigma_1, \sigma_2, \ldots, \sigma_p, \sigma_1)$ circulating $h$, parallel transport yields the local hinge holonomy:
$$R(h, \varepsilon_h) \in \mathrm{SO}(4)$$
In a local frame where the hinge triangle $h$ spans the $(x^1, x^2)$ plane, $R(h, \varepsilon_h)$ acts as a simple rotation by angle $\varepsilon_h$ in the orthogonal $(x^3, x^4)$ normal plane:
$$R(h, \varepsilon_h) = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & \cos \varepsilon_h & -\sin \varepsilon_h \\ 0 & 0 & \sin \varepsilon_h & \cos \varepsilon_h \end{pmatrix}$$

---

## 3. The Geometric Regge Bianchi Identity

### 3.1 Non-Abelian Holonomy Conservation Law & Coherent Boundary Words

In discrete 4D Regge calculus, non-Abelian curvature holonomies satisfy an exact geometric conservation law around closed dual boundaries (Hamber & Kagel, *Exact Bianchi identities in Regge gravity*, gr-qc/0107031, §2).

#### The Algebraic Path-Independence Obstruction
A crucial algebraic subtlety arises from the non-Abelian nature of $\mathrm{SO}(4)$: arbitrary, independently chosen access paths $\gamma_k$ from a basepoint $\sigma_0$ to each hinge $h_k$ do **not** yield an identity product. If an oriented boundary word satisfies $\prod_k \mathcal{R}_k = I$, replacing the access path to the first hinge with a path differing by a basepoint loop of holonomy $H \in \mathrm{SO}(4)$ conjugates only that factor:
$$\mathcal{R}_1' = H^{-1} \mathcal{R}_1 H \implies \mathcal{R}_1' \mathcal{R}_2 \cdots \mathcal{R}_m = H^{-1} \mathcal{R}_1 H \mathcal{R}_1^{-1} \neq I$$
which fails to equal identity for generic non-commuting rotations in $\mathrm{SO}(4)$.

#### Exact Coherent Boundary Construction
To obtain exact closure to $I_{\mathrm{SO}(4)}$, the access paths must be constructed via a **coherent dual boundary spanning tree**:

1. **Dual Boundary 2-Sphere:** Consider a primal edge $e = (v_1, v_2) \in K^{(1)}$. In the Poincaré dual complex $K^*$, the dual cell to $e$ is a 3-dimensional polyhedral cell $C_3^*(e)$, whose boundary is a closed polyhedral 2-sphere:
   $$S^2 = \partial C_3^*(e)$$
2. **Hinge Faces:** The 2-faces of $S^2$ correspond in 1-to-1 bijection with the triangular hinges $h \in K^{(2)}$ containing edge $e$.
3. **Coherent Access Tree:** Choose a basepoint 4-simplex $\sigma_0 \in S^2$. Select a spanning tree $\mathcal{T}$ of the 1-skeleton of $S^2$ rooted at $\sigma_0$. For each hinge face $h_k$, the access path $\gamma_k$ is the unique tree path in $\mathcal{T}$ from $\sigma_0$ to the hinge cycle.
4. **Cancellation of Dual Edge Transports:** When the hinge circulations are traversed in the orientation induced by the topological boundary operator $\partial S^2 = 0$, every dual edge $e^*_{ab} = (\sigma_a, \sigma_b)$ in the boundary complex is traversed exactly twice in opposite orientations: once in the forward direction $T_{ba}$ and once in the reverse direction $T_{ab} = T_{ba}^{-1}$.
5. **The Exact Geometric Regge Bianchi Theorem:**
   Because all internal tree legs and bounding dual edges cancel pairwise ($T_{ba} T_{ab} = I$), the expanded product word evaluates identically to the empty word in $\mathrm{SO}(4)$:
   $$\boxed{ \mathcal{P} \prod_{k=1}^m \left( U(\gamma_k) R(h_k, \varepsilon_k)^{\epsilon_k} U(\gamma_k)^{-1} \right) = I_{\mathrm{SO}(4)} }$$
   where $\epsilon_k \in \{+1, -1\}$ is the orientation sign of hinge face $h_k$ in $\partial C_3^*(e)$.
   *(For a vertex $v \in K^{(0)}$, the dual 4-cell $C_4^*(v)$ has boundary 3-sphere $S^3 = \partial C_4^*(v)$, which is tiled by dual 3-cells $C_3^*(e)$; summing the 3-cell boundary identities enforces total vertex closure).*

### 3.2 Distinction from Linear Cochain Nilpotence ($d_2 \circ d_1 = 0$)

A recurring defect in naive discrete geometric algorithms is conflating the geometric Bianchi identity with algebraic chain nilpotence:

| Property | Combinatorial Chain Nilpotence | Geometric Regge Bianchi Identity |
| :--- | :--- | :--- |
| **Equation** | $\partial_1 \circ \partial_2 = 0$ and $d_2 \circ d_1 = 0$ | $\mathcal{P} \prod_{k} U(\gamma_k) R(h_k, \varepsilon_k)^{\epsilon_k} U(\gamma_k)^{-1} = I_{\mathrm{SO}(4)}$ (same convention as Section 3.1; corrected 2026-10-20) |
| **Algebraic Character** | **Linear** operator identity over $\mathbb{Z}$ or $\mathbb{Q}$ | **Nonlinear** group product identity in $\mathrm{SO}(4)$ |
| **Metric Dependence** | **Metric-independent**: holds on any topology regardless of lengths | **Metric-dependent**: holds only when deficit angles and dihedral angles match Cayley-Menger metric data |
| **Carrier Space** | Abelian chain / cochain spaces $C_k(K), C^k(K)$ | Non-Abelian frame bundle / principal $\mathrm{SO}(4)$ bundle |
| **Linearized Limit** | Identical at all scales | Reduces to $\sum_k \varepsilon_k * h_k = 0$ only in weak-field limit ($\varepsilon_k \to 0$) |

---

## 4. Epistemic Scope Fence & Analogy Quarantine

> **Epistemic Scope Boundary:**
> Discrete 4D simplicial triangulations provide explicit finite carrier models for deficit angles, dihedral angles, and non-Abelian $\mathrm{SO}(4)$ holonomies. They do **not** constitute an empirical proof or mathematical derivation of:
> 1. Continuous Einstein general relativity or smooth pseudo-Riemannian manifolds;
> 2. Continuous Yang-Mills gauge field theories or electroweak unification;
> 3. Spontaneous symmetry breaking via the Higgs mechanism;
> 4. Spacetime supersymmetry (SUSY) or supergravity extensions.
>
> All former titles (such as `gauge_higgs_susy_bridge`) are retired. The mathematical content is strictly limited to discrete simplicial geometry and holonomy closure.
