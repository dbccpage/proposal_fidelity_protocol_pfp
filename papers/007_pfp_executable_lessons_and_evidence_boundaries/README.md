# Designing executable lessons with explicit evidence boundaries

Jeremy H. Carroll · 2026-10-02 · Version 0.1.0 · Initial preprint candidate

Companion 007 is a curriculum-design preprint in the Proposal Fidelity Protocol
(PFP) series; Symbol Game is the legacy name. It develops a finite lesson from a
declared example, worked calculation, first learner prediction, changed-input
probe, and evidence boundary. The rational triangle preserves its cycle sum
under potential adjustments. A deliberate wrong-sign implementation passes a
weak cycle-sum check but fails the predicted-coordinate check.

This package reports no learner study, measured attention half-life,
teaching-efficiency estimate, or transfer-effect result. The 24-problem Landau
quiz and its 96-point rubric are proposed teaching materials.

Source audit baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
Package reviewed from: `b31360060128d992113b602adee326e70d223340`.
External source links are pinned to the audit baseline; local files are the
revised candidate. The [source inventory](docs/source_inventory_2026_10_02.json)
records inspected source hashes and the 20 route notebook identities. The
source-linked route is a reading map, with an old receipt and known API/path
blockers, rather than a fresh 20/20 execution claim.

## Read and study

| File | Purpose |
| --- | --- |
| [paper.md](paper.md), [paper.pdf](paper.pdf), [paper.tex](paper.tex) | Matching manuscript formats |
| [Claim ledger](paper_claim_ledger.md) | Claims and their evidence limits |
| [Change log](paper_change_log.md) | Initial preprint corrections and retained internal history |
| [Study guide](_lev_landau_theoretical_minimum_quiz/study_guide.md) | Worked examples, prediction record, exact worksheet |
| [Quiz](_lev_landau_theoretical_minimum_quiz/quiz.md) | 24 problems at instructional levels 0–7 |
| [Instructor key](_lev_landau_theoretical_minimum_quiz/instructor_key.md) | Separate four-point rubrics |
| [Companion notebook](jupyter_notebooks/007_moving_a_discrepancy.ipynb) | Six standard-library code cells, including the wrong-sign control |
| [Review](docs/first_publication_review.md) | Publication corrections and remaining limits |
| [Fresh validation](docs/first_publication_validation_2026_10_02.json) | Commands, versions, outcomes, tested source hashes |
| [Replay scope](docs/completion_supplement.md) | Current and historical evidence distinctions |
| [Zenodo deposit notes](docs/zenodo_deposit_notes.md) | Record fields and mixed-license declaration |

The Landau preface is fictional examination staging. Read the guide, retain
first predictions, attempt the quiz, and only then consult the instructor key.

## Standalone setup and checks

Use Python 3.12 or newer from this folder. The commands also work in PowerShell;
`python` must name the intended environment.

```bash
python -m pip install -e '.[dev]'
python -m pytest code/tests -q -ra
python -m ruff check code tools/replay_companion_notebook.py tools/check_source_triangle.py tools/build_paper.py
python tools/replay_companion_notebook.py
```

The fraction tests and worksheet need no repository implementation. The printed
Section 3 block test needs repository initialization dependencies and skips in
the standalone archive. The fresh review separately checks those printed
blocks against seven Git-verified DDC modules with parent initialization
isolated; it does not establish full repository integration.

The default replay executes ordinary Python cells in a fresh CPython process
in a temporary working directory. It compares sequential code-cell counters
and normalized output data, and verifies that the deposited notebook was not
changed. These counters are not Jupyter kernel history. Reading stored JSON is
a different check; neither observes a learner.

An optional `--backend jupyter --kernel NAME` replay requires a registered
Python 3.12+ kernel. Jupyter kernel startup was blocked by unavailable socket
operations on the review host. Jupyter rendering and IPython behavior remain
untested.

To repeat the focused source check against an audit-baseline checkout, run
`python tools/check_source_triangle.py --source-root /path/to/checkout`.
The tool checks all seven source hashes before executing the printed blocks;
parent initialization remains isolated.

The legacy timing/metric/status examples remain supplied-value fixtures.
The new counterexample test exposes their substring/status trust boundary;
their chosen thresholds are not calibrated learning standards.

## Formal evidence

The local Lean project is pinned to Lean 4.34.0 and uses no external library.
From `lean4/`, run `lake build`. From the package folder:

```bash
python tools/replay_lean_axiom_census.py --replay .
python tools/replay_full_axiom_census.py .
```

The retained named report selects 21 declarations. The retained full report
lists 64 package-local declarations, including generated/private names and
excluding imported library declarations. Its rows use only `propext` and
`Quot.sound`; `Classical.choice` appears in the permitted whitelist, not as an
observed dependency. The first-publication review verifies source/report
identity and named-census generation, but does not repeat the kernel run:
Lean/Lake are absent on that review host. The successful retained runs remain
historical.

## Build the manuscript

With Pandoc and XeLaTeX installed, run the following from this package:

```bash
python tools/build_paper.py
```

The tool preserves the deposited TeX preamble, regenerates the body from
Markdown, and compiles twice. It keeps build intermediates under the excluded
build directory. Revalidate and rebuild the release manifests after changing
publication files.

## Release integrity

```bash
python verify_deposit.py
python scripts/regen_sha256sums.py --check
python tools/rebuild_release.py --check
```

Default verification checks hashes and the two-way file census. Tests and Lean
are explicit additional operations, not default side effects. Rebuild the
manifests and deterministic archive after an intentional source change:

```bash
python tools/rebuild_release.py
```

The dated fresh validation names the exact tested bytes. The original
`docs/release_validation_2026_10_01.json` and
`docs/release_validation_2026_10_02.json` retain their original bytes and scopes;
they are not fresh validation of the revised candidate.

## Toolchain and licenses

The reproducible development pins are pytest 8.3.5, Ruff 0.14.13, nbclient 0.10.2,
nbformat 5.10.4, and ipykernel 7.3.0. The fresh review records Python 3.12.14 and
the available Pandoc/XeLaTeX versions in its receipt. Lean source remains
unchanged at the pinned toolchain.

Manuscript and documentation: CC BY 4.0 ([LICENSE](LICENSE)).
Code, notebook, and Lean: PolyForm Noncommercial 1.0.0
([LICENSE-CODE](LICENSE-CODE)). For the combined PDF/archive upload, declare
both licenses with their file scopes as described in the
[deposit notes](docs/zenodo_deposit_notes.md); do not infer that code is
relicensed by the manuscript's license field.

The folder was renamed on 2026-09-28 from
`007_pfp_pedagogical_transmission_and_micro_attention_curricula`.
Version 0.1.0 is the first external preprint designation; the earlier internal
1.1.0 history is retained.

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23114712> (DOI: `10.5281/zenodo.23114712`, v0.1.0 Preprint).
Published October 3, 2026. Earlier internal revision 1.1.0 and its corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.
