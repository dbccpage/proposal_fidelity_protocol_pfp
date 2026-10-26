---
pattern_id: AP_PY_008
name: canonical_digest_ascii_drift
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_008_ascii_canonical_digest
language: python
authority_effect: None
---

# Anti-Pattern: Canonical Digest ASCII Drift (`AP_PY_008`)

## Description

One side of a digest seam calls `json.dumps(..., ensure_ascii=False)` while the other side, including the Rust hasher, uses `ensure_ascii=True`. The same object then has two SHA-256 identities.

## Detection Signature

- Regex: `ensure_ascii\s*=\s*False` inside a function whose result is hashed.
- Seen in code-review records for PRs 580 and 588 (`canonical-form-drift`).

## Hazard & Failure Mode

- An operator can mint a request digest Python accepts and Rust rejects, or the reverse.
- Receipt replay fails with no change in the logical payload.

## Dual Healthy Pattern

See [HP_PY_008_ascii_canonical_digest](../../helpful/python/HP_PY_008_ascii_canonical_digest.md).
