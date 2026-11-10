# Dossier 1: Hollow 5-Simplex Boundary ($b_4 = 1$) Exact Rational 4-Volume Flux and Curvature Obstruction Certificate

## 1. Mathematical Claim

**Claim Identifier:** `CLM-DEMO9-SIMPLEX5-B4-1-001`  
**Epistemic Posture:** Exact rational linear programming duality over the ordered field $\mathbb{Q}$ on a degree-4 manifold pipeline with non-trivial 4-cavity ($b_4 = 1$).  
**Rust Verification Engine:** `omega_functional::phi4::Phi4Functional::verify_exact_certificate`.  
**Target Statement:**  
On the hollow 5-simplex boundary complex $K = \partial \Delta^5 \cong S^4$ with 6 vertices, 15 edges, 20 triangular faces, 15 tetrahedra, and 6 4-simplices (pentachora):
1. The chain and cochain complexes satisfy exact nilpotence across degrees 0, 1, 2, 3, 4:
   $$C_4 \xrightarrow{\partial_4} C_3 \xrightarrow{\partial_3} C_2 \xrightarrow{\partial_2} C_1 \xrightarrow{\partial_1} C_0, \qquad C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2 \xrightarrow{d_2} C^3 \xrightarrow{d_3} C^4$$
   where $\partial_k = d_{k-1}^T$, satisfying:
   - 1-skeleton nilpotence: $d_1 d_0 = 0 \in \mathbb{Q}^{20 \times 6}$
   - Discrete Bianchi identity: $d_2 d_1 = 0 \in \mathbb{Q}^{15 \times 15}$
   - 4-volume curvature / Bianchi coboundary identity: $d_3 d_2 = 0 \in \mathbb{Q}^{6 \times 20}$
   identically over $\mathbb{Q}$.
2. The Euler characteristic and Betti numbers are:
   $$\chi(K) = |V| - |E| + |F| - |T| + |P| = 6 - 15 + 20 - 15 + 6 = 2$$
   $$b_0(K) = 1, \quad b_1(K) = 0, \quad b_2(K) = 0, \quad b_3(K) = 0, \quad b_4(K) = 1$$
   where the 4-cavity homology $H_4(K; \mathbb{Q}) = Z_4(K; \mathbb{Q})$ is 1-dimensional, spanned by the fundamental 4-cycle:
   $$v^* = (-1, 1, -1, 1, -1, 1)^T \in C_4(K; \mathbb{Q})$$
   satisfying exact boundary vanishing $\partial_4 v^* = d_3^T v^* = 0 \in \mathbb{Q}^{15}$.
3. For the target 4-cochain flux $G = (-1/6, 1/6, -1/6, 1/6, -1/6, 1/6)^T \in C^4(K; \mathbb{Q})$ and unit 4-simplex weights $\mu_\sigma = 1$:
   - The total flux pairing through the 4-cavity is:
     $$\langle G, v^* \rangle = G^T v^* = 6 \times \frac{1}{6} = 1 \ne 0$$
   - By Stokes' pairing and the 4-volume curvature identity $d_3 d_2 = 0$, any exact 4-flux $d_3 C$ for $C \in C^3(K; \mathbb{Q})$ satisfies:
     $$\langle d_3 C, v^* \rangle = \langle C, d_3^T v^* \rangle = \langle C, 0 \rangle = 0$$
     establishing that the 4-flux cannot be trivialized by any 3-cochain potential $C$.
   - The exact primal $\ell^1$ quotient obstruction mass is:
     $$\Phi_4([G]) = \min_{C \in \mathbb{Q}^{15}} \sum_{\sigma=0}^5 \mu_\sigma |G_\sigma - (d_3 C)_\sigma| = 1$$
   - The optimal gauge potential $C^* = 0 \in \mathbb{Q}^{15}$ achieves primal residual $r^* = G$ with $\|r^*\|_{1, \mu} = 1$.
   - The optimal dual 4-cycle witness $v^* = (-1, 1, -1, 1, -1, 1)^T$ satisfies:
     - 4-cycle closure: $d_3^T v^* = 0 \in \mathbb{Q}^{15}$,
     - Dual bound: $|v_\sigma^*| \le \mu_\sigma = 1$ for all $\sigma \in \{0, \dots, 5\}$,
     - Dual pairing: $\langle G, v^* \rangle = 1$.
   - The exact duality gap in $\mathbb{Q}$ vanishes:
     $$\sum_{\sigma=0}^5 \mu_\sigma |r_\sigma^*| - \langle G, v^* \rangle = 1 - 1 = 0 \in \mathbb{Q}$$
4. Replay in both the Python rational verifier and the Rust `omega_functional::phi4` engine confirms exact optimality under the Zero-Float Law.

---

## 2. Epistemic Ledger (Claim Hygiene Rule)

### 2.1 What This Dossier Supports
- Demonstrates in this finite rational model that exact LP weak duality certifies the optimal degree-4 quotient obstruction $\Phi_4([G]) = 1$ on a cell complex with non-trivial 4-cavity ($b_4 = 1$).
- Demonstrates that the discrete curvature identity $d_3 d_2 = 0$, Bianchi identity $d_2 d_1 = 0$, and 1-skeleton nilpotence $d_1 d_0 = 0$ hold identically over $\mathbb{Q}$ without floating-point error.
- Demonstrates that non-closed candidate 4-chains ($d_3^T v \ne 0$) and float rounding errors are rejected with typed refusals.

### 2.2 What This Dossier Does NOT Support
- Does **not** establish continuous differential form de Rham cohomology on smooth 4-manifolds or pseudo-Riemannian spacetime metrics.
- Does **not** establish Donaldson or Seiberg-Witten gauge invariants.
- Does **not** establish quantum field theoretic 4-volume path integral convergence.

### 2.3 The Narrowest Defensible Claim
*On the finite 6-vertex, 15-edge, 20-face, 15-tetrahedron, 6-pentachoron hollow 5-simplex boundary complex ($b_4 = 1$), the certificate pair $(C^*, v^*)$ certifies in $\mathbb{Q}$ that the degree-4 quotient obstruction of $G = (-1/6, 1/6, -1/6, 1/6, -1/6, 1/6)^T$ is exactly $\Phi_4([G]) = 1$ with zero duality gap, and that $d_3 d_2 = 0$, $d_2 d_1 = 0$, and $d_1 d_0 = 0$.*

### 2.4 Next Test Needed
Couple to 4-manifold complexes ($b_2 \ge 2, b_4 = 1$) to test discrete Pontryagin cup product pairings $\langle F \smile F, [M^4] \rangle$ and topological instanton number quantization.
