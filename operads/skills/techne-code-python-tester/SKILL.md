---
name: techne-code-python-tester
description: "Design and run falsifying Python tests; reject tautological, empty and sys.path-hacked tests."

operad_source_colours: ["Code"]
operad_target_colour: "Receipt"
operad_arity: 1
operad_residual: "unknown"
---

# Python Tester

## Activate when

Writing, reviewing, or executing Python tests — especially validators, receipts,
routing, authority, canonicalization, mathematical adapters, and any change that
claims test coverage.

## Test law

A useful test distinguishes at least one valid case from one invalid case.  
A test that cannot fail after a plausible semantic mutation is execution theater.  
Passing the mechanical quality gate means only that the scanned tests avoid the
encoded anti-patterns; it does **not** certify behavioral adequacy.

**AuthorityEffect: None.**

## Procedure

1. Resolve and record the actual interpreter (`sys.executable`) and pytest version.
2. Run collection before interpreting any failure as a product defect.
3. Run the deterministic quality gate on every changed or new test file:

   ```text
   <configured-python> omega_engine_operads/skills/techne-code-python-tester/scripts/test_quality_gate.py <test-paths>
   ```

   Exit 1 = findings present. Treat findings as **Critical** mechanical defects.
4. Require the shape of a real test (align with Soviet Builder):
   - state the invariant under test (even if only in a comment or receipt);
   - include at least one negative / refusal / malformed / boundary case;
   - assert exact observable state or error, not mere non-exception.
5. Run focused tests first, then the smallest relevant integration surface.
   Preserve raw command and exit status for every run.
6. Measure coverage only with an installed coverage tool. Statement coverage is
   not semantic coverage; for critical gates add a controlled mutation or dual-
   implementation check.
7. Emit a structured receipt (see Residual). Report each gate separately as
   `PASS`, `FAIL`, `BLOCKED_AT_COLLECTION`, or `UNAVAILABLE`.

## Mechanical quality gate (what it catches today)

| Code | Pattern |
|---|---|
| `WEAK_ASSERTION` | `assert True`, `assert ... or True` |
| `EMPTY_TEST` | `test_*` body that is empty or only `pass` / docstring |
| `TAUTOLOGY_EQ` | `assert 1 == 1`, `assert 0 == 0`, literal == literal |
| `WEAK_LEN` | `assert len(...) >= 0`, `assert len(...) > -1` |
| `SYS_PATH_HACK` | `sys.path.insert` / `sys.path.append` inside a test module |
| `BARE_RAISES` | `pytest.raises(Exception)` (or bare base Exception) without `match=` |
| `NO_ASSERTION` | `test_*` function whose body contains no `Assert` and no `pytest.raises` |

New codes require new meta-tests in `test_test_quality_gate.py` **before** the
gate rule is considered live. The gate must be able to fail its own tests.

## Prohibited evidence (still true)

- `assert True`, constant tautologies, empty tests, import-only tests;
- caller-authored audit or certificate booleans;
- counts remembered by a model;
- a mock-only safety or authority result offered as final evidence;
- claiming full-suite or coverage success after only a focused run;
- `sys.path` mutation as a substitute for proper package installation / editable install.

## PYTHONPATH Isolation Guard

Prevent standard-library module shadowing (classic failure: a local `code/` package
shadowing Python’s `code` module).

1. Prefer an explicit, minimal `PYTHONPATH` that contains only the packages under test
   and never a directory whose top-level name collides with a stdlib module.
2. Prefer `python -m pytest` from a properly installed / editable environment over
   ad-hoc path surgery.
3. Concrete monorepo paths belong in a project profile, not in the universal rule.

## Residual — PythonTestReceipt

Every run must leave a machine-readable receipt:

```json
{
  "schema": "omega.python_test_receipt.v1",
  "interpreter": "<sys.executable>",
  "pytest_version": "...",
  "collection": {"status": "PASS|FAIL|BLOCKED", "command": "...", "exit": 0},
  "quality_gate": {
    "status": "PASS|FAIL",
    "files_scanned": N,
    "findings": [{"path": "...", "line": N, "code": "...", "detail": "..."}]
  },
  "focused_run": {"command": "...", "exit": 0, "summary": "..."},
  "coverage": {"status": "PASS|FAIL|UNAVAILABLE", "tool": "..."},
  "mutation_check": {"status": "PERFORMED|NOT_PERFORMED", "detail": "..."},
  "authority_effect": "None"
}
```

## Relationship to the Soviet pair

- **Soviet Inspector** — semantic / tier / SQL / safety / obstruction judge. Issues VETO.
- **Soviet Builder** — Landau author. Constructs tests under Theoretical Minimum + mutation kill.
- **This skill** — Python execution specialist + mechanical pre-filter + receipt producer.

Do not duplicate the Inspector’s semantic vetoes here. Feed gate findings and raw
evidence to the Inspector; do not claim to replace it.

## Final rule

```text
Passing the mechanical gate is necessary and not sufficient.
A test that cannot fail after a semantic mutation is theater.
Record the interpreter, the commands, the exits, and the findings.
AuthorityEffect: None.
```

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
