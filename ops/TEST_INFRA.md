# TEST_INFRA: Woland Adaptive Retinue, Yardstick, & OEWAS Closeout 4-Tier Opaque-Box E2E Testing Infrastructure

**AuthorityEffect**: None.  
**Project**: Woland Adaptive Retinue, Yardstick, & OEWAS Closeout (`EPIC-OE-WOLAND-005`, `EPIC-OE-WOLAND-CONSOLIDATED-RESIDUAL-001`, `EPIC-OE-OEWAS-011`, `EPIC-OE-OEWAS-012`)  
**Specification**: Requirement-Driven Opaque-Box Verification & Quality Assurance Infrastructure  
**Target Coverage**: 100% feature coverage across Features 1-26; 100% clean pass rate across 4 tiers  
**Scope**: All 26 Features defined in `PROJECT.md § Feature Inventory` and `ORIGINAL_REQUEST.md`  
**Canonical Directory**: `tests/e2e_woland_oewas_suite/`  
**Execution Environment**: Windows Python 3.12 (`py -3.12`) with basetemp isolation (`--basetemp .scratch/pytest_e2e`)  

---

## 1. Test Philosophy & Opaque-Box Architecture

The E2E testing infrastructure adheres to the **Dual-Track Testing Architecture**:

```
+---------------------------------------------------------------------------------------------------+
|                                   DUAL-TRACK TESTING ARCHITECTURE                                 |
+-------------------------------------------------+-------------------------------------------------+
| TRACK 1: Developer White-Box Unit Testing       | TRACK 2: Independent Opaque-Box E2E Testing     |
| - Co-located unit tests per package/module      | - Decoupled E2E tests in                        |
| - Internal state and branch coverage            |   tests/e2e_woland_oewas_suite/                 |
| - Authored by implementing worker agents        | - Requirement-driven, contract-based assertions |
| - Validates isolated algorithm logic            | - Authored by test_writer_e2e role              |
|                                                 | - Validates 4 tiers across all 26 features      |
+-------------------------------------------------+-------------------------------------------------+
```

### 1.1 Opaque-Box Independence
- **Requirement-Driven**: Tests assert behavior strictly against documented interface contracts in `PROJECT.md`, `ORIGINAL_REQUEST.md`, and authoritative epic plans, rather than private implementation details.
- **Fail-Closed Semantics**: Every validator, schedule compiler, falsification queue, manifest parser, and reality gate fails closed upon encountering invalid syntax, corrupted data, unverified claims, or unexpected states.
- **Lev Landau Falsification Standard**:
  1. *Invariant*: The exact algebraic boundary, 22-seat closed roster totality, zero-approval currency weight, or parent-linked hash chain that must hold.
  2. *Break Condition*: Hostile, ungrounded, tampered, stale, or missing artifacts designed to challenge the invariant.
  3. *Witness*: Observable typed refusal codes, non-zero return codes, or explicit assertion failures.
  4. *Mutation Response*: Verification that invalid inputs or mutant behaviors turn tests strictly RED.

### 1.2 Execution Discipline & Environment Pinning
- **Windows Python 3.12 Pinning**: On Windows workstations, all Python test sweeps execute via `py -3.12` or `sys.executable`.
- **Zero Paid Provider Calls**: All tests operate purely offline using deterministic fixtures, recorded run bundles, and exact local checkers. Live network calls to paid LLM providers are strictly blocked.
- **Strict Test Isolation**: Every test run specifies an isolated temporary directory (`--basetemp .scratch/pytest_e2e`). Tests clean up after themselves and do not depend on execution order.
- **Zero Silent Skips**: Absolutely no active `@pytest.mark.skip` or `pytest.skip()` calls without documented environment prerequisites.
- **Zero Bare Excepts**: No untyped `except:` blocks; all exception handlers declare explicit exception types.
- **Pure UTF-8**: All source files and test fixtures encoded in UTF-8 without Byte Order Marks (`\xef\xbb\xbf`).

---

## 2. 4-Tier Test Methodology

The E2E test suite partitions verification across four progressive tiers under `tests/e2e_woland_oewas_suite/`:

```
+---------------------------------------------------------------------------------------------------+
|                                 TIER 4: REAL-WORLD APPLICATION                                    |
| - Complete 22-Role Retinue Execution with Offline Deterministic Fixtures                          |
| - Full Yardstick Trial Comparison & Pareto Frontier Evaluation                                    |
| - Deletion Custody Manifest Verification & Protected Archives Fencing                             |
| - Republication Checklist Gate (9 Channels, 52 Checks) Verification                               |
| - End-to-End OEWAS Contract Binding & IC Historical Route Compatibility Replay                    |
+---------------------------------------------------------------------------------------------------+
                                                  ^
+---------------------------------------------------------------------------------------------------+
|                               TIER 3: CROSS-FEATURE COMBINATIONS                                  |
| - Presets Combined with Schedule Skip Logic (e.g. cheap-falsifiers + quorum3_blind)                |
| - Blind Cohorts Combined with Quorum Clean Streak Resetting on Findings                           |
| - Thompson Sampling Combined with Zero-Cost Seat Marginal Values                                  |
| - Bounded Critic-Target Loops Combined with Multi-Model Tiers                                     |
| - Falsification Queue Combined with Failure Attachment to Prompt Families                         |
+---------------------------------------------------------------------------------------------------+
                                                  ^
+---------------------------------------------------------------------------------------------------+
|                                 TIER 2: BOUNDARY & CORNER CASES                                   |
| - Required Seats (hella, azazello, jeremy, koroviev, woland, bezdomny) Cannot Be Turned Off/Blind |
| - Quorum Count Ignored Fails Closed                                                               |
| - Skipped Role Reported as Observed Fails Closed                                                  |
| - Frozen Historical Inventory with Baseline Duplicate Paths Parsed Safely (historical=True)       |
| - Wilson Counts Rejections (Negative Counts, Booleans, n=0) & Input Non-Coercion Refusals        |
+---------------------------------------------------------------------------------------------------+
                                                  ^
+---------------------------------------------------------------------------------------------------+
|                                   TIER 1: FEATURE COVERAGE                                        |
| - F0 Failure-First Currency (Approvals carry 0 weight; host checker verifies; false alarms)       |
| - F3 Roster Accounting (retinue_coverage reports declared, scheduled, contributed, reproduced)   |
| - F2 Falsification Queue (Digest pinning; stale candidate rejection)                             |
| - A6 Parallel Blind Cohorts (Pre-cohort binding; deterministic observation sequence)              |
| - A5 / F1 / F4 / F5 Multi-Model Tiers, Presets, Digest-Pinned Bundles                             |
| - A4 Bounded Critic-Target Loops (Begemot-Koroviev, Koroviev-Bezdomny, round limits)              |
| - F6 / L1-L3 Failure Attachment, Schedule Thompson Sampling, Operand Promotion                    |
| - S6 / S7 Operad Yield-per-Dollar, Retirement, Deletion Custody Cleanup                           |
| - OEWAS-011 & 012 Contract Binding, Ingress Non-Coercion, IC History, Management Ladder          |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Comprehensive Feature Mapping Matrix (All 26 Features)

| # | Feature ID | Feature Name | Milestone | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Primary Test Location |
|---|------------|--------------|:---------:|:------:|:------:|:------:|:------:|-----------------------|
| 1 | F1 | Prior Art Contract Binding Hash Repair | M1 | Yes | - | - | Yes | `test_tier1_feature_coverage.py`, `test_tier4_real_world_application.py` |
| 2 | F2 | IC Historical Baseline Case Collision Fix | M1 | Yes | Yes | - | Yes | `test_tier1_feature_coverage.py`, `test_tier2_boundary_corner.py`, `test_tier4_real_world_application.py` |
| 3 | F3 | Management Ladder Provider Paths Fix | M1 | Yes | - | - | - | `test_tier1_feature_coverage.py` |
| 4 | F4 | Remnant 008_oewas Directory Cleanup | M1 | Yes | - | - | - | `test_tier1_feature_coverage.py` |
| 5 | F5 | Epic Manifest Resealing & OEWAS Verification | M1 | Yes | - | - | Yes | `test_tier1_feature_coverage.py`, `test_tier4_real_world_application.py` |
| 6 | F6 | Regression Test Antibody Path Update | M2 | Yes | - | - | - | `test_tier1_feature_coverage.py` |
| 7 | F7 | Duplicate Antibodies Deletion Custody | M2 | Yes | - | - | Yes | `test_tier1_feature_coverage.py`, `test_tier4_real_world_application.py` |
| 8 | F8 | Self-Digestion Runs Deletion Custody | M2 | Yes | Yes | - | Yes | `test_tier1_feature_coverage.py`, `test_tier2_boundary_corner.py`, `test_tier4_real_world_application.py` |
| 9 | F9 | Failure-First Currency (F0) | M3 | Yes | Yes | Yes | Yes | `test_tier1_feature_coverage.py`, `test_tier2_boundary_corner.py`, `test_tier3_cross_feature.py`, `test_tier4_real_world_application.py` |
| 10 | F10 | Roster Accounting Extension in retinue_coverage (F3) | M3 | Yes | Yes | Yes | Yes | `test_tier1_feature_coverage.py`, `test_tier2_boundary_corner.py`, `test_tier3_cross_feature.py`, `test_tier4_real_world_application.py` |
| 11 | F11 | Yardstick Evidence Metrics Extension (F3) | M3 | Yes | - | Yes | Yes | `test_tier1_feature_coverage.py`, `test_tier3_cross_feature.py`, `test_tier4_real_world_application.py` |
| 12 | F12 | F0 Falsification Test Suite | M3 | Yes | Yes | - | - | `test_tier1_feature_coverage.py`, `test_tier2_boundary_corner.py` |
| 13 | F13 | Bounded Critic-Target Loops (A4) | M4 | Yes | - | Yes | - | `test_tier1_feature_coverage.py`, `test_tier3_cross_feature.py` |
| 14 | F14 | Falsification Queue & Blind Cohorts (F2, A6) | M4 | Yes | Yes | Yes | - | `test_tier1_feature_coverage.py`, `test_tier2_boundary_corner.py`, `test_tier3_cross_feature.py` |
| 15 | F15 | Multi-Model Run Ledger, Tiers & Presets (A5, F1, F4, F5) | M4 | Yes | - | Yes | - | `test_tier1_feature_coverage.py`, `test_tier3_cross_feature.py` |
| 16 | F16 | Prompt-Family Failure Attachment (F6) | M5 | Yes | - | Yes | - | `test_tier1_feature_coverage.py`, `test_tier3_cross_feature.py` |
| 17 | F17 | Schedule Telemetry & Thompson Sampling (L1, L2) | M5 | Yes | - | Yes | - | `test_tier1_feature_coverage.py`, `test_tier3_cross_feature.py` |
| 18 | F18 | Operand Promotion (L3) | M5 | Yes | - | - | - | `test_tier1_feature_coverage.py` |
| 19 | F19 | Operad Yield-per-Dollar & Retirement (S6) | M5 | Yes | - | - | Yes | `test_tier1_feature_coverage.py`, `test_tier4_real_world_application.py` |
| 20 | F20 | Rule & Cross-Host Parity Sync | M5 | Yes | Yes | - | - | `test_tier1_feature_coverage.py`, `test_tier2_boundary_corner.py` |
| 21 | F21 | Woland Test Suite Totality Pass | M6 | - | - | - | Yes | `test_tier4_real_world_application.py` |
| 22 | F22 | Theoretical Minimum Falsifiers & Mutation Controls | M6 | - | Yes | - | - | `test_tier2_boundary_corner.py` |
| 23 | F23 | Cross-Host Mirrors & Republication Gate | M6 | - | - | - | Yes | `test_tier4_real_world_application.py` |
| 24 | F24 | E2E Test Suite Construction | E2E | Yes | Yes | Yes | Yes | Entire Suite (`tests/e2e_woland_oewas_suite/`) |
| 25 | F25 | Final Milestone E2E Test Suite Pass | M6 | Yes | Yes | Yes | Yes | Suite Execution & `TEST_READY.md` |
| 26 | F26 | Adversarial Coverage Hardening (Tier 5) | M6 | - | Yes | Yes | - | `test_tier2_boundary_corner.py`, `test_tier3_cross_feature.py` |

---

## 4. Test Runner Commands

### 4.1 Running the Full E2E Test Suite
```powershell
py -3.12 -m pytest tests/e2e_woland_oewas_suite/ -v --basetemp .scratch/pytest_e2e
```

### 4.2 Running Specific Tiers via Pytest
```powershell
# Tier 1: Feature Coverage (F0, F3, F2, A6, A5/F1/F4/F5, A4, F6/L1-L3, S6/S7, OEWAS)
py -3.12 -m pytest tests/e2e_woland_oewas_suite/test_tier1_feature_coverage.py -v --basetemp .scratch/pytest_e2e

# Tier 2: Boundary & Corner Cases (Required seats, quorum ignore, skipped-as-observed, historical inventory)
py -3.12 -m pytest tests/e2e_woland_oewas_suite/test_tier2_boundary_corner.py -v --basetemp .scratch/pytest_e2e

# Tier 3: Cross-Feature Combinations (Presets + schedules, blind + quorum, Thompson + seat values)
py -3.12 -m pytest tests/e2e_woland_oewas_suite/test_tier3_cross_feature.py -v --basetemp .scratch/pytest_e2e

# Tier 4: Real-World Scenarios (Retinue execution, yardstick comparison, deletion custody, republication)
py -3.12 -m pytest tests/e2e_woland_oewas_suite/test_tier4_real_world_application.py -v --basetemp .scratch/pytest_e2e
```

---

## 5. Pass/Fail Criteria & Acceptance Standards

1. **Pass Rate**: 100% of authored tests across all 4 tiers must pass without unhandled exceptions.
2. **Execution Integrity**: Zero silent skips (`pytest.skip` / `@pytest.mark.skip` count == 0 on offline suites).
3. **Encoding & Hygiene**: Pure UTF-8 without BOM across all files.
4. **Claim Discipline**: All summary claims and test assertions adhere strictly to claim hygiene (`AuthorityEffect: None`, narrow defensible claims, forbidden hype verbs strictly audited).
5. **Fail-Closed Gate Operation**: Approval replies carry zero acceptance weight; failure claims count only when verified by an independent host checker; attempts to turn off required seats or ignore quorums fail closed.
6. **Protected Archives Safety**: Permanent records in `_ic/nara/permanent_records`, `historical`, and `_ic/odni` must never be modified or deleted.
