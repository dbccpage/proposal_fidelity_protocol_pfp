# Demos

This repository keeps three kinds of executable examples apart:

| Kind | Where | Calls a model? | What it is |
| --- | --- | --- | --- |
| Demos | `demos/` (this folder) | No | Offline examples that run with the standard library and pytest. Each one checks a claim exactly. |
| Pilots | [`pilots/`](../pilots/README.md) | Yes | Experiments that ran language models against a task. They need a model runtime that is not published here. |
| Unit tests | `pfp/tests`, `pfp_lab/tests`, `governance/tools/tests`, `code/rust/**/tests`, and so on | No | Tests of the product code, kept beside the code they test. |

Live model testing stays in the private repository. This one holds the
canonical, offline copies.

Run every demo from the repository root:

    python -m pytest demos -q

Each folder's wiki page explains what it shows and what a failure means; the
[Test Catalog](../wiki/Test-Catalog.md) lists them all.

## Certified challenges

[`certified_challenges/`](certified_challenges/README.md): fifty hard exact
problems (homology, quantum codes, mathematical physics, formal proof,
algorithms), each with a reference solver and checkers that verify a
certificate instead of comparing to a stored answer. About 5,100 tests.

## Small worked examples

| Folder | What it shows |
| --- | --- |
| `checkerboard_paths` | Exact counts of lattice paths on a 1+1 checkerboard, by number of turns |
| `clique_homology` | Exact Betti numbers of the clique complex of a small graph |
| `cochains_hodge_adapter` | Closed versus exact integer cochains on a small oriented complex |
| `face_activation` | One permitted transition that switches a triangular face on |
| `finite_provenance` | Consistency of a ledger of supplied, mentioned and admitted records |
| `finite_quotients` | A function of a merged class cannot separate the records merged into it |
| `hodge_decomposition` | Exact rational Hodge decomposition of a cochain |
| `integer_obstruction_lift` | A rational solution does not repair an integer problem with none |
| `interference_weights` | Equal measurement probabilities, opposite results after a Hadamard gate |
| `lp_certificates` | A primal/dual certificate for a two-variable LP, checked exactly |
| `normalization_readout` | Normalizing weights is arithmetic, not a derivation of a measurement law |
| `rewrite_normal_form_loss` | A rewrite system with two normal forms, and what joining them can erase |
| `singular_integrals` | A divergent improper integral versus its Cauchy principal value |
| `triangle_angle_defects` | Angle defects from squared edge lengths, kept exact |
| `triangle_fan_pairing` | Exact angle data and signed pairing sums for a fan of triangles |
| `xor_cycle_obstruction` | Locally satisfiable constraints on an odd cycle with no global solution |

## Harness and safety checks

| Folder | What it checks |
| --- | --- |
| `calibration_task_bank` | Five prompt-and-checker tasks whose checkers compute the truth |
| `candidate_telemetry` | Fault tracing, hashed diffs and backtracking across candidate revisions |
| `grammar_profiles` | A packet is recognized under one syntax profile without repair |
| `oracle_fixture_freeze` | Python formatting behaviour frozen as hashed oracles for a native port |
| `paper_run_rules` | Role-gated transitions and a scan that keeps pure modules free of I/O |
| `provider_reply_guard` | Byte ceilings on prompts and replies, refused with bounded work |
| `qa_receipt_invariants` | Attempts to break a sealed QA receipt one invariant at a time |
| `role_submission_comparison` | Two frozen role submissions compared literally, disagreements kept |
| `tautology_lint` | Test assertions that cannot fail |
| `template_substitution` | Chained string replacement can rewrite inserted data; one template does not |
| `trace_replay_refusal` | Replays a proposed sequence of steps against a declared task |
| `yardstick` | Wilson intervals, exact McNemar tests and Pareto frontiers on hand-computed cases |
