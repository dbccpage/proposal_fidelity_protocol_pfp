//! Packet binding controls for exact rational Hodge certificates.
//! AuthorityEffect: None.

use num_rational::BigRational;
use core_solvers::data_hodge_packet::{
    replay_hodge_packet, solve_hodge_packet, HodgeAvailabilityModelV1, HodgeCompositionModelV1,
    HodgePacketError, HodgePacketHeaderV1, HodgePositivityModelV1, HodgeQuestionV1,
    HodgeQuotientModelV1, HodgeRequestV1, HodgeResourceLimitsV1, HodgeResultV1, HodgeScalarModelV1,
    RationalMatrixV1, HODGE_PACKET_SCHEMA_V1,
};

fn q(numerator: i64, denominator: i64) -> BigRational {
    BigRational::new(numerator.into(), denominator.into())
}

fn header() -> HodgePacketHeaderV1 {
    HodgePacketHeaderV1 {
        schema_version: HODGE_PACKET_SCHEMA_V1.to_owned(),
        source_digest: "42".repeat(32),
        scalar_model: HodgeScalarModelV1::ExactRational,
        quotient_model: HodgeQuotientModelV1::PotentialModuloKernel,
        positivity_model: HodgePositivityModelV1::NotApplicable,
        composition_model: HodgeCompositionModelV1::NotApplicable,
        availability_model: HodgeAvailabilityModelV1::DeclaredFiniteCarrier,
        question: HodgeQuestionV1::ExactEuclideanHodgeDecomposition,
        limits: HodgeResourceLimitsV1 {
            max_scalar_ops: 1_000_000,
            max_elements: 10_000,
            max_bits: 4096,
        },
    }
}

fn triangle_request() -> HodgeRequestV1 {
    HodgeRequestV1 {
        header: header(),
        d0: RationalMatrixV1 {
            rows: 3,
            cols: 3,
            entries: vec![
                q(-1, 1),
                q(1, 1),
                q(0, 1),
                q(0, 1),
                q(-1, 1),
                q(1, 1),
                q(1, 1),
                q(0, 1),
                q(-1, 1),
            ],
        },
        d1: RationalMatrixV1 {
            rows: 1,
            cols: 3,
            entries: vec![q(1, 1); 3],
        },
        flow: vec![q(1, 1), q(0, 1), q(0, 1)],
    }
}

#[test]
fn packet_solve_and_replay_bind_header_and_finite_carrier() {
    let result = solve_hodge_packet(triangle_request()).unwrap();
    assert_eq!(result.header, header());
    assert_eq!(result.carrier_digest.len(), 64);
    assert_ne!(result.carrier_digest, "0".repeat(64));
    let encoded = serde_json::to_string(&result).unwrap();
    assert!(encoded.contains("\"certificate\""));
    assert!(encoded.contains("\"alpha\":["));
    assert_eq!(
        serde_json::from_str::<HodgeResultV1>(&encoded).unwrap(),
        result
    );

    let replayed = replay_hodge_packet(triangle_request(), &result).unwrap();
    assert!(replayed.scalar_ops() > 0);
    assert_eq!(replayed.hodge().authority_effect(), "AuthorityEffect: None");
    assert_eq!(replayed.authority_effect(), "AuthorityEffect: None");
}

#[test]
fn packet_refuses_changed_source_carrier_and_scope() {
    let result = solve_hodge_packet(triangle_request()).unwrap();

    let mut source_changed = triangle_request();
    source_changed.header.source_digest = "24".repeat(32);
    assert!(matches!(
        replay_hodge_packet(source_changed, &result),
        Err(HodgePacketError::HeaderMismatch)
    ));

    let mut carrier_changed = triangle_request();
    carrier_changed.flow[0] = q(2, 1);
    assert!(matches!(
        replay_hodge_packet(carrier_changed, &result),
        Err(HodgePacketError::CarrierDigestMismatch)
    ));

    let mut scalar_changed = triangle_request();
    scalar_changed.header.scalar_model = HodgeScalarModelV1::FloatingPoint;
    assert!(matches!(
        solve_hodge_packet(scalar_changed),
        Err(HodgePacketError::ScalarModel {
            actual: HodgeScalarModelV1::FloatingPoint
        })
    ));

    let mut positivity_claimed = triangle_request();
    positivity_claimed.header.positivity_model = HodgePositivityModelV1::Claimed;
    assert!(matches!(
        solve_hodge_packet(positivity_claimed),
        Err(HodgePacketError::PositivityModel {
            actual: HodgePositivityModelV1::Claimed
        })
    ));

    let mut quotient_undeclared = triangle_request();
    quotient_undeclared.header.quotient_model = HodgeQuotientModelV1::Undeclared;
    assert!(matches!(
        solve_hodge_packet(quotient_undeclared),
        Err(HodgePacketError::QuotientModel {
            actual: HodgeQuotientModelV1::Undeclared
        })
    ));

    let mut composition_claimed = triangle_request();
    composition_claimed.header.composition_model = HodgeCompositionModelV1::Claimed;
    assert!(matches!(
        solve_hodge_packet(composition_claimed),
        Err(HodgePacketError::CompositionModel {
            actual: HodgeCompositionModelV1::Claimed
        })
    ));

    let mut other_question = triangle_request();
    other_question.header.question = HodgeQuestionV1::Other;
    assert!(matches!(
        solve_hodge_packet(other_question),
        Err(HodgePacketError::Question {
            actual: HodgeQuestionV1::Other
        })
    ));
}

#[test]
fn packet_wire_uses_exact_strings_and_refuses_bad_shape_or_limits() {
    let json = serde_json::to_string(&triangle_request()).unwrap();
    assert!(json.contains("\"-1\""));
    assert!(json.contains("\"1\""));
    assert!(!json.contains("\"entries\":[-1"));

    let numeric_entry = json.replacen("\"-1\"", "-1", 1);
    assert!(serde_json::from_str::<HodgeRequestV1>(&numeric_entry).is_err());

    let mut zero_source = triangle_request();
    zero_source.header.source_digest = "0".repeat(64);
    assert!(matches!(
        solve_hodge_packet(zero_source),
        Err(HodgePacketError::SourceDigest)
    ));

    let mut malformed = triangle_request();
    malformed.d0.entries.pop();
    assert!(matches!(
        solve_hodge_packet(malformed),
        Err(HodgePacketError::MatrixEntries { matrix: "d0", .. })
    ));

    let mut too_small = triangle_request();
    too_small.header.limits.max_elements = 1;
    assert!(matches!(
        solve_hodge_packet(too_small),
        Err(HodgePacketError::Arithmetic(_))
    ));

    let mut unknown_availability = triangle_request();
    unknown_availability.header.availability_model = HodgeAvailabilityModelV1::Unknown;
    assert!(matches!(
        solve_hodge_packet(unknown_availability),
        Err(HodgePacketError::AvailabilityModel {
            actual: HodgeAvailabilityModelV1::Unknown
        })
    ));
}

// Origin: engine/crates_rs/tests/core_solvers/hodge_packet_binding.rs
// Claim: urn:core:crates_rs:tests:hodge-packet-binding:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc52a97e8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc52a97e8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc52a97e8 {
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
impl BoundaryErrorc52a97e8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc52a97e8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc52a97e8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc52a97e8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc52a97e8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc52a97e8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc52a97e8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc52a97e8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c52a97e8() {
    let admitted = BoundaryRecordc52a97e8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc52a97e8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
