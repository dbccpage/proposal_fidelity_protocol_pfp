use core_operads::policy::DangerSignalPolicy;
use serde_json::{json, Value};

#[test]
fn frozen_python_exact_danger_policy() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_danger_policy_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 40);
    for (index, row) in rows.iter().enumerate() {
        let result = DangerSignalPolicy::from_json(&row["input"]);
        let decoded = serde_json::from_value::<DangerSignalPolicy>(row["input"].clone());
        let actual = match result {
            Ok(policy) => {
                assert_eq!(decoded?, policy, "validated decode vector {index}");
                let threshold = policy.allosteric_quorum_threshold();
                assert_eq!(
                    json!({"enforce_danger_gate":policy.enforce_danger_gate(),
                        "quarantine_on_critical":policy.quarantine_on_critical(),
                        "allosteric_quorum_threshold":{"numerator":threshold.numer().to_string(),
                            "denominator":threshold.denom().to_string()}}),
                    row["expected"]["ok"],
                );
                json!({"ok":policy})
            }
            Err(error) => {
                assert!(decoded.is_err(), "invalid policy vector {index}");
                json!({"error":error})
            }
        };
        assert_eq!(actual, row["expected"], "policy vector {index}");
    }
    Ok(())
}

#[test]
fn policy_wire_refuses_forged_fields_and_undefined_fractions() {
    for value in [
        Value::Null,
        json!({"authority_effect":"Granted"}),
        json!({"allosteric_quorum_threshold":{"numerator":"1","denominator":"0"}}),
        json!({"allosteric_quorum_threshold":{"numerator":"bad","denominator":"2"}}),
        json!({"allosteric_quorum_threshold":{"numerator":1,"denominator":"2"}}),
        json!({"allosteric_quorum_threshold":{"numerator":"1","denominator":null}}),
        json!({"allosteric_quorum_threshold":{"numerator":"1","denominator":"bad"}}),
        json!({"allosteric_quorum_threshold":{"numerator":"1","denominator":"2","checked":true}}),
    ] {
        assert!(DangerSignalPolicy::from_json(&value).is_err(), "{value}");
        assert!(serde_json::from_value::<DangerSignalPolicy>(value).is_err());
    }
}

// Origin: engine/crates_rs/tests/core_operads/policy_parity.rs
// Claim: urn:core:crates_rs:tests:policy-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
