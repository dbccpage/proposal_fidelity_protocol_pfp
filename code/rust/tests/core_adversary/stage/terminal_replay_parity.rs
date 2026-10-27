use core_adversary::stage::packets::{AgentResult, WorkPacket};
use core_adversary::stage::ports::Refusal;
use core_adversary::stage::receipt_replay::{parse_swarm_run_receipt, verify_swarm_run_receipt};
use core_adversary::stage::run::{ProgressMeasure, SwarmRunReceipt};
use core_adversary::stage::scheduler::DeterministicScheduler;
use serde::{de::DeserializeOwned, Serialize};
use serde_json::{json, Value};

fn decode<T: DeserializeOwned>(value: &Value) -> Result<T, serde_json::Error> {
    serde_json::from_slice(&serde_json::to_vec(value)?)
}

fn outcome<T: Serialize>(result: Result<T, Refusal>) -> Value {
    match result {
        Ok(value) => json!({"ok": value}),
        Err(error) => json!({"error": error}),
    }
}

fn eval_terminal_replay_row(row: &Value) -> Value {
    if row["op"] == "parse" {
        return outcome(parse_swarm_run_receipt(
            &hex::decode(row["raw_hex"].as_str().unwrap()).unwrap(),
        ));
    }
    let base = &row["base"];
    let scheduler = DeterministicScheduler::new(
        decode(&base["definition"]).unwrap(),
        decode(&base["profile"]).unwrap(),
        decode(&base["graph"]).unwrap(),
        decode(&base["plan"]).unwrap(),
        decode(&base["stop"]).unwrap(),
    )
    .unwrap();
    let packet: WorkPacket = decode(&base["packet"]).unwrap();
    let run_key = row["run_key"].as_str().unwrap();
    match row["op"].as_str().unwrap() {
        "verify" => {
            let receipt: SwarmRunReceipt = decode(&row["receipt"]).unwrap();
            outcome(verify_swarm_run_receipt(&receipt, &scheduler, run_key, &packet))
        }
        "loop" => {
            let answer: AgentResult = decode(&row["answer"]).unwrap();
            let progress: ProgressMeasure = decode(&row["progress"]).unwrap();
            let count = row["count"].as_u64().unwrap() as usize;
            let mut state = scheduler.start(run_key, &packet).unwrap();
            for _ in 0..count {
                state = scheduler.advance(&state, &answer, &progress).unwrap();
            }
            let replay = scheduler.replay(run_key, &packet, &vec![answer; count], &vec![progress; count]).unwrap();
            assert_eq!(state, replay, "independent visit replay {}", row["case"]);
            serde_json::to_value(state).unwrap()
        }
        op => panic!("unexpected op {op}"),
    }
}

#[test]
fn synchronized_terminal_causes_packet_binding_and_visit_ceiling(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_terminal_replay_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 63);
    for row in rows {
        let actual = eval_terminal_replay_row(row);
        assert_eq!(actual, row["expected"], "terminal acceptance {}", row["case"]);
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/terminal_replay_parity.rs
// Claim: urn:core:crates_rs:tests:terminal-replay-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
