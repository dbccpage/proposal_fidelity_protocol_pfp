# Dossier 2: Exact Rational Linear Programming Duality & Non-Erasure Certificate Verification

## 1. Mathematical Claim

**Claim Identifier:** `CLM-DEMO4-EXACT-LP-001`  
**Epistemic Posture:** Exact rational linear programming duality over the ordered field $\mathbb{Q}$.  
**Lean 4 Theorem Reference:** `PaperER007.lp_max_form_weak_duality` in [`lean4/LpWeakDuality.lean`](../../../../../lean4/LpWeakDuality.lean).  
**Target Statement:**  
On the 3-cycle cochain complex $C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2$ over $\mathbb{Q}$ with vertices $\{v_0, v_1, v_2\}$, edges $\{e_0, e_1, e_2\}$, uniform weights $\omega_e = 1$, and target 1-cochain $c = (1/3, 1/3, 1/3)^T$:
1. The primal $\ell^1$ quotient defect mass problem is:
   $$\Phi_1([c]) = \min_{\alpha \in \mathbb{Q}^3, u \in \mathbb{Q}^3} \sum_{e=0}^2 u_e \quad \text{s.t.} \quad u_e \ge |c_e - (d_0 \alpha)_e|, \; u_e \ge 0$$
2. The dual linear program over bounded edge multipliers $w \in \mathbb{Q}^3$ is:
   $$\max_{w \in \mathbb{Q}^3} w^T c \quad \text{s.t.} \quad -1 \le w_e \le 1, \; d_0^T w = 0$$
3. By ordered-field weak duality, $w^T c \le \sum u_e$ for any feasible primal-dual pair.
4. The candidate pair consisting of primal potential $\alpha^* = (0, 0, 0)^T$ (with $u^* = (1/3, 1/3, 1/3)^T$) and dual witness $w^* = (1, 1, 1)^T$ satisfies:
   - **Primal Feasibility:** $u_e^* \ge |c_e - (d_0 \alpha^*)_e|$ for all $e \in \{0, 1, 2\}$,
   - **Dual Feasibility:** $\|w^*\|_\infty = 1 \le 1$ and $d_0^T w^* = (0, 0, 0)^T$,
   - **Exact Zero Duality Gap in $\mathbb{Q}$:**
     $$\sum_{e=0}^2 \omega_e u_e^* - w^{*T} c = 1 - 1 = 0 \in \mathbb{Q}$$
5. Under the **Zero-Float Law**, approximate floating-point representations ($0.3333333333333333$) or dual infeasible vectors matching the objective value without vanishing divergence ($d_0^T w \ne 0$) are strictly refused.

---

## 2. Epistemic Ledger (Claim Hygiene Rule)

### 2.1 What This Dossier Supports
- Demonstrates in this finite rational model that exact rational primal-dual certificates certify the optimal value $\Phi_1([c]) = 1$ without floating-point error.
- Verifies that zero duality gap certifies optimality only when both primal and dual feasibility conditions are independently checked in $\mathbb{Q}$.
- Rejects false zero laundering and floating-point precision leakage under the Zero-Float Law.

### 2.2 What This Dossier Does NOT Support
- Does **not** establish strong duality for infinite-dimensional Banach spaces or continuous differential forms.
- Does **not** formalize the $\ell^1 / \ell^\infty$ norm dual statement in Lean 4 (as fenced in `LpWeakDuality.lean`).
- Does **not** forbid heuristic or approximate solvers from proposing candidates during search, provided final certification executes strictly in $\mathbb{Q}$.

### 2.3 The Narrowest Defensible Claim
*Under exact rational arithmetic over $\mathbb{Q}$, the certificate pair $(\alpha^*, w^*)$ shows that the quotient defect mass of $c = (1/3, 1/3, 1/3)^T$ modulo exact coboundaries is certified exactly as $\Phi_1([c]) = 1$, certifying non-erasure of the topological obstruction.*

### 2.4 Next Test Needed
Integrate the exact rational checker with the Rust `omega_functional` dual simplex engine across higher-degree cell complexes.
