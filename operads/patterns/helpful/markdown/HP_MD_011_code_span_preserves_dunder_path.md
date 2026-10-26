---
pattern_id: HP_MD_011
name: code_span_preserves_dunder_path
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_011_dunder_path_stored_as_bold
language: markdown
authority_effect: None
---

# Healthy Pattern: Code Span Preserves The Dunder Path (`HP_MD_011`)

## Description

A markdown finding prints a filesystem path in one code span. Underscores stay underscores. A second copy, if it is printed, is the same bytes as that span and as the stage JSON.

## Structural Signature

- The path is in a code span, including `__init__.py`.
- No quoted twin replaces `__` with `**`.
- The span matches the stage JSON path for that finding.

## Remediation Applied

- Delete the emphasis-rewritten quote, or replace it with the code-span bytes.
- Do not add a deposit file whose name contains `**init**`.
- Keep the historical JSON path as the name the gate listed.

## Limit

The witness in [AP_MD_011_dunder_path_stored_as_bold](../../anti/markdown/AP_MD_011_dunder_path_stored_as_bold.md) is the historical 2026-10-06 file `gates.md`. The gate was not rerun. `R_MANIFEST_BIJECTION` still failed for those unmanifested files. This pattern does not repair the manifest.

`AP_MD_002` still owns spaced tokens in a Lean listing. A viewer that bolds `__init__` while the file bytes remain underscores is not this stored-asterisk defect. `AP_MD_009` still owns a nested `preflight_verdict` of `PASSED` on a blocked stage.

## Dual Anti-Pattern

See [AP_MD_011_dunder_path_stored_as_bold](../../anti/markdown/AP_MD_011_dunder_path_stored_as_bold.md).
