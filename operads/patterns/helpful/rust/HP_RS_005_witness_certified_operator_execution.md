---
pattern_id: HP_RS_005
name: witness_certified_operator_execution
category: helpful_pattern
operad_type: Isomorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "exact"
dual_pattern: AP_RS_005_theatrical_zero_mass_character_operators
language: rust
authority_effect: None
---

# Helpful Pattern: Witness-Certified Operator Execution (`HP_RS_005`)

## Description

Binding every character operator and evaluation gate to concrete subprocess execution or cryptographic witness checks, verifying return codes, checking stdout/stderr logs for expected proof invariants, and asserting non-negative rational residual mass.

## Implementation Pattern

```python
# Operator invokes real compiler and checks actual sorry count:
lake_proc = subprocess.run(["lake", "build"], cwd=lean_dir, capture_output=True, text=True)
sorry_count = len(re.findall(r"\bsorry\b", lake_proc.stdout))
if lake_proc.returncode != 0 or sorry_count > 0:
    return DefectRecord(defect_id="LEAN_SORRY_DETECTED", mass=Fraction(1, 1))
```

## Guarantees Under Declared Assumptions

- Verification verdicts are supported by reproducible subprocess receipts.
- Eliminates theatrical declarations of formal correctness.
