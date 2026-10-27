---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
---

# Rule: Python Engineering Standards

**AuthorityEffect:** None.

**Guard:** Standard library dataclass field discipline, dynamic module loading sys.modules registration, zero-tolerance linter & import hygiene (F401/F841/I001), scoped mypy import checking, and cyclomatic complexity and nesting discipline.

**Compose:** [shared boundary vocabulary](../../skills/techne-documentation-manager/references/rules_index.md#shared-boundary-vocabulary). Read the relevant definition before acting; retain its conditions, exceptions, witnesses and refusal.

## Definitions, loaded on demand

- [Part 1](../../skills/techne-documentation-manager/references/rule_details/engineering/rl_python_engineering_standards_01.md): Rule: Python Engineering & Linter Hygiene Standards; Standard Library Dataclass Field Discipline Invariant; Dynamic Module Loading & Dataclass Module Registration Invariant; Python Linter & Import Hygiene Zero-Tolerance Invariant; Scoped Mypy Import Checking Invariant; Structural Pattern Matching & Control Flow Nesting Invariant.

## Stable invariant references

`RULE_PYTHON_CYCLOMATIC_AND_NESTING_DISCIPLINE_001`, `RULE_PYTHON_DATACLASS_FIELD_001`, `RULE_PYTHON_DYNAMIC_DATACLASS_IMPORT_001`, `RULE_PYTHON_LINTER_CLEANLINESS_001`, `RULE_PYTHON_MYPY_IGNORE_SCOPE_001`.
