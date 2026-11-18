---
name: techne-code-normal-forms-tester
description: "Write falsifying tests for normal forms. Counterexamples for 2NF to 5NF, lossy decomposition traps, CDC perturbations."
operad_source_colours: ["Code"]
operad_target_colour: "Receipt"
operad_arity: 1
operad_residual: "unknown"
families: [testing, normal-forms, relational-algebra, techne, quality]
---

# Normal Forms Tester (`techne-code-normal-forms-tester`)

> *"A normal form verifier that has never rejected a malformed relation is not a verifier; it is an illusion. Construct the counterexample, perturb the timestamp, and observe the defect."*\
> — Techne Code Testing Invariant

**AuthorityEffect:** `None` (Emits property-based test suites, adversarial counterexample fixtures, CDC perturbation generators, and evaluation test receipts).  
**Lead Governance Council:** `L3_logos_techne` (Quality Engineering & Test Rigor) with secondary seat at `L3_logos_thanatos` (Adversarial Falsification).  
**Cross-Host Alias:** `normal-forms-tester`.

---

## 1. Testing Mandate & Scope

The `techne-code-normal-forms-tester` designs, executes, and validates tests that probe normal form evaluators, decomposition routines, and operational contracts. Responsibilities include:

1. **Relational Counterexample Synthesis:**
   - Construct minimal relation instances that violate specific normal forms while satisfying weaker ones (e.g. 2NF but not 3NF, 3NF but not BCNF, BCNF but not 4NF).
   - Generate lossy decomposition instances demonstrating the generation of spurious tuples when Heath's Theorem conditions fail.
   - Test dependency preservation: verify whether decomposed schemas allow enforcing all original functional dependencies locally.

2. **Adversarial CDC & Change-Stream Perturbation:**
   - Inject out-of-order event arrivals, duplicate mutation keys, timestamp jitter, and concurrent updates to stress BQNF deduplication.
   - Verify observer-relative freshness and watermarking against replay anomalies.

3. **Mechanical Test Quality Gate Compliance:**
   - Enforce collection before interpretation.
   - Eliminate test anti-patterns (`WEAK_ASSERTION`, `TAUTOLOGY_EQ`, `BARE_RAISES`, `SYS_PATH_HACK`).
   - Ensure every test asserts observable state or typed domain errors rather than non-exception exit.

---

## 2. Canonical Counterexample Generation Patterns

### 1. The 3NF vs. BCNF Boundary Counterexample

A classic schema satisfying 3NF but violating BCNF:

$$R(\text{Student}, \text{Course}, \text{Instructor}), \quad F = \{ \{\text{Student}, \text{Course}\} \to \text{Instructor}, \quad \text{Instructor} \to \text{Course} \}$$

- **Candidate Keys:** $\{\text{Student}, \text{Course}\}$, $\{\text{Student}, \text{Instructor}\}$.
- **3NF Check:** In $\text{Instructor} \to \text{Course}$, $\text{Course}$ is prime (part of candidate key $\{\text{Student}, \text{Course}\}$). Thus, $R \in \text{3NF}$.
- **BCNF Check:** $\text{Instructor}$ is not a superkey. Thus, $R \notin \text{BCNF}$.
- **Adversarial Fixture:** Test must verify that the BCNF evaluator flags $\text{Instructor} \to \text{Course}$ as a defect while the 3NF evaluator passes it.

### 2. Lossy Join Spurious Tuple Generator

To falsify incorrect decompositions, generate an instance where natural join yields spurious tuples:

```python
def make_lossy_decomposition_fixture() -> dict[str, Any]:
    """Instance where R(A, B, C) decomposed into R1(A, B) and R2(B, C) is lossy.

    F = {A -> B} (B does not determine C, nor does B determine A).
    """
    instance = [
        {"A": "a1", "B": "b1", "C": "c1"},
        {"A": "a2", "B": "b1", "C": "c2"},
    ]
    # Projected:
    # R1 = {(a1, b1), (a2, b1)}
    # R2 = {(b1, c1), (b1, c2)}
    # Natural join R1 |><| R2 produces 4 tuples:
    # {(a1, b1, c1), (a1, b1, c2) [SPURIOUS], (a2, b1, c1) [SPURIOUS], (a2, b1, c2)}
    return {"instance": instance, "spurious_count": 2}
```

---

## 3. Test Invariants & Quality Checklist

Every test file created or audited by `techne-code-normal-forms-tester` must satisfy:

| Invariant | Requirement |
| :--- | :--- |
| **Deterministic Execution** | Zero flaky tests; all random generators seeded deterministically. |
| **Boundary Coverage** | Every normal form gate must test: (1) valid instance, (2) near-miss invalid instance, (3) empty relation, (4) single-tuple relation. |
| **Specific Error Matching** | Negative tests must check `pytest.raises(SpecificDomainError, match="...")`. Bare exceptions are rejected. |
| **Exact Rational Arithmetic** | Any numerical, metric, or defect score must use `fractions.Fraction` or exact integer counts. Float comparisons are prohibited. |
| **No Whole-Suite Sweeps** | Execute only targeted test modules (e.g. `python -m pytest tests/test_normal_forms.py`). |
