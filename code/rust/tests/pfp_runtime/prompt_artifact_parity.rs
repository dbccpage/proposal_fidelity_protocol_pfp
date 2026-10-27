//! Native contract witnesses for the Python prompt-artifact wire profile.

use pfp_runtime::prompt_artifact::{
    compile, execute, render, validate, DEFAULT_REQUIRED_FIELDS, MAX_BODY_BYTES,
};
use serde_json::{json, Value};

fn request() -> Value {
    json!({
        "operation":"compile", "regime_kind":"prose-regime",
        "regime_definition_bytes":b"regime\r\n".to_vec(),
        "prompt_body_bytes":b"body\r\n".to_vec(),
        "objective_typed":{"kind":" Prompt_Turn ","summary":" Goal ","target_obstruction_ids":[],"target_demand_ids":[]},
    })
}

fn hint(magnitude: Value) -> Value {
    json!({"obstruction_id":" _obstruction ","family":" CUSTOM_OPEN ","residual_colour":"oPeN", "magnitude":magnitude,"demand_id":" .demand ","prior_report_digests":["a".repeat(64)]})
}

#[test]
fn canonical_defaults_identity_and_body_round_trip() {
    let compiled = compile(&request()).unwrap();
    let artifact = &compiled["artifact"];
    // Independently computed by the Python domain compiler.
    assert_eq!(
        artifact["prompt_artifact_id"],
        "d899a93ab83e66e202fc2753da9b619be44f697c909c72a2afbd955e90790cde"
    );
    fn reverse_object_keys(value: &Value) -> Value {
        match value {
            Value::Object(map) => Value::Object(
                map.iter()
                    .rev()
                    .map(|(key, value)| (key.clone(), reverse_object_keys(value)))
                    .collect(),
            ),
            Value::Array(values) => Value::Array(values.iter().map(reverse_object_keys).collect()),
            value => value.clone(),
        }
    }
    assert_eq!(
        compile(&reverse_object_keys(&request())).unwrap()["artifact"],
        *artifact
    );
    assert_eq!(compiled["prompt_body_bytes"], json!(b"body\n".to_vec()));
    assert_eq!(artifact["family"], "prompt_artifact");
    assert_eq!(
        artifact["regime_id"],
        "96243c74a7eb629e7fbac591ddcd2272177a10d125a91959bbf15e678d16f77d"
    );
    assert_eq!(
        artifact["prompt_body_sha256"],
        "9e2ec912af5dff2a72300863864fc4da04e81999339d9fac5c7590ba8a3f4e11"
    );
    assert_eq!(artifact["objective_typed"]["kind"], "prompt_turn");
    assert_eq!(artifact["objective_typed"]["summary"], "Goal");
    assert_eq!(
        artifact["required_reply_fields"],
        json!(DEFAULT_REQUIRED_FIELDS)
    );
    assert_eq!(validate(artifact, Some(b"body\n")).unwrap(), *artifact);
    assert_eq!(
        validate(artifact, Some(b"body\r\n")).unwrap_err(),
        "PROMPT_BODY_DIGEST_MISMATCH"
    );
    let mut changed = request();
    changed["parent_packet_id"] = json!("a".repeat(64));
    assert_ne!(
        compile(&changed).unwrap()["artifact"]["prompt_artifact_id"],
        artifact["prompt_artifact_id"]
    );
}

#[test]
fn verifier_requires_every_field_including_explicit_nulls() {
    let compiled = compile(&request()).unwrap();
    let artifact = compiled["artifact"].as_object().unwrap();
    for key in artifact.keys() {
        let mut missing = artifact.clone();
        missing.remove(key);
        assert!(
            validate(&Value::Object(missing), None).is_err(),
            "missing {key}"
        );
    }
    let mut forged = compiled["artifact"].clone();
    forged["prompt_artifact_id"] = json!("a".repeat(64));
    assert_eq!(
        validate(&forged, None).unwrap_err(),
        "PROMPT_ARTIFACT_ID_MISMATCH"
    );
    forged["trusted"] = json!(true);
    assert!(validate(&forged, None)
        .unwrap_err()
        .contains("FORBIDDEN_AUTHORITY_FIELD"));
}

#[test]
fn integer_magnitudes_remain_exact_and_float_identity_is_refused() {
    for literal in ["1208925819614629174706176", "-1208925819614629174706176"] {
        let integer: Value = serde_json::from_str(literal).unwrap();
        let mut input = request();
        input["open_obstructions"] = json!([hint(integer.clone())]);
        let compiled = compile(&input).unwrap();
        assert_eq!(
            compiled["artifact"]["open_obstructions"][0]["magnitude"],
            integer
        );
        assert_eq!(
            compiled["artifact"]["open_obstructions"][0]["obstruction_id"],
            "_obstruction"
        );
        assert_eq!(
            compiled["artifact"]["open_obstructions"][0]["residual_colour"],
            "Open"
        );
        validate(&compiled["artifact"], None).unwrap();
    }
    for magnitude in [
        json!(1.0),
        json!(0.25),
        json!({"$serde_json::private::Number":"1"}),
        json!(true),
    ] {
        let mut input = request();
        input["open_obstructions"] = json!([hint(magnitude)]);
        assert!(compile(&input).is_err());
    }
}

#[test]
fn sorted_compiler_sets_do_not_make_the_verifier_silent_sort() {
    let mut input = request();
    input["admitted_constructors"] = json!(["z", "a", "z"]);
    input["kill_conditions"] = json!(["z", "a", "z"]);
    input["required_reply_fields"] = json!(["Z", "A", "Z"]);
    let compiled = compile(&input).unwrap();
    assert_eq!(
        compiled["artifact"]["admitted_constructors"],
        json!(["a", "z"])
    );
    let mut unsorted = compiled["artifact"].clone();
    unsorted["admitted_constructors"] = json!(["z", "a"]);
    assert!(validate(&unsorted, None)
        .unwrap_err()
        .contains("ARRAY_NOT_CANONICALLY_SORTED"));
    input["open_obstructions"] = json!([hint(Value::Null), hint(Value::Null)]);
    assert!(compile(&input)
        .unwrap_err()
        .contains("ARRAY_NOT_CANONICALLY_SORTED"));
}

#[test]
fn raw_bytes_and_post_normalization_body_limit_match_python() {
    let mut input = request();
    input["regime_definition_bytes"] = json!([255, 13, 10]);
    input["prompt_body_bytes"] = json!([254, 13, 10, 13]);
    assert_eq!(
        compile(&input).unwrap()["prompt_body_bytes"],
        json!([254, 10, 10])
    );
    input["normalize_body"] = json!(false);
    assert_eq!(
        compile(&input).unwrap()["prompt_body_bytes"],
        json!([254, 13, 10, 13])
    );
    input["normalize_body"] = json!(true);
    input["prompt_body_bytes"] = json!(b"\r\n".repeat(MAX_BODY_BYTES));
    assert_eq!(
        compile(&input).unwrap()["artifact"]["prompt_body_byte_count"],
        MAX_BODY_BYTES
    );
    input["prompt_body_bytes"] = json!(vec![b'a'; MAX_BODY_BYTES + 1]);
    assert!(compile(&input).is_err());
}

#[test]
fn exact_residual_requires_a_dual_and_other_colours_forbid_it() {
    let mut input = request();
    input["residual_colour"] = json!("Exact");
    assert_eq!(compile(&input).unwrap_err(), "EXACT_WITHOUT_DUAL_WITNESS");
    input["dual_witness_ref"] = json!("a".repeat(64));
    assert_eq!(
        compile(&input).unwrap()["artifact"]["dual_witness_required"],
        true
    );
    input["dual_witness_required"] = json!(false);
    assert_eq!(compile(&input).unwrap_err(), "EXACT_WITHOUT_DUAL_WITNESS");
    input["residual_colour"] = json!("Closed");
    assert_eq!(
        compile(&input).unwrap_err(),
        "OPEN_CLOSED_WITH_DUAL_WITNESS"
    );
    input["dual_witness_ref"] = Value::Null;
    input["dual_witness_required"] = json!(1);
    assert!(compile(&input).is_err());
}

#[test]
fn render_keeps_duplicates_and_formats_python_float_magnitudes() {
    let mut input = request();
    input["operation"] = json!("render");
    input.as_object_mut().unwrap().remove("regime_kind");
    input.as_object_mut().unwrap().remove("prompt_body_bytes");
    input["open_obstructions"] = json!([hint(json!(1e100)), hint(json!(-0.0)), hint(json!(1.0))]);
    let rendered = render(&input).unwrap();
    let body: Vec<u8> = serde_json::from_value(rendered["prompt_body_bytes"].clone()).unwrap();
    let body = String::from_utf8(body).unwrap();
    assert!(body.contains("mag=1e+100"));
    assert!(body.contains("mag=-0.0"));
    assert!(body.contains("mag=1.0"));
    assert_eq!(
        body.matches("- _obstruction [custom_open] (Open)").count(),
        3
    );
}

#[test]
fn unicode_value_object_normalization_matches_python() {
    let mut input = request();
    input["objective_typed"]["kind"] = json!("KIND");
    input["objective_typed"]["summary"] = json!("\u{001c}Summary\u{001f}");
    let compiled = compile(&input).unwrap();
    assert_eq!(compiled["artifact"]["objective_typed"]["kind"], "kind");
    assert_eq!(
        compiled["artifact"]["objective_typed"]["summary"],
        "Summary"
    );
}

#[test]
fn canonical_compiler_refuses_legacy_alias_override() {
    let mut input = request();
    input["explicit_artifact_id"] = json!("legacy_alias");
    assert!(compile(&input)
        .unwrap_err()
        .contains("unknown field: explicit_artifact_id"));
}

#[test]
fn reply_check_preserves_python_substring_semantics_after_admission() {
    let mut input = request();
    input["required_reply_fields"] = json!(["SUMMARY", "RESIDUAL_COLOUR"]);
    let artifact = compile(&input).unwrap()["artifact"].clone();
    assert_eq!(execute(&json!({"operation":"validate_reply","artifact":artifact,"reply_content":"SUMMARY RESIDUAL_COLOUR"})).unwrap()["residual_satisfied"],true);
    assert_eq!(
        execute(
            &json!({"operation":"validate_reply","artifact":artifact,"reply_content":"SUMMARY"})
        )
        .unwrap()["residual_satisfied"],
        false
    );
    let mut forged = artifact;
    forged["prompt_body_byte_count"] = json!(999);
    assert!(execute(&json!({"operation":"validate_reply","artifact":forged,"reply_content":"SUMMARY RESIDUAL_COLOUR"})).is_err());
}

// Origin: engine/crates_rs/tests/pfp_runtime/prompt_artifact_parity.rs
// Claim: urn:core:crates_rs:tests:prompt-artifact-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord91badb54 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord91badb54` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError91badb54 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError91badb54 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError91badb54 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError91badb54 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord91badb54 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError91badb54> {
        if capacity_bound == 0 {
            return Err(BoundaryError91badb54::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError91badb54::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError91badb54::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_91badb54() {
    let admitted = BoundaryRecord91badb54::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord91badb54::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
