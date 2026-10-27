use core_epistemic_immune_system::independence::{
    assert_signals_independent, signal1_digest, CharacterSpan, DangerEvidence, DetectorContext,
    MatchEvidence,
};
use serde_json::{json, Value};

fn decode_optional_danger(
    index: usize,
    danger_json: &Value,
) -> Result<Option<DangerEvidence>, Box<dyn std::error::Error>> {
    if danger_json.is_null() {
        return Ok(None);
    }
    let danger = DangerEvidence::from_json(danger_json)
        .map_err(|error| format!("danger projection vector {index}: {error}"))?;
    assert_eq!(danger, DangerEvidence::from_bytes(&serde_json::to_vec(danger_json)?)?);
    Ok(Some(danger))
}

fn decode_and_verify_evidence(
    index: usize,
    input: &Value,
) -> Result<(Vec<MatchEvidence>, Option<DangerEvidence>), Box<dyn std::error::Error>> {
    let raw_matches = input["matches"].as_array().ok_or("matches")?;
    let matches = raw_matches
        .iter()
        .map(MatchEvidence::from_json)
        .collect::<Result<Vec<_>, _>>()?;
    let danger = decode_optional_danger(index, &input["danger"])?;
    for (evidence, value) in matches.iter().zip(raw_matches) {
        assert_eq!(*evidence, MatchEvidence::from_bytes(&serde_json::to_vec(value)?)?);
    }
    assert_eq!(json!(matches), input["matches"], "match projection {index}");
    assert_eq!(json!(danger), input["danger"], "danger projection {index}");
    Ok((matches, danger))
}

fn evaluate_independence_vector(
    index: usize,
    input: &Value,
) -> Result<Value, Box<dyn std::error::Error>> {
    let (matches, danger) = decode_and_verify_evidence(index, input)?;
    let context: DetectorContext = serde_json::from_value(
        json!({"detector_id":input["detector_id"],"detector_predicates":input["detector_predicates"],"offsets_are_content":input["offsets_are_content"]}),
    )?;
    Ok(match assert_signals_independent(&matches, danger.as_ref(), &context) {
        Ok(basis) => json!({"ok":basis}),
        Err(error) => json!({"error":error}),
    })
}

#[test]
fn frozen_python_independence_precedence_and_exact_match_digests(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_independence_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors")?;
    assert_eq!(rows.len(), 55);
    for (index, row) in rows.iter().enumerate() {
        let actual = evaluate_independence_vector(index, &row["input"])?;
        assert_eq!(actual, row["expected"], "independence vector {index}");
    }
    let rows = fixture["digests"].as_array().ok_or("digests")?;
    assert_eq!(rows.len(), 7);
    for row in rows {
        let matches = row["input"]
            .as_array()
            .ok_or("matches")?
            .iter()
            .map(MatchEvidence::from_json)
            .collect::<Result<Vec<_>, _>>()?;
        assert_eq!(signal1_digest(&matches), row["expected"]);
    }
    Ok(())
}

#[test]
fn evidence_projection_rejects_negative_float_boolean_and_empty_spans() {
    for offset in [json!(-1), json!(1.5), json!(true), json!("2")] {
        let forged = json!({"epitope_name":"fixture","pattern_matched":"proposal","offset":offset});
        assert!(serde_json::from_value::<MatchEvidence>(forged.clone()).is_err());
        assert_eq!(
            MatchEvidence::from_json(&forged)
                .expect_err("typed wire guard")
                .code,
            "EIS_WIRE_INVALID"
        );
    }
    for span in [
        json!([0, 0]),
        json!([-1, 2]),
        json!([1, 0]),
        json!([0, 1.5]),
        json!([true, 2]),
        json!([0]),
        json!([0, 1, 2]),
    ] {
        assert!(serde_json::from_value::<CharacterSpan>(span).is_err());
    }
    let forged = json!({"danger_type":"REPLAY_FAILURE","observer_id":"host.check","evidence_digest":"evidence","defect_count":-1,"evidence_spans":[]});
    assert!(serde_json::from_value::<DangerEvidence>(forged.clone()).is_err());
    assert_eq!(
        DangerEvidence::from_json(&forged)
            .expect_err("typed wire guard")
            .code,
        "EIS_WIRE_INVALID"
    );
    for raw in [
        r#"{"epitope_name":"fixture","pattern_matched":"proposal","offset":{"$serde_json::private::Number":"2"}}"#,
        r#"{"epitope_name":"fixture","pattern_matched":"proposal","offset":2,"offset":3}"#,
    ] {
        assert_eq!(
            MatchEvidence::from_bytes(raw.as_bytes())
                .expect_err("primitive token required")
                .code,
            "EIS_WIRE_INVALID"
        );
    }
    let forged_number = r#"{"danger_type":"REPLAY_FAILURE","observer_id":"host.check","evidence_digest":"evidence","defect_count":{"$serde_json::private::Number":"1"},"evidence_spans":[]}"#;
    assert_eq!(
        DangerEvidence::from_bytes(forged_number.as_bytes())
            .expect_err("primitive token required")
            .code,
        "EIS_WIRE_INVALID"
    );
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/independence_parity.rs
// Claim: urn:core:crates_rs:tests:independence-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
