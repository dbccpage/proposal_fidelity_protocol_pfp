---
pattern_id: AP_MD_017
name: path_depth_called_math_research
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_017_remediation_matches_listed_error
language: markdown
authority_effect: None
---

# Anti-Pattern: Path Depth Called Math Research (`AP_MD_017`)

## Description

A terminal obstruction lists one Windows path-depth error, then a canned required-work paragraph says that error needs proof editing, algorithm redesign, or mathematical research.

## Detection Signature

- `unresolved_errors` contains only a Win32 `MAX_PATH` depth count. No theorem, proof step, or mathematical obligation is listed there.
- `required_work` says the defects listed above require manual code/proof editing, algorithm redesign, or further mathematical research.
- The co-located republication row `A02` can FAIL with the same detail sentence used when `A02` PASSes: "All audited absolute paths must fit 250 characters." That sentence does not name the file.

## Witness

Historical receipt. This digest did not rerun preflight, the republication gate, pytest, ruff, notebooks, or Lean. Source: `_ic/inr/omega_paper_reviews/pfp_loop_final_20260929_013741/010_the_symbol_game_multi_scale_epistemic_immunity_and_hierarchical_holonomy_decimation/run_all_receipt.json`, review `SWARM_REV_20260929_014727`, overall status `NEEDS_REVISION`.

Stage `preflight_and_envelope_purity` error:

> Win32 MAX_PATH depth violation: 1 files exceed 250 characters.

`summary.obstruction_report.required_work`:

> Automated review and harmonization exhausted fuel without resolving all gates. The unresolved defects listed above require manual code/proof editing, algorithm redesign, or further mathematical research before publication on Zenodo can proceed.

`republication_gate_receipt.json` in the same folder sets `A02` to `FAIL` with detail "All audited absolute paths must fit 250 characters." Paper 001 in this loop sets `A02` to `PASS` with that same detail sentence.

## Hazard & Failure Mode

- A follow-up opens a proof or algorithm task for a path that is longer than 250 characters.
- The path repair is not stated, and the file that failed the limit is still unnamed.
- Fuel-exhausted wording is read as a mathematical block.

## Dual Healthy Pattern

See [HP_MD_017_remediation_matches_listed_error](../../helpful/markdown/HP_MD_017_remediation_matches_listed_error.md).
