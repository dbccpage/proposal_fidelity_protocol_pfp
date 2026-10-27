use num_rational::Rational64;
use core_adversary::stage::oscillation::{
    extract_proposal_tokens, proposal_semantic_distance, OscillationDetector,
};
use core_adversary::stage::packets::CandidateProposal;
use serde_json::{json, Value};

fn candidate(value: &Value) -> Result<CandidateProposal, serde_json::Error> {
    serde_json::from_slice(&serde_json::to_vec(value)?)
}

fn run_oscillation_sequence(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let thresh = Rational64::approximate_float(row["threshold"].as_f64().unwrap()).unwrap();
    let mut detector = OscillationDetector::new(thresh, row["turns"].as_i64().unwrap())?;
    for operation in row["operations"].as_array().unwrap() {
        if operation["reset"] == true {
            detector.reset();
        } else {
            let (stalled, dist) = detector.record_and_evaluate(
                operation["scene"].as_str().unwrap(),
                &candidate(&operation["candidate"])?,
                operation["progressed"].as_bool().unwrap(),
            )?;
            let expected_stalled = operation["result"][0].as_bool().unwrap();
            let expected_dist_f64 = operation["result"][1].as_f64().unwrap();
            assert_eq!(stalled, expected_stalled, "stalled vector {index}");
            let dist_f64 = *dist.numer() as f64 / *dist.denom() as f64;
            assert!((dist_f64 - expected_dist_f64).abs() < 1e-9, "distance vector {index}");
        }
    }
    Ok(())
}

fn verify_oscillation_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    match row["op"].as_str().unwrap() {
        "tokens" => assert_eq!(
            json!(extract_proposal_tokens(&candidate(&row["candidate"])?)),
            row["expected"],
            "token vector {index}"
        ),
        "distance" => {
            let dist = proposal_semantic_distance(&candidate(&row["first"])?, &candidate(&row["second"])?);
            let expected_f64 = row["expected"].as_f64().unwrap();
            let actual_f64 = *dist.numer() as f64 / *dist.denom() as f64;
            assert!(
                (actual_f64 - expected_f64).abs() < 1e-9,
                "distance vector {index}: rational {dist} != expected {expected_f64}"
            );
        }
        "new_refused_nonfinite" => {
            let error = OscillationDetector::new(Rational64::new(-1, 1), 2).err().unwrap();
            assert_eq!(error.code, "OSCILLATION_CONFIGURATION_REFUSED", "nonfinite configuration vector {index}");
        }
        "new_refused" => {
            let thresh = Rational64::approximate_float(row["threshold"].as_f64().unwrap())
                .unwrap_or(Rational64::new(999, 1));
            let error = OscillationDetector::new(thresh, row["turns"].as_i64().unwrap()).err().unwrap();
            assert_eq!(json!(error.message), row["expected"], "configuration vector {index}");
        }
        "sequence" => run_oscillation_sequence(index, row)?,
        op => panic!("unknown op {op}"),
    }
    Ok(())
}

#[test]
fn frozen_python_tokens_distances_and_scene_breaker_state() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_oscillation_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 55);
    for (index, row) in rows.iter().enumerate() {
        verify_oscillation_row(index, row)?;
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/oscillation_parity.rs
// Claim: urn:core:crates_rs:tests:oscillation-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
