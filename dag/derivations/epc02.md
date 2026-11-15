# EPC02: Fixture Vector Generator Parity Scope

AuthorityEffect: None.

- Archive claim: [ATL-P003-013](atl_p003_013.md) (partially covered alongside `NATIVE03-FIXTURES-011`, `narrows`)
- Audit derivation node: `EPC02` (see `dag/derivations_dag.json`)
- Review verdict: `partial` (`narrows` `ATL-P003-013` in [`atlas/atlas_claim_matches.json`](../../atlas/atlas_claim_matches.json))

## 1. Statement under review

The Python fixture generators (`eis/tests/generate_rust_activation_fixtures.py`, `eis/tests/generate_rust_pharmacy_overlap_fixtures.py`, `eis/tests/generate_rust_unicode_data.py`) freeze Python EIS behavior as an oracle for a bounded set of native parity test vectors (`NATIVE03-FIXTURES-011`, including `code/rust/tests/core_epistemic_immune_system/fixtures/python_independence_v1.json`).

## 2. Verified repository evidence

- `dag/derivations_dag.json` node `EPC02` records the three generator modules (`eis/tests/generate_rust_activation_fixtures.py`, `eis/tests/generate_rust_pharmacy_overlap_fixtures.py`, `eis/tests/generate_rust_unicode_data.py`) with ceiling `"Generators not run; no historical fixture regeneration."`
- `dag/derivations_dag.json` node `NATIVE03-FIXTURES-011` records the inspected frozen parity fixtures across `core_operads` and `code/rust/tests/core_epistemic_immune_system/fixtures/python_independence_v1.json`.
- Companion overnight slices (Draft PRs `#100`, `#104`, `#108`, `#113` on branches `gemini/eis-pciv-m2..m5`) repair Rust integration compilation, normalize charpoly wire outputs (`eis/tests/fixtures/wf52_two_signal_charpoly_v1.json`), and add offline Python-vs-`pfp_immune` parity tests; note that the historical generator scripts themselves still reference old `crates_rs` paths in `governance/baseline.json`-grandfathered Python files and were not re-executed.

## 3. Why it narrows `ATL-P003-013`

`ATL-P003-013` asks for native/Python parity over the Paper 003 gate table and package detectors. `EPC02` and `NATIVE03-FIXTURES-011` establish finite parity fixture contracts where Python acts as the reference oracle for the exported overlap subset (`python_independence_v1.json`), which narrows `ATL-P003-013` without substituting for a fresh exhaustive replay across the full Paper 003 package matrix.

## 4. Bounds and open obligations

- Parity fixtures check agreement with the frozen Python oracle; they do not independently validate the Python oracle itself or full Unicode/platform behavior.
- The historical generator scripts remain `governance/baseline.json`-grandfathered (`crates_rs` layout strings) and are not re-executed.
- Exhaustive table parity across the Paper 003 domain remains open on `ATL-P003-013`.
