use core_operads::{
    planar::OperadOperation,
    workflow::{unknown_operations, validate_workflow},
};
use serde_json::{json, Value};
use std::collections::BTreeMap;

#[test]
fn frozen_python_workflow_findings_and_repeated_steps() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_workflow_v1.json"))?;
    let garden = fixture["garden"]
        .as_object()
        .ok_or("garden required")?
        .iter()
        .map(|(name, operation)| {
            OperadOperation::from_json(operation).map(|operation| (name.clone(), operation))
        })
        .collect::<Result<BTreeMap<_, _>, _>>()?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 39);
    for (index, row) in rows.iter().enumerate() {
        let actual = match validate_workflow(&row["input"], &garden) {
            Ok(report) => {
                assert_eq!(
                    json!(unknown_operations(std::slice::from_ref(&report))),
                    row["unknown_operations"],
                    "unknown names vector {index}"
                );
                let mut value = serde_json::to_value(&report)?;
                value["is_valid"] = json!(report.is_valid());
                value["signature_matches"] = json!(report.signature_matches());
                json!({"ok":value})
            }
            Err(error) => json!({"error":error}),
        };
        assert_eq!(actual, row["expected"], "workflow vector {index}");
    }
    Ok(())
}

#[test]
fn workflow_ingress_turns_untyped_python_failures_into_refusals() {
    // Python's tuple(None) and step.get on scalars raise untyped exceptions.
    // These are native boundary defenses, outside the oracle parity claim.
    let garden = BTreeMap::new();
    let base = json!({"workflow_id":"wf","name":"Workflow","source_colours":["State"],
        "target_colour":"State","pipeline":[false],"authority_effect":"None"});
    let error = validate_workflow(&base, &garden).expect_err("scalar step must refuse");
    assert_eq!(error.code, "BAD_STEP");
    assert_eq!(error.message, "BAD_STEP: pipeline step 0 must be an object");
    let mut bad_sources = base;
    bad_sources["source_colours"] = Value::Null;
    let error = validate_workflow(&bad_sources, &garden).expect_err("null sources must refuse");
    assert_eq!(error.code, "BAD_SIGNATURE");
    assert_eq!(
        error.message,
        "BAD_SIGNATURE: source_colours must be an array or string"
    );
}

// Origin: engine/crates_rs/tests/core_operads/workflow_parity.rs
// Claim: urn:core:crates_rs:tests:workflow-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
