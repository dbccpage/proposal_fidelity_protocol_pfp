# Paper 008: Conservative Grammar Growth and Source-Bound Evidence

Jeremy H. Carroll. Initial v0.1.0 Zenodo preprint candidate, 2026-10-02.

Read the [manuscript](paper.md), [claim ledger](paper_claim_ledger.md),
[publication review](docs/publication_review_2026_10_02.md), and
[change log](paper_change_log.md). PFP is the current name; Symbol Game
remains in historical source paths and the legacy ID PO-008.

The paper distinguishes the actual MSS-0/MSS-1 round trip from semantic
conservativity, tests each clause of a finite certificate, and audits
historical challenge and model evidence. A package or aggregate success
label is not an execution receipt. The deposit includes the sources needed
for its initial parser/map examples and eight K4 trace inspections.

| Path | Contents |
| --- | --- |
| `paper.md`, `paper.pdf`, `paper.tex` | Manuscript and rebuilt reading formats |
| `paper_claim_ledger.md` | Claim, source and falsifier for each result |
| `code/retraction_benchmark_runner.py` | Strict single-shot scorer, graph certificates and version-2 receipts |
| `code/tests/` | 34 runner, 7 mocked gate and 11 source-example tests |
| `docs/source_archive/` | Thirteen exact parser/map/report/trace files, with revision and hash bindings |
| `lean4/` | Five discussed formal files, ExactRat, 39-theorem and 576-declaration reports |
| `docs/challenge_census.md` | Historical 40/2/8 categories and receipt limits |
| `docs/historical_census_inventory.json` | File identities from the five untruncated historical category trees |
| `_lev_examiner_theoretical_minimum_quiz/` | [16-question quiz](_lev_examiner_theoretical_minimum_quiz/quiz.md) and [worked study guide](_lev_examiner_theoretical_minimum_quiz/study_guide.md) |
| `docs/review_validation_2026_10_02.json` | Fresh review checks, inputs and explicit replay limits |
| `verify_deposit.py`, `tools/`, `scripts/` | Deposit and replay tooling |

From this package directory, use Python 3.12, one test file per command:

~~~powershell
py -3.12 -m pip install pytest==9.1.1 ruff==0.14.13 mypy==1.19.1
py -3.12 -m pytest code/tests/test_008_mssn_tower_retraction.py -q
py -3.12 -m pytest code/tests/test_008_deposit_gates.py -q
py -3.12 -m pytest code/tests/test_008_source_bound_examples.py -q
py -3.12 -m ruff check code
py -3.12 -m mypy
py -3.12 code/retraction_benchmark_runner.py --mock --condition hinted --output-dir <new-directory>
py -3.12 verify_deposit.py
py -3.12 tools/rebuild_release.py --check .
~~~

On Unix, substitute the Python 3.12 interpreter for `py -3.12`. The review
used Python 3.12.14, pytest 9.1.1, ruff 0.14.13 and mypy 1.19.1.
The optional development requirements and static-check configuration are in
`pyproject.toml`; the runtime uses the standard library.

The offline stub reads the prompt. Its match counts are baseline 3/6,
hinted 6/6, scratchpad 3/6 and exact oracle 6/6; these test plumbing and
scoring, not model ability. Baseline and scratchpad exit 1 as expected
negative controls. Outputs go outside the package. JSON witness certificates
remain checkable after reload, and receipt digests bind the complete case,
prompt, raw reply, certificate and declared runner source. Public hashes
detect changes relative to trusted expected digests; they do not authenticate
a provider.

Lean 4.34.0 is pinned in `lean4/lean-toolchain`. With a working toolchain:

~~~powershell
py -3.12 tools/replay_lean_axiom_census.py --check .
py -3.12 tools/replay_lean_axiom_census.py --replay .
~~~

The named replay compares all 39 expected theorem names and axiom sets.
The full retained report covers 576 local environment declarations, including
ExactRat and generated or private names; these are not 576 manuscript
theorems and do not cover the 52 external Level Engine payloads.
The October 2 author receipt's 13 protected source identities and full
census bindings match the unchanged deposited Lean bytes. The fresh review
host could not start the official digest-verified Lean binary, so this review
records that replay as blocked. Mocked gate tests are control-logic evidence.

The review compiled the revised PDF with Pandoc 3.1.3 and XeLaTeX
(TeX Live 2023), using three passes per PDF and checking rendered pages.
Older receipts retain their original toolchain, source hashes and scope;
their older runner, quiz and PDF identities are not current validation.

Live mode requires a process environment key and uses reported cost plus a
fixed next-call estimate. Its nominal budget is not a guaranteed bound on
provider charges. This package reports no live run.

Historical code baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
Challenge census: `a623568eb0f853b968bc419bf06dfc6af256ab02`.
Review baseline: `23893fc44162555fa12ceda3e1665982e3d7a14e`.
Pinned historical paths may differ from current main.

Text and new documentation: CC BY 4.0 ([LICENSE](LICENSE)). Code, Lean
sources, release tools and archived repository evidence retain PolyForm
Noncommercial 1.0.0 ([LICENSE-CODE](LICENSE-CODE)); the archive does not
relicense its sources.

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23115542> (DOI: `10.5281/zenodo.23115542`, v0.1.0 Preprint).
Published October 3, 2026. Earlier internal revision 1.2.0 and its corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.

