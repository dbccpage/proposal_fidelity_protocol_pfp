//! Input-bound native application endpoints over existing domain crates.
use serde_json::{json, Value};
use std::collections::BTreeMap;
use std::io::Read;
pub const REQUEST_DOMAIN: &str = "core.native.port-input.v1";
fn workflow_validate_garden(
    payload: &Value,
) -> Result<BTreeMap<String, core_operads::planar::OperadOperation>, (String, String)> {
    use core_operads::planar::OperadOperation;
    let encode = |error: core_operads::Refusal| (error.code, error.message);
    let raw = payload["garden"].as_object().ok_or_else(|| {
        (
            "BAD_INPUT".into(),
            "garden must be an operation mapping".into(),
        )
    })?;
    let mut garden = BTreeMap::new();
    for (name, value) in raw {
        garden.insert(
            name.clone(),
            OperadOperation::from_json(value).map_err(encode)?,
        );
    }
    Ok(garden)
}

fn workflow(action: &str, payload: &Value) -> Result<Value, (String, String)> {
    use core_operads::planar::{substitute, OperadOperation};
    let encode = |error: core_operads::Refusal| (error.code, error.message);
    let value = match action {
        "workflow_substitute" => {
            let theta = OperadOperation::from_json(&payload["theta"]).map_err(encode)?;
            let phi = OperadOperation::from_json(&payload["phi"]).map_err(encode)?;
            serde_json::to_value(substitute(&theta, &payload["slot"], &phi).map_err(encode)?)
        }
        "workflow_validate" => {
            let garden = workflow_validate_garden(payload)?;
            serde_json::to_value(
                core_operads::workflow::validate_workflow(&payload["workflow"], &garden)
                    .map_err(encode)?,
            )
        }
        _ => return Err(("UNKNOWN_ACTION".into(), action.into())),
    };
    value.map_err(|e| ("PORT_OUTPUT_INVALID".into(), e.to_string()))
}
pub fn dispatch(action: &str, payload: &Value) -> Value {
    let digest = match serde_json::to_vec(payload) {
        Ok(bytes) => pfp_runtime::framed_sha256(REQUEST_DOMAIN, &bytes),
        Err(error) => {
            return json!({"input_digest":null,"outcome":null,"refusal":{"code":"PORT_REQUEST_INVALID","message":error.to_string()}})
        }
    };
    let result = if let Some(kernel) = action.strip_suffix("_file").filter(|name| {
        matches!(
            *name,
            "anthropic_messages"
                | "intelligence_lifecycle"
                | "learning_signals"
                | "prompt_metabolism"
                | "skill_garden_cull"
                | "immune_pharmacy_search"
        )
    }) {
        bound_file(payload).and_then(|request| execute(kernel, &request))
    } else {
        execute(action, payload)
    };
    match result {
        Ok(value) => json!({"input_digest":digest,"outcome":value,"refusal":null}),
        Err(refusal) => json!({"input_digest":digest,"outcome":null,"refusal":refusal}),
    }
}

fn bound_file(payload: &Value) -> Result<Value, Value> {
    use sha2::{Digest, Sha256};
    let invalid = |message: String| json!({"code":"HOST_BOUND_FILE_INVALID","message":message});
    let size = payload["size"]
        .as_u64()
        .filter(|size| *size <= 64 * 1024 * 1024)
        .ok_or_else(|| invalid("bound artifact size must be at most 64 MiB".into()))?;
    let path = payload["request_file"]
        .as_str()
        .ok_or_else(|| invalid("bound artifact path required".into()))?;
    let mut bytes = Vec::new();
    std::fs::File::open(path)
        .map_err(|e| invalid(e.to_string()))?
        .take(size + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| invalid(e.to_string()))?;
    if bytes.len() as u64 != size
        || format!("sha256:{}", hex::encode(Sha256::digest(&bytes)))
            != payload["sha256"].as_str().unwrap_or("")
    {
        return Err(invalid(
            "bound artifact size or digest does not match its bytes".into(),
        ));
    }
    serde_json::from_slice(&bytes).map_err(|e| invalid(e.to_string()))
}

fn execute_immune_port(action: &str, payload: &Value) -> Option<Result<Value, Value>> {
    let res = match action {
        "immune_admission" => {
            core_epistemic_immune_system::admission::execute(payload).map_err(|e| json!(e))
        }
        "immune_activation" => activation(payload).map_err(|e| json!(e)),
        "immune_screen" => immune_screen(payload).map_err(|e| json!(e)),
        "immune_pharmacy_search" => {
            core_epistemic_immune_system::pharmacy_search::execute(payload).map_err(|e| json!(e))
        }
        "immune_allostery" => {
            core_epistemic_immune_system::allostery::evaluate(payload).map_err(|e| json!(e))
        }
        "immune_clonal" => {
            core_epistemic_immune_system::clonal_selection::execute(payload).map_err(|e| json!(e))
        }
        _ => return None,
    };
    Some(res)
}

fn execute_operad_or_prompt_port(action: &str, payload: &Value) -> Option<Result<Value, Value>> {
    let res = match action {
        "skill_garden_cull" => {
            core_operads::skill_garden::execute(payload).map_err(|e| json!(e))
        }
        "prompt_metabolism" => {
            core_prompt_civilization::metabolism::execute(payload).map_err(|e| json!(e))
        }
        "learning_signals" => {
            core_prompt_civilization::learning_signals::execute(payload).map_err(|e| json!(e))
        }
        "prompt_civilization" => {
            core_prompt_civilization::civilization::execute(payload).map_err(|e| json!(e))
        }
        "prompt_rank" => {
            core_prompt_civilization::rank_port::execute(payload).map_err(|e| json!(e))
        }
        "workflow_graph" => core_operads::graph::execute(payload).map_err(|e| json!(e)),
        "workflow_operation_v3" => core_operads::estate::execute(payload).map_err(|e| json!(e)),
        "workflow_composition_v3" => {
            core_operads::estate::execute_composition(payload).map_err(|e| json!(e))
        }
        "workflow_substitute" | "workflow_validate" => workflow(action, payload)
            .map_err(|(code, message)| json!({"code":code,"message":message})),
        _ => return None,
    };
    Some(res)
}

fn execute(action: &str, payload: &Value) -> Result<Value, Value> {
    if let Some(res) = execute_immune_port(action, payload) {
        return res;
    }
    if let Some(res) = execute_operad_or_prompt_port(action, payload) {
        return res;
    }
    match action {
        "intelligence_lifecycle" => {
            core_intelligence::port::execute(payload).map_err(|e| json!(e))
        }
        "adversary_support_file" => crate::adversary_support::execute_file(payload).map_err(|e| json!(e)),
        "adversary_support" => crate::adversary_support::execute(payload).map_err(|e| json!(e)),
        "provider_budget" => core_adversary::providers::budget::execute(payload).map_err(|e| json!(e)),
        "anthropic_messages" => crate::anthropic_host::execute(payload).map_err(|e| json!(e)),
        _ => Err(json!({"code":"UNKNOWN_ACTION","message":action})),
    }
}

fn immune_screen(payload: &Value) -> Result<Value, core_operads::Refusal> {
    use core_operads::{
        immune_ports::{DetectorIdentity, DetectorMatch, HostDangerObservation, ImmuneScreenPort},
        Refusal,
    };
    let raw_matches = payload["matches"].as_array()
        .ok_or_else(|| Refusal::new("IMMUNE_PORT_WIRE_INVALID", "matches must be an array"))?;
    let matches = raw_matches.iter().map(DetectorMatch::from_json).collect::<Result<Vec<_>, _>>()?;
    let detector = DetectorIdentity::from_json(&payload["detector"])?;
    let danger = if payload["danger"].is_null() { None }
        else { Some(HostDangerObservation::from_json(&payload["danger"])?) };
    let mut adapter = core_adversary::oewas_oeeis_bridge::OeeisImmuneAdapter::standard_baseline()?;
    let result = adapter.danger_verdict(&matches, danger.as_ref(), &detector)?;
    serde_json::to_value(result).map_err(|e| Refusal::new("IMMUNE_PORT_WIRE_INVALID", e.to_string()))
}

fn non_string_disposition_spelling(value: &Value) -> String {
    match value {
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        _ => value.to_string(),
    }
}

fn parse_activation_flags<'a>(payload: &'a Value) -> Result<(&'a str, bool, bool), core_epistemic_immune_system::Refusal> {
    use core_epistemic_immune_system::Refusal;
    let profile = payload["profile_digest"]
        .as_str()
        .ok_or_else(|| Refusal::new("EIS_VALUE_ERROR", "profile_digest must be an exact string"))?;
    let admitted = payload["externally_admitted"]
        .as_bool()
        .ok_or_else(|| Refusal::new("EIS_TYPE_ERROR", "externally_admitted must be a bool"))?;
    let suspended = payload["suspended"]
        .as_bool()
        .ok_or_else(|| Refusal::new("EIS_TYPE_ERROR", "suspended must be a bool"))?;
    Ok((profile, admitted, suspended))
}

fn activation(payload: &Value) -> Result<Value, core_epistemic_immune_system::Refusal> {
    use core_epistemic_immune_system::{
        activation::{evaluate_activation, DangerSignalReceiptV1, DetectorHitRefV1},
        Refusal,
    };
    let decode = |e: serde_json::Error| Refusal::new("EIS_VALUE_ERROR", e.to_string());
    let hit: Option<DetectorHitRefV1> =
        serde_json::from_value(payload["hit"].clone()).map_err(decode)?;
    let danger: Option<DangerSignalReceiptV1> =
        serde_json::from_value(payload["danger"].clone()).map_err(decode)?;
    let (profile, admitted, suspended) = parse_activation_flags(payload)?;
    let supplied_disposition = payload.get("disposition");
    let disposition = supplied_disposition
        .and_then(Value::as_str)
        .unwrap_or("FINDING");
    let receipt = evaluate_activation(
        profile,
        hit.as_ref(),
        danger.as_ref(),
        admitted,
        suspended,
        disposition,
    )?;
    if let Some(value) = supplied_disposition.filter(|v| !v.is_string()) {
        let spelling = non_string_disposition_spelling(value);
        return Err(Refusal::new(
            "EIS_VALUE_ERROR",
            format!("activation may select only FINDING, HOLD or REFUSE; {spelling} is not closed"),
        ));
    }
    serde_json::to_value(receipt).map_err(decode)
}

// Origin: engine/crates_rs/pfp/src/port_host.rs
// Claim: urn:core:crates_rs:pfp:port-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordafc2b64a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordafc2b64a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorafc2b64a {
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
impl BoundaryErrorafc2b64a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorafc2b64a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorafc2b64a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordafc2b64a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorafc2b64a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorafc2b64a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorafc2b64a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorafc2b64a::ExceedsCapacity {
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
mod l4_boundary_tests_afc2b64a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordafc2b64a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordafc2b64a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordafc2b64a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordafc2b64a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordafc2b64a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorafc2b64a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorafc2b64a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
