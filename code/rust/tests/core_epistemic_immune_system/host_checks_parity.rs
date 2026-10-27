use core_epistemic_immune_system::host_checks::{
    persona_authority_leak_loci, protected_field_loci, protected_field_spans,
};
use serde_json::{json, Value};

fn evaluate_host_check_row(row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    let raw = row["raw"].as_str().ok_or("raw input")?;
    let roles: Vec<String> = serde_json::from_value(row["roles"].clone())?;
    let path = row["path"].as_str().ok_or("path")?;
    Ok(json!({
        "protected_loci": protected_field_loci(raw, path)?,
        "persona_loci": persona_authority_leak_loci(raw, &roles)?,
        "protected_spans": protected_field_spans(raw)?
    }))
}

#[test]
fn frozen_python_ordered_loci_and_character_spans() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_host_checks_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 46);
    for (index, row) in rows.iter().enumerate() {
        assert_eq!(evaluate_host_check_row(row)?, row["expected"], "host-check vector {index}");
    }
    let spans = fixture["spans_only"].as_array().ok_or("spans required")?;
    assert_eq!(spans.len(), 13);
    for (index, row) in spans.iter().enumerate() {
        assert_eq!(
            json!(protected_field_spans(row["raw"].as_str().ok_or("text")?)?),
            row["expected"],
            "lexical vector {index}"
        );
    }
    Ok(())
}

#[test]
fn raw_host_check_ingress_refuses_ambiguous_or_unbounded_payloads() {
    // This stricter JSON boundary is separate from Python parsed-value parity.
    for raw in [
        "",
        "{",
        "[",
        "{\"phi\":NaN}",
        "{\"phi\":Infinity}",
        "{\"phi\":1,\"phi\":2}",
        "{\"nested\":{\"phi\":0,\"phi\":1}}",
        "{\"nested\":[{\"phi\":0,\"phi\":1}]}",
        "{\"string\":\"\\ud800\"}",
        "\u{feff}{}",
    ] {
        assert_eq!(
            protected_field_loci(raw, "")
                .expect_err("strict ingress")
                .code,
            "MALFORMED_PAYLOAD"
        );
        assert_eq!(
            persona_authority_leak_loci(raw, &[])
                .expect_err("strict ingress")
                .code,
            "MALFORMED_PAYLOAD"
        );
    }
    let large = " ".repeat(4 * 1024 * 1024 + 1);
    assert_eq!(
        protected_field_loci(&large, "")
            .expect_err("bounded ingress")
            .code,
        "MALFORMED_PAYLOAD"
    );
    assert_eq!(
        persona_authority_leak_loci(&large, &[])
            .expect_err("bounded ingress")
            .code,
        "MALFORMED_PAYLOAD"
    );
    assert_eq!(
        protected_field_spans(&large)
            .expect_err("bounded scan")
            .code,
        "MALFORMED_PAYLOAD"
    );
    let deep = format!("{}null{}", "[".repeat(129), "]".repeat(129));
    assert_eq!(
        protected_field_loci(&deep, "")
            .expect_err("bounded recursion")
            .code,
        "MALFORMED_PAYLOAD"
    );
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/host_checks_parity.rs
// Claim: urn:core:crates_rs:tests:host-checks-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
