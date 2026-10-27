---
documentation_contract: symbol-game-documentation/v1
title: Runtime action reference
kind: public-contract-reference
audience:
- engineers
- coding-agents
status: active
maturity: source-grounded-runtime
claim_status: source-grounded
authority_effect: "None"
source_paths:
- engine/crates_rs/core_symbol_game/src/invoke.rs
- engine/crates_rs/core_symbol_game_runtime/src
source_revision: 305b9690f97fc3f5c13e361cfe752a6d5dc7ad8d
prerequisites: []
verification: py -3.12 -m pfp.scripts.docs_integrity validate
aliases: []
related:
- 08_native_rust_host_architecture.md
- 01_digest_and_canonical_serialization.md
- 11_mss_n_machine_wire_registry.md
last_verified: 2026-10-22
verification_scope: adapter and action names parsed from git show HEAD:invoke.rs at 305b9690; no cargo build or test run. The worktree copy of invoke.rs was dirty and was not the counted text.
---

# 09. Runtime Action Reference & Dispatch Governor

AuthorityEffect: None.

The native host dispatches runtime requests through the action registry in
core_symbol_game/src/invoke.rs. That registry, not a hand-maintained
capability list, is the source of truth. Query --describe-runtime when an
integration needs the currently advertised adapter names.

## Action families

| Adapter | Actions and role |
| --- | --- |
| canonical | Wire, unwire, canonical JSON/bytes, and domain digests |
| diff_parser | Strict unified-diff parsing |
| code_change | Proposal creation, candidate submission, and gate evaluation |
| research_evidence | Bounded research-source intake |
| scoring_frontier | Proposal scoring and ranking |
| f2 | Finite gauge-board classification |
| prompt_turn | Reply residual validation |
| rewriting | Critical-peak evaluation, pair enumeration, and permutation-order checks |
| rational | Exact L1 certificate verification and primal-dual solving |
| coda | CODA evaluation and verification |
| functional | Rust-owned functional evaluation and verification |
| linear_algebra | Exact determinant, rank, LDLT, positivity, minors, and characteristic polynomial |
| homology and holonomy | Exact boundary and ordered-loop checks |
| ddc, prime, lggr, pharmacy | DDC tape checks, Prime handling, LGGR checks, and pharmacy detection |

### Full registry at pin 305b9690 (2026-10-22)

Read from the `runtime_actions!` table in [invoke.rs](../../../../engine/crates_rs/core_symbol_game/src/invoke.rs) as committed at `305b9690`: 150 actions in 57 adapters, in declaration order. `--describe-runtime` returns the adapter names in this order (`advertised_adapters`, which de-duplicates the first column). The summary table above is a reading aid and is incomplete. `f2` is an adapter; its action is `classify_gauge_board`. The CLI still has a separate `classify-board` operation, described in [08](08_native_rust_host_architecture.md). `homology` and `holonomy` are two adapters.

| Adapter | Actions | Action names |
| --- | --- | --- |
| `qddc` | 7 | `qddc_hodge`, `qddc_repair_projector`, `qddc_deform`, `qddc_lindblad`, `qddc_retract`, `qddc_probe`, `qddc_density` |
| `exact_math` | 2 | `math_rational_matrix`, `math_gf2_matrix` |
| `majorana` | 6 | `majorana_braid_action`, `majorana_gf2_diagnostic`, `majorana_kitaev_wire`, `majorana_multiqubit_braid`, `majorana_noise`, `majorana_noise_generate` |
| `homology` | 4 | `homology_contraction`, `homology_perturbation`, `exact_verify_boundary_closed`, `exact_verify_simplicial_boundary_law` |
| `functional` | 5 | `functional_projection_transfer`, `functional_family_bound`, `functional_family_member`, `functional_evaluate`, `functional_verify` |
| `qm_classical` | 2 | `qm_classical_evaluate`, `qm_classical_verify` |
| `workflow` | 8 | `anti_skill_detect`, `skill_garden_cull`, `skill_garden_cull_file`, `workflow_substitute`, `workflow_validate`, `workflow_graph`, `workflow_operation_v3`, `workflow_composition_v3` |
| `adversary` | 3 | `adversary_bout`, `adversary_support`, `adversary_support_file` |
| `immune` | 7 | `immune_allostery`, `immune_clonal`, `immune_admission`, `immune_activation`, `immune_screen`, `immune_pharmacy_search`, `immune_pharmacy_search_file` |
| `prompt_civilization` | 6 | `prompt_civilization`, `prompt_rank`, `prompt_metabolism`, `prompt_metabolism_file`, `learning_signals`, `learning_signals_file` |
| `intelligence` | 2 | `intelligence_lifecycle`, `intelligence_lifecycle_file` |
| `provider` | 3 | `provider_budget`, `anthropic_messages`, `anthropic_messages_file` |
| `canonical` | 5 | `canonical_wire`, `canonical_unwire`, `canonical_json`, `canonical_bytes_hex`, `domain_digest` |
| `diff_parser` | 1 | `parse_unified_diff` |
| `code_change` | 3 | `create_code_change_proposal`, `submit_patch_candidate`, `evaluate_patch_gates` |
| `research_evidence` | 1 | `intake_research_sources` |
| `glyph_trajectory` | 2 | `glyph_trajectory_execute`, `glyph_trajectory_replay` |
| `scoring_frontier` | 4 | `score_discrete_proposal`, `score_cochain_proposal`, `rank_scored_candidates`, `rank_candidate_proposals` |
| `signed_transport` | 1 | `signed_transport` |
| `f2` | 1 | `classify_gauge_board` |
| `prompt_turn` | 1 | `validate_reply_residual` |
| `prompt_artifact` | 2 | `prompt_artifact`, `immune_fence_render` |
| `reply_control` | 1 | `reply_control` |
| `rewriting` | 3 | `evaluate_critical_peak`, `enumerate_critical_pairs`, `verify_pinned_permutation_order` |
| `rational` | 2 | `verify_l1_certificate`, `exact_solve_l1_primal_dual` |
| `operad` | 4 | `operad_validate_prompt`, `operad_graft_slot`, `operad_evaluate_ideals`, `operad_check_annihilator` |
| `cochain` | 1 | `cochain_evaluate` |
| `wdp_architecture` | 1 | `architecture_dag_verify` |
| `genesis` | 2 | `genesis_resolve`, `coupled_relational_operad_verify` |
| `coda` | 2 | `coda_evaluate`, `coda_verify` |
| `continuum` | 1 | `continuum_evaluate` |
| `wdp_kernel` | 2 | `wdp_kernel_check`, `wdp_certificate_check` |
| `wdp_packet` | 2 | `wdp_packet_evaluate`, `wdp_packet_verify` |
| `genesis_reports` | 5 | `genesis_report_evaluate`, `genesis_report_verify`, `genesis_report_describe_operation`, `genesis_report_commit`, `genesis_report_verify_commit` |
| `measurement` | 2 | `measurement_evaluate`, `measurement_verify` |
| `projection` | 2 | `projection_evaluate`, `projection_verify` |
| `graph` | 3 | `graph_evaluate`, `graph_verify`, `graph_challenge` |
| `decode_control` | 2 | `verify_decode_receipt_v2`, `verify_decode_receipt` |
| `linear_algebra` | 6 | `exact_determinant`, `exact_is_positive_definite`, `exact_ldlt`, `exact_rank`, `exact_leading_minors`, `exact_char_poly` |
| `holonomy` | 2 | `exact_ordered_loop_product`, `exact_is_ordered_closure` |
| `ddc` | 1 | `ddc_verify_tape` |
| `prime` | 5 | `prime_admit`, `prime_replay_decide`, `prime_descent`, `prime_candidate_evaluate`, `prime_stage_record` |
| `lggr` | 3 | `lggr_classify`, `lggr_k_cell_classify`, `lggr_soundness` |
| `pharmacy` | 1 | `pharmacy_detect` |
| `certifiers` | 1 | `verify_phi1_form` |
| `run_folder` | 2 | `run_folder_seal`, `run_folder_verify` |
| `turn_driver` | 2 | `turn_driver_next_prompt`, `turn_driver_step` |
| `stabilizer` | 2 | `stabilizer_solve`, `stabilizer_check` |
| `jcs` | 2 | `jcs_canonicalize`, `jcs_digest` |
| `scratch_board` | 1 | `detect_stationary_attractor` |
| `lean_verify` | 2 | `lean_scan_sources`, `lean_audit_report` |
| `task_decomposition` | 1 | `decompose_task` |
| `retraction` | 2 | `retraction_turn`, `retraction_loop` |
| `debate` | 1 | `debate_localize` |
| `dda` | 1 | `dda_surgery` |
| `transport` | 1 | `simplicial_transport` |
| `challenge` | 3 | `challenge_commit`, `challenge_freeze`, `challenge_score` |

## Invocation contract

Send a RuntimeRequestV1 JSON document through the native host:

~~~powershell
Get-Content -Raw .\runtime-request.json | cargo run --quiet --manifest-path engine/crates_rs/Cargo.toml -p core_symbol_game -- invoke
~~~

The invoke operation reads at most 12,582,912 bytes (`MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES = 12 * 1024 * 1024`) so that
large prompt-artifact actions can be identified; every other action keeps the 65,536-byte
complete-envelope limit (`MAX_RUNTIME_REQUEST_BYTES`, invoke.rs lines 47 and 53). Duplicate JSON keys
are refused before decoding. It returns a
RuntimeOutcomeV1 with action name, success state, result or error, and
authority_effect = None.

## Functional boundary

The functional adapter is the only documented route for named Phi1, Gamma2,
and Xi-related receipt work. Python callers may transport a Rust-issued
result, but cannot calculate a named functional themselves. Invalid chain
laws, floats, non-canonical rationals, and unsupported budgets are refused
before a functional result is issued.

## Versioning rule

Do not copy this table into integration code as an independent capability
registry. Query --describe-runtime and bind a request to the returned surface
when the exact deployed action set matters.
