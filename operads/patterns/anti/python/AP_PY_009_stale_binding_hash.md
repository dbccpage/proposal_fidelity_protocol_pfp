---
pattern_id: AP_PY_009
name: stale_binding_hash
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_009_recomputed_binding
language: python
authority_effect: None
---

# Anti-Pattern: Stale Binding Hash (`AP_PY_009`)

## Description

A receipt names one commit, such as `reviewed_head`, while the stored content hashes were computed from a later commit. The digest is well formed and still names the wrong tree.

## Detection Signature

- `reviewed_head` or `head_reviewed` differs from the commit whose blob hashes are stored in the same record.
- Seen in code-review records for PRs 579 and 584 (`stale-binding-hash`).

## Hazard & Failure Mode

- A later reader treats the receipt as evidence for a commit it does not bind.
- Replay of the named commit does not reproduce the stored hashes.

## Dual Healthy Pattern

See [HP_PY_009_recomputed_binding](../../helpful/python/HP_PY_009_recomputed_binding.md).
