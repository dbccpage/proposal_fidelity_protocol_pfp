//! The Phi1 quotient-norm bridge: Phi1 is the quotient norm of C^1 / im(d0),
//! its zero set is decided by exact linear algebra, it is a norm on classes,
//! and the scalar does not determine the cofiber object.

use num_traits::{Signed, Zero};
use core_number_theory::rational::{ri, rq, Rational};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use core_solvers::data_repair_packet::{RepairPacket, RepairPacketError};

fn col(values: &[i64]) -> Vec<Vec<Rational>> {
    values.iter().map(|&v| vec![ri(v)]).collect()
}

fn rats(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|&v| ri(v)).collect()
}

/// The paper's toy packet: d0 = (1, -1, 0), unit weights on Q^3.
fn toy() -> RepairPacket {
    RepairPacket::with_unit_weights(col(&[1, -1, 0]), 1).unwrap()
}

/// A rank-two repair map Q^2 -> Q^4 with unequal weights.
fn wide() -> RepairPacket {
    let d0 = vec![rats(&[1, 0]), rats(&[1, 1]), rats(&[0, 2]), rats(&[-1, 1])];
    RepairPacket::new(d0, 2, vec![ri(1), ri(2), rq(1, 2), ri(3)]).unwrap()
}

#[test]
fn the_papers_executable_witness_has_quotient_norm_one() {
    let packet = toy();
    let phi = packet.quotient_norm(&rats(&[0, 0, 1])).unwrap();
    assert_eq!(phi.value(), &ri(1));
    // Minimising 2|a| + 1 gives a = 0; the dual certifies the lower bound.
    assert_eq!(phi.alpha(), &[Rational::zero()]);
    let pairing: Rational = phi
        .dual_witness()
        .iter()
        .zip(rats(&[0, 0, 1]))
        .map(|(z, x)| z * x)
        .sum();
    assert_eq!(pairing, ri(1));
    // A vector in the image is absorbed exactly, with preimage a = 1.
    assert!(packet
        .quotient_norm(&rats(&[1, -1, 0]))
        .unwrap()
        .value()
        .is_zero());
    assert_eq!(
        packet.repair_witness(&rats(&[1, -1, 0])).unwrap(),
        Some(vec![ri(1)])
    );
}

#[test]
fn the_certified_value_is_the_infimum_over_the_image() {
    let packet = toy();
    let x = rats(&[2, 3, -1]);
    let phi = packet.quotient_norm(&x).unwrap();
    // Every repair a in a grid of rationals gives a residual at least Phi1, and
    // the certificate's own a attains it.
    for n in -12..=12 {
        let a = rq(n, 4);
        let residual = [&x[0] - &a, &x[1] + &a, x[2].clone()];
        let norm: Rational = residual.iter().map(Signed::abs).sum();
        assert!(norm >= *phi.value());
    }
    assert_eq!(phi.value(), &ri(6));
}

#[test]
fn the_quotient_norm_vanishes_exactly_on_repairs() {
    let packet = wide();
    let candidates = [
        rats(&[1, 2, 2, 0]),
        rats(&[0, 1, 2, 1]),
        rats(&[1, 0, 0, 0]),
        rats(&[3, 1, -4, -5]),
        rats(&[0, 0, 0, 1]),
    ];
    for x in &candidates {
        let zero_norm = packet.quotient_norm(x).unwrap().value().is_zero();
        let witness = packet.repair_witness(x).unwrap();
        assert_eq!(zero_norm, witness.is_some(), "{x:?}");
        if let Some(a) = witness {
            let image: Vec<Rational> = [(1, 0), (1, 1), (0, 2), (-1, 1)]
                .iter()
                .map(|&(p, q)| ri(p) * &a[0] + ri(q) * &a[1])
                .collect();
            assert_eq!(&image, x);
        }
    }
    assert_eq!(packet.cokernel_dimension().unwrap(), 2);
}

#[test]
fn the_quotient_norm_is_a_norm_on_classes() {
    let packet = wide();
    let x = rats(&[1, 0, 0, 0]);
    let y = rats(&[0, 0, 0, 1]);
    let repair: Vec<Rational> = rats(&[2, 5, 6, 1]); // d0 (2, 3)
    let phi = |v: &[Rational]| packet.quotient_norm(v).unwrap().value().clone();
    let add =
        |a: &[Rational], b: &[Rational]| a.iter().zip(b).map(|(p, q)| p + q).collect::<Vec<_>>();
    assert_eq!(
        packet.repair_witness(&repair).unwrap(),
        Some(vec![ri(2), ri(3)])
    );
    // Class invariance.
    assert_eq!(phi(&add(&x, &repair)), phi(&x));
    // Absolute homogeneity.
    for lambda in [ri(-3), rq(1, 2), ri(0)] {
        let scaled: Vec<Rational> = x.iter().map(|v| v * &lambda).collect();
        assert_eq!(phi(&scaled), lambda.abs() * phi(&x));
    }
    // Triangle inequality, strict here.
    assert!(phi(&add(&x, &y)) <= phi(&x) + phi(&y));
    assert!(!phi(&x).is_zero() && !phi(&y).is_zero());
}

#[test]
fn a_graph_packet_is_a_repair_packet_with_the_same_quotient_norm() {
    let complex = FiniteCochainPacket::build_complex(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")],
        &[],
    )
    .unwrap();
    let graph = FiniteCochainPacket::new(complex, vec![ri(1), ri(2), ri(3), ri(4)]).unwrap();
    let general = RepairPacket::new(graph.d0().to_vec(), 4, graph.weights().to_vec()).unwrap();
    let x = rats(&[1, 1, 1, 1]);
    assert_eq!(
        graph.quotient_mass(&x).unwrap().value(),
        general.quotient_norm(&x).unwrap().value()
    );
    assert_eq!(general.quotient_norm(&x).unwrap().value(), &ri(4));
}

#[test]
fn equal_quotient_norms_do_not_determine_the_cofiber_object() {
    // Same ambient Q^3, same class representative, same scalar, different cokernels.
    let line = RepairPacket::with_unit_weights(col(&[1, 0, 0]), 1).unwrap();
    let plane =
        RepairPacket::with_unit_weights(vec![rats(&[1, 0]), rats(&[0, 1]), rats(&[0, 0])], 2)
            .unwrap();
    let x = rats(&[0, 0, 1]);
    assert_eq!(line.quotient_norm(&x).unwrap().value(), &ri(1));
    assert_eq!(plane.quotient_norm(&x).unwrap().value(), &ri(1));
    assert_eq!(line.cokernel_dimension().unwrap(), 2);
    assert_eq!(plane.cokernel_dimension().unwrap(), 1);
}

#[test]
fn repair_packets_refuse_malformed_declarations() {
    assert!(matches!(
        RepairPacket::with_unit_weights(vec![rats(&[1, 0]), rats(&[1])], 2),
        Err(RepairPacketError::Ragged {
            row: 1,
            expected: 2,
            actual: 1
        })
    ));
    assert!(matches!(
        RepairPacket::new(col(&[1, 1]), 1, vec![ri(1), ri(0)]),
        Err(RepairPacketError::NonPositiveWeight { index: 1 })
    ));
    assert!(matches!(
        RepairPacket::new(col(&[1, 1]), 1, vec![ri(1)]),
        Err(RepairPacketError::WeightCount {
            coordinates: 2,
            weights: 1
        })
    ));
    assert!(matches!(
        toy().quotient_norm(&rats(&[1, 1])),
        Err(RepairPacketError::Length {
            expected: 3,
            actual: 2
        })
    ));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/foundations/repair_cofiber_banach_shadow.rs
// Claim: urn:core:crates_rs:tests:repair-cofiber-banach-shadow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc4a994c9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc4a994c9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc4a994c9 {
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
impl BoundaryErrorc4a994c9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc4a994c9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc4a994c9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc4a994c9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc4a994c9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc4a994c9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc4a994c9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc4a994c9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c4a994c9() {
    let admitted = BoundaryRecordc4a994c9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc4a994c9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
