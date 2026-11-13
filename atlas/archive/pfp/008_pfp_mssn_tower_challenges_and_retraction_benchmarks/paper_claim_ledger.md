# Paper 008 claim ledger

Initial Zenodo preprint candidate, version 0.1.0, 2026-10-02. Code baseline
`52cb5457f6c485ba548cfd292f6012a941ed22cf`; challenge census commit
`a623568eb0f853b968bc419bf06dfc6af256ab02`. Paper ID PO-008.

## Claims

| ID | Claim | Evidence | Ceiling or falsifier |
| --- | --- | --- | --- |
| PFP008-01 | The implemented old-context round trip is MSS-0 to MSS-1. | [Archived actual maps](docs/source_archive/mss0_mss1_52cb5457/updown_maps.py); Section 2 branch argument | Old domain contains Diff only; no general adjacent-stage map family. |
| PFP008-02 | New packets yield NonDescentReceipt with the original packet. | Actual source and [tests](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/code/python/tests/test_mssn_updown_and_cells.py) | d_1 does not itself validate all S1 admission conditions. |
| PFP008-03 | A left inverse implies injectivity but not conservative extension of a theory. | Section 3 proof and added-old-proposition counterexample; Leroy (2009) for the stronger semantic-preservation form | Must specify meanings and inference rules for a semantic claim. |
| PFP008-04 | Eight-wide integer opcode blocks for stages at least 22 are disjoint. | Arithmetic inequality; [registry](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/code/python/registry.py); package check `test_008_mssn_tower_retraction.py::test_opcode_blocks_are_disjoint_for_stages_22_to_100` | Loaded catalog is 0 to 100; fixed-width encodings require additional bounds. |
| PFP008-05 | Stage grades are based on executed syntax or checker fixtures. | [stage_status.py](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/code/python/stage_status.py) | No grade by level number, no LEAN or GATED grade here, no universal checker soundness. |
| PFP008-06 | A zero flow-certificate gap can coexist with failed balance. | Exact loads (1,0,0) and flows (1,0,0); [FlowCertificate.lean](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/lean4/research_programs/level_engine/FlowCertificate.lean) and its vendored copy [lean4/FlowCertificate.lean](lean4/FlowCertificate.lean) | Every certificate clause matters; the fixture theorem is not a general LP theorem. |
| PFP008-07 | The formal sources have narrower types than several historical titles suggest. | Source table in Section 5, including Level16, 21, 22 and 23 | No inferred colimit, general Regge theory, Grothendieck fibration, or general sheaf gluing theorem. |
| PFP008-08 | The baseline audit requires a matching build and generator-declared axiom census; the local correction also carries audited source hashes through publication. | [Audit source](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/operations/use_cases/level_engine/lean_audit.py); [mocked custody tests](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/operations/tests/level_engine/test_lean.py) | Baseline publication race reproduced with mocked Lean and corrected in the verification patch. No fresh Lean build of the 52 payloads; policy permits propext and Quot.sound. |
| PFP008-09 | Historical reads use pinned Git blobs; active reads use v2 package resources, with no fallback between them. | [Resolver source](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/pfp/infrastructure/tower_evidence/level_engine/resolver.py); [focused tests](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/operations/tests/level_engine/test_evidence_resolver.py) | Optional digest must be supplied for hash comparison; byte identity alone is not scientific validation. |
| PFP008-10 | Historical 150/150 labels are insufficient as scientific success evidence. | [Runner](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/projects/mssn_sn_symgam/challenges/run_150_tests_suite.py) assigns VERIFIED on some missing receipts and exceptions | Aggregate PASS or VERIFIED count does not establish actual successful executions. |
| PFP008-11 | At the census commit, 40 of C001 to C050 are delivered solver packages with two checker modules (C011 to C050), 2 call for model measurements (C001, C005), and 8 are specifications only (C002 to C004, C006 to C010); C051 is a further delivered package outside the range. | [Census file](docs/challenge_census.md), built from the tree of commit `a623568e` | Membership records folder contents only. C047's test-named script has no assertions or failing exit; C048 to C051 have no pytest test file; the C014 receipt is invalidated pending a rescore; no receipt is retained for C015 to C020 or C045 to C051. |
| PFP008-12 | The mutation suites of C011, C021 and C031 rejected every mutation file in the retained September 28 author runs: 40, 40 and 45 files. The C011 and C031 dual-checker and C031 reference-solver tests also passed. | Historical author test files listed under Verification below | Rejection of the retained mutation files does not exclude untested failure modes. |
| PFP008-13 | By source inspection, the C041 checkers refuse listed tokens including sorry, axiom, unsafe, set_option and native_decide, accept only axioms in {propext, Quot.sound}, and record Lean 4.34.1 as the toolchain. | `e_formal_math/c041_lean4_finite_lemma_proofs/reference_solver/lean_compiler.py` and `judge_packet/checkers/` in the challenge folder | The C041 checkers were not executed for this revision. |
| PFP008-14 | C005, per run: three-arm run Arm 1 25/50, Arm 2 36/50, Arm 3 19/50; hybrid run Arm 2 38/50, Arm 4 4/50; paired tables (b, c) = (6, 17), (6, 0), (20, 3), (34, 0) give exact two-sided p = 145499/4194304, 1/32, 1/2048 and 2^−33. | [Archived C005 report](docs/source_archive/c005_working_report.md), with September 27 runs and September 29 correction; p-values computed here from b and c | Per-case rows are not retained, so the counts are transcribed, not recomputed. One model (a 405B fine-tune) against the protocol's 70B limit and a $2.00 per-run ceiling against $0.10 per arm: a protocol deviation. |
| PFP008-15 | C001 has no retained measurement result; its 200-case McNemar module is a synthetic fixture with injected baseline failures. | `a_mechanism/c001_attention_distractor_mask/` in the challenge folder, files `empirical_neural_mcnemar_evaluation.py` and `mcnemar_arms_evaluation.py` | Any C001 accuracy or significance claim needs a retained run. |
| PFP008-16 | In eight K4 traces, one per model and condition for Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct, the correct repair was proposed exactly in the scratchpad and hinted conditions, whose prompts contained the repair values; baseline and partially masked runs ended at Φ1 = 8, 6 (Qwen) and 5, 7 (Llama). | [Archived benchmark report](docs/source_archive/k4_benchmark_report.md) and [eight archived traces](docs/source_archive/README.md), whose SHA-256 digests match the report | n = 1 per cell on one fixture at temperature 0; assisted conditions; terminal defect values are the retained report's replay, with no stored final post-move result; the host's acceptance rule can also be met by a move that replaces the claims with zeros. |
| PFP008-17 | The historical exact-cancellation terminals on the Hamiltonian traces are host false acceptances, and the triangular trace supports only the odd-cycle fact that no site signs satisfy η_u η_v = −1 on every edge. | [Trace audit](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/demos/anti_morphism_observations.md); [Demo 2 notes](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/demos/demo_2/2_demo.md); trace `research/mssn_sn_tower/demos/demo_2/traces/demo2_r5_frustrated_triangular_1790208154.jsonl` | No classification of any Hamiltonian's sign problem. |
| PFP008-18 | Retained source-bound author receipts record compilation of the local formal package with Lean 4.34.0; of their 39 theorems, 38 depend on no axiom beyond propext and Quot.sound, and stage_capacity_monotonic also depends on Classical.choice. | [lean4/axiom_report.txt](lean4/axiom_report.txt) and [lean4/Census.lean](lean4/Census.lean); [October 2 author receipt](docs/release_validation_2026_10_02.json), whose Lean source bindings match | 39 selected theorems are distinct from the retained 576 local environment declarations. The fresh review-host Lean startup is blocked; the 52 external payloads were not rebuilt. |
| PFP008-19 | The package runner's offline mode opens no network connection, reads no credential file, and writes only to an explicit or temporary directory outside the package; its offline stub matches 3, 6, 3 and 6 of 6 verdicts under the baseline, hinted, scratchpad and oracle conditions. | `test_008_mssn_tower_retraction.py::test_offline_run_opens_no_network_connection`; `test_008_mssn_tower_retraction.py::test_cli_refuses_output_inside_the_package`; `test_008_mssn_tower_retraction.py::test_offline_stub_match_counts`; `test_008_mssn_tower_retraction.py::test_cli_live_without_key_is_refused` | The stub reads the prompt and measures no model; no live run is reported. |
| PFP008-20 | Each host verdict of the package runner carries a checkable certificate: a potential satisfying every edge, or a dual witness, a closed walk with nonzero signed claim sum; altered walks and wrong potentials are rejected. | `test_008_mssn_tower_retraction.py::test_every_host_verdict_carries_a_checkable_certificate`; `test_008_mssn_tower_retraction.py::test_tampered_dual_witnesses_are_rejected`; `test_008_mssn_tower_retraction.py::test_potential_check_rejects_wrong_or_partial_values` | Six fixed graphs plus 125 bounded triangle assignments checked against independent potential search; JSON round trips checked. No general checker theorem or model measurement. |

| PFP008-21 | The package scorer refuses malformed, conflicting or substring-only verdicts; it validates fixture labels before a proposer call. | Runner regression tests for invalid verdicts and wrong expected labels | Strict parsing is a scoring contract, not evidence of reasoning. |
| PFP008-22 | Version-2 receipt digests bind the complete graph, prompt, raw response, provider label, measurements, certificate and declared runner source. | `test_receipt_digest_binds_the_raw_reply_prompt_case_and_certificate` and raw-response collision regression | Public unkeyed hashes do not authenticate a provider; compare against a trusted expected digest. |
| PFP008-23 | The named optional Lean gate refuses empty, missing, duplicate, extra or dependency-changed successful report output and a stale generated census. | Seven mocked gate tests in `test_008_deposit_gates.py` | Control-logic checks, not a kernel build. |
| PFP008-24 | Thirteen archived parser/map/report/trace files retain their origin revision, Git blob SHA, SHA-256 and bytes; all eight K4 trace hashes match the report. | [Source index](docs/source_archive/source_index.json); source-example tests | Custody does not adopt withdrawn working-report interpretations or replay final host states. |

## Superseded assertions

The earlier manuscripts' general retraction family, universal semantic
conservativity, current 52-module certification, categorical colimit
interpretation, “perfect” governed benchmark outcome, and retraction-frequency
claim are not supported here. Their spend, duration, receipt labels, and hashes
remain historical data rather than adopted experimental results.

Version 1.1.0 added Sections 9 to 12 with figures that this revision withdraws
or corrects: challenge categories that overlapped and omitted delivered
packages, mutation and test counts for C011, C021 and C031, a C001 evaluation
across 200 tasks, a C005 Arm 2 figure of 37/50 that no run produced, 28
benchmark trials, loop averages, and Hamiltonian terminals. The
[change log](paper_change_log.md) lists each old figure with its replacement.

The local toy in the test file uses a prefix check and None. It is not the
typed domain refusal.

## Verification for the October 2 publication review

The [review report](docs/publication_review_2026_10_02.md) and
[execution receipt](docs/review_validation_2026_10_02.json) identify the revised
inputs and fresh checks. The 52 offline tests comprise 34 runner tests,
7 mocked deposit-gate tests and 11 source-example tests. Lint and typing pass.
Fresh Lean startup is blocked; the retained 13 protected source bindings and
broader census identities match. No model provider call or external deposit
was made. The 16-question quiz has worked answers and source-backed exercises;
its 32-point rubric is a self-study aid, not a validated assessment.

## Historical September 28 author runs

The following table is retained as an author record, not a fresh execution of
this revision. Commands were run from the worktree root with Python 3.12.10, pytest 8.3.5,
ruff 0.14.13, and Lake 5.0.0 with Lean 4.34.0, on 2026-09-28. Each exited
with status 0.

| Command | Scope | Result |
| --- | --- | --- |
| `py -3.12 -m pytest <package>/code/tests/test_008_mssn_tower_retraction.py -q -p no:cacheprovider --basetemp=<scratch>` | Package tests | 24 passed |
| `py -3.12 -m ruff check <package>` | Package Python files, configuration in `pyproject.toml` | All checks passed |
| `py -3.12 -m mypy` in `<package>` (mypy 1.19.1) | `code/`, configuration in `pyproject.toml` | No issues in 3 source files |
| `lake build` in `<package>/lean4` | Vendored Lean files and ExactRat | 12 jobs, build completed |
| `py -3.12 <package>/tools/replay_lean_axiom_census.py --replay --timeout-seconds 600 <package>` | 39 theorems named in the axiom report | Replay matched the report |
| `py -3.12 <package>/code/retraction_benchmark_runner.py --mock --condition hinted --output-dir <scratch>` | Offline runner | 6/6 verdicts matched the host |
| `py -3.12 -m pytest research/mssn_sn_tower/code/python/tests/test_mssn_updown_and_cells.py` | Context maps | 12 passed |
| `py -3.12 -m pytest research/mssn_sn_tower/code/python/tests/test_mssn_grammar.py` | Grammar | 57 passed |
| `py -3.12 -m pytest operations/tests/level_engine/test_evidence_resolver.py` | Resolver | 10 passed |
| `py -3.12 -m pytest operations/tests/level_engine/test_lean.py` | Custody control logic with fake Lean responses | 11 passed |
| `py -3.12 -m pytest <challenges>/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py` | C011 mutation files | 41 passed |
| `py -3.12 -m pytest <challenges>/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/tests/test_dual_checkers.py` | C011 judge cases | 5 passed |
| `py -3.12 -m pytest <challenges>/c_quantum/c021_q40_r/judge_packet/mutation_suite/test_checker_mutations.py` | C021 mutation files | 41 passed |
| `py -3.12 -m pytest <challenges>/d_physics_mtheory/c031_anomaly_free_u1_charges/judge_packet/mutation_suite/test_checker_mutations.py` | C031 mutation files | 47 passed |
| `py -3.12 -m pytest <challenges>/d_physics_mtheory/c031_anomaly_free_u1_charges/tests/test_reference_solver.py` | C031 solver | 9 passed |

Here `<package>` is this package's folder, `<challenges>` is
`projects/mssn_sn_symgam/challenges`, and `<scratch>` is an
untracked scratch directory. Every pytest command also used
`-p no:cacheprovider` and a scratch `--basetemp`, one file per command. The
source-bound review receipt linked above is the fresh execution evidence;
this table is the author's historical record. Its package-test count and
runner behavior refer to the older source bytes.

Leroy's journal record and arXiv abstract confirm the title, venue, and DOI
cited in Section 3. Lean's official axioms chapter and Git's object-reading
documentation support the corresponding tool descriptions.
