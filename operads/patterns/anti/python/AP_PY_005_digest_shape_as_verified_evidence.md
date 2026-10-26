---
pattern_id: AP_PY_005
name: digest_shape_as_verified_evidence
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_005_authenticated_witness_payload_verification
language: python
authority_effect: None
---

# Anti-Pattern: Digest Shape as Verified Evidence (`AP_PY_005`)

## Description

Treating a syntactically valid hash string (e.g. 64-hex string matching `^[0-9a-f]{64}$`) as verified evidence without hashing the underlying witness payload bytes, or awarding passing fitness scores to empty mandatory outcome lists.

## Hazard & Failure Mode

- Fabricated receipts with random 64-hex strings earn credit as valid proofs.
- Empty outcome specifications evaluate to `TaskPass`.
- Untested code mutations enter the genealogy.

## Detection Signature

```python
# Anti-pattern:
if re.fullmatch(r"^[0-9a-f]{64}$", digest):
    # Awards fitness pass without checking if sha256(payload) == digest!
    return FitnessScore(pass_count=1)
```

## Dual Healthy Pattern

See [HP_PY_005_authenticated_witness_payload_verification](../../helpful/python/HP_PY_005_authenticated_witness_payload_verification.md).
