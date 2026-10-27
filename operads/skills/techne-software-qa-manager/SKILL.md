---
name: techne-software-qa-manager
description: "Run the QA gate chain. Test inspector veto, silent-skip detection, docstring audit, red team, repair loop."
status: active
invocation: entry
authority_effect: none
operad_source_colours: ["Code", "Audit", "Receipt"]
operad_target_colour: "Audit"
operad_arity: 3
operad_residual: "unknown"
---

# techne-software-qa-manager

The master software quality assurance and verification orchestrator for the Sentinel Logos Techne engineering panel. Enforces rigorous falsification, small-batch test discipline, and a hard-veto repair loop.

## 1. QA Verification Protocol & Auto-Repair Loop

When invoked (`/techne-software-qa-manager <target_path> [--budget 3]`), the QA manager executes a 5-stage verification gate:

```text
[Stage 1: Pre-Flight Cleanliness & Boundaries]
  │ - techne-contract-docstring-import-boundary-auditor: Line 1 docstrings, 0 E402
  │ - techne-docs-lint-hunter-killer: UTF-8 encoding, zero BOM, 0 markdown errors
  ▼
[Stage 2: Inspector Hard Veto Gate]
  │ - techne-code-inspector: Flags fake-green tests, mock-only illusions,
  │   missing fixtures, and unasserted exceptions.
  │ - techne-test-silent-skip-detector: Flags pytest.skip / bare returns.
  │
  ├─► [Veto Triggered] ──► [Auto-Repair Loop (Budget N <= 3)]
  │                          │ Dispatches failing test/code to techne-code-builder
  │                          │ for hardened mutation repair. Re-enters Stage 2.
  │                          ▼
  │                        [Budget Exhausted] ──► Emit Typed Refusal Receipt (REFUSED)
  ▼
[Stage 3: Small-Batch Test Execution]
  │ - Executes targeted test files only (NEVER whole-suite sweeps):
  │   `python -m pytest <specific_test_file>.py -v`
  │   `cargo test --package <specific_crate> --lib`
  │ - Reproduces the named failing gate directly before aggregate replay.
  ▼
[Stage 4: DDA Invariant & Duality Descent Audit]
  │ - Verifies monotonic defect descent: ΔΦ₁ <= 0, ΔΓ₂ <= 0, Δdefect_count <= 0.
  ▼
[Stage 5: Red Team ChatGPT Adversarial Red Team Audit]
  │ - techne-qa-pr-reviewer / Red Team ChatGPT Red Team Identity v2
  │ - Merciless adversarial falsification check and audit report emission.
```

## 2. Invariants & Execution Rules

1. **Small-Batch Test Execution Invariant (`RULE_TEST_SMALL_BATCH_001`):**
   **YOU MUST NEVER RUN ALL TESTS AT ONCE.** The QA manager runs only individual test files or scoped packages relevant to the active change.

2. **Inspector Hard Veto (`RULE_STRICT_VETO_001`):**
   Any test that passes by asserting nothing (bare returns on missing fixtures, tautological existence assertions, mock-only self-comparisons) is vetoed immediately.

3. **Finite Repair Budget Invariant (`RULE_REPAIR_BUDGET_001`):**
   Auto-repair is capped at $N = 3$ iterations. If defects remain after 3 cycles, execution halts with a typed `RefusalReceipt` rather than looping indefinitely.

4. **Direct-Gate Debugging Invariant (`RULE_DIRECT_GATE_FIRST_001`):**
   Reproduce the named failing gate and check protected evaluator anchors before aggregate replay. Aggregate local CI and PR review confirm one stable final head; they are not an iterative debugging loop. Never rerun an unchanged refusal.

5. **Receipt Emission:**
   Upon completion, emits a canonical `SoftwareQaReceiptV1`:

   ```yaml
   schema_version: core.software-qa-receipt.v1
   status: PASSED | REFUSED
   authority_effect: None
   target_path: engine/...
   strict_veto_status: CLEAN
   silent_skips_detected: 0
   small_batch_tests_passed: 12
   repair_rounds_used: 1
   omc_report_ref: _intelligence/omc_dags/omc_report_...md
   ```
