---
name: migration-coverage-reconciler
description: Audits and reconciles test coverage and FFI boundary parity between legacy Python implementations and native Rust ports.
operad_source_colours: ["Code", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
authority_effect: None
---

# Migration Coverage Reconciler (`migration-coverage-reconciler`)

## Intent

Systematically audits the 33 verification subdomains of the Python-to-Rust native migration, verifying line/branch coverage reports, LCOV data, and FFI regression suites.

## Verification Checklist

1. **Subdomain Verification:** Inspect `coverage.json` and LCOV reports across each verification cohort (immune, the city, woland, workflow, etc.).
2. **FFI Parity:** Ensure native Rust implementations match Python DTO shapes and fail-closed error contracts.
3. **No Coverage Regressions:** Verify that ported Rust code achieves equal or superior branch coverage compared to baseline Python modules.
4. **Log Cleanliness:** Verify zero compiler warnings, zero clippy violations, and clean test runs.
