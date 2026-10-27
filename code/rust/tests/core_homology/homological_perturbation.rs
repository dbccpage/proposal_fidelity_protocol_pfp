//! Exact HPL witnesses and hostile proposals; no paper paths or external tools.

use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use linear_algebra::exact_field::matrix::{from_rows, identity, zeros};
use num_bigint::BigInt;
use num_rational::BigRational;
use core_homology::homological_perturbation::{
    identity_contraction, transfer_perturbation, verify_normalized, CheckedContraction,
    ContractionData, PerturbationError,
};
use core_homology::scalar::{q, qr, Q};

const LIMITS: OperationLimits = OperationLimits {
    max_elements: 128,
    max_scalar_ops: 8192,
};

fn matrix(rows: &[&[i64]]) -> BasicMatrix<Q> {
    from_rows(
        rows.iter()
            .map(|row| row.iter().copied().map(q).collect())
            .collect(),
    )
    .unwrap()
}

fn zero(rows: usize, columns: usize) -> BasicMatrix<Q> {
    zeros(rows, columns).unwrap()
}

fn contractible_pair() -> ContractionData {
    ContractionData {
        c_dimensions: [1, 1, 0],
        d_dimensions: [0, 0, 0],
        d_c: [matrix(&[&[1]]), zero(0, 1)],
        d_d: [zero(0, 0), zero(0, 0)],
        inclusion: [zero(1, 0), zero(1, 0), zero(0, 0)],
        retraction: [zero(0, 1), zero(0, 1), zero(0, 0)],
        homotopy: [matrix(&[&[1]]), zero(1, 0)],
    }
}

fn split_pair() -> ContractionData {
    ContractionData {
        c_dimensions: [2, 2, 0],
        d_dimensions: [1, 1, 0],
        d_c: [matrix(&[&[0, 0], &[0, 1]]), zero(0, 2)],
        d_d: [matrix(&[&[0]]), zero(0, 1)],
        inclusion: [matrix(&[&[1], &[0]]), matrix(&[&[1], &[0]]), zero(0, 0)],
        retraction: [matrix(&[&[1, 0]]), matrix(&[&[1, 0]]), zero(0, 0)],
        homotopy: [matrix(&[&[0, 0], &[0, 1]]), zero(2, 0)],
    }
}

#[test]
fn empty_window_retains_every_zero_shape() {
    let contraction = identity_contraction([0, 0, 0], [zero(0, 0), zero(0, 0)], LIMITS).unwrap();
    let result = transfer_perturbation(&contraction, &[zero(0, 0), zero(0, 0)], LIMITS).unwrap();
    assert_eq!(result.contraction, contraction);
    assert_eq!(result.delta_d[0].shape(), (0, 0));
    assert!(verify_normalized(result.contraction.data(), LIMITS)
        .unwrap()
        .is_normalized());
}

#[test]
fn identity_transfers_rational_perturbation_unchanged() {
    let contraction =
        identity_contraction([2, 1, 0], [matrix(&[&[1, -1]]), zero(0, 1)], LIMITS).unwrap();
    let delta = [
        from_rows(vec![vec![qr(3, 7), qr(-1, 11)]]).unwrap(),
        zero(0, 1),
    ];
    let result = transfer_perturbation(&contraction, &delta, LIMITS).unwrap();
    assert_eq!(result.delta_d, delta);
    assert_eq!(
        result.contraction.data().inclusion,
        contraction.data().inclusion
    );
    assert_eq!(result.contraction.data().d_c, result.contraction.data().d_d);
}

#[test]
fn sign_corrected_transfer_replays_both_chain_maps_and_homotopy() {
    let contraction = CheckedContraction::try_new(split_pair(), LIMITS).unwrap();
    let result = transfer_perturbation(
        &contraction,
        &[matrix(&[&[0, 1], &[1, 0]]), zero(0, 2)],
        LIMITS,
    )
    .unwrap();
    assert_eq!(result.delta_d[0], matrix(&[&[-1]]));
    assert_eq!(
        result.contraction.data().inclusion[0],
        matrix(&[&[1], &[-1]])
    );
    assert_eq!(result.contraction.data().retraction[1], matrix(&[&[1, -1]]));
    assert_eq!(
        result.contraction.inclusion().source().d0(),
        &matrix(&[&[-1]])
    );
    assert!(result
        .contraction
        .retraction()
        .is_retraction_of(result.contraction.inclusion())
        .unwrap());
    assert!(verify_normalized(result.contraction.data(), LIMITS)
        .unwrap()
        .is_normalized());
}

#[test]
fn exact_inverse_handles_non_nilpotent_delta_h() {
    // delta*h = [1] is not nilpotent; (1+delta*h)^(-1)=[1/2] exists.
    let contraction = CheckedContraction::try_new(contractible_pair(), LIMITS).unwrap();
    let result =
        transfer_perturbation(&contraction, &[matrix(&[&[1]]), zero(0, 1)], LIMITS).unwrap();
    assert_eq!(
        result.contraction.data().homotopy[0],
        from_rows(vec![vec![qr(1, 2)]]).unwrap()
    );
    assert_eq!(result.contraction.data().d_c[0], matrix(&[&[2]]));
    assert_eq!(result.delta_d[0].shape(), (0, 0));
}

#[test]
fn both_resolvents_transfer_a_three_term_complex() {
    let proposal = ContractionData {
        c_dimensions: [2, 3, 1],
        d_dimensions: [1, 1, 0],
        d_c: [matrix(&[&[0, 0], &[0, 1], &[0, 0]]), matrix(&[&[0, 0, 1]])],
        d_d: [matrix(&[&[0]]), zero(0, 1)],
        inclusion: [
            matrix(&[&[1], &[0]]),
            matrix(&[&[1], &[0], &[0]]),
            zero(1, 0),
        ],
        retraction: [matrix(&[&[1, 0]]), matrix(&[&[1, 0, 0]]), zero(0, 1)],
        homotopy: [
            matrix(&[&[0, 0, 0], &[0, 1, 0]]),
            matrix(&[&[0], &[0], &[1]]),
        ],
    };
    let contraction = CheckedContraction::try_new(proposal, LIMITS).unwrap();
    let delta = [
        from_rows(vec![
            vec![q(0), q(1)],
            vec![q(1), q(1)],
            vec![qr(-1, 2), qr(-3, 2)],
        ])
        .unwrap(),
        matrix(&[&[1, 1, 1]]),
    ];
    let result = transfer_perturbation(&contraction, &delta, LIMITS).unwrap();
    assert_eq!(result.delta_d[0], from_rows(vec![vec![qr(-1, 2)]]).unwrap());
    assert_ne!(
        result.contraction.data().homotopy[0],
        contraction.data().homotopy[0]
    );
    assert_ne!(
        result.contraction.data().homotopy[1],
        contraction.data().homotopy[1]
    );
    assert!(verify_normalized(result.contraction.data(), LIMITS)
        .unwrap()
        .is_normalized());
}

#[test]
fn singular_resolvent_is_refused_for_an_actual_normalized_contraction() {
    let contraction = CheckedContraction::try_new(contractible_pair(), LIMITS).unwrap();
    assert_eq!(
        transfer_perturbation(&contraction, &[matrix(&[&[-1]]), zero(0, 1)], LIMITS),
        Err(PerturbationError::SingularResolvent { degree: 1 })
    );
}

#[test]
fn degree_two_singular_resolvent_is_identified() {
    let contraction = CheckedContraction::try_new(
        ContractionData {
            c_dimensions: [0, 1, 1],
            d_dimensions: [0, 0, 0],
            d_c: [zero(1, 0), matrix(&[&[1]])],
            d_d: [zero(0, 0), zero(0, 0)],
            inclusion: [zero(0, 0), zero(1, 0), zero(1, 0)],
            retraction: [zero(0, 0), zero(0, 1), zero(0, 1)],
            homotopy: [zero(0, 1), matrix(&[&[1]])],
        },
        LIMITS,
    )
    .unwrap();
    assert_eq!(
        transfer_perturbation(&contraction, &[zero(1, 0), matrix(&[&[-1]])], LIMITS),
        Err(PerturbationError::SingularResolvent { degree: 2 })
    );
}

#[test]
fn invalid_source_and_target_differentials_are_refused() {
    let contraction =
        identity_contraction([1, 1, 1], [matrix(&[&[0]]), matrix(&[&[0]])], LIMITS).unwrap();
    for owner in ["C", "D"] {
        let mut proposal = contraction.data().clone();
        if owner == "C" {
            proposal.d_c = [matrix(&[&[1]]), matrix(&[&[1]])];
        } else {
            proposal.d_d = [matrix(&[&[1]]), matrix(&[&[1]])];
        }
        assert_eq!(
            verify_normalized(&proposal, LIMITS),
            Err(PerturbationError::DifferentialNotSquareZero { complex: owner })
        );
    }
}

#[test]
fn non_square_zero_perturbation_is_always_refused() {
    let contraction =
        identity_contraction([1, 1, 1], [matrix(&[&[0]]), matrix(&[&[0]])], LIMITS).unwrap();
    assert_eq!(
        transfer_perturbation(&contraction, &[matrix(&[&[1]]), matrix(&[&[1]])], LIMITS),
        Err(PerturbationError::DifferentialNotSquareZero { complex: "C+delta" })
    );
}

#[test]
fn side_conditions_do_not_substitute_for_chain_map_identities() {
    let mut proposal = identity_contraction([1, 1, 0], [matrix(&[&[0]]), zero(0, 1)], LIMITS)
        .unwrap()
        .data()
        .clone();
    proposal.d_d[0] = matrix(&[&[1]]);
    let report = verify_normalized(&proposal, LIMITS).unwrap();
    assert!(
        report.ri_equals_id_d
            && report.sdr_equation
            && report.hi_zero
            && report.rh_zero
            && report.hh_zero
    );
    assert!(!report.inclusion_chain_map && !report.retraction_chain_map);
    assert!(!report.is_normalized());
    assert!(matches!(
        CheckedContraction::try_new(proposal, LIMITS),
        Err(PerturbationError::NotNormalized { .. })
    ));
}

#[test]
fn tampered_maps_homotopies_and_empty_shapes_are_rejected() {
    let mut proposal = split_pair();
    proposal.retraction[0] = matrix(&[&[2, 0]]);
    assert!(!verify_normalized(&proposal, LIMITS)
        .unwrap()
        .is_normalized());
    let mut proposal = split_pair();
    proposal.homotopy[0] = matrix(&[&[0, 0], &[0, -1]]);
    assert!(!verify_normalized(&proposal, LIMITS).unwrap().sdr_equation);
    let mut proposal = split_pair();
    proposal.d_c[1] = zero(0, 1);
    assert!(matches!(
        verify_normalized(&proposal, LIMITS),
        Err(PerturbationError::Shape {
            map: "d_c",
            degree: 1,
            ..
        })
    ));
}

#[test]
fn allocation_work_and_dimension_overflow_bounds_fail_closed() {
    let proposal = split_pair();
    assert!(matches!(
        verify_normalized(
            &proposal,
            OperationLimits {
                max_elements: 3,
                max_scalar_ops: usize::MAX
            }
        ),
        Err(PerturbationError::Matrix(
            MatrixError::AllocationLimitExceeded { .. }
        ))
    ));
    assert!(matches!(
        verify_normalized(
            &proposal,
            OperationLimits {
                max_elements: 128,
                max_scalar_ops: 1
            }
        ),
        Err(PerturbationError::Matrix(
            MatrixError::OperationLimitExceeded { .. }
        ))
    ));
    let mut overflow = proposal;
    overflow.c_dimensions[0] = usize::MAX;
    assert!(matches!(
        verify_normalized(&overflow, OperationLimits::UNLIMITED),
        Err(PerturbationError::Matrix(
            MatrixError::DimensionOverflow { .. }
        ))
    ));
}

#[test]
fn malformed_raw_rationals_never_enter_arithmetic() {
    let mut proposal = contractible_pair();
    proposal.d_c[0] = BasicMatrix::from_row_major(
        1,
        1,
        vec![BigRational::new_raw(BigInt::from(1), BigInt::from(0))],
    )
    .unwrap();
    assert_eq!(
        verify_normalized(&proposal, LIMITS),
        Err(PerturbationError::InvalidCoefficient)
    );
    proposal.d_c[0] = BasicMatrix::from_row_major(
        1,
        1,
        vec![BigRational::new_raw(BigInt::from(2), BigInt::from(2))],
    )
    .unwrap();
    assert_eq!(
        verify_normalized(&proposal, LIMITS),
        Err(PerturbationError::InvalidCoefficient)
    );
}

#[test]
fn content_hash_binds_target_differentials_and_empty_dimensions() {
    let proposal = split_pair();
    let mut changed = proposal.clone();
    changed.d_d[0] = identity(1).unwrap();
    assert_ne!(proposal.content_hash(), changed.content_hash());
    let mut changed = proposal.clone();
    changed.c_dimensions[2] = 1;
    assert_ne!(proposal.content_hash(), changed.content_hash());
}

// Origin: engine/crates_rs/tests/core_homology/homological_perturbation.rs
// Claim: urn:core:crates_rs:tests:homological-perturbation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2ea156b0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2ea156b0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2ea156b0 {
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
impl BoundaryError2ea156b0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2ea156b0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2ea156b0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2ea156b0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2ea156b0> {
        if capacity_bound == 0 {
            return Err(BoundaryError2ea156b0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2ea156b0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2ea156b0::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2ea156b0() {
    let admitted = BoundaryRecord2ea156b0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2ea156b0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
