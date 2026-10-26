# PFP II: Signed Certificates, Resumable Search, and a Restricted Path-Pairing Obstruction

Jeremy H. Carroll. Version 0.1.0, 2026-10-02. Author-review preprint.

This package holds Paper 002 of the Proposal Fidelity Protocol (PFP) series.
PFP is the current name; the legacy name Symbol Game remains in source paths
and identifiers. Read the [manuscript](paper.md), the
[claim ledger](paper_claim_ledger.md), and the [change log](paper_change_log.md).

## Contents

- `paper.md`: the manuscript. The PDF, TeX source, checksum manifests, and
  release archive are generated from the package by the series build.
- `code/genesis_alpha/sign_graph.py`: the exact signed-graph checker. It returns
  a vertex-sign assignment or an odd closed walk, and separate verifiers check
  either witness.
- `code/genesis_alpha/frontier_search.py`: deterministic bounded search with
  replayable `UNKNOWN` receipts and presentation-keyed retrieval.
- `code/exact_fock_gap.py`: the exact rational checker for the Fock example of
  Section 6. `code/fock_path_enumerator.py` is a floating-point display of the
  same proposition, and `code/certificate_gate.py` holds finite certificate
  checks shared with Paper 001.
- `code/demo1_signed_gauge.py`, `code/demo2_frontier_search.py`,
  `code/demo3_fock_obstruction.py`, and `code/run_demos.py`: offline
  demonstrations.
- `code/rust/` and `code/native_sign_graph.py`: an optional native Rust
  implementation of the graph checker and its Python adapter (see below).
- `code/live_proposer_demo.py`: the optional live proposer demo (see below).
- `code/tests/`: pytest files. `code/PROVENANCE.md` records the origin and
  hashes of the files copied from the author's Genesis workspace.
- `jupyter_notebooks/signed_exchange_and_frontier.ipynb`: a companion notebook
  with stored outputs; it runs from this folder or from `jupyter_notebooks/`.
- `docs/`: the description, references, and an integration note.
- `_lev_landau_theoretical_minimum_quiz/`: the fictional Apartment 50 preface,
  an eight-level, 14-problem quiz, a study guide, and a separate worked key.
  Start with [the study guide](_lev_landau_theoretical_minimum_quiz/study_guide.md).
- `verify_deposit.py`, `tools/`, and `scripts/`: release tooling.

## Toolchain for this revision

- Python 3.10 or later for the standard-library checkers; the reproduction
  commands use Python 3.12 (Windows launcher `py -3.12`).
- pytest 9.0.3 or later and ruff 0.14.13 or later, as declared in
  `pyproject.toml`; the selected ruff rules are pinned there.
- nbclient, nbformat, and ipykernel for fresh notebook replay; their dependency
  ranges are declared in the optional `dev` dependencies.
- cargo and rustc for the optional Rust crate; Pandoc and XeLaTeX for the PDF.

Actual versions and executed scope are recorded in the
[current preprint review receipt](docs/preprint_review_validation_2026_10_02.json).
Historical Windows toolchains and receipts retain their original dates.

## Running the checks

Run these commands from this folder. On systems without the Windows launcher,
replace `py -3.12` with a Python 3.12 interpreter. Run one test file per
command.

```powershell
py -3.12 -m pytest code/tests/test_sign_graph.py -q
py -3.12 -m pytest code/tests/test_frontier_search.py -q
py -3.12 -m pytest code/tests/test_manuscript_examples.py -q
py -3.12 -m pytest code/tests/test_exact_fock_gap.py -q
py -3.12 -m pytest code/tests/test_native_sign_graph.py -q
py -3.12 -m pytest code/tests/test_native_refusals.py -q
py -3.12 -m ruff check code

py -3.12 code/exact_fock_gap.py
py -3.12 code/run_demos.py --all
py -3.12 -I tools/replay_notebook_source.py

py -3.12 verify_deposit.py
py -3.12 tools/rebuild_release.py --check
```

`code/exact_fock_gap.py` prints the 192 rooted three-hop sequences (96
positive, 96 negative) and the exact rational bounds of Section 6.
`verify_deposit.py` checks the checksum manifest and the two-way file census,
and runs named test files with `--test code/tests/<file>`.
`tools/rebuild_release.py --check` checks the release archive against the
manifests.

`tools/replay_notebook_source.py` executes the notebook's plain-Python code
cells in order with assertions enabled. It is a source-calculation replay,
not an interactive Jupyter kernel check or a comparison of stored outputs.

## Optional native Rust checker

`code/rust/` implements the same signed-graph classification and witness
checks. The paper's statements rest on the proofs and the Python checkers.

```powershell
cargo test -j 1 --manifest-path code/rust/Cargo.toml
cargo build -j 1 --manifest-path code/rust/Cargo.toml --bin solve_sign_graph
```

`code/native_sign_graph.py` uses the executable named by the environment
variable `OMEGA_SIGN_GRAPH_BIN`, or else one built in `code/rust/target/`.
When no executable exists it uses the Python checker, and the binary-discovery
test in `code/tests/test_native_sign_graph.py` is skipped with the build
command as its reason. When an executable is found it decides: a native
refusal raises `NativeSignGraphRefused` and malformed output raises
`NativeSignGraphUnavailable`; neither is replaced by a Python answer
(`code/tests/test_native_refusals.py`).

## Optional live proposer demo

The live demo sends two small signed-graph challenges to a model through the
OpenRouter service and checks every answer with the exact local checker. It is
not part of the paper's evidence and needs your own OpenRouter key. Export
`OPENROUTER_API_KEY`, or copy `.env.example` to a private file such as `.env`,
replace the placeholder, and name that file on the command line. No directory
is searched for credentials, and `.env` is excluded from the deposit. Without a
key the demo refuses and exits with a nonzero status.

```powershell
py -3.12 code/run_demos.py --live --env-file .env
py -3.12 code/live_proposer_demo.py --mock
```

The second command runs a labelled offline check that makes no provider call.

## Verification receipt

Current execution evidence for this revision is
[included in the deposit](docs/preprint_review_validation_2026_10_02.json).
It records commands, versions, source hashes, exit statuses, and skips.
The [preprint review](docs/preprint_review_2026_10_02.md) explains the
readiness judgment. Earlier package-local and repository review records
retain their dates and scope. The optional Rust unit tests use the
`cargo test` command above; Python fallback tests are not a native-build
receipt. The 18-test and 19-test counts in `code/PROVENANCE.md` remain historical.

## License

Text, figures, and documentation: CC BY 4.0 ([LICENSE](LICENSE)). Code,
notebooks, and tooling: PolyForm Noncommercial 1.0.0
([LICENSE-CODE](LICENSE-CODE)).

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23114127> (DOI: `10.5281/zenodo.23114127`, v0.1.0 Preprint).
Published October 3, 2026. Earlier internal revision 1.1.0 and its corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.

The current package-local execution record is
`docs/preprint_review_validation_2026_10_02.json`. The earlier
`docs/release_validation_2026_10_02.json` records its own selected checks
and tested inputs and remains unchanged as historical evidence.

