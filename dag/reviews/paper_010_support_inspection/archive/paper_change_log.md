# Change log: PFP X (Paper 010)

## 2026-10-03 — Zenodo deposit publication (v0.1.0 Preprint)

Recorded canonical Zenodo record <https://zenodo.org/records/23115720> (DOI: `10.5281/zenodo.23115720`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## 2026-10-02 — UTF-8 manuscript body

`tools/render_paper.py` reads Pandoc's `body.tex` as UTF-8. With UTF-8 mode off, the locale read turned U+00A7 into U+00C2 U+00A7 before the TeX was written. `code/tests/test_render_paper.py` calls `render()` under that mode.

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

## 2026-09-30: version 2.0.2

### Changed

- Replaced references to branch `claude/mssn-study-corrections` with the specific commits `e6fbc15cf` and `e2f7a3500`.
- Recorded formal-mathematics baseline replay verification at commit `fce9c4763`.
- Bumped package version to 2.0.2 across manuscript, metadata, and documentation.

## 2026-09-29: version 2.0.1 (erratum)

Version 2.0.0 reported the C045 to C050 pilot counts without saying what the
prompts disclosed. This erratum corrects that. No new model runs were made, and
no count in Table 3 changes; what changes is how the counts may be read.

### Corrected

- Section 4.1 and the abstract: each C045 to C050 runner sent `Case ID: <id>`
  before the case data (runner lines 219, 270, 221, 163, 264 and 236), and the
  identifiers name the expected result for 36 of the 60 cases in the six panels
  whose runner is retained (for example `c045_m02_trefoil_identify`,
  `c045_m09_refusal_corrupt_edge`, `c046_m05_check_non_confluent_group`,
  `c047_m07_prand_decoy`, `c048_m01_solv_11_m2`, `c048_m02_solv_pyth` and
  `c049_m05_no_product_disc2`). The C045, C046, C049 and C050 runners also sent the
  whole case record, including the `note` of the poisoned cases. Table 3's counts
  are now described as counts under leaked labels, which do not measure unaided
  performance and can be read at most as upper bounds on it. New Table 4 counts
  the identifiers by what they name.
- Section 4.1: in C045 and C046 both checkers accept a refusal with any listed
  reason on every case, so an answer that refuses every case passes 10 of 10,
  more than any model. Table 4 gives the best score of an answer that needs no
  mathematics for each panel (10, 10, 0, 3, 2 and 1).
- Section 4.2, "The second checkers" (widening residual O-03): the C045 and C046
  second checkers accept `{}`, a bare abstention and any refusal with a reason and
  a witness on all ten cases;
  the C047 second checker accepts an empty coefficient list and an empty list of
  minor rows on 9 of 10; the C048 second checker accepts any out-of-scope answer
  on all ten; the C049 second checker accepts a constant "does not exist" on 8 of
  10. Version 2.0.0 said only that the second checker accepted the empty answers
  of C045 and C046 and one C047 certificate.
- Section 4.3: the C044 runner wrote its report outside the repository, not to an
  ignored directory inside it, and it sent each example's `note`, which names the
  group or the expected verdict ("Quaternion group Q8" and others). The C043 prompts
  carried no note.
- Sections 3.1 and 5: `stealth/space-bunny-alpha` is described as a new free
  stealth model offered on OpenRouter as of 2026-09-28, whose provider does not
  disclose its identity, size or training; its results are exploratory, fall
  outside SG-CP v1 §2, and may not be reproducible after the stealth period.
  Version 2.0.0 said the results "cannot be reproduced".
- Section 5: the limitations now state that the formal-mathematics prompts named
  the expected result, and that the C045 to C050 checkers are replayed by a
  collection script outside the package.
- Sections 4.2 and 4.3 now say what the later harness corrections changed (commits
  `e6fbc15cf` and `e2f7a3500`): independent second checkers in C045 and C046, no empty
  certificates in C047, a real non-integer coefficient for out-of-scope answers in
  C048, opaque per-run tokens in the C043 to C050 runners, and a C044 runner that
  sends no `note` and writes into the run store. Table 3 is unchanged, and the
  C045 and C046 exact checkers still accept any refusal (residual O-06).

### Added

- The replay `tools/replay_formal_math_baselines.py` of the collection, with its
  record `verification/formal_math_baselines.json`. It extracts the checkers from
  the run commits with `git archive`, parses the runner panels without running the
  runners, and calls no model (Section 4.4 lists the commits).
- Claim ledger rows PFP10-37 to PFP10-40; rows PFP10-28, PFP10-31, PFP10-34 and
  PFP10-35 revised.

### Package changes

- `paper.md`, `paper_claim_ledger.md`, `README.md`, `docs/descriptions.md`,
  `zenodo_metadata.json` and `pyproject.toml`: version 2.0.1, dated 2026-09-29.

## 2026-09-28: version 2.0.0 (rescope)

This revision rescopes the paper to what the retained evidence supports. The title
changes from "PFP X: Multi-Scale Epistemic Immune Orchestration, Hierarchical
Holonomy Decimation, and Autonomous Challenge Verification" to "PFP X: Exact Host
Checking of Model Verdicts on Small Finite Algebraic Challenges — Lattice Holonomy
and Six Formal-Mathematics Pilots". The version 1.0.0 files remain in the
repository history at commit `35e3d7ba2e0e20904d17a79cc395980f50a1a0f1`. No new
model runs were made.

### What the paper now contains

- The package folder was renamed from `010_pfp_multi_scale_epistemic_immunity_and_hierarchical_holonomy_decimation` to `010_pfp_holonomy_checks_and_model_pilots`: the
  old words did not describe the content, and the dated release archive's path
  exceeded the Windows path limit.
- A complete flatness check for finite-group connections on square lattices
  (`code/holonomy.py`): every plaquette product in a fixed orientation, inverses on
  reversed edges, the two torus cycle products, and the verdicts `FLAT_TRIVIAL`,
  `FLAT_NONTRIVIAL` and `NOT_FLAT`, with a separate certificate check.
- Tests of the checker (`code/tests/test_holonomy_checker.py`) and a replay of the
  five retained C017 cases and the retained model certificates
  (`code/tests/test_c017_replay.py`, `code/replay_c017.py`, `code/data/c017/`).
- Exact per-arm C017 counts recomputed from the retained reports, with the models,
  prompts, settings, n and report paths.
- A table of the retained C045 to C050 runs, n = 10 per cell, including the second
  C049 panel and the first C050 run that version 1.0.0 did not report.

### Corrected

- The function `decimate_and_evaluate_holonomy` in the removed test module was
  wrong: it never multiplied group elements, it returned `NOT_FLAT` for any
  plaquette containing a non-identity link (wrong for gauge-trivial connections),
  it labelled the all-identity connection `FLAT_NONTRIVIAL`, and it never computed
  the two torus cycle products. It is replaced by `code/holonomy.py`.
- "24 out of 30 plaquettes consist entirely of identity links" (`base_03`) is
  corrected to 20 of 30.
- "The model evaluated only the two non-contractible homology cycles" is corrected:
  the retained reply evaluates the 10 plaquettes that contain a non-identity link
  and the two cycles. The flatness of all 30 plaquettes is now established by the
  host check, not by the model's reply.
- "Theorem SG-T1" (four identity links give the identity product) is relabelled a
  remark; the Lean declaration is renamed `identity_links_give_identity_product` and
  its group structure now includes all group laws.
- The C017 arms are described by what each prompt contained; the 0 of 5 results of
  Arms 1 and 2 are explained by the unstated vertex-order convention (three and two
  rejections respectively) rather than by "coordinate chirality inversions".
- The C017 lattice sizes are taken from the case files (for example, `base_01` is
  $3 \times 4$ and `base_13` is $4 \times 5$).

### Withdrawn or narrowed claims

- Abstract: prompt-level constraints "converge to zero-defect certificates" on
  commutative sign cancellations and "fail completely (0% pass rate)" on
  nonabelian holonomy "due to coordinate chirality inversions and constructive
  spanning-tree confirmation biases" — withdrawn; replaced by the per-arm counts and
  the vertex-order explanation.
- Abstract: decimation "resolving the 8,000-token completion ceiling barrier",
  "reduced completion tokens from >8,000 to 2,810" and "raising benchmark pass
  rates from 0% to 80.0%" — narrowed to one case with one reply per arm (8,000 and
  2,810 completion tokens for `stealth/space-bunny-alpha` in Arms 5 and 6) and to
  per-run counts of 0, 0, 3, 3 and 4 of 5 across different prompts and models.
- The mechanism inventory table and definitions SG-D1, SG-D2 and SG-D3 — removed;
  SG-D2 is replaced by the remark in Section 2.3.
- Section 1.1, the convergence and compression results cited from the fermion-sign
  benchmark — withdrawn. In the lexically filtered meron-cluster pilot (Paper 011),
  no unassisted prompt produced a passing answer (0 of 9 cells, one run each), and
  every passing run followed a prompt that contained the answer; that pilot supports
  no claim about model capability.
- Section 1.2: "Pinned coordinate grammar tokens eliminated this orientation
  mismatch, enabling 100% pass rates on open non-flat instances" — narrowed to 3
  of 3 open non-flat cases accepted for each model in Arm 5, which also changed
  other parts of the prompt.
- Section 1.2: the "pure gauge fixation pathology" (a spanning-tree instruction
  biased models towards `PURE_GAUGE`, "0% pass rate"; "curvature-first plaquette
  rejection must strictly precede gauge-fixing") — withdrawn; no retained run
  supports it.
- The two flow diagrams (including "Arm 5 Hybrid: 60% Pass Rate" and "Arm 6
  Hierarchical Decimation: 80% Pass Rate") — removed.
- Section 2, the five-stage prompt filter, all withdrawn: kinetic proofreading
  "reducing premature rollback by 40%"; peptide decomposition and list screening
  "reducing prompt token footprints by up to 83.5% and improving proposal accuracy
  by +50%"; the four-label scratchpad check ("transcripts omitting any of these four
  stages are refused deterministically"); the quorum gate with a Hill-type
  activation ($n_H = 2$) over five listed Unicode symbols and the "complement
  cascade" halt, where the code only counted symbols in the prompt and did not use
  the activation function; and the six-row defence matrix marking every mechanism
  PASS. One plain paragraph in Section 1 now states what each function computed and
  that no effect was measured.
- Section 2.5: rejected proposals "hashed using RFC 8785 canonical JSON, bound to
  Blake3/SHA-256 digests, and appended to the immutable" hash-linked store —
  withdrawn. The collection's failure store (Paper 006) is a linear SHA-256
  predecessor chain whose file is rewritten on each append, uses a sorted-key JSON
  encoder that is not full RFC 8785, and is not immutable.
- Section 3.3: "latency dropped to 16.32 s" — removed.
- Section 4: "mutation suites achieving 100% mutation kill rates (512 base cases
  verified, 384 hostile mutations killed)" — narrowed to the retained C043 and C044
  scoring receipts (128 cases and 96 mutations, reference solver only).
- Section 4.1 table: the C043 row (5, 1 and 1 of 10) and the C044 row (3, 3 and 3
  of 10) — withdrawn, because their run reports are not retained; the "Billed Spend"
  column and the total of \$0.01600 — withdrawn (harness-computed prices, not
  provider bills); the totals 43/80 (53.8%), 38/80 (47.5%) and 27/80 (33.8%) —
  withdrawn; the C049 row (9, 6 and 6) — now shown with the second panel (5, 6
  and 4); the C050 row (6, 3 and 1) — now shown with the first run (7, 4 and 1).
- Section 4.1: `stealth/space-bunny-alpha` described as a "frontier long-chain
  reasoning model" — replaced by the statement that it is an unidentified model
  whose results cannot be reproduced.
- Section 4.2: "attained perfect convergence (10/10, 100%)" on C048 and "9/10 (90%)"
  on C049 and "verified natural transformations, triangle identities, and Serre
  Hilbert symbol valuations without falling for adversarial poison bait" — narrowed
  to the counts in Table 3; the descriptions of mechanism are removed.
- Section 4.2: the "reasoning buffer exhaustion boundary" (internal chain of thought
  "exceeded output token limits", dense models "constrained by concise decoding")
  — replaced by the harness completion limits and the recorded token counts.
- Section 4.2: the conclusion that absence proofs remain a capability of symbolic
  algorithms alone — withdrawn; narrowed to the three C047 cases without a
  recurrence within the bounds.
- Section 5: the seven-stage pipeline and its evaluation "50/50 (100.0%)" on 37
  sound complexes and 13 constructed decoys (3, 2, 3, 3 and 2 rejected at stages 2,
  3, 4, 5 and 7) with "zero false positives" — withdrawn; no runner, report or
  receipt is retained, and the decoys were built to trip specific stages.
- Section 6.1: "All calculations use exact rational arithmetic (fractions.Fraction)
  and integer bitmasks" — replaced; the checker uses table lookups on element
  names.
- Section 6.2: the claim that the multi-stage filter intercepted every tested decoy,
  the "narrowest defensible claim" of higher verified consensus rates, and the
  proposed Lean export of quorum certificates — withdrawn.
- Claim ledger rows of version 1.0.0: PFP-01 (the identity-plaquette statement)
  and PFP-03 (reversal inverts a plaquette product) are replaced by PFP10-15 and
  PFP10-05, which now have a Lean lemma and a test. Removed because the new paper
  does not make them: the sign-cancellation statement for four-site chains
  (PFP-02); the six code-inspection rows for the removed functions; the
  fermion-sign benchmark row (receipt `REC_FSP_BLIND_1790605314`); the C005 row (50% to
  74%, $p = 0.035$, \$0.13528), which the manuscript never discussed; the C048 and
  C049 rows citing run folders outside the repository; and the three open
  obligations (Wave 3 challenges, larger Lean models, GPU kernels on H200 nodes).

### Package changes

- `paper.md`, `paper_claim_ledger.md`, `README.md`, `docs/descriptions.md`,
  `docs/references.md` and `zenodo_metadata.json` rewritten for version 2.0.0. The
  header no longer carries the internal catalog address, council code or effect
  label.
- `docs/references.md`: six self-citations with placeholder Zenodo DOIs
  (10.5281/zenodo.1000000 to 10.5281/zenodo.1000008) that identify no deposited
  record removed; Hopfield (1974), Ninio (1975) and Troyer and Wiese (2005) removed
  because the paper no longer cites them; Kogut (1979) and Hatcher (2002) added.
- `completion_supplement.md` moved to `docs/completion_supplement.md` and rewritten
  for the new code.
- Added `code/holonomy.py`, `code/replay_c017.py`, `code/data/c017/` (five case
  files, `provenance.json`, `model_claims.json`),
  `code/tests/test_holonomy_checker.py`, `code/tests/test_c017_replay.py` and
  `docs/lean_claim_map.md`.
- Removed `code/tests/test_010_adversarial_refusals_and_decimation.py`: its
  holonomy function was wrong (see above) and its other functions supported only
  the withdrawn filter claims.
- Removed `lean4/NonAuthority.lean`, which the paper does not use; added
  `lean4/axiom_report.txt` and the generated `lean4/Census.lean`.
- Added the template release tools `verify_deposit.py`, `tools/rebuild_release.py`,
  `tools/replay_lean_axiom_census.py` and `scripts/build_deposit_zip.py`, and
  replaced `scripts/regen_sha256sums.py` with the template version; their exclusion
  sets cover `.env`, `target/`, `.lake/`, `build/`, `dist/` and cache folders.
- `pyproject.toml`: version 2.0.0, license text, pinned ruff, pytest and mypy
  settings; the incorrect MIT classifier removed.
- `LICENSE` now holds the full Creative Commons Attribution 4.0 legal code, and
  `LICENSE-CODE` the PolyForm Noncommercial 1.0.0 terms that the package
  description already declared, replacing a truncated Apache-style fragment.

## 2026-09-28: version 1.0.0 (first release)

- First release of the manuscript, claim ledger, README, companion notes,
  metadata, a Python test module and a two-file Lean project; the paper was added
  to the collection catalog. The statements of this release that version 2.0.0
  withdrew or corrected are listed above.

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 2.0.2 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.


## Initial v0.1 preprint publication review — 2026-10-02

This entry concerns the initial public preprint candidate, version 0.1.0. Earlier
1.x/2.x entries remain internal draft history; no Zenodo publication or DOI is claimed.

- Refuse duplicate parsed edge/gauge names before overwrite, validate unknown and
  non-string links before inverse lookup, and return typed errors for malformed
  group shapes and empty cycles. Add regression controls and check original LF case bytes.
- State open-lattice dimension bounds, explain the three-way verdict and its cost,
  and distinguish gauge invariants from the gauge-dependent identity-link optimization.
- Clarify the 15 retained C017 solution records: 13 parsed certificates and two
  parser-error wrappers, with 10 accepted/5 rejected overall; ten other payloads are missing.
- Include byte copies of 15 historical evidence files with pinned source hashes;
  verify 25 C017 extraction entries and recount Tables 3/4 offline. These are historical
  report audits, not new model trials or fresh C045–C050 checker executions.
- Narrow the second-checker inference to the cited controls, distinguish C049's
  different panels from C050's repeated panel, and mark the external C044 file claim
  as an earlier review report that was not independently checked here.
- Expand the Landau companion to 24 questions in eight levels, worked study notes,
  a separate instructor key and an executable capstone. The practice rubric is
  not a learner study or an examination attributed to Landau.
- Align metadata, description, keywords and development requirements to v0.1;
  deposit a Pandoc/XeLaTeX renderer with wrapping for literal source identifiers.
- Preserve historical validation and Lean reports. The current package-local
  review receipt records actual executions and the unexecuted pinned Lean build.
