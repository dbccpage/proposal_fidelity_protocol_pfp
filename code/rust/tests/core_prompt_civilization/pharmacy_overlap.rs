//! The existing pharmacy agrees with the stated shared projection only.
use core_prompt_civilization::pharmacy::{detect, DetectionContext, FailureClass};
use serde_json::{json, Value};

#[test]
fn frozen_python_shared_pharmacy_projection() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_pharmacy_overlap_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 32);
    for row in rows {
        let context: DetectionContext = serde_json::from_value(row["context"].clone())?;
        let report = detect(&row["candidate"], &context);
        let mut findings = report
            .findings
            .iter()
            .filter(|finding| finding.class != FailureClass::PersonaAuthorityLeak)
            .map(|finding| {
                (
                    finding.class.code(),
                    finding.locus.as_str(),
                    finding.disposition.as_str(),
                )
            })
            .collect::<Vec<_>>();
        findings.sort();
        let findings = findings.into_iter().map(|(code,locus,disposition)|json!({"code":code,"locus":locus,"disposition":disposition})).collect::<Vec<_>>();
        assert_eq!(
            json!({"findings":findings,"subject_digest":report.subject_digest,
            "semantic_payload_digest":report.semantic_payload_digest}),
            row["expected"],
            "projection {}",
            row["id"]
        );
        assert_eq!(report.authority_effect(), "None");
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/pharmacy_overlap.rs
// Claim: urn:core:crates_rs:tests:pharmacy-overlap:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
