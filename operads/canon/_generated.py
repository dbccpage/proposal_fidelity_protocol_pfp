"""Operad canon, generated from code/rust/core_operad_canon. Do not edit.

Regenerate with ``cargo run -p core_operad_canon -- write`` from ``code/rust``; import it as ``operads.canon``.

AuthorityEffect: None.
"""

# fmt: off
# ruff: noqa: E501
from __future__ import annotations

from enum import Enum

SCHEMA_VERSION = "core.operad-canon.v1"

CAPABILITY_KIND: tuple[str, ...] = ("skill", "anti_skill", "rule", "helpful_pattern", "anti_pattern", "antibody")
INVOCATION_MODE: tuple[str, ...] = ("discipline", "entry", "on-demand")
LIFECYCLE_DECLARATION: tuple[str, ...] = ("Declared", "Abstract", "Synthesized")
LIFECYCLE_SCHEMA_BINDING: tuple[str, ...] = ("Unbound", "Bound", "AnySchema")
LIFECYCLE_EXECUTOR_BINDING: tuple[str, ...] = ("Unbound", "Bound", "ExternalService")
LIFECYCLE_VALIDATION: tuple[str, ...] = ("Unchecked", "Validated", "Failed")
LIFECYCLE_ADMISSION: tuple[str, ...] = ("Unadmitted", "Admitted", "Retired")
LIFECYCLE_STAGE_LEGACY: tuple[str, ...] = ("DRAFT", "TYPED", "BOUND", "TESTED", "COMPOSABLE", "ADMITTED")
META_SKILL_STATUS: tuple[str, ...] = ("provisional", "promoted", "certified", "retired")
OPERAD_COLOUR: tuple[str, ...] = ("Audit", "Code", "Contract", "Diagram", "Ledger", "Paper", "Post", "Proof", "Receipt", "State")
OPERAD_SUBCOLOUR: tuple[str, ...] = ("Audit.hype_hits", "Audit.lint_diff", "Audit.sfh_findings", "Audit.shadow_violations", "Audit.layout_findings", "Audit.verdict", "Code.purged", "Ledger.source_hashes")
OPERAND_COLOUR: tuple[str, ...] = ("Audit", "Code", "Contract", "Diagram", "Ledger", "Paper", "Post", "Proof", "Receipt", "State")
PROMPT_COLOUR: tuple[str, ...] = ("RawTextSpan", "Equation", "IsolatedVariable", "SubstitutionStep", "RationalValue", "InvariantWitness", "TargetResult")
CAPABILITY_WIRE_TYPE: tuple[str, ...] = ("anti_skill_subject", "anti_skill_hits", "typed_audit_receipt", "code_text")
ADVERSARY_PORT: tuple[str, ...] = ("AdversaryRuntime", "NativeBout", "SeatTransport", "SgtEmission", "ImmuneAntibodies", "OeopLearning", "OeopAntiSkill", "PromptGenealogy", "CodaEvaluation", "LggrGluing", "EnvelopeStore")
ADVERSARY_WIRE_TYPE: tuple[str, ...] = ("CandidateProposal", "CochainDefect", "Context", "Contract", "DualMultiplier", "DualityReceipt", "FlawAudit", "GateWitness", "GroundTruth", "PrimalResidual", "RawPacket", "RawSpan", "SanitizedPacket", "SessionHintRequest", "SessionHintResult", "TerminalStatus")
OPERATION_KIND: tuple[str, ...] = ("Identity", "Generator", "Composite")
OPERAD_VARIANT: tuple[str, ...] = ("Planar", "Symmetric")
OPERATION_TERM: tuple[str, ...] = ("Identity", "Primitive", "Substitute", "Admitted")
OPERAD_TREE: tuple[str, ...] = ("Leaf", "Node", "NullTree")
OP_BINDING_KIND: tuple[str, ...] = ("host", "pfp_turn")
INVENTORY_OP: tuple[str, ...] = ("ara.bind_source_hashes", "ara.receipt", "ara.refute", "glossa.merge_hits", "glossa.propose_replacements", "glossa.report", "glossa.scan_hype_code", "glossa.scan_hype_prose", "gti.layout_check", "gti.receipt", "gti.shadow_scan", "mnc.gate", "mnc.purge", "sfh.report", "sfh.scan")
INVENTORY_ANTI_OP: tuple[str, ...] = ("ara.refuse_undeclared_omission", "ara.refuse_unrecomputed_hash", "glossa.refuse_missing_claim_envelope", "gti.refuse_duplicate_test_basename", "gti.refuse_sys_path_hack", "sfh.refuse_bare_except", "sfh.refuse_pass_handler", "sfh.refuse_rust_unwrap")
PROMPT_ANTI_OP: tuple[str, ...] = ("glossa.refuse_missing_claim_envelope", "pfp.refuse_scalar_proxy_theorem_substitution", "pfp.refuse_target_fitting_constant_compensation", "pfp.refuse_unlicensed_causality", "pfp.refuse_unlicensed_multiplication", "pfp.refuse_unmapped_continuum_import", "pfp.refuse_witness_certificate_desynchronization")
DDC_LETTER: tuple[str, ...] = ("E", "R", "C", "I", "Λ", "D", "M", "T")
DDC_REPAIR_STAGE: tuple[str, ...] = ("C", "R", "E", "I", "M", "T")
DDA_OPERATION_KIND: tuple[str, ...] = ("SuccessorProbe", "ResidualUpdate", "CarrierLift")
RESIDUAL_EFFECT: tuple[str, ...] = ("unknown", "contractive", "neutral", "dilative")
MORPHISM_EXECUTION_STATUS: tuple[str, ...] = ("SUCCESS", "CONTRACTIVE_PASS", "NEUTRAL_PASS", "REFUSED", "FAILED")
COHOMOLOGY_DEGREE: tuple[str, ...] = ("H0_INVARIANT_FENCE", "H1_FIRST_ORDER_DEFORMATION", "H2_REPAIR_OBSTRUCTION", "HN_HIGHER_COHERENCE")
EVIDENCE_TYPE: tuple[str, ...] = ("compilation", "budget_audit", "associativity", "slice_verification", "cochain_obstruction")
OPEN_OBLIGATION_KIND: tuple[str, ...] = ("unverified_claim", "unavailable_gate", "type_precision_loss", "ambiguous_import", "missing_oracle", "anti_pattern_detected", "dirty_worktree", "packaging_mismatch", "counterexample_not_property_based", "architectural_smell", "security_or_resource_boundary", "escalation_required", "invariant_not_reexecutable")
CONTRACTIVE_META_OPERAD: tuple[str, ...] = ("meta-code-audit--code--contractive", "meta-contract-audit--contract--contractive", "meta-contract-code--audit--contractive", "meta-paper--audit--contractive", "meta-paper--receipt--contractive", "meta-proof-code--proof--contractive", "meta-state--receipt--contractive", "meta-state--state--contractive")
CONTRACTIVE_META_OPERAD_RESIDUAL: tuple[str, ...] = ("contractive",)
X_TO_Y_VERIFIER: tuple[str, ...] = ("meta-atlas-state-to-state-verifier", "meta-auto-paper-to-paper-verifier", "meta-auto-state-to-receipt-verifier", "meta-blackrod-contract-to-audit-verifier", "meta-glossa-proof-to-proof-verifier", "meta-goo-ledger-to-ledger-verifier", "meta-goo-paper-to-paper-verifier", "meta-goo-proof-to-audit-verifier", "meta-kybernesis-paper-to-post-verifier", "meta-proof-to-paper-verifier", "meta-techne-code-to-audit-verifier", "meta-techne-code-to-code-verifier")
PFP_POLARITY: tuple[str, ...] = ("CONSTRUCTIVE", "INTERROGATIVE", "CORRECTIVE", "GATE")
POLARITY_PAIR_PROVENANCE: tuple[str, ...] = ("declared", "inferred")
RESOLVER_ROUTE: tuple[str, ...] = ("historical_pr_immunity", "oe010_dda", "six_host_parity", "coda_gtla_paper", "test_quality", "canonical_value_validation", "append_only_log_integrity", "pipeline_exit_code", "formal_lean", "skill_budget", "knowledge_parity_gate", "skill_name_verify", "rule_gate")
REGISTERED_OPERAND: tuple[str, ...] = ("op_exact_cochain_coboundary_repair", "op_f2_gauge_board_classification", "op_meron_surgery_sign_inversion", "op_unpromoted_candidate_template", "op_adversary_hermetic_task_evidence_attestation", "op_adversary_strict_typed_input_refusal", "op_lean4_constructive_kernel_axiom_audit")
OBSTRUCTION_CLASS: tuple[str, ...] = ("ExactRepair", "ClosedResidual", "OpenObstruction")
OPERAND_CARRIER_KIND: tuple[str, ...] = ("evidence_record", "f2_gauge_board", "graph_cochain", "meron_cluster", "proof_term", "schema_mapping", "unverified_proposal")
OPERAND_DDC_MOTIF: tuple[str, ...] = ("CE", "CM", "CP", "CR", "EM", "ID")
CONSTRAINT_TYPE: tuple[str, ...] = ("ProjectOut", "Restrain", "Enforce")
OPERATORIZABILITY: tuple[str, ...] = ("repairable", "fatal")
RUNTIME_ACTION: tuple[str, ...] = ("repair", "abort", "refuse")
SEVERITY: tuple[str, ...] = ("P0", "P1", "P2", "P3")
ANTIBODY_PHARMACY_STATUS: tuple[str, ...] = ("candidate", "admitted", "rejected", "retired")
ANTI_SKILL_STATUS: tuple[str, ...] = ("Proposed", "Candidate", "Admitted", "Suspended", "Retired")
PHARMACY_FAILURE_CLASS: tuple[str, ...] = ("SELF_CERTIFICATION", "FAKE_RECEIPT", "CONCLUSION_PRELOAD", "SCHEMA_SEMANTIC_LAUNDERING", "THEOREM_NAME_LAUNDERING", "OPTIMALITY_HALLUCINATION", "COMPLEXITY_HALLUCINATION", "BRANCH_DROP_EXHAUSTION", "PERSONA_AUTHORITY_LEAK", "PRIVATE_COT_DEPENDENCY", "VERSION_DUPLICATION", "DETECT_REPAIR_COUPLING")
ANTI_SKILL_FAILURE_CLASS: tuple[str, ...] = ("SemanticHallucination", "ApproximateContradiction", "ToyPromotion", "UnmechanizedProofClaim", "SelfContradiction", "DualityGapNonZero", "BoundaryLeakage", "UnboundPortAssumption", "CounterfeitExactness", "SycophanticAgreement", "StructuralNonFit", "StaleCensusReference")
HIT_DISPOSITION: tuple[str, ...] = ("FINDING", "HOLD", "REFUSE")
GUARD_DISPOSITION: tuple[str, ...] = ("NO_ACTIVATION", "FINDING", "HOLD", "REFUSE", "DEFENSIVE_LOCKDOWN", "TWO_SIGNAL_COLLAPSE")
DANGER_DECISION: tuple[str, ...] = ("TOLERATED", "DIAGNOSTIC_ONLY", "DEFENSIVE_LOCKDOWN", "QUARANTINED")
AUTHORITY_LEVEL: tuple[str, ...] = ("BLOCKING_GATE", "DIAGNOSTIC_ONLY")
ANTI_SKILL_CLAIM_MODE: tuple[str, ...] = ("PROPOSAL", "BOUNDED", "UNRESTRICTED", "SELF_CERTIFIED")
ANTI_SKILL_PREDICATE_MODE: tuple[str, ...] = ("ALL", "ANY")

COLOUR_MEANINGS: dict[str, str] = {
    "Audit": "Symmetry audit, red-team diagnostic, compliance report, or defect escalation",
    "Code": "Rust/Python implementation, AST, solver module, or Pydantic schema",
    "Contract": "Nomos governance contract, prime rule YAML, or API boundary specification",
    "Diagram": "DIME figure, quick-start card, AST graph, or visualization artifact",
    "Ledger": "Claim queue row, refusal store, hypothesis tree, or issue register entry",
    "Paper": "OEARS paper package, LaTeX source, Pandoc AST, or claim ledger",
    "Post": "Public math post, Glossa dialect draft, or forum cadence item",
    "Proof": "Lean 4 formal proof term, math derivation, or step-truth assertion",
    "Receipt": "Evidence receipt, CI report, GTLA swarm review, or SHA256 manifest",
    "State": "Repository, session worktree, git ref, or execution environment state",
}

TYPES: dict[str, dict[str, object]] = {
    "capability_kind": {
        "family": "capabilities_and_lifecycle",
        "description": "The kind discriminator of a typed capability.",
        "status": "SETTLED",
        "closed": True,
        "values": CAPABILITY_KIND,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "invocation_mode": {
        "family": "capabilities_and_lifecycle",
        "description": "How a catalogued skill is invoked.",
        "status": "SETTLED",
        "closed": True,
        "values": INVOCATION_MODE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "lifecycle_declaration": {
        "family": "capabilities_and_lifecycle",
        "description": "Lifecycle facet 1 of 5, how an operation came to exist.",
        "status": "SETTLED",
        "closed": True,
        "values": LIFECYCLE_DECLARATION,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "lifecycle_schema_binding": {
        "family": "capabilities_and_lifecycle",
        "description": "Lifecycle facet 2 of 5, whether a schema is bound.",
        "status": "SETTLED",
        "closed": True,
        "values": LIFECYCLE_SCHEMA_BINDING,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "lifecycle_executor_binding": {
        "family": "capabilities_and_lifecycle",
        "description": "Lifecycle facet 3 of 5, whether an executor is bound.",
        "status": "SETTLED",
        "closed": True,
        "values": LIFECYCLE_EXECUTOR_BINDING,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "lifecycle_validation": {
        "family": "capabilities_and_lifecycle",
        "description": "Lifecycle facet 4 of 5, the validation result.",
        "status": "SETTLED",
        "closed": True,
        "values": LIFECYCLE_VALIDATION,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "lifecycle_admission": {
        "family": "capabilities_and_lifecycle",
        "description": "Lifecycle facet 5 of 5, the admission state.",
        "status": "SETTLED",
        "closed": True,
        "values": LIFECYCLE_ADMISSION,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "lifecycle_stage_legacy": {
        "family": "capabilities_and_lifecycle",
        "description": "The older single-axis lifecycle stage of a skill package, superseded by the five facets.",
        "status": "SETTLED",
        "closed": True,
        "values": LIFECYCLE_STAGE_LEGACY,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "meta_skill_status": {
        "family": "capabilities_and_lifecycle",
        "description": "Status of a synthesized meta-skill.",
        "status": "SETTLED",
        "closed": True,
        "values": META_SKILL_STATUS,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "operad_colour": {
        "family": "colours_and_wires",
        "description": "The sorts of the OEOP coloured planar multicategory.",
        "status": "PROPOSED",
        "closed": True,
        "values": OPERAD_COLOUR,
        "decision": "The ten colours are defined once, as OperadColour in this crate, and every Python and Rust colour list reads them. The kernel type core_operad_theory::OperadColour still accepts any non-empty name. Proposed: make its constructor refuse names outside these ten, so the kernel rejects the same colours as everything else.",
        "note": "The pattern estate (operads/patterns) types anti-patterns Code -> Witness. A witness is a finding, so the anti-skill catalogue reads Witness as Audit.",
        "letters_of": None,
        "legacy_map": {"Witness": "Audit"},
    },
    "operad_subcolour": {
        "family": "colours_and_wires",
        "description": "Typed sub-wires inside a colour, written Colour.subcolour.",
        "status": "SETTLED",
        "closed": True,
        "values": OPERAD_SUBCOLOUR,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "operand_colour": {
        "family": "colours_and_wires",
        "description": "Source and target colours that registered operands declare; they should be operad colours.",
        "status": "PROPOSED",
        "closed": True,
        "values": OPERAND_COLOUR,
        "decision": "Four of the seven operands use Open and Closed as colours. These are not colours: they describe the obstruction before and after the operand (an open obstruction, then a closed one). Proposed: replace them with the operad colours of the actual input and output, and keep before and after in obstruction_signature.",
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "prompt_colour": {
        "family": "colours_and_wires",
        "description": "Colours of the prompt operad: the types of the spans inside one prompt.",
        "status": "SETTLED",
        "closed": True,
        "values": PROMPT_COLOUR,
        "decision": None,
        "note": "A separate vocabulary from operad_colour. It types spans inside one prompt, not skill ports, so the two are not reconciled. The source repository's Rust prompt runtime also had an open Custom colour; that crate is not in this repository and the Python enum has no Custom, so the set here is closed.",
        "letters_of": None,
        "legacy_map": {},
    },
    "capability_wire_type": {
        "family": "colours_and_wires",
        "description": "Wire types of typed capability ports.",
        "status": "SETTLED",
        "closed": True,
        "values": CAPABILITY_WIRE_TYPE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "adversary_port": {
        "family": "colours_and_wires",
        "description": "Estate ports a Adversary specialisation may license.",
        "status": "SETTLED",
        "closed": True,
        "values": ADVERSARY_PORT,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "adversary_wire_type": {
        "family": "colours_and_wires",
        "description": "Value types on Adversary mission operation wires; each maps to one operad colour.",
        "status": "SETTLED",
        "closed": True,
        "values": ADVERSARY_WIRE_TYPE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "operation_kind": {
        "family": "operations",
        "description": "Kinds of operation in the coloured operad kernel.",
        "status": "SETTLED",
        "closed": True,
        "values": OPERATION_KIND,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "operad_variant": {
        "family": "operations",
        "description": "Whether an operad is planar or symmetric.",
        "status": "SETTLED",
        "closed": True,
        "values": OPERAD_VARIANT,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "operation_term": {
        "family": "operations",
        "description": "Term constructors of composed operations.",
        "status": "SETTLED",
        "closed": True,
        "values": OPERATION_TERM,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "operad_tree": {
        "family": "operations",
        "description": "Tree shape of a prompt operad composition.",
        "status": "SETTLED",
        "closed": True,
        "values": OPERAD_TREE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "op_binding_kind": {
        "family": "operations",
        "description": "How an op in the op inventory is executed.",
        "status": "SETTLED",
        "closed": True,
        "values": OP_BINDING_KIND,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "inventory_op": {
        "family": "operations",
        "description": "Ops declared in the op inventory.",
        "status": "SETTLED",
        "closed": True,
        "values": INVENTORY_OP,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "inventory_anti_op": {
        "family": "operations",
        "description": "Anti-ops declared in the op inventory.",
        "status": "SETTLED",
        "closed": True,
        "values": INVENTORY_ANTI_OP,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "prompt_anti_op": {
        "family": "operations",
        "description": "Built-in keyword detectors for prompt-hierarchy anti-ops.",
        "status": "SETTLED",
        "closed": True,
        "values": PROMPT_ANTI_OP,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "ddc_letter": {
        "family": "operations",
        "description": "The Discrete Deformation Calculus operational alphabet A_DDC.",
        "status": "SETTLED",
        "closed": True,
        "values": DDC_LETTER,
        "decision": None,
        "note": "Defined once, as DdcOp in this crate; core_wdp re-exports it and the Python DdcLetter is generated from it. The deprecated DdcRune alias is removed.",
        "letters_of": None,
        "legacy_map": {},
    },
    "ddc_repair_stage": {
        "family": "operations",
        "description": "Stages of a DDC code-repair operation; Λ and D are not repair stages.",
        "status": "SETTLED",
        "closed": True,
        "values": DDC_REPAIR_STAGE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "dda_operation_kind": {
        "family": "operations",
        "description": "Operation kinds on the DDC degree tower.",
        "status": "SETTLED",
        "closed": True,
        "values": DDA_OPERATION_KIND,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "residual_effect": {
        "family": "operations",
        "description": "What an operad morphism does to the residual it acts on.",
        "status": "PROPOSED",
        "closed": True,
        "values": RESIDUAL_EFFECT,
        "decision": "Three vocabularies are in use. The Python enum has the four values above. The schema in operad_data_type.yaml has eight values and no neutral or dilative. The catalogues use exact, diagnostic and ExactRationalCertificate, and the signature identities use residual_unknown. Proposed: keep the four Python values, which describe what happens to the residual, and map the rest as in legacy_map. exact, exact_receipt and ExactRationalCertificate describe the evidence an operation emits, not its residual effect, so they move to a separate evidence field.",
        "note": None,
        "letters_of": None,
        "legacy_map": {"preserving": "neutral", "diagnostic": "neutral", "residual_unknown": "unknown", "exact": "(not a residual effect: evidence kind)", "exact_receipt": "(not a residual effect: evidence kind)", "ExactRationalCertificate": "(not a residual effect: evidence kind)"},
    },
    "morphism_execution_status": {
        "family": "operations",
        "description": "Outcome of applying a morphism.",
        "status": "SETTLED",
        "closed": True,
        "values": MORPHISM_EXECUTION_STATUS,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "cohomology_degree": {
        "family": "operations",
        "description": "Meta-operad obstruction degree.",
        "status": "SETTLED",
        "closed": True,
        "values": COHOMOLOGY_DEGREE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "evidence_type": {
        "family": "operations",
        "description": "Kinds of operad evidence observation.",
        "status": "SETTLED",
        "closed": True,
        "values": EVIDENCE_TYPE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "open_obligation_kind": {
        "family": "operations",
        "description": "Kinds of obligation an evidence receipt can leave open.",
        "status": "SETTLED",
        "closed": True,
        "values": OPEN_OBLIGATION_KIND,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "contractive_meta_operad": {
        "family": "signature_families",
        "description": "Meta skills named meta-<source colours>--<target colour>--contractive.",
        "status": "SETTLED",
        "closed": True,
        "values": CONTRACTIVE_META_OPERAD,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "contractive_meta_operad_residual": {
        "family": "signature_families",
        "description": "The residual effect the contractive meta operads declare.",
        "status": "PROPOSED",
        "closed": True,
        "values": CONTRACTIVE_META_OPERAD_RESIDUAL,
        "decision": "All eight skills named --contractive declare operad_residual unknown. Proposed: once residual_effect is settled, set operad_residual to contractive in these eight SKILL.md files, or drop the suffix from the names.",
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "x_to_y_verifier": {
        "family": "signature_families",
        "description": "Meta skills named meta-<domain>-<x>-to-<y>-verifier; the name gives only the first source colour.",
        "status": "SETTLED",
        "closed": True,
        "values": X_TO_Y_VERIFIER,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "pfp_polarity": {
        "family": "signature_families",
        "description": "Polarity of a PFP operad morphism.",
        "status": "SETTLED",
        "closed": True,
        "values": PFP_POLARITY,
        "decision": None,
        "note": "PolarizedOperadTriad holds sub-operads for constructive, interrogative and corrective only. GATE morphisms have no sub-operad there, so whether gates belong in the triad is an open design question.",
        "letters_of": None,
        "legacy_map": {},
    },
    "polarity_pair_provenance": {
        "family": "signature_families",
        "description": "How a declared constructive and adversarial skill pair was established.",
        "status": "SETTLED",
        "closed": True,
        "values": POLARITY_PAIR_PROVENANCE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "resolver_route": {
        "family": "signature_families",
        "description": "Keyword routes from a request to a shared contract or a code gate.",
        "status": "SETTLED",
        "closed": True,
        "values": RESOLVER_ROUTE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "registered_operand": {
        "family": "operands",
        "description": "Operands in the operand registry.",
        "status": "SETTLED",
        "closed": True,
        "values": REGISTERED_OPERAND,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "obstruction_class": {
        "family": "operands",
        "description": "The diagnostic class an operand addresses (GTLA invariant 6, diagnostic class axis).",
        "status": "PROPOSED",
        "closed": True,
        "values": OBSTRUCTION_CLASS,
        "decision": "The schema and GTLA invariant 6 fix the diagnostic axis at three values, but three operands use EvidenceLeakage, SchemaCoercion and SmuggledAxiom. These are failure classes, not diagnostic classes. Using them here mixes the failure axis into the diagnostic axis, which GTLA invariant 4 forbids. Proposed: give each of those operands a diagnostic class, and record its failure class in a separate failure_class field.",
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "operand_carrier_kind": {
        "family": "operands",
        "description": "Carrier an operand's obstruction lives on; open, one per operand family.",
        "status": "SETTLED",
        "closed": False,
        "values": OPERAND_CARRIER_KIND,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "operand_ddc_motif": {
        "family": "operands",
        "description": "DDC letter sequence an operand applies; every letter must be a ddc_letter.",
        "status": "PROPOSED",
        "closed": False,
        "values": OPERAND_DDC_MOTIF,
        "decision": "op_lean4_constructive_kernel_axiom_audit declares motif CP, but P is not a DDC letter. An axiom audit that refuses a smuggled axiom reads as C then M. Proposed: CM, which the operand's owner should confirm.",
        "note": None,
        "letters_of": "ddc_letter",
        "legacy_map": {},
    },
    "constraint_type": {
        "family": "immune_and_negative",
        "description": "How an antibody constrains a candidate.",
        "status": "SETTLED",
        "closed": True,
        "values": CONSTRAINT_TYPE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "operatorizability": {
        "family": "immune_and_negative",
        "description": "Whether a failure can be repaired by an operator.",
        "status": "SETTLED",
        "closed": True,
        "values": OPERATORIZABILITY,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "runtime_action": {
        "family": "immune_and_negative",
        "description": "What an antibody does when it fires.",
        "status": "PROPOSED",
        "closed": True,
        "values": RUNTIME_ACTION,
        "decision": "RuntimeAction allows only repair and abort, but antibody YAML files also use refuse. A refusal is its own routing terminal (Refusal in core_types::routing), distinct from aborting the run. Proposed: add REFUSE = \"refuse\" to RuntimeAction rather than rewrite the antibody files.",
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "severity": {
        "family": "immune_and_negative",
        "description": "Antibody severity.",
        "status": "SETTLED",
        "closed": True,
        "values": SEVERITY,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "antibody_pharmacy_status": {
        "family": "immune_and_negative",
        "description": "Pharmacy status of an antibody; farming writes candidate only, admission is a separate act.",
        "status": "SETTLED",
        "closed": True,
        "values": ANTIBODY_PHARMACY_STATUS,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "anti_skill_status": {
        "family": "immune_and_negative",
        "description": "Lifecycle of a native anti-skill, a different object from a pharmacy antibody.",
        "status": "SETTLED",
        "closed": True,
        "values": ANTI_SKILL_STATUS,
        "decision": None,
        "note": "This is a separate lifecycle from antibody_pharmacy_status, so the two sets are not one vocabulary declared twice.",
        "letters_of": None,
        "legacy_map": {},
    },
    "pharmacy_failure_class": {
        "family": "immune_and_negative",
        "description": "Failure classes of the MSS-N pharmacy.",
        "status": "SETTLED",
        "closed": True,
        "values": PHARMACY_FAILURE_CLASS,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "anti_skill_failure_class": {
        "family": "immune_and_negative",
        "description": "Failure classes of native anti-skills; a separate taxonomy from pharmacy_failure_class.",
        "status": "SETTLED",
        "closed": True,
        "values": ANTI_SKILL_FAILURE_CLASS,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "hit_disposition": {
        "family": "immune_and_negative",
        "description": "What a fired anti-skill or pharmacy check does with the candidate.",
        "status": "SETTLED",
        "closed": True,
        "values": HIT_DISPOSITION,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "guard_disposition": {
        "family": "immune_and_negative",
        "description": "Danger-gate guard outcome.",
        "status": "SETTLED",
        "closed": True,
        "values": GUARD_DISPOSITION,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "danger_decision": {
        "family": "immune_and_negative",
        "description": "Danger-gate decision.",
        "status": "SETTLED",
        "closed": True,
        "values": DANGER_DECISION,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "authority_level": {
        "family": "immune_and_negative",
        "description": "Authority level in regulatory T-cell supervision.",
        "status": "SETTLED",
        "closed": True,
        "values": AUTHORITY_LEVEL,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "anti_skill_claim_mode": {
        "family": "immune_and_negative",
        "description": "Claim mode an anti-skill subject declares.",
        "status": "SETTLED",
        "closed": True,
        "values": ANTI_SKILL_CLAIM_MODE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
    "anti_skill_predicate_mode": {
        "family": "immune_and_negative",
        "description": "How an anti-skill predicate combines its atoms.",
        "status": "SETTLED",
        "closed": True,
        "values": ANTI_SKILL_PREDICATE_MODE,
        "decision": None,
        "note": None,
        "letters_of": None,
        "legacy_map": {},
    },
}


class OperadColour(str, Enum):
    """The sorts of the OEOP coloured planar multicategory."""

    AUDIT = "Audit"
    CODE = "Code"
    CONTRACT = "Contract"
    DIAGRAM = "Diagram"
    LEDGER = "Ledger"
    PAPER = "Paper"
    POST = "Post"
    PROOF = "Proof"
    RECEIPT = "Receipt"
    STATE = "State"


class DdcLetter(str, Enum):
    """The Discrete Deformation Calculus operational alphabet A_DDC."""

    E = "E"
    R = "R"
    C = "C"
    I = "I"
    LAMBDA = "Λ"
    D = "D"
    M = "M"
    T = "T"


class HitDisposition(str, Enum):
    """What a fired anti-skill or pharmacy check does with the candidate."""

    FINDING = "FINDING"
    HOLD = "HOLD"
    REFUSE = "REFUSE"
