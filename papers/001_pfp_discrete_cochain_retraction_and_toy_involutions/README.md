# PFP I: Exact Graph Repair and the Boundary Between a Proposal and a Certificate

Jeremy H. Carroll. Version 0.1.0, 2026-10-02. Author-review preprint.

This package holds Paper 001 of the Proposal Fidelity Protocol (PFP) series.
PFP is the current name; the legacy name Symbol Game remains in source paths
and identifiers. Read the [manuscript](paper.md), the
[claim ledger](paper_claim_ledger.md), and the [change log](paper_change_log.md).

## Contents

- `paper.md`: the manuscript. The PDF, TeX source, checksum manifests, and
  release archive are generated from the package by the series build.
- `code/symbol_game_governor.py`: the paper-local Python reference. It builds
  and independently checks the primal and dual certificate of Section 3 on
  small graphs, and its governor admits only strictly decreasing updates.
- `code/rust/`: the native Rust solver. It returns the exact minimum and a
  minimizing potential by spanning-forest enumeration capped at 100,000
  forests. It returns no dual certificate.
- `code/native_functional.py`: the exact Python adapter to the Rust executable.
- `code/demo1_holonomy.py`, `code/demo2_bqnf_fsign.py`,
  `code/run_adversarial_debate_benchmark.py`, and `code/run_demos.py`: offline
  demonstrations. Demo 1 replays the manuscript's worked witnesses; Demo 3
  replays a deposited historical debate trace.
- `code/live_adversarial_demo.py`: the optional live debate demo (see below).
- `code/exact_fock_gap.py` and `code/fock_path_enumerator.py`: the retained
  Fock path checker; the example itself is developed in Paper 002.
- `code/tests/`: pytest files.
- `code/generate_figures.py`: regenerates
  `public_export/fig1_descent_and_obstruction.png` from exact governor runs.
- `jupyter_notebooks/`: three companion notebooks with stored outputs from a
  Python 3.12 kernel. They run from this folder or from `jupyter_notebooks/`.
- `lean4/`: three small Lean files, `Census.lean`, and the axiom report.
- `results/` and `specs/`: historical receipts, model traces, and contract
  files from earlier revisions. They are not current execution evidence.
- `docs/`: the description, references, and a scope supplement.
- `verify_deposit.py`, `tools/`, and `scripts/`: release tooling.

## Toolchain for this revision

- Python 3.12.10 (Windows launcher `py -3.12`), pytest 8.3.5, and ruff
  0.14.13; the ruff rule selection is pinned in `pyproject.toml`.
- matplotlib 3.10.8 for the figure; nbclient 0.10.2, nbformat 5.10.4, and
  ipykernel 7.3.0 for notebook replay.
- cargo and rustc 1.98.0 for the Rust crate.
- Lean 4.34.0-rc1, pinned in `lean4/lean-toolchain` and installed with elan.
- Pandoc 3.7.0.2 and XeTeX (MiKTeX 25.12) for the PDF.

## Running the checks

Run these commands from this folder. On systems without the Windows launcher,
replace `py -3.12` with a Python 3.12 interpreter. Run one test file per
command.

```powershell
py -3.12 -m pytest code/tests/test_manuscript_witnesses.py -q
py -3.12 -m pytest code/tests/test_review_regressions.py -q
py -3.12 -m pytest code/tests/test_zenodo_regression_suite.py -q
py -3.12 -m pytest code/tests/test_governor.py -q
py -3.12 -m pytest code/tests/test_certificate_gate.py -q
py -3.12 -m pytest code/tests/test_exact_fock_gap.py -q
py -3.12 -m pytest code/tests/test_fock_path_proposition.py -q
py -3.12 -m pytest code/tests/test_proposed_boundaries.py -q
py -3.12 -m ruff check code

cargo test -j 1 --manifest-path code/rust/Cargo.toml
cargo build -j 1 --manifest-path code/rust/Cargo.toml --bin solve_graph_phi1

py -3.12 code/run_demos.py --all
py -3.12 code/generate_figures.py

cd lean4
lake build
lake env lean Census.lean
cd ..

py -3.12 verify_deposit.py
py -3.12 tools/rebuild_release.py --check
```

`verify_deposit.py` checks the checksum manifest and the two-way file census.
It also runs named test files with `--test code/tests/<file>` and the Lean
build and axiom census with `--lean`. `tools/rebuild_release.py --check`
checks the release archive against the manifests.

## Optional live debate demo

The live demo calls the OpenRouter service and is not part of the paper's
evidence. It needs your own OpenRouter key. Export `OPENROUTER_API_KEY`, or
copy `.env.example` to a private file such as `.env`, replace the placeholder,
and name that file on the command line. No directory is searched for
credentials, and `.env` is excluded from the deposit.

```powershell
py -3.12 code/run_demos.py --demo 3 --live --output-dir <new-directory> --env-file .env
```

Each run writes its trace and receipt to the new directory named by
`--output-dir`.

## Verification receipt

The complete package test suite, code lint, Lean build, notebook execution, and
Rust cargo tests are recorded in
`docs/release_validation_2026_10_02_review_repairs.json`. Follow-on targeted
checks (Demo 1 string potentials, BQNF route aliases, and worksheet
verification) are recorded in
`docs/release_validation_2026_10_02_continued_review.json`. Each receipt lists
its specific commands, tool versions, exit status, and tested scope. The Rust
unit tests run with the `cargo test` command above. Receipts in `results/` and
the earlier validation files keep their original dates and scope.

## License

Text, figures, and documentation: CC BY 4.0 ([LICENSE](LICENSE)). Code, Lean
files, notebooks, and tooling: PolyForm Noncommercial 1.0.0
([LICENSE-CODE](LICENSE-CODE)).

## Zenodo Preprint Deposit

Zenodo Record: <https://zenodo.org/records/23114044> (DOI: `10.5281/zenodo.23114044`, v0.1.0 Preprint).
Published October 3, 2026. Earlier internal revision 1.3.0 and its corrections are preserved in the
change log and historical evidence. No external peer review or acceptance is claimed.

The current package-local execution records are
`docs/release_validation_2026_10_02_review_repairs.json` (complete package suite,
Lean build, notebook execution, and adapter/governor SHA-256 bindings) and
`docs/release_validation_2026_10_02_continued_review.json` (follow-on checks run
after the continued 2026-10-02 review). `docs/release_validation_2026_10_02.json`
and `docs/release_validation_2026_10_01.json` keep their original dates and scope.
The cited code baseline `c819bec432446dd3c9b1edf1583384cfe76c6c71` is the
pre-repair source pin. It does not identify the repaired adapter and governor.
