---
pattern_id: AP_MD_016
name: gate_fail_called_math_research
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_016_obstruction_names_the_failing_gate
language: markdown
authority_effect: None
---

# Anti-Pattern: Gate Failure Called Mathematical Research (`AP_MD_016`)

## Description

A one-round review receipt uses one terminal sentence for every blocked package. The sentence says harmonization exhausted its fuel and that the unresolved defects require proof editing, algorithm redesign, or further mathematical research. The recorded errors are a linter, a missing verifier, a hash mismatch, or a missing TeX file.

## Detection Signature

- `rounds_executed` is 1, and `obstruction_report.status` is `TERMINAL_OBSTRUCTION`.
- `required_work` is the same sentence on packages whose stage errors differ.
- The sentence names proof editing, algorithm redesign, or further mathematical research, and it does not name the stage error.
- The unresolved errors name ruff, `verify_deposit.py`, a manifest hash, `.env`, or a TeX/PDF requirement.

## Witness

Historical receipts. This digest did not rerun gates. Source folder `_ic/inr/omega_paper_reviews/pfp_loop_20260928_234130/`.

`002_the_symbol_game_signed_presentations_and_search_frontier/run_all_receipt.json` (`SWARM_REV_20260928_234210`) has `rounds_executed` 1. Stages 0, 1, 3, 4, and 5 are `PASS`. Stage 2 is `NOT_APPLICABLE`. Stage 5 still records `visual_inspection` `NOT_VERIFIED`; that limit is not this pattern. The only failing stage is packaging. Its error is `verify_deposit.py` exit 1: recorded file missing `.env`, hash mismatch on `jupyter_notebooks/signed_exchange_and_frontier.ipynb`, and excluded file listed in the manifest `.env`. The obstruction sentence is:

> Automated review and harmonization exhausted fuel without resolving all gates. The unresolved defects listed above require manual code/proof editing, algorithm redesign, or further mathematical research before publication on Zenodo can proceed.

The same sentence is the `required_work` of all eleven receipts in that folder. Ten of them do not record a mathematical blocker.

## Hazard & Failure Mode

- A later note treats an import-sort failure or a missing `verify_deposit.py` as an open mathematical problem.
- Fuel exhaustion is cited after one round that did not attempt a repair.
- A real dual-witness blocker, when one receipt has it, is not named, so it is mixed with the lint and deposit lines.

## Dual Healthy Pattern

See [HP_MD_016_obstruction_names_the_failing_gate](../../helpful/markdown/HP_MD_016_obstruction_names_the_failing_gate.md).
