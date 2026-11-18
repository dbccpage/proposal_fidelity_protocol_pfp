# Detailed definition: Cochain Defect & Guarded Descent Invariants (1)

**AuthorityEffect:** None.

Parent: [Cochain Defect & Guarded Descent Invariants](../../../../../rules/math/rl_cochain_defect_and_guarded_descent_invariants.md). Load for the matching predicate, not every task.

# Rule: Cochain Defect Compatibility, Guarded Descent & Cochain Bridges

**AuthorityEffect:** None.

This rule codifies multi-channel obstruction compatibility, guarded descent lexicographic dominance, constructive guard factorization, typed cochain bridges, and observer-robust bundle adequacy. Cross-reference exact verifier foundations: [`rl_exact_verification_and_witness_integrity_invariants.md`](../../../../../rules/math/rl_exact_verification_and_witness_integrity_invariants.md).

---

## Multi-Channel Obstruction Algebraic Compatibility & Cochain Defect Invariant

> **Algebraic Channel Compatibility & Fail-Closed Defect Validation:**
>
> 1. **Curvature-Forced Obstruction Floor ($\Gamma_2 > 0 \implies \Phi_1 > 0$):**
>    - In complexes $(C^\bullet, d)$ with $d^1 d^0 = 0$, curvature $\kappa = d^1 \omega$ is invariant under gauge shifts: $\Gamma_2(\omega) \le \|d^1\|_{1 \to 1} \Phi_1([\omega])$ and $\Phi_1([\omega]) \ge \Psi(d^1 \omega) := \min \{ \|r\|_1 : d^1 r = d^1 \omega \}$.
>    - Non-zero curvature ($\kappa \ne 0$) strictly forces $\Phi_1([\omega]) > 0$.
> 2. **Impossible Cochain State Rejection in Value Objects & Test Fixtures:**
>    - Value objects (`CochainDefect`) and evaluators must validate compatibility in `__post_init__`/gates: $\Phi_1 = 0 \land \Gamma_2 > 0$ is algebraically impossible and must fail closed (`ValueError` or typed refusal).
>    - Test suites and fixtures must never hardcode decoupled $(\Phi_1 = 0, \Gamma_2 > 0)$ as admitted test cases. Tests must compute values from verified cochain data.
>    - **Chain Complex Bound & Zero Cochains:** In any complex with $d^1 d^0 = 0$, $\Gamma_2(\omega) \le \|d^1\|_{1\to 1} \Phi_1([\omega])$; exact $\Phi_1 = 0 \implies \Gamma_2 = 0$. Fixtures with $\Phi_1 = 0 \land \Gamma_2 > 0$ model numerical threshold bounds, not realizable exact cochains. Pipelines must branch natively on zero cochains ($\Phi_1 = 0, \Gamma_2 = 0$) at the boundary before invoking density operators undefined for zero mass.
> 3. **Topological Invariant on Simplicial Survivors:**
>    - Survivor criterion ($\Phi_1 > 0 \land \Gamma_2 = 0$) satisfies $\dim \operatorname{span}\{\text{survivors}\} = \beta_1(K)$.
>    - On 1-acyclic complexes ($\beta_1(K) = 0$), all closed cocycles satisfy $\Phi_1 = 0$; survivors are topologically excluded. Empirical survivor certificates must verify $\beta_1(K) > 0$.

---

## Guarded Descent Evaluator, Global Ranking & Exact Boundary Ratio Invariant

> **Exact Piecewise Closure Ratio, Global $\varepsilon$-Optimal Ranking & Refusal Taxonomy:**
>
> 1. **Strict Lexicographic Metric Priority ($\Phi_1 \succ \Gamma_2 \succ \Xi$):**
>    - In guarded descent over discrete simplicial or cochain complexes, operator trace metrics ($\Xi$) must never supersede topological quotient residuals ($\Phi_1$) or boundary defects ($\Gamma_2$).
>    - Candidate selection must enforce strict lexicographic priority:
>      a. Primary: Minimization and non-increase in 1-cell quotient residual ($\Phi_1$).
>      b. Secondary: Minimization of 2-cell boundary defect ($\Gamma_2 = \|d_1 \omega\|_1$) when $\Phi_1$ is tied.
>      c. Tertiary: Minimization of operator trace metric distance ($\Xi$) only when both $\Phi_1$ and $\Gamma_2$ are tied.
>      d. Metric Triangle Inequality: Metrics (e.g. $\Xi$) must never apply step-function cutoffs on near-identity overlaps ($|\langle a, b \rangle| \ge 1 - 10^{-14} \to 0$), which collapses open metric balls and violates $\Xi(A, C) \le \Xi(A, B) + \Xi(B, C)$. Implementations must use stable product forms ($\Xi(a, b) = \frac{1}{2} \|a - b\|_2 \|a + b\|_2$).
> 2. **Exact Piecewise Closure Ratio ($R_{cl}$):**
>    Defined piecewise without relaxation: $R_{cl}(S) = 0$ if $\Phi_1 = \Gamma_2 = 0$; $\Gamma_2/\Phi_1$ if $\Phi_1 > 0$; $+\infty$ if $\Phi_1 = 0 \land \Gamma_2 > 0$. Threshold $R_{cl} \le R_{\max}$ is an exact hard boundary. Signatures with $\Phi_1 = 0 \land \Gamma_2 > 0$ cannot arise from valid cochains and fail closed. Guardrails must execute with identical priority across `evaluate_transition`, `compare_candidates`, and `rank_candidates`. Early descent acceptance must not bypass guardrails that fail closed in comparison. Compound states must validate algebraic consistency among $\Phi_1$, $\Gamma_2$, and $R_{cl}$.
> 3. **Guarded Descent Literal Non-Increase:**
>    Guarded descent enforces $\Phi_{\mathrm{geom}}(o(S_t)) \le \Phi_{\mathrm{geom}}(S_t)$ with zero additive $\varepsilon$-slack.
> 4. **Global Set-Based $\varepsilon$-Optimal Ranking Policy:**
>    To eliminate pairwise cyclic preferences:
>    a. Find minimal score $F_{\min} = \min_{o \in \text{Admissible}} F_{\mathrm{discrete}}(o)$.
>    b. Form $\varepsilon$-optimal set $\mathcal{C}_\varepsilon = \{ o : F_{\mathrm{discrete}}(o) \le F_{\min} + \varepsilon \}$.
>    c. Find minimal trace metric $\Xi_{\min} = \min_{o \in \mathcal{C}_\varepsilon} \Xi(o)$ and tie-break set $\mathcal{T}_\varepsilon = \{ o \in \mathcal{C}_\varepsilon : \Xi(o) \le \Xi_{\min} + \varepsilon \}$.
>    d. Deterministic tie-breaking on $\mathcal{T}_\varepsilon$ (smaller $F_{\mathrm{discrete}}$, then smaller $\Xi$, then catalog order). Outside the $\varepsilon$-band, $\Xi$ cannot override discrete defect.
>    e. **Pairwise $\varepsilon$-Equivalence Ban & Strict Transitivity:** Pairwise $\varepsilon$-proximity is not an equivalence relation. Comparators must never treat $\varepsilon$-ties as equivalence to unlock secondary criteria, which admits cycles ($A \succ B \succ C \succ A$). Comparators must evaluate exact lexicographic order or return explicit unresolved outcomes. Ranking functions must sort candidates rather than returning input order.
> 5. **Four-Class Typed Refusal Taxonomy:**
>    Controllers emit typed refusal records: `RefusedTearing` ($R_{cl} > R_{\max}$), `RefusedDescentViolation` ($\Phi_{\mathrm{geom}}' > \Phi_{\mathrm{geom}}$), `RefusedInvalidInput` (non-finite or contradictory), `RefusedStalled` (empty/mixed violations).
> 6. **Antipodal Fiber Blindness & Topological Orientation:**
>    - The rank-one density lift $v \mapsto \rho = v v^T / \text{Tr}(v v^T)$ is even: $\Xi(v, -v) = 0$. Reversing edge flow negates circulation ($\oint (-v) = -\oint v$); spectral trace distance is blind to orientation reversals.
>    - Direct density matrix reconstruction recovers only the unoriented pair $\{ \pm v \}$. Signed cochains require discrete boundary verification or explicit orientation witnesses.
> 7. **Executable Evaluator Prerequisite:**
>    Descent ordering claims must never be classified `[VERIFIED]` on derivation alone; verification requires an executable evaluator with integration tests over discrete cell complexes.

---

## Constructive Guard Factorization & Typed Cochain Bridge Invariant

> **Guard Factorization & Typed Component Bridge Rule:**
>
> 1. **Constructor Proof Binding for Guarded Evidence:**
>    In formal proof kernels (Lean 4) and verifiers, authority records ($\mathsf{IsAuth}_S$) must require proof of guard conjunction satisfaction (`AllGuardsPass guards`) directly within the type constructor. Purported authority tokens without constructor-bound guard proofs are invalid.
> 2. **Operational Guard Factorization:**
>    Verification engines must formally prove the Guard Factorization Theorem: operational authority ($\mathsf{IsAuth}_S$) factors through structural coproduct membership ($\mathsf{IsGuardedAuth}$).
> 3. **Typed Component Bridge for Cochain Obstructions:**
>    When bridging discrete diagnostic cochain complexes ($C^0, C^1, d^0$) and quotient spaces ($Q^1 = C^1 / \operatorname{im} d^0$) to authority routes:
>    - Non-repairable obstructions ($[c] \neq 0 \in Q^1$) map strictly to diagnostic residual terminals in the coproduct summand (`Sum.inr`).
>    - Systems must verify constructor image mutual exclusion (`diagnosticRoute ≠ authorityRoute`) and absence of authority.
>    - Truthful delta guards (`deltaZero = true → IsCoboundary c`) must be proven to strictly falsify all-guards conjunction when non-repairable obstructions exist.

---
