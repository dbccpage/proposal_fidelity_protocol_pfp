# Verification of the PFP paper collection, revision of 2026-09-28

This is an execution record for the revision of Papers 001 to 010 and of the
meron-cluster benchmark (`omega_engine_projects/fsp/meron_sign_problem`, called
011 here). It is not a peer review, and it claims no deposit, DOI, or
acceptance. The report of the previous revision is kept as
[report_first_revision_2026-09-28.md](report_first_revision_2026-09-28.md).

- Reviewed commit: `1c7092c3db2ab2fa65999cf2555aff7733b97b99` on branch
  `claude/pfp-paper-review-loop`.
- Run recorded: 2026-09-29, 02:02 to 02:06 UTC (2026-09-28, 22:02 to 22:06 EDT),
  Windows 11, one package at a time.
- Receipts: `_intelligence/omega_paper_reviews/pfp_loop_final2_20260929_020235/`,
  one folder per package with `run_all_receipt.json`,
  `republication_gate_receipt.json` and both logs. An earlier run on the same
  day, `pfp_loop_final_20260929_013741`, found the three defects fixed before
  this run (a path over the Windows limit in 010, and hyphenated Lean file names
  in the PDFs of 001 and 008).
- Open items: [residuals.md](residuals.md).

## Tool versions

Python 3.12.10; pytest 8.3.5; ruff 0.14.13; mypy 1.19.1; nbclient 0.10.2 and
nbformat 5.10.4; PyMuPDF 1.27.1; pdftotext 4.00; Pandoc 3.7.0.2; MiKTeX-XeTeX 4.16
(MiKTeX 25.12); Lake 5.0.0 with the Lean toolchain each package pins
(4.34.0, or 4.34.0-rc1 for 001, 004 and 010); cargo and rustc 1.98.0
(x86_64-pc-windows-msvc).

## Review pipeline, Stages 0 to 6

Command, from the repository root, for each package `<p>`:

```text
py -3.12 -m omega_engine_research_papers.use_cases.paper_review.cli run-all --paper-path <p> --output <receipt> --fuel 0 --no-auto-rebuild
```

Scope: Stage 0 preflight and envelope, Stage 1 dialect firewall and the Old Man
audit, Stage 2 `lake build` where a `lean4/` project exists, Stage 3 figure
generation, every `code/tests/test_*.py` file run separately, and ruff over
`code/`, Stage 4 fresh notebook replay compared cell by cell, Stage 5 three
XeLaTeX passes with no overfull lines and extracted-text equality with the
deposited PDF, Stage 6 `verify_deposit.py` and `tools/rebuild_release.py --check`.
Every command exited 0 and every package's overall status is PASS.

| Package | S0 | S1 | S2 Lean | S3 code | S4 notebooks | S5 PDF | S6 release |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 002 | PASS | PASS | n/a | PASS | PASS | PASS | PASS |
| 003 | PASS | PASS | n/a | PASS | n/a | PASS | PASS |
| 004 | PASS | PASS | PASS | PASS | n/a | PASS | PASS |
| 005 | PASS | PASS | n/a | PASS | n/a | PASS | PASS |
| 006 | PASS | PASS | n/a | PASS | n/a | PASS | PASS |
| 007 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 008 | PASS | PASS | PASS | PASS | n/a | PASS | PASS |
| 009 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 010 | PASS | PASS | PASS | PASS | n/a | PASS | PASS |
| 011 | PASS | PASS | PASS | PASS | n/a | PASS | PASS |

"n/a" means the package has no Lean project or no notebook. The only warning in
Stage 0 is the preflight's request for a mechanism inventory (residual T-01).
Stage 3 runs the tests without native pins, so Paper 005's native-requesting
tests skip there; the native runs are recorded below.

## Republication checklist (Stage Ω)

Command: `py -3.12 -m omega_engine_research_papers.use_cases.paper_review.cli republication-gate --paper-path <p> --output <receipt>`.
Each receipt binds its result to a snapshot digest of the package files.

| Package | Static PASS | Not applicable | Not verified | FAIL | Snapshot |
| --- | ---: | ---: | ---: | ---: | --- |
| 001 | 27 | 0 | 25 | 0 | `71213b982fc6` |
| 002 | 23 | 6 | 23 | 0 | `c8cef914c79f` |
| 003 | 23 | 6 | 23 | 0 | `4320b1548ed4` |
| 004 | 24 | 5 | 23 | 0 | `1fcdfe81253c` |
| 005 | 20 | 11 | 21 | 0 | `ca6869b5fa4f` |
| 006 | 20 | 11 | 21 | 0 | `df864306b8a5` |
| 007 | 27 | 0 | 25 | 0 | `1c648a2cb7a7` |
| 008 | 24 | 5 | 23 | 0 | `ca3acdace7e4` |
| 009 | 27 | 0 | 25 | 0 | `2b04073ebb12` |
| 010 | 24 | 5 | 23 | 0 | `b7dc901aa921` |
| 011 | 24 | 5 | 23 | 0 | `600cd2c6af42` |

No static predicate fails. Each command exits nonzero and reports BLOCKED
because the checklist cannot pass its review, execution, and authorization
obligations by itself: B01 to B06, C04, C05, D02, D04, D05, E02 to E06, E08,
F03, F05, G04, G06, H02, H03, I03 and I04 (where they apply). Section 6 of the
residual register describes them.

## Native runs

These use native executables, which the review pipeline does not build.

- Paper 004: `cargo test -j 1 --locked --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --test <target>`
  for `host_contract` (12 passed), `foundation_contract` (11), `invoke_contract`
  (32) and `native_cli_intake` (9); every command exited 0. The crate's source is
  identical to the code baseline `52cb5457`.
- Paper 005: `cargo build --locked -j 1 --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_functional --bin solve_graph_phi1`
  (exit 0; the crate's source is identical to the code baseline), then each of
  the package's twelve test files with `OMEGA_FUNCTIONAL_GRAPH_BIN` set to that
  executable and `OMEGA_FUNCTIONAL_GRAPH_SHA256` to its digest
  `2b0379557993246cacb1ed8964f9f096964019ecc1c2fb781e6b18f2ca6c8a65`:
  75 passed, none skipped, every command exited 0.
- Papers 001 to 003: `cargo test -j 1 --manifest-path <package>/code/rust/Cargo.toml`
  for each package's own crate, after this run: 8, 3 and 13 tests passed, every
  command exited 0.

## Collection checks

From the series directory, after the final collection build
(`py -3.12 tools/build_publications.py --pdf`, exit 0, all ten collection PDFs
reused because their TeX was unchanged):

- `py -3.12 tools/check_publications.py`: exit 0, status PASS, 10 publications,
  17 local links checked.
- `py -3.12 -m unittest discover -s tools -p test_publication_checks.py`: 5 tests,
  OK.
- `py -3.12 tools/replay_finite_witnesses.py`: exit 0; `finite_witnesses.json`
  unchanged.

## Review tooling changed in this revision

- `py -3.12 -m pytest omega_engine_research_papers/tests/paper_review/test_republication_gate.py -q`: 51 passed.
- `py -3.12 -m pytest omega_engine_research_papers/tests/test_cli.py -q`: 8 passed.
- `py -3.12 -m pytest omega_engine_research_papers/tests/paper_review/test_old_man_red_team.py -q`: 6 passed, including four new Gate 4 cases.

Historical receipts keep their original dates and scope and are not current
execution evidence.
