---
documentation_contract: symbol-game-documentation/v1
title: 'Self Panel Diversity: Regeneration Ticket'
kind: reference
audience:
- engineers
- coding-agents
status: active
maturity: legacy-source
claim_status: source-legacy
authority_effect: "None"
source_paths:
- omega_engine_education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/0_epistemic_immune_system_eis/oeeis_notes.md
source_revision: 44aff3782
prerequisites: []
verification: python omega_engine_education/documentation/the_symbol_game/scripts/docs_integrity.py
  validate
aliases: []
related: []
last_verified: 2026-09-27
---


# Self Panel Diversity: Regeneration Ticket

**AuthorityEffect:** None. **Status:** open. **Recorded:** 2026-09-26.

## Finding

`omega_engine_pfp/domain/immune/self_panel.json` is the sealed self panel used for thymus negative selection and the clonal kill condition. Its seal is `9f5a786101cdc2371b00fa0a3c929d1edbfee935f87db904388ca9c11c68e789`.

- It holds **1,000 entries**: 250 in each of four categories (`clean_lean4_proof`, `clean_architecture_port`, `clean_prompt_template`, `clean_physics_expression`).
- It holds only **40 distinct base contents**, 10 per category.
- Each base content appears 25 times, differing only by a generated trailer of the form `-- index NNN hash_mod_M`.

A detector checked against this panel is really checked against 40 fixtures. Any conclusion of the form "tolerant of all 1,000 self entries" overstates coverage by a factor of 25.

`SelfPanel.distinct_base_contents()` measures the real diversity. `omega_engine_pfp/tests/test_immune_defect_regressions.py::test_canonical_self_panel_has_forty_distinct_base_contents` pins today's value, so any regeneration has to change the test on purpose.

## What not to do

Do not edit `self_panel.json` in place. The panel is sealed: rewriting entries under the same `sealed_sha256` would make every earlier thymus receipt refer to content that no longer exists.

## Regeneration plan

1. **Build a new panel file with a new seal.** Keep the old file and its seal readable for replaying historical receipts.
2. **Draw real, verified-clean material, not templated variants:**
   - core Lean 4 proofs that compile, from `lean4/research_programs/`;
   - Clean Architecture port and adapter code from `omega_engine_operations/`;
   - governed prompt templates under `omega_engine_governance/contracts/contracts_prompts/`;
   - exact physics expressions from the challenge catalogs.
3. **Size and trailers.** Target at least 400 distinct base contents, with no synthetic trailers. Each entry records its source path and commit.
4. **Screen before sealing.** Run the current detector repertoire against the new panel, and record every detector that becomes self-reactive; the old panel was hiding these.
5. **Update the tests deliberately.** Change the pinned count in the regression test, and update the thymus and kill-condition tests that rely on specific fixture strings, such as `theorem coboundary_nilpotent`.
6. **Note the other implementation.** The thymus that commit 765f81f045 moved out of OEWAS into `omega_engine_epistemic_immune_system/domain/thymus.py` takes its self panel as an argument, so it is unaffected. Unifying the two implementations is upgrade U16 (Omega Engine Epistemic Immune System turn-loop integration) in `omega_engine_projects/mssn_sn_symgam/upgrades/`, added by PR #163.

## Acceptance

- The new panel has at least 400 distinct base contents and a new seal.
- The old panel remains loadable by its seal.
- Every detector that the new panel makes self-reactive is listed with its apoptosis receipt.
