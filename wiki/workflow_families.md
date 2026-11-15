# Workflow families WF6-WF49, WF51 and WF55-WF57

Each family is one class in `pfp_core/workflow_families/` on a shared runtime: one spec, one budget per run, one host check that alone can certify, and offline fixtures that must be accepted or refused. WF1-WF5 keep their own runners (see [Workflows](workflows.md)).

The host checks are moving from Python to the Rust host, `pfp_operad family`, one layer at a time. Moved so far: WF7, WF9, WF10, WF11, WF13, WF20, WF24, WF25, WF26, WF27, WF30, WF31, WF32, WF33, WF38, WF40, WF45, WF46, WF47. For these the host reads the task, writes and guards the prompt and gives the verdict; their page links the Rust file.

```powershell
python -m pfp_core.workflow_families list
python -m pfp_core.workflow_families check-all
```

| WF | Family | Layer | Builds on | Host check |
| --- | --- | ---: | --- | --- |
| [WF7](workflow_wf7.md) | Typed refusal | 1 | WF1 | `typed_refusal_rank_test` |
| [WF30](workflow_wf30.md) | Constraint-forcing anti-recitation | 1 | WF1 | `comparator_network_zero_one_principle` |
| [WF31](workflow_wf31.md) | Multi-agent tournament with held-out cross-validation | 1 | WF1 | `exact_held_out_referee` |
| [WF9](workflow_wf9.md) | Bounded check-and-repair | 2 | WF2 | `xor_cycle_minimal_repair` |
| [WF13](workflow_wf13.md) | Exact-domain capsule battery | 2 | WF1, WF7 | `per_domain_registered_checker` |
| [WF24](workflow_wf24.md) | Pinned-token operational scratchpad | 2 | WF2 | `dual_holonomy_checkers` |
| [WF32](workflow_wf32.md) | Claim-scoped receipt | 2 | WF1, WF2 | `per_claim_independent_checkers` |
| [WF45](workflow_wf45.md) | Finite terminal selector and plenitude test | 2 | WF7 | `finite_survivor_set_verifier` |
| [WF56](workflow_wf56.md) | Host-run operad candidates | 2 | WF2 | `rust_candidate_body_run_against_host_judge` |
| [WF10](workflow_wf10.md) | Local-to-global obstruction certificate | 3 | WF4, WF9 | `cochain_gluing_or_cycle_obstruction` |
| [WF11](workflow_wf11.md) | Dual-certificate synthesis | 3 | WF3, WF9 | `lp_dual_and_farkas_certificate` |
| [WF25](workflow_wf25.md) | Hierarchical decimation | 3 | WF24 | `cycle_residual_preserving_decimation` |
| [WF27](workflow_wf27.md) | Hinted retraction with a stationary-loop detector | 3 | WF9 | `xor_residual_gate_stationary_loop` |
| [WF38](workflow_wf38.md) | Diagnostic-trace proposal selection | 3 | WF9 | `host_recomputed_defect_ranking` |
| [WF46](workflow_wf46.md) | Boundary sufficiency and gluing diagnostic | 3 | WF4 | `glued_trace_global_evaluator` |
| [WF47](workflow_wf47.md) | Resumable bounded frontier search | 3 | WF9 | `sign_gauge_checkpoint_chain` |
| [WF57](workflow_wf57.md) | Host-tested patch repair | 3 | WF9, WF56 | `rust_patch_tested_on_working_copy` |
| [WF6](workflow_wf6.md) | Dialect sweep | 4 | WF5 | `dialect_query_preservation_sweep` |
| [WF8](workflow_wf8.md) | Staged sealed packets | 4 | WF2, WF5 | `stage_seal_chain_recompute` |
| [WF16](workflow_wf16.md) | Substrate crosswalk | 4 | WF5, WF10 | `incidence_rank_crosswalk` |
| [WF17](workflow_wf17.md) | Witnessed-difference programme | 4 | WF10, WF11 | `hml_separator_bisimulation_check` |
| [WF21](workflow_wf21.md) | Structural prompt rewriting | 4 | WF5 | `fenced_rewrite_exact_judge` |
| [WF23](workflow_wf23.md) | Judge-packet custody audit | 4 | WF11 | `judge_packet_custody_audit` |
| [WF29](workflow_wf29.md) | Checker synthesis scored by mutation kill rate | 4 | WF11 | `mutation_kill_rate_with_valid_panel` |
| [WF44](workflow_wf44.md) | Exact certificate presets | 4 | WF11, WF10 | `exact_certificate_presets` |
| [WF12](workflow_wf12.md) | Mechanism-control arms | 5 | WF6, WF3 | `integer_rank_difference_certificate` |
| [WF36](workflow_wf36.md) | Guarded staged slot materialisation | 5 | WF8 | `exact_cochain_check` |
| [WF39](workflow_wf39.md) | Authority firewall gate | 5 | WF1, WF23 | `authority_guard_vector` |
| [WF42](workflow_wf42.md) | Reasoning-trace validation | 5 | WF10, WF21 | `rational_lp_primal_dual_check` |
| [WF43](workflow_wf43.md) | Gate-honesty and answer-free leak audit | 5 | WF23 | `answer_free_probe_replay` |
| [WF48](workflow_wf48.md) | Commit-reveal with a hostile mutation gate | 5 | WF11, WF23 | `dual_checker_mutation_suite` |
| [WF14](workflow_wf14.md) | Immune failure classification | 6 | WF7, WF12 | `thymus_two_signal_admission` |
| [WF18](workflow_wf18.md) | Dossier replay campaign | 6 | WF6, WF12 | `dossier_replay_reproduces_grades` |
| [WF35](workflow_wf35.md) | Proposal-channel comparison | 6 | WF6, WF12 | `channel_blind_fixed_oracle` |
| [WF15](workflow_wf15.md) | Adversary tribunal | 7 | WF4, WF14 | `kripke_box_witness_check` |
| [WF19](workflow_wf19.md) | Failure-derived rule transfer | 7 | WF12, WF14 | `held_out_transfer_gain` |
| [WF22](workflow_wf22.md) | Certified cost ladder | 7 | WF6, WF8, WF18 | `cost_ladder_refusal_escalation` |
| [WF26](workflow_wf26.md) | Multi-round antibody dialogue | 7 | WF9, WF14 | `epitope_antibody_exact_oracle` |
| [WF41](workflow_wf41.md) | Detector adequacy and two-signal admission | 7 | WF14 | `detector_calibration_completeness` |
| [WF51](workflow_wf51.md) | Exclusion hypotheses with cheapest falsifiers | 7 | WF14, WF31 | `exact_falsifier_and_open_branch_check` |
| [WF55](workflow_wf55.md) | Failure ledger with trial-gated rules | 7 | WF1, WF14 | `rust_ledger_admission_on_host_judged_trial` |
| [WF20](workflow_wf20.md) | Derivation loop with lift grants | 8 | WF9, WF10, WF19 | `structural_lift_grant_loop` |
| [WF28](workflow_wf28.md) | Eight-role audit dialogue | 8 | WF15 | `strict_l1_defect_descent` |
| [WF34](workflow_wf34.md) | Future-faithful compression and bounded context | 8 | WF8, WF22 | `continuation_verdict_equality` |
| [WF37](workflow_wf37.md) | Evidence-bound harness evolution | 8 | WF19, WF22 | `taint_pareto_sign_test_confirmation` |
| [WF49](workflow_wf49.md) | Query-preservation stage and mode campaign | 8 | WF8, WF22 | `decoded_query_equality_seal_chain` |
| [WF33](workflow_wf33.md) | Recursive re-entry with shared fuel | 9 | WF9, WF20 | `shared_fuel_parent_bound_reentry` |
| [WF40](workflow_wf40.md) | Restart boundary after exhausted repair | 9 | WF9, WF20 | `cochain_trichotomy_boundary` |

WF1-WF5 have their own runners ([Workflows](workflows.md)); WF50 is a maintenance workflow ([WF50](workflow_wf50.md)).

Every page states what its fixtures support and what they do not. No family has a recorded live or local model campaign yet.
