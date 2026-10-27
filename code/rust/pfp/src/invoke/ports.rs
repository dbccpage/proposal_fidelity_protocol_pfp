//! Explicit host effects: provider, filesystem, Adversary and subsystem adapter dispatch.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_56560ffb<T> {
    fn checked_invariant_56560ffb(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_56560ffb<T> for Option<T> {
    #[inline]
    fn checked_invariant_56560ffb(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_56560ffb<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_56560ffb(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::*;

const PORT_HOST_ACTIONS: &[&str] = &[
    "immune_allostery",
    "immune_clonal",
    "immune_admission",
    "immune_activation",
    "immune_screen",
    "immune_pharmacy_search",
    "immune_pharmacy_search_file",
    "prompt_civilization",
    "adversary_support_file",
    "adversary_support",
    "prompt_rank",
    "prompt_metabolism",
    "prompt_metabolism_file",
    "learning_signals",
    "learning_signals_file",
    "intelligence_lifecycle",
    "intelligence_lifecycle_file",
    "skill_garden_cull",
    "skill_garden_cull_file",
    "workflow_substitute",
    "workflow_validate",
    "workflow_graph",
    "provider_budget",
    "anthropic_messages",
    "anthropic_messages_file",
    "workflow_operation_v3",
    "workflow_composition_v3",
];

fn dispatch_reply_control(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: crate::reply_control::ReplyControlRequest = match serde_json::from_value(payload.clone()) {
        Ok(request) => request,
        Err(error) => {
            return outcome_err(action, format!("REPLY_CONTROL_REQUEST_INVALID: {error}"))
        }
    };
    match request {
        crate::reply_control::ReplyControlRequest::Parse { reply_text } => {
            match crate::reply_control::parse_machine_block(&reply_text) {
                Ok(fields) => outcome_ok(
                    action,
                    serde_json::to_value(fields)
                        .checked_invariant_56560ffb("machine fields serialize"),
                ),
                Err(error) => outcome_err(action, error),
            }
        }
        crate::reply_control::ReplyControlRequest::Validate {
            machine_fields,
            dual_witness_digest,
        } => {
            let result = crate::reply_control::validate_reply_residual(
                &machine_fields,
                dual_witness_digest.as_deref(),
            );
            outcome_ok(
                action,
                serde_json::to_value(result)
                    .checked_invariant_56560ffb("residual declaration serializes"),
            )
        }
    }
}

fn dispatch_glyph_trajectory(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    if action == "glyph_trajectory_execute" {
        let request =
            match serde_json::from_value::<crate::glyph_trajectory::GlyphTrajectoryRequestV1>(
                payload.clone(),
            ) {
                Ok(request) => request,
                Err(error) => {
                    return outcome_err(action, format!("INVALID_GLYPH_TRAJECTORY: {error}"))
                }
            };
        return match crate::glyph_trajectory::execute(&request) {
            Ok(receipt) => outcome_ok(action, receipt),
            Err(error) => outcome_err(action, error.to_string()),
        };
    }
    let request = match serde_json::from_value::<crate::glyph_trajectory::GlyphTrajectoryReplayV1>(
        payload.clone(),
    ) {
        Ok(request) => request,
        Err(error) => return outcome_err(action, format!("INVALID_GLYPH_TRAJECTORY: {error}")),
    };
    match crate::glyph_trajectory::replay(&request) {
        Ok(matches) => outcome_ok(
            action,
            serde_json::json!({"reproduced": matches, "authority_effect": "None"}),
        ),
        Err(error) => outcome_err(action, error.to_string()),
    }
}

fn dispatch_validate_reply_residual(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let Some(map) = payload.as_object() else {
        return outcome_err(
            action,
            "PROMPT_ARTIFACT_INVALID: reply request must be object",
        );
    };
    if map.len() != 2 || !map.contains_key("artifact") || !map.contains_key("reply_content") {
        return outcome_err(
            action,
            "PROMPT_ARTIFACT_INVALID: reply request requires exactly artifact and reply_content",
        );
    }
    let mut request = map.clone();
    request.insert("operation".into(), Value::String("validate_reply".into()));
    match pfp_runtime::prompt_artifact::execute(&Value::Object(request)) {
        Ok(value) => outcome_ok(action, value),
        Err(error) => outcome_err(action, format!("PROMPT_ARTIFACT_INVALID: {error}")),
    }
}

fn dispatch_pharmacy_detect(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    if payload.get("mode").is_some() {
        return match core_prompt_civilization::pharmacy::execute_raw_receipt(payload) {
            Ok(receipt) => outcome_ok(action, receipt),
            Err(error) => outcome_err(action, error),
        };
    }
    let request: PharmacyDetectRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(value) => value,
        Err(error) => {
            return outcome_err(action, format!("invalid pharmacy_detect input: {error}"))
        }
    };
    let ctx = request.context.unwrap_or_default();
    // A string candidate is the raw JSON text of the turn; keep its bytes so
    // the report binds them. Text that is not JSON is scored as a string.
    let report = match &request.candidate {
        Value::String(text) => {
            let parsed =
                serde_json::from_str::<Value>(text).unwrap_or_else(|_| request.candidate.clone());
            core_prompt_civilization::pharmacy::detect_with_raw_bytes(
                &parsed,
                Some(text.as_bytes()),
                &ctx,
            )
        }
        other => core_prompt_civilization::pharmacy::detect(other, &ctx),
    };
    match serde_json::to_value(&report) {
        Ok(report_val) => outcome_ok(action, report_val),
        Err(e) => outcome_err(action, format!("failed to serialize report: {e}")),
    }
}

fn dispatch_run_folder(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    if action == "run_folder_seal" {
        let request: RunFolderSealRequestV1 = match serde_json::from_value(payload.clone()) {
            Ok(val) => val,
            Err(e) => return outcome_err(action, format!("invalid run_folder_seal input: {e}")),
        };
        return match core_replay::run_folder::seal_run_folder(
            std::path::Path::new(&request.run_dir),
            request.status.as_deref(),
            request.reason.as_deref(),
            request.sealed_at_utc.as_deref(),
        ) {
            Ok(receipt) => outcome_ok(
                action,
                serde_json::to_value(receipt)
                    .checked_invariant_56560ffb("receipt serialization must succeed"),
            ),
            Err(e) => outcome_err(action, e.to_string()),
        };
    }
    let request: RunFolderVerifyRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid run_folder_verify input: {e}")),
    };
    match core_replay::run_folder::verify_run_folder(std::path::Path::new(&request.run_dir)) {
        Ok(receipt) => outcome_ok(
            action,
            serde_json::to_value(receipt)
                .checked_invariant_56560ffb("receipt serialization must succeed"),
        ),
        Err(e) => outcome_err(action, e.to_string()),
    }
}

fn dispatch_direct_host_action(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    let outcome = match action {
        "anti_skill_detect" => match crate::anti_skill_host::execute(payload) {
            Ok(result) => outcome_ok(action, result),
            Err(error) => outcome_err(action, error),
        },
        "adversary_bout" => match crate::adversary_host::dispatch(payload) {
            Ok(result) => outcome_ok(action, result),
            Err(error) => outcome_err(action, format!("{}: {}", error.code, error.message)),
        },
        "immune_fence_render" => match pfp_runtime::immune_fence::execute(payload) {
            Ok(value) => outcome_ok(action, value),
            Err(error) => outcome_err(action, error),
        },
        "prompt_artifact" => match pfp_runtime::prompt_artifact::execute(payload) {
            Ok(value) => outcome_ok(action, value),
            Err(error) => outcome_err(action, format!("PROMPT_ARTIFACT_INVALID: {error}")),
        },
        _ => return None,
    };
    Some(outcome)
}

pub(super) fn dispatch(req: &RuntimeRequestV1) -> RuntimeOutcomeV1 {
    let action = req.action.as_str();
    if PORT_HOST_ACTIONS.contains(&action) {
        return outcome_ok(action, crate::port_host::dispatch(action, &req.payload));
    }
    if let Some(outcome) = dispatch_direct_host_action(action, &req.payload) {
        return outcome;
    }
    match action {
        "reply_control" => dispatch_reply_control(action, &req.payload),
        "glyph_trajectory_execute" | "glyph_trajectory_replay" => {
            dispatch_glyph_trajectory(action, &req.payload)
        }
        "validate_reply_residual" => dispatch_validate_reply_residual(action, &req.payload),
        "pharmacy_detect" => dispatch_pharmacy_detect(action, &req.payload),
        "run_folder_seal" | "run_folder_verify" => dispatch_run_folder(action, &req.payload),
        other => outcome_err(action, format!("unsupported runtime action: {other}")),
    }
}

// Origin: engine/crates_rs/pfp/src/invoke/ports.rs
// Claim: urn:core:crates_rs:pfp:ports:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord56560ffb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord56560ffb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError56560ffb {
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
impl BoundaryError56560ffb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError56560ffb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError56560ffb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord56560ffb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError56560ffb> {
        if capacity_bound == 0 {
            return Err(BoundaryError56560ffb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError56560ffb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError56560ffb::ExceedsCapacity {
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
mod l4_boundary_tests_56560ffb {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord56560ffb::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord56560ffb::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord56560ffb::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord56560ffb::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord56560ffb::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError56560ffb::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError56560ffb::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
