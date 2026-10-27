use super::NumpyPcg64;
use serde_json::Value;

fn verify_numpy_stream_row(row: &Value) {
    let seed = u32::try_from(row["seed"].as_u64().unwrap()).unwrap();
    let mut rng = NumpyPcg64::new(seed);
    assert_eq!(rng.state.to_string(), row["state"].as_str().unwrap());
    assert_eq!(rng.inc.to_string(), row["inc"].as_str().unwrap());
    for (index, value) in row["raw"].as_array().unwrap().iter().enumerate() {
        assert_eq!(rng.next_u64().to_string(), value.as_str().unwrap(), "seed {seed}, raw {index}");
    }
    let mut rng = NumpyPcg64::new(seed);
    for (index, value) in row["normal_bits"].as_array().unwrap().iter().enumerate() {
        let expected = u64::from_str_radix(value.as_str().unwrap(), 16).unwrap();
        assert_eq!(rng.standard_normal().unwrap().to_bits(), expected, "seed {seed}, normal {index}");
    }
}

#[test]
fn frozen_numpy_pcg64_seed_state_raw_and_normal_double_bits(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("../fixtures/python_sbe_v1.json"))?;
    let rows = fixture["streams"].as_array().ok_or("streams")?;
    assert_eq!(rows.len(), 17);
    for row in rows {
        verify_numpy_stream_row(row);
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/support/numpy_stream_cases.rs
// Claim: urn:core:crates_rs:tests:numpy-stream-cases:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
