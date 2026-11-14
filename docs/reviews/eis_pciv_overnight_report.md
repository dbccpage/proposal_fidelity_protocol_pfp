# EIS and PCIV Overnight Review and Integration Report

AuthorityEffect: None.

Generated on `2026-11-14` from dedicated worktree `..\pfp_eis_pciv` (`main` checkout left clean and untouched). All tests and checks ran offline without model API calls.

## 1. Draft Pull Requests and Branch Topology

| Milestone | Draft PR | Branch (`origin/...`) | Head Commit | Base / Stacking | Summary |
| --- | --- | --- | --- | --- | --- |
| M0 / M1 | `#94` | `gemini/eis-pciv-review` | `48d745223` | `main` | 6 baseline `.run.json` receipts + 50-record review ledger (`docs/reviews/eis_pciv_review.{json,md}`) |
| M2 | `#100` | `gemini/eis-pciv-m2` | `6f509abbd` | `main` | Fixed K1 integration lifetimes, K2 3 PCIV failures, clippy `-D warnings`, `cargo fmt`, CI `.github/workflows/eis_pciv_rust.yml` |
| M3 | `#104` | `gemini/eis-pciv-m3` | `88aee1a4f` | `M2` (`#100`) | Charpoly exact normalization wire, central tolerance, Ab09 CHSH exact check, 6 PCIV support falsifiers |
| M4 | `#108` | `gemini/eis-pciv-m4` | `d8dd51339` | `M2+M3` (`#104`) | Unified `core_prompt_civilization/src/immune/` onto `core_epistemic_immune_system`; migrated `clonal_selection.rs` to `BigRational` |
| M5 | `#113` | `gemini/eis-pciv-m5` | `95cff1174` | `main` | Added standalone Rust host binary `code/rust/pfp_immune` (`screen`, `decide`, `taint`, `select`, `exclusion`) + 23 parity tests |
| M6 | `#118` | `gemini/eis-pciv-m6` | `961376d26` | `main` | Added `pfp_core/operad_ledger.py` + `test_operad_ledger.py` connecting EIS/PCIV outcomes and cemetery headstones to `pfp_operads::ledger` |
| M7 | `#121` | `gemini/eis-pciv-m7` | `719ed006a` | `M6` (`#118`) | Added `pfp_core/immune_host.py`; routed `WF14`, `WF19`, `WF41`, `WF51`, `immunity.py`, `civilization.py`, `exclusions.py` through `pfp_immune` + `operad_ledger` |
| M8 | `#<M8_PR>` | `gemini/eis-pciv-m8` | `pending` | `main` | Fixed K9 path drift in 34 doc/YAML files, updated 11 wiki pages + SHA-256 pins, wired 4 K10 Atlas `partial` claims + 4 derivation docs, overnight report |

- **Unpushed branches:** none.
- **Stacking notes:** `#104` builds on `#100`; `#108` builds on `#104`; `#121` builds on `#118`. Draft PRs `#94`, `#100`, `#113`, `#118`, and `#<M8_PR>` branch directly from `origin/main`.

## 2. Verified Milestones, Commands, and Before/After Counts

### Baseline (M0 / M1 — `#94`)

- `cargo test --manifest-path code/rust/Cargo.toml -p core_epistemic_immune_system`: Exit `101` (`E0621` at `code/rust/tests/core_epistemic_immune_system/activation_use_case_parity.rs:61`, `E0597` at line `90`; library alone `24/24`).
- `cargo test --manifest-path code/rust/Cargo.toml -p core_prompt_civilization --lib`: Exit `101` (`113` passed, `3` failed).
- `cargo fmt ... --check` & `cargo clippy ... -D warnings`: Exit `1` (formatting diffs) and Exit `101` (`3` clippy diagnostics).
- `python -m pytest -q --continue-on-collection-errors eis/tests pciv/tests`: Exit `1` (`386` passed, `26` failed, `2` skipped, `40` collection errors).
- `python -m pytest pfp_core/workflow_families pfp_core/tests/test_exclusions.py pfp/workflows -q`: Exit `0` (`633` passed in `108.02s`).
- `git grep -n "crates_rs" -- eis pciv wiki`: `156` matches across `52` files.
- `python dag/build_atlas.py --check` (`origin/main` baseline): Exit `0`, `"stale": []`, `matched: 82`, `partial: 108`, `gap: 417` (`32` gaps across `ATL-P003-*`, `ATL-P006-*`, `ATL-P019-*`).

### Remediation Across M2–M7 (`#100`, `#104`, `#108`, `#113`, `#118`, `#121`)

- **M2 (`#100`):** `cargo test -p core_epistemic_immune_system` (`63/63` passed), `cargo test -p core_prompt_civilization --lib` (`116/116` passed), `cargo fmt --check` and `cargo clippy -- -D warnings` pass (`0` warnings), `.github/workflows/eis_pciv_rust.yml` added, `checker.py` (`32/32` meet floor).
- **M3 (`#104`):** `core_epistemic_immune_system` extended with `normalization` (charpoly exact reduction and zero-omission), normalized `Thymus` tolerance, exact Ab09 CHSH check, and `support_falsifiers_parity.rs`: `cargo test -p core_epistemic_immune_system` (`80` passed), `core_prompt_civilization --lib` (`116` passed), `checker.py` (`35/35` meet floor).
- **M4 (`#108`):** `core_prompt_civilization/src/immune/` delegates shared logic to `core_epistemic_immune_system`; `clonal_selection.rs` migrated to `BigRational` (`0` float types remaining): `cargo test -p core_epistemic_immune_system` (`83/83`), `core_prompt_civilization --lib` (`116/116`), `--test oeeis_kernel` (`9/9`), `checker.py` (`40/40` meet floor).
- **M5 (`#113`):** `code/rust/pfp_immune` CLI binary verified by `cargo test -p pfp_immune` (`23/23` passed in `0.18s`), `cargo clippy` (`0` warnings), `cargo fmt --check` (clean), lexical mutation report `8/8` decisive mutants killed, `checker.py` (`2/2` meet floor).
- **M6 (`#118`):** `pfp_core/operad_ledger.py` + `test_operad_ledger.py`: `pytest pfp_core/tests/test_operad_ledger.py pfp_core/tests/test_exclusions.py pfp_core/workflow_families/tests/test_learning.py -q` (`79` passed in `5.59s`), `cargo test -p pfp_operads --test ledger` (`15/15` passed), ruff & `checker.py` (`0/0` violations).
- **M7 (`#121`):** `pfp_core/immune_host.py` and workflow migrations (`WF14`, `WF19`, `WF41`, `WF51`): `test_immune_parity.py` (`19` passed in `3.78s`), `-k "WF14 or WF19 or WF41 or WF51"` (`34` passed in `7.66s`), `test_operad_ledger.py` + `test_exclusions.py` (`70` passed in `2.63s`), `test_pfp_core.py` + `test_hardening_20261111.py` (`16` passed in `2.85s`), ruff & `checker.py` (`0/0` violations).

### M8 Verification (`gemini/eis-pciv-m8` — `#<M8_PR>`)

- **K9 doc/YAML updates:** Updated `34` files (`12` YAML specs under `eis/antibodies/` and `eis/antibodies/specs/`, `eis/documentation/oeeis_residual_obligations.md`, and `21` Markdown docs under `pciv/documentation/`):
  - `git grep -n "crates_rs" -- eis/antibodies eis/documentation pciv/documentation` -> `0` matches.
  - Link verification across `pciv/documentation/` -> `broken_links: []`.
- **In-scope wiki sync:** Updated `11` files (`wiki/eis*.md`, `wiki/pciv*.md`, `wiki/workflow_eis_pciv.md`) and updated both `wiki/workflow_eis_pciv.md` `page_sha256` entries (`9464977bf8f0abf76e8df6977f4665a4aebd3847088e454622c7e1e3db1234d4`) in `dag/wiki/workflow_documentation.json`. `wiki/publish_wiki.py` was not run.
- **K10 derivation docs & Atlas wiring:** Added `dag/derivations/epc02.md`, `native_eis_001.md`, `native_eis_004.md`, and `native_eis_006.md`; upgraded `ATL-P003-008`, `ATL-P003-013`, `ATL-P003-014`, and `ATL-P006-009` in `atlas/atlas_claim_matches.json` from `gap` to `partial` (retaining `proposed_derivation`).
  - `python dag/build_dags.py` -> Exit `0` (`derivations`: `3010` nodes, `2943` edges; `workflows`: `4351` nodes, `9072` edges; `acyclic: true`).
  - `python dag/build_atlas.py` & `python dag/build_atlas.py --check` -> Exit `0`, `"stale": []`, `ledger_rows: 1356`, `derivation_nodes: 1356`, `archive_claim_review: {"matched": 82, "partial": 112, "gap": 413}` (`4` archive claims moved from `gap` to `partial`).
- **Governance & workflow test suite on `gemini/eis-pciv-m8`:**
  - `python -m governance.tools.checker check --changed-since origin/main` -> Exit `0`, `0/0 governed sources meet the floor`.
  - Targeted wiki/DAG sync + exclusions + WF52 source-custody suite (`python -m pytest pfp_core/workflow_families/tests/test_families.py pfp_core/tests/test_exclusions.py workflows/wf52_finite_qm_benchmark/test_source_custody.py -q`) -> Exit `0`, `481 passed in 112.45s`.
  - Full combined workflow + WF52 EIS/PCIV suite (`python -m pytest pfp_core/workflow_families pfp_core/tests/test_exclusions.py pfp/workflows workflows/wf52_finite_qm_benchmark/test_eis_pciv_workflows.py workflows/wf52_finite_qm_benchmark/test_source_custody.py -q`) -> Exit `1`, `754 passed, 3 failed in 295.57s` — all `3` failures occur in `workflows/wf52_finite_qm_benchmark/test_eis_pciv_workflows.py` raising `SWAPPED_BINARY: native custody check failed: NATIVE_BINARY_CHANGED` (pre-existing `origin/main` defect; see Section 3 item 6).

## 3. Remaining Findings and Intentionally Deferred Items

1. **`governance/baseline.json`-grandfathered Python files with `crates_rs` (`REV-K09-DRIFT-FIXTURE-GENERATORS`, `REV-K06-DRIFT-METABOLISM-FIXTURE-PATH`):**
   - Left untouched (`9` files): `eis/infrastructure/mssn_pharmacy.py`, `eis/tests/generate_rust_{activation_fixtures,guard_use_case_fixtures,host_check_fixtures,independence_fixtures,pharmacy_overlap_fixtures,signal_gate_fixtures,unicode_data}.py`, and `pciv/tests/intelligence_metabolism/test_native_metabolism.py`. Editing grandfathered files voids `governance/baseline.json` exemption and triggers external-engine import failures without source monorepo dependencies.
2. **External monorepo engine dependencies (`REV-K05-COLLECT-FFI-RUST-SYMBOL-GAME`, `REV-K05-COLLECT-PCIV-OPERATING-SYSTEM`, `REV-K05-COLLECT-OPS-ROP-RESULT`, `REV-K05-COLLECT-PCIV-ADVERSARY`, `REV-K06-DEP-*`):**
   - Modules missing from `pfp` (`operating_system.adapters.rust_host.ffi`, `core_symbol_game`, `auto_p/compiler/phase_wiring.rs`, `.agents/antibodies/specs`, `operations.domain.rop.result`, `operations/skill_operad/json/operand_registry.json`, `dag.benchmark`) leave `eis/tests` + `pciv/tests` collection errors open where no pure-`pfp` replacement belongs inside these legacy suites.
3. **Frozen historical receipts & out-of-scope wiki:**
   - `eis/receipts/` (`8` files dated `20261012` / `20261027`) remain untouched historical QA records.
   - `wiki/operads_type_inventory.md:145` (`REV-K09-DRIFT-WIKI-TYPE-INVENTORY`) remains untouched because it sits outside the allowed wiki scope (`wiki/eis*.md`, `wiki/pciv*.md`, `wiki/workflow_eis_pciv.md`) and touches the parallel operads track.
4. **Legacy Python check duplicates retained per Rule 1 (`REV-K04-QUAD-DUPLICATE-EIS-DOMAIN`, `REV-K04-QUAD-DUPLICATE-PFP-IMMUNITY`, `REV-K07-FLOAT-DETECTOR-AFFINITY-PYTHON`):**
   - Retained in place alongside the new Rust paths (`pfp_immune` and `immune_host.py`) until parity tests run together on `main`.
5. **Open operator obligations & remaining Paper 003 / 006 / 019 gaps (`REV-K10-ATLAS-GAP-CLAIMS-P003-006-019`):**
   - `eis/documentation/oeeis_residual_obligations.md` operator, deployment, key-custody, continuous host-health, and statistical-independence obligations remain open (not closable offline).
   - Remaining Atlas `gap` claims (`28` total across these three papers):
     - `ATL-P003-*` (`15` gaps, `13` partial, `2` matched): `003, 004, 007, 009, 010, 011, 012, 015, 016, 017, 018, 019, 023, 029, 030`.
     - `ATL-P006-*` (`6` gaps, `6` partial, `6` matched): `006, 007, 008, 010, 011, 014`.
     - `ATL-P019-*` (`7` gaps, `2` partial, `0` matched): `001, 002, 003, 006, 007, 008, 009` (deferred harness-evolution / live campaign claims).
6. **Pre-existing `WF52` sidecar custody path mismatch (`workflows/wf52_finite_qm_benchmark/native_sidecar_host/build_receipt.json:89`):**
   - Observed when running `workflows/wf52_finite_qm_benchmark/test_eis_pciv_workflows.py`: commit `2ee3083e2` on `origin/main` moved `dag/benchmark/` to `workflows/wf52_finite_qm_benchmark/`, leaving `"binary": {"path": "dag\\benchmark\\native_sidecar_host\\target\\debug\\pfp-native-sidecar-host.exe"}` inside `workflows/wf52_finite_qm_benchmark/native_sidecar_host/build_receipt.json` (and no built binary under `native_sidecar_host/target/`). Because `NativeHost.custody()` (`workflows/wf52_finite_qm_benchmark/native_sidecar.py:193-196`) compares `ROOT / receipt["binary"]["path"]` against `workflows/wf52_finite_qm_benchmark/native_sidecar_host/target/debug/pfp-native-sidecar-host.exe` and `build_receipt.json` is hash-pinned across `charpoly_rebuild_validation.json`, `native_sidecar_manifest.json`, `qm_native_charpoly_manifest.json`, and `dag/reviews/` (untouchable under scope rules), `3` sidecar-invoking tests fail pre-existingly with `NATIVE_BINARY_CHANGED`.

## 4. Open Decisions for Jeremy

1. **PR merge sequence and release binary rebuild:**
   - Merge order recommended: `#94` (M0/M1) -> `#100` (M2) -> `#104` (M3) -> `#108` (M4) and `#113` (M5), `#118` (M6) -> `#121` (M7), `#<M8_PR>` (M8). Once `#113` and `#121` are both on `main`, decide whether CI (`eis_pciv_rust.yml` or workflow jobs) should build `pfp_immune` automatically before Python workflow suites run so `immune_host.py` exercises the native binary instead of offline fallback.
2. **Deprecation/removal schedule for legacy Python check modules & monorepo-dependent tests:**
   - Decide when to remove Python check duplicates (`eis/domain/*`, `pfp_core/immunity.py` fallbacks) and archive or re-home grandfathered `eis/tests` / `pciv/tests` importing `operating_system.*` once M2–M7 land on `main`.
3. **Wiki publication & `oeeis_residual_obligations.md` operator sign-off:**
   - Decide when to run `wiki/publish_wiki.py` (intentionally omitted offline in M8) to sync updated `wiki/*.md` to the GitHub Wiki, and assign operator owners for production Ed25519 keys, tip pinning, and continuous host health.
4. **Re-pinning `WF52` native sidecar custody after directory fold (`commit 2ee3083e2`):**
   - Decide whether to rebuild `workflows/wf52_finite_qm_benchmark/native_sidecar_host` and update hash pins in `charpoly_rebuild_validation.json`, `native_sidecar_manifest.json`, `qm_native_charpoly_manifest.json`, `test_charpoly_workflows.py`, and `dag/reviews/` so `test_eis_pciv_workflows.py` passes `NativeHost.custody()` from clean worktrees.

## 5. Requested `core_operad_canon` Additions (Untouched per Scope Boundary)

Both `code/rust/core_operad_canon/` and `code/rust/pfp_operads/` were left untouched under the hard parallel-session boundary. When the operads track incorporates EIS/PCIV natively, consider adding typed schema/enum definitions in `core_operad_canon` for:

- **EIS typed check records:** `MatchEvidence`, `CategorizedDangerEvidence`, `ThymusVerdict` (`Survived`, `SelfReactive`, `InvalidPattern`), and `DangerDecision` (`Tolerated`, `DiagnosticOnly`, `DefensiveLockdown`, `Quarantined`) so `pfp_immune` and `pfp_operad ledger` validate identical Rust enums directly without Python adapter mapping.
- **PCIV genome & cemetery records:** Canonical `PromptGenomeV1` digest references, `InheritanceEdgeKind` (`DirectMutation`, `Repair`, `Retry`), `ExclusionHypothesis` statuses, and `CemeteryHeadstone` failure-class normalization directly into `pfp_operads::ledger::Record` without string translation in `pfp_core/operad_ledger.py`.

## 6. Claim Hygiene Summary

1. **What it supports:** Verified offline compilation, formatting, clippy, unit/integration parity, exact-rational migration, CLI binary check routing, append-only ledger persistence, documentation path alignment (`34` doc/YAML files + `11` wiki pages), and `4` new Atlas `partial` links across the M0–M8 Draft PR stack under declared offline test fixtures.
2. **What it does not support:** Live LLM evaluations, statistical observer independence, population false-positive rates (`FP/(FP+TN)`), closing operator deployment/key-custody obligations, or removing grandfathered monorepo-dependent Python tests.
3. **The narrowest defensible claim:** Each EIS and PCIV defect and documentation gap addressed across M0–M8 matches its recorded branch checks (`cargo test`, `cargo clippy`, `pytest`, `governance.tools.checker`, and `dag/build_atlas.py --check`), while branches M2–M8 remain separate Draft PRs pending review and integration onto `main`.
4. **The next test needed:** After merging `#100`->`#104`->`#108`, `#113`, `#118`->`#121`, and `#<M8_PR>` onto a single integration branch, build both `pfp_operads` and `pfp_immune` in release mode and execute `cargo test` plus the combined Python parity and workflow suites (`test_immune_parity.py`, `test_operad_ledger.py`, `pfp_core/workflow_families`) with `pfp_immune` actively on `PATH` (verifying non-fallback execution end-to-end).
