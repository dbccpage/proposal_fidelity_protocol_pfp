# Workflows

**One folder per workflow, numbered to match the wiki.** WF1-WF5 have their
own runners. WF6-WF49, WF51, WF55 and WF56 run offline on a shared family runtime
([`pfp_core/workflow_families/`](../pfp_core/workflow_families/)): fixtures only,
no model campaign yet. WF50 is a maintenance workflow. WF52-WF54 have their
own runners: the finite-QM benchmark (live runs recorded), and the industry
replacement benchmark and five-seam showcase (offline only). Open a folder's README
to see what the workflow is for, its status, how to run it offline, what checks
the answer, and where its code is.

**Start here:** [WF1 — typed answer](wf01_typed_answer/README.md). Install once
with `pip install ".[workflows]"`. Every README has offline commands (no model,
no cost); WF1-WF5 also have live commands. The step-by-step
guides are on the [Workflows wiki page](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflows).

| WF | Workflow | Status | Kind | Builds on | Pilots |
| --- | --- | --- | --- | --- | ---: |
| 1 | [Typed answer](wf01_typed_answer/README.md) | **runnable** | base | — | — |
| 2 | [Full slots](wf02_full_slots/README.md) | **runnable** | procedure extension | WF1 | — |
| 3 | [Mine, then solve](wf03_mine_then_solve/README.md) | **runnable** | procedure extension | WF1 | — |
| 4 | [Five agents + LGGR](wf04_five_agents_lggr/README.md) | **runnable** | procedure extension | WF3 | — |
| 5 | [Checked rewrite](wf05_checked_rewrite/README.md) | **runnable** | procedure extension | WF4 | — |
| 6 | [Dialect sweep](wf06_dialect_sweep/README.md) | runnable offline | experiment design | WF5 | 4 |
| 7 | [Typed refusal](wf07_typed_refusal/README.md) | runnable offline | procedure extension | WF1 | 2 |
| 8 | [Staged sealed packets](wf08_staged_sealed_packets/README.md) | runnable offline | procedure extension | WF2, WF5 | — |
| 9 | [Bounded check-and-repair](wf09_bounded_check_and_repair/README.md) | runnable offline | procedure extension | WF2 | — |
| 10 | [Local-to-global obstruction certificate](wf10_local_to_global_obstruction_certificate/README.md) | runnable offline | task preset | WF4, WF9 | 1 |
| 11 | [Dual-certificate synthesis](wf11_dual_certificate_synthesis/README.md) | runnable offline | task preset | WF3, WF9 | 6 |
| 12 | [Mechanism-control arms](wf12_mechanism_control_arms/README.md) | runnable offline | experiment design | WF6, WF3 | 5 |
| 13 | [Exact-domain capsule battery](wf13_exact_domain_capsule_battery/README.md) | runnable offline | task preset | WF1, WF7 | — |
| 14 | [Immune failure classification](wf14_immune_failure_classification/README.md) | runnable offline | meta workflow | WF7, WF12 | 1 |
| 15 | [Adversary tribunal](wf15_adversary_tribunal/README.md) | runnable offline | procedure extension | WF4, WF14 | — |
| 16 | [Substrate crosswalk](wf16_substrate_crosswalk/README.md) | runnable offline | task preset | WF5, WF10 | — |
| 17 | [Witnessed-difference programme](wf17_witnessed_difference_programme/README.md) | runnable offline | task preset | WF10, WF11 | — |
| 18 | [Dossier replay campaign](wf18_dossier_replay_campaign/README.md) | runnable offline | harness gate | WF6, WF12 | 6 |
| 19 | [Failure-derived rule transfer](wf19_failure_derived_rule_transfer/README.md) | runnable offline | experiment design | WF12, WF14 | 4 |
| 20 | [Derivation loop with lift grants](wf20_derivation_loop_with_lift_grants/README.md) | runnable offline | procedure extension | WF9, WF10, WF19 | 10 |
| 21 | [Structural prompt rewriting](wf21_structural_prompt_rewriting/README.md) | runnable offline | procedure extension | WF5 | 4 |
| 22 | [Certified cost ladder](wf22_certified_cost_ladder/README.md) | runnable offline | experiment design | WF6, WF8, WF18 | 2 |
| 23 | [Judge-packet custody audit](wf23_judge_packet_custody_audit/README.md) | runnable offline | harness gate | WF11 | 1 |
| 24 | [Pinned-token operational scratchpad](wf24_pinned_token_operational_scratchpad/README.md) | runnable offline | procedure extension | WF2 | — |
| 25 | [Hierarchical decimation](wf25_hierarchical_decimation/README.md) | runnable offline | procedure extension | WF24 | — |
| 26 | [Multi-round antibody dialogue](wf26_multi_round_antibody_dialogue/README.md) | runnable offline | procedure extension | WF9, WF14 | — |
| 27 | [Hinted retraction with a stationary-loop detector](wf27_hinted_retraction_with_a_stationary_loop_detector/README.md) | runnable offline | procedure extension | WF9 | — |
| 28 | [Eight-role audit dialogue](wf28_eight_role_audit_dialogue/README.md) | runnable offline | procedure extension | WF15 | — |
| 29 | [Checker synthesis scored by mutation kill rate](wf29_checker_synthesis_scored_by_mutation_kill_rate/README.md) | runnable offline | task preset | WF11 | — |
| 30 | [Constraint-forcing anti-recitation](wf30_constraint_forcing_anti_recitation/README.md) | runnable offline | procedure extension | WF1 | — |
| 31 | [Multi-agent tournament with held-out cross-validation](wf31_multi_agent_tournament_with_held_out_cross_validation/README.md) | runnable offline | experiment design | WF1 | — |
| 32 | [Claim-scoped receipt](wf32_claim_scoped_receipt/README.md) | runnable offline | procedure extension | WF1, WF2 | — |
| 33 | [Recursive re-entry with shared fuel](wf33_recursive_re_entry_with_shared_fuel/README.md) | runnable offline | procedure extension | WF9, WF20 | — |
| 34 | [Future-faithful compression and bounded context](wf34_future_faithful_compression_and_bounded_context/README.md) | runnable offline | procedure extension | WF8, WF22 | — |
| 35 | [Proposal-channel comparison](wf35_proposal_channel_comparison/README.md) | runnable offline | experiment design | WF6, WF12 | — |
| 36 | [Guarded staged slot materialisation](wf36_guarded_staged_slot_materialisation/README.md) | runnable offline | procedure extension | WF8 | — |
| 37 | [Evidence-bound harness evolution](wf37_evidence_bound_harness_evolution/README.md) | runnable offline | meta workflow | WF19, WF22 | — |
| 38 | [Diagnostic-trace proposal selection](wf38_diagnostic_trace_proposal_selection/README.md) | runnable offline | procedure extension | WF9 | — |
| 39 | [Authority firewall gate](wf39_authority_firewall_gate/README.md) | runnable offline | harness gate | WF1, WF23 | — |
| 40 | [Restart boundary after exhausted repair](wf40_restart_boundary_after_exhausted_repair/README.md) | runnable offline | procedure extension | WF9, WF20 | — |
| 41 | [Detector adequacy and two-signal admission](wf41_detector_adequacy_and_two_signal_admission/README.md) | runnable offline | meta workflow | WF14 | — |
| 42 | [Reasoning-trace validation](wf42_reasoning_trace_validation/README.md) | runnable offline | procedure extension | WF10, WF21 | — |
| 43 | [Gate-honesty and answer-free leak audit](wf43_gate_honesty_and_answer_free_leak_audit/README.md) | runnable offline | harness gate | WF23 | — |
| 44 | [Exact certificate presets](wf44_exact_certificate_presets/README.md) | runnable offline | task preset | WF11, WF10 | — |
| 45 | [Finite terminal selector and plenitude test](wf45_finite_terminal_selector_and_plenitude_test/README.md) | runnable offline | procedure extension | WF7 | — |
| 46 | [Boundary sufficiency and gluing diagnostic](wf46_boundary_sufficiency_and_gluing_diagnostic/README.md) | runnable offline | procedure extension | WF4 | — |
| 47 | [Resumable bounded frontier search](wf47_resumable_bounded_frontier_search/README.md) | runnable offline | procedure extension | WF9 | — |
| 48 | [Commit-reveal with a hostile mutation gate](wf48_commit_reveal_with_a_hostile_mutation_gate/README.md) | runnable offline | harness gate | WF11, WF23 | — |
| 49 | [Query-preservation stage and mode campaign](wf49_query_preservation_stage_and_mode_campaign/README.md) | runnable offline | experiment design | WF8, WF22 | — |
| 50 | [Repo hygiene](wf50_repo_hygiene/README.md) | runnable | maintenance workflow | — | — |
| 51 | [Exclusion hypotheses with cheapest falsifiers](wf51_exclusion_hypotheses_with_cheapest_falsifiers/README.md) | runnable offline | meta workflow | WF14, WF31 | — |
| 52 | [Finite-QM benchmark](wf52_finite_qm_benchmark/README.md) | **runnable** | experiment design | WF1, WF9, WF12 | — |
| 53 | [Industry replacement benchmark](wf53_industry_replacement_benchmark/README.md) | runnable offline | experiment design | WF12, WF14 | — |
| 54 | [Five-seam mechanism showcase](wf54_five_seam_mechanism_showcase/README.md) | runnable offline | experiment design | WF12, WF24, WF27 | — |
| 55 | [Failure ledger with trial-gated rules](wf55_failure_ledger_with_trial_gated_rules/README.md) | runnable offline | meta workflow | WF1, WF14 | — |
| 56 | [Host-run operad candidates](wf56_host_run_operad_candidates/README.md) | runnable offline | procedure extension | WF2 | — |

## Other folders here

| Folder | What it is |
| --- | --- |
| [`tasks/`](tasks/README.md) | The problems workflows run on: 29 offline examples and 50 certified challenges, each with exact checkers |
| [`dag/`](dag/README.md) | The dependency graph of WF1–WF56 (JSON, Mermaid; the SVG draws WF1–WF49), plus the recorded variations of each workflow |
| [`library/`](library/README.md) | Recipe catalogue, contracts, the raw evidence of the WF1–WF5 runs, and the shared pilot-estate registers |

**Where the code is.** The runnable code for WF1–WF5 is the installable
`pfp.workflows` package ([`pfp/workflows/`](../pfp/workflows/README.md)), so
`pip install` and the `pfp-wf1`…`pfp-wf5` commands keep working; each workflow
README links straight to its code. WF6-WF49, WF51, WF55 and WF56 are one class each in
[`pfp_core/workflow_families/`](../pfp_core/workflow_families/); `python -m
pfp_core.workflow_families check-all` runs all their fixtures offline. Pilot
experiments (earlier model runs with an older harness; most need a runtime that
is not published here) sit inside their workflow folder under `pilots/`. They are
records, not runs of the family runner. Their shared registers and records are in
[`library/pilot_estate/`](library/pilot_estate/README.md).

**Naming.** A folder is `wfNN_short_name`. New workflows take the next number;
a variation of an existing workflow (a different setting or step) goes under
that workflow's "Recorded variations", not into a new folder.

**Paths in older records.** Historical records keep their bytes and may still
name `demos/`, `docs/workflows/`, `pilots/`, `dag/benchmark/` (now WF52),
`benchmarks/` (now WF53 and WF54) or the pre-`tasks/` paths.
