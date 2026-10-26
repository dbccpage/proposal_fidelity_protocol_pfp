---
pattern_id: AP_PY_019
name: tautological_and_self_certifying_test_slop
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_018_landau_mutation_sensitivity_protocol
language: python
authority_effect: None
---

# Anti-Pattern: Tautological and Self-Certifying Test Slop (`AP_PY_019`)

## Description

Tests that assert mathematical or boolean tautologies without exercising production code, or manually raise exceptions inside `pytest.raises` blocks to artificially inflate test counts.

## Detection Signature

- AST Patterns:
  ```python
  # BAD: Literal tautologies that never fail
  assert 10 <= 32
  assert 1050 > 1000 is True
  assert Fraction(0, 1) == Fraction(0, 1)
  assert 2 % 2 == 0

  # BAD: Manually raising an exception inside pytest.raises without calling code under test
  with pytest.raises(ValueError):
      raise ValueError("forced error")
  ```
- Good Pattern:
  ```python
  # GOOD: Exercise actual domain logic and verify against specific property bounds
  with pytest.raises(RefusalRecord) as excinfo:
      parse_packet(invalid_input)
  assert excinfo.value.code == "BAD_STEP"
  ```

## Hazard & Failure Mode

- Inflates test counts without testing behavior.
- Fails to detect real regressions when implementation contracts are broken.

## Prevention & Resolution

Apply the Lev Landau mutation protocol: test suites must be evaluated against deliberate property-breaking mutations. An AST linter must reject literal comparisons in test assertions.
