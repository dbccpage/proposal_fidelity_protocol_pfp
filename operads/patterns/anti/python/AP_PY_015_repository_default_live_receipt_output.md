---
pattern_id: AP_PY_015
name: repository_default_live_receipt_output
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_015_caller_selected_receipt_custody
language: python
authority_effect: None
---

# Anti-Pattern: Repository-Default Live Receipt Output (`AP_PY_015`)

## Description

An operational command selects a repository-owned receipt directory when the
caller does not name an output path. Fresh runs then overwrite or mingle with
committed historical reports, while later readers can mistake those reports for
facts about the current candidate.

## Detection Signature

- A CLI gives `--json`, `--markdown-output`, or a similar output flag a default
  beneath a checked-in `evidence/` or receipt directory.
- A helper constructs an output path from its own module location instead of a
  caller-provided directory.
- A per-stop audit scans a historical corpus by default and reports its results
  as though the corpus described the ambient source tree.

## Hazard & Failure Mode

- A live command changes tracked history as an incidental side effect.
- Old pass reports become accidental runtime inputs or apparent current proof.
- An audit can fail or pass for the wrong subject because its receipt scope was
  inferred from a repository path rather than named by the operator.

## Dual Healthy Pattern

See [HP_PY_015_caller_selected_receipt_custody](../../helpful/python/HP_PY_015_caller_selected_receipt_custody.md).
