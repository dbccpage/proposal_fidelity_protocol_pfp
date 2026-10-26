---
documentation_contract: symbol-game-documentation/v1
title: 'Application Note: Higher-Degree Cell Complexes, Discrete Bianchi Identities, and Anomaly Cancellation'
kind: application-reference
audience:
  - researchers
  - topologists
  - physics-engineers
  - coding-agents
status: active
maturity: emerging
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - higher_degree_cochain_complex
    - discrete_bianchi_identity
    - bianchi_defect_functional
    - higher_degree_quotient_obstruction_mass
    - dual_cavity_witness
    - cup_product_anomaly_pairing
  prose_theorems:
    - cochain_nilpotence_all_degrees
    - stokes_pairing_vanishing_on_cavities
    - degree_k_weak_duality_over_rationals
    - discrete_green_schwarz_anomaly_cancellation
  lean_theorems: []
  finite_computations:
    - demo_6_hollow_tetrahedron_b2_1
    - demo_6_fused_tetrahedra_b2_2
    - demo_7_hollow_4simplex_b3_1
    - demo_7_torsion_bianchi_complex
    - demo_9_hollow_5simplex_b4_1
    - demo_11_green_schwarz_anomaly
  declared_policies:
    - zero_float_in_higher_degree_certificates
  applications:
    - higher_dimensional_topological_obstructions
    - discrete_gauge_theories_and_anomalies
  open_conjectures: []
coefficient_domain: "ℚ"
runtime_dependency: "Chapter 02 (Cochain Complexes), Chapter 03 (Obstruction Mass & LP Duality)"
governance_dependency: "None"
---

# Application Note: Higher-Degree Cell Complexes, Discrete Bianchi Identities, and Anomaly Cancellation

**Status:** Downstream Mathematical Application  
**Context:** Formulates graded chain and cochain complexes beyond 1-skeletons ($C_k \xrightarrow{\partial_k} C_{k-1}$ and $C^{k-1} \xrightarrow{d_{k-1}} C^k$), exact nilpotence, the discrete Bianchi identity ($d_2 \circ d_1 = 0$), higher-degree quotient obstruction functionals $\Phi_k([H])$, exact rational dual cavity witnesses, and discrete cup-product anomaly cancellation. Grounded in executable dossiers from Demos 6, 7, 9, 11 and Challenges C011–C020.  
**Authority:** None. Mathematical models, exact rational certifiers, and discrete combinatorial topology.

---

## 1. Graded Complexes & All-Degree Nilpotence

Let $K$ be an oriented finite cell complex of dimension $n$. For each integer degree $0 \le k \le n$:
- $C_k(K; \mathbb{Q})$ denotes the finite-dimensional vector space of formal rational $k$-chains spanned by oriented $k$-cells $\sigma_k \in X_k$.
- $C^k(K; \mathbb{Q}) = \operatorname{Hom}(C_k, \mathbb{Q})$ denotes the dual space of rational $k$-cochains.

### 1.1 Graded Differentials & Duality
The geometric boundary operators $\partial_k$ and algebraic coboundary operators $d_{k-1}$ are formal transposes under the canonical pairing $\langle \omega, c \rangle = \sum_{\sigma \in X_k} \omega_\sigma c_\sigma$:

$$\text{Chains:} \quad C_n \xrightarrow{\partial_n} C_{n-1} \xrightarrow{\partial_{n-1}} \cdots \xrightarrow{\partial_2} C_1 \xrightarrow{\partial_1} C_0$$
$$\text{Cochains:} \quad C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2 \xrightarrow{d_2} \cdots \xrightarrow{d_{n-1}} C^n$$

with matrix representation:
$$\partial_k = d_{k-1}^T \in \mathbb{Q}^{|X_{k-1}| \times |X_k|}, \qquad d_{k-1} \in \mathbb{Q}^{|X_k| \times |X_{k-1}|}$$

### 1.2 All-Degree Nilpotence Theorem
**Theorem (Cochain Nilpotence at All Degrees):**  
For any oriented simplicial complex $K$ with the standard alternating-sign boundary, and any degree $k \ge 1$:
$$d_k \circ d_{k-1} = 0 \in \mathbb{Q}^{|X_{k+1}| \times |X_{k-1}|}, \qquad \partial_k \circ \partial_{k+1} = 0 \in \mathbb{Q}^{|X_{k-1}| \times |X_{k+1}|}$$

*Proof in this combinatorial setting:*  
Every $(k+1)$-cell has a boundary comprised of $k$-cells, and each $(k-1)$-cell interface between adjacent $k$-cells appears exactly twice with opposing induced orientations. The rational sum of boundary coefficients vanishes identically. $\square$

*Scope (2026-10-20):* the pairing argument is the simplicial one: removing vertices $i < j$ in the two orders gives signs $(-1)^{i}(-1)^{j-1}$ and $(-1)^{j}(-1)^{i}$, which cancel. For a general cell complex presented by incidence matrices, $\partial_k \partial_{k+1} = 0$ is a condition the presentation must satisfy, not a consequence of having cells; a host should check it on the supplied matrices, as the dossiers below do.

---

## 2. The Discrete Bianchi Identity & The Bianchi Defect Functional

In discrete gauge theories and higher differential geometry, the nilpotence of coboundary operators takes concrete physical and computational meaning:
- Degree 1: $d_1 \circ d_0 = 0$ ensures that any gradient 1-cochain $A = d_0 \phi$ has zero curl around every face $f$: $(d_1 d_0 \phi)_f = 0$.
- Degree 2: $d_2 \circ d_1 = 0$ is the **Discrete Bianchi Identity**. For any 1-cochain gauge connection $A \in C^1$, its field strength (curvature) $F = d_1 A \in C^2$ satisfies:
  $$d_2 F = d_2 (d_1 A) = 0 \in C^3(K; \mathbb{Q})$$

### 2.1 The Bianchi Defect Functional $\Gamma_{k+1}$
When an arbitrary candidate field strength $B \in C^k(K; \mathbb{Q})$ is proposed (which may not be derived from a global gauge potential), the **Bianchi Defect Functional** measures its obstruction to closure:

$$\Gamma_{k+1}(B) = \|d_k B\|_{1, \nu} = \sum_{t \in X_{k+1}} \nu_t |(d_k B)_t|$$

where $\nu_t > 0$ are positive rational cell weights.

**Properties:**
1. **Vanishing on Exact Fluxes:** If $B = d_{k-1} A$ for some $A \in C^{k-1}$, then $\Gamma_{k+1}(B) = \|d_k d_{k-1} A\|_{1, \nu} = 0$.
2. **Local Evaluation:** Computing $\Gamma_{k+1}(B)$ requires only a sparse matrix-vector multiplication $d_k B$ and an $\ell^1$ norm evaluation, with no optimization required.

---

## 3. Higher-Degree Quotient Obstruction Mass $\Phi_k([H])$

When a target $k$-cochain flux $H \in C^k(K; \mathbb{Q})$ is specified on a cell complex with $k$-cavities ($b_k = \dim H_k(K; \mathbb{Q}) \ge 1$), the net flux through a closed $k$-cycle cannot be eliminated by any gauge transformation.

### 3.1 Primal $\ell^1$ Optimization
For target flux $H \in C^k(K; \mathbb{Q})$ and positive rational cell weights $\omega_\sigma > 0$:

$$\Phi_k([H]) = \min_{B \in C^{k-1}(K; \mathbb{Q})} \sum_{\sigma \in X_k} \omega_\sigma |H_\sigma - (d_{k-1} B)_\sigma|$$

### 3.2 Dual Exact Rational Formulation
Dualizing over $\mathbb{Q}$ via exact linear programming:

$$\Phi_k^*([H]) = \max_{u \in C_k(K; \mathbb{Q})} \sum_{\sigma \in X_k} u_\sigma H_\sigma$$
$$\text{subject to:} \quad d_{k-1}^T u = 0 \quad (\partial_k u = 0, \text{ closed } k\text{-chain}), \quad |u_\sigma| \le \omega_\sigma \quad \forall \sigma \in X_k$$

**Theorem (Degree-$k$ Weak Duality over $\mathbb{Q}$):**  
For any primal gauge candidate $B \in C^{k-1}(K; \mathbb{Q})$ and any dual candidate $u \in C_k(K; \mathbb{Q})$ satisfying $d_{k-1}^T u = 0$ and $\|u\|_\infty \le \omega$:

$$\langle H, u \rangle \le \sum_{\sigma \in X_k} \omega_\sigma |H_\sigma - (d_{k-1} B)_\sigma|$$

*Proof:*
$$\langle H, u \rangle = \langle H - d_{k-1} B, u \rangle + \langle d_{k-1} B, u \rangle = \langle H - d_{k-1} B, u \rangle + \langle B, d_{k-1}^T u \rangle$$
Since $d_{k-1}^T u = 0$, the second term vanishes:
$$\langle H, u \rangle = \langle H - d_{k-1} B, u \rangle \le \sum_\sigma |(H - d_{k-1} B)_\sigma| \cdot |u_\sigma| \le \sum_\sigma \omega_\sigma |(H - d_{k-1} B)_\sigma| \quad \square$$

### 3.3 Exact Zero-Gap Certificate
When the host is provided with a pair $(B^*, u^*)$ such that:
1. $d_{k-1}^T u^* = 0 \in \mathbb{Q}^{|X_{k-1}|}$ (exact closed $k$-cycle),
2. $|u^*_\sigma| \le \omega_\sigma$ for all $\sigma \in X_k$ (dual box feasibility),
3. $\sum_\sigma \omega_\sigma |H_\sigma - (d_{k-1} B^*)_\sigma| - \langle H, u^* \rangle = 0 \in \mathbb{Q}$ (zero duality gap),

the exact quotient obstruction mass is certified unconditionally: $\Phi_k([H]) = \langle H, u^* \rangle$.

---

## 4. Canonical Finite Cell Complex Dossiers

### 4.1 Degree 2: Hollow Tetrahedron $\partial \Delta^3 \cong S^2$ ($b_2 = 1$)
- **Carrier:** 4 vertices, 6 edges, 4 triangular faces.
- **Topology:** Euler characteristic $\chi = 4 - 6 + 4 = 2$; Betti numbers $b_0 = 1, b_1 = 0, b_2 = 1$.
- **Nilpotence:** $d_1 d_0 = 0 \in \mathbb{Q}^{4 \times 4}$.
- **Fundamental 2-Cycle:** $Z = (1, -1, 1, -1)^T \in C_2$, satisfying $d_1^T Z = 0 \in \mathbb{Q}^6$.
- **Stokes' Pairing:** For any $A \in C^1$, $\langle d_1 A, Z \rangle = \langle A, d_1^T Z \rangle = 0$.
- **Test Target:** For $B = (1/4, -1/4, 1/4, -1/4)^T$ with $\omega_f = 1$:
  $$\langle B, Z \rangle = 1, \quad B^* = 0 \implies \Phi_2([B]) = 1, \quad \text{Gap} = 0 \in \mathbb{Q}$$
  *(Worked, 2026-10-20: here $B^* = 0$ is the primal gauge potential in $C^1$, not the target. Primal value: $\sum_f |B_f| = 4 \cdot 1/4 = 1$. Dual value: $Z$ is closed and $|Z_f| = 1 \le \omega_f$, and $\langle B, Z \rangle = 1/4 + 1/4 + 1/4 + 1/4 = 1$. Primal minus dual is $0$. The cycle $Z = (1, -1, 1, -1)$ assumes the faces are listed as $[1,2,3], [0,2,3], [0,1,3], [0,1,2]$, the order in $\partial[0,1,2,3]$.)*

### 4.2 Degree 3: Hollow 4-Simplex Boundary $\partial \Delta^4 \cong S^3$ ($b_3 = 1$)
- **Carrier:** 5 vertices, 10 edges, 10 triangular faces, 5 tetrahedra.
- **Topology:** $\chi = 5 - 10 + 10 - 5 = 0$; Betti numbers $b_0 = 1, b_1 = 0, b_2 = 0, b_3 = 1$.
- **Bianchi Nilpotence:** $d_2 d_1 = 0 \in \mathbb{Q}^{5 \times 10}$ and $d_1 d_0 = 0 \in \mathbb{Q}^{10 \times 5}$.
- **Fundamental 3-Cycle:** $W = (1, -1, 1, -1, 1)^T \in C_3$, satisfying $d_2^T W = 0 \in \mathbb{Q}^{10}$.
- **Test Target:** For $H = (1/5, -1/5, 1/5, -1/5, 1/5)^T$ with $\nu_t = 1$:
  $$\langle H, W \rangle = 1, \quad \Phi_3([H]) = 1, \quad \text{Gap} = 0 \in \mathbb{Q}$$

### 4.3 Degree 4: Hollow 5-Simplex Boundary $\partial \Delta^5 \cong S^4$ ($b_4 = 1$)
- **Carrier:** 6 vertices, 15 edges, 20 triangular faces, 15 tetrahedra, 6 4-simplices.
- **Topology:** $\chi = 6 - 15 + 20 - 15 + 6 = 2$; Betti numbers $b_0 = 1, b_1 = 0, b_2 = 0, b_3 = 0, b_4 = 1$.
- **Nilpotence:** $d_3 d_2 = 0 \in \mathbb{Q}^{6 \times 20}$.
- **Fundamental 4-Cycle:** $P_4 = (1, -1, 1, -1, 1, -1)^T \in C_4$, satisfying $d_3^T P_4 = 0 \in \mathbb{Q}^{15}$.
- **Intersection Pairing:** the cup-product pairing $H^2 \times H^2 \to H^4 \cong \mathbb{Q}$ on a closed oriented 4-manifold. For $S^4$ it is zero, because $H^2(S^4; \mathbb{Q}) = 0$ ($b_2 = 0$ above). No test target or duality gap is computed for this dossier. *(Corrected 2026-10-20: the earlier line called this a Pontryagin dual pairing on $C^2$.)*

---

## 5. Higher-Group 2-Gauge Fields & Green-Schwarz Anomaly Cancellation

In higher gauge theory (Demo 11 and Challenge C032), a 1-gauge connection $A \in C^1$ and a 2-gauge field $B \in C^2$ couple through an explicit cup-product boundary modification:

### 5.1 Modified 3-Form Bianchi Identity
Standard 3-form field strength $H \in C^3$ satisfies $H = d_2 B + \operatorname{CS}(A)$, leading to the discrete modified Bianchi identity:

$$d_3 H = F \smile F$$

where $F = d_1 A \in C^2$ is the gauge curvature 2-form, and $\smile: C^2 \times C^2 \to C^4$ is the simplicial cup product.

> **Correction and derivation (2026-10-20).** The earlier text wrote $H = d_2 B - \operatorname{CS}(A)$ and $d_3 H = \operatorname{Tr}(F \smile F)$; with the minus sign the identity comes out as $d_3 H = -F \smile F$. For a $\mathbb{Q}$-valued (abelian) connection take $\operatorname{CS}(A) = A \smile d_1 A \in C^3$. The cochain Leibniz rule $d(a \smile b) = da \smile b + (-1)^{|a|} a \smile db$ with $|A| = 1$ gives $d_3(A \smile d_1 A) = d_1 A \smile d_1 A - A \smile d_2 d_1 A = F \smile F$, and $d_3 d_2 B = 0$, so $d_3 H = F \smile F$. The identity was checked with exact rationals on the full 4-simplex for a random rational 1-cochain on 2026-10-20 (a review-time script, not retained in the repository). A trace $\operatorname{Tr}$ needs matrix-valued (non-abelian) cochains; the cochain-level non-abelian version is not derived here and stays open.

### 5.2 Discrete Anomaly Cancellation Condition
An operational higher-gauge state on a 4-dimensional cell complex is **anomaly-free** if and only if the 4-cochain obstruction vanishes on every 4-cell:

$$d_3 H - F \smile F = 0 \in C^4(K; \mathbb{Q})$$

> **Correction (2026-10-20).** The earlier condition paired the obstruction with closed 4-cycles, $\langle d_3 H - F \smile F, Z \rangle = 0$ for $Z \in Z_4(K)$. That test can never fail when $A$ and $H$ are global cochains: $\langle d_3 H, Z \rangle = \langle H, \partial_4 Z \rangle = 0$, and $F \smile F = d_3(A \smile d_1 A)$ is exact, so its pairing with a closed cycle is also 0. A defect is visible only cell by cell (or when $H$ is supplied patch-wise without a global $B$).

If a candidate state proposes non-matching Chern-Simons terms or uncompensated gauge curvature, the host calculates the exact rational anomaly defect $\Gamma_{\text{anomaly}} = \|d_3 H - F \smile F\|_1 > 0$ and refuses certification.

---

## 6. Host Refusal Taxonomy

The host evaluation boundary enforces strict typed refusals for invalid certificates:

| Refusal Code | Trigger Condition | Operational Meaning |
| :--- | :--- | :--- |
| `REFUSED_FLOAT_DETECTED` | Any matrix entry, coordinate, or weight contains floating-point representations. | Enforces Zero-Float Law over $\mathbb{Q}$. |
| `REFUSED_DUAL_NOT_CLOSED` | Dual candidate $u$ violates $d_{k-1}^T u = 0$. | Dual witness is not a cycle; fails boundary orthogonality. |
| `REFUSED_DUAL_NORM_EXCEEDS_WEIGHT` | Dual candidate has $|u_\sigma| > \omega_\sigma$ for some cell $\sigma$. | Violates dual box constraint; invalidates weak duality bound. |
| `REFUSED_DUALITY_GAP_NONZERO` | Primal objective minus dual pairing satisfies $\Delta > 0$. | Candidate is sub-optimal; quotient obstruction is uncertified. |
| `REFUSED_BIANCHI_VIOLATION` | Field strength candidate has non-zero Bianchi defect where exactness was asserted. | Curvature fails discrete Bianchi identity $d_k \circ d_{k-1} = 0$. |

---

## 7. Claim Hygiene & Artifact Boundary

1. **What this document supports:**
   - Demonstrates that the $\ell^1$ quotient obstruction mass formulation $\Phi_1$ extends to arbitrary degree $k \ge 2$ ($C^0 \to C^1 \to \cdots \to C^n$) over $\mathbb{Q}$.
   - Demonstrates that discrete Bianchi identities $d_k \circ d_{k-1} = 0$ provide cheap, optimization-free linear defect functionals $\Gamma_{k+1}(B) = \|d_k B\|_{1,\nu}$ for $B \in C^k$ (Section 2.1).
   - Confirms that exact rational dual cavity witnesses yield certified duality gaps of zero on the $S^2$ and $S^3$ dossiers ($S^4$ lists nilpotence and a cycle only).

2. **What this document does NOT support:**
   - Does not establish smooth manifold differential geometry or continuum limit convergence for arbitrary simplicial triangulations without uniform geometric shape bounds.
   - Does not demonstrate that quantum anomalies in continuous spacetime are resolved by finite combinatorial models alone.

3. **Narrowest defensible claim:**
   - On any finite oriented cell complex $K$ over $\mathbb{Q}$, the linear coboundary operator satisfies $d_k \circ d_{k-1} = 0$, and the degree-$k$ $\ell^1$ quotient obstruction mass is dualized by closed $k$-chains with box constraints under exact linear programming duality.

4. **Next test needed:**
   - Formalize the degree-2 weak duality theorem in Lean 4 (extending the existing Lean 4 proof for $k=1$ in `03_math_obstruction_mass_duality_and_exact_lp.md`).
