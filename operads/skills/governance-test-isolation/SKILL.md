---
name: governance-test-isolation
description: "Gate for test discipline, Windows basetemp isolation, scoped test tree layout and shadow scans."
operad_source_colours: ["Code", "State"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: neutral
families: [governance, testing]
---

# governance-test-isolation

AuthorityEffect: None.

## The single rule

> Test suites must use targeted execution without unbounded sweeps, isolate basetemp directories on Windows, excise sys.path hacks, and protect test entry points with immutable family snapshotting.

## Consolidated Invariants

1. **Four Rules of Test Hygiene**: Excising `sys.path` hacks, decoupling unit tests via synthetic mocks, isolating disk I/O in tempdir fixtures, and granular assertions over lazy dumps (`goo-test-hygiene-four-rules-gate`).
2. **Execution Discipline & Windows Isolation**: Enforce single-file or targeted pytest invocations over unbounded sweeps, and require `--basetemp=scratch/pytest_tmp` on Windows (`goo-strict-test-execution-discipline-enforcer`, `goo-pytest-windows-basetemp-isolation-enforcer`).
3. **Scoped Test Harness Layout**: Tests must live in scoped subdirectories (`tests/<bounded_context>/`), eliminating orphan files from `tests/` root (`goo-scoped-test-harness-synchronizer`).
4. **Package Isolation & Shadow Scanning**: Sub-package `pyproject.toml` files must declare local code paths, and names must not shadow standard library modules (`goo-package-local-pythonpath-isolation-gate`, `goo-module-shadow-scan-required-gate`).
5. **Entrypoint Immutability & Gate Executability**: Test families must be snapshotted as immutable tuples at public evaluation entry points, and gate packages must ship runnable check scripts (`goo-callback-immutable-family-snapshot-guard`, `goo-gate-executability-requirement`).
6. **Cross-Package Test Basename Collision Prevention**: When copying or replicating test suites across different towers or packages in the monorepo (e.g. `coda_all_universe/1_the_tower/*`), test module filenames must be uniquely prefixed or disambiguated with the tower/domain context (e.g. `test_fsp_cdt_*.py` vs `test_cdt_*.py`). Because pytest registers modules by basename in non-package directories, identical basenames across multiple directories trigger fatal `import file mismatch` errors during multi-directory or parallel test runs (`pytest -n 8`).
7. **Self-Contained Bounded-Context Asset Co-location**: Replicated evaluators and test harnesses that resolve relative filesystem artifacts (e.g. `databases/*.sql` or `lean4/*.lean`) must have local instances or explicit local schemas co-located within the destination bounded context. This prevents fragile cross-tower dependencies and guarantees that each tower is self-contained and independently testable.
8. **Parallel Multi-Worker Collection Protection (`--dist=loadfile`)**: When executing multi-worker test suites (`pytest -n 8`) across directories importing heavy mathematical/scientific dependencies (e.g. `scipy`, `numpy`, `sympy`), simultaneous file collection across parallel workers on Windows can cause path resolution memory exhaustion (`MemoryError`) or worker collection discrepancies. Use `--dist=loadfile` with external `--basetemp` to group tests by file during distribution, avoiding worker collection contention while maintaining 8-CPU execution parallelism.
9. **Declarative Normal Form YAML Contract Syntax Hygiene**: Mathematical conditions and predicates containing single or double vertical bars (e.g. absolute values `|x|`, determinants `|det(M)|`, or norms `||A - B||`) in declarative YAML contracts (`nf.*.yaml`) must be wrapped in explicit double quotes (`"|...| <= tol"`). An unquoted leading `|` triggers PyYAML `ScannerError` by falsely parsing as a multiline block scalar indicator.
10. **SQL Audit View Verdict String Bijection**: The verdict strings emitted by relational audit views (`ViewCdt*Audit`) in `regge_wdw_schema.sql` via `CASE WHEN ... THEN 'VERDICT'` must maintain strict 1:1 bijective correspondence with the contract terminal routes declared in `nf.*.yaml` and the pytest assertion literals.
11. **Native Rust Engine Tests Exclusivity (`RULE_TESTS_RUST_EXCLUSIVE_001`)**: `engine/tests` is strictly dedicated to native Rust tests and fixtures. It is strictly forbidden to create or locate Python test files, fixtures, or module packages (`test_*.py`, `__init__.py`, `conftest.py`) in `engine/tests`. All Python test suites across the repository reside in their respective operational contexts (e.g., `operations/tests/`, `research/papers/.../code/tests/`, `bench/.../tests/`).
12. **Windows Python 3.12 Pinning & Subprocess Interpreter Resolution (`py -3.12`)**: On Windows development workstations where ambient `python` defaults to Python 3.14 without binary wheels or Visual Studio Python 3.9 without installed packages, all test runners, compiler scripts, and review swarms must explicitly invoke `py -3.12` (or use `sys.executable` in active virtual environments). Subprocess runners must never invoke raw `python` without verifying interpreter path and dependencies, preventing false execution failures.

## Verification Requirements

Run the test environment isolation checker:

```bash
python operads/skills/governance-test-isolation/scripts/check_test_isolation.py
```

## Large fixtures and historical accounting

Give large or adversarial parametrized inputs short explicit pytest IDs. Keep the
raw fixture and assertions intact: on Windows a huge node ID can overflow
`PYTEST_CURRENT_TEST` environment metadata before a product assertion runs.
Distinguish setup failures from assertion failures before changing production code.

Use module-qualified node IDs when accounting for combined suites. For old JUnit
output with missing class names or overlapping test names, inspect its exact
command and validate the contextual partition; never guess source attribution.

[Hodge's retained fixture and retry](../../../_ic/nara/historical/oewas007/research/briefs/pfp_migration/hodge_companion_candidate/README.md)
and [Pilot 22 accounting correction](../../../_ic/nara/historical/oewas007/research/briefs/pfp_expansion/pilot22_typed_engine/bind_extraction.py)
supply the motivating cases. Reading them does not rerun their tests.
