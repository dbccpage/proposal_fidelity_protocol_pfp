//! Lifecycle metadata parity only; evidence authenticity and execution authority are separate.
use omega_workflows_agents_skills::estate::execute;
use serde_json::{json, Value};

fn digest(algorithm: &str, content: &str) -> Value {
    json!({"algorithm": algorithm, "hex_digest": content})
}
fn request(schema: Value, executor: Value) -> Value {
    json!({"operation": {
        "operation_id": {"value": "test.lifecycle"},
        "inputs": [],
        "output": {
            "name": "result", "colour_id": {"value": "Code"},
            "schema_ref": {"value": "test.schema"},
            "schema_digest": digest("sha256", &"a".repeat(64)),
            "validator_ref": "test.validator",
            "validator_digest": digest("sha256", &"b".repeat(64))
        },
        "operand_refs": [],
        "lifecycle": {
            "declaration": "Declared", "schema_binding": "Bound", "executor_binding": "Bound",
            "validation": "Validated", "admission": "Admitted",
            "schema_digest": schema, "executor_digest": executor
        },
        "residual_status": "HOLD", "authority_effect": "None", "authority_ceiling": "None"
    }})
}
fn assert_flag(payload: &Value, expected: bool) {
    let result = execute(payload).expect("well-formed lifecycle metadata");
    assert_eq!(result["is_executable"], json!(expected));
    assert_eq!(result["operation"]["authority_effect"], "None");
}

#[test]
fn canonical_zero_schema_evidence_is_not_executable() {
    assert_flag(
        &request(
            digest("sha256", &"0".repeat(64)),
            digest("sha256", &"c".repeat(64)),
        ),
        false,
    );
}
#[test]
fn canonical_zero_executor_evidence_is_not_executable() {
    assert_flag(
        &request(
            digest("sha256", &"b".repeat(64)),
            digest("sha256", &"0".repeat(64)),
        ),
        false,
    );
}
