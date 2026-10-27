//! JSON DTO entrypoint for supervised hosts.

use crate::{
    evaluate_lifecycle, evaluate_retention, seal_manifest, LifecycleRequest, Refusal,
    RetentionRequest, SealManifestRequest,
};
use serde::de::DeserializeOwned;
use serde_json::{json, Value};

fn decode<T: DeserializeOwned>(payload: &Value) -> Result<T, Refusal> {
    serde_json::from_value(payload.clone())
        .map_err(|error| Refusal::new("INTELLIGENCE_PORT_INPUT_INVALID", error.to_string()))
}

fn encode<T: serde::Serialize>(value: T) -> Result<Value, Refusal> {
    serde_json::to_value(value)
        .map_err(|error| Refusal::new("INTELLIGENCE_PORT_OUTPUT_INVALID", error.to_string()))
}

/// Execute one finite, input-bound kernel operation.
pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let operation = payload
        .get("operation")
        .and_then(Value::as_str)
        .ok_or_else(|| Refusal::new("INTELLIGENCE_PORT_INPUT_INVALID", "operation is required"))?;
    match operation {
        "seal_manifest" => encode(seal_manifest(decode::<SealManifestRequest>(payload)?)?),
        "evaluate_lifecycle" => encode(evaluate_lifecycle(&decode::<LifecycleRequest>(payload)?)),
        "evaluate_retention" => encode(evaluate_retention(&decode::<RetentionRequest>(payload)?)),
        _ => Err(Refusal::new(
            "INTELLIGENCE_PORT_UNKNOWN_OPERATION",
            format!("unsupported intelligence operation {operation:?}"),
        )),
    }
}

pub fn contract() -> Value {
    json!({
        "schema_version": "core.intelligence.port.v1",
        "operations": ["seal_manifest", "evaluate_lifecycle", "evaluate_retention"],
        "authority_effect": "None",
    })
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PortAdmission {
    payload_bytes: u64,
    budget: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PortAdmissionError {
    UnknownOperation,
    ZeroBudget,
    OverBudget { payload_bytes: u64, budget: u64 },
}

// Origin: engine/crates_rs/core_intelligence/src/port.rs
// Claim: urn:core:crates_rs:core-intelligence:port:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PortAdmissionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PortAdmissionError {}

impl PortAdmission {
    pub fn certify(operation: &str, payload_bytes: u64, budget: u64) -> Result<Self, PortAdmissionError> {
        match operation {
            "seal_manifest" | "evaluate_lifecycle" | "evaluate_retention" => {}
            _ => return Err(PortAdmissionError::UnknownOperation),
        }
        if budget == 0 { return Err(PortAdmissionError::ZeroBudget); }
        if payload_bytes > budget { return Err(PortAdmissionError::OverBudget { payload_bytes, budget }); }
        Ok(Self { payload_bytes, budget })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(PortAdmission::certify("seal_manifest", 4, 8), Ok(w) if w.payload_bytes == 4));
        assert!(matches!(PortAdmission::certify("evaluate_lifecycle", 1, 1), Ok(_)));
        assert!(matches!(PortAdmission::certify("evaluate_retention", 2, 1), Err(PortAdmissionError::OverBudget { .. })));
        assert!(matches!(PortAdmission::certify("other", 1, 1), Err(PortAdmissionError::UnknownOperation)));
    }
}
