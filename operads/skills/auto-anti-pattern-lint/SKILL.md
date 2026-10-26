---
name: auto-anti-pattern-lint
description: "Scan repository codebase against the 18 mined anti-patterns across Lean 4, Python, Rust, and SQL."
operad_source_colours: ["Code"]
operad_target_colour: "Receipt"
operad_arity: 1
operad_residual: "unknown"
families: [governance, linting, quality]
---

# Anti-Pattern Registry Linter (`anti-pattern-lint`)

**AuthorityEffect:** None.

## Purpose

Automate detection of known repository anti-patterns codified in `_intelligence/archive/anti_patterns_registry.json` across Lean 4, Python, Rust, and SQL codebases.

## Mined Patterns & Signatures

1. **Python**:
   - `AP_PY_001` (Blanket Mypy Ignore): Disallow `ignore_missing_imports = true` globally in `pyproject.toml`. Enforce scoped overrides (`HP_PY_001`).
   - `AP_PY_002` (Array Hash/Equality Asymmetry): Reject mutable numpy/list equality without normalized tuple conversion (`HP_PY_002`).
2. **Rust**:
   - `AP_RS_001` (Worktree Target Duplication): Disallow unshared `target/` directories causing disk bloat. Use `CARGO_TARGET_DIR` (`HP_RS_001`).
   - `AP_RS_002` (Domain Enum Missing Ord): Enforce deterministic ordering traits (`Ord`, `PartialOrd`) on all domain key enums (`HP_RS_002`).
   - `AP_RS_003` (Incremental Cache Disk Exhaustion): Enforce periodic cargo clean / cache pruning (`HP_RS_003`).
3. **Lean 4**:
   - `AP_LN_001` (Unmechanized Sorry): Disallow `sorry` in verified theorem claims (`HP_LN_001`).
   - `AP_LN_002` (Unconstrained Lake Rebuild): Require scoped target cache builds (`HP_LN_002`).
4. **SQL**:
   - `AP_SQL_001` (Unparameterized String Query): Enforce parameterized query binding against SQL injection (`HP_SQL_001`).
   - `AP_SQL_002` (Unbounded Transaction Leak): Enforce Unit of Work transaction fences with context managers (`HP_SQL_002`).

## Execution Command

```powershell
py -3.12 omega_engine_operads/skills/anti-pattern-lint/scripts/anti_pattern_lint.py --catalog .agents/patterns --check
```

The lint checks that every required catalog slot exists under `anti/` and `helpful/` and that each `AP_*.md` names a dual pattern file. Empty slots are valid. OEAUTOP calls this script on every run.
