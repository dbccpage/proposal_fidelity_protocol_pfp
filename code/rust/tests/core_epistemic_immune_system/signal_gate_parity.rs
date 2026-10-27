use core_epistemic_immune_system::danger_gate::TwoSignalDangerGate;
use core_epistemic_immune_system::independence::{DangerEvidence, DetectorContext, MatchEvidence};
use core_epistemic_immune_system::signal_gate::{CategorizedDangerEvidence, DangerSeverity};
use serde_json::{json, Value};

fn decode_categorized_danger(
    danger_json: &Value,
) -> Result<Option<CategorizedDangerEvidence>, Box<dyn std::error::Error>> {
    if danger_json.is_null() {
        return Ok(None);
    }
    let value = CategorizedDangerEvidence::from_bytes(&serde_json::to_vec(danger_json)?)?;
    assert_eq!(value, CategorizedDangerEvidence::from_json(danger_json)?);
    let evidence = DangerEvidence::from_json(&danger_json["evidence"])?;
    let severity: DangerSeverity = serde_json::from_value(danger_json["severity"].clone())?;
    assert_eq!(value, CategorizedDangerEvidence::new(evidence, severity));
    assert_eq!(json!(value), *danger_json);
    Ok(Some(value))
}

fn evaluate_signal_gate_row(row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    let matches = row["matches"]
        .as_array()
        .ok_or("matches required")?
        .iter()
        .map(MatchEvidence::from_json)
        .collect::<Result<Vec<_>, _>>()?;
    let danger = decode_categorized_danger(&row["danger"])?;
    let context: DetectorContext = serde_json::from_value(row["context"].clone())?;
    let result = if row["independent"] == true {
        TwoSignalDangerGate::evaluate_independent(&matches, danger.as_ref(), &context)
    } else {
        TwoSignalDangerGate::evaluate_signals(&matches, danger.as_ref())
    };
    Ok(match result {
        Ok(value) => {
            assert_eq!(json!(value.decision()), row["expected"]["ok"]["decision"]);
            assert_eq!(json!(value.is_suppressed()), row["expected"]["ok"]["is_suppressed"]);
            json!({"ok": value})
        }
        Err(error) => json!({"error": error}),
    })
}

#[test]
fn frozen_python_severity_disposition_and_independence_precedence(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_signal_gate_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 108);
    for (index, row) in rows.iter().enumerate() {
        let actual = evaluate_signal_gate_row(row)?;
        assert_eq!(actual, row["expected"], "gate vector {index}");
    }
    Ok(())
}

#[test]
fn severity_ingress_refuses_untyped_or_unknown_labels() {
    let evidence = json!({"danger_type":"REPLAY_FAILURE","observer_id":"host.check",
        "evidence_digest":"sha256:evidence","defect_count":1,"evidence_spans":[]});
    for severity in [
        json!("high"),
        json!("UNKNOWN"),
        json!(true),
        Value::Null,
        json!(1),
    ] {
        let wire = json!({"evidence":evidence,"severity":severity});
        assert_eq!(
            CategorizedDangerEvidence::from_json(&wire)
                .expect_err("closed severity")
                .code,
            "EIS_WIRE_INVALID"
        );
    }
    let unknown = json!({"evidence":evidence,"severity":"HIGH","checked":true});
    assert!(CategorizedDangerEvidence::from_json(&unknown).is_err());
    let duplicate = format!(r#"{{"evidence":{evidence},"severity":"HIGH","severity":"LOW"}}"#);
    assert!(CategorizedDangerEvidence::from_bytes(duplicate.as_bytes()).is_err());
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/signal_gate_parity.rs
// Claim: urn:core:crates_rs:tests:signal-gate-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
