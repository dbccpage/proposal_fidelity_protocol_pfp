---
pattern_id: HP_PY_008
name: ascii_canonical_digest
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_008_canonical_digest_ascii_drift
language: python
authority_effect: None
---

# Healthy Pattern: ASCII Canonical Digest (`HP_PY_008`)

## Description

Every digest on a shared seam uses one canonical JSON profile: sorted keys, compact separators, `ensure_ascii=True`, and ASCII bytes. Rust uses the same profile.

## Structural Signature

```python
def canonical_digest(payload: dict) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(raw.encode("ascii")).hexdigest()
```

## Remediation Applied

- Replace `ensure_ascii=False` on digest paths with `ensure_ascii=True`.
- Add a fixture that hashes one payload in Python and Rust and compares the digests.
