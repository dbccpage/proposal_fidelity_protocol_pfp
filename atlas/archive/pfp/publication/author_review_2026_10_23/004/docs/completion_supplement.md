# Mathematical note: a weighted directed cycle

Jeremy H. Carroll · 2026-09-28 · Supplement to PFP IV, version 2.8.0

This note supplies a small hand calculation used to interpret the graph adapter.
The [main paper](../paper.md) is the complete systems manuscript. This
calculation is mathematical evidence, not a second executable Phi1
implementation or a fresh native test receipt.

Take a directed cycle with at least three edges, rational claims w_i, and
positive rational penalties a_i. Set h = sum(w_i) and rho = min(a_i).
For potentials f define residuals r_i = w_i - (f_(i+1)-f_i). Then

```text
min_f sum_i a_i |r_i| = rho |h|.
```

Telescoping gives sum(r_i)=h. Positivity and the triangle inequality imply
sum(a_i |r_i|) >= rho sum(|r_i|) >= rho |h|. Choose a minimum-penalty edge j,
set r_j=h, and set all other residuals to zero. The repaired edge values w_i-r_i
sum to zero, so partial sums from a fixed initial potential construct a closing
potential attaining the bound.

With nonzero h and a unique minimum-penalty edge, the projected edge cochain is
unique; potentials retain an additive constant. Tied minimum penalties allow
same-sign distributions of h across the tied edges. A deterministic tie rule
selects one optimum without adding physical significance.

| Claims | Penalties | Minimum |
| --- | --- | --- |
| (1,1,1) | (1,2,2) | 3, attained by projected claims (-2,1,1) |
| (1,1,0) | (1,1,1) | 2; modulo-2 parity and additive exactness differ |
| (1,-1,0) | (1,1,1) | 0 |

The first row is the historical operator fixture. The series' shared foundation
example instead uses penalties (1,2,3); its minimum is also 3, but its
zero-potential cost is 6 instead of 5.

A CUT replacing the declared claims changes the problem's data. It cannot
establish that immutable external observations were wrong. The package
governor accepts such a CUT only when it supplies one exact value for every
declared edge; a proposal that omits an edge is refused, not scored as if the
omitted claim were zero. The quotient minimum also differs from the residual
evaluated at an arbitrary chosen potential.

The package's legacy wrappers `solve_phi1_lp_exact_basis` (in
`code/scaling_benchmark_v20.py`) and `compute_phi1` (in
`code/l1_symbol_game_governor.py`) are one computation: the first calls the
second. At the pinned source baseline, `compute_phi1` delegated to the pinned
native graph calculator only. The package copy later gained a fallback that
computed the minimum in Python whenever the native call raised, including for
native input refusals. This revision narrows it: the governor calls the native
calculator only when `CORE_FUNCTIONAL_GRAPH_BIN` is set and then lets every
native refusal or error propagate; without that setting it computes the minimum
by exact enumeration of spanning-tree potentials. Both paths refuse floating-point and
Boolean edge weights. The package tests therefore exercise the Python enumeration unless
a native executable is configured. Comparing the two wrappers is API compatibility, not independent
solver agreement. The old scaling benchmark has an explicit retirement
boundary. Neither historical timing nor a Lean filename establishes a general
complexity or matrix-integrality theorem.
