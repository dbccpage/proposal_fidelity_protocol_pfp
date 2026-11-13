---
pattern_id: HP_PY_005
name: authenticated_witness_payload_verification
category: helpful_pattern
operad_type: Isomorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "exact"
dual_pattern: AP_PY_005_digest_shape_as_verified_evidence
language: python
authority_effect: None
---

# Helpful Pattern: Authenticated Witness Payload Verification (`HP_PY_005`)

## Description

Computing cryptographic digests directly from raw witness payload bytes, verifying that declared digests match computed hashes, and evaluating empty mandatory test lists as `NotMeasured` rather than `TaskPass`.

## Implementation Pattern

```python
# Authenticate payload:
computed_digest = hashlib.sha256(raw_bytes).hexdigest()
if computed_digest != declared_digest:
    return WitnessRejection("DIGEST_MISMATCH")

# Reject empty test specifications:
if not mandatory_outcomes:
    return OutcomeStatus.NOT_MEASURED
```

## Guarantees Under Declared Assumptions

- Synthesizers cannot forge evidence using arbitrary hex strings.
- Empty test configurations cannot counterfeit pass receipts.
