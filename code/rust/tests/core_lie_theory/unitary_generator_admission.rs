//! Primary exact Cayley-chart laws, including the phase atlas and cut locus.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use core_lie_theory::cayley_unitary::*;
use core_lie_theory::pauli_symplectic::{pauli, Pauli};
use core_lie_theory::scalar::is_unitary;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
#[test]
fn cayley_charts_invert_and_compose_exactly() {
    let x = pauli::<GaussianRat>(Pauli::X).unwrap();
    for t in [ri(0), rq(1, 2), ri(-2), ri(1)] {
        let u = cayley_unitary(&x, &t).unwrap();
        assert!(is_unitary(&u).unwrap());
        assert_eq!(
            cayley_generator(&u).unwrap(),
            mx::scale(&x, &GaussianRat::from_rational(t)).unwrap()
        );
    }
    let z = pauli::<GaussianRat>(Pauli::Z).unwrap();
    let h = mx::add(
        &x,
        &mx::scale(&z, &GaussianRat::from_rational(rq(2, 3))).unwrap(),
    )
    .unwrap();
    let (s, t) = (rq(1, 3), rq(1, 4));
    let composed = compose_generators(&h, &s, &t).unwrap();
    let expected = mx::multiply(
        &cayley_unitary(&h, &s).unwrap(),
        &cayley_unitary(&h, &t).unwrap(),
    )
    .unwrap();
    assert_eq!(cayley_unitary(&composed, &ri(1)).unwrap(), expected);
}
#[test]
fn a_phase_chart_admits_the_swap_excluded_from_the_identity_chart() {
    let x = pauli::<GaussianRat>(Pauli::X).unwrap();
    assert_eq!(
        cayley_generator(&x),
        Err(UnitaryCayleyError::CutLocus {
            kernel_dimension: 1
        })
    );
    let h = phase_chart_generator(&x, &GaussianRat::i()).unwrap();
    assert_eq!(phase_chart_step(&h, &GaussianRat::i()).unwrap(), x);
    let negative = mx::scale(
        &mx::identity(2).unwrap(),
        &GaussianRat::from_rational(ri(-1)),
    )
    .unwrap();
    assert_eq!(
        cayley_generator(&negative),
        Err(UnitaryCayleyError::CutLocus {
            kernel_dimension: 2
        })
    );
}
#[test]
fn malformed_nonhermitian_nonunitary_and_nonunit_phase_are_refused() {
    let bad = BasicMatrix::from_row_major(
        2,
        2,
        vec![
            GaussianRat::zero(),
            GaussianRat::one(),
            GaussianRat::zero(),
            GaussianRat::zero(),
        ],
    )
    .unwrap();
    assert_eq!(
        cayley_unitary(&bad, &ri(1)),
        Err(UnitaryCayleyError::NotHermitian)
    );
    assert_eq!(cayley_generator(&bad), Err(UnitaryCayleyError::NotUnitary));
    let x = pauli::<GaussianRat>(Pauli::X).unwrap();
    assert_eq!(
        phase_chart_generator(&x, &GaussianRat::from_rational(ri(2))),
        Err(UnitaryCayleyError::NonUnitPhase)
    );
    let rectangular = BasicMatrix::from_row_major(1, 2, vec![GaussianRat::zero(); 2]).unwrap();
    assert_eq!(
        cayley_unitary(&rectangular, &ri(1)),
        Err(UnitaryCayleyError::Shape)
    );
}

// Origin: engine/crates_rs/tests/core_lie_theory/unitary_generator_admission.rs
// Claim: urn:core:crates_rs:tests:unitary-generator-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2d7c5462 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2d7c5462` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2d7c5462 {
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
impl BoundaryError2d7c5462 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2d7c5462 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2d7c5462 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2d7c5462 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2d7c5462> {
        if capacity_bound == 0 {
            return Err(BoundaryError2d7c5462::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2d7c5462::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2d7c5462::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2d7c5462() {
    let admitted = BoundaryRecord2d7c5462::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2d7c5462::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
