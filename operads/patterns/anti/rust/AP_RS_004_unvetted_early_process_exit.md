---
pattern_id: AP_RS_004
name: unvetted_early_process_exit
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_RS_004_structured_exit_and_count_gate
language: rust
authority_effect: None
---

# Anti-Pattern: Unvetted Early Process Exit (`AP_RS_004`)

## Description

Subprocesses or test candidates invoking immediate process exit (such as `os._exit(0)`, `std::process::exit(0)`, or terminating signals) during test collection or execution phases, causing test harnesses to record an exit status of 0 without running any required verification assertions.

## Detection Signature

- AST Pattern: Direct calls to `os._exit`, `sys.exit`, or `std::process::exit` within test files or candidate payloads.
- Regex: `(os\._exit\(0\)|process::exit\(0\))` in candidate diffs or test harness boundaries.
- Harness Pattern: A test runner reporting exit code 0 while execution logs record 0 collected or passed tests.

## Hazard & Failure Mode

- Oracles and test runners interpret exit code 0 as test suite success.
- Candidates with invalid, unvetted, or breaking behavior are falsely admitted as verified.
- Bypasses the entire truth verification boundary.

## Dual Healthy Pattern

See [HP_RS_004_structured_exit_and_count_gate](../../helpful/rust/HP_RS_004_structured_exit_and_count_gate.md).
