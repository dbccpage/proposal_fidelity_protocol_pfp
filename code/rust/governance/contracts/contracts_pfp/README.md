# Symbol Game packet contract index

**AuthorityEffect:** None. This page names files and quotes their `title` or `status` fields. It does not certify a contract, promote a status, or merge homes.

## Two homes

The documentation strategy named `contracts_packets/symbol_game/` and
`contracts_crates/symbol_game/`, and left merging them as an
open author decision. Neither directory is on disk. This page does not
create them, does not move files, and does not merge homes.

This directory, `contracts_pfp/`, is the corpus that is present.
Excluding this README, it holds 161 files: 160 `*.contract.yaml` files and
`UNCONTRACTED.md`. The catalog below indexes those 161 files. The strategy
figure of 145 is not this listing.

The product-boundary file in this directory is
[symbol_game.contract.yaml](symbol_game.contract.yaml). Its `status` field
is `mathematical_wip`. The same directory holds
[llm_symbol_game_interface.contract.yaml](llm_symbol_game_interface.contract.yaml),
also `kind: product_contract`, also `status: mathematical_wip`.

## Where the packet files are

Python packet checks read this directory when it exists, and otherwise
the absent fallback `contracts_packets/symbol_game/`. The check lives in
[test_packet_contracts.py](../../../pfp/tests/test_packet_contracts.py).
This directory exists, so that fallback is unused. A listing excluding this
README has 161 files, and the catalog indexes those 161. This README is not
one of them.

Of the 160 YAML files, 158 have `kind: packet_contract`, `layer: 40_packets`, and `status: active`. The other two are the product contracts named above (`kind: product_contract`, `layer: 07_products`).

Each purpose is that file's YAML `title`, or the first heading of `UNCONTRACTED.md`.

## Catalog

### Product contracts

| File | Purpose |
| --- | --- |
| [llm_symbol_game_interface.contract.yaml](llm_symbol_game_interface.contract.yaml) | LLMSymbolGameInterface (`status: mathematical_wip`) |
| [symbol_game.contract.yaml](symbol_game.contract.yaml) | SymbolGame (`status: mathematical_wip`) |

### Packet contracts: `budget*`

| File | Purpose |
| --- | --- |
| [budget.contract.yaml](budget.contract.yaml) | Budget |
| [budget_summary_v1.contract.yaml](budget_summary_v1.contract.yaml) | Budget Summary v1 |

### Packet contracts: `candidate_*`

| File | Purpose |
| --- | --- |
| [candidate_artifact_v1.contract.yaml](candidate_artifact_v1.contract.yaml) | Candidate Artifact v1 |
| [candidate_binding_v1.contract.yaml](candidate_binding_v1.contract.yaml) | Candidate Binding v1 |
| [candidate_fingerprint.contract.yaml](candidate_fingerprint.contract.yaml) | Candidate Fingerprint |
| [candidate_move_packet.contract.yaml](candidate_move_packet.contract.yaml) | Candidate Move Packet |
| [candidate_proposal.contract.yaml](candidate_proposal.contract.yaml) | Candidate Proposal |
| [candidate_relation_v1.contract.yaml](candidate_relation_v1.contract.yaml) | Candidate Relation v1 |
| [candidate_turn.contract.yaml](candidate_turn.contract.yaml) | Candidate Turn |

### Packet contracts: `carrier_*`

| File | Purpose |
| --- | --- |
| [carrier_input_v1.contract.yaml](carrier_input_v1.contract.yaml) | Carrier Input v1 |
| [carrier_manifest_summary_v1.contract.yaml](carrier_manifest_summary_v1.contract.yaml) | Carrier Manifest Summary v1 |

### Packet contracts: `citation*`

| File | Purpose |
| --- | --- |
| [citation.contract.yaml](citation.contract.yaml) | Citation |
| [citation_role.contract.yaml](citation_role.contract.yaml) | Citation Role |

### Packet contracts: `code_change_*`

| File | Purpose |
| --- | --- |
| [code_change_patch_artifact_v1.contract.yaml](code_change_patch_artifact_v1.contract.yaml) | Code Change Patch Artifact v1 |
| [code_change_proposal_payload_v1.contract.yaml](code_change_proposal_payload_v1.contract.yaml) | Code Change Proposal Payload v1 |
| [code_change_run_root_v1.contract.yaml](code_change_run_root_v1.contract.yaml) | Code Change Run Root v1 |

### Packet contracts: `critical_*`

| File | Purpose |
| --- | --- |
| [critical_pair.contract.yaml](critical_pair.contract.yaml) | Host-Derived Critical Pair |
| [critical_peak_claim.contract.yaml](critical_peak_claim.contract.yaml) | Claimed Critical Peak |

### Packet contracts: `curvature_*`

| File | Purpose |
| --- | --- |
| [curvature_kind.contract.yaml](curvature_kind.contract.yaml) | Curvature Kind |
| [curvature_profile.contract.yaml](curvature_profile.contract.yaml) | Curvature Profile |
| [curvature_receipt_v1.contract.yaml](curvature_receipt_v1.contract.yaml) | Curvature Receipt V1 |

### Packet contracts: `exact_*`

| File | Purpose |
| --- | --- |
| [exact_rational_wire_v1.contract.yaml](exact_rational_wire_v1.contract.yaml) | Exact Rational Wire v1 |
| [exact_stage_summary_v1.contract.yaml](exact_stage_summary_v1.contract.yaml) | Exact Stage Summary v1 |

### Packet contracts: `gauge_*`

| File | Purpose |
| --- | --- |
| [gauge_board.contract.yaml](gauge_board.contract.yaml) | Gauge Board |
| [gauge_verdict.contract.yaml](gauge_verdict.contract.yaml) | Gauge Verdict |

### Packet contracts: `glyph_*`

| File | Purpose |
| --- | --- |
| [glyph_game.contract.yaml](glyph_game.contract.yaml) | Glyph Game |
| [glyph_registry.contract.yaml](glyph_registry.contract.yaml) | Glyph Registry |

### Packet contracts: `grammar_*`

| File | Purpose |
| --- | --- |
| [grammar_spec.contract.yaml](grammar_spec.contract.yaml) | Grammar Spec |
| [grammar_termination_receipt_v1.contract.yaml](grammar_termination_receipt_v1.contract.yaml) | Grammar Termination Receipt V1 |

### Packet contracts: `guard_*`

| File | Purpose |
| --- | --- |
| [guard_compilation_receipt_v1.contract.yaml](guard_compilation_receipt_v1.contract.yaml) | Guard Compilation Receipt V1 |
| [guard_scope.contract.yaml](guard_scope.contract.yaml) | Guard Scope |

### Packet contracts: `host_*`

| File | Purpose |
| --- | --- |
| [host_admission_summary.contract.yaml](host_admission_summary.contract.yaml) | Admission Summary (Host Wire) |
| [host_budgets_v1.contract.yaml](host_budgets_v1.contract.yaml) | Host Budgets v1 |
| [host_carrier_declaration.contract.yaml](host_carrier_declaration.contract.yaml) | Carrier Declaration (Host Wire) |
| [host_carrier_edge_wire.contract.yaml](host_carrier_edge_wire.contract.yaml) | Carrier Edge (Host Wire) |
| [host_description_v1.contract.yaml](host_description_v1.contract.yaml) | Host Description v1 |
| [host_outcome_v1.contract.yaml](host_outcome_v1.contract.yaml) | Host Outcome v1 |
| [host_permutation_order_evidence.contract.yaml](host_permutation_order_evidence.contract.yaml) | Exact permutation order evidence (native runtime) |
| [host_pinned_permutation_evaluation.contract.yaml](host_pinned_permutation_evaluation.contract.yaml) | Pinned permutation evaluation alternatives (native runtime) |
| [host_pinned_permutation_order_observation.contract.yaml](host_pinned_permutation_order_observation.contract.yaml) | Pinned permutation order observation (native runtime result) |
| [host_pinned_permutation_order_request.contract.yaml](host_pinned_permutation_order_request.contract.yaml) | Pinned permutation order request (native runtime payload) |
| [host_refusal_summary.contract.yaml](host_refusal_summary.contract.yaml) | Refusal Summary (Host Wire) |
| [host_request_v1.contract.yaml](host_request_v1.contract.yaml) | Host Request v1 |
| [host_runtime_outcome.contract.yaml](host_runtime_outcome.contract.yaml) | Runtime Outcome (Host Wire) |
| [host_runtime_request.contract.yaml](host_runtime_request.contract.yaml) | Runtime Request (Host Wire) |

### Packet contracts: `ooutwire_*`

| File | Purpose |
| --- | --- |
| [ooutwire_manifest.contract.yaml](ooutwire_manifest.contract.yaml) | Ooutwire Manifest |
| [ooutwire_record.contract.yaml](ooutwire_record.contract.yaml) | Ooutwire Record |
| [ooutwire_validation_receipt_v1.contract.yaml](ooutwire_validation_receipt_v1.contract.yaml) | Ooutwire Validation Receipt V1 |

### Packet contracts: `peak_*`

| File | Purpose |
| --- | --- |
| [peak_evaluation.contract.yaml](peak_evaluation.contract.yaml) | Critical Peak Evaluation |
| [peak_verdict.contract.yaml](peak_verdict.contract.yaml) | Critical Peak Verdict |

### Packet contracts: `presentation*`

| File | Purpose |
| --- | --- |
| [presentation.contract.yaml](presentation.contract.yaml) | Finite Rewrite Presentation |
| [presentation_authority.contract.yaml](presentation_authority.contract.yaml) | Presentation Authority |

### Packet contracts: `prime*`

| File | Purpose |
| --- | --- |
| [prime000_conformance_v1.contract.yaml](prime000_conformance_v1.contract.yaml) | Prime000 Conformance v1 |
| [prime000_summary_v1.contract.yaml](prime000_summary_v1.contract.yaml) | Prime000 Summary v1 |
| [prime001_summary_v1.contract.yaml](prime001_summary_v1.contract.yaml) | Prime001 Summary v1 |
| [prime002_profile_v1.contract.yaml](prime002_profile_v1.contract.yaml) | Prime002 Profile v1 |
| [prime002_summary_v1.contract.yaml](prime002_summary_v1.contract.yaml) | Prime002 Summary v1 |
| [prime_profiles_v1.contract.yaml](prime_profiles_v1.contract.yaml) | Prime Profiles v1 |

### Packet contracts: `py_*`

| File | Purpose |
| --- | --- |
| [py_calculus_receipt.contract.yaml](py_calculus_receipt.contract.yaml) | Calculus Receipt (Python) |
| [py_carrier.contract.yaml](py_carrier.contract.yaml) | Carrier (Python) |
| [py_carrier_authority.contract.yaml](py_carrier_authority.contract.yaml) | Carrier Authority (Python) |
| [py_carrier_member.contract.yaml](py_carrier_member.contract.yaml) | Carrier Member (Python) |
| [py_claim_kind.contract.yaml](py_claim_kind.contract.yaml) | Claim Kind (Python) |
| [py_constraint_mode.contract.yaml](py_constraint_mode.contract.yaml) | Decode Constraint Mode (Python) |
| [py_corpus_file_ref.contract.yaml](py_corpus_file_ref.contract.yaml) | Corpus File Reference (Python) |
| [py_decider_context.contract.yaml](py_decider_context.contract.yaml) | Decider Context (Python) |
| [py_decoding_receipt.contract.yaml](py_decoding_receipt.contract.yaml) | Decoding Receipt (Python) |
| [py_derivation.contract.yaml](py_derivation.contract.yaml) | Row Derivation (Python) |
| [py_evidence_ceiling.contract.yaml](py_evidence_ceiling.contract.yaml) | Evidence Ceiling (Python) |
| [py_finding.contract.yaml](py_finding.contract.yaml) | Refusal Finding (Python) |
| [py_frozen_corpus.contract.yaml](py_frozen_corpus.contract.yaml) | Frozen Research Corpus (Python) |
| [py_glyph_reply_verdict.contract.yaml](py_glyph_reply_verdict.contract.yaml) | Glyph Reply Verdict (Python) |
| [py_pinned_presentation.contract.yaml](py_pinned_presentation.contract.yaml) | Pinned Presentation (Python) |
| [py_pinned_rule.contract.yaml](py_pinned_rule.contract.yaml) | Pinned Rewrite Rule (Python) |
| [py_presentation_pins.contract.yaml](py_presentation_pins.contract.yaml) | Presentation Pin Registry (Python) |
| [py_receipt_row.contract.yaml](py_receipt_row.contract.yaml) | Calculus Receipt Row (Python) |
| [py_replay_trace_packet.contract.yaml](py_replay_trace_packet.contract.yaml) | Replay Trace Packet (Python) |
| [py_research_claim.contract.yaml](py_research_claim.contract.yaml) | Research Claim (Python) |
| [py_research_mode.contract.yaml](py_research_mode.contract.yaml) | Research Mode (Python) |
| [py_research_proposal.contract.yaml](py_research_proposal.contract.yaml) | Research Proposal Packet (Python) |
| [py_research_seed_packet.contract.yaml](py_research_seed_packet.contract.yaml) | Research Seed Packet (Python) |
| [py_research_step_packet.contract.yaml](py_research_step_packet.contract.yaml) | Research Step Packet (Python) |
| [py_row_outcome.contract.yaml](py_row_outcome.contract.yaml) | Row Outcome (Python) |
| [py_step_realization.contract.yaml](py_step_realization.contract.yaml) | Step Realization (Python) |
| [py_symbol_game_research_packet.contract.yaml](py_symbol_game_research_packet.contract.yaml) | Symbol Game Research Packet (Python) |
| [py_terminal.contract.yaml](py_terminal.contract.yaml) | Receipt Terminal (Python) |

### Packet contracts: `reduction_*`

| File | Purpose |
| --- | --- |
| [reduction_path.contract.yaml](reduction_path.contract.yaml) | Reduction Path |
| [reduction_step.contract.yaml](reduction_step.contract.yaml) | Rule Application At A Redex |

### Packet contracts: `register_*`

| File | Purpose |
| --- | --- |
| [register_envelope_v1.contract.yaml](register_envelope_v1.contract.yaml) | Register Envelope V1 |
| [register_value.contract.yaml](register_value.contract.yaml) | Register Value |

### Packet contracts: `residual_*`

| File | Purpose |
| --- | --- |
| [residual_drop_v1.contract.yaml](residual_drop_v1.contract.yaml) | Residual Drop v1 |
| [residual_input_v1.contract.yaml](residual_input_v1.contract.yaml) | Residual Input v1 |

### Packet contracts: `simplicial_*`

| File | Purpose |
| --- | --- |
| [simplicial_boundary_report.contract.yaml](simplicial_boundary_report.contract.yaml) | Simplicial Boundary Report |
| [simplicial_composition_record.contract.yaml](simplicial_composition_record.contract.yaml) | Simplicial Composition Record |

### Packet contracts: `source_*`

| File | Purpose |
| --- | --- |
| [source_artifact_v1.contract.yaml](source_artifact_v1.contract.yaml) | Source Artifact v1 |
| [source_binding_checks_v1.contract.yaml](source_binding_checks_v1.contract.yaml) | Source Binding Checks v1 |
| [source_bindings_v1.contract.yaml](source_bindings_v1.contract.yaml) | Source Bindings v1 |
| [source_intake_bundle_v1.contract.yaml](source_intake_bundle_v1.contract.yaml) | Source Intake Bundle v1 |
| [source_intake_receipt_v1.contract.yaml](source_intake_receipt_v1.contract.yaml) | Source Intake Receipt v1 |

### Packet contracts: `terminal_*`

| File | Purpose |
| --- | --- |
| [terminal_disposition.contract.yaml](terminal_disposition.contract.yaml) | Terminal Disposition |
| [terminal_proposal.contract.yaml](terminal_proposal.contract.yaml) | Terminal Proposal |

### Packet contracts: `token_*`

| File | Purpose |
| --- | --- |
| [token_distance.contract.yaml](token_distance.contract.yaml) | Token Distance |
| [token_frontier_receipt_v1.contract.yaml](token_frontier_receipt_v1.contract.yaml) | Token Frontier Receipt V1 |

### Packet contracts: other names

| File | Purpose |
| --- | --- |
| [act.contract.yaml](act.contract.yaml) | Act |
| [adapter_receipt_v1.contract.yaml](adapter_receipt_v1.contract.yaml) | Adapter Receipt V1 |
| [boundary_rule.contract.yaml](boundary_rule.contract.yaml) | Boundary Rule |
| [bytecode_execution_receipt_v1.contract.yaml](bytecode_execution_receipt_v1.contract.yaml) | Bytecode Execution Receipt V1 |
| [canary_report.contract.yaml](canary_report.contract.yaml) | Canary Report |
| [cemetery_record.contract.yaml](cemetery_record.contract.yaml) | Cemetery Record |
| [census_report.contract.yaml](census_report.contract.yaml) | Census Report |
| [claim.contract.yaml](claim.contract.yaml) | Claim |
| [coboundary_score_result.contract.yaml](coboundary_score_result.contract.yaml) | Coboundary Score Result |
| [coda_boundary_receipt_v1.contract.yaml](coda_boundary_receipt_v1.contract.yaml) | Coda Boundary Receipt V1 |
| [commitment_check_v1.contract.yaml](commitment_check_v1.contract.yaml) | Commitment Check v1 |
| [context_delimiters_v1.contract.yaml](context_delimiters_v1.contract.yaml) | Context Delimiters V1 |
| [corpus_state.contract.yaml](corpus_state.contract.yaml) | Corpus State |
| [defect_cartography.contract.yaml](defect_cartography.contract.yaml) | Defect Cartography |
| [demand_item_v1.contract.yaml](demand_item_v1.contract.yaml) | Demand Item v1 |
| [descent_triad.contract.yaml](descent_triad.contract.yaml) | Descent Triad |
| [disagreement_localization_receipt_v1.contract.yaml](disagreement_localization_receipt_v1.contract.yaml) | Disagreement Localization Receipt V1 |
| [disposition.contract.yaml](disposition.contract.yaml) | Disposition |
| [domain_census.contract.yaml](domain_census.contract.yaml) | Domain Census |
| [elimination_receipt_v1.contract.yaml](elimination_receipt_v1.contract.yaml) | Elimination Receipt v1 |
| [evidence.contract.yaml](evidence.contract.yaml) | Evidence |
| [exhaustion_basis.contract.yaml](exhaustion_basis.contract.yaml) | Exhaustion Basis |
| [f2_error.contract.yaml](f2_error.contract.yaml) | F2 Error |
| [fibration_rule.contract.yaml](fibration_rule.contract.yaml) | Fibration Rule |
| [finding.contract.yaml](finding.contract.yaml) | Finding |
| [formal_certificate.contract.yaml](formal_certificate.contract.yaml) | Formal Certificate |
| [frontier_state.contract.yaml](frontier_state.contract.yaml) | Frontier State |
| [gate_receipt_v1.contract.yaml](gate_receipt_v1.contract.yaml) | Gate Receipt v1 |
| [instruction.contract.yaml](instruction.contract.yaml) | Instruction |
| [kernel_primitive.contract.yaml](kernel_primitive.contract.yaml) | Kernel Primitive |
| [layer.contract.yaml](layer.contract.yaml) | Layer |
| [learned_guard.contract.yaml](learned_guard.contract.yaml) | Learned Guard |
| [library_custody_receipt_v1.contract.yaml](library_custody_receipt_v1.contract.yaml) | Library Custody Receipt V1 |
| [local_replay_status.contract.yaml](local_replay_status.contract.yaml) | Local Replay Status |
| [localization.contract.yaml](localization.contract.yaml) | Localization |
| [loss_ledger_v1.contract.yaml](loss_ledger_v1.contract.yaml) | Loss Ledger V1 |
| [meron_surgery_receipt_v1.contract.yaml](meron_surgery_receipt_v1.contract.yaml) | Meron Surgery Receipt V1 |
| [move_kind.contract.yaml](move_kind.contract.yaml) | Move Kind |
| [objective_typed_v1.contract.yaml](objective_typed_v1.contract.yaml) | Objective Typed v1 |
| [obligation.contract.yaml](obligation.contract.yaml) | Obligation |
| [obstruction_hint_v1.contract.yaml](obstruction_hint_v1.contract.yaml) | Obstruction Hint v1 |
| [oesos_summary_v1.contract.yaml](oesos_summary_v1.contract.yaml) | Oesos Summary v1 |
| [packet_envelope_wire_v2.contract.yaml](packet_envelope_wire_v2.contract.yaml) | Packet Envelope Wire V2 |
| [parse_result.contract.yaml](parse_result.contract.yaml) | Parse Result |
| [placement.contract.yaml](placement.contract.yaml) | Placement |
| [prompt_artifact_v1.contract.yaml](prompt_artifact_v1.contract.yaml) | Prompt Artifact v1 |
| [registry_census.contract.yaml](registry_census.contract.yaml) | Registry Census |
| [relation_rule.contract.yaml](relation_rule.contract.yaml) | Relation Rule |
| [retraction_receipt_v1.contract.yaml](retraction_receipt_v1.contract.yaml) | Retraction Receipt V1 |
| [rule.contract.yaml](rule.contract.yaml) | Oriented Rewrite Rule |
| [stop_reason.contract.yaml](stop_reason.contract.yaml) | Stop Reason |
| [symbolic_opcode.contract.yaml](symbolic_opcode.contract.yaml) | Symbolic Opcode |
| [topological_anchors_v1.contract.yaml](topological_anchors_v1.contract.yaml) | Topological Anchors V1 |
| [transport_certificate_v1.contract.yaml](transport_certificate_v1.contract.yaml) | Transport Certificate V1 |
| [witness_verdict.contract.yaml](witness_verdict.contract.yaml) | Witness Verdict |

### Non-contract note

| File | Purpose |
| --- | --- |
| [UNCONTRACTED.md](UNCONTRACTED.md) | Types this directory deliberately does not contract |
