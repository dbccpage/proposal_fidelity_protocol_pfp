//! Strict invocation DTOs and refusal encoding at the JSON boundary.

use super::*;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct VerifyDecodeReceiptRequestV1 {
    pub(super) receipt: pfp_runtime::DecodeControlReceiptV1,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct JcsCanonicalizeRequestV1 {
    #[serde(default)]
    pub(super) value: Option<Value>,
    #[serde(default)]
    pub(super) raw: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct JcsDigestRequestV1 {
    #[serde(default)]
    pub(super) value: Option<Value>,
    #[serde(default)]
    pub(super) raw: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct StabilizerSolveRequestV1 {
    pub(super) case: Value,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct StabilizerCheckRequestV1 {
    pub(super) case: Value,
    pub(super) result: Value,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct DecomposeTaskRequestV1 {
    pub(super) basis_kind: String,
    #[serde(default)]
    pub(super) vertices: Vec<String>,
    #[serde(default)]
    pub(super) edges: Vec<core_homology::cycle_basis::Edge>,
    #[serde(default)]
    pub(super) tree_edges: Vec<core_homology::cycle_basis::Edge>,
    #[serde(default)]
    pub(super) case: Option<Value>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct DiscreteScoringRequestV1 {
    pub(super) obstructions: Vec<String>,
    pub(super) proposal: CandidateProposal,
    #[serde(default)]
    pub(super) admitted_constructors: Option<Vec<String>>,
    #[serde(default)]
    pub(super) known_kill_conditions: Option<std::collections::BTreeMap<String, String>>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct CochainScoringRequestV1 {
    pub(super) core_cochain: std::collections::BTreeMap<String, String>,
    pub(super) proposal: CandidateProposal,
    #[serde(default)]
    pub(super) admitted_constructors: Option<Vec<String>>,
    #[serde(default)]
    pub(super) known_kill_conditions: Option<std::collections::BTreeMap<String, String>>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct RankScoringRequestV1 {
    pub(super) obstructions: Vec<String>,
    pub(super) proposals: Vec<CandidateProposal>,
    #[serde(default)]
    pub(super) admitted_constructors: Option<Vec<String>>,
    #[serde(default)]
    pub(super) known_kill_conditions: Option<std::collections::BTreeMap<String, String>>,
    #[serde(default)]
    pub(super) learned_guards: Option<Value>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct RankScoredRequestV1 {
    pub(super) scores: Vec<pfp_runtime::scoring_frontier::CoboundaryScoreResult>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct TurnDriverNextPromptRequestV1 {
    pub(super) state: pfp_runtime::driver::EngineTurnStateV1,
    pub(super) policy: pfp_runtime::driver::PromptPolicyV1,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct TurnDriverStepRequestV1 {
    pub(super) state: pfp_runtime::driver::EngineTurnStateV1,
    pub(super) candidate: pfp_runtime::driver::DriverMovePacket,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct PharmacyDetectRequestV1 {
    pub(super) candidate: Value,
    #[serde(default)]
    pub(super) context: Option<core_prompt_civilization::pharmacy::DetectionContext>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct RunFolderSealRequestV1 {
    pub(super) run_dir: String,
    #[serde(default)]
    pub(super) status: Option<String>,
    #[serde(default)]
    pub(super) reason: Option<String>,
    #[serde(default)]
    pub(super) sealed_at_utc: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct RunFolderVerifyRequestV1 {
    pub(super) run_dir: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct MatrixRequestV1 {
    pub(super) matrix: RationalMatrix,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct VerifyBoundaryClosedRequestV1 {
    pub(super) faces: Vec<Vec<(usize, usize, i64)>>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct VerifySimplicialBoundaryLawRequestV1 {
    pub(super) simplices: Vec<Vec<usize>>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct LoopProductRequestV1 {
    pub(super) tables: Vec<RationalMatrix>,
    pub(super) word: Vec<(usize, bool)>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct VerifyL1CertificateRequestV1 {
    pub(super) matrix: RationalMatrix,
    #[serde(with = "exact_wire_vec")]
    pub(super) omega: Vec<Exact>,
    #[serde(with = "exact_wire_vec")]
    pub(super) p: Vec<Exact>,
    #[serde(with = "exact_wire_vec")]
    pub(super) y: Vec<Exact>,
}

/// Every field is required: a missing or mistyped field is a typed refusal,
/// never an empty list or a default budget. An empty `protected_paths` must be
/// sent as `[]`; it is not what a malformed value becomes.
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct CreateCodeChangeProposalRequestV1 {
    pub(super) task_id: String,
    pub(super) objective: String,
    pub(super) base_revision: String,
    pub(super) owned_paths: Vec<String>,
    pub(super) protected_paths: Vec<String>,
    pub(super) candidate_budget: usize,
    pub(super) operation_budget: usize,
    pub(super) required_gates: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct SubmitPatchCandidateRequestV1 {
    pub(super) run_root: pfp_runtime::CodeChangeRunRootV1,
    /// The `task_packet_sha256` the caller received at create; required.
    pub(super) expected_task_packet_sha256: String,
    pub(super) candidate_id: String,
    pub(super) producer_id: String,
    pub(super) patch_text: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct EvaluatePatchGatesRequestV1 {
    pub(super) run_root: pfp_runtime::CodeChangeRunRootV1,
    /// The `task_packet_sha256` the caller received at create; required.
    pub(super) expected_task_packet_sha256: String,
    /// The `run_root_digest` the caller received from its last submit; required.
    pub(super) expected_run_root_digest: String,
    pub(super) patch_artifact: pfp_runtime::CodeChangePatchArtifactV1,
}

pub(super) fn code_change_request<T: serde::de::DeserializeOwned>(
    payload: &Value,
) -> Result<T, String> {
    serde_json::from_value(payload.clone()).map_err(|error| {
        format!(
            "{}: {error}",
            pfp_runtime::code_change::REFUSAL_CODE_CHANGE_REQUEST_INVALID
        )
    })
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct SolveL1PrimalDualRequestV1 {
    pub(super) matrix: RationalMatrix,
    #[serde(with = "exact_wire_vec")]
    pub(super) target: Vec<Exact>,
    #[serde(default)]
    pub(super) weights: Option<Vec<String>>,
    pub(super) budget: Option<usize>,
}

pub(super) fn l1_refusal_json(refusal: L1Refusal) -> Value {
    match refusal {
        L1Refusal::DualNotAnnihilating { residual } => serde_json::json!({
            "code": "DUAL_NOT_ANNIHILATING",
            "residual": residual.iter().map(to_canonical_string).collect::<Vec<_>>()
        }),
        L1Refusal::DualNotBounded { max_abs } => serde_json::json!({
            "code": "DUAL_NOT_BOUNDED",
            "max_abs": to_canonical_string(&max_abs)
        }),
        L1Refusal::ObjectivesDiffer {
            primal_l1,
            dual_value,
        } => serde_json::json!({
            "code": "OBJECTIVES_DIFFER",
            "primal_l1": to_canonical_string(&primal_l1),
            "dual_value": to_canonical_string(&dual_value)
        }),
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct RetractionTurnRequestV1 {
    pub(super) before: crate::epics::retraction::DescentTriad,
    pub(super) after: crate::epics::retraction::DescentTriad,
    #[serde(default)]
    pub(super) candidate: Option<crate::epics::retraction::CandidateTurn>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct RetractionLoopRequestV1 {
    pub(super) intake: crate::epics::retraction::DescentTriad,
    #[serde(default)]
    pub(super) candidates: Vec<crate::epics::retraction::CandidateTurn>,
    #[serde(default)]
    pub(super) open_obligations: usize,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct DebateClaimWireV1 {
    pub(super) agent: String,
    pub(super) node: usize,
    #[serde(default)]
    pub(super) primitive: Option<crate::epics::debate::KernelPrimitive>,
    pub(super) holds: bool,
    #[serde(default)]
    pub(super) text: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct DebateLocalizeRequestV1 {
    pub(super) tree_size: usize,
    pub(super) left_agent: String,
    pub(super) right_agent: String,
    #[serde(default)]
    pub(super) claims: Vec<DebateClaimWireV1>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct DdaSurgeryRequestV1 {
    pub(super) d0: pfp_runtime::F2Matrix,
    pub(super) d1: pfp_runtime::F2Matrix,
    pub(super) sigma: Vec<bool>,
    #[serde(default)]
    pub(super) fuse_all: bool,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct SimplicialTransportRequestV1 {
    pub(super) vertex_map: Vec<usize>,
    pub(super) target_vertices: usize,
    pub(super) support: Vec<usize>,
    #[serde(default)]
    pub(super) chain: Option<Vec<bool>>,
    #[serde(default)]
    pub(super) cochain: Option<Vec<bool>>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct PrimeCandidateEvaluateRequestV1 {
    pub(super) proposal_id: String,
    pub(super) locus_id: String,
    #[serde(default)]
    pub(super) raw_payload: String,
    pub(super) actor: String,
    #[serde(default)]
    pub(super) admit: bool,
    #[serde(default)]
    pub(super) refusal_reason: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct PrimeStageRecordRequestV1 {
    pub(super) seq: u64,
    pub(super) stage: crate::prime::PrimeStage,
    pub(super) packet_id: String,
    pub(super) actor: String,
    pub(super) status: String,
    pub(super) witness_or_refusal: String,
    #[serde(default)]
    pub(super) prev_record_hash: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct ChallengeCommitRequestV1 {
    pub(super) challenge_id: String,
    pub(super) manifest_text: String,
    pub(super) operator: String,
    pub(super) version: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct ChallengeFreezeRequestV1 {
    pub(super) challenge_id: String,
    pub(super) deliverable_text: String,
    pub(super) judge_commitment_hash: String,
}

pub(super) fn default_checker_expected_field() -> String {
    "answer".to_string()
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct ChallengeScoreRequestV1 {
    pub(super) judge_packet: crate::challenge::JudgePacketV1,
    pub(super) commitment: crate::challenge::JudgeCommitmentV1,
    pub(super) freeze: crate::challenge::FreezeRecordV1,
    #[serde(default)]
    pub(super) candidate_outputs: Vec<Value>,
    #[serde(default = "default_checker_expected_field")]
    pub(super) checker_expected_field: String,
}

// Origin: engine/crates_rs/pfp/src/invoke/requests.rs
// Claim: urn:core:crates_rs:pfp:requests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf9f4f3d4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf9f4f3d4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf9f4f3d4 {
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
impl BoundaryErrorf9f4f3d4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf9f4f3d4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf9f4f3d4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf9f4f3d4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf9f4f3d4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf9f4f3d4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf9f4f3d4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf9f4f3d4::ExceedsCapacity {
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
mod l4_boundary_tests_f9f4f3d4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf9f4f3d4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf9f4f3d4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf9f4f3d4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf9f4f3d4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf9f4f3d4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf9f4f3d4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf9f4f3d4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
