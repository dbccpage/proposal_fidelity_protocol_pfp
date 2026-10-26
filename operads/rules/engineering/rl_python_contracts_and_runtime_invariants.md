---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
  - "pytest.ini"
---

# Rule: Python Contracts & Runtime Invariants

**AuthorityEffect:** None.

**Guard:** Boolean subclass guard in exact numeric contracts, array value object hash/equality normalization, zero-assert production runtime checking, explicit subprocess check discipline, monkeypatch signature parity, and YAML colon quoting discipline.

**Compose:** [shared boundary vocabulary](../../skills/techne-documentation-manager/references/rules_index.md#shared-boundary-vocabulary). Read the relevant definition before acting; retain its conditions, exceptions, witnesses and refusal.

## Definitions, loaded on demand

- [Part 1](../../skills/techne-documentation-manager/references/rule_details/engineering/rl_python_contracts_and_runtime_invariants_01.md): Rule: Python Contracts & Runtime Invariants; Python Array Value Object Hash & Equality Discipline Invariant; Standard Library Monkeypatch Signature Parity Invariant; Python Subprocess Explicit Check Parameter Invariant; Runtime Invariant Checking Without Asserts Invariant; YAML Colon-in-String Quoting Discipline Invariant; Boolean Subclass Guard in Exact Numeric Contracts Invariant; Python Dataclass Replace Exception Typing Invariant; Complete Typed Answer Comparison.

## Retained typed-boundary evidence

```text
At an existing exact contract boundary, compare the complete typed answer and its
complete task binding, then snapshot nested result data.
```

## Stable invariant references

`RULE_PYTHON_BOOLEAN_SUBCLASS_GUARD_001`, `RULE_PYTHON_DATACLASS_REPLACE_EXCEPTION_TYPING_001`, `RULE_PYTHON_HASH_EQUALITY_NORMALIZATION_001`, `RULE_PYTHON_MONKEYPATCH_SIGNATURE_PARITY_001`, `RULE_PYTHON_NO_ASSERT_RUNTIME_CHECK_001`, `RULE_PYTHON_SUBPROCESS_CHECK_DISCIPLINE_001`, `RULE_PYTHON_YAML_COLON_QUOTING_001`.
