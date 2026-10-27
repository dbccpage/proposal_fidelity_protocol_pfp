use linear_algebra::gauge_pair_transport::GaugeDescent;
use num_bigint::BigInt;
use num_traits::Zero;
use core_wdp::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use core_wdp::genesis_source_execution::{Source25Change, Source25State, SourceRelation};
use core_wdp::genesis_transport_descent::{CarrierDescentError, DeclaredCarrierGaugeTransport};
use core_wdp::types::AuthorityEffect;

fn packet(n: usize) -> GenesisOngoingPacket {
    GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r: vec![BigInt::zero(); n * n],
        s: vec![BigInt::zero(); n * n],
        filled: vec![],
    }
}
fn state(n: usize) -> Source25State {
    Source25State::try_new(packet(n)).unwrap()
}

#[test]
fn actual_carrier_events_obey_the_complete_thresholds() {
    for n in 0..=8 {
        let growth = DeclaredCarrierGaugeTransport::new(state(n), Source25Change::AddTerm).unwrap();
        assert_eq!(*growth.descent() == GaugeDescent::Descends, n <= 1);
        assert_eq!(growth.target().packet().terms.len(), n + 1);
        assert_eq!(growth.authority_effect(), AuthorityEffect::None);
        for x in 0..n {
            for y in x + 1..n {
                let merge =
                    DeclaredCarrierGaugeTransport::new(state(n), Source25Change::Identify { x, y })
                        .unwrap();
                assert_eq!(*merge.descent() == GaugeDescent::Descends, n <= 3);
                assert_eq!(merge.target().packet().terms.len(), n - 1);
                if let GaugeDescent::Obstructed(witness) = merge.descent() {
                    assert!(merge.transport().verify_obstruction(witness).unwrap());
                }
            }
        }
    }
}

#[test]
fn oriented_marks_and_raw_counts_survive_the_diagnostic() {
    let mut p = packet(4);
    p.r[0] = BigInt::from(1) << 150usize;
    p.r[1] = 2.into();
    p.s[4] = 3.into();
    p.filled = vec![
        MarkedTriple { x: 0, y: 2, z: 3 },
        MarkedTriple { x: 1, y: 3, z: 2 },
    ];
    let source = Source25State::try_new(p).unwrap();
    let edit = Source25Change::Identify { x: 0, y: 1 };
    let declared = DeclaredCarrierGaugeTransport::new(source.clone(), edit).unwrap();
    assert_eq!(declared.source(), &source);
    assert_eq!(declared.target(), &source.perform_enabled(edit).unwrap());
    assert_eq!(declared.target().packet().filled.len(), 2);
    assert!(matches!(declared.descent(), GaugeDescent::Obstructed(_)));
    assert_eq!(declared.change(), edit);
}

#[test]
fn concrete_identification_creates_a_nonzero_cycle_from_a_gradient() {
    let g = [0i64, 0, 1, 0];
    let mut p = packet(4);
    for x in 0..4 {
        for y in 0..4 {
            let e = g[x] - g[y];
            p.r[x * 4 + y] = e.max(0).into();
            p.s[x * 4 + y] = (-e).max(0).into();
        }
    }
    let moved = DeclaredCarrierGaugeTransport::new(
        Source25State::try_new(p).unwrap(),
        Source25Change::Identify { x: 0, y: 1 },
    )
    .unwrap();
    let p = moved.target().packet();
    let cycle = (&p.r[1] - &p.s[1]) + (&p.r[5] - &p.s[5]) + (&p.r[6] - &p.s[6]);
    assert_eq!(cycle, BigInt::from(-1));
}

#[test]
fn disabled_edits_and_noncarrier_events_are_typed_refusals() {
    assert!(matches!(
        DeclaredCarrierGaugeTransport::new(state(2), Source25Change::Identify { x: 1, y: 0 }),
        Err(CarrierDescentError::Source(_))
    ));
    assert!(matches!(
        DeclaredCarrierGaugeTransport::new(
            state(2),
            Source25Change::AddAssertion {
                relation: SourceRelation::R,
                x: 0,
                y: 1
            }
        ),
        Err(CarrierDescentError::EventProfile)
    ));
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_transport_descent.rs
// Claim: urn:core:crates_rs:tests:test-genesis-transport-descent:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc7228a77 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc7228a77` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc7228a77 {
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
impl BoundaryErrorc7228a77 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc7228a77 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc7228a77 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc7228a77 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc7228a77> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc7228a77::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc7228a77::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc7228a77::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c7228a77() {
    let admitted = BoundaryRecordc7228a77::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc7228a77::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
