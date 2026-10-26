# Change Log: PFP XX (Paper 020)

## 2026-10-03 — Cross-Validation on Larger Lattice Clusters (v0.2.0)

- Extended multi-qubit carrier to $N=4$ qubits ($16$ Majorana zero modes) on $L=8$ lattice.
- Generalized non-local topological SWAP routing and non-local Clifford operations (CNOT(1,4), GHZ-4, Cluster-4, Star-14).
- Added correlated cluster spatial noise model with rational distance decay across all 120 mode pairs.
- Implemented $O(1)$ signed column permutation composition in `MajoranaBraidCircuit.evaluate_matrix()`.
- Authored `code/l8_n4_cross_validation.py` and test suite achieving 99% coverage.
- Authored CLI runner `scripts/run_cross_validation.py`.
- Updated claim ledger with claims PFP20-09 to PFP20-12.
- AuthorityEffect: None.

## 2026-10-03 — Initial Public Preprint Candidate (v0.1.0)

- Initial release candidate for Paper 020: "PFP XX: Multi-Agent Evaluation Tournaments and Adaptive Noise Mitigation in the Symbol Game".
- Author: Jeremy H. Carroll.
- Established multi-agent braid tournament framework evaluating OpenRouter models (LLaMA 3.1 8B, LLaMA 3.3 70B, GLM 5.3) and deterministic reference baselines.
- Integrated `MultiQubitNoisyBraidReferee` from `omega_engine_projects/ms_majorana`.
- Added exact rational noise defect calculation under Zero-Float Law.
- Authored `code/adaptive_braid_tournament_demo.py` and `scripts/run_tournament.py`.
- Authored test suite `code/tests/test_adaptive_braid_tournament_demo.py` achieving 96% coverage.
- Formulated Zenodo metadata, claim ledger, and verification tooling.
- AuthorityEffect: None.
