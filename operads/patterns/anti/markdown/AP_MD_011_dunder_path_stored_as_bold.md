---
pattern_id: AP_MD_011
name: dunder_path_stored_as_bold
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_011_code_span_preserves_dunder_path
language: markdown
authority_effect: None
---

# Anti-Pattern: Dunder Path Stored As Bold (`AP_MD_011`)

## Description

A markdown finding prints one filesystem path twice. The quoted copy stores `__init__.py` as `**init**.py`. The code span on the same line still has `__init__.py`. Copying the quote names a path the stage JSON does not contain.

## Detection Signature

- A finding quote contains the six characters `**init**` where a Python path has `__init__.py`.
- The backtick path on that same line contains `__init__.py`.
- The stage JSON lists that file with underscores, not asterisks.
- The two copies on the line are not the same path bytes.

## Witness

Historical gate markdown. This digest did not rerun the gate and did not reopen the deposit. Source: `_ic/inr/core_paper_reviews/2026-10-06_wdp_r1/gates.md`, dated 2026-10-06, overall status FAIL, 20 / 26 rules passed.

> Unmanifested file present in deposit: 'code/relational_coincidence/**init**.py' (`code/relational_coincidence/__init__.py`)

The same receipt repeats it:

> Unmanifested file present in deposit: 'code/relational_coincidence/tests/**init**.py' (`code/relational_coincidence/tests/__init__.py`)

`stage_0.json` in that folder lists both files with `__init__.py` under `R_MANIFEST_BIJECTION`. `preflight.txt` has those same error strings and drops only the stage `seconds` field.

## Hazard & Failure Mode

- A repair searches for a filename that contains asterisks, or it skips the real `__init__.py` because the quote no longer matches.
- The code span is the path that agrees with the JSON. The quote is not a second file.
- The manifest-bijection failure stays a historical deposit finding. This pattern does not clear it.

## Dual Healthy Pattern

See [HP_MD_011_code_span_preserves_dunder_path](../../helpful/markdown/HP_MD_011_code_span_preserves_dunder_path.md).
