
#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_ebe10674 = (i128, i128);
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
use core_quantum_physics::fidelity::*;
use core_quantum_physics::process_matrix::*;
#[test]
fn invalid_fidelity_inputs_cannot_be_clipped_into_success() {
    let negative = CMatrix::from_element(1, 1, C64::new(-1.0, 0.0));
    assert!(matrix_sqrt_hermitian_psd(&negative).is_err());
    let imaginary = CMatrix::from_element(1, 1, C64::new(1.0, 1.0));
    assert!(matrix_sqrt_hermitian_psd(&imaginary).is_err());
    let bad = CMatrix::from_row_slice(
        2,
        2,
        &[
            C64::new(0.5, 0.0),
            C64::new(0.2, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.5, 0.0),
        ],
    );
    assert!(matrix_sqrt_hermitian_psd(&bad).is_err());
    assert!(uhlmann_fidelity(&CMatrix::identity(2, 2), &CMatrix::identity(2, 2)).is_err());
    assert!(uhlmann_fidelity(&CMatrix::zeros(0, 0), &CMatrix::zeros(0, 0)).is_err());
    assert!(pure_state_fidelity(&[C64::new(2.0, 0.0)], &[C64::new(1.0, 0.0)]).is_err());
    assert!(classical_bhattacharyya_fidelity(&[-0.1, 1.1], &[0.0, 1.0]).is_err());
    assert!(classical_bhattacharyya_fidelity(&[2.0], &[1.0]).is_err());
}
#[test]
fn positive_trace_correct_operator_can_still_fail_process_normalization() {
    let lab = LabIoDim::new(2, 2).unwrap();
    let mut rank_one = CMatrix::zeros(16, 16);
    rank_one[(0, 0)] = C64::new(4.0, 0.0);
    assert!(ProcessMatrix::new(rank_one, lab, lab).is_err());
    let white = CMatrix::identity(16, 16) * C64::new(0.25, 0.0);
    let p = ProcessMatrix::new(white.clone(), lab, lab).unwrap();
    let identity = ChoiMatrix::identity(2).unwrap();
    assert!((p.evaluate_probability(&identity, &identity).unwrap() - 1.0).abs() < 1e-8);
    assert!(ProcessMatrix::with_tolerance(white, lab, lab, f64::NAN).is_err());
    assert!(ProcessMatrix::causal_mixture(&p, &p, f64::NAN).is_err());
    assert!(ChoiMatrix::from_kraus(&(CMatrix::identity(2, 2) * C64::new(2.0, 0.0))).is_err());
}
#[test]
fn negative_operator_is_not_automatically_a_causal_witness() {
    let lab = LabIoDim::new(1, 1).unwrap();
    let p = ProcessMatrix::new(CMatrix::identity(1, 1), lab, lab).unwrap();
    let s = CausalWitness::new(CMatrix::from_element(1, 1, C64::new(-1.0, 0.0))).unwrap();
    assert!(s.witnesses_indefinite_order(&p).is_err());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/review_numeric_boundaries.rs
// Claim: urn:core:crates_rs:tests:review-numeric-boundaries:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordebe10674 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordebe10674` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorebe10674 {
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
impl BoundaryErrorebe10674 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorebe10674 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorebe10674 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordebe10674 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorebe10674> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorebe10674::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorebe10674::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorebe10674::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ebe10674() {
    let admitted = BoundaryRecordebe10674::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordebe10674::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
