---
pattern_id: HP_PY_018
name: examiner_mutation_sensitivity_protocol
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_019_tautological_and_self_certifying_test_slop
language: python
authority_effect: None
---

# Healthy Pattern: Examiner Mutation Sensitivity Protocol (`HP_PY_018`)

## Description

Every newly authored or updated test suite must be verified against at least one deliberate property-breaking mutation of the code under test (adversarial falsification). If the test suite passes on a broken mutant, the test is rejected as insensitive or tautological.

## Implementation Pattern

```python
def test_verifier_sensitivity():
    # 1. Normal run passes on valid candidate
    result = verify_candidate(valid_candidate)
    assert result.is_pass()

    # 2. Deliberate mutant breaks the invariant
    mutated_candidate = make_mutant(valid_candidate, inject_defect=True)
    mutated_result = verify_candidate(mutated_candidate)
    
    # 3. Assert test suite detects the mutant and refuses
    assert mutated_result.is_refusal()
    assert mutated_result.refusal_code == "INVARIANT_DEFECT"
```

## Resolution

- Eliminates tautological assertions and self-certifying dummy tests.
- Verifies that test suites actively constrain the implementation space.
