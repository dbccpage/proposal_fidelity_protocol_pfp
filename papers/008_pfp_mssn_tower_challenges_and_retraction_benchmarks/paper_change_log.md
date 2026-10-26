# Change log for Paper 008

## 2026-10-03 — Zenodo deposit publication (v0.1.0 Preprint)

Recorded canonical Zenodo record <https://zenodo.org/records/23115542> (DOI: `10.5281/zenodo.23115542`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## 2026-10-02 — v0.1 publication review


- Corrected four reproducible control defects: verdict substring acceptance,
  disconnected repeat counts, receipts that did not bind raw execution inputs,
  and a Lean gate accepting exit 0 with an empty or incomplete report. JSON
  witness round trips and inconsistent fixture labels now have refusal checks.
- Archived the actual initial grammar/maps, C005 and K4 working reports, and
  eight raw K4 traces without changing their bytes. Added full revision, Git
  blob and SHA-256 provenance; all eight trace hashes match the report.
- Kept newly deposited evidence links beside the current canonical package in
  the series renderer, instead of pointing to a historical commit before those
  files existed. Typeset exact p-values as TeX math and separated rounded
  approximations into their own column for reliable PDF glyphs.
- Replaced stale evidence links with pinned historical revisions, recorded the
  40/2/8 census inventory, and corrected the C047 print-only script description.
  Category B membership is a requested measurement, not a completed result.
- Distinguished 39 selected Lean theorems from 576 local environment
  declarations and the 52 external payloads. Retained source hashes match;
  fresh local Lean startup is blocked and is not recorded as a kernel pass.
- Reworked the Landau companion into 16 questions with worked calculations,
  scope limits, source-backed exercises and a self-study rubric. No learner
  outcome study is asserted.
- Expanded offline coverage from 24 to 52 tests, including all 125 bounded
  triangle assignments; rebuilt the manuscript, collection mirror and deposit
  ZIP with current source-bound validation. No live run or deposit occurred.

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

All notable changes to this paper and its package are recorded here. The
format follows Keep a Changelog, and versions follow Semantic Versioning.

## [1.2.0] - 2026-09-28

### Changed

- Sections 9 to 12 were rewritten from retained evidence. Sections 1 to 8 were
  kept; their source links were rechecked and their four repository test files
  re-run (Section 11). Section 5 now reports the vendored Lean build and its
  axiom report, and Section 6 states which Lean work this revision did.
- Section 12 is now "Scope of the claims", and a Limitations section and the
  standard "Verification for this revision" section were added. The manuscript
  header states the date and version.
- The census date and commit are stated: commit
  `a623568eb0f853b968bc419bf06dfc6af256ab02` (2026-09-28).
- The test file moved from `code/` to `code/tests/`. The runner now defaults to
  an offline stub, opens no network connection offline, reads no `.env` file,
  refuses live mode without an environment key, and writes only to an explicit
  or temporary directory outside the package. Each host verdict now carries a
  certificate: a potential, or a dual witness walk with nonzero signed claim
  sum. Its live test was removed; the test file now has 24 offline tests.
- `completion_supplement.md` moved to `docs/`.

### Withdrawn or corrected

Each item gives the earlier text, its replacement, and the evidence path.

- Challenge categories. Earlier: Category A was C001, C005, C011, C021, C031,
  C041 and C042; Category B was C001 and C005; Category C included C012 to
  C020, C022 to C030, C032 to C040 and C043 to C050. Now: A is C011 to C050
  (plus C051 outside the range), B is C001 and C005 only, C is C002 to C004 and
  C006 to C010. Evidence: `docs/challenge_census.md`, tree of commit
  `a623568e`.
- C011 mutations: 32 → 40 mutation files, all rejected in a re-run. Evidence:
  `omega_engine_projects/mssn_sn_symgam/challenges/b_cohomology/c011_cycle_rank_ladder_coboundary_repair/judge_packet/mutation_suite/`.
- C021 tests: "38 passed end-to-end tests" → withdrawn (that was the number of
  test functions in `challenges/e2e_tests/`, not run here); 40 mutation files
  rejected in a re-run. Evidence: the C021 `judge_packet/mutation_suite/`.
- C031 tests and mutations: "71 passed tests" → withdrawn; "36/36 mutations" →
  45 mutation files, all rejected (47 tests in that file); 9 reference-solver
  tests passed. Evidence: the C031 `judge_packet/mutation_suite/` and
  `tests/test_reference_solver.py`.
- C041 toolchain: `v4.34.0` → Lean 4.34.1, as recorded by the package.
  Evidence: C041 `judge_packet/generate_cases.py`.
- C001: "evaluated eager distractor-key masking ... across 200 tasks" →
  withdrawn; no measurement is retained, and the 200-case module is a synthetic
  fixture. Evidence: C001 `mcnemar_arms_evaluation.py` and
  `empirical_neural_mcnemar_evaluation.py`.
- C005 Arm 2: "37/50 (74.0%)" → 36/50 in the three-arm run and 38/50 in the
  hybrid run. Evidence:
  `omega_engine_atlas/coda_atlas/omega_engine_pfp/c005_structured_decoding_controls_empirical_results.md`.
- C005 p-value: "p = 0.035" → exact two-sided p = 145499/4194304 ≈ 0.0347 for
  b = 6, c = 17, with the other three tables' exact p-values added. Evidence:
  the same report; computed from b and c.
- C005 spend: "$0.13528 total spend across four arms" → withdrawn; the report
  gives $0.13528 as its total across all C005-related runs, not the four arms.
- C005 protocol: the model-size rule was quoted as binding; now the deviation
  is stated (a 405B model and a $2.00 per-run ceiling against at most 70B
  parameters and $0.10 per arm). Evidence: `01_challenge_protocol.md` and
  `a_mechanism/c005_hosted_decode_controls_bakeoff.md` in the challenge folder.
- C005 interpretation: "prompt and schema complexity can degrade
  autoregressive model accuracy" → a single-model, single-case-set observation.
- SG-CP v1 summary: ceilings "≤ $0.50 to $1.00 per arm" → $0.10 (T1) to $5.00
  (T5) per arm; "falsification suites ... with 100% target kill rates" →
  mutation suites of corrupted outputs that the checker must reject; "float
  firewall ... rejecting binary floats" → exact arithmetic, with floating-point
  checks allowed as labeled secondary evidence. Evidence:
  `01_challenge_protocol.md`.
- Retraction trials: "Across 28 benchmark trials" → eight traces, one per
  model and condition. Evidence:
  `research/mssn_sn_tower/demos/demo_1/benchmark_report.md`.
- Baseline condition: Llama "0/4 with an average of 5.2 stationary loops" →
  0/1, loop count 5; Qwen "0/4 with an average of 6.0" → 0/1, loop count 6.
- Hinted condition: "stationary loops drop to ≤ 1.0 ... 4/4 ... within an
  average of 8.8–11.0 turns" → Qwen 1/1 (loop count 1, 9 turns) and Llama 1/1
  (loop count 4, 12 turns). The hinted prompt supplied the full repair move,
  so it is an assisted condition; it was earlier described as injecting only a
  boundary vector.
- Scratchpad condition: "100% convergence in tested instances" → 1/1 per
  model; the prompt's worked example contained the repair values.
- "Φ1 = 0.000" → Φ1 = 0.
- Hamiltonian terminals: exact cancellation on `2site_TFI`,
  `4site_tightbinding` and `2site_attractive_hubbard` → withdrawn as host false
  acceptances. Evidence: `research/mssn_sn_tower/demos/anti_morphism_observations.md`.
- Triangular plaquette: "cannot be eliminated by any 1D discrete gauge
  transformation" → only the odd-cycle fact that no site signs satisfy
  η_u η_v = −1 on every edge; no sign-problem classification. Evidence:
  `research/mssn_sn_tower/demos/demo_2/traces/demo2_r5_frustrated_triangular_1790208154.jsonl`.
- Diamond and K4: "local greedy moves created infinite 2-cycles, whereas cycle
  decoupling guidance enabled single-turn diagonal factorization" → withdrawn.
- Narrowest claim: prompts "separated solvable gauge repairs from irreducible
  topological obstructions" → the host's exact check decides acceptance, and
  the small models proposed the correct repair only when the prompt contained
  it.
- Next test: reference solvers for C012 and C022 → closed; both packages are
  delivered with retained scoring receipts.
- Package tests and runner: "14 passing unit and live API tests" and "both
  mock and live execution validated" → 24 offline tests; no live run is
  reported.
- The manuscript's nonclaim list no longer uses internal governance wording.

### Added

- `lean4/` with byte-identical copies (plus a provenance header) of
  FlowCertificate.lean, Level16IndObject.lean, Level21DiscreteRegge.lean,
  Level22FibredDependentContexts.lean and Level23SheafDescent.lean and the
  ExactRat library, a Lake file pinned to Lean 4.34.0, `Census.lean`, and
  `axiom_report.txt` listing 39 theorems: 38 depend on no axiom beyond propext
  and Quot.sound, and one also depends on Classical.choice.
- `docs/challenge_census.md`, `docs/descriptions.md`, `docs/references.md`.
- `zenodo_metadata.json`, `LICENSE`, `LICENSE-CODE`, `verify_deposit.py`,
  `code/deposit_paths.py`, `tools/rebuild_release.py`,
  `tools/replay_lean_axiom_census.py`, `scripts/regen_sha256sums.py` and
  `scripts/build_deposit_zip.py` from the paper template kit.
- Pinned ruff, pytest and mypy configuration in `pyproject.toml`.

## [1.1.0] - 2026-09-28

The figures this version added to Sections 9 to 12 are withdrawn or corrected
in 1.2.0.

### Added

- The C001–C050 challenge framework, the SG-CP v1 protocol summary, and a
  three-way status classification taken from
  `symbol_game_challenge_and_demos_findings/challenges_findings_and_updates.md`.
- C005 bake-off results on a 405B model and a C001 masking summary.
- Retraction benchmark summaries, a stationary-loop analysis, and hint-based
  guidance from the same findings file.
- `retraction_benchmark_runner.py` with live and offline modes and a spending
  ceiling, and an expanded package test file.
- Claim ledger rows PFP008-11 to PFP008-15.

## [1.0.0] - 2026-09-28

### Added

- Initial research paper on MSS-N tower challenges, later narrowed.
- An 11-element front matter following the repository standard at the time.
- A statement that 52 Lean 4 payload modules were verified within the axioms
  propext and Quot.sound; later revisions withdrew it as current evidence.
- 150-test benchmark execution logs and hashes; later revisions withdrew them
  as scientific evidence.
- A mechanism inventory table with 14 compliance slots.
- The release claim ledger `paper_claim_ledger.md`.

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 1.2.0 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.
