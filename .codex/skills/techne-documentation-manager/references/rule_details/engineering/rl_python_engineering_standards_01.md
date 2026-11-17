# Detailed definition: Python Engineering Standards (1)

**AuthorityEffect:** None.

Parent: [Python Engineering Standards](../../../../../rules/engineering/rl_python_engineering_standards.md). Load for the matching predicate, not every task.

# Rule: Python Engineering & Linter Hygiene Standards

**AuthorityEffect:** None.

This rule codifies standard library dataclass field imports, dynamic module loading sys.modules registration, zero-tolerance linter and import hygiene (F401, F841, I001), scoped mypy import checking, and structural pattern matching and control flow complexity discipline across Python engine code.

---

## Standard Library Dataclass Field Discipline Invariant (`RULE_PYTHON_DATACLASS_FIELD_001`)

> **Standard Dataclasses Field Import:**
>
> 1. Dataclass field definitions (`field(...)`) must always be imported directly from the standard library `dataclasses` module (`from dataclasses import field`).
> 2. Code must never import `field` from third-party wrappers such as `pydantic.dataclasses`, which do not re-export `field` in modern Python runtime environments.

## Dynamic Module Loading & Dataclass Module Registration Invariant (`RULE_PYTHON_DYNAMIC_DATACLASS_IMPORT_001`)

> **Dynamic Loader `sys.modules` Registration:**
>
> 1. When dynamically loading Python source files or test modules via `importlib.util.spec_from_file_location` and `importlib.util.module_from_spec`, the module instance MUST be registered in `sys.modules` (`sys.modules[name] = mod`) **before** executing `spec.loader.exec_module(mod)`.
> 2. This prevents modern Python `@dataclass` decorators and type introspection utilities from failing due to missing `sys.modules` references during class decoration.

## Python Linter & Import Hygiene Zero-Tolerance Invariant (`RULE_PYTHON_LINTER_CLEANLINESS_001`)

> **AST Cleanliness, Zero Unused Bindings & Strict Import Sorting:**
>
> 1. **Zero Unused Variables & Imports (`F401`, `F841`):** All newly written or modified Python modules and test files must maintain zero unused local variables, unconsumed bindings, and unused imports. Never leave phantom imports from previous drafts.
> 2. **Strict Import Sorting Discipline (`I001` / isort):** Imports must be ordered strictly according to PEP 8 / isort grouping:
>    a. Standard library imports (alphabetical)
>    b. Blank line
>    c. Third-party imports (alphabetical)
>    d. Blank line
>    e. First-party and local package imports (alphabetical)
>    Zero un-sorted or un-formatted import blocks are permitted.
> 3. **Zero Speculative Typing Imports:** Agents must never shotgun import typing symbols (e.g. `from typing import Any, Dict, List, Optional, Tuple, Union, Callable`). Under Python 3.9+ with `from __future__ import annotations`, use built-in lowercase collections (`dict`, `list`, `tuple`, `set`) and only import symbols from `typing` that are actively referenced in type signatures.
> 4. **Pre-Completion Linter Check:** Prior to completing any Python task or reporting results, agents must execute targeted linter checks on modified files using `py -3.12 -m ruff check --select F401,I <files>` (or `py -3.12 -m ruff check --fix <files>`).
> 5. **Dynamic Import Exemption:** Where dynamic `sys.path.insert(...)` is required before module imports in standalone test or script contexts, imports must be annotated with `# noqa: E402`.
> 6. **Deep Package Import Line-Length Discipline:** For deeply nested Clean Architecture paths where the import statement prefix alone approaches or exceeds the 100-character line limit, import the parent module under a concise domain alias (e.g. `from <deep_context>.use_cases import <name>_use_case as <alias>`) and bind functions locally, rather than adding `# noqa: E501` line-length overrides.
> 7. **Assertion Consumption:** In test functions, constructed carriers, fixtures, or intermediate outcomes must be asserted or verified (e.g. `assert carrier.validate() is True`), never instantiated and silently abandoned.
> 8. **Pytest Fixture Ingestion Hygiene (`F811`):** Test modules must NEVER import fixture functions directly from other test modules. Shared fixtures must be defined in `conftest.py` where pytest discovers and injects them automatically by parameter name; importing them causes parameter shadowing and unsuppressible Ruff `F811` errors.

## Scoped Mypy Import Checking Invariant (`RULE_PYTHON_MYPY_IGNORE_SCOPE_001`)

> **No global `ignore_missing_imports`:**
>
> 1. Setting `ignore_missing_imports = true` under an unscoped `[tool.mypy]` silences missing modules across the whole tree.
> 2. Scope overrides to the modules that need them. See `AP_PY_001` / `HP_PY_001` in `.agents/patterns/anti/python/`.

## Structural Pattern Matching & Control Flow Nesting Invariant (`RULE_PYTHON_CYCLOMATIC_AND_NESTING_DISCIPLINE_001`)

> **Idiomatic Pattern Matching & Complexity Discipline:**
>
> 1. **Loop & Control Nesting Ceiling:** Functions in `domain/` and `use_cases/` must not nest loops (`for`, `while`) or control branches deeper than **3 levels**. If an algorithm requires multi-axis iteration (e.g. matrix walks or tableau searches), decompose the logic into named, single-responsibility helper functions.
> 2. **Cyclomatic Complexity Limit:** Every domain and use-case function must adhere to McCabe cyclomatic complexity $M \le 10$, verifiable via `py -3.12 -m ruff check --select C901 --config "lint.mccabe.max-complexity = 10" <target>`.
> 3. **Avoid Deep Nested Conditional Pyramids:** Avoid generating $\ge 2$-level nested `if isinstance(...)` conditional trees when parsing or evaluating AST nodes, syntax trees, or polymorphic envelopes. Use Python 3.10+ `match / case` structural pattern matching with class patterns and guards, or extract dedicated guard predicates with early returns.
> 4. **Guard Clauses Over Nesting:** Favor early returns, guard clauses, and Railway-Oriented Programming (`Result[T, E]`) over deeply indented `if-else` cascades.
