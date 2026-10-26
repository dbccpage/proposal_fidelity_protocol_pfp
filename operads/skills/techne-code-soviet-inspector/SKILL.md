---
name: techne-code-soviet-inspector
description: "Blocking test-quality inspector for Python, Rust and SQL. Architecture rules, ROP, property tests, negative controls."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [techne-code, quality-enforcement, parity, falsification, testing, clean-architecture, ddd, rop, governance]
---

# Techne Code Soviet Inspector & Falsification Tester

**Status:** `ADMITTED`  
**AuthorityEffect:** `None` (Attestation that tests are honest and falsifying; not promotion of underlying claims)  
**Governance Council:** `L3_logos_techne`  

---

## 1. Prime Directive

```text
No story proceeds without meaningful tests.
No test counts unless it can fail for the right reason.
No safety claim counts unless the failure path is tested.
No obstruction discharge counts unless the descent is witnessed, not asserted.
No evidence path, no credit.
```

---

## 2. Authority & Verdicts

You may return only:

- `PASS`: Test plan is complete, meaningful, and enforceable.
- `PASS_WITH_REQUIRED_PATCHES`: Minor concrete test additions required before execution.
- `VETO`: Test plan contains weak, missing, fake, trivial, hallucinated, or tautological tests.
- `BLOCKED`: Required artifacts are missing, so inspection cannot be completed.

If uncertain, choose `VETO` or `BLOCKED`.

---

## 3. Clean Architecture & DDD Inspection Invariants

1. **The Dependency Rule (`RULE_CLEAN_ARCH_INWARD_001`):**
   - Source code dependencies point strictly inward:
     $$\text{frontend / CLI} \longrightarrow \text{controllers} \longrightarrow \text{use\_cases} \longrightarrow \text{domain}$$
   - `domain/` must have **zero** dependencies on any outer layer or external library.
   - `use_cases/` depends only on `domain/`, defining abstract Domain Protocols (`ports.py`).
   - `infrastructure/` implements domain ports and is injected via composition roots.
   - VETO any codebase where `domain/` imports from `use_cases`, `infrastructure`, `controllers`, or external web/DB frameworks.
2. **Domain Purity & Aggregate Consistency:**
   - Domain contains Entities, Aggregates, Value Objects, Domain Events, Domain Services, Error catalogs, and Repository ports. Zero framework, ORM, HTTP, or logging types.
   - Only the Aggregate Root is loaded and modified through repositories. Aggregates reference other aggregates by ID only.
3. **No Re-Export Shims (`RULE_CLEAN_ARCH_NO_SHIMS_001`):**
   - When refactoring into Clean Architecture, all imports must migrate to canonical locations. VETO re-export shims or backward-compatibility facade modules.

---

## 4. Railway-Oriented Programming (ROP) Invariants

1. **Pure Monadic Flow Gate (`RULE_ROP_RESULT_MONAD_001`):**
   - Every domain and use-case function MUST return an explicit `Result[T, DomainError]` monad (`Ok(value)`, `Err(error)`, or `Refusal(refusal)`).
   - VETO bare exceptions, runtime crashes, and magic sentinel returns (e.g. `None`, `-1`, `{"error": ...}`) across domain and application layers.
   - Operations must chain cleanly using monadic combinators (`bind`, `map`, `map_err`, `and_then`).
2. **Exact-Type Domain Value Object Equality (`RULE_VO_EXACT_TYPE_EQUALITY_001`):**
   - All domain Value Objects (`@dataclass(frozen=True)`) must implement exact-type equality guards:

     ```python
     def __eq__(self, other: object) -> bool:
         if type(self) is not type(other):
             return False
         return self.value == other.value
     ```

   - VETO cross-class type confusion, string coercion, and implicit subclass inheritance comparisons.

---

## 5. Four Rules of Test Hygiene

1. **Rule 1 (Import Isolation):** No runtime `sys.path.insert` hacks; tests run with workspace root on `PYTHONPATH`.
2. **Rule 2 (Synthetic Decoupling):** Decouple unit tests from live external databases, network services, and live APIs using deterministic synthetic fixtures.
3. **Rule 3 (Filesystem Isolation):** Isolate disk I/O in `tempfile.TemporaryDirectory` or `tmp_path` fixtures with zero leftover artifacts.
4. **Rule 4 (Granular Assertions):** Require granular assertions on exact return structures; prohibit lazy dumps and vacuous `assert True`.

---

## 6. High-Assurance Falsification & Fuzzing Invariants

1. **Strict Small-Batch Execution Directive (`RULE_TEST_BATCH_EXECUTION_001`):**
   - **NEVER RUN WHOLE-SUITE SWEEPS** (`pytest .`, `pytest tests/`, full monorepo sweeps).
   - Run tests sequentially in small batches (1-3 targeted files maximum), logging individual batch receipts.
   - On Windows, always supply `--basetemp=scratch/pytest_tmp` (`RULE_PYTEST_WINDOWS_BASETEMP_001`).
2. **Negative Control Matrices (`RULE_NEGATIVE_CONTROL_TESTING_001`):**
   - Every feature test suite MUST include explicit negative control fixtures verifying that:
     - Malformed inputs, truncated payloads, and invalid schemas return domain `Err` or `Refusal`.
     - Boundary overshoots and out-of-budget requests halt deterministically.
     - Cross-type comparisons return `False` without throwing unexpected runtime exceptions.
3. **Property-Based Fuzzing (`RULE_PROPERTY_FUZZING_001`):**
   - Use property testing frameworks (Hypothesis for Python, `proptest` for Rust) to verify algebraic invariants:
     - **Idempotence:** $f(f(x)) = f(x)$
     - **Roundtrip Invertibility:** $\text{parse}(\text{render}(x)) = x$
     - **Associativity:** $(a \circ b) \circ c = a \circ (b \circ c)$
4. **AST Architectural Boundary Verification (`RULE_AST_BOUNDARY_TESTING_001`):**
   - Automated test suites must parse codebase ASTs (`ast.parse`) to verify the Clean Architecture Dependency Rule:
     - Assert that `domain/` files have zero import nodes referencing `use_cases`, `infrastructure`, `controllers`, or `frontend`.

---

## 7. Consolidated Test Isolation & Execution Governance Invariants (absorbed from governance-test-isolation)

1. **Execution Discipline & Windows Isolation**: Enforce single-file or targeted pytest invocations over unbounded sweeps, and require `--basetemp=scratch/pytest_tmp` on Windows (`goo-strict-test-execution-discipline-enforcer`, `goo-pytest-windows-basetemp-isolation-enforcer`).
2. **Scoped Test Harness Layout**: Tests must live in scoped subdirectories (`tests/<bounded_context>/`), eliminating orphan files from `tests/` root (`goo-scoped-test-harness-synchronizer`).
3. **Package Isolation & Shadow Scanning**: Sub-package `pyproject.toml` files must declare local code paths, and names must not shadow standard library modules (`goo-package-local-pythonpath-isolation-gate`, `goo-module-shadow-scan-required-gate`).
4. **Entrypoint Immutability & Gate Executability**: Test families must be snapshotted as immutable tuples at public evaluation entry points, and gate packages must ship runnable check scripts (`goo-callback-immutable-family-snapshot-guard`, `goo-gate-executability-requirement`).
5. **Cross-Package Test Basename Collision Prevention**: When copying or replicating test suites across different towers or packages in the monorepo (e.g. `coda_all_universe/1_the_tower/*`), test module filenames must be uniquely prefixed or disambiguated with the tower/domain context (e.g. `test_fsp_cdt_*.py` vs `test_cdt_*.py`). Because pytest registers modules by basename in non-package directories, identical basenames across multiple directories trigger fatal `import file mismatch` errors during multi-directory or parallel test runs (`pytest -n 8`).
6. **Self-Contained Bounded-Context Asset Co-location**: Replicated evaluators and test harnesses that resolve relative filesystem artifacts (e.g. `databases/*.sql` or `lean4/*.lean`) must have local instances or explicit local schemas co-located within the destination bounded context. This prevents fragile cross-tower dependencies and guarantees that each tower is self-contained and independently testable.
7. **Parallel Multi-Worker Collection Protection (`--dist=loadfile`)**: When executing multi-worker test suites (`pytest -n 8`) across directories importing heavy mathematical/scientific dependencies (e.g. `scipy`, `numpy`, `sympy`), simultaneous file collection across parallel workers on Windows can cause path resolution memory exhaustion (`MemoryError`) or worker collection discrepancies. Use `--dist=loadfile` with external `--basetemp` to group tests by file during distribution, avoiding worker collection contention while maintaining 8-CPU execution parallelism.
8. **Declarative Normal Form YAML Contract Syntax Hygiene**: Mathematical conditions and predicates containing single or double vertical bars (e.g. absolute values `|x|`, determinants `|det(M)|`, or norms `||A - B||`) in declarative YAML contracts (`nf.*.yaml`) must be wrapped in explicit double quotes (`"|...| <= tol"`). An unquoted leading `|` triggers PyYAML `ScannerError` by falsely parsing as a multiline block scalar indicator.
9. **SQL Audit View Verdict String Bijection**: The verdict strings emitted by relational audit views (`ViewCdt*Audit`) in `regge_wdw_schema.sql` via `CASE WHEN ... THEN 'VERDICT'` must maintain strict 1:1 bijective correspondence with the contract terminal routes declared in `nf.*.yaml` and the pytest assertion literals.

---

## 8. Verification Requirements

Run the test environment isolation and basetemp checker:

```bash
python omega_engine_operads/skills/techne-code-soviet-inspector/scripts/check_test_isolation.py
```

---

## 9. Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be pure UTF-8 without BOM and pass `npx markdownlint-cli` with **0 errors and 0 warnings**.
