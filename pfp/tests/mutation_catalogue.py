"""The Symbol Game's mutants, declared so a third party can replay them.

Every claim of the form "N mutants, N killed" made about this module during the
2026-09-01..03 sprint is reconstructed here as a record, because the claims
themselves did not meet the estate's own standard. From
`techne-mutation-evidence-custody`:

    A mutation count is a claim about work nobody can repeat. A mutation table
    is evidence. Quote the table or quote nothing.

Those runs reported a label and a failure *count*. They named no failing test,
carried no restore proof, and executed from scripts in a scratch directory that
no longer exists. Under the law above they were candidates. This file, plus
`mutation_harness.py`, is what turns them into evidence -- and the replay is
what actually establishes them, not this docstring.

What belongs here
-----------------

A mutant per **decision**, not per line. The `intent` field says what would be
true of the system if the mutation survived, because that is what a reader needs
in order to judge whether the kill means anything. "Changed <= to ==" is the
`applied` field and tells a reader nothing.

Anchors drift. A mutant whose anchor no longer matches exactly once is a **setup
failure, not a result**, and `test_mutation_catalogue.py` fails fast on it so the
drift surfaces the moment the code moves rather than at the next audit.

AuthorityEffect: None.
"""

from __future__ import annotations

from operations.use_cases.verification.mutation_harness import Mutant

__all__ = ["DEFAULT_RUNNER", "DEFAULT_TESTS", "EXCLUDE_FROM_RUNS", "MUTANTS"]

#: Dropped from every mutated run. `test_mutation_catalogue.py` asserts that
#: each anchor matches exactly once, and while a mutant is APPLIED its anchor is
#: gone by construction -- so left in, it fails on every run and witnesses every
#: mutation. A genuinely surviving mutant would then be reported as killed by
#: the harness's own bookkeeping. A harness must not be a witness in its own
#: experiment.
EXCLUDE_FROM_RUNS = ("pfp/tests/test_mutation_catalogue.py",)

DEFAULT_RUNNER = "pytest"

#: The whole Python suite for this bounded context, named explicitly and sorted.
#: The harness runs it in deterministic batches of at most three files, as the
#: repository test-execution law requires. Deliberately not a narrow per-mutant
#: selection: choosing the tests most likely to fail is how a table comes to
#: describe the author's confidence rather than the suite's power.
#:
#: `test_mutation_catalogue.py` is excluded because its anchor assertions would
#: witness the harness's own experiment. It remains named in EXCLUDE_FROM_RUNS
#: above as the machine-readable reason for that omission.
DEFAULT_TESTS = (
    'pfp/tests/test_adversarial_challenger_1_rust_exact_ffi.py',
    'pfp/tests/test_adversarial_m1_challenger.py',
    'pfp/tests/test_adversarial_m5_challenger_2.py',
    'pfp/tests/test_architecture_fitness.py',
    'pfp/tests/test_arms_harness.py',
    'pfp/tests/test_bridge_fault_isolation.py',
    'pfp/tests/test_calculus_receipt.py',
    'pfp/tests/test_canonical_claims.py',
    'pfp/tests/test_canonical_stage_execution.py',
    'pfp/tests/test_carrier_decoding.py',
    'pfp/tests/test_cec_bridge_unavailable.py',
    'pfp/tests/test_cemetery_sink.py',
    'pfp/tests/test_certified_ladder_evaluator.py',
    'pfp/tests/test_challenge_cli.py',
    'pfp/tests/test_challenge_learning.py',
    'pfp/tests/test_cochain_gradient_simplicial_k6.py',
    'pfp/tests/test_code_change_gates_stage.py',
    'pfp/tests/test_code_change_repository_port.py',
    'pfp/tests/test_code_change_session_integrity.py',
    'pfp/tests/test_code_change_submit_stage.py',
    'pfp/tests/test_cohomology_certificate_fail_closed.py',
    'pfp/tests/test_complex_face_boundaries.py',
    'pfp/tests/test_cot_miner.py',
    'pfp/tests/test_cycle_balance_ddd.py',
    'pfp/tests/test_ddc_functional_boundary.py',
    'pfp/tests/test_ddc_visualization_adapter.py',
    'pfp/tests/test_decode_controls.py',
    'pfp/tests/test_demo_004_execution.py',
    'pfp/tests/test_demo_3_live_receipt.py',
    'pfp/tests/test_demo_live_receipt.py',
    'pfp/tests/test_demo_registry_closure.py',
    'pfp/tests/test_diff_parser_multifile.py',
    'pfp/tests/test_dimension_register_models.py',
    'pfp/tests/test_discrete_channel_token_witnesses.py',
    'pfp/tests/test_dispatch_crash_durability.py',
    'pfp/tests/test_documentation_strategy_doors.py',
    'pfp/tests/test_documented_numbers_are_current.py',
    'pfp/tests/test_domain_layer_purity.py',
    'pfp/tests/test_domain_value_objects.py',
    'pfp/tests/test_exact.py',
    'pfp/tests/test_exact_functional_port.py',
    'pfp/tests/test_execution_trace.py',
    'pfp/tests/test_extensional_task_ingress.py',
    'pfp/tests/test_fail_closed_negative_mutations.py',
    'pfp/tests/test_ffi_ddc_payload.py',
    'pfp/tests/test_ffi_seam_isolation.py',
    'pfp/tests/test_file_run_recorder.py',
    'pfp/tests/test_finite_gauge_workbench.py',
    'pfp/tests/test_functional_boundary.py',
    'pfp/tests/test_glyph_calculus.py',
    'pfp/tests/test_host_cli_seam.py',
    'pfp/tests/test_immune_defect_regressions.py',
    'pfp/tests/test_import_purity_and_candidate_identity.py',
    'pfp/tests/test_kinds_search.py',
    'pfp/tests/test_llm_turn_submission.py',
    'pfp/tests/test_local_process_sandbox.py',
    'pfp/tests/test_migration_fitness.py',
    'pfp/tests/test_mode_discovery.py',
    'pfp/tests/test_mode_trials.py',
    'pfp/tests/test_model_loading.py',
    'pfp/tests/test_mssn_catalog.py',
    'pfp/tests/test_named_native_refusals.py',
    'pfp/tests/test_native_scoring_migration.py',
    'pfp/tests/test_openrouter_seat_gateway.py',
    'pfp/tests/test_openrouter_seat_gateway_adversarial.py',
    'pfp/tests/test_openrouter_turn_executor.py',
    'pfp/tests/test_p0_baseline.py',
    'pfp/tests/test_p0_evidence_integrity.py',
    'pfp/tests/test_packet_contracts.py',
    'pfp/tests/test_pfp_aggregates.py',
    'pfp/tests/test_pfp_clean_arch.py',
    'pfp/tests/test_pfp_consolidation.py',
    'pfp/tests/test_pfp_domain_models.py',
    'pfp/tests/test_pfp_mode_additional_checks.py',
    'pfp/tests/test_pfp_mode_checks.py',
    'pfp/tests/test_pfp_package.py',
    'pfp/tests/test_pfp_pipeline_provider.py',
    'pfp/tests/test_pfp_relocation_paths.py',
    'pfp/tests/test_pfp_rop_results.py',
    'pfp/tests/test_pfp_runtime.py',
    'pfp/tests/test_pfp_runtime_migration.py',
    'pfp/tests/test_pfp_seed_cli.py',
    'pfp/tests/test_pfp_types_package.py',
    'pfp/tests/test_pfp_use_cases.py',
    'pfp/tests/test_pfp_value_objects.py',
    'pfp/tests/test_pilot_catalog_execution.py',
    'pfp/tests/test_pilot_models.py',
    'pfp/tests/test_pilot_relocation_alias.py',
    'pfp/tests/test_pilot_runner.py',
    'pfp/tests/test_pilot_scoured_types.py',
    'pfp/tests/test_pilot_suite.py',
    'pfp/tests/test_pilot_use_cases.py',
    'pfp/tests/test_po035_adaptive.py',
    'pfp/tests/test_po035_closeout.py',
    'pfp/tests/test_po035_derivation_runtime.py',
    'pfp/tests/test_po035_stage_replay.py',
    'pfp/tests/test_presentation_pins.py',
    'pfp/tests/test_prompt_representations.py',
    'pfp/tests/test_provider_dispatch_durability.py',
    'pfp/tests/test_research_replay_authority.py',
    'pfp/tests/test_research_use_case_imports.py',
    'pfp/tests/test_residue_parity.py',
    'pfp/tests/test_retraction_fail_closed.py',
    'pfp/tests/test_retraction_turn_loop.py',
    'pfp/tests/test_row_rederivation.py',
    'pfp/tests/test_sbe_quantum_bridge.py',
    'pfp/tests/test_schema_validator.py',
    'pfp/tests/test_seed_advanced_checks.py',
    'pfp/tests/test_seed_core_checks.py',
    'pfp/tests/test_seed_exact_checks.py',
    'pfp/tests/test_sign_switching_native_transport.py',
    'pfp/tests/test_simplicial_boundary_matrix.py',
    'pfp/tests/test_swarm_developer.py',
    'pfp/tests/test_swarm_reply_control_native.py',
    'pfp/tests/test_symbol_game.py',
    'pfp/tests/test_symbol_game_clean_architecture_domain_coverage.py',
    'pfp/tests/test_symbol_game_cli.py',
    'pfp/tests/test_symbol_game_controllers_promoted.py',
    'pfp/tests/test_symbol_game_core_infra_promoted.py',
    'pfp/tests/test_symbol_game_deepening.py',
    'pfp/tests/test_symbol_game_domain_promoted.py',
    'pfp/tests/test_symbol_game_e2e_multi_act_bout.py',
    'pfp/tests/test_symbol_game_event_driven.py',
    'pfp/tests/test_symbol_game_ffi.py',
    'pfp/tests/test_symbol_game_master_mutation_battery.py',
    'pfp/tests/test_symbol_game_pr_workflow.py',
    'pfp/tests/test_symbol_game_release_gate.py',
    'pfp/tests/test_symbol_game_rop_result.py',
    'pfp/tests/test_three_layer_sovereignty.py',
    'pfp/tests/test_traced_code_change.py',
    'pfp/tests/test_turn_driver_controller.py',
    'pfp/tests/test_unbound_solver_ports.py',
    'pfp/tests/test_uns_emitter_custody.py',
    'pfp/tests/test_verify_glyph_reply.py',
    'pfp/tests/test_wp6_expectation_corpus.py',
)

#: The Rust workspace root. `cargo` cannot be invoked from the repository root.
_CRATES = "engine/crates_rs"

#: Inherit the ambient toolchain; the repository build policy forbids pinning
#: a channel in the command. Keep one package, serial compilation, and lib tests.
_RUNTIME_LIB = (
    "test",
    "-j",
    "1",
    "-p",
    "core_symbol_game_runtime",
    "--lib",
)


MUTANTS: list[Mutant] = [
    # ------------------------------------------------------------------
    # Presentation pinning (Rust). Commit 46b77abc55.
    # ------------------------------------------------------------------
    Mutant(
        mutant_id="M01",
        intent=(
            "A producer could defeat a host pin by shuffling the rules in its "
            "payload, silently downgrading a pinned presentation to "
            "SELF_CONSISTENT_ONLY"
        ),
        target="engine/crates_rs/core_symbol_game_runtime/src/rewriting/peak.rs",
        anchor="    rules.sort_unstable();\n",
        applied="    // MUTANT M01: the sort that makes the digest name the system\n",
        runner="cargo",
        tests=_RUNTIME_LIB,
        cwd=_CRATES,
    ),
    Mutant(
        mutant_id="M02",
        intent=(
            "Every peak verdict would report SELF_CONSISTENT_ONLY, including "
            "NeedsEvidence -- claiming consistency for a run that decided nothing"
        ),
        target="engine/crates_rs/core_symbol_game_runtime/src/rewriting/peak.rs",
        anchor=(
            "        if self.decides() && matches!(self.authority, "
            "PresentationAuthority::ProducerDeclared) {"
        ),
        applied=(
            "        if matches!(self.authority, "
            "PresentationAuthority::ProducerDeclared) {"
        ),
        runner="cargo",
        tests=_RUNTIME_LIB,
        cwd=_CRATES,
    ),
    Mutant(
        mutant_id="M03",
        intent=(
            "A join decided under rules the producer supplied would read as "
            "JOINED -- the defect the whole pinning mechanism exists to close"
        ),
        target="engine/crates_rs/core_symbol_game_runtime/src/rewriting/peak.rs",
        anchor=(
            "        if self.decides() && matches!(self.authority, "
            "PresentationAuthority::ProducerDeclared) {\n"
            "            return TOKEN_SELF_CONSISTENT_ONLY;\n"
            "        }\n"
        ),
        applied="",
        runner="cargo",
        tests=_RUNTIME_LIB,
        cwd=_CRATES,
    ),
    # ------------------------------------------------------------------
    # RoundRecord's seal-only fence (Rust). Commit 1884dc582b.
    # ------------------------------------------------------------------
    Mutant(
        mutant_id="M04",
        intent=(
            "serde would rebuild a RoundRecord field by field and accept a "
            "caller-supplied canonical_digest, making a model-authored receipt "
            "hash constructible -- which the type's own doc calls impossible"
        ),
        target="engine/crates_rs/core_symbol_game_runtime/src/packets.rs",
        anchor="#[derive(Debug, Clone, PartialEq, Eq, Serialize)]\npub struct RoundRecord {",
        applied=(
            "#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]\n"
            "pub struct RoundRecord {"
        ),
        runner="cargo",
        tests=_RUNTIME_LIB,
        cwd=_CRATES,
    ),
    # ------------------------------------------------------------------
    # Carrier authorship (Python). Commit 207a58b35b.
    # ------------------------------------------------------------------
    Mutant(
        mutant_id="M05",
        intent=(
            "A packet that declared its own carrier could reach PASS, so a "
            "producer wanting a clean receipt need only widen its carrier"
        ),
        target="pfp/domain/calculus_receipt.py",
        anchor=(
            "        if self.carrier_authored_by is CarrierAuthority.PRODUCER:\n"
            "            # Every row re-derived against an allowlist the packet wrote. The\n"
            "            # rows agree with the carrier and the carrier agrees with the rows;\n"
            "            # a producer wanting this outcome need only widen its carrier.\n"
            "            return Terminal.SELF_CONSISTENT_ONLY\n"
            "        return Terminal.PASS\n"
        ),
        applied="        return Terminal.PASS\n",
    ),
    Mutant(
        mutant_id="M06",
        intent=(
            "No run could ever reach PASS, so a host that really did pin its "
            "carrier would be silently capped at SELF_CONSISTENT_ONLY"
        ),
        target="pfp/domain/calculus_receipt.py",
        anchor=(
            "        if self.carrier_authored_by is CarrierAuthority.PRODUCER:\n"
            "            # Every row re-derived against an allowlist the packet wrote. The\n"
            "            # rows agree with the carrier and the carrier agrees with the rows;\n"
            "            # a producer wanting this outcome need only widen its carrier.\n"
            "            return Terminal.SELF_CONSISTENT_ONLY\n"
            "        return Terminal.PASS\n"
        ),
        applied="        return Terminal.SELF_CONSISTENT_ONLY\n",
    ),
    Mutant(
        mutant_id="M07",
        intent=(
            "A run with unchecked rows would report SELF_CONSISTENT_ONLY, "
            "claiming consistency over rows the host never looked at"
        ),
        target="pfp/domain/calculus_receipt.py",
        anchor="        if any(row.outcome is RowOutcome.UNCHECKABLE for row in self.rows):",
        applied=(
            "        if self.carrier_authored_by is CarrierAuthority.PRODUCER:\n"
            "            return Terminal.SELF_CONSISTENT_ONLY\n"
            "        if any(row.outcome is RowOutcome.UNCHECKABLE for row in self.rows):"
        ),
    ),
    Mutant(
        mutant_id="M08",
        intent=(
            "Carrier authorship would default UP, handing every caller that "
            "brought no carrier of its own a PASS it did not earn"
        ),
        target="pfp/use_cases/verify_glyph_reply.py",
        anchor="    authored_by = CarrierAuthority.PRODUCER\n",
        applied="    authored_by = CarrierAuthority.HOST\n",
    ),
    Mutant(
        mutant_id="M09",
        intent=(
            "A packet declaring any carrier would be accepted as host-authored "
            "without the digests ever being compared"
        ),
        target="pfp/use_cases/verify_glyph_reply.py",
        anchor="        if declared != pinned:\n",
        applied="        if False:\n",
    ),
    # ------------------------------------------------------------------
    # The op predicate (Python). Commit c5543a841a.
    # ------------------------------------------------------------------
    Mutant(
        mutant_id="M10",
        intent=(
            "The closed op set would be matched case-insensitively, which is a "
            "different and larger set; 'prove x' would lint clean and then be "
            "rejected by ReceiptRow, raising out of the use case"
        ),
        target="pfp/domain/glyph_calculus.py",
        anchor="    if token not in CLOSED_OPS:\n",
        applied="    if token.upper() not in CLOSED_OPS:\n",
    ),
    # ------------------------------------------------------------------
    # The modular decider (Python). Commit 28131384ae.
    # ------------------------------------------------------------------
    Mutant(
        mutant_id="M11",
        intent=(
            "mod would use the C-family truncating remainder, so -17 mod 5 = -2 "
            "and this host would disagree with its own cyclic-group semantics"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor="    host_value = lhs % modulus\n",
        applied="    host_value = abs(lhs) % modulus * (1 if lhs >= 0 else -1)\n",
    ),
    Mutant(
        mutant_id="M12",
        intent=(
            "A ZeroDivisionError would escape the use case on `17 mod 0`; a "
            "crash is not a terminal"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor="    if modulus <= 0:\n",
        applied="    if False:\n",
    ),
    Mutant(
        mutant_id="M13",
        intent=(
            "A negative modulus would be treated as a cyclic group order, and "
            "Python's sign-following % would answer a question nobody asked"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor="    if modulus <= 0:\n",
        applied="    if modulus == 0:\n",
    ),
    Mutant(
        mutant_id="M14",
        intent=(
            "`17 MOD 5 = 99` would be filed as UNCHECKABLE, letting a false "
            "claim escape the hallucination count on a capitalisation"
        ),
        target="pfp/domain/row_rederivation.py",
        # Anchored on the modular pattern's own closing line. Bare
        # `re.IGNORECASE,` matched three regexes once `period` and `successor`
        # landed, and `test_mutation_catalogue` failed on the ambiguity the
        # same minute -- an anchor matching many times is a setup failure, not
        # a result.
        anchor=('(?P<claimed>[+-]?\\d+)$",\n    re.IGNORECASE,\n'),
        applied=('(?P<claimed>[+-]?\\d+)$",\n    0,\n'),
    ),
    Mutant(
        mutant_id="M15",
        intent=(
            "`REDUCE 17 mod 5 = 2 and pigs fly` would re-derive clean, and the "
            "trailing claim would ride out on the arithmetic"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor=r'\s*=\s*(?P<claimed>[+-]?\d+)$"',
        applied=r'\s*=\s*(?P<claimed>[+-]?\d+)"',
    ),
    Mutant(
        mutant_id="M16",
        intent=(
            "A disagreement would be reported as a blind spot, so the "
            "hallucination count would stay structurally zero and read as a "
            "clean bill of health"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor=(
            "    return Derivation(\n"
            "        RowOutcome.CONTRADICTED,\n"
            "        host_value=str(host_value),\n"
        ),
        applied=(
            "    return Derivation(\n"
            "        RowOutcome.UNCHECKABLE,\n"
            "        missing_fields=(BLIND_SPOT_NO_DECIDER,),\n"
        ),
    ),
    Mutant(
        mutant_id="M17",
        intent=(
            "A claim with no truth value would be charged to the producer as a "
            "contradiction, inflating the count with the host's own admission "
            "policy"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor=(
            "            RowOutcome.REFUSED,\n"
            "            refusal_code=REFUSAL_STATEMENT_ILL_FORMED,\n"
        ),
        applied=(
            "            RowOutcome.CONTRADICTED,\n"
            "            host_value=str(modulus),\n"
        ),
    ),
    Mutant(
        mutant_id="M18",
        intent=(
            "Deciding would be keyed on the row's op rather than the "
            "statement's form, so what the host can compute would depend on "
            "what the producer called it"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor="    body = statement_body(sentence)\n",
        applied=(
            "    body = statement_body(sentence) "
            "if sentence.strip().startswith('REDUCE') else ''\n"
        ),
    ),
    # ------------------------------------------------------------------
    # The referential deciders: period(NAME) and successor^k. Commit 2026-09-03.
    # ------------------------------------------------------------------
    Mutant(
        mutant_id="M19",
        intent=(
            "period(NAME) would fall back to whatever single presentation "
            "happens to be pinned, so the host would answer about c5 a question "
            "asked about c7 -- guessing the SUBJECT of the sentence it claims "
            "to have verified"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor="    presentation = context.pins.resolve(name)\n",
        applied=(
            "    presentation = context.pins.resolve(name) or (\n"
            "        context.pins.resolve(context.pins.names[0])\n"
            "        if context.pins.names\n"
            "        else None\n"
            "    )\n"
        ),
    ),
    Mutant(
        mutant_id="M20",
        intent=(
            "period would report the SIZE of the signature instead of the ORDER "
            "of the permutation -- right for c5, and wrong for any presentation "
            "with two orbits"
        ),
        target="pfp/domain/presentation_pins.py",
        anchor="        return order\n",
        applied="        return len(self.signature)\n",
    ),
    Mutant(
        mutant_id="M21",
        intent=(
            "the totality check would be removed from successor_map. Declared "
            "EQUIVALENT: it changes no observable behaviour, because the ONTO "
            "check two lines below already implies totality. Keys are distinct "
            "and drawn from the signature, so |keys| <= |symbols|; and "
            "set(values) == symbols forces |keys| >= |symbols|. Verified "
            "exhaustively over every mapping on signatures of size 1..5 (8476 "
            "cases, zero counterexamples), and pinned by "
            "test_the_totality_check_is_redundant_given_the_onto_check. The "
            "check is kept because it states the intent directly, and this "
            "mutant is kept so that if the onto check is ever weakened, M21 "
            "starts failing as declared-equivalent-but-killed and says so"
        ),
        expectation="equivalent",
        target="pfp/domain/presentation_pins.py",
        anchor="        if set(mapping) != symbols:\n            return None\n",
        applied="        if False:\n            return None\n",
    ),
    Mutant(
        mutant_id="M22",
        intent=(
            "carrier symbol names would be matched case-insensitively, so the "
            "host would answer about a symbol the row did not name -- a carrier "
            "may legitimately declare `alpha` and `Alpha` as two members"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor="        if member.symbol == token:\n",
        applied="        if member.symbol.lower() == token.lower():\n",
    ),
    Mutant(
        mutant_id="M23",
        intent=(
            "a host_value would carry the raw glyph, turning a receipt printed "
            "on a cp1252 console into a UnicodeEncodeError -- a crash instead of "
            "a finding"
        ),
        target="pfp/domain/row_rederivation.py",
        anchor="            return member.symbol\n",
        applied="            return glyph\n",
    ),
]
