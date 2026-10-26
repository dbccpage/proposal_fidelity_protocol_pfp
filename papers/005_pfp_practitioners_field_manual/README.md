# PFP V: A Practitioner's Guide to Checked Proposals

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · Initial preprint candidate

Read the [guide](paper.md), or its [PDF](paper.pdf). This instructional companion to the Proposal Fidelity Protocol (PFP), formerly the Symbol Game, follows one exact triangle through declaration, proposal, refusal, repair, verification, and restoration of a saved snapshot. It adds no new theorem or measured model-performance result.

The guide separates a potential adjustment, which preserves the original cycle sum, from replacement of edge claims. The manuscript, worked session, and capstone all use claims (1,1,1) and weights (1,2,3).

- [Landau quiz: 32 questions in eight levels](_lev_landau_theoretical_minimum_quiz/quiz.md)
- [Study guide, worked answers, and capstone](_lev_landau_theoretical_minimum_quiz/study_guide.md)
- [Claim ledger](paper_claim_ledger.md) and [editorial history](paper_change_log.md)
- [Publication review](docs/publication_review_2026_10_02.md) and [fresh execution record](docs/publication_review_2026_10_02.json)
- [Description](docs/descriptions.md) and [references](docs/references.md)

Code baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
Package reviewed at: `e11c07ce90318309f058c8097ffd1c440a8ffb84`, with the local corrections described in the review.

## Run the worked examples

The Python companion requires Python 3.10 or newer and no third-party runtime packages. From this directory, use `python` (or `py -3.12` on Windows):

```powershell
python code/play_demo.py
python code/study_capstone.py
```

With `OMEGA_FUNCTIONAL_GRAPH_BIN` unset, these use exact Python enumeration. Both print the selected calculator path. A configured native calculator's refusal or error propagates; neither substitutes a Python value after that failure. The capstone preserves actual verdicts and snapshot restoration but is not a canonical native receipt.

The native-only [quickstart](code/quickstart.py) requires `solve_graph_phi1`, which is not included in the deposit. In a separate checkout or worktree at the code baseline, confirm the source revision with `git rev-parse HEAD`, then build:

```powershell
cargo build --locked -j 1 --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_functional --bin solve_graph_phi1
$env:OMEGA_FUNCTIONAL_GRAPH_BIN = (Resolve-Path omega_engine/crates_rs/target/debug/solve_graph_phi1.exe).Path
$env:OMEGA_FUNCTIONAL_GRAPH_SHA256 = (Get-FileHash -Algorithm SHA256 $env:OMEGA_FUNCTIONAL_GRAPH_BIN).Hash.ToLowerInvariant()
```

Use the actual output path if Cargo uses a custom target directory, and the native executable name on other platforms. Return to the paper directory and run:

```powershell
python code/quickstart.py --non-interactive
```

The digest pins the executable bytes; source-to-binary provenance requires its own evidence. Section 3 of the guide includes a hand-checkable worksheet that does not need Rust.

## Self-contained Python and documented source copies

The package includes `code/native_functional.py` and `code/l1_symbol_game_governor.py`, with source paths, commits, source-byte SHA-256, and local modifications in their headers. The governor has documented patches to input normalization, exact-value admission, CUT completeness and rollback, and scoped verification. Its Python route refuses unknown claim edges and duplicate carrier entries; supported Edge object keys are normalized on both routes.

`test_vendored_sources.py` checks the unpatched executable structure against the recorded Git objects when they are available. Its explicitly excluded patched functions and methods have behavioral tests in `test_manual_contracts.py` and the earlier boundary tests. The current review also compares the copies with the source bytes retrieved at their recorded commits. That verifies source custody, not a native build.

A section CUT checks the current discrepancy; a replacement CUT checks the quotient minimum. ZERO_OBSTRUCTION and ZERO_DEFECT are different obligations. A stationary score can accompany changed claims, and RETRACT can increase a score when restoring a prior instance. The guide and study key work each distinction explicitly.

## Reproduce checks and release assets

Install the declared development dependencies if needed (`pytest>=9.0.3`, `ruff==0.14.13` in `pyproject.toml`). From this directory:

```powershell
python -m pytest code/tests -q
python -m ruff check code
python verify_deposit.py
python tools/rebuild_release.py --check
```

The fixture reads only caller-supplied native executable and digest pins; it discovers no binary, builds nothing, and writes no pin. Missing configuration skips native-dependent tests. Invalid supplied configuration fails them. Four Git-source comparisons can also skip when their original objects are absent. Skips are recorded separately from passes.

Tests make no external provider calls. Two streaming tests start a local HTTP server on 127.0.0.1. The fresh review uses Python 3.12.14, pytest 9.1.1, and ruff 0.14.13. Its native execution is unavailable, not inferred from historical records. The default deposit verifier checks file custody and structure; the explicit pytest command checks the implementation. `rebuild_release.py --check` additionally checks the deterministic archive.

After editing publication files, run `python tools/render_paper.py` with pandoc and XeLaTeX available to regenerate `paper.tex` and `paper.pdf`, then run `python tools/rebuild_release.py` before the two release checks. The renderer refuses overfull boxes and missing characters; visual inspection is still required. The review records its actual commands and toolchain.

## Historical evidence and initial publication scope

`code/paper_033_execution_receipt.json`, `code/cross_domain_symbol_game_receipt.json`, and the earlier `docs/release_validation_*.json` retain their original bytes, dates, and scope. Re-running legacy scenario scripts writes new files in the working directory. Earlier reported pass counts do not certify the patched package.

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23114578> (DOI: `10.5281/zenodo.23114578`, Concept DOI: `10.5281/zenodo.23114577`, v0.1.0 Preprint).
Published October 3, 2026. Earlier internal revision 1.2.0 and its corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.

For an introduction, start with Paper 000. The [graph mathematics paper](../001_pfp_discrete_cochain_retraction_and_toy_involutions/paper.md) develops the finite theory, and [Paper 004](../004_pfp_native_verification_and_evidence_custody/paper.md) explains native verification and evidence custody.

## 2026-10-23 author-review extension

The current manuscript adds the evidence-bound harness study. New PDFs are built in the collection's `publication/author_review_2026_10_23/` directory. Existing package PDFs, archives and deposited metadata retain their historical identities. See Paper 029 for source mapping and campaign reproduction. The live campaign is NOT_RUN.

Working-tree `MANIFEST.sha256` and `SHA256SUMS` describe the current author-review
revision. Historical release ZIPs and their embedded manifests retain their original
bytes and deposited identities; these working manifests do not redeposit them.
