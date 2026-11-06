# Evidence scope for Degree-Wise Obstruction Calculus and Symbolic DSL

**Review scope (2026-09-30). Nonclaims: This monograph assigns no authorization and changes no jurisdiction.**

The degree-wise obstruction calculus formalizes graded cochain complexes and degree separation over finite simplicial carriers. The Lean 4 mechanized formalization establishes degree separation on $C_3$, discrete boundary nilpotency $d_1 \circ d_0 = 0$, and local-global gate non-factorization under `PrimitiveDifference` quotients.

The Python implementation in `code/mod_004_degree_wise_dsl_core.py` provides exact rational arithmetic for cochains, coboundary evaluations, degree separation witnesses, and guarded descent evaluators tested across 21 unit tests.

Explicit exclusions:
1. Operator dynamics or transport proposals are excluded (deferred to Paper 011).
2. Trace metrics, density lifts, or Hilbert spaces are declared as boundary slots but not constructed (deferred to Paper 013).
3. No physical interpretation, continuum limits, or empirical claims regarding real neural models are made.
4. No authority, acceptance, correctness, or semantic-truth claim is assigned. Authority status is strictly None.
5. Probability semantics are excluded; aggregation is strictly finite weighted $\ell^1$ tallies.
6. Quantum-cohomology admission classification or classical/quantum non-selection is excluded (deferred to QM_032).
