---
pattern_id: HP_MD_052
name: slop_audit_path_matches_router
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_052_slop_skill_path_misses_router
language: markdown
authority_effect: None
---

# Healthy Pattern: The Slop Audit Path Matches The Router (`HP_MD_052`)

## Description

The skill, the taxonomy, and `comment_slop_router.py` name one output directory. For this router that directory is `_ic/nro/documentation/slop_audit/<relative_path>.md`.

## Structural Signature

- `doc_dest` in the router is the directory named by the skill re-routing invariant and by the taxonomy destination section.
- An audit card is read from that joined path, not from a second tree the writer does not use.
- A missing `.agents/documentation/slop_audit/` tree is not treated as a missing extract when the card is on the router path.

## Remediation Applied

- Change the skill and taxonomy sentences to the `doc_dest` the router assigns, or change `doc_dest` to the path the skill names, in one edit.
- Do not reroute by memory. Open the assignment and the card path.

## Limit

The witness in [AP_MD_052_slop_skill_path_misses_router](../../anti/markdown/AP_MD_052_slop_skill_path_misses_router.md) is historical: the five crates_rs cards were not regenerated. Comment categories stay owned by `techne-comment-slop-hunter-killer`. `AP_MD_001` still owns a bundle size, reproduction command, or version the package does not run. This pattern only binds the slop-audit output directory.
