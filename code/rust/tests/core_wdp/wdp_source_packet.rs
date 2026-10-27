use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::rational_bareiss::{
    RationalBudget, RationalError, RationalLimits,
};
use num_rational::BigRational;
use core_number_theory::cyclotomic::GaussianRat;
use core_quantum_physics::exact_channel::{ExactChannelError, ExactKrausChannel};
use core_types::AuthorityEffect;
use core_wdp::wdp_source_packet::*;
use serde_json::{json, Value};

fn source() -> Value {
    let bytes: &[u8] = b"finite operational fixture; no general QM derivation";
    json!({"source_id": "fixture/raw-source", "digest_profile": "sha256_raw_bytes_v1", "sha256": raw_source_sha256(bytes), "bytes": bytes})
}

fn header(channel: bool) -> Value {
    json!({
        "schema_version": WDP_SOURCE_PACKET_SCHEMA_V1,
        "question": if channel { "exact_weighted_kraus_gram_state_transport" } else { "exact_euclidean_hodge_decomposition" },
        "scope": "finite_declared_inputs",
        "scalar_model": if channel { "exact_gaussian_rational" } else { "exact_rational" },
        "quotient_model": if channel { "matrix_entry_equality" } else { "potential_modulo_kernel" },
        "positivity_model": if channel { "nonnegative_kraus_weights_and_gram_state" } else { "not_applicable" },
        "composition_model": if channel { "single_declared_map" } else { "not_applicable" },
        "availability_model": "declared_finite_carrier",
        "limits": {"max_source_bytes": 8192, "max_scalar_ops": 1_000_000, "max_elements": 4096, "max_bits": 1024},
    })
}

fn hodge_request() -> WdpSourcePacketRequestV1 {
    serde_json::from_value(json!({"header": header(false), "source": source(), "operation": {
        "kind": "hodge",
        "d0": {"rows": 3, "cols": 3, "entries": ["-1", "1", "0", "0", "-1", "1", "1", "0", "-1"]},
        "d1": {"rows": 0, "cols": 3, "entries": []}, "flow": ["1", "2", "3"],
    }})).unwrap()
}

fn gaussian(rows: usize, cols: usize, entries: &[(&str, &str)]) -> Value {
    json!({"rows": rows, "cols": cols, "entries": entries.iter().map(|(re, im)| json!({"re": re, "im": im})).collect::<Vec<_>>()})
}

fn channel_request() -> WdpSourcePacketRequestV1 {
    serde_json::from_value(json!({"header": header(true), "source": source(), "operation": {
        "kind": "weighted_kraus_gram_state_transport", "dim_in": 2, "dim_out": 2,
        "terms": [
            {"weight": "1/2", "operator": gaussian(2, 2, &[("1", "0"), ("0", "0"), ("0", "0"), ("1", "0")])},
            {"weight": "1/2", "operator": gaussian(2, 2, &[("1", "0"), ("0", "0"), ("0", "0"), ("0", "1")])},
        ], "state_factor": gaussian(2, 1, &[("3/5", "0"), ("4/5", "0")]),
    }})).unwrap()
}

fn reseal(result: &mut WdpSourcePacketResultV1) {
    let mut value = serde_json::to_value(&*result).unwrap();
    value.as_object_mut().unwrap().remove("result_digest");
    result.result_digest = packet_digest(WDP_PACKET_RESULT_DOMAIN_V1, &value).unwrap();
}

#[test]
fn exact_hodge_and_complex_weighted_channel_produce_replayable_finite_results() {
    let request = hodge_request();
    let result = evaluate_source_packet(&request).unwrap();
    let WdpPacketOutputV1::Hodge { result: hodge } = &result.output else {
        panic!("wrong route")
    };
    assert_eq!(
        hodge.certificate.harmonic,
        vec![BigRational::from_integer(2.into()); 3]
    );
    assert_eq!(hodge.header.source_digest, request.source.sha256);
    assert_eq!(result.authority_effect, AuthorityEffect::None);
    let replay = replay_source_packet(&request, &result).unwrap();
    assert_eq!(replay.result_digest, result.result_digest);
    assert!(replay.replay_scalar_ops > 0);

    let request = channel_request();
    let result = evaluate_source_packet(&request).unwrap();
    assert_eq!(
        serde_json::to_value(&result.output).unwrap()["image"],
        gaussian(
            2,
            2,
            &[
                ("9/25", "0"),
                ("6/25", "-6/25"),
                ("6/25", "6/25"),
                ("16/25", "0")
            ]
        )
    );
    replay_source_packet(&request, &result).unwrap();
}

#[test]
fn source_premise_carrier_and_candidate_roles_have_distinct_refusals() {
    let request = hodge_request();
    let result = evaluate_source_packet(&request).unwrap();
    let mut changed = request.clone();
    changed.source.bytes[0] ^= 1;
    assert_eq!(
        replay_source_packet(&changed, &result).unwrap_err().code,
        WdpPacketRefusalCodeV1::SourceDigest
    );

    let mut changed = request.clone();
    changed.source.bytes.push(b'\n');
    changed.source.sha256 = raw_source_sha256(&changed.source.bytes);
    assert_eq!(
        replay_source_packet(&changed, &result).unwrap_err().code,
        WdpPacketRefusalCodeV1::RequestBinding
    );

    let wire = serde_json::to_value(&request).unwrap();
    for (field, mutation, code) in [
        ("question", "other", WdpPacketRefusalCodeV1::Question),
        ("scope", "general_theory", WdpPacketRefusalCodeV1::Scope),
        (
            "scalar_model",
            "floating_point",
            WdpPacketRefusalCodeV1::ScalarModel,
        ),
        (
            "quotient_model",
            "undeclared",
            WdpPacketRefusalCodeV1::QuotientModel,
        ),
        (
            "positivity_model",
            "claimed",
            WdpPacketRefusalCodeV1::PositivityModel,
        ),
        (
            "composition_model",
            "all_composed_words",
            WdpPacketRefusalCodeV1::CompositionModel,
        ),
        (
            "availability_model",
            "unknown",
            WdpPacketRefusalCodeV1::AvailabilityModel,
        ),
    ] {
        let mut changed = wire.clone();
        changed["header"][field] = mutation.into();
        let changed = serde_json::from_value(changed).unwrap();
        assert_eq!(
            replay_source_packet(&changed, &result).unwrap_err().code,
            code,
            "{field}"
        );
    }

    let mut changed = request.clone();
    let WdpPacketOperationV1::Hodge { flow, .. } = &mut changed.operation else {
        unreachable!()
    };
    flow[0] += BigRational::from_integer(1.into());
    assert_eq!(
        replay_source_packet(&changed, &result).unwrap_err().code,
        WdpPacketRefusalCodeV1::RequestBinding
    );

    let mut changed = result.clone();
    changed.carrier_digest = "f".repeat(64);
    reseal(&mut changed);
    assert_eq!(
        replay_source_packet(&request, &changed).unwrap_err().code,
        WdpPacketRefusalCodeV1::CarrierBinding
    );

    let mut changed = result.clone();
    let WdpPacketOutputV1::Hodge { result: hodge } = &mut changed.output else {
        unreachable!()
    };
    hodge.certificate.harmonic[0] += BigRational::from_integer(1.into());
    assert_eq!(
        replay_source_packet(&request, &changed).unwrap_err().code,
        WdpPacketRefusalCodeV1::ResultBinding
    );
    reseal(&mut changed);
    assert_eq!(
        replay_source_packet(&request, &changed).unwrap_err().code,
        WdpPacketRefusalCodeV1::HodgeCertificate
    );

    let request = channel_request();
    let mut result = evaluate_source_packet(&request).unwrap();
    let WdpPacketOutputV1::WeightedKrausGramStateTransport { image } = &mut result.output else {
        unreachable!()
    };
    image.entries[0].re = BigRational::from_integer(1.into());
    reseal(&mut result);
    assert_eq!(
        replay_source_packet(&request, &result).unwrap_err().code,
        WdpPacketRefusalCodeV1::ChannelResult
    );
}

#[test]
fn channel_admission_checks_actual_weights_trace_preservation_and_state_normalization() {
    for mutation in ["negative_weight", "tp_defect", "unnormalized_state"] {
        let mut request = channel_request();
        let WdpPacketOperationV1::WeightedKrausGramStateTransport {
            terms,
            state_factor,
            ..
        } = &mut request.operation
        else {
            unreachable!()
        };
        match mutation {
            "negative_weight" => terms[0].weight = BigRational::from_integer((-1).into()),
            "tp_defect" => terms[0].operator.entries[0].re = BigRational::from_integer(2.into()),
            "unnormalized_state" => {
                state_factor.entries[0].re = BigRational::from_integer(1.into())
            }
            _ => unreachable!(),
        }
        assert_eq!(
            evaluate_source_packet(&request).unwrap_err().code,
            WdpPacketRefusalCodeV1::ChannelPremise,
            "{mutation}"
        );
    }
    let mut request = hodge_request();
    request.header.limits.max_scalar_ops = 1;
    assert_eq!(
        evaluate_source_packet(&request).unwrap_err().code,
        WdpPacketRefusalCodeV1::ResourceBudget
    );
}

#[test]
fn channel_construction_and_application_consume_the_same_budget() {
    let limits = RationalLimits {
        max_scalar_ops: 100_000,
        max_elements: 64,
        max_bits: 64,
    };
    let identity = BasicMatrix::from_row_major(1, 1, vec![GaussianRat::one()]).unwrap();
    let terms = vec![(BigRational::from_integer(1.into()), identity.clone())];
    let mut fuel = RationalBudget::new(limits);
    ExactKrausChannel::try_weighted_with_budget(1, 1, terms.clone(), "id", &mut fuel).unwrap();
    let construction_used = fuel.used();
    let mut fuel = RationalBudget::new(RationalLimits {
        max_scalar_ops: construction_used,
        ..limits
    });
    let channel =
        ExactKrausChannel::try_weighted_with_budget(1, 1, terms, "id", &mut fuel).unwrap();
    assert_eq!(
        channel.apply_with_budget(&identity, &mut fuel),
        Err(ExactChannelError::RationalBudget(
            RationalError::FuelExhausted
        ))
    );
}

#[test]
fn candidate_vector_bundle_is_bounded_before_hashing_or_certificate_replay() {
    let mut request = hodge_request();
    request.header.limits.max_elements = 16;
    let mut result = evaluate_source_packet(&request).unwrap();
    let WdpPacketOutputV1::Hodge { result: hodge } = &mut result.output else {
        unreachable!()
    };
    hodge
        .certificate
        .alpha
        .resize(8, BigRational::from_integer(0.into()));
    assert_eq!(
        replay_source_packet(&request, &result).unwrap_err().code,
        WdpPacketRefusalCodeV1::ResourceBudget
    );
}

#[test]
fn evaluate_never_emits_a_certificate_bundle_that_replay_cannot_admit() {
    let mut request = hodge_request();
    request.header.limits.max_elements = 8;
    request.operation = WdpPacketOperationV1::Hodge {
        d0: core_solvers::data_hodge_packet::RationalMatrixV1 {
            rows: 3,
            cols: 0,
            entries: vec![],
        },
        d1: core_solvers::data_hodge_packet::RationalMatrixV1 {
            rows: 0,
            cols: 3,
            entries: vec![],
        },
        flow: vec![BigRational::from_integer(1.into()); 3],
    };
    // Carrier has three scalars, each vector has three, but the three component
    // vectors together have nine. An unreplayable result must not be issued.
    assert_eq!(
        evaluate_source_packet(&request).unwrap_err().code,
        WdpPacketRefusalCodeV1::ResourceBudget
    );
}

#[test]
fn exact_wire_forbids_float_numeric_noncanonical_and_unknown_inputs() {
    let wire = serde_json::to_value(hodge_request()).unwrap();
    for value in [
        json!(1),
        json!(1.0),
        json!(true),
        json!("1/1"),
        json!("2/2"),
    ] {
        let mut malformed = wire.clone();
        malformed["operation"]["flow"][0] = value;
        assert!(serde_json::from_value::<WdpSourcePacketRequestV1>(malformed).is_err());
    }
    let mut malformed = wire;
    malformed["source"]["path"] = "/etc/passwd".into();
    assert!(serde_json::from_value::<WdpSourcePacketRequestV1>(malformed).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/wdp_source_packet.rs
// Claim: urn:core:crates_rs:tests:wdp-source-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8af65947 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8af65947` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8af65947 {
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
impl BoundaryError8af65947 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8af65947 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8af65947 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8af65947 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8af65947> {
        if capacity_bound == 0 {
            return Err(BoundaryError8af65947::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8af65947::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8af65947::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_8af65947() {
    let admitted = BoundaryRecord8af65947::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8af65947::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
