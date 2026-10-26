# Claim Ledger: PFP XX (Paper 020)

Version 0.1.0, 2026-10-03. Code baseline: Local workspace.

Each row is a claim made in the manuscript, with the section that makes it, its kind, and the evidence that supports it. Kinds are: *executable check* (a named test in `code/tests/`), *standard fact* (a cited reference), or *source inspection* (reading code). Claims are evaluated strictly under declared assumptions with `AuthorityEffect: None`.

## Claims and Evidence Register

| ID | Claim | Section | Kind | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| PFP20-01 | Parameter boundary checks reject non-positive qubit counts and malformed gate inputs. | 2 | Executable check | `test_adaptive_braid_tournament_demo.py::TestAdaptiveBraidTournament::test_tournament_run_sweep_deterministic` |
| PFP20-02 | The host referee verifies $SO(4N)$ orthogonality and unit determinant ($\det U = +1$) on all compiled braid matrices. | 2 | Executable check | `test_adaptive_braid_tournament_demo.py::TestAdaptiveBraidTournament::test_canonical_tournament_demo_entrypoint` |
| PFP20-03 | Operator commutation defect $\|U K U^T - K\|_1$ is evaluated in exact rational arithmetic (`fractions.Fraction`) under the Zero-Float Law. | 1, 2 | Executable check | `test_adaptive_braid_tournament_demo.py::TestAdaptiveBraidTournament::test_tournament_run_sweep_deterministic` |
| PFP20-04 | The host referee emits `ACCEPTED_STABLE` when commutation defect is within tolerance and `REFUSAL_NOISE_LEAKAGE` when noise exceeds tolerance. | 2, 4 | Executable check | `test_adaptive_braid_tournament_demo.py::TestAdaptiveBraidTournament::test_refusal_on_high_noise` |
| PFP20-05 | Proposer agents synthesize adaptive braid schedules for canonical single-qubit and two-qubit Clifford operations. | 3 | Executable check | `test_adaptive_braid_tournament_demo.py::TestBraidTournamentProposerAgent::test_direct_unmitigated_schedules` |
| PFP20-06 | Dual execution supports live OpenRouter queries and deterministic offline strategy fallbacks complying with credential boundary invariants. | 3 | Executable check | `test_adaptive_braid_tournament_demo.py::TestBraidTournamentProposerAgent::test_openrouter_live_query_handling` |
| PFP20-07 | Tournament run receipts contain deterministic SHA-256 canonical digests and declare `AuthorityEffect: None`. | 4 | Executable check | `test_adaptive_braid_tournament_demo.py::TestAdaptiveBraidTournament::test_tournament_run_sweep_deterministic` |
| PFP20-08 | Claim hygiene summaries state what is supported, what is not supported, the narrowest defensible claim, and the next test needed without forbidden hype verbs. | 5 | Executable check | `test_adaptive_braid_tournament_demo.py::TestAdaptiveBraidTournament::test_claim_hygiene_summary_formatting` |
| PFP20-09 | Non-local multi-qubit entangling gates (CNOT, GHZ-4, Cluster-4, Star-14) compiled via exact topological SWAP routing preserve SO(16) orthogonality and det +1 on 16 Majorana modes. | 4.2 | Executable check | `test_l8_n4_cross_validation.py::TestL8N4CrossValidation::test_all_target_operations_and_strategies` |
| PFP20-10 | Correlated cluster noise models with rational distance decay across L=8 lattices are verified in exact rational arithmetic under the Zero-Float Law. | 4.2 | Executable check | `test_l8_n4_cross_validation.py::TestL8N4CrossValidation::test_cross_validation_run_deterministic` |
| PFP20-11 | Tightened referee tolerances trigger deterministic `REFUSAL_NOISE_LEAKAGE` under excessive noise leakage on 16-mode clusters. | 4.2 | Executable check | `test_l8_n4_cross_validation.py::TestL8N4CrossValidation::test_tight_tolerance_refusal` |
| PFP20-12 | L=8, N=4 cross-validation receipts emit deterministic SHA-256 digests and claim hygiene summaries declaring `AuthorityEffect: None`. | 4.2, 5 | Executable check | `test_l8_n4_cross_validation.py::TestL8N4CrossValidation::test_claim_hygiene_summary_formatting` |
