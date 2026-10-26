---
name: techne-run-tests
description: "Use to run project tests with coverage, check tests pass, or validate changes."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# Run Tests

## Example Session

**Rationale:** test_sovereign_observability.py found to silently pass without running.
**Pattern to detect:**

### Silent Skip Detection

## Constraints

**Family:** code-quality (see [family_registry.md](../_shared/family_registry.md))

## Related Skills

**Action Items:**
**Coverage Gaps:**
**Failed Tests:**
**Results:**

## Example Session (2)

**Source:** Anomalon.com MVP deployment session (convo.md) -- 4 serial Vercel failures before green deploy
**Emergency triage pipeline** (when Vercel deploys fail in sequence):

## Vercel / Next.js Pre-Deploy Checklist (Anomalon.com MVP Learning)

**Source:** Sprint 058 Copilot PR review feedback (weak assertions in test_news_migration.py)
**Red Flags to Check:**
**Required for Migration Tests:**
**Forbidden Patterns (auto-fail):**

## Test Quality Gates (MANDATORY)

## Quality Gates

## Reporting

**Source:** Copilot AI feedback 2026-01-30 on test_news_migration.py
**Guidelines:**

### Test Documentation Accuracy (Sprint 071-0 Learning)

**Source:** QUIP implementation session 2026-02-20

### PyO3 with Python 3.14+ (omega_engine)

### Rust Build Resource Constraints (MANDATORY)

**Recommended**: Use Task tool with test-runner subagent for cross-platform reliability:

### Running Tests on Windows

**Source:** Sprint 085 - `test_news_pipeline_integration.py` had class-level decorator with sync methods
**Rules:**
**Common gotcha:** Class-level `@pytest.mark.asyncio` does NOT make sync functions async.
**Project configuration** (pyproject.toml):

### Async Test Marking: pytest.mark.asyncio (Sprint 085 Learning)

**CognitiveWarfareService test patterns:**
**Why**: When a function is imported inside a method body, it's not bound to the consumer module's namespace at import time. The mock decorator can't find it there because it doesn't exist until the method runs.
**Decision tree for patch paths:**

### Patch Path Selection for Service Layer Tests (Sprint 056 Learning)

**Source:** Sprint 085 - `test_hook_registry.py` module-level mocking caused cross-test contamination
**Key principle:** Any modification to `sys.modules` must be:
**CORRECT Pattern - Use fixtures or context managers:**
**Why this is dangerous:**
**NEVER** assign to `sys.modules` at module level in test files. This pollutes the module cache for ALL tests in the suite, not just the current test file.

### Testing Anti-Patterns: Module-Level sys.modules Pollution (Sprint 085 Learning)

**Why**: MagicMock auto-generates attributes including `pytest_plugins`. Pytest tries to interpret this as a plugin configuration, causing: `pytest.UsageError: Plugins may be specified as a sequence... Got: <MagicMock>`

### Mocking Modules for Pytest (Sprint 046 Learning)

**Why**: Windows defaults to `cp1252` encoding. Explicit `encoding="utf-8"` ensures consistent behavior across platforms and prevents `'utf-8' codec can't decode` errors in CI.

### Cross-Platform Test Fixtures (Sprint 040 Learning)

## Best Practices

## Frontend Tests (if applicable)

## Python Tests (pytest)

## When to Activate

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).

## Entry: goo-coverage-is-unmeasurable-here-use-mutation (session 2026-08-04 HIGH)

**This skill's own description says "with coverage reporting". In this repository,
on this interpreter, coverage cannot be collected at all.** Do not promise a
coverage number; do not report one you did not measure.

Verified 2026-08-04 -- Python 3.14.2, numpy 2.4.2, pytest 9.0.2, pytest-cov 7.0.0,
coverage 7.13.1:

| Command | Result |
| --- | --- |
| `python -m pytest <any test> --cov=<mod>` | dies during **collection**: `ImportError: cannot load module more than once per process` (raised from `numpy/_core/multiarray.py`) |
| `python -m coverage run -m pytest ...` | runs, but collects nothing: `No data was collected`, modules reported "never imported" |

It reproduces on **untouched** files (`omega_epk/tests/test_defects.py`,
`omega_epk/tests/test_metrics_identity.py`), so it is an environment/tooling
incompatibility, never evidence about the code under test. Always demonstrate that
before blaming a change.

### Use mutation testing instead

Coverage is only a proxy for *"do the tests actually bite?"*. Get that property
directly:

1. Back up the file under test.
2. Break exactly one gate (invert a predicate, force a branch, `return true`).
3. Run the suite. Record **which** tests fail and confirm they are the ones that
   *should*.
4. Restore, then `grep -c` your mutation marker to prove 0 residue, and re-run to
   confirm green.

A test that has never failed has not been shown to test anything. Report the
mutation table -- target, failures, assessment -- in place of a coverage percentage.

Session witness 2026-08-04: 4 mutations across Rust and Python; each failed exactly
the intended tests (3/3/2/4). The strongest result was a mutation that broke a
cross-rail agreement check, proving it detected a real contract divergence rather
than merely executing. Coverage was reported as `DECLARED_UNVERIFIED`, never as a
number.
