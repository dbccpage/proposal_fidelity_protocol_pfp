# Degree-Wise DSL Lean 4 Formalization Estate

**Review scope (2026-09-30). Nonclaims:** This monograph assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing.

This directory contains the Lean 4 formalization estate for *Degree-Wise Obstruction Calculus and Symbolic DSL* (Paper FOC-006).

It establishes the complete formal verification baseline for:

1. Graded cochain complexes on $C_3$, discrete differential operators $d_0, d_1$, and nilpotency $d_1 \circ d_0 = 0$.
2. The declared $\Gamma_2$ readout gate: missing 2-cell yields undefined (`none`), not zero.
3. Declared projection contracts: idempotence and exact component annihilation.
4. Local-Green/Global-Red (LGGR) PrimitiveDifference non-factorization theorems:
   - $C^1$-local edge data does not determine global $\Gamma_2$ readout.
   - Diagnostic constructibility does not determine acceptance authority.
   - Composite degree/DSL local fingerprint does not determine the global gated readout.
   - External context extension does not repair the LGGR boundary.

## Modules

| File | Scope | Key Theorems | Axioms |
|---|---|---|---|
| `DegreeSeparation.lean` | Core formalization | `c3_d1_d0_zero`, `gamma2_graphOnly_undefined`, `gamma2_withTwoCell_one`, `declaredProjection_idempotent`, `declaredProjection_kills_exact`, `c1_local_green_not_gamma2_global`, `diagnostic_local_green_not_acceptance_authority`, `degreeDsl_local_green_not_global_gate`, `contextual_local_green_not_global_gate` | `{propext, Quot.sound}` |
| `Census.lean` | Axiom replay census | Replays all 19 declarations and verifies dependencies | `{propext, Quot.sound}` |

## Building

Requires Lean 4 (`v4.33.1`):

```bash
lake build
lake env lean Census.lean
```

Verification status:
- Offline clean build: PASS (0 errors, 0 warnings).
- Axiom honesty: strictly within `{propext, Quot.sound}`.
- Proof-placeholder commands: absent (`sorry`, `admit`, `unsafe` are 0).
