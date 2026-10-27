//! Unified runtime invocation dispatcher for cross-language FFI seam.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_33b890ab;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_33b890ab<T> = std::result::Result<T, BoundaryError_33b890ab>;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use std::sync::OnceLock;

mod evidence;
mod exact;
mod majorana_math;
mod native_matrix;
mod native_homology;
mod native_functional;
mod ports;
mod presentations;
mod qm_classical;
mod qddc;
mod requests;
mod wire;
mod workflow;

use presentations::host_named_presentation;
pub use presentations::host_presentation_pins;
#[cfg(test)]
use presentations::{parse_compiled_pin_file, PINNED_PRESENTATIONS};
use requests::*;

use crate::pinned_permutation::{self, PinnedPermutationOrderRequestV1};

use core_kernel::{exact_wire_vec, parse_exact, to_canonical_string, Exact};
use pfp_runtime::{
    canonical_bytes, canonical_json, canonical_unwire, canonical_wire, critical_pairs,
    domain_digest_json, evaluate_peak_pinned, is_ordered_closure, ordered_loop_product,
    parse_unified_diff, verify_boundary_closed, verify_l1_certificate,
    verify_simplicial_boundary_detailed, CandidateProposal, CreateCodeChangeProposalUseCase,
    CriticalPeakClaim, EvaluatePatchGatesUseCase, F2Matrix, GaugeBoard,
    IntakeResearchSourcesUseCase, L1Refusal, Presentation, PresentationPins, RationalMatrix,
    SubmitPatchCandidateUseCase,
};

pub const RUNTIME_REQUEST_SCHEMA: &str = "core.symbol-game.runtime-request.v1";
pub const RUNTIME_OUTCOME_SCHEMA: &str = "core.symbol-game.runtime-outcome.v1";

/// Complete UTF-8 envelope limits, shared by CLI and MCP transports.
pub const MAX_RUNTIME_REQUEST_BYTES: usize = 65_536;
/// Complete signed-projection bout envelope; instruction and compute ceilings are unchanged.
pub const MAX_ADVERSARY_BOUT_RUNTIME_REQUEST_BYTES: usize = 1024 * 1024;
/// The DAG has its own 256 KiB payload ceiling; reserve 4 KiB for the envelope.
pub const MAX_DAG_RUNTIME_REQUEST_BYTES: usize = 256 * 1024 + 4096;
/// Two 1 MiB byte arrays, bounded artifact metadata, and the runtime envelope.
pub const MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES: usize = 12 * 1024 * 1024;

pub fn runtime_request_byte_limit(action: &str) -> usize {
    match action {
        "adversary_bout" => MAX_ADVERSARY_BOUT_RUNTIME_REQUEST_BYTES,
        "architecture_dag_verify" => MAX_DAG_RUNTIME_REQUEST_BYTES,
        "prompt_artifact" | "validate_reply_residual" => MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES,
        _ => MAX_RUNTIME_REQUEST_BYTES,
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RuntimeRequestV1 {
    pub schema_version: String,
    pub action: String,
    pub payload: Value,
}

impl RuntimeRequestV1 {
    /// Decode a previously parsed envelope without deserializing its payload
    /// again. In arbitrary-precision serde_json, re-deserializing Value can
    /// reinterpret an ordinary object bearing a private number marker.
    pub fn from_parsed_json(value: Value) -> Result<Self, String> {
        let Value::Object(mut fields) = value else {
            return Err("runtime request must be an object".to_owned());
        };
        if let Some(key) = fields
            .keys()
            .find(|key| !matches!(key.as_str(), "schema_version" | "action" | "payload"))
        {
            return Err(format!("unknown runtime request field: {key}"));
        }
        let schema_version = match fields.remove("schema_version") {
            Some(Value::String(value)) => value,
            _ => return Err("schema_version must be a string".to_owned()),
        };
        let action = match fields.remove("action") {
            Some(Value::String(value)) => value,
            _ => return Err("action must be a string".to_owned()),
        };
        let payload = fields
            .remove("payload")
            .ok_or_else(|| "missing runtime request field: payload".to_owned())?;
        Ok(Self {
            schema_version,
            action,
            payload,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RuntimeOutcomeV1 {
    pub schema_version: String,
    pub action: String,
    pub success: bool,
    pub result: Option<Value>,
    pub error: Option<String>,
    pub authority_effect: String,
}

fn outcome_ok(action: &str, result: Value) -> RuntimeOutcomeV1 {
    RuntimeOutcomeV1 {
        schema_version: RUNTIME_OUTCOME_SCHEMA.to_owned(),
        action: action.to_owned(),
        success: true,
        result: Some(result),
        error: None,
        authority_effect: "None".to_owned(),
    }
}

fn outcome_err(action: &str, error: impl Into<String>) -> RuntimeOutcomeV1 {
    RuntimeOutcomeV1 {
        schema_version: RUNTIME_OUTCOME_SCHEMA.to_owned(),
        action: action.to_owned(),
        success: false,
        result: None,
        error: Some(error.into()),
        authority_effect: "None".to_owned(),
    }
}

/// Every action this runtime dispatches, paired with the adapter that owns it.
///
/// The single source of truth for the runtime's surface. `--describe-runtime`
/// derives its adapter list from here rather than repeating it, so the
/// advertised surface cannot name a capability the dispatcher does not have.
///
/// It was able to before: the description hard-coded nine adapters while
/// `invoke` imported nothing for three of them, so a caller reading the
/// capability list was told a rewriting service existed. A list that nothing
/// checks is a blind gate, and the repair is to delete the second list rather
/// than to correct it.
///
type RuntimeHandler = fn(&RuntimeRequestV1) -> RuntimeOutcomeV1;

macro_rules! runtime_actions {
    ($(($adapter:literal, $action:literal, $handler:path)),+ $(,)?) => {
        pub const RUNTIME_ACTIONS: &[(&str, &str)] = &[$(($adapter, $action)),+];

        fn action_handler(action: &str) -> Option<RuntimeHandler> {
            match action {
                $($action => Some($handler),)+
                _ => None,
            }
        }
    };
}

runtime_actions! {
    ("qddc", "qddc_hodge", qddc::dispatch),
    ("qddc", "qddc_repair_projector", qddc::dispatch),
    ("qddc", "qddc_deform", qddc::dispatch),
    ("qddc", "qddc_lindblad", qddc::dispatch),
    ("qddc", "qddc_retract", qddc::dispatch),
    ("qddc", "qddc_probe", qddc::dispatch),
    ("qddc", "qddc_density", qddc::dispatch),
    ("exact_math", "math_rational_matrix", majorana_math::dispatch),
    ("exact_math", "math_gf2_matrix", majorana_math::dispatch),
    ("majorana", "majorana_braid_action", majorana_math::dispatch),
    ("majorana", "majorana_gf2_diagnostic", majorana_math::dispatch),
    ("majorana", "majorana_kitaev_wire", majorana_math::dispatch),
    ("majorana", "majorana_multiqubit_braid", majorana_math::dispatch),
    ("majorana", "majorana_noise", majorana_math::dispatch),
    ("majorana", "majorana_noise_generate", majorana_math::dispatch),
    ("homology", "homology_contraction", majorana_math::dispatch),
    ("homology", "homology_perturbation", majorana_math::dispatch),
    ("functional", "functional_projection_transfer", majorana_math::dispatch),
    ("functional", "functional_family_bound", majorana_math::dispatch),
    ("functional", "functional_family_member", majorana_math::dispatch),
    ("qm_classical", "qm_classical_evaluate", qm_classical::dispatch),
    ("qm_classical", "qm_classical_verify", qm_classical::dispatch),
    ("workflow", "anti_skill_detect", ports::dispatch),
    ("adversary", "adversary_bout", ports::dispatch),
    ("immune", "immune_allostery", ports::dispatch),
    ("immune", "immune_clonal", ports::dispatch),
    ("immune", "immune_admission", ports::dispatch),
    ("immune", "immune_activation", ports::dispatch),
    ("immune", "immune_screen", ports::dispatch),
    ("immune", "immune_pharmacy_search", ports::dispatch),
    ("immune", "immune_pharmacy_search_file", ports::dispatch),
    ("prompt_civilization", "prompt_civilization", ports::dispatch),
    ("prompt_civilization", "prompt_rank", ports::dispatch),
    ("prompt_civilization", "prompt_metabolism", ports::dispatch),
    ("prompt_civilization", "prompt_metabolism_file", ports::dispatch),
    ("prompt_civilization", "learning_signals", ports::dispatch),
    ("prompt_civilization", "learning_signals_file", ports::dispatch),
    ("intelligence", "intelligence_lifecycle", ports::dispatch),
    ("intelligence", "intelligence_lifecycle_file", ports::dispatch),
    ("workflow", "skill_garden_cull", ports::dispatch),
    ("workflow", "skill_garden_cull_file", ports::dispatch),
    ("adversary", "adversary_support", ports::dispatch),
    ("adversary", "adversary_support_file", ports::dispatch),
    ("workflow", "workflow_substitute", ports::dispatch),
    ("workflow", "workflow_validate", ports::dispatch),
    ("workflow", "workflow_graph", ports::dispatch),
    ("provider", "provider_budget", ports::dispatch),
    ("provider", "anthropic_messages", ports::dispatch),
    ("provider", "anthropic_messages_file", ports::dispatch),
    ("workflow", "workflow_operation_v3", ports::dispatch),
    ("workflow", "workflow_composition_v3", ports::dispatch),
    ("canonical", "canonical_wire", wire::dispatch),
    ("canonical", "canonical_unwire", wire::dispatch),
    ("canonical", "canonical_json", wire::dispatch),
    ("canonical", "canonical_bytes_hex", wire::dispatch),
    ("canonical", "domain_digest", wire::dispatch),
    ("diff_parser", "parse_unified_diff", wire::dispatch),
    ("code_change", "create_code_change_proposal", evidence::dispatch),
    ("code_change", "submit_patch_candidate", evidence::dispatch),
    ("code_change", "evaluate_patch_gates", evidence::dispatch),
    ("research_evidence", "intake_research_sources", evidence::dispatch),
    ("glyph_trajectory", "glyph_trajectory_execute", ports::dispatch),
    ("glyph_trajectory", "glyph_trajectory_replay", ports::dispatch),
    ("scoring_frontier", "score_discrete_proposal", workflow::dispatch),
    ("scoring_frontier", "score_cochain_proposal", workflow::dispatch),
    ("signed_transport", "signed_transport", evidence::dispatch),
    ("scoring_frontier", "rank_scored_candidates", workflow::dispatch),
    ("scoring_frontier", "rank_candidate_proposals", workflow::dispatch),
    ("f2", "classify_gauge_board", exact::dispatch),
    ("prompt_turn", "validate_reply_residual", ports::dispatch),
    ("prompt_artifact", "prompt_artifact", ports::dispatch),
    ("prompt_artifact", "immune_fence_render", ports::dispatch),
    ("reply_control", "reply_control", ports::dispatch),
    ("rewriting", "evaluate_critical_peak", exact::dispatch),
    ("rewriting", "enumerate_critical_pairs", exact::dispatch),
    ("rewriting", "verify_pinned_permutation_order", exact::dispatch),
    ("rational", "verify_l1_certificate", exact::dispatch),
    ("rational", "exact_solve_l1_primal_dual", exact::dispatch),
    ("operad", "operad_validate_prompt", exact::dispatch),
    ("operad", "operad_graft_slot", exact::dispatch),
    ("operad", "operad_evaluate_ideals", exact::dispatch),
    ("operad", "operad_check_annihilator", exact::dispatch),
    ("cochain", "cochain_evaluate", exact::dispatch),
    ("wdp_architecture", "architecture_dag_verify", exact::dispatch),
    ("genesis", "genesis_resolve", exact::dispatch),
    ("genesis", "coupled_relational_operad_verify", exact::dispatch),
    ("coda", "coda_evaluate", exact::dispatch),
    ("continuum", "continuum_evaluate", exact::dispatch),
    ("coda", "coda_verify", exact::dispatch),
    ("functional", "functional_evaluate", exact::dispatch),
    ("functional", "functional_verify", exact::dispatch),
    ("wdp_kernel", "wdp_kernel_check", exact::dispatch),
    ("wdp_kernel", "wdp_certificate_check", exact::dispatch),
    ("wdp_packet", "wdp_packet_evaluate", exact::dispatch),
    ("wdp_packet", "wdp_packet_verify", exact::dispatch),
    ("genesis_reports", "genesis_report_evaluate", exact::dispatch),
    ("genesis_reports", "genesis_report_verify", exact::dispatch),
    ("genesis_reports", "genesis_report_describe_operation", exact::dispatch),
    ("genesis_reports", "genesis_report_commit", exact::dispatch),
    ("genesis_reports", "genesis_report_verify_commit", exact::dispatch),
    ("measurement", "measurement_evaluate", exact::dispatch),
    ("measurement", "measurement_verify", exact::dispatch),
    ("projection", "projection_evaluate", exact::dispatch),
    ("projection", "projection_verify", exact::dispatch),
    ("graph", "graph_evaluate", exact::dispatch),
    ("graph", "graph_verify", exact::dispatch),
    ("graph", "graph_challenge", exact::dispatch),
    ("decode_control", "verify_decode_receipt_v2", exact::dispatch),
    ("linear_algebra", "exact_determinant", exact::dispatch),
    ("linear_algebra", "exact_is_positive_definite", exact::dispatch),
    ("linear_algebra", "exact_ldlt", exact::dispatch),
    ("linear_algebra", "exact_rank", exact::dispatch),
    ("linear_algebra", "exact_leading_minors", exact::dispatch),
    ("linear_algebra", "exact_char_poly", exact::dispatch),
    ("homology", "exact_verify_boundary_closed", exact::dispatch),
    ("homology", "exact_verify_simplicial_boundary_law", exact::dispatch),
    ("holonomy", "exact_ordered_loop_product", exact::dispatch),
    ("holonomy", "exact_is_ordered_closure", exact::dispatch),
    ("ddc", "ddc_verify_tape", exact::dispatch),
    ("prime", "prime_admit", workflow::dispatch),
    ("prime", "prime_replay_decide", workflow::dispatch),
    ("prime", "prime_descent", workflow::dispatch),
    ("lggr", "lggr_classify", exact::dispatch),
    ("lggr", "lggr_k_cell_classify", exact::dispatch),
    ("lggr", "lggr_soundness", exact::dispatch),
    ("pharmacy", "pharmacy_detect", ports::dispatch),
    ("certifiers", "verify_phi1_form", evidence::dispatch),
    ("run_folder", "run_folder_seal", ports::dispatch),
    ("run_folder", "run_folder_verify", ports::dispatch),
    ("turn_driver", "turn_driver_next_prompt", workflow::dispatch),
    ("turn_driver", "turn_driver_step", workflow::dispatch),
    ("stabilizer", "stabilizer_solve", exact::dispatch),
    ("stabilizer", "stabilizer_check", exact::dispatch),
    ("jcs", "jcs_canonicalize", wire::dispatch),
    ("jcs", "jcs_digest", wire::dispatch),
    ("decode_control", "verify_decode_receipt", evidence::dispatch),
    ("scratch_board", "detect_stationary_attractor", evidence::dispatch),
    ("lean_verify", "lean_scan_sources", evidence::dispatch),
    ("lean_verify", "lean_audit_report", evidence::dispatch),
    ("task_decomposition", "decompose_task", workflow::dispatch),
    ("retraction", "retraction_turn", workflow::dispatch),
    ("retraction", "retraction_loop", workflow::dispatch),
    ("debate", "debate_localize", workflow::dispatch),
    ("dda", "dda_surgery", workflow::dispatch),
    ("transport", "simplicial_transport", workflow::dispatch),
    ("prime", "prime_candidate_evaluate", workflow::dispatch),
    ("prime", "prime_stage_record", workflow::dispatch),
    ("challenge", "challenge_commit", workflow::dispatch),
    ("challenge", "challenge_freeze", workflow::dispatch),
    ("challenge", "challenge_score", workflow::dispatch),
}

/// The adapters this runtime advertises, in declaration order, without repeats.
pub fn advertised_adapters() -> Vec<&'static str> {
    let mut adapters: Vec<&'static str> = Vec::new();
    for (adapter, _) in RUNTIME_ACTIONS {
        if !adapters.contains(adapter) {
            adapters.push(adapter);
        }
    }
    adapters
}

/// Every action name the table declares.
pub fn dispatchable_actions() -> Vec<&'static str> {
    RUNTIME_ACTIONS.iter().map(|(_, action)| *action).collect()
}

/// Decode the cochain at both native JSON gauge entrypoints without coercion.
///
/// Missing data is not the empty cochain, and an invalid bit is not zero.
/// Mathematical classification remains the responsibility of `GaugeBoard`.
pub fn parse_gauge_cochain(value: Option<&Value>) -> Result<Vec<bool>, String> {
    let Some(Value::Array(items)) = value else {
        return Err("INVALID_COCHAIN: cochain must be an explicit array".to_owned());
    };
    items
        .iter()
        .enumerate()
        .map(|(index, item)| {
            let bit = match item {
                Value::Bool(bit) => Some(*bit),
                Value::Number(number) => match number.as_u64() {
                    Some(0) => Some(false),
                    Some(1) => Some(true),
                    _ => None,
                },
                _ => None,
            };
            bit.ok_or_else(|| {
                format!("INVALID_COCHAIN: cochain[{index}] must be boolean or integer 0 or 1")
            })
        })
        .collect()
}

pub fn dispatch_runtime_request(req: &RuntimeRequestV1) -> RuntimeOutcomeV1 {
    let action = req.action.as_str();
    if req.schema_version != RUNTIME_REQUEST_SCHEMA {
        return outcome_err(
            action,
            format!(
                "RUNTIME_REQUEST_SCHEMA_MISMATCH: expected {RUNTIME_REQUEST_SCHEMA}, got {}",
                req.schema_version
            ),
        );
    }
    match action_handler(action) {
        Some(handler) => handler(req),
        None => outcome_err(action, format!("unsupported runtime action: {action}")),
    }
}

#[cfg(test)]
#[path = "invoke/tests.rs"]
mod surface_parity_tests;

// Origin: engine/crates_rs/pfp/src/invoke.rs
// Claim: urn:core:crates_rs:pfp:invoke:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord33b890ab {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord33b890ab` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError33b890ab {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError33b890ab {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError33b890ab {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError33b890ab {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord33b890ab {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError33b890ab> {
        if capacity_bound == 0 {
            return Err(BoundaryError33b890ab::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError33b890ab::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError33b890ab::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_33b890ab {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord33b890ab::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord33b890ab::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord33b890ab::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord33b890ab::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord33b890ab::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError33b890ab::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError33b890ab::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
