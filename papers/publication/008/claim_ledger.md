# Paper 008 claim ledger

Initial Zenodo preprint candidate, version 0.1.0, 2026-10-02. Code
baseline `52cb5457f6c485ba548cfd292f6012a941ed22cf`; challenge census
commit `a623568eb0f853b968bc419bf06dfc6af256ab02`. Paper ID PO-008.

## Claims

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ID                Claim                      Evidence                                                                                                                                                                              Ceiling or
                                                                                                                                                                                                                                     falsifier
  ----------------- -------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------
  PFP008-01         The implemented            [Archived actual maps](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/docs/source_archive/mss0_mss1_52cb5457/updown_maps.py); Section 2 branch argument    Old domain
                    old-context round trip is                                                                                                                                                                                        contains Diff
                    MSS-0 to MSS-1.                                                                                                                                                                                                  only; no general
                                                                                                                                                                                                                                     adjacent-stage
                                                                                                                                                                                                                                     map family.

  PFP008-02         New packets yield          Actual source and                                                                                                                                                                     d_1 does not
                    NonDescentReceipt with the [tests](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/code/python/tests/test_mssn_updown_and_cells.py)             itself validate
                    original packet.                                                                                                                                                                                                 all S1 admission
                                                                                                                                                                                                                                     conditions.

  PFP008-03         A left inverse implies     Section 3 proof and added-old-proposition counterexample; Leroy (2009) for the stronger semantic-preservation form                                                                    Must specify
                    injectivity but not                                                                                                                                                                                              meanings and
                    conservative extension of                                                                                                                                                                                        inference rules
                    a theory.                                                                                                                                                                                                        for a semantic
                                                                                                                                                                                                                                     claim.

  PFP008-04         Eight-wide integer opcode  Arithmetic inequality; [registry](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/code/python/registry.py); package  Loaded catalog is
                    blocks for stages at least check `test_008_mssn_tower_retraction.py::test_opcode_blocks_are_disjoint_for_stages_22_to_100`                                                                                       0 to 100;
                    22 are disjoint.                                                                                                                                                                                                 fixed-width
                                                                                                                                                                                                                                     encodings require
                                                                                                                                                                                                                                     additional
                                                                                                                                                                                                                                     bounds.

  PFP008-05         Stage grades are based on  [stage_status.py](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/code/python/stage_status.py)                       No grade by level
                    executed syntax or checker                                                                                                                                                                                       number, no LEAN
                    fixtures.                                                                                                                                                                                                        or GATED grade
                                                                                                                                                                                                                                     here, no
                                                                                                                                                                                                                                     universal checker
                                                                                                                                                                                                                                     soundness.

  PFP008-06         A zero flow-certificate    Exact loads (1,0,0) and flows (1,0,0);                                                                                                                                                Every certificate
                    gap can coexist with       [FlowCertificate.lean](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/lean4/research_programs/level_engine/FlowCertificate.lean) and its   clause matters;
                    failed balance.            vendored copy [lean4/FlowCertificate.lean](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/lean4/FlowCertificate.lean)                                      the fixture
                                                                                                                                                                                                                                     theorem is not a
                                                                                                                                                                                                                                     general LP
                                                                                                                                                                                                                                     theorem.

  PFP008-07         The formal sources have    Source table in Section 5, including Level16, 21, 22 and 23                                                                                                                           No inferred
                    narrower types than                                                                                                                                                                                              colimit, general
                    several historical titles                                                                                                                                                                                        Regge theory,
                    suggest.                                                                                                                                                                                                         Grothendieck
                                                                                                                                                                                                                                     fibration, or
                                                                                                                                                                                                                                     general sheaf
                                                                                                                                                                                                                                     gluing theorem.

  PFP008-08         The baseline audit         [Audit source](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_operations/use_cases/level_engine/lean_audit.py); [mocked       Baseline
                    requires a matching build  custody tests](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_operations/tests/level_engine/test_lean.py)                     publication race
                    and generator-declared                                                                                                                                                                                           reproduced with
                    axiom census; the local                                                                                                                                                                                          mocked Lean and
                    correction also carries                                                                                                                                                                                          corrected in the
                    audited source hashes                                                                                                                                                                                            verification
                    through publication.                                                                                                                                                                                             patch. No fresh
                                                                                                                                                                                                                                     Lean build of the
                                                                                                                                                                                                                                     52 payloads;
                                                                                                                                                                                                                                     policy permits
                                                                                                                                                                                                                                     propext and
                                                                                                                                                                                                                                     Quot.sound.

  PFP008-09         Historical reads use       [Resolver                                                                                                                                                                             Optional digest
                    pinned Git blobs; active   source](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_pfp/infrastructure/tower_evidence/level_engine/resolver.py);   must be supplied
                    reads use v2 package       [focused tests](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_operations/tests/level_engine/test_evidence_resolver.py)       for hash
                    resources, with no                                                                                                                                                                                               comparison; byte
                    fallback between them.                                                                                                                                                                                           identity alone is
                                                                                                                                                                                                                                     not scientific
                                                                                                                                                                                                                                     validation.

  PFP008-10         Historical 150/150 labels  [Runner](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_projects/mssn_sn_symgam/challenges/run_150_tests_suite.py) assigns    Aggregate PASS or
                    are insufficient as        VERIFIED on some missing receipts and exceptions                                                                                                                                      VERIFIED count
                    scientific success                                                                                                                                                                                               does not
                    evidence.                                                                                                                                                                                                        establish actual
                                                                                                                                                                                                                                     successful
                                                                                                                                                                                                                                     executions.

  PFP008-11         At the census commit, 40   [Census file](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/docs/challenge_census.md), built from the tree of commit `a623568e`                           Membership
                    of C001 to C050 are                                                                                                                                                                                              records folder
                    delivered solver packages                                                                                                                                                                                        contents only.
                    with two checker modules                                                                                                                                                                                         C047's test-named
                    (C011 to C050), 2 call for                                                                                                                                                                                       script has no
                    model measurements (C001,                                                                                                                                                                                        assertions or
                    C005), and 8 are                                                                                                                                                                                                 failing exit;
                    specifications only (C002                                                                                                                                                                                        C048 to C051 have
                    to C004, C006 to C010);                                                                                                                                                                                          no pytest test
                    C051 is a further                                                                                                                                                                                                file; the C014
                    delivered package outside                                                                                                                                                                                        receipt is
                    the range.                                                                                                                                                                                                       invalidated
                                                                                                                                                                                                                                     pending a
                                                                                                                                                                                                                                     rescore; no
                                                                                                                                                                                                                                     receipt is
                                                                                                                                                                                                                                     retained for C015
                                                                                                                                                                                                                                     to C020 or C045
                                                                                                                                                                                                                                     to C051.

  PFP008-12         The mutation suites of     Historical author test files listed under Verification below                                                                                                                          Rejection of the
                    C011, C021 and C031                                                                                                                                                                                              retained mutation
                    rejected every mutation                                                                                                                                                                                          files does not
                    file in the retained                                                                                                                                                                                             exclude untested
                    September 28 author runs:                                                                                                                                                                                        failure modes.
                    40, 40 and 45 files. The
                    C011 and C031 dual-checker
                    and C031 reference-solver
                    tests also passed.

  PFP008-13         By source inspection, the  `e_formal_math/c041_lean4_finite_lemma_proofs/reference_solver/lean_compiler.py` and `judge_packet/checkers/` in the challenge folder                                                 The C041 checkers
                    C041 checkers refuse                                                                                                                                                                                             were not executed
                    listed tokens including                                                                                                                                                                                          for this
                    sorry, axiom, unsafe,                                                                                                                                                                                            revision.
                    set_option and
                    native_decide, accept only
                    axioms in {propext,
                    Quot.sound}, and record
                    Lean 4.34.1 as the
                    toolchain.

  PFP008-14         C005, per run: three-arm   [Archived C005 report](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/docs/source_archive/c005_working_report.md), with September 27 runs and September 29 Per-case rows are
                    run Arm 1 25/50, Arm 2     correction; p-values computed here from b and c                                                                                                                                       not retained, so
                    36/50, Arm 3 19/50; hybrid                                                                                                                                                                                       the counts are
                    run Arm 2 38/50, Arm 4                                                                                                                                                                                           transcribed, not
                    4/50; paired tables (b, c)                                                                                                                                                                                       recomputed. One
                    = (6, 17), (6, 0), (20,                                                                                                                                                                                          model (a 405B
                    3), (34, 0) give exact                                                                                                                                                                                           fine-tune)
                    two-sided p =                                                                                                                                                                                                    against the
                    145499/4194304, 1/32,                                                                                                                                                                                            protocol's 70B
                    1/2048 and 2\^−33.                                                                                                                                                                                               limit and a
                                                                                                                                                                                                                                     \$2.00 per-run
                                                                                                                                                                                                                                     ceiling against
                                                                                                                                                                                                                                     \$0.10 per arm: a
                                                                                                                                                                                                                                     protocol
                                                                                                                                                                                                                                     deviation.

  PFP008-15         C001 has no retained       `a_mechanism/c001_attention_distractor_mask/` in the challenge folder, files `empirical_neural_mcnemar_evaluation.py` and `mcnemar_arms_evaluation.py`                                Any C001 accuracy
                    measurement result; its                                                                                                                                                                                          or significance
                    200-case McNemar module is                                                                                                                                                                                       claim needs a
                    a synthetic fixture with                                                                                                                                                                                         retained run.
                    injected baseline
                    failures.

  PFP008-16         In eight K4 traces, one    [Archived benchmark report](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/docs/source_archive/k4_benchmark_report.md) and [eight archived                 n = 1 per cell on
                    per model and condition    traces](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/docs/source_archive/README.md), whose SHA-256 digests match the report                              one fixture at
                    for Qwen2.5-7B-Instruct                                                                                                                                                                                          temperature 0;
                    and Llama-3.1-8B-Instruct,                                                                                                                                                                                       assisted
                    the correct repair was                                                                                                                                                                                           conditions;
                    proposed exactly in the                                                                                                                                                                                          terminal defect
                    scratchpad and hinted                                                                                                                                                                                            values are the
                    conditions, whose prompts                                                                                                                                                                                        retained report's
                    contained the repair                                                                                                                                                                                             replay, with no
                    values; baseline and                                                                                                                                                                                             stored final
                    partially masked runs                                                                                                                                                                                            post-move result;
                    ended at Φ1 = 8, 6 (Qwen)                                                                                                                                                                                        the host's
                    and 5, 7 (Llama).                                                                                                                                                                                                acceptance rule
                                                                                                                                                                                                                                     can also be met
                                                                                                                                                                                                                                     by a move that
                                                                                                                                                                                                                                     replaces the
                                                                                                                                                                                                                                     claims with
                                                                                                                                                                                                                                     zeros.

  PFP008-17         The historical             [Trace audit](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/demos/anti_morphism_observations.md); [Demo 2          No classification
                    exact-cancellation         notes](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/research/mssn_sn_tower/demos/demo_2/2_demo.md); trace                                of any
                    terminals on the           `research/mssn_sn_tower/demos/demo_2/traces/demo2_r5_frustrated_triangular_1790208154.jsonl`                                                                                          Hamiltonian's
                    Hamiltonian traces are                                                                                                                                                                                           sign problem.
                    host false acceptances,
                    and the triangular trace
                    supports only the
                    odd-cycle fact that no
                    site signs satisfy η_u η_v
                    = −1 on every edge.

  PFP008-18         Retained source-bound      [lean4/axiom_report.txt](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/lean4/axiom_report.txt) and                                                        39 selected
                    author receipts record     [lean4/Census.lean](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/lean4/Census.lean); [October 2 author                                                   theorems are
                    compilation of the local   receipt](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/docs/release_validation_2026_10_02.json), whose Lean source bindings match                         distinct from the
                    formal package with Lean                                                                                                                                                                                         retained 576
                    4.34.0; of their 39                                                                                                                                                                                              local environment
                    theorems, 38 depend on no                                                                                                                                                                                        declarations. The
                    axiom beyond propext and                                                                                                                                                                                         fresh review-host
                    Quot.sound, and                                                                                                                                                                                                  Lean startup is
                    stage_capacity_monotonic                                                                                                                                                                                         blocked; the 52
                    also depends on                                                                                                                                                                                                  external payloads
                    Classical.choice.                                                                                                                                                                                                were not rebuilt.

  PFP008-19         The package runner's       `test_008_mssn_tower_retraction.py::test_offline_run_opens_no_network_connection`; `test_008_mssn_tower_retraction.py::test_cli_refuses_output_inside_the_package`;                   The stub reads
                    offline mode opens no      `test_008_mssn_tower_retraction.py::test_offline_stub_match_counts`; `test_008_mssn_tower_retraction.py::test_cli_live_without_key_is_refused`                                        the prompt and
                    network connection, reads                                                                                                                                                                                        measures no
                    no credential file, and                                                                                                                                                                                          model; no live
                    writes only to an explicit                                                                                                                                                                                       run is reported.
                    or temporary directory
                    outside the package; its
                    offline stub matches 3, 6,
                    3 and 6 of 6 verdicts
                    under the baseline,
                    hinted, scratchpad and
                    oracle conditions.

PFP008-20         Each host verdict of the   `test_008_mssn_tower_retraction.py::test_every_host_verdict_carries_a_checkable_certificate`; `test_008_mssn_tower_retraction.py::test_tampered_dual_witnesses_are_rejected`;         Six fixed graphs
                    package runner carries a   `test_008_mssn_tower_retraction.py::test_potential_check_rejects_wrong_or_partial_values`                                                                                             plus 125 bounded
                    checkable certificate: a                                                                                                                                                                                         triangle
                    potential satisfying every                                                                                                                                                                                       assignments
                    edge, or a dual witness, a                                                                                                                                                                                       checked against
                    closed walk with nonzero                                                                                                                                                                                         independent
                    signed claim sum; altered                                                                                                                                                                                        potential search;
                    walks and wrong potentials                                                                                                                                                                                       JSON round trips
                    are rejected.                                                                                                                                                                                                    checked. No
                                                                                                                                                                                                                                     general checker
                                                                                                                                                                                                                                     theorem or model
                                                                                                                                                                                                                                     measurement.
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| PFP008-21 \| The package scorer refuses malformed, conflicting or
  substring-only verdicts; it validates fixture labels before a proposer
  call. \| Runner regression tests for invalid verdicts and wrong
  expected labels \| Strict parsing is a scoring contract, not evidence
  of reasoning. \|
| PFP008-22 \| Version-2 receipt digests bind the complete graph,
  prompt, raw response, provider label, measurements, certificate and
  declared runner source. \|
  `test_receipt_digest_binds_the_raw_reply_prompt_case_and_certificate`
  and raw-response collision regression \| Public unkeyed hashes do not
  authenticate a provider; compare against a trusted expected digest. \|
| PFP008-23 \| The named optional Lean gate refuses empty, missing,
  duplicate, extra or dependency-changed successful report output and a
  stale generated census. \| Seven mocked gate tests in
  `test_008_deposit_gates.py` \| Control-logic checks, not a kernel
  build. \|
| PFP008-24 \| Thirteen archived parser/map/report/trace files retain
  their origin revision, Git blob SHA, SHA-256 and bytes; all eight K4
  trace hashes match the report. \| [Source
  index](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/docs/source_archive/source_index.json);
  source-example tests \| Custody does not adopt withdrawn
  working-report interpretations or replay final host states. \|

## Superseded assertions

The earlier manuscripts' general retraction family, universal semantic
conservativity, current 52-module certification, categorical colimit
interpretation, "perfect" governed benchmark outcome, and
retraction-frequency claim are not supported here. Their spend,
duration, receipt labels, and hashes remain historical data rather than
adopted experimental results.

Version 1.1.0 added Sections 9 to 12 with figures that this revision
withdraws or corrects: challenge categories that overlapped and omitted
delivered packages, mutation and test counts for C011, C021 and C031, a
C001 evaluation across 200 tasks, a C005 Arm 2 figure of 37/50 that no
run produced, 28 benchmark trials, loop averages, and Hamiltonian
terminals. The [change
log](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/paper_change_log.md)
lists each old figure with its replacement.

The local toy in the test file uses a prefix check and None. It is not
the typed domain refusal.

## Verification for the October 2 publication review

The [review
report](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/docs/publication_review_2026_10_02.md)
and [execution
receipt](../../008_pfp_mssn_tower_challenges_and_retraction_benchmarks/docs/review_validation_2026_10_02.json)
identify the revised inputs and fresh checks. The 52 offline tests
comprise 34 runner tests, 7 mocked deposit-gate tests and 11
source-example tests. Lint and typing pass. Fresh Lean startup is
blocked; the retained 13 protected source bindings and broader census
identities match. No model provider call or external deposit was made.
The 16-question quiz has worked answers and source-backed exercises; its
32-point rubric is a self-study aid, not a validated assessment.

## Historical September 28 author runs

The following table is retained as an author record, not a fresh
execution of this revision. Commands were run from the worktree root
with Python 3.12.10, pytest 8.3.5, ruff 0.14.13, and Lake 5.0.0 with
Lean 4.34.0, on 2026-09-28. Each exited with status 0.

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Command                                                                                                                                         Scope                   Result
  ----------------------------------------------------------------------------------------------------------------------------------------------- ----------------------- -----------------------
  `py -3.12 -m pytest <package>/code/tests/test_008_mssn_tower_retraction.py -q -p no:cacheprovider --basetemp=<scratch>`                         Package tests           24 passed

  `py -3.12 -m ruff check <package>`                                                                                                              Package Python files,   All checks passed
                                                                                                                                                  configuration in
                                                                                                                                                  `pyproject.toml`

  `py -3.12 -m mypy` in `<package>` (mypy 1.19.1)                                                                                                 `code/`, configuration  No issues in 3 source
                                                                                                                                                  in `pyproject.toml`     files

  `lake build` in `<package>/lean4`                                                                                                               Vendored Lean files and 12 jobs, build
                                                                                                                                                  ExactRat                completed

  `py -3.12 <package>/tools/replay_lean_axiom_census.py --replay --timeout-seconds 600 <package>`                                                 39 theorems named in    Replay matched the
                                                                                                                                                  the axiom report        report

  `py -3.12 <package>/code/retraction_benchmark_runner.py --mock --condition hinted --output-dir <scratch>`                                       Offline runner          6/6 verdicts matched
                                                                                                                                                                          the host

  `py -3.12 -m pytest research/mssn_sn_tower/code/python/tests/test_mssn_updown_and_cells.py`                                                     Context maps            12 passed

  `py -3.12 -m pytest research/mssn_sn_tower/code/python/tests/test_mssn_grammar.py`                                                              Grammar                 57 passed

  `py -3.12 -m pytest omega_engine_operations/tests/level_engine/test_evidence_resolver.py`                                                       Resolver                10 passed

  `py -3.12 -m pytest omega_engine_operations/tests/level_engine/test_lean.py`                                                                    Custody control logic   11 passed
                                                                                                                                                  with fake Lean
                                                                                                                                                  responses

  `py -3.12 -m pytest <challenges>/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/test_checker_mutations.py`   C011 mutation files     41 passed

  `py -3.12 -m pytest <challenges>/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/tests/test_dual_checkers.py`                             C011 judge cases        5 passed

  `py -3.12 -m pytest <challenges>/c_quantum/c021_q40_r/judge_packet/mutation_suite/test_checker_mutations.py`                                    C021 mutation files     41 passed

  `py -3.12 -m pytest <challenges>/d_physics_mtheory/c031_anomaly_free_u1_charges/judge_packet/mutation_suite/test_checker_mutations.py`          C031 mutation files     47 passed

`py -3.12 -m pytest <challenges>/d_physics_mtheory/c031_anomaly_free_u1_charges/tests/test_reference_solver.py`                                 C031 solver             9 passed
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Here `<package>` is this package's folder, `<challenges>` is
`omega_engine_projects/mssn_sn_symgam/challenges`, and `<scratch>` is an
untracked scratch directory. Every pytest command also used
`-p no:cacheprovider` and a scratch `--basetemp`, one file per command.
The source-bound review receipt linked above is the fresh execution
evidence; this table is the author's historical record. Its package-test
count and runner behavior refer to the older source bytes.

Leroy's journal record and arXiv abstract confirm the title, venue, and
DOI cited in Section 3. Lean's official axioms chapter and Git's
object-reading documentation support the corresponding tool
descriptions.
