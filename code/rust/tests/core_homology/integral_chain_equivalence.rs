//! Positive and adversarial checks of exact integral chain-equivalence
//! certificates. Fixtures are explicit cellular complexes over Z.
//! AuthorityEffect: None.

use core_homology::f2_cohomology::ComplexError;
use core_homology::integral_chain_complex::{IntegralChainComplex, SparseIntegerMatrix};
use core_homology::integral_chain_equivalence::{
    checked_cycle_cocycle_pairing, verify_chain_equivalence, ChainEquivalenceCertificate,
    ChainEquivalenceError, ChainIdentity, MapFamily,
};

fn matrix(rows: usize, columns: Vec<Vec<(usize, i64)>>) -> SparseIntegerMatrix {
    SparseIntegerMatrix::new(rows, columns).unwrap()
}

fn zero(rows: usize, cols: usize) -> SparseIntegerMatrix {
    matrix(rows, vec![Vec::new(); cols])
}

fn identity(n: usize) -> SparseIntegerMatrix {
    matrix(n, (0..n).map(|j| vec![(j, 1)]).collect())
}

fn interval() -> IntegralChainComplex {
    IntegralChainComplex::new(vec![2, 1], vec![matrix(2, vec![vec![(0, -1), (1, 1)]])]).unwrap()
}

fn point() -> IntegralChainComplex {
    IntegralChainComplex::new(vec![1], vec![]).unwrap()
}

fn circle() -> IntegralChainComplex {
    IntegralChainComplex::new(vec![1, 1], vec![zero(1, 1)]).unwrap()
}

fn interval_to_point() -> ChainEquivalenceCertificate {
    ChainEquivalenceCertificate {
        projection: vec![matrix(1, vec![vec![(0, 1)], vec![(0, 1)]]), zero(0, 1)],
        inclusion: vec![matrix(2, vec![vec![(0, 1)]]), zero(1, 0)],
        source_homotopy: vec![matrix(1, vec![vec![], vec![(0, -1)]]), zero(0, 1)],
        target_homotopy: vec![zero(0, 1), zero(0, 0)],
    }
}

fn identity_certificate(complex: &IntegralChainComplex) -> ChainEquivalenceCertificate {
    let maps: Vec<_> = (0..=complex.top_dimension())
        .map(|k| identity(complex.cell_count(k)))
        .collect();
    let homotopy: Vec<_> = (0..=complex.top_dimension())
        .map(|k| zero(complex.cell_count(k + 1), complex.cell_count(k)))
        .collect();
    ChainEquivalenceCertificate {
        projection: maps.clone(),
        inclusion: maps,
        source_homotopy: homotopy.clone(),
        target_homotopy: homotopy,
    }
}

#[test]
fn interval_contraction_reconstructs_signed_integral_fillings() {
    let source = interval();
    let target = point();
    let proposal = interval_to_point();
    let checked = verify_chain_equivalence(&source, &target, &proposal).unwrap();
    assert_eq!(checked.source(), &source);
    assert_eq!(checked.target(), &target);
    assert_eq!(checked.certificate(), &proposal);
    for coefficient in [-100, -1, 0, 1, 100] {
        let cycle = [-coefficient, coefficient];
        assert_eq!(checked.project_chain(0, &cycle).unwrap(), vec![0]);
        assert_eq!(
            checked.reconstruct_source_boundary(0, &cycle, &[]).unwrap(),
            vec![coefficient]
        );
    }
    assert_eq!(checked.include_chain(0, &[7]).unwrap(), vec![7, 0]);
}

#[test]
fn nonzero_target_homotopy_is_checked_and_preserves_pairing() {
    let source = point();
    let target = interval();
    let reverse = interval_to_point();
    let proposal = ChainEquivalenceCertificate {
        projection: reverse.inclusion,
        inclusion: reverse.projection,
        source_homotopy: reverse.target_homotopy,
        target_homotopy: reverse.source_homotopy,
    };
    let checked = proposal.verify(&source, &target).unwrap();
    let witness = checked
        .transport_target_obstruction(0, &[1, 0], &[1, 1])
        .unwrap();
    assert_eq!(witness.source_cycle(), &[1]);
    assert_eq!(witness.source_cocycle(), &[1]);
    assert_eq!(witness.pairing(), 1);
    let mut forged = proposal.clone();
    forged.target_homotopy[0] = zero(1, 2);
    assert!(matches!(
        forged.verify(&source, &target),
        Err(ChainEquivalenceError::Identity {
            identity: ChainIdentity::ProjectionInclusionMinusIdentity,
            degree: 0
        })
    ));
}

#[test]
fn circle_obstruction_survives_orientation_reversal() {
    let source = circle();
    let target = circle();
    let mut proposal = identity_certificate(&source);
    proposal.projection[1] = matrix(1, vec![vec![(0, -1)]]);
    proposal.inclusion[1] = matrix(1, vec![vec![(0, -1)]]);
    let checked = proposal.verify(&source, &target).unwrap();
    let witness = checked.transport_target_obstruction(1, &[3], &[2]).unwrap();
    assert_eq!(witness.degree(), 1);
    assert_eq!(witness.target_cycle(), &[3]);
    assert_eq!(witness.target_cocycle(), &[2]);
    assert_eq!(witness.source_cycle(), &[-3]);
    assert_eq!(witness.source_cocycle(), &[-2]);
    assert_eq!(witness.pairing(), 6);
    assert_eq!(witness.equivalence().source(), &source);
    assert!(matches!(
        checked.reconstruct_source_boundary(1, &[3], &[]),
        Err(ChainEquivalenceError::TargetFillingMismatch { degree: 1 })
    ));
}

#[test]
fn zero_pairing_is_not_advertised_as_nonboundary() {
    let complex = circle();
    let proposal = identity_certificate(&complex);
    let checked = proposal.verify(&complex, &complex).unwrap();
    assert_eq!(
        checked_cycle_cocycle_pairing(&complex, 1, &[0], &[1]).unwrap(),
        0
    );
    assert!(matches!(
        checked.transport_target_obstruction(1, &[0], &[1]),
        Err(ChainEquivalenceError::ZeroPairing { degree: 1 })
    ));
}

#[test]
fn circle_cannot_be_certified_equivalent_to_point() {
    let source = circle();
    let target = point();
    let proposal = ChainEquivalenceCertificate {
        projection: vec![identity(1), zero(0, 1)],
        inclusion: vec![identity(1), zero(1, 0)],
        source_homotopy: vec![zero(1, 1), zero(0, 1)],
        target_homotopy: vec![zero(0, 1), zero(0, 0)],
    };
    assert!(matches!(
        proposal.verify(&source, &target),
        Err(ChainEquivalenceError::Identity {
            identity: ChainIdentity::InclusionProjectionMinusIdentity,
            degree: 1
        })
    ));
}

#[test]
fn chain_map_identities_are_checked_independently_in_positive_degree() {
    let complex = IntegralChainComplex::new(vec![1, 1], vec![identity(1)]).unwrap();
    let mut projection = identity_certificate(&complex);
    projection.projection[1] = matrix(1, vec![vec![(0, 2)]]);
    assert!(matches!(
        projection.verify(&complex, &complex),
        Err(ChainEquivalenceError::Identity {
            identity: ChainIdentity::ProjectionCommutesWithBoundary,
            degree: 1
        })
    ));
    let mut inclusion = identity_certificate(&complex);
    inclusion.inclusion[1] = matrix(1, vec![vec![(0, 2)]]);
    assert!(matches!(
        inclusion.verify(&complex, &complex),
        Err(ChainEquivalenceError::Identity {
            identity: ChainIdentity::InclusionCommutesWithBoundary,
            degree: 1
        })
    ));
}

#[test]
fn reconstruction_checks_a_nonempty_supplied_filling() {
    let complex = interval();
    let proposal = identity_certificate(&complex);
    let checked = proposal.verify(&complex, &complex).unwrap();
    assert_eq!(
        checked
            .reconstruct_source_boundary(0, &[-2, 2], &[2])
            .unwrap(),
        vec![2]
    );
    assert!(matches!(
        checked.reconstruct_source_boundary(0, &[-2, 2], &[3]),
        Err(ChainEquivalenceError::TargetFillingMismatch { degree: 0 })
    ));
}

#[test]
fn omitted_or_extra_degree_maps_are_refused_for_every_family() {
    let source = interval();
    let target = point();
    for family in [
        MapFamily::Projection,
        MapFamily::Inclusion,
        MapFamily::SourceHomotopy,
        MapFamily::TargetHomotopy,
    ] {
        for extra in [false, true] {
            let mut proposal = interval_to_point();
            let maps = match family {
                MapFamily::Projection => &mut proposal.projection,
                MapFamily::Inclusion => &mut proposal.inclusion,
                MapFamily::SourceHomotopy => &mut proposal.source_homotopy,
                MapFamily::TargetHomotopy => &mut proposal.target_homotopy,
            };
            if extra {
                maps.push(zero(0, 0));
            } else {
                maps.pop();
            }
            assert!(
                matches!(proposal.verify(&source, &target), Err(ChainEquivalenceError::MapCount {
                family: refused, expected: 2, actual
            }) if refused == family && actual == if extra { 3 } else { 1 })
            );
        }
    }
}

#[test]
fn shape_checks_include_empty_and_top_homotopy_matrices() {
    let source = interval();
    let target = point();
    let mut proposal = interval_to_point();
    proposal.source_homotopy[1] = zero(1, 1);
    assert!(matches!(
        proposal.verify(&source, &target),
        Err(ChainEquivalenceError::MapShape {
            family: MapFamily::SourceHomotopy,
            degree: 1,
            expected: (0, 1),
            actual: (1, 1)
        })
    ));
    let mut proposal = interval_to_point();
    proposal.projection[1] = zero(0, 0);
    assert!(matches!(
        proposal.verify(&source, &target),
        Err(ChainEquivalenceError::MapShape {
            family: MapFamily::Projection,
            degree: 1,
            expected: (0, 1),
            actual: (0, 0)
        })
    ));
}

#[test]
fn altered_homotopy_sign_or_map_entry_is_refused() {
    let source = interval();
    let target = point();
    let mut proposal = interval_to_point();
    proposal.source_homotopy[0] = matrix(1, vec![vec![], vec![(0, 1)]]);
    assert!(matches!(
        proposal.verify(&source, &target),
        Err(ChainEquivalenceError::Identity {
            identity: ChainIdentity::InclusionProjectionMinusIdentity,
            degree: 0
        })
    ));
    let mut proposal = interval_to_point();
    proposal.inclusion[0] = matrix(2, vec![vec![(0, 2)]]);
    assert!(proposal.verify(&source, &target).is_err());
}

#[test]
fn certificate_is_bound_to_boundary_coefficients_not_only_dimensions() {
    let source = interval();
    let altered =
        IntegralChainComplex::new(vec![2, 1], vec![matrix(2, vec![vec![(0, 1), (1, -1)]])])
            .unwrap();
    let target = point();
    let proposal = interval_to_point();
    assert!(proposal.verify(&source, &target).is_ok());
    assert!(proposal.verify(&altered, &target).is_err());
}

#[test]
fn rejected_shapes_cycles_cocycles_and_fillings_are_not_repaired() {
    let source = interval();
    let target = point();
    let proposal = interval_to_point();
    let checked = proposal.verify(&source, &target).unwrap();
    assert!(matches!(
        checked.project_chain(0, &[1]),
        Err(ChainEquivalenceError::VectorShape { .. })
    ));
    assert!(matches!(
        checked.include_chain(usize::MAX, &[]),
        Err(ChainEquivalenceError::Complex(
            ComplexError::DegreeOutOfRange { .. }
        ))
    ));
    assert!(matches!(
        checked.reconstruct_source_boundary(1, &[1], &[]),
        Err(ChainEquivalenceError::Complex(ComplexError::NotACycle {
            degree: 1
        }))
    ));
    assert!(matches!(
        checked.reconstruct_source_boundary(0, &[1, 0], &[]),
        Err(ChainEquivalenceError::TargetFillingMismatch { degree: 0 })
    ));
    assert!(matches!(
        checked.reconstruct_source_boundary(0, &[-1, 1], &[0]),
        Err(ChainEquivalenceError::VectorShape { .. })
    ));
    assert!(matches!(
        checked_cycle_cocycle_pairing(&source, 0, &[1, 0], &[1, 0]),
        Err(ChainEquivalenceError::Complex(ComplexError::NotACocycle {
            degree: 0
        }))
    ));
    assert!(matches!(
        checked_cycle_cocycle_pairing(&source, 0, &[1, 0], &[1]),
        Err(ChainEquivalenceError::VectorShape { .. })
    ));
}

#[test]
fn empty_complexes_and_trailing_zero_degrees_are_checked() {
    let empty = IntegralChainComplex::new(vec![0], vec![]).unwrap();
    let empty_proposal = identity_certificate(&empty);
    let checked = empty_proposal.verify(&empty, &empty).unwrap();
    assert_eq!(
        checked.reconstruct_source_boundary(0, &[], &[]).unwrap(),
        Vec::<i64>::new()
    );
    let padded = IntegralChainComplex::new(vec![1, 0, 0], vec![zero(1, 0), zero(0, 0)]).unwrap();
    let target = point();
    let proposal = identity_certificate(&padded);
    let checked = proposal.verify(&padded, &target).unwrap();
    assert_eq!(checked.project_chain(2, &[]).unwrap(), Vec::<i64>::new());
    assert_eq!(
        checked.reconstruct_source_boundary(2, &[], &[]).unwrap(),
        Vec::<i64>::new()
    );
}

#[test]
fn checked_arithmetic_refuses_product_overflow() {
    let complex = point();
    let mut proposal = identity_certificate(&complex);
    proposal.projection[0] = matrix(1, vec![vec![(0, i64::MAX)]]);
    proposal.inclusion[0] = matrix(1, vec![vec![(0, i64::MAX)]]);
    assert!(matches!(
        proposal.verify(&complex, &complex),
        Err(ChainEquivalenceError::Complex(
            ComplexError::Overflow { .. }
        ))
    ));
}

#[test]
fn valid_large_basis_change_refuses_overflowing_chain_images() {
    let complex = IntegralChainComplex::new(vec![2], vec![]).unwrap();
    let proposal = ChainEquivalenceCertificate {
        projection: vec![matrix(2, vec![vec![(0, 1)], vec![(0, i64::MAX), (1, 1)]])],
        inclusion: vec![matrix(2, vec![vec![(0, 1)], vec![(0, -i64::MAX), (1, 1)]])],
        source_homotopy: vec![zero(0, 2)],
        target_homotopy: vec![zero(0, 2)],
    };
    let checked = proposal.verify(&complex, &complex).unwrap();
    assert!(matches!(
        checked.project_chain(0, &[1, 1]),
        Err(ChainEquivalenceError::Complex(
            ComplexError::Overflow { .. }
        ))
    ));
    assert!(matches!(
        checked.include_chain(0, &[1, -1]),
        Err(ChainEquivalenceError::Complex(
            ComplexError::Overflow { .. }
        ))
    ));
}

#[test]
fn torsion_cycle_does_not_gain_a_fabricated_integral_cocycle_witness() {
    let complex = IntegralChainComplex::new(
        vec![1, 1, 1],
        vec![zero(1, 1), matrix(1, vec![vec![(0, 2)]])],
    )
    .unwrap();
    let proposal = identity_certificate(&complex);
    let checked = proposal.verify(&complex, &complex).unwrap();
    assert!(matches!(
        checked.transport_target_obstruction(1, &[1], &[1]),
        Err(ChainEquivalenceError::Complex(ComplexError::NotACocycle {
            degree: 1
        }))
    ));
    assert!(matches!(
        checked.transport_target_obstruction(1, &[1], &[0]),
        Err(ChainEquivalenceError::ZeroPairing { degree: 1 })
    ));
}

#[test]
fn pairing_is_i128_and_refuses_accumulation_overflow() {
    let complex = IntegralChainComplex::new(vec![3], vec![]).unwrap();
    let large = i128::from(i64::MAX) * i128::from(i64::MAX);
    assert_eq!(
        checked_cycle_cocycle_pairing(&complex, 0, &[i64::MAX, 0, 0], &[i64::MAX, 0, 0]).unwrap(),
        large
    );
    assert!(matches!(
        checked_cycle_cocycle_pairing(&complex, 0, &[i64::MAX; 3], &[i64::MAX; 3]),
        Err(ChainEquivalenceError::Complex(
            ComplexError::Overflow { .. }
        ))
    ));
}

// Origin: engine/crates_rs/tests/core_homology/integral_chain_equivalence.rs
// Claim: urn:core:crates_rs:tests:integral-chain-equivalence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf959ce74 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf959ce74` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf959ce74 {
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
impl BoundaryErrorf959ce74 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf959ce74 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf959ce74 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf959ce74 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf959ce74> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf959ce74::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf959ce74::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf959ce74::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f959ce74() {
    let admitted = BoundaryRecordf959ce74::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf959ce74::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
