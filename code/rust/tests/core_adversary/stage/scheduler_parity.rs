use core_adversary::stage::canonical::semantic_id;
use core_adversary::stage::packets::{AgentResult, LicensedWorkflowPlan, WorkPacket};
use core_adversary::stage::ports::SchedulerPort;
use core_adversary::stage::run::{ProgressMeasure, StopCondition, SwarmRunState};
use core_adversary::stage::scheduler::{validate_swarm_composition, DeterministicScheduler};
use core_adversary::stage::topology::{SceneGraph, SwarmDefinition, SwarmProfile};
use serde::{de::DeserializeOwned, Serialize};
use serde_json::{json, Value};

fn decode<T: DeserializeOwned>(value: &Value) -> Result<T, serde_json::Error> {
    // Keep exact numbers on the JSON seam rather than Value's generic visitor.
    serde_json::from_slice(&serde_json::to_vec(value)?)
}

fn string_result<T: Serialize>(value: Result<T, core_adversary::stage::ports::Refusal>) -> Value {
    match value {
        Ok(value) => json!({"ok": value}),
        Err(error) => json!({"error": error.message}),
    }
}

fn scheduler(
    value: &Value,
    stop: &Value,
) -> Result<DeterministicScheduler, Box<dyn std::error::Error>> {
    Ok(DeterministicScheduler::new(
        decode(&value["definition"])?,
        decode(&value["profile"])?,
        decode(&value["graph"])?,
        decode(&value["plan"])?,
        decode(stop)?,
    )?)
}

fn eval_composition_row(base: &Value, index: usize, row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    let definition: SwarmDefinition = decode(&row["definition"])?;
    let profile: SwarmProfile = decode(&row["profile"])?;
    let graph: SceneGraph = decode(&row["graph"])?;
    let plan: LicensedWorkflowPlan = decode(&row["plan"])?;
    let composition = match validate_swarm_composition(&definition, &profile, &graph, &plan) {
        Ok(()) => json!({"ok": null}),
        Err(error) => json!({"error": error}),
    };
    let initialized = match DeterministicScheduler::new(definition, profile, graph, plan, decode(&base["stop"])?) {
        Ok(_) => json!({"ok": true}),
        Err(error) => json!({"error": error.message}),
    };
    assert_eq!(initialized, row["initialized"], "constructor vector {index}");
    Ok(composition)
}

fn eval_advance_row(
    kernel: &mut DeterministicScheduler,
    index: usize,
    row: &Value,
) -> Result<Value, Box<dyn std::error::Error>> {
    let state: SwarmRunState = decode(&row["state"])?;
    let result: AgentResult = decode(&row["result"])?;
    let progress: ProgressMeasure = decode(&row["progress"])?;
    assert_eq!(serde_json::to_value(&state)?, row["state"], "state round trip {index}");
    assert_eq!(serde_json::to_value(&result)?, row["result"], "result round trip {index}");
    assert_eq!(serde_json::to_value(&progress)?, row["progress"], "progress round trip {index}");
    Ok(match SchedulerPort::advance(kernel, &state, &result, &progress) {
        Ok(state) => json!({"ok": state}),
        Err(error) => json!({"error": error}),
    })
}

fn eval_scheduler_row(
    base: &Value,
    kernel: &mut DeterministicScheduler,
    index: usize,
    row: &Value,
) -> Result<Value, Box<dyn std::error::Error>> {
    match row["op"].as_str().unwrap() {
        "semantic_id" => Ok(string_result(semantic_id(
            row["domain"].as_str().unwrap(),
            row["payload"].as_object().unwrap(),
        ))),
        "composition" => eval_composition_row(base, index, row),
        "start" => Ok(string_result(SchedulerPort::start(
            kernel,
            row["run_key"].as_str().unwrap(),
            &decode::<WorkPacket>(&row["packet"])?,
        ))),
        "advance" => eval_advance_row(kernel, index, row),
        "replay" => Ok(string_result(kernel.replay(
            "run-one",
            &decode::<WorkPacket>(&base["packet"])?,
            &decode::<Vec<AgentResult>>(&row["results"])?,
            &decode::<Vec<ProgressMeasure>>(&row["progress_measures"])?,
        ))),
        op => panic!("unknown op {op}"),
    }
}

#[test]
fn frozen_python_scheduler_and_identity_vectors() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_scheduler_v1.json"))?;
    let base = &fixture["base"];
    let mut kernel = scheduler(base, &base["stop"])?;
    assert_eq!(serde_json::to_value(SchedulerPort::plan(&kernel))?, base["plan"]);
    let vectors = fixture["vectors"].as_array().ok_or("vectors must be an array")?;
    assert_eq!(vectors.len(), 38);
    for (index, row) in vectors.iter().enumerate() {
        let actual = eval_scheduler_row(base, &mut kernel, index, row)?;
        assert_eq!(actual, row["expected"], "scheduler vector {index}: {}", row["op"]);
    }
    Ok(())
}

#[test]
fn packet_identity_and_immutable_boundaries_reject_forged_input(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_scheduler_v1.json"))?;
    let base = &fixture["base"];
    let mut packet = base["packet"].clone();
    packet["objective"] = json!("changed without changing its identity");
    assert!(decode::<WorkPacket>(&packet).is_err());
    packet["packet_id"] = json!("");
    let fresh: WorkPacket = decode(&packet)?;
    assert_ne!(
        fresh.packet_id(),
        base["packet"]["packet_id"]
            .as_str()
            .ok_or("packet_id required")?
    );
    for bad in [json!(true), json!(1.0), json!(-1), json!(1_000_001)] {
        packet["budget_units"] = bad;
        assert!(decode::<WorkPacket>(&packet).is_err());
    }
    let mut graph = base["graph"].clone();
    graph["graph_id"] = json!("");
    graph["transitions"][0]["target_scene_id"] = json!("absent");
    assert!(decode::<SceneGraph>(&graph).is_err());
    graph = base["graph"].clone();
    graph["authority_effect"] = json!("Accept");
    assert!(decode::<SceneGraph>(&graph).is_err());
    let mut progress = fixture["vectors"]
        .as_array()
        .ok_or("vectors required")?
        .iter()
        .find(|row| row["op"] == "advance")
        .ok_or("advance required")?["progress"]
        .clone();
    progress["progressed"] = json!(false);
    assert!(decode::<ProgressMeasure>(&progress).is_err());
    let mut stop = base["stop"].clone();
    stop["max_scene_steps"] = json!(0);
    assert!(decode::<StopCondition>(&stop).is_err());
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/scheduler_parity.rs
// Claim: urn:core:crates_rs:tests:scheduler-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
