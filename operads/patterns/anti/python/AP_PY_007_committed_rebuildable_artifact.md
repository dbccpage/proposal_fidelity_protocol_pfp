---
pattern_id: AP_PY_007
name: committed_rebuildable_artifact
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_007_rebuild_and_hash_pin
language: python
authority_effect: None
---

# Anti-Pattern: Committed Rebuildable Artifact (`AP_PY_007`)

## Description

A generated archive, coverage database, or rendered bundle is committed as if it were source. A sibling script already rebuilds those bytes, and no consumer opens the committed copy.

## Detection Signature

- A tracked `*.zip`, rebuilt `*.pdf`, or `.coverage` file sits next to `rebuild_release.py`, `build_paper_artifacts.py`, or an equivalent generator.
- The manifest does not list the committed blob, or the blob re-archives a package the generator already emits.
- Seen in code-review records for PRs 578 and 584 (`committed-rebuildable-artifact`).

## Hazard & Failure Mode

- The git object store keeps a second copy of bytes a command can recreate.
- Reviewers cannot tell which copy is the witness.
- A later generator change leaves the committed blob stale while tests still pass.

## Dual Healthy Pattern

See [HP_PY_007_rebuild_and_hash_pin](../../helpful/python/HP_PY_007_rebuild_and_hash_pin.md).
