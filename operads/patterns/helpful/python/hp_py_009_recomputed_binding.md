---
pattern_id: HP_PY_009
name: recomputed_binding
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_PY_009_stale_binding_hash
language: python
authority_effect: None
---

# Healthy Pattern: Recomputed Binding (`HP_PY_009`)

## Description

A receipt names one commit. Every content hash in that receipt is recomputed from that commit before the file is written. A mismatch is a refusal, not a stored pair of disagreeing fields.

## Structural Signature

```python
def bind_review(head: str, paths: list[str]) -> dict:
    hashes = {path: blob_sha256(head, path) for path in paths}
    return {"reviewed_head": head, "blobs": hashes}
```

## Remediation Applied

- Recompute hashes from `reviewed_head` at write time.
- Refuse the write when any stored hash was taken from a different commit.
