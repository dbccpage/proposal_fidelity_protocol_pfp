use core_operads::{
    planar::{
        admissible_substitutions, associativity_witness, is_admissible, substitute,
        OperadOperation, OPERAD_COLOURS,
    },
    Refusal,
};
use serde::Serialize;
use serde_json::{json, Value};

fn outcome<T: Serialize>(value: Result<T, Refusal>) -> Value {
    match value {
        Ok(value) => json!({"ok":value}),
        Err(error) => json!({"error":error}),
    }
}

fn assert_construct_error(row: &Value, error: &impl std::fmt::Display) -> Result<(), Box<dyn std::error::Error>> {
    assert_eq!(json!(error.to_string()), row["expected"]["error"]["message"]);
    let decoded = serde_json::from_slice::<OperadOperation>(&serde_json::to_vec(&row["input"])?)
        .err()
        .ok_or("invalid operation decoded")?
        .to_string();
    let message = decoded.rsplit_once(" at line ").map_or(decoded.as_str(), |(message, _)| message);
    assert_eq!(json!(message), row["expected"]["error"]["message"]);
    Ok(())
}

fn check_typed_construct_boundary(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    if let (Some(name), Some(sources), Some(target)) = (
        row["input"]["name"].as_str(),
        row["input"]["source_colours"].as_array(),
        row["input"]["target_colour"].as_str(),
    ) {
        let sources = sources
            .iter()
            .map(|source| source.as_str().map(str::to_owned).ok_or("source required"))
            .collect::<Result<Vec<_>, _>>()?;
        assert_eq!(
            outcome(OperadOperation::new(name.into(), sources, target.into())),
            row["expected"],
            "typed operation boundary {index}"
        );
    }
    Ok(())
}

fn evaluate_construct_row(index: usize, row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    let result = OperadOperation::from_json(&row["input"]);
    if let Err(error) = &result {
        assert_construct_error(row, error)?;
    }
    check_typed_construct_boundary(index, row)?;
    if let Ok(operation) = &result {
        assert_eq!(json!(operation.arity()), row["arity"]);
        assert_eq!(
            json!({"name":operation.name(),"source_colours":operation.source_colours(),"target_colour":operation.target_colour()}),
            row["input"]
        );
        let decoded: OperadOperation = serde_json::from_slice(&serde_json::to_vec(&row["input"])?)?;
        assert_eq!(decoded, *operation);
    }
    Ok(outcome(result))
}

fn evaluate_substitute_or_assoc(op: &str, row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    if op == "substitute" {
        let theta = OperadOperation::from_json(&row["theta"])?;
        let phi = OperadOperation::from_json(&row["phi"])?;
        assert_eq!(json!(is_admissible(&theta, &row["index"], &phi)), row["admissible"]);
        Ok(outcome(substitute(&theta, &row["index"], &phi)))
    } else {
        Ok(outcome(associativity_witness(
            &OperadOperation::from_json(&row["theta"])?,
            &row["i"],
            &OperadOperation::from_json(&row["phi"])?,
            &row["j"],
            &OperadOperation::from_json(&row["psi"])?,
        )))
    }
}

fn dispatch_planar_op(index: usize, row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    match row["op"].as_str().ok_or("op required")? {
        "vocabulary" => Ok(json!(OPERAD_COLOURS)),
        "construct" => evaluate_construct_row(index, row),
        "substitute" | "associativity" => {
            evaluate_substitute_or_assoc(row["op"].as_str().unwrap_or(""), row)
        }
        "admissible_substitutions" => {
            let operations = row["operations"]
                .as_array()
                .ok_or("operations required")?
                .iter()
                .map(OperadOperation::from_json)
                .collect::<Result<Vec<_>, _>>()?;
            Ok(json!(admissible_substitutions(&operations)))
        }
        op => Err(format!("unknown op {op}").into()),
    }
}

#[test]
fn frozen_python_planar_domain_and_sovereign_kernel_overlap(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_planar_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 251);
    for (index, row) in rows.iter().enumerate() {
        let actual = dispatch_planar_op(index, row)?;
        assert_eq!(actual, row["expected"], "planar vector {index}");
    }
    Ok(())
}

fn assert_forged_fields_refused(original: &Value) -> Result<(), Box<dyn std::error::Error>> {
    for (field, value) in [
        ("arity", json!(99)),
        ("authority_effect", json!("StateTransition")),
    ] {
        let mut forged = original.clone();
        forged[field] = value;
        let refusal = OperadOperation::from_json(&forged)
            .err()
            .ok_or("forged operation admitted")?;
        assert_eq!(refusal.code, "BAD_OPERATION");
        assert!(serde_json::from_slice::<OperadOperation>(&serde_json::to_vec(&forged)?).is_err());
    }
    Ok(())
}

#[test]
fn operation_ingress_rejects_caller_authored_arity_and_authority(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_planar_v1.json"))?;
    let original = fixture["vectors"]
        .as_array()
        .ok_or("vectors required")?
        .iter()
        .find(|row| row["op"] == "construct" && row["expected"].get("ok").is_some())
        .ok_or("valid operation required")?["input"]
        .clone();
    assert_forged_fields_refused(&original)?;
    let mut missing = original;
    missing
        .as_object_mut()
        .ok_or("object required")?
        .remove("target_colour");
    assert!(OperadOperation::from_json(&missing).is_err());
    for wrong in [Value::Null, json!([])] {
        assert_eq!(
            OperadOperation::from_json(&wrong)
                .err()
                .ok_or("wrong operation type admitted")?
                .code,
            "BAD_OPERATION"
        );
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_operads/planar_parity.rs
// Claim: urn:core:crates_rs:tests:planar-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
