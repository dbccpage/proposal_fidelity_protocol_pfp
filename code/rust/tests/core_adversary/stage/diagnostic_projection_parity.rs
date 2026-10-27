use num_traits::Signed;
use core_adversary::stage::diagnostics::SbeReport;
use serde_json::{json, Value};

#[test]
fn frozen_python_act4_synthetic_point_projection() -> Result<(), Box<dyn std::error::Error>> {
    // Projection of the Act IV source corpus frozen before this implementation.
    let fixture: Value = serde_json::from_str(include_str!(
        "fixtures/python_sbe_points_projection_v1.json"
    ))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors")?;
    assert_eq!(rows.len(), 84);
    for (index, row) in rows.iter().enumerate() {
        let first = SbeReport::from_json(&row["reports"][0])?;
        let second = SbeReport::from_json(&row["reports"][1])?;
        assert_eq!(first.to_dict(), row["reports"][0]);
        assert_eq!(second.to_dict(), row["reports"][1]);
        let delta = first.point().zip(second.point()).map(|(first, second)| {
            ((first.0 - second.0).abs() + (first.1 - second.1).abs()).to_string()
        });
        assert_eq!(json!(delta), row["delta"], "diagnostic projection {index}");
    }
    Ok(())
}

#[test]
fn native_report_boundary_rejects_nonobjects() {
    // Native wire acceptance; this malformed report is outside source-produced maps.
    for value in [Value::Null, json!([]), json!("report"), json!(1)] {
        let Err(error) = SbeReport::from_json(&value) else {
            panic!("malformed report accepted")
        };
        assert_eq!(error.code, "SBE_REPORT_INVALID");
    }
}

// Origin: engine/crates_rs/tests/core_adversary/stage/diagnostic_projection_parity.rs
// Claim: urn:core:crates_rs:tests:diagnostic-projection-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
