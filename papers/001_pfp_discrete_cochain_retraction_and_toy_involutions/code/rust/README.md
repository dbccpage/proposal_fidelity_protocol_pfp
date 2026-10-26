# Native evaluator ownership

This package is a paper adapter to the repository's canonical Rust implementation.
Run Cargo from this directory; the path dependencies require the repository checkout.

Proposal search belongs to `omega_solvers`. Every Phi1 residual mass and exact
primal-dual replay is evaluated by `omega_functional::phi1::Phi1Functional`.
The former in-package calculator copy has been removed. The graph solver's
paper examples now run in `omega_solvers::graph_phi1::paper_conformance`.

Previously published build receipts and release manifests describe their pinned
source snapshots. They are historical evidence, not validation of this refactor.
