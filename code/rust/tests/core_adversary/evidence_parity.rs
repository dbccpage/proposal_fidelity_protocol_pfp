use core_adversary::evidence::{
    canonical_rational, parse_exact_rational, CandidateCheck, ObstructionMeasurement,
};
use serde_json::{json, Value};

fn eval_measurement_row(row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    match ObstructionMeasurement::from_json(&row["input"]) {
        Ok(value) => {
            assert_eq!(value, ObstructionMeasurement::from_bytes(&serde_json::to_vec(&row["input"])?)?);
            assert_eq!(value.backend(), row["input"]["backend"].as_str().unwrap());
            assert_eq!(value.dual_witness().len(), row["input"]["dual_witness"].as_array().unwrap().len());
            assert_eq!(json!(value.certificate_verified()), row["input"]["certificate_verified"]);
            assert_eq!(json!(value.phi1().map(canonical_rational)), row["input"]["phi1"]);
            let mut keys = std::collections::HashSet::new();
            assert!(keys.insert(value.clone()));
            assert!(!keys.insert(value.clone()));
            if row["input"]["status"] == "NOT_MEASURED" && row["input"]["defect_count"] == 0 {
                assert_eq!(
                    value,
                    ObstructionMeasurement::not_measured(
                        row["input"]["reason"].as_str().unwrap().into(),
                        value.backend().into()
                    )?
                );
            }
            Ok(json!({"ok":value.to_dict()?,"is_measured":value.is_measured(),
                "is_exact_joint_zero":value.is_exact_joint_zero(),"has_open_obstruction":value.has_open_obstruction()}))
        }
        Err(error) => Ok(json!({"error":error})),
    }
}

fn eval_candidate_check_row(row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    match CandidateCheck::from_json(&row["input"]) {
        Ok(value) => {
            assert_eq!(value, CandidateCheck::from_bytes(&serde_json::to_vec(&row["input"])?)?);
            assert_eq!(value.candidate_id(), row["input"]["candidate_id"].as_str().unwrap());
            assert_eq!(json!(value.verdict()), row["input"]["verdict"]);
            assert_eq!(hex::encode(value.receipt_bytes()), row["input"]["checker_receipt_hex"].as_str().unwrap());
            assert_eq!(json!(value.receipt_sha256()), row["input"]["checker_receipt_sha256"]);
            assert_eq!(json!(value.candidate_content_sha256()), row["input"]["candidate_content_sha256"]);
            assert_eq!(json!(value.checker_id()), row["input"]["checker_id"]);
            let bindings: Vec<bool> = row["bindings"]
                .as_array()
                .unwrap()
                .iter()
                .map(|binding| {
                    let refs: Vec<String> = serde_json::from_value(binding["artifact_refs"].clone()).unwrap();
                    value.binds(binding["candidate_id"].as_str().unwrap(), &refs)
                })
                .collect();
            Ok(json!({"ok":value.to_dict(),"can_authorize":value.can_authorize(),"bindings":bindings}))
        }
        Err(error) => Ok(json!({"error":error})),
    }
}

#[test]
fn frozen_python_exact_measurements_bound_receipts_and_rational_admission(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_evidence_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 57);
    for (index, row) in rows.iter().enumerate() {
        let actual = match row["op"].as_str().unwrap() {
            "measurement" => eval_measurement_row(row)?,
            "candidate_check" => eval_candidate_check_row(row)?,
            "rational" => match parse_exact_rational(&row["input"]) {
                Ok(value) => json!({"ok":canonical_rational(&value)}),
                Err(error) => json!({"error":error}),
            },
            op => panic!("unknown op {op}"),
        };
        assert_eq!(actual, row["expected"], "evidence vector {index}: {}", row["op"]);
    }
    Ok(())
}

#[test]
fn evidence_ingress_refuses_forged_number_shapes_duplicate_fields_and_bad_hex() {
    for count in ["true", "1.0", r#"{"$serde_json::private::Number":"0"}"#] {
        let raw = format!(
            r#"{{"status":"NOT_MEASURED","backend":"null.host","reason":"no scorer","defect_count":{count}}}"#
        );
        assert_eq!(
            ObstructionMeasurement::from_bytes(raw.as_bytes())
                .expect_err("primitive exact count")
                .code,
            "ADVERSARY_EVIDENCE_TYPE_ERROR"
        );
    }
    for raw in [
        r#"{"status":"NOT_MEASURED","backend":"null.host","backend":"changed","reason":"no scorer"}"#,
        r#"{"status":"NOT_MEASURED","backend":"null.host","reason":"no scorer","checked":true}"#,
        r#"{"status":"NOT_MEASURED","backend":"null.host","reason":"no scorer","certificate_verified":1}"#,
    ] {
        assert_eq!(
            ObstructionMeasurement::from_bytes(raw.as_bytes())
                .expect_err("checked schema")
                .code,
            "ADVERSARY_EVIDENCE_WIRE_INVALID"
        );
    }
    let wire = json!({"verdict":"ACCEPTED","candidate_id":"candidate","candidate_content_sha256":"sha256:".to_owned()+&"0".repeat(64),
        "checker_id":"host","checker_receipt_hex":"zz"});
    assert_eq!(
        CandidateCheck::from_json(&wire)
            .expect_err("receipt bytes required")
            .code,
        "ADVERSARY_EVIDENCE_WIRE_INVALID"
    );
}

// Origin: engine/crates_rs/tests/core_adversary/evidence_parity.rs
// Claim: urn:core:crates_rs:tests:evidence-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
