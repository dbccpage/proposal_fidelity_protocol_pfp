use core_adversary::stage::exact::{rational, Rational};
use serde_json::Value;

#[test]
fn independent_python_fraction_values_and_bounded_exact_wire(
) -> Result<(), Box<dyn std::error::Error>> {
    let rows: Vec<Value> = serde_json::from_str(include_str!("fixtures/python_exact_v1.json"))?;
    assert_eq!(rows.len(), 18);
    for row in rows {
        let actual = rational(row["raw"].as_str().ok_or("raw required")?);
        assert_eq!(
            serde_json::to_value(actual.as_ref().map(ToString::to_string))?,
            row["expected"]
        );
        if let Some(value) = actual {
            let encoded = serde_json::to_vec(&Rational(value))?;
            let decoded: Rational = serde_json::from_slice(&encoded)?;
            assert_eq!(serde_json::to_vec(&decoded)?, encoded);
        }
    }
    assert!(rational("1e10001").is_none());
    assert!(rational("1e-10001").is_none());
    assert!(serde_json::from_str::<Rational>("1.5").is_err());
    assert!(serde_json::from_str::<Rational>("\"bogus\"").is_err());
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/exact_parity.rs
// Claim: urn:core:crates_rs:tests:exact-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
