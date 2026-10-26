---
name: techne-code-soviet-builder
description: "Write Rust, Python and SQL unit, integration and e2e tests. State the invariant first; kill each test with a mutation."
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "unknown"
families: [techne-code, testing, clean-architecture, ddd, rop, falsification]
---

# Techne Code Soviet Builder

**Status:** `canonical`  
**AuthorityEffect:** `None` (You are the producer; the Inspector holds the veto)  

**Target:** `$ARGUMENTS` -- path, crate, package, tier, or a specific Inspector finding.

---

## 1. The Theoretical Minimum (gate on yourself)

Before writing a single line of a test you must state all four, in writing, in one sentence each.
If you cannot, you do not yet understand the code well enough to test it. Go read it.

```text
1. INVARIANT   What must always be true? State it as a proposition, not a feeling.
2. BREAK       Exactly how can it fail? Name the concrete wrong value or state.
3. WITNESS     What observable distinguishes held from broken? Name the assertion.
4. MUTATION    What one-line change to PRODUCTION code makes this test go red?
```

Item 4 is the whole discipline. **A test you cannot break on purpose is not a test.**

---

## 2. Clean Architecture, DDD & ROP Test Construction Invariants

### A. Railway-Oriented Programming (ROP) Test Discipline

- Every test on a use case or domain service MUST assert against the `Result[T, E]` monad:
  - Assert `res.is_ok()` and extract `res.value` for valid paths.
  - Assert `res.is_err()` and check the exact domain error type (`isinstance(res.error, ExpectedError)`) for negative paths.
  - Assert `res.is_refusal()` for security, boundary, or contract violations.
- Never write tests that catch bare uncaught exceptions from domain layers; business failures must be captured in the `Result` container.

### B. Exact-Type Value Object Equality Testing

- Author negative-control tests asserting that Value Objects reject comparisons across distinct types:

  ```python
  vo = DomainId("123")
  assert vo != "123"  # String coercion rejected
  assert vo != OtherId("123")  # Cross-type equality rejected
  ```

### C. Clean Architecture AST Boundary Testing

- Author automated architecture fitness functions using Python's `ast` module to assert inward dependency rules:

  ```python
  def test_domain_has_zero_outer_dependencies():
      # Parse all AST import nodes in domain/
      # Assert no imports from use_cases, infrastructure, controllers, or frameworks
  ```

---

## 3. The Landau Ranking

Report the class of every test you build. Counting tests as interchangeable is a lie.

```text
Class 1  Kills an entire family of bugs.
         Property/invariant over a generated domain; round-trip law;
         exactness or conservation identity; SQL constraint/isolation invariant
         that holds for any legal input; Clean Architecture AST fitness rule.

Class 2  Kills a whole failure mode.
         Negative-control matrix: tampered, expired, replayed, revoked,
         out-of-scope, wrong-kind, unique-violation, FK-violation, ROP Refusal.

Class 3  Pins one real behavior with an exact assertion, including the exact
         error variant on the failure path.

Class 4  Pins one concrete case with a golden fixture or known-good vector.

Class 5  Guards one specific past regression. Cite the defect it commemorates.

Class 0  Not a test. Constructs, prints, asserts a tautology, asserts on a
         reimplementation, asserts on a mock's call count. Delete it.
```

---

## 4. Construction Order (do not reorder)

1. **Read the production code that matters:** Never test unread code. Find the enforcement point, not the type.
2. **Confirm the subject exists outside your test file:** Never create self-referential tests.
3. **Write the negative control FIRST:** Author the breaking/rejection case before the happy path.
4. **Kill the test with a mutation:** Introduce a intentional fault in production code to verify the test fails for the exact right reason.
5. **Run in small isolated batches:** Always supply `--basetemp=scratch/pytest_tmp` on Windows (`RULE_PYTEST_WINDOWS_BASETEMP_001`).

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be pure UTF-8 without BOM and pass `npx markdownlint-cli` with **0 errors and 0 warnings**.
