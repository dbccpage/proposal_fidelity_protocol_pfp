# Gap report: PFP, PCIV, EIS and operads

Checked 2026-11-13 against `main` at f3533f29. Each item was confirmed by reading the file named. Most severe first in each section. Written by the [WF50 repo hygiene](workflow_wf50.md) workflow.

## PFP

- **The Paper 005 oracle test looks in the wrong place.** `pfp_lab/tests/test_differential.py` line 6 points to `papers/005_...`, but the paper is now at `papers/pfp/005_...`. Fix: update the path to match `pfp_lab/core/PROVENANCE.md`.
- **CI runs almost none of the tests.** `.github/workflows/` has four jobs. Nothing runs `pfp_lab`, `pfp_core`, `benchmarks/`, `governance/tools/tests`, mypy, ruff or `governance.tools.checker check`, and `pyproject.toml` `testpaths` lists only two folders. Fix: add one job that runs the default suite and the floor check.
- **`pfp_core/` and `benchmarks/` are outside governance.** `governance/policy.json` does not list them, yet it says "Every tree is governed". No `pfp_core/*.score.json` exists. Fix: add both trees to the policy and score them, or list them under `not_yet_governed`.
- **The wheel leaves out `pfp_core`.** The `packages` list in `pyproject.toml` has no `pfp_core`, which only works from a checkout through its own `sys.path` changes. Fix: package it, and move `budget_ledger` out of `dag/benchmark`.
- **WF50's tests are not in the default run.** `workflows/wf50_repo_hygiene/test_hygiene.py` is not in `testpaths`. WF50 now has a [wiki page](workflow_wf50.md); it is a maintenance workflow, not a family, so it is not in `pfp_core/workflow_families/registry.py`. Fix: add its tests to `testpaths`.
- **The wiki Lab page is out of date.** [PFP Lab](pfp_lab.md) says "Five example scenarios" while `pfp_lab/core/packs` has nine. It also has a "Planned front ends" section for front ends that already ship. Fix: regenerate the page from the pack list and the README.

## PCIV

- **No CI and no default run.** No workflow file mentions `pciv`, and `testpaths` leaves it out. Fix: add `pciv/tests` to the new CI job once it collects.
- **Tests use paths from an older layout.** `pciv/tests/intelligence_metabolism/test_operand_registry.py` lines 38-40 look in `.agents/` and in `operations/` at the repo root. Neither exists here; the real folder is `ops/operations/`. `ops/adversary/roles/scenes.yaml` is missing too. Fix: change the paths to the `ops/` layout, or add the fixtures.
- **Rank and solver checks need a native binary nobody builds.** `pciv/use_cases/rank.py` goes through the `ops/` Rust host, which looks for a host binary (named in `ops/adversary/infrastructure/cochain_adapter.py`) that `code/rust/Cargo.toml` does not build. Fix: document how to build it, or skip these tests with a clear reason when it is absent.
- **The `inspect` command does nothing.** `pciv/frontend/cli/prompt_civ_cli.py` defines `inspect` but `main()` only handles `interrogate`. Fix: implement `inspect` or remove it.
- **The docs claim more than the code proves.** `pciv/documentation/levels/README.md` carries both `maturity: draft` and `claim_status: verified`. Fix: lower `claim_status` until the falsifier tests pass in a clean checkout.

## EIS

- **There is no CI gate.** No workflow and no `testpaths` entry covers `eis/`. Fix: add it to the CI job.
- **Imports fail without `ops/` on the path.** `eis/infrastructure/native_domain.py` imports `operating_system...` and `operations...`. Neither package is declared in `pyproject.toml`. Fix: declare the package paths, or add a `conftest.py` that sets them.
- **A stale test contradicts the code.** `eis/tests/unit/test_two_signal_regulation.py` line 597 expects a bare `expectation = 4` to fail Ab09, but the check in `eis/use_cases/two_signal_regulation.py` dropped that trigger on purpose. Fix: update the test to state a real CHSH claim.
- **The wiki gives no way to run EIS.** [EIS](eis.md) describes the pipeline, but it has no install or run steps and does not list the limits in `eis/documentation/oeeis_residual_obligations.md`. Fix: add a short how-to-run section and a section on known limits.

## Operads

- **The DDC parser crashes on import.** `operads/skill_operad/ddc_operad_parser.py` line 30 uses `DDC_LETTER` but never imports it. This breaks collection of four test files. Fix: add `from operads.canon import DDC_LETTER`.
- **Being Koszul is decided by name, not computed.** In `code/rust/core_operad_theory/src/deformation/bar_cobar.rs` line 20, any name in a fixed list, or any name ending in `KoszulDual`, is marked Koszul. Fix: return "not computed" until a real check exists, and remove the note that says a minimal model was evaluated.
- **No CI builds the Rust operad crates.** `pfp_cli.yml` builds only `pfp_cli`, so the drift guard in `cargo test -p core_operad_canon` never runs. Fix: add a cargo test step for `core_operad_canon`, `core_operad_theory` and `core_operads`.
- **The operad CI runs a small subset.** `operad_gates.yml` runs about seven test files. Its first step runs without `PYTHONPATH`, and later steps use `ops:.`, which fails on Windows. Fix: run all of `operads/` from a `conftest.py` that sets the path, and keep frozen receipt tests out of collection.
- **The kernel accepts any colour.** `operads/canon/_generated.py` line 204 records that `OperadColour` accepts any non-empty name, against the ten fixed colours. Fix: make its constructor refuse names outside the ten.
- **Dead module still declared.** `code/rust/core_homology/src/l_infinity_operad.rs` begins with `#![cfg(any())]`, so it compiles to nothing, yet `lib.rs` line 85 still declares it. Fix: delete the file and its `mod` line.

## Dropped since the first draft

- EIS "tests expect a `.agents/` folder": `eis/infrastructure/definitions_store.py` now finds the repository root by `.agents/` or `.git/` and reads `eis/antibodies/definitions`, so the item no longer holds.
