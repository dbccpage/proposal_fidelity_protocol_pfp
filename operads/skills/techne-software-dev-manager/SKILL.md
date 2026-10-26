---
name: techne-software-dev-manager
description: "Enforce Rust and Python parity and Clean Architecture; veto modules with under 95 percent coverage or drift."

operad_source_colours: ["Code", "State", "Contract"]
operad_target_colour: "Code"
operad_arity: 3
operad_residual: "unknown"
---

# techne-software-dev-manager

## authority_effect_ceiling: None

## 1. Governance & Mandate

- **Parity Guarantee:** Ensure 1:1 structural and operational parity between Rust production crates (`omega_engine/crates/<crate>`) and Python companion packages (`omega_engine_py/<package>`).
- **Minimum Test Coverage Gate:** Veto any crate, package, or module whose test line coverage falls below **95%**.
- **Authority Ceiling:** `AuthorityEffect: None`. Code checks enforce standards; descent and human review authorize releases.

---

## 2. Engineering Standards & Design Patterns

### A. Clean Architecture & Layer Isolation

- **Domain Core (`omega_types` / `omega_contracts`):** Zero external dependencies, pure domain models and contract invariants.
- **Application Services / Pipeline Runners:** Stateless orchestrators executing pure state transforms.
- **Adapters & Interfaces (`omega_retrieval` / CLI):** Provider-neutral bridges into SQLite FTS5, file IO, or network APIs.

### B. Functional Programming Patterns

- Immutable data structures and explicit value types.
- Pure functions for all numerical calculation, hash derivation, and contract validation.
- Algebraic Data Types (Enums/discriminated unions) with total pattern matching.

### C. Antipattern Prohibitions Across Languages

| Language | Prohibited Antipatterns |
| --- | --- |
| **Rust** | Micro-crate proliferation, `unwrap()`/`expect()` in library paths without invariant context, swallowing `Result` or `Option`, non-deterministic thread ordering in tests, main looper thread blocking. |
| **Python** | Missing Pydantic v2 schemas, untyped function signatures, dynamic monkey-patching, swallow-all `except Exception: pass`, un-parameterized raw SQL strings. |
| **SQL / BigQuery** | Un-indexed full scans, non-deterministic `ORDER BY` without tie-breakers, string concatenation for queries (injection vulnerability). |
| **Lean 4** | Unproven `sorry`/`admit` in production proof paths, broken Lake reachability, non-canonical module imports outside `omega_engine/lean4/research_programs/`. |

---

## 3. Audit Protocol & Execution

When invoked manually or via `/rip-code`:

1. **Parity Check:** Compare exported symbols and structs between `omega_engine/crates/<crate>` and `omega_engine_py/<package>`. Report missing or un-synced modules.
2. **Coverage Audit:** Run `cargo tarpaulin` / `pytest --cov` or inspect test manifests. Reject any component under 95% line/branch coverage.
3. **Antipattern Sweep:** Scan for prohibited patterns, swallowing errors, or hardcoded magic constants.
4. **Emit Report:** Produce a `techne_software_dev_manager_receipt` table:
   - `PARITY_STATUS: PASS | DESYNCED` ext
   - `COVERAGE_STATUS: PASS (>=95%) | REJECTED (<95%)` ext
   - `ARCHITECTURAL_DRIFT: NONE | DETECTED` ext

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
