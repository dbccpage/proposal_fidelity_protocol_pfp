use super::python_integer;
use serde_json::{json, Value};

#[test]
fn frozen_python_decimal_integer_grammar_unicode_digits_and_digit_limit(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("../fixtures/python_carrier_v1.json"))?;
    let rows = fixture["integer_parsing"]
        .as_array()
        .ok_or("integer rows")?;
    assert_eq!(rows.len(), 220);
    for (index, row) in rows.iter().enumerate() {
        let actual =
            python_integer(row["text"].as_str().ok_or("text")?).map(|value| value.to_string());
        assert_eq!(json!(actual), row["decimal"], "integer case {index}");
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/support/carrier_integer_cases.rs
// Claim: urn:core:crates_rs:tests:carrier-integer-cases:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
