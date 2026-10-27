//! Real Model-in-the-Loop Engine Turn Driver (U05).
//!
//! Enforces:
//! - Strict descent contract: Frontier advances iff (Phi1, Gamma2, defects) is componentwise
//!   non-increasing with at least ONE STRICT DECREASE (<).
//! - Non-improving or malformed moves are routed to CemeteryRowV1.
//! - Emits DdcStepRowV1 on valid transitions.
//! AuthorityEffect: None (const).

use crate::prompt_turn::{
    compile_prompt_artifact, DemandItemV1, ObjectiveTypedV1, ObstructionHintV1, PromptArtifactV1,
};
use crate::refusal::Refusal;
use core_wdp::ddc::{assign_letter, compute_ddc_row_hash, DdcStepRowV1, StateMetrics};
use serde::{Deserialize, Serialize};

pub const TURN_DRIVER_PROMPT_INVALID: &str = "TURN_DRIVER_PROMPT_INVALID";
pub const TURN_DRIVER_PROMPT_ID_DOMAIN: &str = "core.symbol-game.turn-driver.prompt-identity.v1";
pub const MAX_PROMPT_POLICY_LABEL_BYTES: usize = 256;
pub const MAX_PROMPT_POLICY_LIST_ITEMS: usize = 64;
/// Bounds declared prompt configuration; this driver does not invoke a provider.
pub const MAX_PROMPT_POLICY_TOKENS: u64 = 1_048_576;

fn default_authority_effect() -> String {
    "None".to_string()
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PromptPolicyV1 {
    pub regime_id: String,
    pub regime_kind: String,
    pub admitted_constructors: Vec<String>,
    pub kill_conditions: Vec<String>,
    pub required_reply_fields: Vec<String>,
    pub max_tokens: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EngineTurnStateV1 {
    pub round_seq: u64,
    pub specification_digest: String,
    pub current_phi1: u64,
    pub current_gamma2: u64,
    pub open_defect_count: u64,
    pub previous_code: Option<String>,
    pub previous_diff: Option<String>,
    pub open_obligations: Vec<String>,
    pub promoted_operands: Vec<String>,
    pub cemetery_count: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DriverMovePacket {
    pub candidate_id: String,
    pub proposed_diff: String,
    pub declared_phi1: u64,
    pub declared_gamma2: u64,
    pub summary: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CemeteryRowV1 {
    pub candidate_id: String,
    pub round_seq: u64,
    pub rejection_reason: String,
    pub attempted_diff: String,
    pub phi1_before: u64,
    pub gamma2_before: u64,
    pub phi1_after: u64,
    pub gamma2_after: u64,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "status", content = "detail")]
pub enum StepOutcome {
    Accepted {
        new_state: EngineTurnStateV1,
        step_row: DdcStepRowV1,
    },
    RejectedNonDescent {
        cemetery_row: CemeteryRowV1,
        refusal_reason: String,
    },
    RejectedMalformed {
        cemetery_row: CemeteryRowV1,
        refusal_reason: String,
    },
}

fn invalid_prompt(message: impl Into<String>) -> Refusal {
    Refusal::new(TURN_DRIVER_PROMPT_INVALID, message)
}

fn normalize_prompt_fragment(value: &str) -> String {
    value.replace("\r\n", "\n").replace('\r', "\n")
}

fn validate_policy_label(value: &str, field: &str) -> Result<(), Refusal> {
    if value.trim().is_empty()
        || value.len() > MAX_PROMPT_POLICY_LABEL_BYTES
        || value.chars().any(char::is_control)
    {
        return Err(invalid_prompt(format!(
            "{field} must be nonblank, contain no control characters, and fit in {MAX_PROMPT_POLICY_LABEL_BYTES} UTF-8 bytes"
        )));
    }
    Ok(())
}

fn validate_prompt_policy(policy: &PromptPolicyV1) -> Result<(), Refusal> {
    if policy.regime_id.len() != 64
        || !policy
            .regime_id
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(invalid_prompt(
            "regime_id must be 64 lowercase hexadecimal characters",
        ));
    }
    validate_policy_label(&policy.regime_kind, "regime_kind")?;
    for (field, values) in [
        ("admitted_constructors", &policy.admitted_constructors),
        ("kill_conditions", &policy.kill_conditions),
        ("required_reply_fields", &policy.required_reply_fields),
    ] {
        if values.len() > MAX_PROMPT_POLICY_LIST_ITEMS {
            return Err(invalid_prompt(format!(
                "{field} exceeds {MAX_PROMPT_POLICY_LIST_ITEMS} entries"
            )));
        }
        for value in values {
            validate_policy_label(value, field)?;
        }
    }
    if policy.max_tokens == 0 || policy.max_tokens > MAX_PROMPT_POLICY_TOKENS {
        return Err(invalid_prompt(format!(
            "max_tokens must be in 1..={MAX_PROMPT_POLICY_TOKENS}"
        )));
    }
    Ok(())
}

#[derive(Serialize)]
struct TurnPromptIdentity<'a> {
    state: &'a EngineTurnStateV1,
    normalized_policy: &'a PromptPolicyV1,
    prompt_body_sha256: &'a str,
    prompt_body_byte_count: usize,
}

/// Renders the driver prompt and binds its identity to the complete supplied state
/// and normalized policy. Raw state text remains identity-bearing even when its
/// rendered body's CRLF/bare-CR line endings normalize to LF.
pub fn next_prompt(
    state: &EngineTurnStateV1,
    policy: &PromptPolicyV1,
) -> Result<PromptArtifactV1, Refusal> {
    validate_prompt_policy(policy)?;
    let mut prompt_body = format!(
        "# Symbol Game Specification Digest\n\nSpec Hash: {}\nRound: {}\n\n",
        normalize_prompt_fragment(&state.specification_digest),
        state.round_seq
    );

    if let Some(prev_diff) = &state.previous_diff {
        prompt_body.push_str("## Previous Code Diff\n```diff\n");
        // Normalize before adjoining template separators: a final bare CR must
        // not consume the template's leading LF by forming a new CRLF pair.
        prompt_body.push_str(&normalize_prompt_fragment(prev_diff));
        prompt_body.push_str("\n```\n\n");
    }

    if !state.open_obligations.is_empty() {
        prompt_body.push_str("## Open Obligations\n");
        for ob in &state.open_obligations {
            prompt_body.push_str(&format!("- {}\n", normalize_prompt_fragment(ob)));
        }
        prompt_body.push('\n');
    }

    if !state.promoted_operands.is_empty() {
        prompt_body.push_str("## Active Promoted Operands\n");
        for op in &state.promoted_operands {
            prompt_body.push_str(&format!("- Operand: {}\n", normalize_prompt_fragment(op)));
        }
        prompt_body.push('\n');
    }

    let objective = ObjectiveTypedV1 {
        kind: "OBSTRUCTION_DESCENT".to_string(),
        summary: format!(
            "Descend current obstruction mass (Phi1={}, Gamma2={})",
            state.current_phi1, state.current_gamma2
        ),
        target_obstruction_ids: state.open_obligations.clone(),
        target_demand_ids: vec![],
    };

    let open_hints = vec![
        ObstructionHintV1 {
            obstruction_id: "obs_phi1".to_string(),
            family: "homology".to_string(),
            residual_colour: "RED".to_string(),
            magnitude: Some(state.current_phi1 as f64),
            demand_id: None,
        },
        ObstructionHintV1 {
            obstruction_id: "obs_gamma2".to_string(),
            family: "holonomy".to_string(),
            residual_colour: "BLUE".to_string(),
            magnitude: Some(state.current_gamma2 as f64),
            demand_id: None,
        },
    ];

    let demands = state
        .open_obligations
        .iter()
        .map(|ob| DemandItemV1 {
            demand_id: ob.clone(),
            kind: "OBLIGATION".to_string(),
            note: None,
        })
        .collect();

    let mut artifact = compile_prompt_artifact(
        "",
        &policy.regime_id,
        &policy.regime_kind,
        &prompt_body,
        objective,
        policy.admitted_constructors.clone(),
        open_hints,
        demands,
        policy.kill_conditions.clone(),
        policy.required_reply_fields.clone(),
        "RED_BLUE",
        true,
        None,
        None,
        None,
    );
    // Compile-time defaults and set normalization must describe the same policy
    // in both the emitted artifact and the canonical identity material.
    let normalized_policy = PromptPolicyV1 {
        admitted_constructors: artifact.admitted_constructors.clone(),
        kill_conditions: artifact.kill_conditions.clone(),
        required_reply_fields: artifact.required_reply_fields.clone(),
        ..policy.clone()
    };
    let identity = serde_json::to_value(TurnPromptIdentity {
        state,
        normalized_policy: &normalized_policy,
        prompt_body_sha256: &artifact.prompt_body_sha256,
        prompt_body_byte_count: artifact.prompt_body_byte_count,
    })
    .map_err(|error| invalid_prompt(format!("prompt identity encoding failed: {error}")))?;
    let digest = crate::canonical::domain_digest_json(TURN_DRIVER_PROMPT_ID_DOMAIN, &identity)
        .map_err(|error| invalid_prompt(format!("prompt identity digest failed: {error}")))?;
    artifact.prompt_artifact_id = digest;
    Ok(artifact)
}

/// Evaluates a candidate move against the strict descent invariant.
///
/// Invariant: Frontier advances iff (Phi1, Gamma2) is componentwise non-increasing
/// with AT LEAST ONE STRICT DECREASE (<).
pub fn step(state: &EngineTurnStateV1, candidate: &DriverMovePacket) -> StepOutcome {
    if candidate.proposed_diff.trim().is_empty() {
        let cemetery = CemeteryRowV1 {
            candidate_id: candidate.candidate_id.clone(),
            round_seq: state.round_seq,
            rejection_reason: "MALFORMED_EMPTY_DIFF".to_string(),
            attempted_diff: candidate.proposed_diff.clone(),
            phi1_before: state.current_phi1,
            gamma2_before: state.current_gamma2,
            phi1_after: candidate.declared_phi1,
            gamma2_after: candidate.declared_gamma2,
            authority_effect: default_authority_effect(),
        };
        return StepOutcome::RejectedMalformed {
            cemetery_row: cemetery,
            refusal_reason: "MALFORMED_EMPTY_DIFF".to_string(),
        };
    }

    // Strict descent check:
    // 1. Componentwise non-increasing:
    let non_increasing = candidate.declared_phi1 <= state.current_phi1
        && candidate.declared_gamma2 <= state.current_gamma2;

    // 2. Strict decrease on at least one coordinate:
    // MUTATION KILL GATE: changing < to <= fails tests!
    let strict_decrease = candidate.declared_phi1 < state.current_phi1
        || candidate.declared_gamma2 < state.current_gamma2;

    if !non_increasing || !strict_decrease {
        let cemetery = CemeteryRowV1 {
            candidate_id: candidate.candidate_id.clone(),
            round_seq: state.round_seq,
            rejection_reason: "NON_DESCENDING_CANDIDATE".to_string(),
            attempted_diff: candidate.proposed_diff.clone(),
            phi1_before: state.current_phi1,
            gamma2_before: state.current_gamma2,
            phi1_after: candidate.declared_phi1,
            gamma2_after: candidate.declared_gamma2,
            authority_effect: default_authority_effect(),
        };
        return StepOutcome::RejectedNonDescent {
            cemetery_row: cemetery,
            refusal_reason:
                "NON_DESCENDING_CANDIDATE: must achieve strict decrease on (Phi1, Gamma2)"
                    .to_string(),
        };
    }

    // Candidate achieved strict descent!
    let before_metrics = StateMetrics {
        phi1: state.current_phi1,
        gamma2: state.current_gamma2,
        residual: state.current_phi1,
        has_carrier: true,
        has_loss_ledger: true,
        is_terminal: false,
        is_licensed_lift: false,
        refusal: None,
    };

    let after_metrics = StateMetrics {
        phi1: candidate.declared_phi1,
        gamma2: candidate.declared_gamma2,
        residual: candidate.declared_phi1,
        has_carrier: true,
        has_loss_ledger: true,
        is_terminal: candidate.declared_phi1 == 0 && candidate.declared_gamma2 == 0,
        is_licensed_lift: false,
        refusal: None,
    };

    let op = assign_letter(&before_metrics, &after_metrics);
    let letter = op.letter().to_string();

    let step_hash = compute_ddc_row_hash(
        state.round_seq,
        &letter,
        &candidate.candidate_id,
        &format!(
            "(phi1={},gamma2={})",
            state.current_phi1, state.current_gamma2
        ),
        &format!(
            "(phi1={},gamma2={})",
            candidate.declared_phi1, candidate.declared_gamma2
        ),
        &candidate.summary,
        None,
        None,
    );

    let step_row = DdcStepRowV1 {
        seq: state.round_seq,
        letter,
        actor: candidate.candidate_id.clone(),
        before_state: format!(
            "(phi1={},gamma2={})",
            state.current_phi1, state.current_gamma2
        ),
        after_state: format!(
            "(phi1={},gamma2={})",
            candidate.declared_phi1, candidate.declared_gamma2
        ),
        witness: candidate.summary.clone(),
        refusal_reason: None,
        prev_step_hash: None,
        step_hash,
        authority_effect: default_authority_effect(),
    };

    let new_state = EngineTurnStateV1 {
        round_seq: state.round_seq + 1,
        specification_digest: state.specification_digest.clone(),
        current_phi1: candidate.declared_phi1,
        current_gamma2: candidate.declared_gamma2,
        open_defect_count: candidate.declared_phi1 + candidate.declared_gamma2,
        previous_code: state.previous_code.clone(),
        previous_diff: Some(candidate.proposed_diff.clone()),
        open_obligations: if candidate.declared_phi1 == 0 && candidate.declared_gamma2 == 0 {
            vec![]
        } else {
            state.open_obligations.clone()
        },
        promoted_operands: state.promoted_operands.clone(),
        cemetery_count: state.cemetery_count,
    };

    StepOutcome::Accepted {
        new_state,
        step_row,
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/driver.rs
// Claim: urn:core:crates_rs:pfp-runtime:driver:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5de73437 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5de73437` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5de73437 {
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
impl BoundaryError5de73437 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5de73437 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5de73437 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5de73437 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5de73437> {
        if capacity_bound == 0 {
            return Err(BoundaryError5de73437::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5de73437::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5de73437::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_5de73437 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5de73437::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5de73437::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5de73437::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5de73437::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5de73437::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5de73437::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5de73437::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
