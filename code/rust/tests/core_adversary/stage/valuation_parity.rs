use core_adversary::stage::evaluation::{EvaluatorEpoch, ValuationReceipt};
use core_adversary::stage::packets::CandidateProposal;
use serde::{de::DeserializeOwned, Serialize};
use serde_json::Value;

fn replay<T: DeserializeOwned + Serialize>(value: &Value) -> Result<Value, serde_json::Error> {
    let decoded: T = serde_json::from_slice(&serde_json::to_vec(value)?)?;
    serde_json::to_value(decoded)
}

fn verify_valuation_row(index: usize, row: &Value) {
    let actual = match row["record"].as_str().unwrap() {
        "candidate" => replay::<CandidateProposal>(&row["input"]),
        "epoch" => replay::<EvaluatorEpoch>(&row["input"]),
        "valuation" => replay::<ValuationReceipt>(&row["input"]),
        record => panic!("unknown record {record}"),
    };
    if let Some(expected) = row.get("expected") {
        assert_eq!(actual.unwrap(), *expected, "valuation record {index}");
    } else {
        let error = actual.err().unwrap().to_string();
        let message = error.rsplit_once(" at line ").map_or(error.as_str(), |(m, _)| m);
        assert_eq!(message, row["python_error"].as_str().unwrap(), "valuation refusal {index}");
    }
}

#[test]
fn frozen_python_evaluator_candidate_and_weighted_valuation_records(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_valuation_v1.json"))?;
    let vectors = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(vectors.len(), 37);
    for (index, row) in vectors.iter().enumerate() {
        verify_valuation_row(index, row);
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/valuation_parity.rs
// Claim: urn:core:crates_rs:tests:valuation-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
