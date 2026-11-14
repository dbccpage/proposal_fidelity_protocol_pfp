# Comprehensive Review: Epistemic Immune System (EIS) & Prompt Civilization (PCIV)

**Authority Statement:** AuthorityEffect: None. This document records an empirical and architectural code review of the Epistemic Immune System (`core_epistemic_immune_system` and `eis/`) and Prompt Civilization (`core_prompt_civilization` and `pciv/`).  
**Reviewed on:** 2026-11-14  
**Ledger Reference:** `docs/reviews/eis_pciv_review.json` (schema: `pfp.eis-pciv-review.v1`)  
**Target Branch:** `gemini/eis-pciv-review`  

---

## 1. Executive Summary

This review establishes the empirical baseline, diagnoses identified defects, and maps concrete remediation milestones for the Epistemic Immune System (EIS) and Prompt Civilization (PCIV) subsystems within the repository.

All findings from the initial survey (K1 through K10) were verified on disk through reproducible test and checker executions, and are backed by recorded execution receipts in `governance/evidence/`.

### Summary of Baseline Findings (K1–K10)

1. **K1 (EIS Integration Test Compilation Errors):** The Rust integration test `code/rust/tests/core_epistemic_immune_system/activation_use_case_parity.rs` fails compilation due to lifetime omission (`error[E0621]` at line 61) and statement-level borrow drop ordering (`error[E0597]` at line 90). The underlying crate library passes all 24 unit tests.
2. **K2 (PCIV Library Test Failures):** The Rust PCIV library exhibits 3 test failures out of 116 (`immunity::tests::test_f_immune_09_max_10_hops`, `immunity::tests::test_f_immune_10_shortest_hop_distance`, and `record::tests::genome_identity_is_stable_under_nested_key_reordering`). Two stem from unhashed mock witness strings failing witness validation, and one stems from an outdated pre-rename expected digest pin.
3. **K3 (CI Coverage & Code Hygiene):** Neither `core_epistemic_immune_system` nor `core_prompt_civilization` is currently executed in GitHub Actions CI workflows. Both crates present formatting diffs under `cargo fmt` and trigger three blocking clippy warnings (`manual_contains`, `manual_is_multiple_of`, `too_many_arguments`).
4. **K4 (Quadruplicate Immune Logic):** Immune gating and selection logic exists in four parallel variants across `core_epistemic_immune_system`, `core_prompt_civilization/src/immune/`, `eis/domain/`, and `pfp_core/immunity.py`.
5. **K5 (Python Test Suite Baseline & Collection Breakdown):** Python test execution across `eis/tests` and `pciv/tests` yields 386 passes, 26 failures, 2 skips, and 40 collection errors in system Python (404 passes and 36 collection errors in the repository `.venv`). The collection errors stem from out-of-repo monorepo imports (`operating_system.adapters.rust_host.ffi`, `core_symbol_game`, `operations.domain.rop`, `adversary`).
6. **K6 (Defect Inventory & Target Parity):** Real defects include silent charpoly wire normalization bypass due to import path resolution failure, central tolerance autoimmune false-positives in normalized matching, test fixture drift in the Ab09 CHSH header check, Python 3.13 regex error type prefix mismatch, and 6 PCIV support/admission falsifiers lacking a native host implementation.
7. **K7 (Exactness Debt):** `DetectorRule.affinity_score` is stored as a floating-point number, and `clonal_selection.rs` executes `f64` arithmetic during stimulation when `exact == false`, conflicting with the repository rational exactness invariant.
8. **K8 (Open-Loop Failure Learning):** Failures and cemetery headstones are recorded within isolated runs but discarded or written to disjoint files without being indexed into an append-only ledger or subjected to falsifier retesting.
9. **K9 (Path Drift):** 52 files contain 156 occurrences of obsolete paths citing `crates_rs/...` or `engine/crates_rs/...` instead of the active location `code/rust/...`, causing test collection errors and fixture generator misdirection.
10. **K10 (Atlas Gap Claims):** Atlas archive papers 003, 006, and 019 encompass 32 gap claims in `atlas/atlas_claim_matches.json` and 40 proposed derivation nodes in `dag/derivations/`. Stale dependency graphs cause `python dag/build_atlas.py --check` to exit non-zero.

---

## 2. Review Statistics

The companion review ledger `docs/reviews/eis_pciv_review.json` catalogs **50 typed finding records**.

### Breakdown by Finding Class

| Finding Class | Count | Description |
|---|---|---|
| `bug` | 18 | Programmatic defects, compilation failures, panic loci, or assertion mismatches |
| `drift` | 9 | Path drift, stale DAG/Atlas files, missing CI workflows, or formatting diffs |
| `engine_dependency` | 8 | External monorepo modules (`operating_system`, `core_symbol_game`, `adversary`) |
| `doc_wrong` | 4 | Documentation, specification, or wiki files referencing obsolete directory paths |
| `python_check` | 4 | Workflow check stages performing validation in Python rather than Rust |
| `duplicate` | 3 | Quadruplicate immune gate and domain implementations across crates and modules |
| `float` | 3 | Floating-point exactness debt in detector affinity scoring and stimulation |
| `untyped` | 1 | Schema lack of typed falsifier bindings in failure models |
| **Total** | **50** | |

### Breakdown by Target Milestone

| Milestone | Count | Focus Scope | PR Assignment |
|---|---|---|---|
| `M2` | 10 | Rust Test & CI Suite Stabilization (K1, K2, K3, fmt, clippy, CI workflow) | Draft PR 2 |
| `M3` | 11 | Rust Parity Implementations for Python Bugs & Support Falsifiers (K6) | Draft PR 3 |
| `M4` | 5 | Immune Core Unification & Exactness Debt Migration (K4, K7) | Draft PR 4 |
| `M5` | 8 | Host Immune CLI Binary (`pfp_immune`) & Adapter Resolution (K5, R4) | Draft PR 5 |
| `M6` | 3 | Operad Failure Ledger Wiring & Closed-Loop Learning (K8) | Draft PR 6 |
| `M7` | 5 | Workflow Migration (WF14, WF19, WF41, WF51 to `pfp_immune`) (R4) | Draft PR 7 |
| `M8` | 8 | Path Drift Remediation, Wiki Sync, Atlas Derivations & Morning Report (K9, K10) | Draft PR 8 |
| **Total** | **50** | | |

---

## 3. Baseline Findings Verification Table

Every baseline finding was independently verified in the newly established worktree `..\pfp_eis_pciv`. Execution artifacts were recorded using `python -m governance.tools.evidence`.

| # | Finding Description | Exact Verification Command | Observed Exit Status & Result | Evidence Receipt Path |
|---|---|---|---|---|
| K1 | EIS Rust Integration Test Lifetimes | `cargo test --manifest-path code/rust/Cargo.toml -p core_epistemic_immune_system` | Exit 101. Fails with E0621 (`activation_use_case_parity.rs:61`) and E0597 (`line 90`). Library passes 24/24. | `governance/evidence/baseline-eis-rust-tests.run.json` |
| K2 | PCIV Rust Library Failures | `cargo test --manifest-path code/rust/Cargo.toml -p core_prompt_civilization --lib` | Exit 101. 113 passed; 3 failed (`test_f_immune_09`, `test_f_immune_10`, `genome_identity_is_stable`). | `governance/evidence/baseline-pciv-rust-tests.run.json` |
| K3 | Rust Code Formatting | `cargo fmt --manifest-path code/rust/Cargo.toml -p core_epistemic_immune_system -p core_prompt_civilization --check` | Exit 1. Formatting diffs detected across both crate source trees. | `governance/evidence/baseline-eis-pciv-fmt.run.json` |
| K3 | Rust Clippy Lints | `cargo clippy --manifest-path code/rust/Cargo.toml --locked -p core_epistemic_immune_system -p core_prompt_civilization --all-targets --no-deps -- -D warnings` | Exit 101. 3 blocking diagnostics (`manual_contains`, `manual_is_multiple_of`, `too_many_arguments`). | `governance/evidence/baseline-eis-pciv-clippy.run.json` |
| K5 | Python Test Suite Baseline | `python -m pytest -q --continue-on-collection-errors eis/tests pciv/tests` | Exit 1. 26 failed, 386 passed, 2 skipped, 40 collection errors in system Python environment. | `governance/evidence/baseline-python-tests.run.json` |
| WF | Workflow Baseline Suite | `python -m pytest pfp_core/workflow_families pfp_core/tests/test_exclusions.py pfp/workflows -q` | Exit 0. 633 passed cleanly in 108.02s. | `governance/evidence/baseline-workflow-tests.run.json` |
| K9 | Path Drift Count | `git grep -n "crates_rs" -- eis pciv wiki` | 156 matches across 52 non-binary files. | Documented in `docs/reviews/eis_pciv_review.json` |
| K10 | Atlas Synchronization Gate | `python dag/build_atlas.py --check` | Exit 1. 4 stale files identified (`atlas_claim_ledger.*`, `derivations_dag.json`, `atlas.md`). | Documented in `docs/reviews/eis_pciv_review.json` |

---

## 4. Itemized Finding Tables by Subsystem

### 4.1 Rust: Epistemic Immune System (`core_epistemic_immune_system`)

| ID | Locus | Class | Reproduction Command | Proposed Fix |
|---|---|---|---|---|
| `REV-K01-EIS-INTEG-LIFETIME` | `activation_use_case_parity.rs:61` | `bug` | `cargo test -p core_epistemic_immune_system` | Add explicit lifetime `'a` to `input: &'a Value` in `build_activation_request`. |
| `REV-K01-EIS-INTEG-BORROW-DROP` | `activation_use_case_parity.rs:90` | `bug` | `cargo test -p core_epistemic_immune_system` | Bind serialized `trace.borrow()` to local variable before returning to ensure borrow drops prior to `trace`. |
| `REV-K03-CLIPPY-MANUAL-IS-MULTIPLE` | `authenticated.rs:119` | `bug` | `cargo clippy -p core_epistemic_immune_system -- -D warnings` | Replace manual modulo arithmetic with `num_integer::Integer::is_multiple_of()`. |
| `REV-K03-CLIPPY-TOO-MANY-ARGS` | `authenticated.rs:393` | `bug` | `cargo clippy -p core_epistemic_immune_system -- -D warnings` | Group parameters into a verification request context or annotate with `#[allow(clippy::too_many_arguments)]`. |
| `REV-K03-FMT-EIS-PCIV-DIFFS` | `activation.rs:1` | `drift` | `cargo fmt --check` | Apply `cargo fmt` formatting across all touched Rust sources. |
| `REV-K07-FLOAT-DETECTOR-AFFINITY-RUST` | `clonal_selection.rs:64` | `float` | `cargo test -p core_epistemic_immune_system --lib` | Migrate `DetectorRule.affinity_score` from `f64` to `BigRational`. |
| `REV-K07-FLOAT-STIMULATE-ADDITION-RUST` | `clonal_selection.rs:138` | `float` | `cargo test -p core_epistemic_immune_system --lib` | Replace floating-point addition in `stimulate` with exact `BigRational` addition and deprecate non-exact path. |

### 4.2 Rust: Prompt Civilization (`core_prompt_civilization`)

| ID | Locus | Class | Reproduction Command | Proposed Fix |
|---|---|---|---|---|
| `REV-K02-PCIV-WITNESS-09-HOPS` | `immunity.rs:267` | `bug` | `cargo test -p core_prompt_civilization --lib` | Replace mock strings ("w1", "w2") with authentic `inheritance_witness_digest(&parent, &child, &relationship)` hashes. |
| `REV-K02-PCIV-WITNESS-10-SHORTEST` | `immunity.rs:241` | `bug` | `cargo test -p core_prompt_civilization --lib` | Replace mock witness strings with authentic `inheritance_witness_digest` hashes. |
| `REV-K02-PCIV-RECORD-DIGEST-PIN` | `record.rs:308` | `bug` | `cargo test -p core_prompt_civilization --lib` | Update pinned hash constant to canonical post-rename digest `5a60fd3bc53dc83c9953864b00297b0278e3ad62358742582cdd7ec9366f5663`. |
| `REV-K03-CLIPPY-MANUAL-CONTAINS` | `pharmacy.rs:522` | `bug` | `cargo clippy -p core_prompt_civilization -- -D warnings` | Replace `.iter().any(\|w\| lower == *w)` with `.contains(&lower.as_str())`. |
| `REV-K04-QUAD-DUPLICATE-PCIV-IMMUNE` | `immune/allostery.rs:1` | `duplicate` | Architecture diff | Add path dependency to `core_epistemic_immune_system` and consume shared gates. |

### 4.3 Python: Epistemic Immune System (`eis/`)

| ID | Locus | Class | Reproduction Command | Proposed Fix |
|---|---|---|---|---|
| `REV-K05-COLLECT-FFI-RUST-SYMBOL-GAME` | `infrastructure/native_domain.py:9` | `engine_dependency` | `python -m pytest eis/tests` | Decouple module import from out-of-repo FFI host; route execution to `pfp_immune`. |
| `REV-K05-COLLECT-CHARPOLY-IMPORT-PATH` | `tests/unit/test_challenger_two_signal_regulation.py:37` | `drift` | `python -m pytest eis/tests` | Correct import path to `workflows.wf52_finite_qm_benchmark.charpoly_wire`. |
| `REV-K06-BUG-CHARPOLY-NORM-SILENT-NONE` | `use_cases/two_signal_regulation.py:57` | `bug` | `python -m pytest eis/tests -k test_signal1_alone` | Fix import and implement exact rational normalization in Rust. |
| `REV-K06-BUG-NORMALIZED-MATCHER-CENTRAL-TOLERANCE` | `tests/unit/test_two_signal_regulation.py:113` | `bug` | `python -m pytest eis/tests -k test_normalized_matcher` | Implement central tolerance in Rust preventing apoptosis on self panel rational variants. |
| `REV-K06-BUG-AB09-CHSH-HEADER-REGEX` | `tests/unit/test_two_signal_regulation.py:601` | `bug` | `python -m pytest eis/tests -k test_ab09_fails` | Implement CHSH check in Rust and align test fixture text to include "CHSH expectation = 4". |
| `REV-K06-BUG-THYMUS-EVAL-ERROR-PREFIX` | `domain/thymus.py:141` | `bug` | `python -m pytest eis/tests -k test_invalid_pattern` | Format error prefix as `"error: "` across Python 3.12 (`re.error`) and 3.13+ (`re.PatternError`). |
| `REV-K07-FLOAT-DETECTOR-AFFINITY-PYTHON` | `domain/clonal_selection.py:25` | `float` | Code inspection | Support exact rational / `Fraction` representation in Python model. |

### 4.4 Python: Prompt Civilization (`pciv/`)

| ID | Locus | Class | Reproduction Command | Proposed Fix |
|---|---|---|---|---|
| `REV-K05-COLLECT-PCIV-OPERATING-SYSTEM` | `infrastructure/genealogy_adapter.py:12` | `engine_dependency` | `python -m pytest pciv/tests` | Provide standalone file/JSON persistence adapters. |
| `REV-K05-COLLECT-PCIV-ADVERSARY` | `tests/falsifiers/test_falsifiers_spine_and_adversary.py:29` | `engine_dependency` | `python -m pytest pciv/tests` | Guard external adversary package imports in test harness. |
| `REV-K06-BUG-PCIV-SUPPORT-FALSIFIER-01` | `tests/falsifiers/test_falsifiers_support_and_admission.py:58` | `bug` | `python -m pytest pciv/tests -k test_f_support_01` | Implement observation support order-independence check in Rust. |
| `REV-K06-BUG-PCIV-SUPPORT-FALSIFIER-02` | `tests/falsifiers/test_falsifiers_support_and_admission.py:99` | `bug` | `python -m pytest pciv/tests -k test_f_support_02` | Implement non-transitive overlap support check in Rust. |
| `REV-K06-BUG-PCIV-SUPPORT-FALSIFIER-03` | `tests/falsifiers/test_falsifiers_support_and_admission.py:134` | `bug` | `python -m pytest pciv/tests -k test_f_support_03` | Implement support feasibility check without relabelling in Rust. |
| `REV-K06-BUG-PCIV-SUPPORT-FALSIFIER-04` | `tests/falsifiers/test_falsifiers_support_and_admission.py:149` | `bug` | `python -m pytest pciv/tests -k test_f_support_04` | Implement support monotonicity check in Rust. |
| `REV-K06-BUG-PCIV-PHARM-FALSIFIER-01` | `tests/falsifiers/test_falsifiers_support_and_admission.py:180` | `bug` | `python -m pytest pciv/tests -k test_f_pharm_01` | Implement duplicate collapse replay count deduplication in Rust. |
| `REV-K06-BUG-PCIV-RES-FALSIFIER-05` | `tests/falsifiers/test_falsifiers_support_and_admission.py:324` | `bug` | `python -m pytest pciv/tests -k test_f_res_05` | Enforce propagated references are never treated as direct observations in Rust. |
| `REV-K06-DEP-PCIV-RANK-FALSIFIERS` | `tests/falsifiers/test_falsifiers_rank_and_events.py:54` | `engine_dependency` | `python -m pytest pciv/tests` | Port PageRank solver and transition matrix verification to Rust. |
| `REV-K06-DEP-PCIV-CUSTODY-FALSIFIER` | `tests/falsifiers/test_falsifiers_immune_and_danger.py:243` | `engine_dependency` | `python -m pytest pciv/tests -k test_f_custody_01` | Implement provisional custody check in Rust. |
| `REV-K06-DRIFT-METABOLISM-FIXTURE-PATH` | `tests/intelligence_metabolism/test_native_metabolism.py:24` | `drift` | `python -m pytest pciv/tests` | Update fixture path to `code/rust/tests/core_prompt_civilization/fixtures/metabolism.json`. |
| `REV-K08-OPENLOOP-HEADSTONE-FALSIFIERS` | `domain/models.py:184` | `untyped` | Code inspection | Align `CemeteryHeadstoneV1` schema with operad canon failure types. |

### 4.5 Workflows & Operad Kernel (`pfp_core/` & `pfp_operads`)

| ID | Locus | Class | Reproduction Command | Proposed Fix |
|---|---|---|---|---|
| `REV-K04-QUAD-DUPLICATE-PFP-IMMUNITY` | `pfp_core/immunity.py:1` | `duplicate` | Code inspection | Transition `pfp_core/immunity.py` methods to invoke `pfp_immune` binary behind parity tests. |
| `REV-K08-OPENLOOP-CEMETERY-DISCONNECTED` | `dag/operad_coverage.md:12` | `drift` | Documentation inspection | Connect cemetery headstones into `pfp_operads::ledger` `Record::Failure`. |
| `REV-K08-OPENLOOP-OPERAD-LEDGER-WIRING` | `code/rust/pfp_operads/src/ledger.rs:1` | `drift` | Code inspection | Expose ledger CLI subcommands and Python wrapper `pfp_core/operad_ledger.py`. |
| `REV-WORKFLOW-CHECK-STAGE-WF14-MIGRATION` | `pfp_core/workflow_families/layer6.py:202` | `python_check` | Workflow inspection | Migrate WF14 thymus screening and two-signal admission check to Rust binary `pfp_immune screen` / `decide`. |
| `REV-WORKFLOW-CHECK-STAGE-WF19-MIGRATION` | `pfp_core/workflow_families/layer7.py:191` | `python_check` | Workflow inspection | Migrate WF19 rule screening and transfer accuracy gain evaluation to Rust binary `pfp_immune`. |
| `REV-WORKFLOW-CHECK-STAGE-WF41-MIGRATION` | `pfp_core/workflow_families/layer7.py:430` | `python_check` | Workflow inspection | Migrate WF41 two-signal independence verification to Rust binary `pfp_immune`. |
| `REV-WORKFLOW-CHECK-STAGE-WF51-MIGRATION` | `pfp_core/workflow_families/layer7.py:565` | `python_check` | Workflow inspection | Migrate WF51 model family vote aggregation and branch exclusions to Rust binary `pfp_immune exclusion`. |

### 4.6 Governance, Documentation & Atlas (`governance/`, `wiki/`, `atlas/`, `dag/`)

| ID | Locus | Class | Reproduction Command | Proposed Fix |
|---|---|---|---|---|
| `REV-K03-CI-MISSING-WORKFLOW` | `.github/workflows/eis_pciv_rust.yml:1` | `drift` | Directory inspection | Author GitHub Actions CI workflow executing fmt, clippy, and cargo tests. |
| `REV-K09-DRIFT-FIXTURE-GENERATORS` | `eis/tests/generate_rust_activation_fixtures.py:93` | `drift` | Path grep | Update 7 fixture generators to output into `code/rust/tests/...`. |
| `REV-K09-DRIFT-ANTIBODY-SPECS` | `eis/antibodies/anti_rust_capture_completion_loss.yaml:42` | `doc_wrong` | Path grep | Update 12 antibody YAML specs from `crates_rs` to `code/rust`. |
| `REV-K09-DRIFT-PCIV-CURRICULUM-DOCS` | `pciv/documentation/README.md:120` | `doc_wrong` | Path grep | Update 20 PCIV documentation files from `crates_rs` to `code/rust`. |
| `REV-K09-DRIFT-OEEIS-RESIDUAL-DOC` | `eis/documentation/oeeis_residual_obligations.md:44` | `doc_wrong` | Path grep | Update path reference from `crates_rs` to `code/rust`. |
| `REV-K09-DRIFT-WIKI-TYPE-INVENTORY` | `wiki/operads_type_inventory.md:145` | `doc_wrong` | Path grep | Update path reference from `crates_rs` to `code/rust` without running `publish_wiki.py`. |
| `REV-K10-ATLAS-GAP-CLAIMS-P003-006-019` | `atlas/atlas_claim_matches.json:1` | `drift` | `python dag/build_atlas.py --check` | Author derivations in `dag/derivations/` for covered gap claims across Papers 003, 006, 019. |
| `REV-K10-ATLAS-STALE-CHECK-SYNC` | `atlas/atlas.md:1` | `drift` | `python dag/build_atlas.py --check` | Run synchronization sequence: `build_dags.py` then `build_atlas.py` to satisfy `--check`. |

---

## 5. Open Decisions for Jeremy

The following decisions involve external authority boundaries, operational credentials, or intentional design divergences that cannot be unilaterally resolved without operator review:

### Open Decision 1: Residual Obligations Boundary Classification
- **Context:** `eis/documentation/oeeis_residual_obligations.md` lists outstanding items from the initial implementation.
- **Classification:**
  - **In Scope (Closable):** Numeric exactness debt (`DetectorRule.affinity_score` float migration and `stimulate` exact rational arithmetic). These are addressed in Milestone M4.
  - **Out of Scope (Documented Boundary):** Items requiring an external operator, physical hardware, or live production infrastructure cannot be closed by automated subagents:
    1. Enrolling production Ed25519 signing keys and authorized signer mapping.
    2. Retaining ledger tips (pins) in durable off-database storage.
    3. Key rollover and migration policy.
    4. Deploying physical host-health observers and streaming real live telemetry.
    5. Continuous-health monitoring across live activations.
    6. False-positive rate `FP/(FP+TN)` telemetry contract (current telemetry carries no TN).
- **Recommendation:** Maintain these out-of-scope obligations as formal documentation boundaries in `oeeis_residual_obligations.md` without claiming closed status.

### Open Decision 2: Architectural Divergence Seams Between EIS and PCIV
- **Context:** Milestone M4 unifies duplicate immune logic by directing `core_prompt_civilization` to consume `core_epistemic_immune_system`.
- **Divergence:**
  - `core_epistemic_immune_system` implements formal port-based contracts (`GuardStatePort`, `DangerSensorPort`), explicit typed receipts, and two-signal regulation requiring independent danger signals for state transitions.
  - `core_prompt_civilization/src/immune/` implements a simplified 8-gate model (`allostery`, `clonal`, `complement`, `danger_gate`, `mhc`, `proofreading`, `thymus`, `treg`) that acts directly on in-memory representations.
- **Recommendation:** Re-export and adapt shared gates (`ThymusGate`, `DangerGate`) from EIS into PCIV where interfaces align. Preserve PCIV-specific gate simplifications where forced alignment would alter existing unit test semantics, and document the seam as an intentional architectural abstraction layer.

### Open Decision 3: External Monorepo Engine Dependencies vs. Standalone Native Host
- **Context:** 40 Python collection errors in `eis/tests` and `pciv/tests` stem from out-of-tree packages (`operating_system.adapters.rust_host.ffi`, `core_symbol_game`, `adversary`).
- **Recommendation:** Do not attempt to reintroduce or mock the legacy monorepo FFI framework. Instead, provide all necessary validation capabilities via the native Rust host CLI binary `pfp_immune` (Milestone M5), allowing Python workflows and tests to interact with a clean, standalone JSON IPC interface.

---

## 6. Artifact Assessment (Claim Hygiene Summary)

1. **What this review supports:**
   - Demonstrates empirical reproducibility of findings K1 through K10 on disk under the declared repository environment.
   - Diagnoses the program-level causes of all failing Rust compilation and test targets.
   - Enforces a typed, structured review ledger of 50 itemized records across 8 milestones.
   - Provides concrete, localized remediation plans preserving the invariant that Rust validates and Python executes model/file operations.
2. **What this review does not support:**
   - Does not demonstrate runtime execution of out-of-repo monorepo components or live external models.
   - Does not assert that future PR fixes will be free of regressions until each PR's verification suite is executed.
3. **The narrowest defensible claim:**
   Under the declared repository conditions, the 50 itemized defects cataloged in `docs/reviews/eis_pciv_review.json` represent the complete set of identified baseline obstacles preventing clean compilation, lint greenness, and CI passage for the EIS and PCIV subsystems.
4. **The next test needed:**
   Execute Milestone M2 (Branch: `gemini/eis-pciv-m2`) to fix K1, K2, fmt, clippy, and author `.github/workflows/eis_pciv_rust.yml`.
