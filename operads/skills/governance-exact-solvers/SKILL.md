---
name: governance-exact-solvers
description: "Consolidated exact rational arithmetic, discrete Hamiltonian solver, and finite operational closure gate."
operad_source_colours: ["Code", "Proof"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: neutral
families: [governance, exact-math]
---

# governance-exact-solvers

AuthorityEffect: None.

## The single rule

> Discrete Hamiltonian and constraint solvers must execute rational sums by exact stepwise GCD-reduced folding rather than pairwise self-joins or floating-point approximations, while strictly adhering to finite operational closure laws.

> **Procedural Reference:** Detailed checklists and implementations for Python strict boolean validation, SQL null-totality (`IS DISTINCT FROM`), exact residual vanishing, and candidate set exhaustiveness reside in [`references/relational_math_discipline.md`](references/relational_math_discipline.md).

## Consolidated Invariants

1. **Exact Rational Folding**: Solvers decide rational sums by exact stepwise GCD-reduced folding; floating-point comparisons in discrete decision paths are strictly prohibited (`goo-exact-rational-hamiltonian-solver-gate`, `goo-exact-rational-fold-gate`, `goo-exact-gaussian-rational-arithmetic-guard`).
2. **Five-Way Finiteness Taxonomy**: Enforce distinct conceptual boundaries across the 5 meanings of finiteness in quantum foundations to prevent cross-domain no-go overclaims (`goo-five-way-finiteness-taxonomy-guard`).
3. **Finite Operational Closure**: Audit operational closure at its declared system class, preserving unresolved evidence and distinguishing raw cochain variation from quotient residual distance (`goo-finite-operational-closure-gate`, `goo-quotient-residual-cycle-closure-gate`).
4. **Isomorphism & Transport Bounds**: Representation transport models must implement verifiable round-trip isomorphism laws and polynomial size bounds (`goo-pea-representation-transport-pricing-gate`, `goo-residual-projection-obstruction-solver-suite`).
5. **Executable Research Dossier Specification**: Mathematical claims in research preprints must be backed by a hermetic 6-artifact dossier (`claim.md`, `input.yaml`, `witness_valid.json`, `witness_near_miss.json`, `checker.py`, `checker_output.json`, and `claim_ledger.json`) with an explicit 4-part Claim Hygiene ledger (what it supports, what it does not support, narrowest defensible claim, next test needed).
6. **Zero-Float Law & Duality Feasibility Precondition**: Exact linear programming duality checkers must parse floats to exact rationals in $\mathbb{Q}$ and reject precision leakage. Zero duality gap certifies optimality only after independent verification of primal feasibility, divergence balance ($d_0^T w = 0$), and dual box capacity constraints ($\|w\|_\infty \le 1$). Numerical equality between primal candidate values and dual dot products without flow balance verification is strictly rejected (the Triangle Counterexample). Furthermore, strict rational descent alone does not imply finite termination ($D_t = 2^{-t}$ strictly decreases in $\mathbb{Q}^+$ forever without reaching 0); solvers must bound operation counts ($\#\mathrm{ops} \le \lfloor B_{\mathrm{tot}} / \delta_{\mathrm{control}} \rfloor$) and enforce per-attempt fuel and timeouts.
7. **Strict Rust Delegation & Anti-Ad-Hoc Python Math Gate**: Mathematical solvers in `challenges/` and `pfp` are strictly prohibited from implementing ad-hoc Python Gaussian elimination, row-reduction, Smith normal form loops, or cycle basis solvers. All exact arithmetic, reductions, and invariant factor extractions must delegate to `core_linear_algebra`, `core_homology`, `core_holonomy`, `core_solvers`, or `core_search` via `RustSymbolGameHost`.
8. **Problem-Bound Terminal Verification**: Terminal route dispatchers (`terminal_route`) must never accept `ExactRepair` based solely on internal certificate attributes. Routing strictly requires problem data binding (either an active registry or explicit problem inputs), input digest matching, direct verification of the exact repair equation ($x + d_0 f = 0$ with residual $= 0$), verification of the boundary certificate, and independent recomputation of diagnosis against problem data. Missing problem data or unverified equations must fail closed to `TerminalRoute.OPEN_OBSTRUCTION`.
9. **Matrix-to-Vector Shape Purity & Non-Fabrication**: Vector conversion routines (`_exact_vector`) must never convert empty matrices with zero columns and more than one row (e.g. SymPy `Matrix.zeros(n, 0)` with $n > 1$, or NumPy `zeros((n, 0))`) into fabricated zero vectors. Malformed matrices with zero columns and $n > 1$ rows must raise `ValueError`. Only true 0-dimensional carriers (`(0, 0)`, `(0, 1)`, `(1, 0)`) may normalize to empty vector shapes `(0, 1)`.
10. **Spanning Forest Basis for Exact $\ell^1$ Cochain Minimization**: In discrete cochain optimization $\Phi_1(\omega) = \min_{\varphi} \|\omega - d^0 \varphi\|_1$, compactness of the real extension guarantees attainment of a minimum. The objective is piecewise linear on polyhedral regions, ensuring an optimum is attained at an extreme vertex where residual errors vanish on a spanning forest. Because incidence matrices are totally unimodular, the optimum is strictly rational and solvable exactly over $\mathbb{Q}$ without floating-point approximations.

## Verification Requirements

Run the exact solver arithmetic check:

```bash
python operads/skills/governance-exact-solvers/scripts/check_exact_solvers.py
```
