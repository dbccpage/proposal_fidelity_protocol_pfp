---
documentation_contract: symbol-game-documentation/v1
title: 'Chapter 03: Obstruction Mass, Duality, and Exact Linear Programming'
kind: mathematical-reference
audience:
- researchers
- optimization-engineers
- coding-agents
status: active
maturity: canonical
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - l1_quotient_obstruction_mass
    - closure_diagnostic_gamma2
    - stabilized_survivor_condition
    - dual_witness_certificate
    - declared_exact_certified_scalar_law
  prose_theorems:
    - weak_lp_duality_bound
    - three_condition_optimality_certification
  lean_theorems: []
  lean_statements_not_typechecked:
    - PaperER007.lp_max_form_weak_duality
  finite_computations:
    - three_cycle_dual_witness_example
  declared_policies:
    - exact_rational_certificate_verification
  applications: []
  open_conjectures: []
coefficient_domain: "Declared Exact Scalars (Specializing to ℚ)"
runtime_dependency: "Chapter 02 (Cochain Complexes, Repairs, and Quotients)"
governance_dependency: "None"
---

# Chapter 03: Obstruction Mass, Duality, and Exact Linear Programming

**Status:** Canonical Mathematics Specification (Spine Chapter 03)  
**Authority:** None. Convex polyhedral analysis, linear programming duality, and certified exact rational arithmetic.  
**Lean 4 Reference:** `PaperER007.lp_max_form_weak_duality` in [`lean4/LpWeakDuality.lean`](../../../../lean4/LpWeakDuality.lean). Rechecked 2026-10-22 at `305b9690f9`: the file's own header still says it does not elaborate on the v4.34.0 package, which has no Mathlib, and that its declarations were not typechecked against the pinned Mathlib on v4.33.1. It is not a root of [`lean4/lakefile.lean`](../../../../lean4/lakefile.lean). Treat it as a source-visible Lean statement, not a mechanized result. The same reading was recorded on 2026-10-20 at `c419cc6beb`.

## Listen, then watch

Read this block before the general formula. It was not recorded on 2026-10-22. AuthorityEffect: None. The same triangle is computed again, with the dual conditions named, in section 3.2.

**Plain opening.** On a triangle, three measured edge values of 1 cannot all be height differences. The smallest leftover, adding absolute values, is 3.

**Terms at first use.** A height list is a potential. "D zero" turns heights into edge differences. The residual is the measurement minus those differences. The ell-one norm adds absolute values. Phi, said "phi", is the smallest such norm. A dual witness is a list of edge weights that balances at every corner and stays within the weight limit. Its pairing with the measurements is a lower bound.

**One number before the general case.** Orient the triangle a to b, b to c, and c to a. Measure x as 1, 1, 1. Heights 0, 1 and 2 give differences 1, 1 and minus 2. The residual is 0, 0, 3. The norm is 3. Weights 1, 1, 1 balance, because each corner has one incoming 1 and one outgoing 1, and they pair with the measurements to 3. The lower bound meets the leftover, so phi is 3. The general statement, in section 3, replaces this one triangle by any finite complex and any positive rational edge weights.

**A check you can fail.** Weights 1, 0, 0 pair with the measurements to 1, which is positive. They do not balance: the first corner loses 1 and the second corner gains 1. If you treat the pairing 1 as a proof that phi is at least 1, the check fails. Balance is required.

**Spoken segment.** Duration: 40 seconds. One idea: the all-ones weights show that the leftover cannot be smaller than 3.

> Measure one, one and one around the triangle. Heights zero, one and two explain the first two edges and miss the third by three. The leftover norm is three. Weights one, one and one balance at every corner, and one plus one plus one is three. So three is the smallest leftover. A weight list that does not balance does not prove a lower bound, even when its pairing is positive.

**Check with no screen.** What is one plus one plus one on this triangle? If you said zero, you were thinking of height-made slopes, which do sum to zero. These measurements sum to three. The leftover is three.

**Video beats.**

| Time | On screen | Narration |
| --- | --- | --- |
| 0:00–0:10 | measure 1, 1, 1 | "Three edges, each measured one." |
| 0:10–0:22 | heights 0, 1, 2 | "Heights zero, one, two. Differences one, one, minus two." |
| 0:22–0:32 | leftover 0, 0, 3 | "The leftover is zero, zero, three. The absolute sum is three." |
| 0:32–0:45 | weights 1, 1, 1 | "Weights one, one, one balance. Their pairing is three. Three is optimal." |
| 0:45–0:55 | 1, 0, 0 fails | "Weights one, zero, zero do not balance. Their pairing is not a proof." |

---

## 1. Measuring Obstruction: The $\ell^1$ Quotient Mass $\Phi_n$

In Chapter 02, an edge cochain $x \in C^1_n$ was evaluated modulo the subspace of exact repairs $B^1_n = \operatorname{im}(d_{0,n})$.  
To quantify the severity of an un-repaired cochain, we measure its minimal weighted distance to the exact repair subspace:

$$\Phi_n([x]) = \inf_{\alpha \in C^0_n} \|x - d_{0,n}\alpha\|_{1, \omega_n} = \inf_{\alpha \in C^0_n} \sum_{e \in E_n} \omega_e |x(e) - (d_{0,n}\alpha)(e)|$$

where $\omega_n \in \mathbb{Q}_{>0}^{E_n}$ is an explicit, positive rational edge-weight vector. The weighted $\ell^1$-norm is selected because discrete edge differences and traversal costs accumulate additively across cells.

### 1.1 Interpretation of $\Phi_n$
- **$\Phi_n([x]) = 0$:** The cochain is exact ($x \in \operatorname{im}(d_{0,n})$). A vertex potential assignment exists that completely eliminates the observed differences.
- **$\Phi_n([x]) > 0$:** The cochain carries an unavoidable, positive obstruction mass that cannot be absorbed by any vertex gauge adjustment.

---

## 2. The Closure Diagnostic $\Gamma_2$ and Stabilized Survivors

A cochain may also possess a boundary on higher cells. When declared 2-cells are present with coboundary operator $d_{1,n}: C^1_n \to C^2_n$, we define the **closure diagnostic**:

$$\Gamma_2(h) = \|d_{1,n} h\|$$

- **$\Gamma_2(h) = 0$:** The cochain $h$ is a **cocycle** ($h \in \ker(d_{1,n})$). Its boundary closes upon itself without leaking into 2-cells.
- **$\Gamma_2(h) > 0$:** The defect has a non-vanishing boundary on declared faces.

### 2.1 The Stabilized Survivor

Combining $\Phi_n$ and $\Gamma_2$ identifies non-trivial elements of discrete cohomology:

$$\boxed{\text{A quotient class } [h] \in Q^1_n \text{ is a \textbf{Stabilized Survivor} if: } \Phi_n([h]) > 0 \quad \text{and} \quad \Gamma_2(h) = 0}$$

A stabilized survivor represents an element of non-trivial 1-cohomology:
$$H^1_n = \ker(d_{1,n}) / \operatorname{im}(d_{0,n})$$
It cannot be repaired locally by 0-cochains ($\Phi_n > 0$) and does not leak into declared 2-cells ($\Gamma_2 = 0$).

---

## 3. Dual Certificates of Non-Erasure

How does a computational engine prove to an independent verifier that $\Phi_n([x]) > 0$ without forcing the verifier to re-run an optimization search?

An algorithm failing to find a repair $\alpha$ does **not** prove that no repair exists; it may have timed out or failed numerically. Instead, mathematical proof of non-erasure is provided by **exact dual certificates**.

### 3.1 Linear Programming Duality Formulation

The primal minimization problem:
$$\Phi_n([x]) = \inf_{\alpha \in C^0_n} \|x - d_{0,n}\alpha\|_{1,\omega_n}$$
has the exact dual formulation over the linear dual space $(C^1_n)^*$:

$$\Phi_n([x]) = \max_{\substack{y \in (C^1_n)^* \\ |y_e| \le \omega_e \; \forall e \in E_n \\ d_{0,n}^* y = 0}} \langle y, x \rangle$$

where $d_{0,n}^*: (C^1_n)^* \to (C^0_n)^*$ is the adjoint divergence operator, enforcing circulation flow conservation at every vertex:
$$(d_{0,n}^* y)(v) = \sum_{u: (u, v) \in E_n} y_{(u, v)} - \sum_{w: (v, w) \in E_n} y_{(v, w)} = 0 \quad \forall v \in V_n$$

### 3.2 Dual Witness Verification

A vector $y^* \in (C^1_n)^*$ is a **certified dual witness** of non-erasure for $x$ if it satisfies three finite linear conditions:
1. **Divergence Conservation:** $d_{0,n}^* y^* = 0$ (orthogonal to all vertex coboundaries),
2. **Coordinatewise Capacity Feasibility:** $|y_e^*| \le \omega_e$ for all $e \in E_n$,
3. **Strictly Positive Pairing:** $\langle y^*, x \rangle = \sum_{e \in E_n} y_e^* x_e = \gamma > 0$.

By weak linear programming duality, checking these three conditions verifies:
$$\Phi_n([x]) \ge \langle y^*, x \rangle = \gamma > 0$$
The verifier needs only to perform finite matrix-vector multiplications to verify the certificate.

**Why the inequality holds (one line).** For any $\alpha$, $\langle y^*, x \rangle = \langle y^*, x - d_{0,n}\alpha \rangle + \langle d_{0,n}^* y^*, \alpha \rangle = \langle y^*, x - d_{0,n}\alpha \rangle \le \sum_e |y^*_e|\,|x_e - (d_{0,n}\alpha)_e| \le \sum_e \omega_e |x_e - (d_{0,n}\alpha)_e|$. Take the minimum over $\alpha$.

**Worked example (2026-10-20).** Take the oriented 3-cycle $a \to b \to c \to a$ with unit weights and $x = (1, 1, 1)$.

1. Divergence: on a cycle, $d_0^* y = 0$ forces $y_1 = y_2 = y_3$, so try $y^* = (1, 1, 1)$. Each vertex has one incoming and one outgoing edge with value 1, so the divergence is $1 - 1 = 0$ at every vertex.
2. Capacity: $|y^*_e| = 1 \le 1 = \omega_e$.
3. Pairing: $\langle y^*, x \rangle = 1 + 1 + 1 = 3 > 0$.

So $\Phi([x]) \ge 3$. The potential $\alpha = (0, 1, 2)$ on $(a, b, c)$ gives $d_0\alpha = (1, 1, -2)$ and residual $x - d_0\alpha = (0, 0, 3)$ with norm 3, so the lower bound is attained and $\Phi([x]) = 3$. A four-edge version with a declared face is worked in [the C4 supplement](10_finite_qm_certificate_scope.md).

---

## 4. The Declared Exact / Certified Scalar Law

The epistemic boundary between candidate exploration and verified admission is governed by scalar discipline:

> **Declared Exact / Certified Scalar Law:**  
> Heuristic or approximate numerical algorithms (e.g. IEEE-754 floating-point simplex, interior point methods, subgradient heuristics) are permitted to propose candidate vectors $x^*$ and dual witnesses $y^*$. However, **all certificate admissions must be verified strictly over declared exact or certified scalar systems**:
> 1. Exact rational arithmetic over $\mathbb{Q}$,
> 2. Certified algebraic number extensions $\mathbb{Q}(\alpha)$,
> 3. Certified rational interval arithmetic $\operatorname{Interval}[\mathbb{Q}]$.
>
> *Specialization:* The present $\ell^1$ linear programming certificate implementation specializes strictly to the rational field $\mathbb{Q}$.

### 4.1 Hazards of Floating-Point Tolerances
1. **False Zero Laundering:** Machine precision roundoff can map non-zero coboundary discrepancies $\|d_0 \alpha - x\| > 0$ to $0.0$, falsely certifying invalid repairs.
2. **Subgradient Stalling:** Floating-point tolerances can cycle indefinitely or prematurely terminate on polyhedral corners without reaching a valid extremal vertex.

---

## 5. The Three-Condition Optimality Requirement

A central lesson of linear optimization certification is:

$$\boxed{\text{Objective equality is insufficient without primal and dual feasibility independently verified.}}$$

A candidate pair $(x^*, y^*)$ certifies exact optimality for an LP problem ($\min c^T x$ subject to $A x \ge b, x \ge 0$) in $\mathbb{Q}$ **if and only if all three of the following conditions are independently checked in exact arithmetic**:

1. **Primal Feasibility:** $A x^* \ge b$ and $x^* \ge 0$ in $\mathbb{Q}$,
2. **Dual Feasibility:** $A^T y^* \le c$ and $y^* \ge 0$ in $\mathbb{Q}$,
3. **Zero Duality Gap:** $c^T x^* - b^T y^* = 0$ in $\mathbb{Q}$.

> **Critical Logical Requirement:**  
> Zero duality gap certifies optimality *only after* both primal and dual feasibility conditions have been checked. Two infeasible vectors can accidentally satisfy $c^T x = b^T y$ without either being an optimizer or even lying inside the feasible polyhedron.

---

## 6. Formal Mechanization in Lean 4

Weak duality for maximum-form linear programming is stated over arbitrary linearly ordered fields in [`lean4/LpWeakDuality.lean`](../../../../lean4/LpWeakDuality.lean). That file has not been typechecked (its own header, read 2026-10-20), so the entries below describe a Lean statement, not a checked proof:

- **Mechanized Theorem:** `PaperER007.lp_max_form_weak_duality`
- **Hypotheses:** Over any linearly ordered field $K$ (including $\mathbb{Q}$):
  - Primal feasibility: $A *_{\mathsf{v}} x \le b$ and $0 \le x$
  - Dual feasibility: $c \le A^T *_{\mathsf{v}} y$ and $0 \le y$
- **Conclusion:** $c \cdot x \le b \cdot y$
- **Explicit Scope Fence:** As declared in `LpWeakDuality.lean`, this theorem states weak duality for the maximum-form LP convention by finite algebraic rearrangement. Strong duality (the existence of an optimizer achieving equality) and the norm-pairing $\ell^1 / \ell^\infty$ duality for cochains are distinct mathematical claims requiring explicit hypotheses.
