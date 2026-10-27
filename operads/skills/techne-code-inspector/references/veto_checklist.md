# Inspector Hard Veto Checklist

The Inspector returns `VETO` or `BLOCKED` upon encountering any of the following conditions:

---

## 1. Test Quality & Ornament Vetoes

1. **Class 0 Ornament Veto:**
   - Tests that assert trivial tautologies (`assert True`, `assert x == x`).
   - Tests asserting on mock call counts or mock returns rather than actual domain behavior.
   - Tests that cannot fail when the production code is mutated.

2. **Silent Skip Veto (`RULE_TEST_SILENT_SKIP_VETO_001`):**
   - Tests containing `pytest.skip()` on repository fixtures.
   - Bare `return` statements on missing environment configurations.
   - Catch-all `except Exception: pass` blocks masking real failures.

3. **Self-Referential Target Veto:**
   - Tests asserting against helper structs or mock classes defined exclusively inside the test file rather than against production modules.

---

## 2. Execution & Batch Discipline Vetoes

1. **Unbounded Suite Sweep Veto (`RULE_TEST_BATCH_EXECUTION_001`):**
   - Attempting whole-suite sweeps (`pytest .`, `pytest tests/`, concurrent multi-crate sweeps).
   - Local execution must proceed in small batches (1-3 targeted test files).

2. **Filesystem & Leakage Veto:**
   - Tests leaving unmanaged temporary files or mutating shared staging databases without clean `try...finally` teardown.

3. **AST Layer Boundary Veto (`RULE_AST_BOUNDARY_TESTING_001`):**
   - `domain/` files importing from `use_cases/`, `infrastructure/`, `controllers/`, or `frontend/`.

---

## 3. Architecture & State Invariant Vetoes

1. **Value Object Exact-Type Equality Veto (`RULE_VO_EXACT_TYPE_EQUALITY_001`):**
   - `@dataclass(frozen=True)` value objects in domain models lacking an explicit `__eq__` exact-type guard (`if type(self) is not type(other): return False`), allowing implicit cross-type equality or subclass confusion.

2. **Replay State Accumulator Parity Veto (`RULE_REPLAY_STATE_PARITY_001`):**
   - Live multi-stage execution pipelines failing to record intermediate stage outcomes or host checks into runtime state accumulators (`prior`) identically to how replay reconstructors deserialize them from persistent storage, causing downstream prompt reconstruction hash divergence (`PROMPT_RECONSTRUCTION_CHANGED`).

