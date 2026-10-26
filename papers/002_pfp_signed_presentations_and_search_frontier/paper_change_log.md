# Paper Change Log — 002_the_symbol_game

## 2026-10-03 — Zenodo deposit publication (v0.1.0 Preprint)

Recorded canonical Zenodo record <https://zenodo.org/records/23114127> (DOI: `10.5281/zenodo.23114127`, Concept DOI: `10.5281/zenodo.23114126`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## 2026-10-02 - First preprint review and Landau companion revision


- Kept the initial publication version at 0.1.0 and reconciled the current
  claim-ledger header, references to PFP I 0.1.0, and README dependencies.
  The review source baseline is e11c07ce90318309f058c8097ffd1c440a8ffb84;
  manifests and the new package-local execution receipt bind revised bytes.
- Made the matrix-exponential convergence argument explicit and added the
  triangle path-expansion bound \(64e^{4\beta}\). This is an absolute
  convergence argument for the stated carrier, not a sampling or general
  sign-problem result.
- Replaced the five-question quiz with 14 scored problems at Levels 0-7.
  Corrected the frontier to eight zero-based candidates, covered full batches,
  both balance proofs, exact matrices, pairing, and every path-length class.
  Separated the worked instructor key from the preparation guide; all required
  companion links resolve within this deposit.
- Repaired native witness decoding: null/missing payloads, nonbinary or
  wrongly typed bits, and malformed walk steps now raise the documented
  NativeSignGraphUnavailable error. Ten fixture-executable regressions verify
  typed failure and absence of a Python fallback.
- Added a portable standard-library notebook-source replay command, with an
  explicit active-assertion guard and an explicit distinction from interactive
  Jupyter kernel verification.
- Added the first-publication review and its execution receipt. Historical
  receipts remain unchanged. The PDF/TeX, checksum envelopes, and dated
  release ZIP are regenerated for this source revision.

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

## 2026-09-28: Version 1.1.0 author-review revision

This revision prepares the package for review. The mathematics and its scope
are unchanged. The manuscript now carries a version number; none was stated
before.

Manuscript:

- Removed the "Mechanism inventory" table. Its apparatus slots were not
  objects used in the paper.

Code:

- `code/native_sign_graph.py` no longer replaces a native refusal with a Python
  answer. Before, a nonzero exit, a non-PASS status, or an execution error fell
  through to the Python checker unless `require_native=True`. Now the Python
  checker runs only when no executable is found; a found executable's refusal
  raises `NativeSignGraphRefused` and malformed output raises
  `NativeSignGraphUnavailable`. New tests: `code/tests/test_native_refusals.py`.
- Section 7 now gives package-local commands (`py -3.12`, one pytest file per
  command, the exact Fock checker, and the demo runner) and points to the dated
  review receipt. Withdrawn: "These commands are reproduction instructions;
  this authoring pass did not run them" and the stale repository-root command
  block. The caveat that historical 18-test and 19-test receipts apply only to
  their dated snapshots is kept.
- Rephrased the sentence about formal proofs without naming a proof assistant:
  this package contains no machine-checked proof of the signed-graph
  implementation, and the small formal proofs of Paper 001 concern their own
  restricted types. The meaning is unchanged.
- Folded floating source links into author-year citations. The Harary
  reference now gives pages 143–146, confirmed on the publisher's landing page;
  the Klassen–Terhal and Troyer–Wiese entries were checked against Crossref.
  Added the companion paper PFP I to the references.
- Replaced the "Verification for this revision" section.

Package:

- `docs/references.md` now matches the manuscript. Placeholder DOIs
  (10.5281/zenodo.1000000 to 1000002) and uncited entries (Zaslavsky; Loh et
  al.; a CODA entry) were removed.
- `docs/descriptions.md` was rewritten and agrees with the Zenodo description.
  `zenodo_metadata.json` now uses the manuscript title, version 1.1.0, and the
  date 2026-09-28. `completion_supplement.md` moved to `docs/`.
- New test file `code/tests/test_manuscript_examples.py` checks the worked
  examples of Sections 1, 2, and 4.
- `code/native_sign_graph.py` no longer searches a machine-specific temporary
  directory for the Rust executable; it uses an explicitly configured path or
  the crate's own build directory. The binary-discovery test now skips, with
  the build command as its reason, when the executable has not been built.
- `code/live_proposer_demo.py` reads the key only from the environment or a
  file named with `--env-file`; it no longer searches parent directories for
  `.env` files. Without a key it refuses and exits nonzero instead of reporting
  an offline mock as a pass; the mock now runs only with `--mock`.
  `code/run_demos.py` passes `--env-file` through.
- `code/PROVENANCE.md` records the current hashes of the four files copied
  from Genesis, with the packaging changes that explain them, while keeping
  the original capture hashes.
- Governance tokens were removed from docstrings, the notebook's first
  Markdown cell, and this log.
- Notebook: a fresh run on a loaded machine split one cell's printed output
  into two stream messages, so it no longer matched the stored cell. Each
  printing cell now sends its output as one message. The code locator now
  looks only in the package root and `jupyter_notebooks/` and no longer names
  a retired repository path. Execution-timing metadata was removed. The stored
  output text is unchanged.
- Release tooling was replaced with the current template versions, which
  exclude `.env`, build output, and caches from manifests and archives. The
  earlier archive had carried a comment-only `.env` file.
- `LICENSE` and `LICENSE-CODE` now hold the full CC BY 4.0 and PolyForm
  Noncommercial 1.0.0 texts in place of truncated excerpts. The code license
  changed from Apache-2.0 to PolyForm Noncommercial 1.0.0, following the
  series packaging contract; the crate metadata matches.
- `pyproject.toml` (version 1.1.0) pins the ruff rule selection and pytest
  configuration. `README.md` and `.env.example` were rewritten.

## 2026-09-28: First-publication review repairs and release freeze

Resolved all four pre-publication blockers and editorial findings identified during the independent first-publication review:

1. **Live parser witness fidelity:** `live_proposer_demo.py` now enforces strict type and membership validation (`type(b) is int and b in (0, 1)`) without mutating floats or booleans, validates every odd-cycle step dictionary against declared vertices and edge bounds without silent dropping, and returns typed refusals for malformed response shapes.
2. **Demo failure propagation:** Demo 1, Demo 2, and Demo 3 now replace bare assertions with explicit runtime checks, enforce expected witness types, ensure unexpected admittance fails, and propagate outcomes through `run_demos.py` with non-zero process exits.
3. **Provenance reconciliation:** Reconciled the current SHA-256 for `tests/test_frontier_search.py` in `code/PROVENANCE.md` (`ACCD534AFF3D0F5AF2C54BFC373194A6AF0A4FEB9E25780230E4CA557830E308`) while preserving historical Genesis baseline hashes.
4. **Native Rust CLI input validation:** `solve_sign_graph.rs` now enforces explicit `mode` validation, rejects unknown operation modes, distinguishes omitted inputs from empty graphs, rejects ambiguous multi-representation inputs, and emits structured error payloads.
5. **Editorial corrections:** Harmonized mechanism inventory to state deterministic batch enumeration rather than branch-and-bound; updated `verify_deposit.py` description as reproduction machinery; labeled Demo 3 sign problem classification field explicitly.

## 2026-09-27: Complete methods revision

Rewrote the canonical manuscript around finite signed witnesses, the exact
matrix adapter, contiguous UNKNOWN receipt replay, and the restricted Fock
integrated-path gap. Added complete proofs, exact worked examples, primary
references, source boundaries, and current reproduction commands. No runtime
files were changed and no tests or builds were run during authoring. Source
baseline: 52cb5457f6c485ba548cfd292f6012a941ed22cf.

Earlier dated test totals and notebook outputs below remain historical;
they are not fresh validation of this revision.

## Retained historical metadata

**Paper:** [The Symbol Game II](paper.md)

**Status:** research draft for author review; no deposit or DOI

## Draft 0.1 — 2026-09-23

- Created a standalone sequel in the structure of Paper 001: [manuscript](paper.md), [claim ledger](paper_claim_ledger.md), and [README](README.md). Paper 001 was consulted only as an untracked style reference in the shared checkout and is not included here.
- Distinguished a free two-point swap presentation, its object quotient, and an additional one-object carrier retaining swap isotropy. Stated the limited scalar descent obstruction without attributing an endogenous fermion to Genesis's parity-blind certified quotient.
- Proved the finite signed-graph parity criterion and its complete fixed-basis diagonal-sign-gauge matrix instance. Kept the rational BQNF packet and partial path-pairing routes separate.
- Specified the Hamiltonian-to-presentation adapter, physical preservation, observables, estimator cost, and transformation grammar needed before a finite certificate can be promoted to a physical sign claim.
- Documented a Gin-style presentation index and the finite deterministic parallel batch baseline. MCTS and live Demo 3 effects remain proposed experiments.
- Reclassified historical Demo 2 R1–R4 terminal strings as unverified trace observations using the corrected Demo 2 and strict Demo 3 source. Recorded 45-test Demo 2 and 14-test Demo 3 passes at merged main `2868e9fa75b562d2dc357abdd5610df081ebf2fb` as code receipts only.

## Draft 0.2 — 2026-09-23: frozen finite companion

- Copied four Genesis finite-code files byte-for-byte into [code/genesis_alpha/](code/genesis_alpha/) and `tests/` (now `code/tests/`). [PROVENANCE.md](code/PROVENANCE.md) records each source path and SHA-256 hash, separating this frozen copy from the mutable live Genesis waystation.
- Ran the paper-local `unittest` suite: **18/18** tests passed. The results cover finite signed graphs, exact matrix gauges, index retrieval, deterministic eight-wide batch enumeration, resumable receipts, and restricted obstructions; they do not establish a physical Hamiltonian adapter.
- Added the [interactive signed-exchange notebook](jupyter_notebooks/signed_exchange_and_frontier.ipynb), with five successfully executed standard-library code cells as an educational companion. Notebook outputs add no theorem or physical certificate.
- Updated manuscript, README, and claim ledger links to use the frozen in-repo implementation.

## Draft 0.3 — 2026-09-24: exact-matrix input binding repair

- Found that one-shot matrix iterators were consumed by validation before hashing, then consumed again before classification: an input containing a positive triangle could yield the digest and gauge certificate of an empty matrix.
- Snapshotted rows before validation/hashing in `exact_matrix_digest` and before digest/classification in `search_exact_matrix`. Added a regression covering both entry points and a mismatched key; the paper-local suite now passes **19/19** tests.
- [PROVENANCE.md](code/PROVENANCE.md) preserves the original Genesis SHA-256 values beside the changed paper-local file hashes. Updated the current manuscript and ledger receipt counts; the dated 0.2 record above remains historical.

## Release boundary

This draft requires author review. Its versioned paper-local finite graph/frontier code is available for portable replay. A publication-level physical classification would additionally need a justified Hamiltonian adapter, a declared completeness domain, preservation of observables, independent held-out replay, and a claim ledger updated to the final artifact.

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 1.1.0 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.
