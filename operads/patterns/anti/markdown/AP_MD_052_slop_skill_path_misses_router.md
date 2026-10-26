---
pattern_id: AP_MD_052
name: slop_skill_path_misses_router
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_052_slop_audit_path_matches_router
language: markdown
authority_effect: None
---

# Anti-Pattern: Slop Skill Path Misses The Router (`AP_MD_052`)

## Description

A comment-slop skill or taxonomy says extracted comments are written under `.agents/documentation/slop_audit/`. The router writes them under `_ic/nro/documentation/slop_audit/`.

## Detection Signature

- The skill or taxonomy names `.agents/documentation/slop_audit/<relative_path>.md`.
- `comment_slop_router.py` sets `doc_dest` to `repo_root / "_ic/nro/documentation"` and joins `slop_audit`.
- The audit card for the scanned source is on the `_ic/nro` path, and `.agents/documentation` is absent.

## Witness

Historical. No `--fix` run was repeated. The opened skill `.agents/skills/techne-comment-slop-hunter-killer/SKILL.md` still says stripped comments are written to `.agents/documentation/slop_audit/<relative_path>.md`. The opened router `omega_engine_operations/use_cases/packaging/comment_slop_router.py` still assigns `doc_dest = repo_root / "_ic/nro/documentation"` and writes `doc_dest / "slop_audit" / rel_path.with_suffix(".md")`. The historical card `_ic/nro/documentation/slop_audit/omega_engine/crates_rs/omega_symbol_game_runtime/src/jcs.md` records line 94 as `Step 6: k digits followed by (n - k) zeros`. That sentence is not in the current `jcs.rs`. `.agents/documentation` is not a directory.

## Hazard & Failure Mode

- A reader looks up the skill path and treats the extract as missing.
- A later pass drops the `_ic/nro` card because the skill names a different directory.

## Dual Healthy Pattern

See [HP_MD_052_slop_audit_path_matches_router](../../helpful/markdown/HP_MD_052_slop_audit_path_matches_router.md).
