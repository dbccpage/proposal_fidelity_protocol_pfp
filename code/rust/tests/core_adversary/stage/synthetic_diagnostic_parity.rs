use core_adversary::stage::diagnostics::SbeDiagnosticPort;
use core_adversary::stage::synthetic_diagnostic::{compute_sbe_metrics, NativeSbeDiagnostic};
use serde_json::Value;

#[test]
fn frozen_numpy_concrete_synthetic_reports_and_dimension_refusals(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_sbe_v1.json"))?;
    let rows = fixture["reports"].as_array().ok_or("reports")?;
    assert_eq!(rows.len(), 122);
    for (index, row) in rows.iter().enumerate() {
        let text = row["text"].as_str().ok_or("text")?;
        let report = compute_sbe_metrics(text, &row["dim"])?;
        assert_eq!(report.to_dict(), row["expected"], "SBE report {index}");
        if row["dim"] == 28 {
            assert_eq!(
                NativeSbeDiagnostic.compute(text, 28)?.to_dict(),
                row["expected"],
                "SBE port {index}"
            );
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/synthetic_diagnostic_parity.rs
// Claim: urn:core:crates_rs:tests:synthetic-diagnostic-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
