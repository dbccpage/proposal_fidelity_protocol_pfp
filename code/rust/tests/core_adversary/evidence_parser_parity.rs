use core_adversary::evidence_parse::{
    parse_checker_receipt, parse_structured_critique, CritiqueStatus, StructuredCritique,
};
use serde_json::{json, Value};

fn eval_checker_receipt_row(row: &Value) -> Value {
    let raw = hex::decode(row["raw_hex"].as_str().unwrap()).unwrap();
    match parse_checker_receipt(&raw) {
        Ok(record) => {
            assert_eq!(json!(record.verdict()), row["expected"]["ok"]["verdict"]);
            assert_eq!(
                json!(record.candidate_content_sha256()),
                row["expected"]["ok"]["candidate_content_sha256"]
            );
            assert_eq!(json!(record.checker_id()), row["expected"]["ok"]["checker_id"]);
            assert_eq!(json!(record.candidate_id()), row["expected"]["ok"]["candidate_id"]);
            json!({"ok":record.to_dict()})
        }
        Err(error) => json!({"error":error}),
    }
}

fn eval_critique_row(row: &Value) -> Value {
    match parse_structured_critique(&row["input"]) {
        Ok(record) => {
            assert_eq!(json!(record.blocking()), row["expected"]["ok"]["blocking"]);
            assert_eq!(json!(record.status()), row["expected"]["ok"]["status"]);
            assert_eq!(json!(record.challenge_kind()), row["expected"]["ok"]["challenge_kind"]);
            assert_eq!(json!(record.counterexample()), row["expected"]["ok"]["counterexample"]);
            json!({"ok":record.to_dict()})
        }
        Err(error) => json!({"error":error}),
    }
}

#[test]
fn frozen_python_checker_receipt_and_structured_critique_semantics(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_evidence_parsers_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 93);
    for (index, row) in rows.iter().enumerate() {
        let actual = match row["op"].as_str().unwrap() {
            "checker_receipt" => eval_checker_receipt_row(row),
            "critique" => eval_critique_row(row),
            op => panic!("unknown op {op}"),
        };
        assert_eq!(actual, row["expected"], "parser vector {index}: {}", row["op"]);
    }
    Ok(())
}

#[test]
fn malformed_critique_cannot_be_constructed_as_nonblocking() {
    let error = StructuredCritique::new(
        CritiqueStatus::Malformed,
        false,
        String::new(),
        "LOGIC".into(),
        "bad reply".into(),
    )
    .expect_err("fail closed");
    assert_eq!(error.code, "ADVERSARY_EVIDENCE_VALUE_ERROR");
    assert!(StructuredCritique::new(
        CritiqueStatus::Structured,
        false,
        String::new(),
        "UNKNOWN".into(),
        String::new()
    )
    .is_err());
    let finding = parse_structured_critique(&json!("```critique\n{bad JSON}\n```"))
        .expect("malformed finding");
    assert!(finding.blocking());
    assert_eq!(finding.status(), CritiqueStatus::Malformed);
    assert!(parse_checker_receipt(b"\xff").is_err());
}

// Origin: engine/crates_rs/tests/core_adversary/evidence_parser_parity.rs
// Claim: urn:core:crates_rs:tests:evidence-parser-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
