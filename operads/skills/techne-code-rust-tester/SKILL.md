---
name: techne-code-rust-tester
description: "Write and run Rust tests. Integration tests, property tests and exact rational certifiers."

operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "unknown"
---

# techne-code-rust-tester

**Source:** Sprint 324-0 session (2026-03-24), updated Sprint 324-0-0 (2026-03-24)

## Known Toolchain Issues

**Source:** Session 2026-03-22 (7 physics sub-lambdas: L059_2 QCD, L059_3 Quantum Optics, L065_1 CFT Bootstrap, L068_1 M-Theory, L068_2 Superstrings, L069_1 Holographic Entanglement, L069_2 AdS/CFT Advanced)
**Key conventions:**
**Implementation .rs** (~250-300 lines):
**mod.rs** (37-line doc header):

### Physics Sub-Lambda Template (Tier 6-8)

## Domain-as-Sheaf Lambda Template (Batch Generation)

## Functional Style Mandate

## Lambda Test Remediation Checklist

## Axiom Necessity Testing (Python Proof Scripts)

## Evidence Capture

## Techne Code Inspector Compatibility

## Test Gap Classification

## Test Naming

## Test Gap Detection

**Source:** Sprint 324 — 29 errors across 8 files, all 5 patterns above.

## Common Test Compilation Error Patterns

## Rand 0.10 API

## Property-Based Testing

## GF(2) Cohomological Tests

## Floating Point Comparison

### D. Dummy Carrier Boilerplate

### C. Governance Outcome Completeness

### B. Mock Oracle Coupling

### A. Test Struct Evolution (Builder Pattern)

### 5. Test Context and Mocks

**Rule (source-scanning matchers):** A test/gate that scans Rust source TEXT (e.g. a `tests/*conformance.rs` gate) must strip literals+comments before substring-matching (reuse `sentinel_councils::test_quality::strip_literals_and_comments`), require an identifier boundary on **both** sides, and strip each file once. See rust-principal-developer → *Source-Scanning Matcher Hygiene*.
**Rule:** Production code should prefer `Result` types over `unwrap()`/`expect()`. Only use `expect()` when an invariant guarantees success, and document the invariant with a `// SAFETY:` or `# Invariant` comment.

#### E. Fixed Examples (Session 2026-03-24)

#### D. Audit Commands

#### C. Empty Collection Access

#### B. Division-by-Zero

#### A. Unwrap/Expect in Production Code

**Production code must be free of panic-inducing patterns.** Audit lambda modules for:

### 4. Security Audit Tests

### 3. Edge Case Tests

### 2. Physics-as-Sheaf Tests

### 1. Categorical Tests

## Test Categories

**Source:** Session 2026-03-24 (proof_solver.rs integration, 2 type mismatches fixed)

### Lambda Integration Type Matching

**Source:** Session 2026-03-24 (user explicit stop after compiler stack overflow)
**NEVER** run background builds on Windows. The canonical build target is Linux.
**Verification strategy on Windows (no compilation):**
**CRITICAL: Do NOT compile the `engine` workspace on Windows unless the user explicitly requests it.**

### Cross-Platform Compilation (Windows Resource Constraint)

**Known issue (test compilation):** `cargo test --lib` may report errors in `#[cfg(test)]` blocks even when `cargo check` passes clean. Pre-existing test-only errors (E0689 ambiguous float, E0061 argument mismatch after signature changes) accumulate when function signatures evolve but test callsites are not updated. Track these as test-debt, distinct from library compilation errors.
**Known issue (runtime):** Test binary may fail with `STATUS_DLL_NOT_FOUND` (0xc0000135) on Windows when PyO3 DLLs are not in PATH. Use `--no-run` to verify compilation.
**Read cargo's exit code, not the pipeline's.** `cargo test ... | grep | tail` reports the

### Toolchain and Build Policy

### Integration Tests

#### Cargo Staged Test Target Isolation (`autotests = false`)

When porting or refactoring multi-file test suites where some test files remain staged or legacy:
1. Disable automatic discovery in `Cargo.toml`:
   ```toml
   [package]
   autotests = false
   ```
2. Explicitly register only verified test targets:
   ```toml
   [[test]]
   name = "verified_suite"
   path = "tests/verified_suite.rs"
   ```
3. Run targeted tests without compiling unlinked scratch files:
   ```bash
   cargo test -p <crate_name> --test verified_suite
   ```

**Source:** Session 2026-03-27 (proof_solver.rs unused-import fix)

### Test-Only Import Gating

### Inline Tests (standard pattern)

## Test Structure

## When to Activate

## description: Test patterns for engine Rust crates (inline tests, property tests, categorical invariants, edge cases). Use when writing tests under engine/crates/

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
