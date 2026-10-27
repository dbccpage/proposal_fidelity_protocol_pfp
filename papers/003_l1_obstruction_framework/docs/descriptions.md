# Scientific Description: Finite ℓ¹ Coboundary Obstructions

This deposit contains the complete research package for Finite ℓ¹ Coboundary Obstructions: Primal–Dual Certificates, Operator-Valued Extensions, and Spectral Comparisons, authored by Jeremy H. Carroll.

Series: 001_finite_obstruction_calculus
Paper ID: 001_finite_obstruction_calculus/003_l1_obstruction_framework
Version: 5.5.3 (2026-10-15)

---

## 1. Context and Problem Statement

In discrete cochain complexes, distributed consensus protocols, and applied combinatorial topology, local evaluations often fail to compose into globally realizable assignments. While classical approaches evaluate such discrepancies using quadratic Hilbert-space norms, the resulting solutions typically diffuse obstruction across all degrees of freedom. This monograph investigates the structural consequences of selecting the L1 norm for finite obstruction measurement under contractive aggregation and operator-valued extensions.

---

## 2. Core Mathematical Contributions

1. Proved finite certificate: the integer-list inequality `general_finite_certificate_optimality`, evaluated on finite graphs by `LocalPrimalDualIterator.certificate_dominates`.
2. Valid mathematical proofs in text: functorial aggregation monotonicity (Theorem 2.1), finite scalar KKT certificate (Theorem 4.2), distinguishability bound (Theorem 5.1), and rank-one comparison-operator secular root (Proposition E.7e) are maintained as classical mathematical theorems in text, distinguished from mechanized rows.
3. Negative boundary: a coboundary defect is not the same thing as a bipartite product defect (refuted by the Bell-state check); the withdrawn candidate 3-step iterator is refuted and quarantined.

---

## 3. Mathematical Framework

The framework operates over finite cell complexes and directed graphs with cochain spaces equipped with additive valuation structures:
- Cochains and Coboundaries: Discrepancy fields are evaluated as coboundaries of local vertex assignments.
- Dual Certificates: Feasibility and optimality are certified by combinatorial dual certificates residing in the unit hypercube of the dual space.
- Conserved Flux and Holonomy: Irreducible cycle obstructions yield discrete holonomies and conserved fluxes under quotient variational symmetries.

---

## 4. Computational Implementation and Conformance Testing

The package includes a deterministic Python reference implementation in `code/mod_004_l1_obstruction_framework_core.py` utilizing exact rational arithmetic (fractions.Fraction) and audited floating-point solvers:
- A pytest suite under `code/tests/` that calls the shipped checkers, including `certificate_dominates`.
- Benchmark validation against cycle complexes, discrete tori, and non-trivial graph topologies.
- Rigorous cryptographic checksum manifest and verification tooling under `SHA256SUMS` and `verify_deposit.py`.

---

## 5. Evaluator Soundness and Non-Claims

We verify the discrete evaluator soundness condition: coboundaries of global states evaluate to zero obstruction under the local evaluation kernels. All results are discrete, finite, and constructive.

---

## 6. Scope Boundaries and Open Conjectures

- Formal Scaling Limit: Continuum limits recovering total variation flow and geometric interface evolution are presented as formal scaling analogies; full Gamma-convergence remains open.
- Refuted Candidate Update: The candidate 3-step primal-dual update is formally withdrawn and refuted by a single-edge counterexample; it provides neither descent nor convergence.
- Metric Emergence: The framework analyzes path residual pseudometrics but assumes underlying graph topology as an input.

---

## 7. Deposit Contents

- `l1_obstruction_framework.md`: Canonical scientific monograph (Version 5.5.3).
- `code/mod_004_l1_obstruction_framework_core.py`: Sovereign implementation of L1 obstruction solvers and dual certifiers.
- `code/tests/test_004_l1_obstruction_framework.py`: 53 comprehensive unit, property, and regression tests.
- `docs/descriptions.md`: Scientific and architectural documentation.
- `docs/references.md`: Complete bibliographic and cross-paper reference register.
- `verify_deposit.py`: Automated cryptographic, structure, and test suite verifier.
- `zenodo_metadata.json`: Deposit metadata conforming to Zenodo schema.

---

## 8. Licensing and Citation

- Manuscript and documentation: Creative Commons Attribution 4.0 International (CC-BY-4.0).
- Code, proofs, and release tooling: PolyForm Noncommercial License 1.0.0 (PolyForm-Noncommercial-1.0.0).
- Citation: Carroll, J. H. (2026). Finite ℓ¹ Coboundary Obstructions: Primal–Dual Certificates, Operator-Valued Extensions, and Spectral Comparisons. Research Monograph, Series 001_finite_obstruction_calculus.
