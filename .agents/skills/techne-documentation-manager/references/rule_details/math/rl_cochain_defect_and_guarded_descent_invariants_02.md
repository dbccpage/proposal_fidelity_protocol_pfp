# Detailed definition: Cochain Defect & Guarded Descent Invariants (2)

**AuthorityEffect:** None.

Parent: [Cochain Defect & Guarded Descent Invariants](../../../../../rules/math/rl_cochain_defect_and_guarded_descent_invariants.md). Load for the matching predicate, not every task.

## Observer-Robust Bundles, Joint Detector Adequacy & Degree Typing Invariant

> **Observer Bundle Adequacy, Degree Separation & Finite Arithmetic Gating:**
>
> 1. **Joint Detector Adequacy & Bounded Coordinate Diagnostics Invariant:**
>    - Evaluators operating over an observer bundle $\mathfrak{O}$ must never claim defect containment, non-tearing, or spoofing protection without an explicit Joint Detector Adequacy hypothesis: $\forall k < m, \, \exists \mathcal{O} \in \mathfrak{O} \text{ s.t. } w_k^{\mathcal{O}} > 0$.
>    - **Coordinate Defect Bounding Scope:** Joint Detector Adequacy ensures post-transition coordinate defects are bounded by initial observer budget: $w_k^{\mathcal{O}} \cdot |c'_k| \le \Phi_1^{\mathcal{O}}(c) + \varepsilon_{\mathcal{O}}$, preventing unmonitored defect explosions. Monograph claims must not assert defect transfer between monitored subcomplexes is impossible under aggregate descent: norm-reducing transfers are admitted unless governed by partition guardrails.
>    - **Shared Blind Subspaces:** If any coordinate is blind across all observers ($\forall \mathcal{O}, w_k^{\mathcal{O}} = 0$), claims must state that transfers into blind modes cannot be detected by bundle-relative evaluations.
> 2. **Fail-Closed Observer & Controller Parameter Validation:**
>    - `ObserverModel` implementations must validate in `__post_init__`: positive finite weights ($w > 0, \text{math.isfinite}(w)$), finite non-negative tolerances ($0 \le \varepsilon_{\mathcal{O}} < \infty$), finite coboundary matrices with exact dimension matching ($d_0: \text{len}(w_e) \times n, d_1: \text{len}(w_f) \times \text{len}(w_e)$), and valid projection indices $\pi_{\mathcal{O}}$.
>    - `ObserverRobustController` must validate $R_{\max} > 0, M_{\max} > 0, \Gamma_{\max} \ge 0, \delta_{\Gamma} \ge 0$, and $\lambda \ge 0$ are non-NaN real numbers fail-closed.
> 3. **Routing Objective & Subcomplex Projection API Fidelity:**
>    When an objective specifies multi-channel evaluation ($\Phi_{\mathrm{sat}}^{\mathcal{O}} + R_{cl}^{\mathcal{O}}$) and projection maps $\pi_{\mathcal{O}}$, the implementation must provide explicit API parameters (dedicated SAT channels and projection support) rather than undocumented heuristics.
> 4. **Structural Degree Typing for Boundary Diagnostics ($C^1$ vs. $C^2$):**
>    - Evaluators must strictly separate 1-cochains ($C^1$, edges) from 2-cochains ($C^2$, faces). Face boundary weights $\mathcal{W}_{2, \mathcal{O}}$ must match row dimension of $d_1 : C^1 \to C^2$ ($\dim C^2$) and never fall back to edge weights $\mathcal{W}_{1, \mathcal{O}}$.
>    - Evaluators must support directly evaluated 2-cochains of length $\dim C^2$ without requiring length parity with edge sets.
> 5. **Fail-Closed IEEE-754 Finite Validation & Empty Bundle Refusal:**
>    - Evaluators must validate all cochains, diagnostics, and costs are finite real numbers (`math.isfinite(x)`); `NaN` and infinite inputs must fail closed (`status = "RefusedStalled"` or exception).
>    - Observer bundles must enforce non-empty initialization (`len(observers) >= 1`); empty bundles must emit a typed refusal rather than vacuously admitting candidates.
> 6. **Quotient Solver vs. Certified Residual Precondition Discipline:**
>    Functions summing weighted coordinates compute an $\ell^1$ norm, not a quotient obstruction norm $\Phi_1 = \min_\alpha \|\omega - d_0 \alpha\|_1$. A function evaluates $\Phi_1$ only if it executes coboundary quotient minimization (e.g. exact LP) or if the cochain is certified as an optimal residual.
