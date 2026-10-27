use core_adversary::stage::packets::{AgentResult, WorkPacket};
use core_adversary::stage::ports::Refusal;
use core_adversary::stage::receipt_replay::{
    build_swarm_run_receipt, parse_swarm_run_receipt, verify_swarm_run_receipt,
};
use core_adversary::stage::run::{CandidateSelectionProposal, ProgressMeasure, SwarmRunReceipt};
use core_adversary::stage::scheduler::DeterministicScheduler;
use serde::{de::DeserializeOwned, Serialize};
use serde_json::{json, Value};

fn decode<T: DeserializeOwned>(value: &Value) -> Result<T, serde_json::Error> {
    serde_json::from_slice(&serde_json::to_vec(value)?)
}
fn outcome<T: Serialize>(result: Result<T, Refusal>) -> Value {
    match result {
        Ok(receipt) => json!({"ok": receipt}),
        Err(error) => json!({"error": error}),
    }
}

fn eval_receipt_row(
    scheduler: &DeterministicScheduler,
    packet: &WorkPacket,
    row: &Value,
) -> Result<Value, Box<dyn std::error::Error>> {
    match row["op"].as_str().unwrap() {
        "build" => {
            let receipt = build_swarm_run_receipt(
                scheduler,
                "run-one",
                packet,
                decode(&row["results"])?,
                decode(&row["progress_measures"])?,
                decode(&row["selection"])?,
            )?;
            Ok(serde_json::to_value(receipt)?)
        }
        "parse" => Ok(outcome(parse_swarm_run_receipt(
            &hex::decode(row["raw_hex"].as_str().unwrap()).unwrap(),
        ))),
        "verify" => {
            let receipt: SwarmRunReceipt = decode(&row["receipt"])?;
            Ok(outcome(verify_swarm_run_receipt(
                &receipt,
                scheduler,
                row["run_key"].as_str().unwrap(),
                packet,
            )))
        }
        op => panic!("unknown op {op}"),
    }
}

#[test]
fn frozen_python_receipt_construction_parsing_and_independent_replay(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_receipt_v1.json")).unwrap();
    let base = &fixture["base"];
    let scheduler = DeterministicScheduler::new(
        decode(&base["definition"]).unwrap(),
        decode(&base["profile"]).unwrap(),
        decode(&base["graph"]).unwrap(),
        decode(&base["plan"]).unwrap(),
        decode(&base["stop"]).unwrap(),
    )
    .unwrap();
    let packet: WorkPacket = decode(&base["packet"]).unwrap();
    let vectors = fixture["vectors"].as_array().unwrap();
    assert_eq!(vectors.len(), 63);
    for (index, row) in vectors.iter().enumerate() {
        if row["op"] == "selection_refused" {
            let error = decode::<CandidateSelectionProposal>(&row["input"]).err().unwrap().to_string();
            let message = error.rsplit_once(" at line ").map_or(error.as_str(), |(m, _)| m);
            assert_eq!(message, row["python_error"].as_str().unwrap(), "selection refusal {index}");
            continue;
        }
        let actual = eval_receipt_row(&scheduler, &packet, row)?;
        assert_eq!(actual, row["expected"], "receipt vector {index}: {}", row["op"]);
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/receipt_parity.rs
// Claim: urn:core:crates_rs:tests:receipt-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
