---
pattern_id: AP_PY_017
name: verification_chain_hallucination_phantom_tests
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_016_fail_closed_test_suite_disk_verification
language: python
authority_effect: None
---

# Anti-Pattern: Verification Chain Hallucination / Phantom Test Suite (`AP_PY_017`)

## Description

A worker or subagent reports that a test directory (e.g., `tests/e2e/`) contains a suite of tests and claims all passed. Reviewers and orchestrators accept this count transitively without running the suite or checking whether the path exists on disk. In reality, the directory does not exist, and running the command yields `ERROR: file or directory not found`.

## Detection Signature

- Reports or receipts citing test suites whose directory path cannot be resolved on disk:
  ```python
  # BAD: Trusting reported pass metrics without verifying directory existence
  if reported_pass_count > 0:
      record_gate_pass("e2e_suite", count=reported_pass_count)
  ```
- Good Pattern:
  ```python
  # GOOD: Fail-closed path existence check before recording verification
  suite_path = repo_root / "tests" / "e2e"
  if not suite_path.is_dir():
      raise RefusalError("PHANTOM_TEST_SUITE", f"Directory {suite_path} does not exist on disk")
  ```

## Hazard & Failure Mode

- Hallucinates complete verification coverage across milestones and orchestrator quad-receipts.
- Allows unverified or missing code to pass release gates unchecked.

## Prevention & Resolution

A test suite does not exist unless `pytest` or `cargo test` is executed directly by the verifying agent and returns exit code 0 on the current worktree. Prior to accepting any test pass report, verify `path.is_dir()` and assert non-zero collected items.
