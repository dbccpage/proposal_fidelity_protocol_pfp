# Demo 4: Executable Research Dossier Pair — Finite Parity Obstruction and Exact Rational LP Certification

## Current packaged execution

AuthorityEffect: None. The installed catalog owns current runs.

```console
symbol-game demo run demo_4 --output-dir ./runs/demo_4
symbol-game demo verify ./runs/demo_4/receipt.json
```

Current scope: Named functionals require an explicitly pinned Rust adapter. Historical values are not newly computed.

See the [migration ledger](../../migration/README.md) for source custody,
intentional behavior changes, native refusals, and the offline release gate.

## Historical baseline notes

The following describes the pre-migration research demonstration. Its old
runner commands and recorded values are historical; use the packaged commands
above for current execution. This migration does not refresh its evidence.

**Status:** Executable research dossier pair, 2026-09-24.  
**AuthorityEffect:** None.  
**Related Lean 4 Formalization:** [`lean4/LpWeakDuality.lean`](../../../../lean4/LpWeakDuality.lean) (`PaperER007.lp_max_form_weak_duality`).  
**Preceding Demos:** [Demo 1](../demo_1/1_demo.md) (Pilot trace audit), [Demo 2](../demo_2/2_demo.md) (Finite exact controls), [Demo 3](../demo_3/3_demo.md) (Immune host protocol).

---

## 1. Problem Formulation & Architecture

The Symbol Game and MSS-N research programs mandate strict claim hygiene: every mathematical claim presented in research preprints must be backed by an independently verifiable, deterministic artifact rather than narrative text, proof prose, or unchecked model claims.

Demo 4 implements the **first recommended executable research dossier pair**:
1. **Dossier 1 (`dossier_1_f2_spin_triangle`):** An exact $\mathbb{F}_2$ chain complex and syndrome check for a frustrated antiferromagnetic spin triangle.
2. **Dossier 2 (`dossier_2_exact_lp_certificate`):** An exact rational linear programming (LP) certificate checker over $\mathbb{Q}$ enforcing ordered-field weak duality and the **Zero-Float Law**.

Each dossier operates as a self-contained, typed bundle adhering to the standard six-artifact dossier layout:

```
dossier_X/
├── claim.md               # Scoped mathematical claim with epistemic hygiene ledger
├── input.yaml             # Typed, machine-readable boundary matrices and problem inputs
├── witness_valid.json     # Valid primal/dual certificate witness
├── witness_near_miss.json # Counter-witness or perturbed candidate testing refusal boundaries
├── checker.py             # Deterministic verification algorithm in pure integer/rational arithmetic
├── checker_output.json    # Standardized verification receipt with cryptographic digests
└── claim_ledger.json      # Cross-system registration and metadata
```

---

## 2. Dossier 1: Exact $\mathbb{F}_2$ Chain Complex & Frustrated Spin Triangle

- **Directory:** [`dossier_1_f2_spin_triangle/`](../../../../research/mssn_sn_tower/demos/demo_4/dossier_1_f2_spin_triangle/)
- **Claim Identifier:** `CLM-DEMO4-F2-SPIN-001`
- **Field:** Binary finite field $\mathbb{F}_2 = \{0, 1\}$.

### 2.1 Complex Topology & Nilpotence

Consider the 1-skeleton triangular cell complex $K = (V, E, F)$:
- Vertices: $V = \{v_0, v_1, v_2\}$
- Edges: $E = \{e_{01} = (v_0, v_1), \; e_{12} = (v_1, v_2), \; e_{20} = (v_2, v_0)\}$
- Oriented 2-cell (face): $F = \{f_0 = [e_{01}, e_{12}, e_{20}]\}$

The boundary matrices over $\mathbb{F}_2$ are:
$$d_0 = \begin{pmatrix} 1 & 1 & 0 \\ 0 & 1 & 1 \\ 1 & 0 & 1 \end{pmatrix}, \quad d_1 = \begin{pmatrix} 1 & 1 & 1 \end{pmatrix}$$

The composite operator satisfies exact chain nilpotence:
$$d_1 \circ d_0 = \begin{pmatrix} 1 & 1 & 1 \end{pmatrix} \begin{pmatrix} 1 & 1 & 0 \\ 0 & 1 & 1 \\ 1 & 0 & 1 \end{pmatrix} = \begin{pmatrix} 2 & 2 & 2 \end{pmatrix} \equiv \begin{pmatrix} 0 & 0 & 0 \end{pmatrix} \pmod 2$$

### 2.2 Parity Obstruction

The target cochain represents uniform antiferromagnetic frustration where every bond demands opposing spins:
$$c_{\mathrm{afm}} = \begin{pmatrix} 1 \\ 1 \\ 1 \end{pmatrix} \in C^1(K; \mathbb{F}_2)$$

Evaluating the face curl yields:
$$d_1 c_{\mathrm{afm}} = 1 + 1 + 1 = 3 \equiv 1 \pmod 2 \ne 0$$

Because $d_1(d_0 s) = 0 \pmod 2$ for all vertex configurations $s \in \mathbb{F}_2^3$, it is algebraically excluded that $c_{\mathrm{afm}} \in \operatorname{im}(d_0)$. Consequently:
- For every spin assignment $s \in \mathbb{F}_2^3$, the residual defect $r = c_{\mathrm{afm}} - d_0 s \pmod 2$ has Hamming weight $\|r\|_0 \ge 1$.
- The optimal configuration $s^* = (0, 1, 0)^T$ leaves exactly one frustrated bond ($e_{20}$), achieving $\|c_{\mathrm{afm}} - d_0 s^*\|_0 = 1$.

### 2.3 Refusal of Near-Miss Claims

The near-miss candidate (`witness_near_miss.json`) proposes $s = (1, 0, 1)^T$ while claiming a defect weight of 0. The checker computes:
$$d_0 s = \begin{pmatrix} 1 \\ 1 \\ 0 \end{pmatrix}, \quad r = c_{\mathrm{afm}} - d_0 s = \begin{pmatrix} 0 \\ 0 \\ 1 \end{pmatrix} \implies \|r\|_0 = 1 \ne 0$$
The candidate claim is deterministically refused with status `REFUSED_FALSE_ZERO_DEFECT_CLAIM`.

---

## 3. Dossier 2: Exact Rational LP Certificate Checker over $\mathbb{Q}$

- **Directory:** [`dossier_2_exact_lp_certificate/`](../../../../research/mssn_sn_tower/demos/demo_4/dossier_2_exact_lp_certificate/)
- **Claim Identifier:** `CLM-DEMO4-EXACT-LP-001`
- **Field:** Ordered field of rational numbers $\mathbb{Q}$.

### 3.1 Primal-Dual Formulation

On the 3-cycle cochain complex over $\mathbb{Q}$ with uniform edge weights $\omega_e = 1$ and target 1-cochain $c = (1/3, 1/3, 1/3)^T$:

1. **Primal $\ell^1$ Quotient Defect Minimization:**
   $$\Phi_1([c]) = \min_{\alpha \in \mathbb{Q}^3, u \in \mathbb{Q}^3} \sum_{e=0}^2 u_e \quad \text{s.t.} \quad u_e \ge |c_e - (d_0 \alpha)_e|, \; u_e \ge 0$$
2. **Dual Linear Program:**
   $$\max_{w \in \mathbb{Q}^3} w^T c \quad \text{s.t.} \quad -1 \le w_e \le 1, \; d_0^T w = 0$$

### 3.2 Formal Lean 4 Connection

Weak duality over an ordered field is formalized in `lean4/LpWeakDuality.lean` (`PaperER007.lp_max_form_weak_duality`):
$$\forall w \in \text{DualFeasible}, (\alpha, u) \in \text{PrimalFeasible} \implies w^T c \le \sum_{e} \omega_e u_e$$
When a feasible primal-dual pair achieves an exact equality:
$$\sum_{e=0}^2 \omega_e u_e^* - w^{*T} c = 0 \in \mathbb{Q}$$
the duality gap vanishes, certifying that $\Phi_1([c]) = w^{*T} c$ without invoking floating-point approximations.

### 3.3 Zero-Float Law and Near-Miss Boundaries

The checker strictly implements the **Zero-Float Law**:
1. **Float Laundering Refusal:** A near-miss proposing $u = (0.3333333333333333, \dots)$ is parsed into rational representation $3333333333333333/10000000000000000$. Because this rational is strictly less than $1/3$, it violates primal feasibility $u_e \ge |c_e - (d_0 \alpha)_e| = 1/3$ and is refused with `REFUSED_PRIMAL_INFEASIBLE`.
2. **Dual Feasibility Enforcement:** A near-miss proposing $w = (3, 0, 0)^T$ achieves $w^T c = 3 \cdot (1/3) = 1$ (matching the primal value), but violates both bound constraints $\|w\|_\infty \le 1$ and divergence-free cycle closure $d_0^T w = 0$. The checker requires feasibility prior to gap evaluation, refusing the candidate with `REFUSED_DUAL_INFEASIBLE`.

The certified pair $\alpha^* = (0, 0, 0)^T$, $u^* = (1/3, 1/3, 1/3)^T$, $w^* = (1, 1, 1)^T$ yields primal cost 1 and dual value 1, producing an exact rational gap of 0 and receipt status `CERTIFIED_OPTIMAL_LP_GAP_ZERO`.

---

## 4. Execution & Verification

### 4.1 Standalone Unified Runner

To execute both dossiers and emit summary receipts:

```bash
python research/mssn_sn_tower/demos/demo_4/run_demo4.py
```

Expected output:
```text
================================================================================
MSS-N DEMO 4: EXECUTABLE RESEARCH DOSSIER PAIR
================================================================================

--- Running Dossier 1: F2 Frustrated Spin Triangle Parity Obstruction ---
  [+] Valid Witness: CERTIFIED_OBSTRUCTION
      Detail: Exact obstruction certified: d1*d0 == 0 mod 2, d1*c = 1 != 0 mod 2. Candidate s=[0, 1, 0] achieves minimal defect weight 1 with frustrated bond(s).
  [-] Near Miss:     REFUSED_FALSE_ZERO_DEFECT_CLAIM
      Detail: Candidate falsely claims defect 0, but curl d1*c = 1 != 0 forces at least one frustrated bond. Actual recomputed defect weight = 1.

--- Running Dossier 2: Exact Rational LP Certificate Checker (Over Q) ---
  [+] Valid Witness: CERTIFIED_OPTIMAL_LP_GAP_ZERO
      Detail: Exact optimality certified in Q: primal_obj = 1, dual_obj = 1, duality_gap = 0. Both primal and dual feasibility conditions independently checked.
  [-] Near Miss [case_float_rounding_defect]: REFUSED_PRIMAL_INFEASIBLE
      Detail: Primal bounding vector u violates u_e >= |c_e - (d0*alpha)_e|
  [-] Near Miss [case_infeasible_dual_gap_match]: REFUSED_DUAL_INFEASIBLE
      Detail: Dual multiplier bounds violated: max|w_e| = 3 > 1; Dual divergence non-zero: d0^T * w = ['-3', '3', '0'] != 0

================================================================================
DEMO 4 VERIFICATION PASSED: BOTH DOSSIERS DETERMINISTICALLY CHECKED
================================================================================
```

### 4.2 Targeted Pytest Suite

In accordance with the Strict Test Execution Directive, run only the targeted test file:

```bash
python -m pytest research/mssn_sn_tower/demos/demo_4/test_run_demo4.py
```

All 8 tests exercise:
- $\mathbb{F}_2$ coboundary nilpotence and face curl calculation.
- Minimal Hamming defect search across all $2^3 = 8$ configurations.
- Near-miss rejection of flawed defect claims.
- Exact rational fraction parsing and Zero-Float enforcement.
- Duality gap certification over $\mathbb{Q}$.
- Rejection of float truncation and dual constraint violations.
- Unified runner execution.

---

## 5. Epistemic Hygiene Ledger (Claim Hygiene Rule)

| Dimension | Epistemic Assessment |
| :--- | :--- |
| **What this demo supports** | 1. Shows in this finite setting that non-zero face curl over $\mathbb{F}_2$ algebraically excludes uniform antiferromagnetic satisfaction by exact chain nilpotence $d_1 d_0 = 0 \pmod 2$.<br>2. Shows that exact rational primal-dual certificates certify optimal quotient defect mass $\Phi_1([c]) = 1$ in $\mathbb{Q}$ with zero duality gap without floating-point error.<br>3. Demonstrates deterministic rejection of floating-point rounding errors and infeasible dual vectors under the Zero-Float Law. |
| **What this demo does NOT support** | 1. Does **not** establish quantum spin-1/2 operators, Pauli algebra, continuous Hilbert spaces, or macroscopic thermodynamic spin-glass phase transitions.<br>2. Does **not** establish strong duality for infinite-dimensional Banach spaces or continuous differential forms.<br>3. Does **not** formalize the general $\ell^1 / \ell^\infty$ norm dual statement in Lean 4 (as fenced in `LpWeakDuality.lean`). |
| **Narrowest defensible claim** | On the finite 3-cycle complex, non-zero curl over $\mathbb{F}_2$ algebraically precludes $c = (1, 1, 1)^T \in \operatorname{im}(d_0)$ forcing $\ge 1$ frustrated bond, and the rational certificate pair $(\alpha^*, w^*)$ certifies in $\mathbb{Q}$ that the quotient defect mass is $\Phi_1([c]) = 1$. |
| **Next test needed** | Scale the exact rational certificate checker to multi-cycle cell complexes (planar triangular and kagome lattices with $b_1 \ge 2$) coupled to the Rust `omega_functional` exact dual simplex engine. |
