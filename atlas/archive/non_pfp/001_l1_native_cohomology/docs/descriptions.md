# Scientific Description: ℓ¹-Native Cohomology of Finite Defect Fields

## Overview
This deposit contains the complete, self-contained research package for "ℓ¹-Native Cohomology of Finite Defect Fields: Quotient Norms, Dual Circulations, Sparse Representatives, and the L^p Geometric Family", authored by Jeremy H. Carroll.

For a finite directed graph or 2-simplicial complex equipped with strictly positive edge weights, we formulate and study the family of weighted L^p norms (p in [1, ∞), with a separately weighted Chebyshev endpoint at ∞) induced on the first cochain quotient space Q¹ = C¹ / im(d₀). Under this formulation:
- For every p in [1, ∞], the quotient infimum is attained by an exact finite minimizer and defines a legitimate quotient norm Φ_p on Q¹.
- Strong Fenchel-Rockafellar duality holds across all p, pairing primal potential adjustments with dual divergence-free circulations.
- In the polyhedral base case p = 1, primal-dual solutions are computed via two-phase simplex with Bland's pivot rule over the field of rational numbers Q, attaining exact integer certificates when edge capacities and boundary data are integral.
- In the strictly convex regime p in (1, ∞), the potential is unique up to connected-component gauge shifts, solving the nonlinear graph p-Laplacian.
- Discrete physics: on 2-simplicial complexes, coboundary nilpotency d₁ ∘ d₀ = 0 enforces discrete Bianchi identity conservation, while off-diagonal quantum state coherence is bounded under Schatten trace norms and additive real flux is distinguished from U(1) phase holonomy.

The general attainment, quotient-norm, Fenchel-Rockafellar, uniform-convexity, Moore-Penrose, Chebyshev, entropy-selection, total-unimodularity, and Schatten sentences above are classical background. Their proofs are supplied in the manuscript. Lean separately mechanizes the conditional finite integer certificate and the specified finite-model lemmas; it does not establish certificate existence or Python implementation correctness.

## Verification & Artifacts
The package contains:
1. Publication monograph in Markdown, compiled XeLaTeX, and vector PDF formats.
2. Verified Python implementation with exact rational arithmetic (fractions.Fraction) closed under Q for polyhedral and certificate decision paths (p = 1, 2, ∞), two-phase simplex solver, and binary64 solvers for continuous Lp and Schatten quantum trace diagnostics.
3. 110 pytest cases across 91 test functions, including rational-weight receipt round trips and independent Chebyshev feasibility and tampering checks. No full branch-coverage claim is made.
4. Lean 4 proofs of the conditional finite integer-list certificate and scoped coercivity, ambient norm, weak duality, complementary-slackness, cycle and Bianchi lemmas. General attainment and minimized quotient-norm proofs are supplied in prose.
5. Interactive Jupyter pedagogical notebooks for headless execution.
6. Manifests and deposit verification harnesses (SHA256SUMS and verify_deposit.py).

## Epistemic Boundaries
The results apply strictly to finite discrete cell complexes and finite-dimensional operator spaces under exact arithmetic. They do not constitute an infinite-dimensional Hodge-de Rham theorem on manifolds, continuous Sobolev cohomology, or continuous open quantum system dynamics.

## Licensing
The monograph text, figures, and documentation are licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0). Software, Lean 4 formalizations, and tooling are licensed under PolyForm Noncommercial License 1.0.0.


Coherence is exact when the required complex moduli are rational, and binary64 otherwise. Exact rational feasibility, stationarity, squared-norm and PSD decisions are independent of these numerical displays.

Jiang, Lim, Yao, and Ye (preprint v2, §6.1) already formulate weighted L^1 projection of edge flows onto gradients and its dual over bounded divergence-free flows. Here the contribution is a presentation through weighted finite-graph quotient optimization and exact, independently checkable certificates, a rational computational companion, and mechanization of specified finite integer certificate statements in Lean. The bounded-circulation dual is classical background.

9. X. Jiang, L.-H. Lim, Y. Yao, and Y. Ye, “Statistical ranking and combinatorial Hodge theory,” *Mathematical Programming* 127(1), 2011, 203–244. [DOI](https://doi.org/10.1007/s10107-010-0419-x) (preprint: [arXiv:0811.1067v2](https://arxiv.org/abs/0811.1067v2), §6.1).
