---
name: clean-extraction-dependency-replay
description: Reproduce each advertised verification profile from a fresh extraction without the developer's checkout.
operad_source_colours: ["State", "Contract"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# Clean-Extraction Dependency Replay

**AuthorityEffect:** None.

## Purpose & Invariant

Reproduce each advertised verification profile from a fresh extraction without relying on ambient state in the developer's checkout. Resolve every required dependency through deposited sources or a pinned, verified bootstrap, and record unavailable prerequisites as `BLOCKED` rather than `PASS`.

## Execution Protocol

1. **Extraction Hermeticity:**
   - Extract the release archive into an isolated clean directory (`C:\lk\clean_test` or temporary directory).
   - Ensure the working environment does not inherit undeclared external repositories or ambient workspace modules on `PYTHONPATH` or `CARGO_TARGET_DIR`.

2. **Profile Separation:**
   - **Profile A (Standalone Archive-Only):**
     - Execute pure Python and core Lean verification suites.
     - Any check requiring unbundled native binaries must gracefully return `NO_RULE` or `BLOCKED` and never claim successful native verification or falsely reject valid certificates.
   - **Profile B (Full Native & Surrounding Repository):**
     - Document all external crate path dependencies explicitly.
     - Verify dependencies against pinned commits or workspace locations before compiling binaries (`evaluate_wdp_functionals`).
     - Execute the full certified progress and native solver test suites.

3. **Gate Verification Check:**
   - Extract the release into a fresh directory, resolve the selected profile's dependencies, build `evaluate_wdp_functionals`, and execute that profile's documented checks.
   - Fail the release profile if it depends on an undeclared local source tree or pre-existing binary.
