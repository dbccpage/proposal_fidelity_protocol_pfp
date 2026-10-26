---
pattern_id: AP_MD_022
name: axiom_lines_replace_failed_olean
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_022_lake_exit_before_axiom_lines
language: markdown
authority_effect: None
---

# Anti-Pattern: Axiom Lines Replace A Failed Olean (`AP_MD_022`)

## Description

A formal Lean stage fails because `lake build` exits 1 while creating an `.olean`. The same error still contains `does not depend on any axioms` info lines, and a sibling stage is `PASS` with a mechanized-proof survival bullet. Quoting those lines drops the failed create.

## Detection Signature

- Stage `formal_lean4_mechanization` has `status` `FAIL`. The error says `lake build` exited 1 and that historical axiom reports cannot replace a current build.
- That error then prints `does not depend on any axioms` lines and `failed to create file` for an `.olean`.
- A different stage, `mathematical_foundations_and_dialect_firewall`, is `PASS` and lists mechanized proof terms verified without unproven axioms.
- `required_work` asks for proof editing, algorithm redesign, or further mathematical research. `remediation_route` is a paper-edition `rebuild`. Neither names the failed `.olean` create.

## Witness

Historical receipt, not a fresh Lean build. This digest did not rerun gates. Source folder `_ic/inr/omega_paper_reviews/pfp_mssn_batch_20260930_140849/`.

`009/run_all_receipt.json` (`SWARM_REV_20260930_141404`) has `overall_status` `NEEDS_REVISION` and verdict `NOT READY FOR ZENODO REPUBLICATION`. Stages 0, 1, 3, 4, 5, and 6 are `PASS`. Stage 2 is `FAIL`. `rounds_executed` is 1. `obstruction_report.status` is `TERMINAL_OBSTRUCTION`.

Stage 2 error begins:

> lake build failed (exit 1); historical axiom reports cannot replace a current build

The same error records thirteen info lines, `RuntimeLimits.lean:176` through `:188`. The first is:

> info: RuntimeLimits.lean:176:0: 'SnSymbolGameAndPackets.same_level_target_not_licensed_lift' does not depend on any axioms

The stderr in that error is:

> failed to write 'C:\Users\a343o\.gemini\antigravity\worktrees\the_symbol_game\sync_with_remote_main\omega_engine_atlas\coda_atlas\omega_engine_pfp\009_the_symbol_game_adversarial_dialectics_and_terminal_reality_gates\lean4\.lake\build\lib\lean\RuntimeLimits.olean': failed to create file

> error: Lean exited with code 1

The error then names required targets that logged failures: `Level15AuthorityCalculus` and `RuntimeLimits`. The quoted create failure is `RuntimeLimits.olean` only.

Stage 1 `old_man_survived` includes:

> Mechanized proof terms verified without unproven axioms or sorry escapes.

`summary.remediation_route` is `python -m omega_engine_research_papers.use_cases.paper_edition.cli rebuild` with a paper path. `summary.obstruction_report.required_work` is:

> Automated review and harmonization exhausted fuel without resolving all gates. The unresolved defects listed above require manual code/proof editing, algorithm redesign, or further mathematical research before publication on Zenodo can proceed.

## Hazard & Failure Mode

- A later note treats the axiom-free info lines, or the stage-1 survival bullet, as a current mechanization.
- The failed `.olean` create is then sent to proof editing or to a paper rebuild.
- Pytest, ruff, notebook, and packaging `PASS` rows in the same receipt are cited as if they discharged stage 2.

## Dual Healthy Pattern

See [HP_MD_022_lake_exit_before_axiom_lines](../../helpful/markdown/HP_MD_022_lake_exit_before_axiom_lines.md).
