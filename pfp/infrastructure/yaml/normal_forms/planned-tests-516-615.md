# Planned Tests 516–615

**AuthorityEffect:** `None`
**Parent inventory:** [planned-tests.md](planned-tests.md)

Tests 1–515 stay in the parent inventory. The rows below are planned. They have no module and no execution receipt.

## 26. Tranche 27: Exact Rational Constraint Sums (Tests 516–535)

**Status:** Planned. No module and no execution receipt.  
Target Module: `omega_engine_governance/tests/normal_forms/test_tranche27_exact_rational_constraint_sums.py`  
Aligned Contracts: `nf.physics.wdwnf`, `nf.physics.l1_constraint_closure`, `nf.runtime.zfnf`

Each amplitude is a signed rational $\sigma_i N_i / D_i$ with $D_i > 0$. The net constraint is the GCD-reduced fold $\sum_i \sigma_i N_i / D_i$, and the constraint vanishes exactly when $N_{\text{net}} = 0$.

| # | Test Identifier | Category | Target Invariant & Scope |
|---|---|---|---|
| 516 | `test_single_term_rational_amplitude_is_not_zero` | Exact sum | A one-term constraint $1/7$ yields $N_{\text{net}} \neq 0$. The $k=1$ term remains in the fold. |
| 517 | `test_two_term_exact_cancellation` | Exact sum | $1/2 - 1/2$ yields $N_{\text{net}} = 0$ after reduction. |
| 518 | `test_two_term_false_zero_rejected` | Exact sum | $1/2 - 1/3$ yields $1/6$, so $N_{\text{net}} \neq 0$. |
| 519 | `test_three_term_false_zero_rejected` | Exact sum | $1/2 + 1/3 - 3/5$ yields $7/30$, so $N_{\text{net}} \neq 0$. |
| 520 | `test_three_term_true_zero_accepted` | Exact sum | $1/2 + 1/3 - 5/6$ yields $N_{\text{net}} = 0$. |
| 521 | `test_large_integer_beyond_2_64` | Exact sum | Numerators and denominators above $10^{18}$ fold by stepwise GCD reduction and return the same reduced fraction as arbitrary-precision arithmetic. |
| 522 | `test_stepwise_fold_keeps_single_term` | Exact sum | The fold of a single fraction equals that fraction. A pairwise sum over $i \neq j$ is not used as the constraint value. |
| 523 | `test_stepwise_fold_disagrees_with_pairwise_product_at_k3` | Exact sum | For three fractions, the stepwise rational sum differs from $\sum_{i \neq j} n_i d_j$. The harness reports the stepwise sum. |
| 524 | `test_denominator_strictly_positive` | Exact sum | An amplitude with $D_i = 0$ is a typed refusal before any fold begins. |
| 525 | `test_sign_applied_before_reduction` | Exact sum | $\sigma_i \in \{+1,-1\}$ is applied to the numerator, and GCD reduction leaves a positive denominator. |
| 526 | `test_unreduced_fractions_canonicalize` | Exact sum | $2/4 + 1/2$ reduces to the same $(N_{\text{net}}, D_{\text{net}})$ as $1/2 + 1/2$. |
| 527 | `test_wdw_constraint_vanishes_iff_numerator_zero` | WDWNF | The Wheeler–DeWitt constraint $H_{\perp}$ is recorded as zero exactly when the folded numerator is zero. |
| 528 | `test_positive_wdw_residual_refuses_preserve` | WDWNF | A folded residual of $1/2$ routes away from `Preserve`. |
| 529 | `test_momentum_constraint_uses_same_rational_fold` | L1 closure | The spatial diffeomorphism constraint uses the same signed rational fold as $H_{\perp}$. |
| 530 | `test_four_term_mixed_sign_cancellation` | Exact sum | $1/3 + 1/6 - 1/2 + 0/1$ yields $N_{\text{net}} = 0$. |
| 531 | `test_zero_numerator_is_exact_zero` | Exact sum | $0/5$ is exact zero and stays exact zero inside a larger fold. |
| 532 | `test_negative_denominator_normalized` | Exact sum | Input $-1/-2$ is stored as $+1/2$ with $D > 0$. Input $1/-2$ is stored as $-1/2$ with $D > 0$. |
| 533 | `test_gcd_reduction_is_deterministic` | Exact sum | Two calls on the same multiset of fractions return identical $(N_{\text{net}}, D_{\text{net}})$. |
| 534 | `test_rational_fold_order_independence` | Exact sum | Every permutation of a fixed list of signed fractions returns the same reduced sum. |
| 535 | `test_float_constraint_payload_refused` | Exact sum | A float payload such as `0.16666666666666666` is a typed refusal. The fold accepts only integer numerators and denominators. |

---

## 27. Tranche 28: Null Totality, Boolean Identity, Residual Zero & Candidate Sets (Tests 536–555)

**Status:** Planned. No module and no execution receipt.  
Target Module: `omega_engine_governance/tests/normal_forms/test_tranche28_null_totality_and_guard_identity.py`  
Aligned Contracts: `nf.evidence.certificate`, `nf.coda.eqnf`, `nf.runtime.zfnf`, `normal_form_contract_schema.yaml`

Boolean fields use `type(val) is bool`. SQL disagreement uses `IS DISTINCT FROM`. Guard $g_3$ requires `residual_mass == 0`. Guard $g_5$ requires set equality of candidate identifiers.

| # | Test Identifier | Category | Target Invariant & Scope |
|---|---|---|---|
| 536 | `test_bool_field_rejects_int_one` | Boolean identity | A schema boolean rejects integer `1`. The mutation is the witness. |
| 537 | `test_bool_field_rejects_int_zero` | Boolean identity | A schema boolean rejects integer `0`. The mutation is the witness. |
| 538 | `test_bool_field_accepts_true_and_false` | Boolean identity | `True` and `False` pass a schema boolean check, and their Python types are `bool`. |
| 539 | `test_conditional_field_accepts_bool_or_conditional` | Boolean identity | A field whose schema is boolean-or-`"conditional"` accepts `True`, `False`, and the string `"conditional"`. |
| 540 | `test_conditional_field_rejects_other_strings` | Boolean identity | The same field refuses `"true"`, `"false"`, `"yes"`, and the empty string. |
| 541 | `test_null_preflight_flags_null_fact_value` | Null totality | A totality preflight returns the row whose protected fact value is NULL. |
| 542 | `test_null_preflight_flags_null_global_verdict` | Null totality | A totality preflight returns the row whose `global_verdict` is NULL. |
| 543 | `test_null_preflight_flags_null_local_product` | Null totality | A totality preflight returns the row whose `local_product` is NULL. |
| 544 | `test_sql_inequality_misses_null_disagreement` | Null totality | `global_verdict <> local_product` returns no row when one side is NULL. The same row is returned by `IS DISTINCT FROM`. |
| 545 | `test_is_distinct_from_detects_null_versus_value` | Null totality | `NULL IS DISTINCT FROM 1` and `0 IS DISTINCT FROM NULL` both select the disagreeing row. |
| 546 | `test_is_distinct_from_detects_value_mismatch` | Null totality | Two non-null unequal verdicts are selected by `IS DISTINCT FROM`. |
| 547 | `test_is_distinct_from_accepts_equal_pair` | Null totality | Two equal non-null verdicts are absent from the `IS DISTINCT FROM` result. |
| 548 | `test_zero_residual_guard_requires_exact_zero` | Residual gate | Guard $g_3$ passes only when `residual_mass == 0` as an exact rational. |
| 549 | `test_half_residual_fails_under_positive_tolerance` | Residual gate | Residual mass $1/2$ fails $g_3$ when a caller supplies a positive numeric tolerance. |
| 550 | `test_certificate_verify_is_executed` | Certificate | An attached distance certificate is accepted only after `certificate.verify()` returns success. |
| 551 | `test_certificate_distance_equals_residual_mass` | Certificate | The validator requires `certificate.distance == residual_mass` on the exact rational. |
| 552 | `test_contradictory_certificate_refuses` | Certificate | A certificate whose distance differs from the computed residual mass produces an explicit refusal. |
| 553 | `test_exhaustive_guard_requires_set_equality` | Exhaustiveness | Guard $g_5$ passes when the checked candidate-id set equals `packet.evaluator_class_e` and the lengths are equal. |
| 554 | `test_duplicate_checks_fail_set_exhaustiveness` | Exhaustiveness | A count `candidates_checked >= candidates_declared` with a repeated id and a missing declared id fails $g_5$. |
| 555 | `test_extraneous_candidate_id_fails_exhaustiveness` | Exhaustiveness | A checked id absent from the packet fails $g_5$ even when the counts match. |

---

## 28. Tranche 29: Loss-Ledger Trigger Registry (Tests 556–575)

**Status:** Planned. No module and no execution receipt.  
Target Module: `omega_engine_governance/tests/normal_forms/test_tranche29_loss_ledger_trigger_registry.py`  
Aligned Contracts: `nf.evidence.loss_ledger`, `nf.compilation.cpnf`, `nf.transport.gtmur`, `nf.motion.flow_control`, `nf.representation.gnf`, `nf.motion.locality_lrb`, `nf.epistemic.location`, `nf.epistemic.enf`

The closed registry in `normal_form_contract_schema.yaml` is the only source of trigger ids. `loss_ledger_required: conditional` carries one of those ids.

| # | Test Identifier | Category | Target Invariant & Scope |
|---|---|---|---|
| 556 | `test_conditional_obligation_requires_trigger_id` | Registry | `loss_ledger_required: conditional` with `loss_ledger_trigger_id: null` is a schema refusal. |
| 557 | `test_conditional_prose_without_trigger_id_refused` | Registry | A free-text loss commentary and a null trigger id is a schema refusal. |
| 558 | `test_trigger_id_cpnf_lossy_compilation_lowering_resolves` | Registry | `cpnf.lossy_compilation_lowering` resolves to the closed registry entry for lossy compilation lowering. |
| 559 | `test_trigger_id_gtmur_unmapped_field_drop_resolves` | Registry | `gtmur.unmapped_field_drop` resolves to the closed registry entry for unmapped field drop. |
| 560 | `test_trigger_id_flow_control_buffer_drop_resolves` | Registry | `flow_control.buffer_drop` resolves to the closed registry entry for buffer drop. |
| 561 | `test_trigger_id_gnf_hyperedge_projection_loss_resolves` | Registry | `gnf.hyperedge_projection_loss` resolves to the closed registry entry for hyperedge projection loss. |
| 562 | `test_trigger_id_locality_lrb_tail_truncation_resolves` | Registry | `locality_lrb.tail_truncation` resolves to the closed registry entry for Lieb–Robinson tail truncation. |
| 563 | `test_trigger_id_epistemic_location_partition_divergence_resolves` | Registry | `epistemic_location.partition_divergence` resolves to the closed registry entry for partition divergence. |
| 564 | `test_trigger_id_enf_lossy_epistemic_transition_resolves` | Registry | `enf.lossy_epistemic_transition` resolves to the closed registry entry for lossy epistemic transition. |
| 565 | `test_unregistered_trigger_id_refused` | Registry | `loss_ledger_trigger_id: "custom.operator_note"` is a schema refusal. |
| 566 | `test_registry_keys_equal_schema_enum` | Registry | The keys of `loss_ledger_trigger_registry` equal the non-null enum of `loss_ledger_trigger_id`. |
| 567 | `test_required_false_permits_null_trigger` | Registry | `loss_ledger_required: false` with a null trigger id passes the trigger check. |
| 568 | `test_required_true_demands_ledger_entries` | Ledger payload | `loss_ledger_required: true` with an empty entry list is a refusal. |
| 569 | `test_required_true_rejects_missing_ledger_object` | Ledger payload | `loss_ledger_required: true` with no ledger object is a refusal. |
| 570 | `test_loss_ledger_required_rejects_int_zero_and_one` | Boolean identity | Integer `0` and integer `1` fail the `loss_ledger_required` type check. Accepted values are `True`, `False`, and `"conditional"`. |
| 571 | `test_trigger_fires_only_for_its_event` | Predicate | `flow_control.buffer_drop` stays inactive on a compilation-lowering event, and `cpnf.lossy_compilation_lowering` stays inactive on a buffer-drop event. |
| 572 | `test_inactive_trigger_omits_ledger` | Predicate | When `loss_ledger_required` is `conditional` and the registered predicate is false, a missing ledger passes. |
| 573 | `test_active_trigger_demands_ledger` | Predicate | When the same contract's predicate is true, a missing ledger is a refusal. |
| 574 | `test_sealed_ledger_digest_tracks_erased_attributes` | Ledger payload | Changing `erased_attributes` changes the sealed ledger digest. |
| 575 | `test_parser_preserves_declared_trigger_id` | Registry | Parsing a contract with `loss_ledger_required: conditional` and `loss_ledger_trigger_id: gtmur.unmapped_field_drop` returns that id unchanged. A missing id stays null, and the conditional check then refuses. |

---

## 29. Tranche 30: Pseudometric Separation & Quotient Factors (Tests 576–595)

**Status:** Planned. No module and no execution receipt.  
Target Module: `omega_engine_governance/tests/normal_forms/test_tranche30_pseudometric_and_quotient_factors.py`  
Aligned Contracts: `nf.epistemic.odnf`, `nf.coda.eqnf`, `nf.transport.gtmur`

Distance zero is a pseudometric fact. Point equality is claimed only after a declared separation axiom. Quotient distance is the $L_1$ distance on the quotient, and a factor through the quotient is unique on the declared kernel.

| # | Test Identifier | Category | Target Invariant & Scope |
|---|---|---|---|
| 576 | `test_pseudometric_zero_keeps_distinct_ids` | Pseudometric | Two observer states with $d(O_1, O_2) = 0$ retain distinct identifiers when no separation axiom is declared. |
| 577 | `test_equality_requires_separation_axiom` | Pseudometric | A collapse of those states to one point is refused until the contract declares a separation axiom. |
| 578 | `test_odnf_zero_divergence_routes_to_abstain` | ODNF | ODNF distance zero, with separation undeclared, routes to `Abstain`. |
| 579 | `test_positive_pseudometric_blocks_collapse` | Pseudometric | $d(O_1, O_2) = 1/2$ refuses a collapse receipt. |
| 580 | `test_pseudometric_nonnegative` | Pseudometric | Every evaluated pair returns $d \ge 0$ as an exact rational. |
| 581 | `test_pseudometric_symmetric` | Pseudometric | $d(a, b) = d(b, a)$ on the fixture pairs. |
| 582 | `test_pseudometric_triangle_inequality` | Pseudometric | $d(a, c) \le d(a, b) + d(b, c)$ on the fixture triple, with exact rational addition. |
| 583 | `test_separation_axiom_makes_zero_into_equality` | Pseudometric | After the contract declares separation, $d(a, b) = 0$ yields $a = b$ in the quotient of the pseudometric. |
| 584 | `test_l1_quotient_distance_is_the_reported_distance` | Quotient | The reported distance is the $L_1$ distance between quotient classes, computed from class representatives. |
| 585 | `test_kernel_inclusion_checked_before_factor` | Quotient | A map factors through the quotient only when the declared kernel sits inside the map's kernel. |
| 586 | `test_factor_missing_a_kernel_pair_refused` | Quotient | A candidate factor that separates two kernel-equivalent representatives is refused. |
| 587 | `test_universal_factor_unique_on_classes` | Quotient | Two factors that agree on every quotient class are recorded as the same factor. |
| 588 | `test_second_factor_disagreement_refused` | Quotient | A second factor that disagrees on one class is refused as a universal factor. |
| 589 | `test_quotient_identifies_only_the_declared_kernel` | Quotient | Representatives outside the declared kernel remain distinct classes. |
| 590 | `test_nontrivial_class_is_not_a_point_equality_claim` | Quotient | A class with two representatives is reported as one quotient point and two carrier points. |
| 591 | `test_eqnf_unverified_quotient_refuses_preserve` | EQNF | An EQNF quotient whose verification status is `absent` refuses `Preserve`. |
| 592 | `test_gtmur_unmapped_field_opens_loss_ledger` | GTMUR | Dropping an unmapped field opens a loss-ledger entry bound to `gtmur.unmapped_field_drop`. |
| 593 | `test_gtmur_mapped_roundtrip_preserves_payload` | GTMUR | A payload whose fields are all in the declared map round-trips to the same canonical bytes. |
| 594 | `test_certificate_does_not_supply_separation` | Pseudometric | Attaching a distance certificate leaves the separation axiom unset. Zero distance still withholds point equality. |
| 595 | `test_two_representatives_at_quotient_distance_zero` | Quotient | Two distinct representatives of one class have quotient distance zero and unequal carrier ids. |

---

## 30. Tranche 31: Operational Pipeline & Terminal Routes (Tests 596–615)

**Status:** Planned. No module and no execution receipt.  
Target Module: `omega_engine_governance/tests/normal_forms/test_tranche31_operational_pipeline_and_terminal_routes.py`  
Aligned Contracts: `nf.epistemic.authority`, `nf.evidence.certificate`, `nf.evidence.ddanf`, `nf.coda.eqnf`

The operational harness runs `route`, then `descend`, then `verify`, then `terminalize`, and stops at the first refusal. `GuardEvidence` is read from that trace. Caller-supplied booleans are `GuardAttestations` and stay on the attestation side of the boundary.

| # | Test Identifier | Category | Target Invariant & Scope |
|---|---|---|---|
| 596 | `test_stages_run_in_route_descend_verify_terminalize_order` | Pipeline | A clean fixture records the four stage names in that order in the serialized trace. |
| 597 | `test_route_refusal_skips_later_stages` | Pipeline | A refusal from `route` leaves `descend`, `verify`, and `terminalize` absent from the trace. |
| 598 | `test_descend_refusal_skips_verify_and_terminalize` | Pipeline | A refusal from `descend` leaves `verify` and `terminalize` absent from the trace. |
| 599 | `test_verify_refusal_skips_terminalize` | Pipeline | A refusal from `verify` leaves `terminalize` absent from the trace. |
| 600 | `test_trace_lists_each_executed_stage` | Pipeline | The trace entries are exactly the stages that ran, each with its input digest and output digest. |
| 601 | `test_trace_sha256_binds_canonical_json` | Pipeline | The receipt digest equals the SHA-256 of the RFC 8785 canonical JSON of the trace. |
| 602 | `test_mutated_trace_byte_fails_digest` | Pipeline | Flipping one byte of the canonical trace makes the stored digest fail recomputation. |
| 603 | `test_guard_evidence_is_read_from_the_trace` | Evidence | `GuardEvidence` fields match the stage outputs in the trace and are absent when the stage did not run. |
| 604 | `test_caller_true_without_trace_refuses_preserve` | Attestation | A caller attestation `verified: true` with no trace refuses `Preserve`. |
| 605 | `test_attestation_input_type_is_guard_attestations` | Attestation | The policy-evaluator entry point accepts `GuardAttestations` and refuses a payload typed as `GuardEvidence` when no trace is attached. |
| 606 | `test_policy_evaluator_receipt_names_attestation_boundary` | Attestation | The attestation receipt states that the evaluator judges caller-supplied attestations and records no pipeline execution. |
| 607 | `test_observed_no_mixed_fiber_routes_to_abstain` | Terminal route | Evidence label `ObservedNoMixedFiberInCorpus` routes to `Abstain`. |
| 608 | `test_claimed_view_determinate_routes_to_abstain` | Terminal route | Evidence label `ClaimedViewDeterminate` routes to `Abstain`. |
| 609 | `test_preserve_requires_machine_checked_and_verifier` | Terminal route | `Preserve` is emitted when `verification_status` is `machine_checked` and `verifier_required` is `True`. |
| 610 | `test_preserve_refused_when_verifier_required_is_false` | Terminal route | `verification_status: machine_checked` with `verifier_required: False` refuses `Preserve`. |
| 611 | `test_preserve_refused_when_verification_status_absent` | Terminal route | `verifier_required: True` with `verification_status: absent` refuses `Preserve`. |
| 612 | `test_count_only_coverage_is_labeled_count_coverage` | Exhaustiveness | A packet that supplies counts and no candidate ids is labeled count coverage. |
| 613 | `test_count_coverage_does_not_emit_exhaustive` | Exhaustiveness | The count-coverage label is refused as an `exhaustive` guard result. |
| 614 | `test_replay_of_trace_reproduces_terminal` | Replay | Re-executing the stored trace yields the same terminal and the same SHA-256 digest. |
| 615 | `test_first_refusal_is_the_recorded_terminal` | Pipeline | When `descend` refuses, the recorded terminal is that refusal, and later stage names do not appear. |

---
