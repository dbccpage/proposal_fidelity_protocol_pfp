# Project: Woland Adaptive Retinue, Yardstick, & OEWAS Closeout

## Architecture
The system consists of two parallel tracks governed by fail-closed Woland terminal reality gates:
1. **Implementation Track**:
   - **M1: OEWAS Reconciliation & Ingress Repair**: Resolve contract binding hash drift in `prior_art_contract_binding.py`, repair IC migration baseline validation for historical archives, fix provider paths in `management_ladder.py`, remove remnant `008_oewas` directory, and reseal `epic_manifest.json`.
   - **M2: Woland Custody Cleanup & Regression Remediation**: Update antibody log paths in `test_cross_batch_d1_d20_regression.py`, create SHA-256 deletion custody manifests, remove duplicate `_ic/antibodies`, and execute self-digestion deletion of `_ic/woland/runs` while preserving protected archives (`_ic/nara/permanent_records`, `historical`, `_ic/odni/migration(s)`).
   - **M3: Woland Failure-First Currency & Roster Accounting (F0, F3)**: Enforce approvals carry zero acceptance weight, require independent host checker reproduction for failure claims, track candidate false-alarm rates, extend `retinue_coverage` and yardstick metrics (`declared`, `scheduled`, `contributed`, `failures_reproduced`, `false_alarms`), and author falsification tests.
   - **M4: Woland Adaptive Retinue: Loops, Presets, Tiers, Falsification Queue & Blind Cohorts (A4–A6, F1, F2, F4, F5)**: Implement generalized bounded critic-target loops (`A4`), per-seat model tiers in unified run ledger (`A5`), parallel blind cohort dispatch (`A6`), cross-family falsifiers (`F1`), digest-pinned falsification queue (`F2`), `teamwork run --preset` CLI flags (`F4`), and SHA-256 digest-pinned bundles (`F5`).
   - **M5: Woland Operad Learning, Self-Digestion Yardstick & Cross-Host Rule Sync (F6, L1–L3, S6, Rule Sync)**: Implement prompt-family failure attachment (`F6`), per-run schedule telemetry (`L1`), schedule Thompson sampling (`L2`), operand promotion (`L3`), yardstick yield-per-dollar and unused operad retirement (`S6`), and cross-host sync of `RULE_WOLAND_ORCHESTRATOR_DISCIPLINE_001` item 5 across `.agents`, `.claude`, `.codex`, `.grok`, and `omega_engine_operads`.
   - **M6: Final E2E Pass, Falsification Minimums & Adversarial Hardening**: Execute 100% of E2E test suite (Tiers 1-4), verify theoretical minimum falsifiers and mutation controls, execute cross-host parity and republication checklist gate, and complete Tier 5 adversarial coverage hardening.
2. **E2E Testing Track**:
   - Requirement-driven opaque-box test suite (`TEST_INFRA.md`, `tests/e2e_woland_oewas_suite/`) evaluating all requirements R1, R2, R3 across Tiers 1-4 independently of internal implementation design. Publishes `TEST_READY.md`.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Prior Art Contract Binding Hash Repair | Update `SOURCE_SHA256` constant and plan digest in `prior_art_contract_binding.py` following rename to `omega_engine_operads/` | M1 | Survey 3 |
| 2 | IC Historical Baseline Case Collision Fix | Update `ic_migration.py` `_validate_baseline` to tolerate existing duplicates when `historical=True` so frozen `inventory.json` is verified without modifying bytes | M1 | Survey 3 |
| 3 | Management Ladder Provider Paths Fix | Update folded crate paths from `omega_engine/crates_rs/omega_providers/...` to `omega_engine/crates_rs/omega_woland/src/providers/...` | M1 | Survey 3 |
| 4 | Remnant 008_oewas Directory Cleanup | Remove empty remnant `omega_engine_education/documentation/008_oewas` and clean remaining stale references | M1 | Survey 3 |
| 5 | Epic Manifest Resealing & OEWAS Verification | Reseal `epic_manifest.json` for `epic_oe_oewas_011` and `012` bytes/hashes; verify all 4 OEWAS-011 test suites pass clean | M1 | Survey 3 |
| 6 | Regression Test Antibody Path Update | Point `tests/fuzzing/test_cross_batch_d1_d20_regression.py` to `_ic/cdc/antibodies/antibodies_log.md` | M2 | Survey 2 |
| 7 | Duplicate Antibodies Deletion Custody | Record SHA-256 deletion custody manifest for `_ic/antibodies/antibodies_log.md` and delete duplicate `_ic/antibodies` | M2 | Survey 2 |
| 8 | Self-Digestion Runs Deletion Custody | Delete `_ic/woland/runs` (and digests) verified against `woland_runs_2026_10_22.json` manifest while preserving protected archives | M2 | Survey 2 |
| 9 | Failure-First Currency (F0) | Enforce approvals carry 0 weight; failure claims count only when reproduced by host checker; false alarms tracked | M3 | Survey 1, Survey 2 |
| 10 | Roster Accounting Extension in retinue_coverage (F3) | Extend `TeamworkRun.retinue_coverage` to report `declared`, `scheduled`, `contributed`, `failures_reproduced`, `false_alarms` | M3 | Survey 1 |
| 11 | Yardstick Evidence Metrics Extension (F3) | Extend `Trial` and `ArmStats` in `yardstick.py` to aggregate declared, scheduled, contributed, reproduced failures, false alarms | M3 | Survey 1 |
| 12 | F0 Falsification Test Suite | Author `test_teamwork_f0_falsifiers.py` ensuring counting unreproduced claims or "none found" passes fails closed | M3 | Survey 2 |
| 13 | Bounded Critic-Target Loops (A4) | Generalize bounded loops (Begemot–Koroviev, Koroviev–Bezdomny) up to declared round limit with before/after yardstick measurement | M4 | Survey 1 |
| 14 | Falsification Queue & Blind Cohorts (F2, A6) | Implement digest-pinned falsification queue in run ledger (refuse stale candidate claims) and parallel blind cohort dispatch | M4 | Survey 1 |
| 15 | Multi-Model Run Ledger, Tiers & Presets (A5, F1, F4, F5) | Implement per-seat model tiers in unified run ledger, cross-family falsifier metrics, `--preset` flags, and SHA-256 digest bundles | M4 | Survey 1 |
| 16 | Prompt-Family Failure Attachment (F6) | Attach reproduced failures to originating prompt family binding stores as candidate antibodies | M5 | Survey 1 |
| 17 | Schedule Telemetry & Thompson Sampling (L1, L2) | Record per-run schedule/seat/obstruction telemetry and select schedules via Thompson sampling over correctness-per-unit-cost | M5 | Survey 1 |
| 18 | Operand Promotion (L3) | Implement candidate operand promotion for recurring seat compositions gated by yardstick improvement | M5 | Survey 1 |
| 19 | Operad Yield-per-Dollar & Retirement (S6) | Add operad yield-per-dollar and unused/unhelpful operad retirement to yardstick | M5 | Survey 1 |
| 20 | Rule & Cross-Host Parity Sync | Update `RULE_WOLAND_ORCHESTRATOR_DISCIPLINE_001` item 5, Woland skills, rules registry to ENFORCED, and closed-roster tests across 5 roots | M5 | Survey 1, Survey 2 |
| 21 | Woland Test Suite Totality Pass | Verify all unit and integration tests across Y1–Y4, A1–A6, L1–L3, F0–F6, S1–S7 pass via `pytest` with isolated `--basetemp` | M6 | ORIGINAL_REQUEST |
| 22 | Theoretical Minimum Falsifiers & Mutation Controls | Verify 22-role completeness, required seats, quorum ignore mutations, and F0 mutations pass | M6 | ORIGINAL_REQUEST |
| 23 | Cross-Host Mirrors & Republication Gate | Verify 100% bit-for-bit parity across 5 host trees and pass `republication_checklist_gate` | M6 | ORIGINAL_REQUEST |
| 24 | E2E Test Suite Construction | Build 4-tier E2E test suite verifying OEWAS & Woland epics independently of implementation design | E2E Track | ORIGINAL_REQUEST |
| 25 | Final Milestone E2E Test Suite Pass | Verify 100% pass across all E2E test tiers (Tiers 1-4) | M6 | Project Pattern |
| 26 | Adversarial Coverage Hardening (Tier 5) | Challenger-driven white-box gap analysis and adversarial test cases across all new modules | M6 | Project Pattern |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | OEWAS Reconciliation & Ingress Repair | `prior_art_contract_binding`, `ic_migration.py`, `management_ladder.py`, `008_oewas` cleanup, `epic_manifest.json` | none | DONE |
| M2 | Woland Custody Cleanup & Regression Remediation | `test_cross_batch_d1_d20_regression.py`, `_ic/antibodies` deletion custody, `_ic/woland/runs` self-digestion deletion | none | DONE |
| M3 | Woland Failure-First Currency & Roster Accounting | `teamwork.py` F0 currency, `retinue_coverage` F3 accounting, `yardstick.py` metrics, `test_teamwork_f0_falsifiers.py` | none | DONE |
| M4 | Woland Adaptive Retinue: Loops, Presets, Tiers & Queue | Bounded loops (A4), per-seat tiers (A5), parallel blind cohorts (A6), cross-family falsifiers (F1), queue (F2), `--preset` (F4), bundles (F5) | M3 | IN_PROGRESS |
| M5 | Woland Operad Learning, Yield & Rule Sync | Failure attachment (F6), Thompson sampling (L2), operand promotion (L3), yield/retirement (S6), rule sync across 5 roots | M4 | PLANNED |
| M6 | Final Verification & Adversarial Hardening | 100% E2E test suite execution (Tiers 1-4), falsifier controls, republication gate, Tier 5 adversarial hardening | M1, M2, M5, E2E Track | PLANNED |

## Interface Contracts
### OEWAS Contract Binding ↔ Operad Catalog
- Retained Source Digest: `dc4a3787a2947e20a9f020c43c857ccbc21afd577e2bf1b590367d8ac4eca0a4` (`omega_engine_operads/catalog/contracts/v1/woland_claim_audit.json`).
- Plan Selection: `SelectedCandidatePlanV01` matches contextual task arity; fail-closes on swapped or omitted ports.
- Migration Inventory: `historical=True` bypasses `CASE_COLLISION` on frozen duplicate paths in protected permanent records.

### Woland Failure-First Currency ↔ Host Checker
- Currency Rule: Approval carries 0 weight. Reviewer finding carries weight ONLY when reproduced by independent host checker.
- Unreproduced Finding: Categorized as candidate with false-alarm credit; cannot block clearance or alter baseline state.
- Retinue Coverage Schema:
  `{"status": str, "required": list, "observed": list, "missing": list, "complete": bool, "plan_sha256": str, "schedule": str, "skipped_by_schedule": list, "schedule_skips": dict, "declared": int, "scheduled": int, "contributed": int, "failures_reproduced": int, "false_alarms": int}`.

### Retinue Schedule ↔ Run Ledger
- Presets: `all-anthropic`, `cross-family`, `cheap-falsifiers`.
- Bounded Loops: Bounded by `max_critique_rounds` or 0 new findings; returns `ROUND_LIMIT_REACHED` on exhaustion.
- Falsification Queue: Reject review findings referencing candidate digests differing from active ledger candidate digest.
- Bundle Digest: `sha256(preset_name + prompt_family_versions + checker_ids)`.

### Operad Learning ↔ Yardstick
- Thompson Sampling: Beta distribution over successes / failures per unit cost seeded from Y4 empirical data.
- Candidate Promotion: Operands with positive yardstick delta promoted to admitted catalog.
- Yield per Dollar: `unique_failures_found / cost_usd`; operads with 0 yield across N evaluation runs marked retired.

## Code Layout
- Woland Core: `omega_engine_woland/`
  * Use Cases: `use_cases/teamwork.py`, `use_cases/teamwork_schedule.py`, `use_cases/yardstick.py`, `use_cases/self_digestion.py`
  * Entrypoints: `entrypoints/teamwork_cli.py`, `entrypoints/self_digestion_cli.py`
  * Configurations: `the_master_and_margarita/wolands_retinue.yaml`, `the_master_and_margarita/retinue_schedules.yaml`
  * Infrastructure: `infrastructure/prompt_family_binder.py`, `infrastructure/teamwork_remote.py`
  * Tests: `omega_engine_woland/tests/`
- OEWAS & Operads: `omega_engine_operads/`
  * Catalog & Contracts: `catalog/contracts/v1/`
  * Ingress & Ports: `use_cases/`
  * Documentation Examples: `documentation/examples/prior_art_contract_binding.py`
- Operating System & IC Custody:
  * Migration: `omega_engine_operating_system/adapters/intelligence_custody/ic_migration.py`
  * Custody & Manifests: `_ic/darpa/woland/self_digestion/deletion_custody/`
  * Protected Archives: `_ic/nara/permanent_records/`, `historical/`, `_ic/odni/`
- PFP & Providers:
  * Management Ladder: `omega_engine_pfp/infrastructure/management_ladder.py`
  * Rust Provider Sources: `omega_engine/crates_rs/omega_woland/src/providers/`
- Cross-Host Governance Roots:
  * Canonical: `omega_engine_operads/skills/`
  * Host Gardens: `.agents/`, `.claude/`, `.codex/`, `.grok/`
  * Rule Registry: `omega_engine_operads/rules/rules_registry.yaml`
- E2E Test Suite:
  * `tests/e2e_woland_oewas_suite/`
  * Infrastructure: `TEST_INFRA.md`
  * Completion Signal: `TEST_READY.md`
