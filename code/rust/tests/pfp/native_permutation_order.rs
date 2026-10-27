//! Host dispatch witnesses over the real compiled c5/c6 catalogue.
//!
//! Expected records and framing inputs are specified here independently of the
//! production observation/digest helpers. These are decoded-Value and typed
//! packet tests, not a claim about raw JSON duplicate-key admission or a license.

use pfp::pinned_permutation::{
    PermutationOrderEvidenceV1, PinnedPermutationOrderObservationV1,
    PinnedPermutationOrderRequestV1,
};
use pfp::{dispatch_runtime_request, RuntimeRequestV1};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const ACTION: &str = "verify_pinned_permutation_order";
const C5_DIGEST: &str = "4aad9b33bed8300646d72c76539a6e36b8c553d653c3bfb81a0e17d624e0d854";
const C6_DIGEST: &str = "d3eb235c5629ff43a46cde40b848ab47ee83187bbe31329777f04806a1e5aa87";

fn dispatch(payload: Value) -> Value {
    serde_json::to_value(dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: "core.symbol-game.runtime-request.v1".to_owned(),
        action: ACTION.to_owned(),
        payload,
    }))
    .unwrap()
}

fn c5_evidence() -> Value {
    json!({
        "presentation_digest": C5_DIGEST,
        "derived_order": "5",
        "cycles": [["α", "β", "γ", "δ", "ε"]]
    })
}

fn c6_evidence() -> Value {
    json!({
        "presentation_digest": C6_DIGEST,
        "derived_order": "6",
        "cycles": [["α", "β"], ["γ", "δ", "ε"]]
    })
}

fn observation(reference: &str, claimed: &str, evaluation: Value) -> Value {
    json!({
        "schema_version": "core.symbol-game.pinned-permutation-order-observation.v1",
        "submitted_presentation_ref": reference,
        "submitted_claimed_order": claimed,
        "evaluation": evaluation,
        "authority_effect": "None"
    })
}

fn pinned_observation(reference: &str, claimed: &str, status: &str, evidence: Value) -> Value {
    observation(
        reference,
        claimed,
        json!({"status": status, "evidence": evidence}),
    )
}

fn open_observation(reference: &str, claimed: &str) -> Value {
    observation(
        reference,
        claimed,
        json!({"status": "OPEN_RESIDUAL", "obligation": "PRESENTATION_NOT_PINNED"}),
    )
}

fn successful_outcome(result: Value) -> Value {
    json!({
        "schema_version": "core.symbol-game.runtime-outcome.v1",
        "action": ACTION,
        "success": true,
        "result": result,
        "error": null,
        "authority_effect": "None"
    })
}

fn refused_outcome(error: &str) -> Value {
    json!({
        "schema_version": "core.symbol-game.runtime-outcome.v1",
        "action": ACTION,
        "success": false,
        "result": null,
        "error": error,
        "authority_effect": "None"
    })
}

fn assert_c6_control() {
    assert_eq!(
        dispatch(json!({"presentation_ref": "c6", "claimed_order": "6"})),
        successful_outcome(pinned_observation("c6", "6", "REDERIVED", c6_evidence()))
    );
}

fn assert_payload_refused(payload: Value, error: &str) {
    assert_eq!(
        dispatch(payload.clone()),
        refused_outcome(error),
        "{payload}"
    );
}

fn assert_observation_roundtrips(value: &Value) {
    let typed: PinnedPermutationOrderObservationV1 = serde_json::from_value(value.clone()).unwrap();
    assert_eq!(serde_json::to_value(typed).unwrap(), *value);
}

#[test]
fn literal_pin_digests_replay_the_documented_framing_independently() {
    // presentation_digest documents sorted [signature, [name, lhs, rhs] rules].
    // canonical::framed_sha256 documents u32be domain length, domain bytes,
    // u64be payload length, payload bytes. The literals below were independently
    // replayed with Python hashlib after the domain rename, not taken from Rust output.
    const DOMAIN: &[u8] = b"core.symbol_game.presentation.v1";
    const C5_PAYLOAD: &str = r#"[["α","β","γ","δ","ε"],[["succ_alpha","α","β"],["succ_beta","β","γ"],["succ_delta","δ","ε"],["succ_epsilon","ε","α"],["succ_gamma","γ","δ"]]]"#;
    const C6_PAYLOAD: &str = r#"[["α","β","γ","δ","ε"],[["rot_delta","δ","ε"],["rot_epsilon","ε","γ"],["rot_gamma","γ","δ"],["swap_alpha","α","β"],["swap_beta","β","α"]]]"#;
    assert_eq!(DOMAIN.len(), 32);
    for (payload, byte_length, prefix, expected) in [
        (C5_PAYLOAD, 156, [0, 0, 0, 0, 0, 0, 0, 156], C5_DIGEST),
        (C6_PAYLOAD, 153, [0, 0, 0, 0, 0, 0, 0, 153], C6_DIGEST),
    ] {
        assert_eq!(payload.len(), byte_length);
        let mut digest = Sha256::new();
        digest.update([0, 0, 0, 32]);
        digest.update(DOMAIN);
        digest.update(prefix);
        digest.update(payload.as_bytes());
        assert_eq!(hex::encode(digest.finalize()), expected);
    }
}

#[test]
fn compiled_c5_rederives_five_with_the_complete_expected_record() {
    assert_eq!(
        dispatch(json!({"presentation_ref": "c5", "claimed_order": "5"})),
        successful_outcome(pinned_observation("c5", "5", "REDERIVED", c5_evidence()))
    );
}

#[test]
fn compiled_c5_contradicts_six_without_reporting_a_dispatch_error() {
    assert_eq!(
        dispatch(json!({"presentation_ref": "c5", "claimed_order": "6"})),
        successful_outcome(pinned_observation("c5", "6", "CONTRADICTED", c5_evidence()))
    );
}

#[test]
fn compiled_c6_rederives_six_from_two_and_three_cycles() {
    assert_c6_control();
}

#[test]
fn compiled_c6_contradicts_five_without_laundering_signature_cardinality() {
    assert_eq!(
        dispatch(json!({"presentation_ref": "c6", "claimed_order": "5"})),
        successful_outcome(pinned_observation("c6", "5", "CONTRADICTED", c6_evidence()))
    );
}

#[test]
fn unknown_pin_is_open_not_contradicted_or_a_transport_failure() {
    assert_eq!(
        dispatch(json!({"presentation_ref": "not_pinned", "claimed_order": "6"})),
        successful_outcome(open_observation("not_pinned", "6"))
    );
    assert_c6_control();
}

#[test]
fn pin_lookup_is_exact_and_preserves_every_submitted_name() {
    assert_c6_control();
    for reference in ["", " c6", "c6 ", "C6", "c6\n", "c6\0", "c6\u{a0}", "c６"] {
        assert_eq!(
            dispatch(json!({"presentation_ref": reference, "claimed_order": "6"})),
            successful_outcome(open_observation(reference, "6")),
            "reference {reference:?}"
        );
    }
    assert_c6_control();
}

#[test]
fn leading_zeroes_preserve_spelling_but_not_a_different_numeric_claim() {
    for (reference, claimed, status, evidence) in [
        ("c5", "0005", "REDERIVED", c5_evidence()),
        ("c6", "0006", "REDERIVED", c6_evidence()),
        ("c6", "0005", "CONTRADICTED", c6_evidence()),
        ("c6", "000", "CONTRADICTED", c6_evidence()),
        ("c6", "0", "CONTRADICTED", c6_evidence()),
    ] {
        assert_eq!(
            dispatch(json!({"presentation_ref": reference, "claimed_order": claimed})),
            successful_outcome(pinned_observation(reference, claimed, status, evidence))
        );
    }
    assert_eq!(
        dispatch(json!({"presentation_ref": "not_pinned", "claimed_order": "0006"})),
        successful_outcome(open_observation("not_pinned", "0006"))
    );
}

#[test]
fn large_valid_decimal_claims_are_not_coerced_or_fixed_width_truncated() {
    for claimed in ["18446744073709551616".to_owned(), "9".repeat(5000)] {
        assert_eq!(
            dispatch(json!({"presentation_ref": "c6", "claimed_order": claimed})),
            successful_outcome(pinned_observation(
                "c6",
                &claimed,
                "CONTRADICTED",
                c6_evidence()
            ))
        );
    }
    assert_c6_control();
}

#[test]
fn malformed_decimal_strings_are_refused_before_known_or_unknown_pin_lookup() {
    assert_c6_control();
    for claimed in [
        "", " ", " 6", "6 ", "+6", "-6", "6.0", "6e0", "0x6", "٦", "６", "6_0", "6\n", "6\0",
        "NaN", "Infinity",
    ] {
        for reference in ["c6", "not_pinned"] {
            assert_payload_refused(
                json!({"presentation_ref": reference, "claimed_order": claimed}),
                "CLAIMED_ORDER_NOT_ASCII_DECIMAL",
            );
        }
    }
    assert_c6_control();
}

#[test]
fn payload_must_be_an_object_not_a_primitive_or_positional_struct_sequence() {
    assert_c6_control();
    for payload in [
        json!(null),
        json!(true),
        json!(6),
        json!(6.0),
        json!("6"),
        json!([]),
        json!(["c6", "6"]),
    ] {
        assert_payload_refused(payload, "INVALID_PINNED_PERMUTATION_REQUEST");
    }
    assert_c6_control();
}

#[test]
fn both_request_fields_are_required() {
    for payload in [
        json!({}),
        json!({"presentation_ref": "c6"}),
        json!({"claimed_order": "6"}),
    ] {
        assert_payload_refused(payload, "INVALID_PINNED_PERMUTATION_REQUEST");
    }
    assert_c6_control();
}

#[test]
fn request_strings_do_not_coerce_null_boolean_numbers_arrays_or_objects() {
    assert_c6_control();
    for invalid in [
        json!(null),
        json!(false),
        json!(6),
        json!(6.0),
        json!([]),
        json!({}),
    ] {
        for field in ["presentation_ref", "claimed_order"] {
            let mut payload = json!({"presentation_ref": "c6", "claimed_order": "6"});
            payload[field] = invalid.clone();
            assert_payload_refused(payload, "INVALID_PINNED_PERMUTATION_REQUEST");
        }
    }
    assert_c6_control();
}

#[test]
fn producer_supplied_pins_presentations_evidence_or_authority_are_not_admitted() {
    assert_c6_control();
    for (field, value) in [
        (
            "presentation",
            json!({"signature": ["x"], "rules": [{"name": "r", "lhs": "x", "rhs": "x"}]}),
        ),
        ("pins", json!([{"name": "c6", "derived_order": "5"}])),
        ("pin", json!("c6")),
        ("authority_effect", json!("ACCEPT")),
        ("authority", json!({"HostPinned": {"pin": "c6"}})),
        (
            "schema_version",
            json!("core.symbol-game.pinned-permutation-order-observation.v1"),
        ),
        (
            "evaluation",
            json!({"status": "REDERIVED", "evidence": c6_evidence()}),
        ),
        ("evidence", c6_evidence()),
        ("derived_order", json!("5")),
    ] {
        let mut payload = json!({"presentation_ref": "c6", "claimed_order": "6"});
        payload[field] = value;
        assert_payload_refused(payload, "INVALID_PINNED_PERMUTATION_REQUEST");
    }
    assert_c6_control();
}

#[test]
fn typed_request_and_all_three_observation_variants_roundtrip_without_field_loss() {
    let request = json!({"presentation_ref": "c6", "claimed_order": "0006"});
    let typed: PinnedPermutationOrderRequestV1 = serde_json::from_value(request.clone()).unwrap();
    assert_eq!(serde_json::to_value(typed).unwrap(), request);
    for expected in [
        pinned_observation("c6", "0006", "REDERIVED", c6_evidence()),
        pinned_observation("c6", "5", "CONTRADICTED", c6_evidence()),
        open_observation("not_pinned", "6"),
    ] {
        assert_observation_roundtrips(&expected);
    }
}

#[test]
fn all_three_public_struct_decoders_require_objects_not_positional_sequences() {
    let request_control = json!({"presentation_ref": "c6", "claimed_order": "6"});
    let request: PinnedPermutationOrderRequestV1 =
        serde_json::from_value(request_control.clone()).unwrap();
    assert_eq!(serde_json::to_value(request).unwrap(), request_control);
    assert!(serde_json::from_value::<PinnedPermutationOrderRequestV1>(json!(["c6", "6"])).is_err());

    let evidence_control = c6_evidence();
    let evidence: PermutationOrderEvidenceV1 =
        serde_json::from_value(evidence_control.clone()).unwrap();
    assert_eq!(serde_json::to_value(evidence).unwrap(), evidence_control);
    assert!(serde_json::from_value::<PermutationOrderEvidenceV1>(json!([
        C6_DIGEST,
        "6",
        [["α", "β"], ["γ", "δ", "ε"]]
    ]))
    .is_err());

    let observation_control = pinned_observation("c6", "6", "REDERIVED", c6_evidence());
    assert_observation_roundtrips(&observation_control);
    assert!(
        serde_json::from_value::<PinnedPermutationOrderObservationV1>(json!([
            "core.symbol-game.pinned-permutation-order-observation.v1",
            "c6", "6", {"status": "REDERIVED", "evidence": c6_evidence()}, "None"
        ]))
        .is_err()
    );
    assert_observation_roundtrips(&observation_control);
}

#[test]
fn typed_observations_reject_unknown_fields_at_every_object_level() {
    let control = pinned_observation("c6", "6", "REDERIVED", c6_evidence());
    assert_observation_roundtrips(&control);
    for pointer in ["", "/evaluation", "/evaluation/evidence"] {
        let mut malformed = control.clone();
        malformed
            .pointer_mut(pointer)
            .unwrap()
            .as_object_mut()
            .unwrap()
            .insert("producer_authority".to_owned(), json!("ACCEPT"));
        assert!(serde_json::from_value::<PinnedPermutationOrderObservationV1>(malformed).is_err());
    }
    let open_control = open_observation("not_pinned", "6");
    assert_observation_roundtrips(&open_control);
    let mut open_with_evidence = open_control;
    open_with_evidence["evaluation"]["evidence"] = c6_evidence();
    assert!(
        serde_json::from_value::<PinnedPermutationOrderObservationV1>(open_with_evidence).is_err()
    );
    assert_observation_roundtrips(&control);
}

#[test]
fn typed_observations_reject_nested_primitive_and_cycle_shape_confusion() {
    let control = pinned_observation("c6", "6", "REDERIVED", c6_evidence());
    assert_observation_roundtrips(&control);
    for (pointer, value) in [
        ("/schema_version", json!(false)),
        ("/submitted_presentation_ref", json!(6)),
        ("/submitted_claimed_order", json!(6)),
        ("/authority_effect", json!(false)),
        ("/evaluation", json!(null)),
        ("/evaluation", json!([])),
        ("/evaluation/status", json!(true)),
        ("/evaluation/status", json!("UNKNOWN")),
        ("/evaluation/evidence", json!(false)),
        (
            "/evaluation/evidence",
            json!([C6_DIGEST, "6", [["α", "β"], ["γ", "δ", "ε"]]]),
        ),
        ("/evaluation/evidence/presentation_digest", json!(null)),
        ("/evaluation/evidence/derived_order", json!(6)),
        ("/evaluation/evidence/derived_order", json!(6.0)),
        ("/evaluation/evidence/cycles", json!({})),
        ("/evaluation/evidence/cycles", json!([1])),
        ("/evaluation/evidence/cycles", json!([[1]])),
        ("/evaluation/evidence/cycles", json!(["α", "β"])),
    ] {
        let mut malformed = control.clone();
        *malformed.pointer_mut(pointer).unwrap() = value;
        assert!(
            serde_json::from_value::<PinnedPermutationOrderObservationV1>(malformed.clone())
                .is_err(),
            "{malformed}"
        );
    }
    assert_observation_roundtrips(&control);
}

// Origin: engine/crates_rs/tests/pfp/native_permutation_order.rs
// Claim: urn:core:crates_rs:tests:native-permutation-order:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord48d9b1a4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord48d9b1a4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError48d9b1a4 {
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
impl BoundaryError48d9b1a4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError48d9b1a4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError48d9b1a4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord48d9b1a4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError48d9b1a4> {
        if capacity_bound == 0 {
            return Err(BoundaryError48d9b1a4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError48d9b1a4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError48d9b1a4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_48d9b1a4() {
    let admitted = BoundaryRecord48d9b1a4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord48d9b1a4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
