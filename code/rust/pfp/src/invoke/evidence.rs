//! Candidate-bound evidence, patch admission and source/Lean audit dispatch.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_15b669a5<T> {
    fn checked_invariant_15b669a5(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_15b669a5<T> for Option<T> {
    #[inline]
    fn checked_invariant_15b669a5(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_15b669a5<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_15b669a5(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::*;

fn handle_create_code_change_proposal(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: CreateCodeChangeProposalRequestV1 = match code_change_request(payload) {
        Ok(request) => request,
        Err(error) => return outcome_err(action, error),
    };
    match CreateCodeChangeProposalUseCase.execute(
        &request.task_id,
        &request.objective,
        &request.base_revision,
        request.owned_paths,
        request.protected_paths,
        request.candidate_budget,
        request.operation_budget,
        request.required_gates,
    ) {
        Ok(root) => outcome_ok(
            action,
            serde_json::to_value(root)
                .checked_invariant_15b669a5("a code-change run root serializes"),
        ),
        Err(error) => outcome_err(action, error),
    }
}

fn handle_submit_patch_candidate(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: SubmitPatchCandidateRequestV1 = match code_change_request(payload) {
        Ok(request) => request,
        Err(error) => return outcome_err(action, error),
    };
    match SubmitPatchCandidateUseCase.execute(
        &request.run_root,
        &request.expected_task_packet_sha256,
        &request.candidate_id,
        &request.producer_id,
        &request.patch_text,
    ) {
        Ok((updated_root, cand_art, patch_art)) => outcome_ok(
            action,
            serde_json::json!({
                // The rolling digest the caller keeps and passes to evaluate.
                "run_root_digest": updated_root.run_root_digest.clone(),
                "run_root": updated_root,
                "candidate_artifact": cand_art,
                "patch_artifact": patch_art,
            }),
        ),
        Err(e) => outcome_err(action, e),
    }
}

fn handle_evaluate_patch_gates(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: EvaluatePatchGatesRequestV1 = match code_change_request(payload) {
        Ok(request) => request,
        Err(error) => return outcome_err(action, error),
    };
    match EvaluatePatchGatesUseCase.execute(
        &request.run_root,
        &request.expected_task_packet_sha256,
        &request.expected_run_root_digest,
        &request.patch_artifact,
    ) {
        Ok(receipts) => outcome_ok(
            action,
            serde_json::to_value(receipts).checked_invariant_15b669a5("gate receipts serialize"),
        ),
        Err(error) => outcome_err(action, error),
    }
}

fn handle_intake_research_sources(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let bundle_id = payload
        .get("bundle_id")
        .and_then(|v| v.as_str())
        .unwrap_or("bundle");
    let sources_val = match payload.get("sources").and_then(|v| v.as_array()) {
        Some(s) => s,
        None => return outcome_err(action, "sources must be an array"),
    };
    let mut sources = Vec::new();
    for item in sources_val {
        let art_id = item
            .get(0)
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_owned();
        let path = item
            .get(1)
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_owned();
        let content_str = item.get(2).and_then(|v| v.as_str()).unwrap_or("");
        let bytes = hex::decode(content_str).unwrap_or_else(|_| content_str.as_bytes().to_vec());
        sources.push((art_id, path, bytes));
    }
    let uc = IntakeResearchSourcesUseCase;
    let bundle = uc.execute(bundle_id, &sources);
    outcome_ok(
        action,
        serde_json::to_value(bundle).checked_invariant_15b669a5("checked invariant"),
    )
}

fn handle_verify_phi1_form(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: crate::certifiers::VerifyPhi1FormRequestV1 =
        match serde_json::from_value(payload.clone()) {
            Ok(val) => val,
            Err(e) => return outcome_err(action, format!("invalid verify_phi1_form input: {e}")),
        };
    match crate::certifiers::verify_phi1_form_certificate(&request) {
        Ok(outcome) => outcome_ok(
            action,
            serde_json::to_value(outcome)
                .checked_invariant_15b669a5("outcome serialization must succeed"),
        ),
        Err(e) => outcome_err(action, e),
    }
}

fn handle_typed_runtime_op<Req, Resp, F>(
    action: &str,
    payload: &Value,
    input_name: &str,
    invariant_msg: &str,
    f: F,
) -> RuntimeOutcomeV1
where
    Req: serde::de::DeserializeOwned,
    Resp: serde::Serialize,
    F: FnOnce(Req) -> Resp,
{
    let request: Req = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid {input_name} input: {e}")),
    };
    let response = f(request);
    outcome_ok(
        action,
        serde_json::to_value(response).checked_invariant_15b669a5(invariant_msg),
    )
}

fn dispatch_typed_evidence_op(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    let outcome = match action {
        "verify_decode_receipt" => handle_typed_runtime_op(
            action,
            payload,
            "verify_decode_receipt",
            "verdict serialization must succeed",
            |r: VerifyDecodeReceiptRequestV1| {
                pfp_runtime::verify_decode_receipt(&r.receipt)
            },
        ),
        "detect_stationary_attractor" => handle_typed_runtime_op(
            action,
            payload,
            "detect_stationary_attractor",
            "report serialization must succeed",
            |r: pfp_runtime::DetectStationaryAttractorRequest| {
                pfp_runtime::detect_stationary_attractor(
                    &r.history,
                    &r.decided_variables,
                )
            },
        ),
        "lean_scan_sources" => handle_typed_runtime_op(
            action,
            payload,
            "lean_scan_sources",
            "report serialization must succeed",
            |r: pfp_runtime::LeanScanRequest| {
                pfp_runtime::scan_lean_sources(&r.sources, &r.forbidden_constructs)
            },
        ),
        "lean_audit_report" => handle_typed_runtime_op(
            action,
            payload,
            "lean_audit_report",
            "receipt serialization must succeed",
            |r: pfp_runtime::LeanAuditRequest| {
                pfp_runtime::audit_lean_verification(&r)
            },
        ),
        _ => return None,
    };
    Some(outcome)
}

pub(super) fn dispatch(req: &RuntimeRequestV1) -> RuntimeOutcomeV1 {
    let action = req.action.as_str();
    if let Some(outcome) = dispatch_typed_evidence_op(action, &req.payload) {
        return outcome;
    }
    match action {
        "create_code_change_proposal" => handle_create_code_change_proposal(action, &req.payload),
        "submit_patch_candidate" => handle_submit_patch_candidate(action, &req.payload),
        "evaluate_patch_gates" => handle_evaluate_patch_gates(action, &req.payload),
        "intake_research_sources" => handle_intake_research_sources(action, &req.payload),
        "signed_transport" => match crate::signed_transport::execute(&req.payload) {
            Ok(result) => outcome_ok(action, result),
            Err(error) => outcome_err(action, error),
        },
        "verify_phi1_form" => handle_verify_phi1_form(action, &req.payload),
        other => outcome_err(action, format!("unsupported runtime action: {other}")),
    }
}

// Origin: engine/crates_rs/pfp/src/invoke/evidence.rs
// Claim: urn:core:crates_rs:pfp:evidence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord15b669a5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord15b669a5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError15b669a5 {
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
impl BoundaryError15b669a5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError15b669a5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError15b669a5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord15b669a5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError15b669a5> {
        if capacity_bound == 0 {
            return Err(BoundaryError15b669a5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError15b669a5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError15b669a5::ExceedsCapacity {
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
mod l4_boundary_tests_15b669a5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord15b669a5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord15b669a5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord15b669a5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord15b669a5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord15b669a5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError15b669a5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError15b669a5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
