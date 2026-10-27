use core_epistemic_immune_system::{
    activation::{
        evaluate_activation, DangerSignalInput, DangerSignalReceiptV1, DetectorHitInput,
        DetectorHitRefV1, GuardActivationInput, GuardActivationReceiptV1,
    },
    AntiSkillSpecV2, AntiSkillStatus, FailureClass, Refusal, ThymusGate, ThymusVerdict,
};
use serde::Serialize;
use serde_json::{json, Value};

fn outcome<T: Serialize>(value: Result<T, Refusal>) -> Value {
    match value {
        Ok(record) => json!({"ok":record}),
        Err(error) => json!({"error":error}),
    }
}
fn fixture() -> Result<Value, serde_json::Error> {
    serde_json::from_str(include_str!("fixtures/python_activation_v1.json"))
}

fn evaluate_hit_row(input: Value, expected: &Value) -> Result<(Value, bool), Box<dyn std::error::Error>> {
    let value = DetectorHitRefV1::new(serde_json::from_value::<DetectorHitInput>(input.clone())?);
    if let Ok(hit) = &value {
        assert_eq!(hit.hit_id(), expected["ok"]["hit_id"]);
        assert_eq!(hit.spec_id(), expected["ok"]["spec_id"]);
        assert_eq!(hit.failure_code(), expected["ok"]["failure_code"]);
        assert_eq!(hit.subject_id(), expected["ok"]["subject_id"]);
    }
    Ok((outcome(value), serde_json::from_value::<DetectorHitRefV1>(input).is_ok()))
}

fn evaluate_danger_row(input: Value, expected: &Value) -> Result<(Value, bool), Box<dyn std::error::Error>> {
    let value = DangerSignalReceiptV1::new(serde_json::from_value::<DangerSignalInput>(input.clone())?);
    if let Ok(danger) = &value {
        assert_eq!(danger.receipt_id(), expected["ok"]["receipt_id"]);
        assert_eq!(danger.observer_id(), expected["ok"]["observer_id"]);
        assert_eq!(danger.subject_id(), expected["ok"]["subject_id"]);
        assert_eq!(danger.evidence_digest(), expected["ok"]["evidence_digest"]);
    }
    Ok((outcome(value), serde_json::from_value::<DangerSignalReceiptV1>(input).is_ok()))
}

fn evaluate_activation_row(input: Value, expected: &Value) -> Result<(Value, bool), Box<dyn std::error::Error>> {
    let value = GuardActivationReceiptV1::new(serde_json::from_value::<GuardActivationInput>(input.clone())?);
    if let Ok(activation) = &value {
        assert_eq!(activation.receipt_id(), expected["ok"]["receipt_id"]);
        assert_eq!(activation.disposition(), expected["ok"]["disposition"]);
        assert_eq!(activation.independence_basis(), expected["ok"]["independence_basis"]);
    }
    Ok((outcome(value), serde_json::from_value::<GuardActivationReceiptV1>(input).is_ok()))
}

fn evaluate_record_row(row: &Value) -> Result<(Value, bool), Box<dyn std::error::Error>> {
    let input = row["input"].clone();
    match row["kind"].as_str().ok_or("record kind")? {
        "hit" => evaluate_hit_row(input, &row["expected"]),
        "danger" => evaluate_danger_row(input, &row["expected"]),
        "activation" => evaluate_activation_row(input, &row["expected"]),
        kind => Err(format!("unknown record kind {kind}").into()),
    }
}

#[test]
fn frozen_python_receipt_constructors_and_checked_decode() -> Result<(), Box<dyn std::error::Error>>
{
    let fixture = fixture()?;
    let rows = fixture["records"].as_array().ok_or("records required")?;
    assert_eq!(rows.len(), 52);
    for (index, row) in rows.iter().enumerate() {
        let (actual, admitted) = evaluate_record_row(row)?;
        assert_eq!(actual, row["expected"], "record vector {index}");
        assert_eq!(admitted, row["expected"].get("ok").is_some(), "decode vector {index}");
    }
    Ok(())
}

#[test]
fn frozen_python_activation_refusal_precedence_and_receipts(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture = fixture()?;
    let rows = fixture["activations"]
        .as_array()
        .ok_or("activations required")?;
    assert_eq!(rows.len(), 19);
    for (index, row) in rows.iter().enumerate() {
        let input = &row["input"];
        let hit: Option<DetectorHitRefV1> = serde_json::from_value(input["hit"].clone())?;
        let danger: Option<DangerSignalReceiptV1> =
            serde_json::from_value(input["danger"].clone())?;
        let actual = evaluate_activation(
            input["profile_digest"].as_str().ok_or("profile required")?,
            hit.as_ref(),
            danger.as_ref(),
            input["externally_admitted"]
                .as_bool()
                .ok_or("admission required")?,
            input["suspended"].as_bool().ok_or("suspension required")?,
            input["disposition"]
                .as_str()
                .ok_or("disposition required")?,
        );
        assert_eq!(
            outcome(actual),
            row["expected"],
            "activation vector {index}"
        );
    }
    Ok(())
}

#[test]
fn legacy_thymus_overlap_is_limited_to_candidate_tolerance(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture = fixture()?;
    let rows = fixture["legacy_thymus_overlap"]
        .as_array()
        .ok_or("overlap required")?;
    assert_eq!(rows.len(), 6);
    for row in rows {
        let gate = ThymusGate::new(serde_json::from_value(row["panel"].clone())?);
        let mut spec = AntiSkillSpecV2::propose(
            row["pattern"].as_str().ok_or("pattern")?,
            FailureClass::CounterfeitExactness,
            "fixture",
            "Fixture projection",
            0,
        );
        let verdict = gate.screen(&mut spec);
        let tolerant = matches!(verdict, ThymusVerdict::Survived { .. });
        assert_eq!(
            json!({"self_tolerant":tolerant,"is_admitted":spec.status == AntiSkillStatus::Admitted}),
            row["expected"]
        );
        assert_eq!(spec.authority_effect, "None");
    }
    Ok(())
}

#[test]
fn receipt_decode_rejects_unknown_fields_without_mutating_checked_values(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture = fixture()?;
    for row in fixture["records"]
        .as_array()
        .ok_or("records")?
        .iter()
        .filter(|row| row["expected"].get("ok").is_some())
    {
        let mut forged = row["expected"]["ok"].clone();
        forged["externally_admitted"] = json!(true);
        let admitted = match row["kind"].as_str().ok_or("kind")? {
            "hit" => serde_json::from_value::<DetectorHitRefV1>(forged).is_ok(),
            "danger" => serde_json::from_value::<DangerSignalReceiptV1>(forged).is_ok(),
            "activation" => serde_json::from_value::<GuardActivationReceiptV1>(forged).is_ok(),
            _ => return Err("unknown kind".into()),
        };
        assert!(!admitted);
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/activation_parity.rs
// Claim: urn:core:crates_rs:tests:activation-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
