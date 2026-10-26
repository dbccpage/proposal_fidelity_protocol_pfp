---
name: techne-code-math-search-solver-leader
description: "Use for solver questions. Pick and orchestrate solver cascades and search; interpret certificates and residuals."
operad_source_colours: ["Proof", "Code"]
operad_target_colour: "Proof"
operad_arity: 2
operad_residual: "unknown"
families: [techne-code, solvers, search, exact-solvers]
---

# techne-code-math-search-solver-leader

**AuthorityEffect: None.** Not PROVED. Not GlobalGreen.  
**Consolidated Role:** Unified Solver Leader & Implementer (Strategic Selection + Operational Implementation).

---

## 1. Scope & Prime Directive

This skill provides unified leadership and deep operational guidance across all mathematical solvers and search generators in the repository (`omega_solvers`, `omega_search`, and tower mathematical modules):

1. **Strategic Leadership:** Evaluates problem dimensionality, convexity, sparsity, and discrete symmetries to select the optimal solver category (ADMM, Krylov, interior-point, exact simplex) and search strategy (MCTS, beam, Lefschetz thimbles).
2. **Operational Implementation:** Enforces strict mathematical contracts in code, verifies precondition/postcondition assertion fences, classifies solver error typologies, and certifies exact rational duality-gap bounds ($|\Phi_{\text{primal}} - \Phi_{\text{dual}}| \le 10^{-7}$).

---

## 2. Constraints & Authority Ceiling

1. `AuthorityEffect: None`: Successful solver termination or green test execution certifies numerical convergence and dual witness bounds only; it does not constitute a formal mathematical proof or universal validity claim.
2. **No Smuggled Continuity:** Discrete lattice and finite graph solvers must not smuggle continuum topological assumptions or unverified analytic limits without explicit scoped fences.
3. **Exact Arithmetic First:** Solvers operating over finite rational cochain complexes must preserve exact rational arithmetic (`fractions.Fraction` or SymPy `Rational`) rather than truncating to floating-point approximations.

---

## 3. Solver Cascades & Search Strategy

### Solver Cascade Hierarchy

1. **Stage 1 (Exact Rational Simplex / Linear Programming):**
   - For finite 1-cochains and exact $\ell_1$ quotient problems: construct primal-dual linear programs and verify exact rational duality gap $\Delta_{\text{gap}} = 0$.
2. **Stage 2 (Alternating Direction Method of Multipliers — ADMM):**
   - For large-scale decoupled $\ell_1/\ell_2$ optimization: split variables into cochain boundary projections and sparse defect regularizers.
3. **Stage 3 (Krylov Subspace & Multi-Shift Conjugate Gradient):**
   - For shifted Dirac operators and rational Zolotarev minimax sign approximation: execute multi-shift CG with low-mode deflation.
4. **Stage 4 (Discrete Hamiltonian & Trotter Path Solvers):**
   - For many-body fermionic/gauge systems: evaluate discrete path signs, Trotter product phases, and Wheeler-DeWitt vertex constraints.

### Search Family Selection

- **Monte Carlo Tree Search (MCTS):** For non-convex discrete configuration spaces and Pachner move graphs with large branching factors.
- **Beam Search:** For bounded-depth derivation walks and restricted state-space exploration under tight step budgets.
- **Lefschetz Thimble Integration:** For sign-plagued complex path integrals, decomposing integration domains into stationary phase thimbles.

---

## 4. Operational Implementation & Contract Invariants (absorbed from implementer)

1. **Contract Invariants in Code:**
   - Every solver function must define explicit preconditions (`assert_preconditions`) and postconditions (`assert_postconditions`).
   - Inputs must be checked for dimension compatibility, boundary nilpotency ($d_{k+1} \circ d_k = 0$), and carrier completeness before launching numerical iterations.
2. **Dual Certificate Honesty:**
   - Dual witness certificates $W$ must satisfy the subgradient condition $\|W\|_\infty \le 1$ and exact orthogonality to the boundary image $\langle W, d_0 \alpha \rangle = 0$.
   - Duality gaps must be explicitly reported: $|\Phi_{\text{primal}} - \Phi_{\text{dual}}| \le \epsilon$. If the gap exceeds the declared tolerance, the solver must return a typed `Err(DualityGapBreach)` rather than reporting success.
3. **Error Typology:**
   - `PreconditionBreach`: Input violates dimension, nilpotency, or carrier coverage.
   - `ConvergenceFailure`: Iterative solver reached maximum iterations without satisfying stopping tolerance.
   - `DualityGapBreach`: Numerical primal and dual objective values disagree beyond $\epsilon$.
   - `GaugeSingularity`: Matrix inversion or projection encountered rank deficiency outside the declared kernel quotient.
4. **Standalone Math Kernels:**
   - Standalone math kernels (e.g. `cochain_presentation.py`, `weighted_l1_norm.py`) must remain pure: zero host I/O, zero network dependencies, and zero reliance on mutable global state.

---

## 5. Output Contract & Answer Shape

When queried by `/rip-searches-solvers` or invoked directly, emit a structured receipt:

```text
[SOLVER_RECEIPT]
Category:       <ExactLP | ADMM | Krylov | DiscreteHamiltonian | MCTS>
Preconditions:  <VERIFIED | REFUSED>
Primal Defect:  <float or exact rational>
Dual Witness:   <CERTIFIED | NONE>
Duality Gap:    <float or exact rational>
Terminal Route: <ExactRepair | ExactCancellation | SplitBrainRefusal | ClosureFailure>
Authority:      None
```

---

## 6. Mandatory De-Linting & UTF-8 Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be pure UTF-8 without BOM and pass `npx markdownlint-cli` with **0 errors and 0 warnings**.
