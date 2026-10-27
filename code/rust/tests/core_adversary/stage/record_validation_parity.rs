use core_adversary::stage::packets::{AgentResult, LicensedWorkflowPlan, WorkPacket};
use core_adversary::stage::run::{ProgressMeasure, SceneVisit, StopCondition, SwarmRunState};
use core_adversary::stage::topology::{
    NodeAssignment, SceneGraph, SceneSpec, SceneTransition, SeatRequirement, SwarmDefinition,
    SwarmProfile,
};
use serde::de::DeserializeOwned;
use serde_json::Value;

fn decode<T: DeserializeOwned>(value: &Value) -> Result<(), serde_json::Error> {
    serde_json::from_slice::<T>(&serde_json::to_vec(value)?).map(|_| ())
}

fn decode_execution_record(name: &str, input: &Value) -> Result<(), serde_json::Error> {
    match name {
        "plan" => decode::<LicensedWorkflowPlan>(input),
        "packet" => decode::<WorkPacket>(input),
        "result" => decode::<AgentResult>(input),
        "progress" => decode::<ProgressMeasure>(input),
        "state" => decode::<SwarmRunState>(input),
        "visit" => decode::<SceneVisit>(input),
        "stop" => decode::<StopCondition>(input),
        other => panic!("unknown record {other}"),
    }
}

fn decode_record_by_name(name: &str, input: &Value) -> Result<(), serde_json::Error> {
    match name {
        "seat" => decode::<SeatRequirement>(input),
        "assignment" => decode::<NodeAssignment>(input),
        "scene" => decode::<SceneSpec>(input),
        "transition" => decode::<SceneTransition>(input),
        "definition" => decode::<SwarmDefinition>(input),
        "graph" => decode::<SceneGraph>(input),
        "profile" => decode::<SwarmProfile>(input),
        other => decode_execution_record(other, input),
    }
}

#[test]
fn independent_python_constructor_refusals() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_record_validation_v1.json"))?;
    let vectors = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(vectors.len(), 103);
    for (index, row) in vectors.iter().enumerate() {
        let input = &row["input"];
        let outcome = decode_record_by_name(row["record"].as_str().unwrap(), input);
        let error = outcome
            .err()
            .ok_or_else(|| format!("vector {index} unexpectedly accepted"))?
            .to_string();
        // Serde adds a JSON location to the unchanged domain error message.
        let message = error
            .rsplit_once(" at line ")
            .map_or(error.as_str(), |(message, _)| message);
        assert_eq!(
            message,
            row["python_error"]
                .as_str()
                .ok_or("python_error required")?,
            "constructor refusal {index}: {}",
            row["record"]
        );
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/record_validation_parity.rs
// Claim: urn:core:crates_rs:tests:record-validation-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
