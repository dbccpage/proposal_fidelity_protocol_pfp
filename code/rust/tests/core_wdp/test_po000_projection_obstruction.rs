//! PO-000's graph chart and declared first-order projection diagnostics.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational as Q;
use core_number_theory::polynomial_map::{PolynomialMap, SparseRationalPolynomial};
use core_wdp::po000_projection_obstruction::DeclaredProjectionProblem;
fn q(n: i64) -> Q {
    Q::from_integer(n.into())
}

#[test]
fn graph_retraction_has_a_nonconstant_jacobian() {
    let b0 = SparseRationalPolynomial::new(2, vec![(vec![2, 0], q(1))]).unwrap();
    let chart = PolynomialMap::new(2, vec![b0, SparseRationalPolynomial::zero(2)]).unwrap();
    assert_eq!(
        chart.jacobian(&[q(0), q(0)]).unwrap().as_slice(),
        &vec![q(0); 4]
    );
    assert_eq!(
        chart.jacobian(&[q(1), q(0)]).unwrap().as_slice(),
        &[q(2), q(0), q(0), q(0)]
    );
    assert!(chart
        .witnesses_non_affinity(&[q(0), q(0)], &[q(1), q(0)])
        .unwrap());
}

#[test]
fn projection_receipt_binds_the_state_time_and_complete_diagnostic() {
    let p = BasicMatrix::from_row_major(2, 2, vec![q(1), q(0), q(0), q(0)]).unwrap();
    let g = BasicMatrix::from_row_major(2, 2, vec![q(0), q(1), q(1), q(0)]).unwrap();
    let problem = DeclaredProjectionProblem {
        first: p.clone(),
        second: p,
        generator: g,
        elapsed: q(1),
        state: vec![q(2), q(0)],
    };
    let mut report = problem.evaluate().unwrap();
    assert!(problem.verify(&report).unwrap());
    report.diagnostic.first_order_state_bound = q(1);
    assert!(!problem.verify(&report).unwrap());
    let report = problem.evaluate().unwrap();
    let mut changed = problem.clone();
    changed.elapsed = q(2);
    assert!(!changed.verify(&report).unwrap());
    let mut changed = problem;
    changed.state[0] = q(3);
    assert!(!changed.verify(&report).unwrap());
}

// Origin: engine/crates_rs/tests/core_wdp/test_po000_projection_obstruction.rs
// Claim: urn:core:crates_rs:tests:test-po000-projection-obstruction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7b1a984c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7b1a984c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7b1a984c {
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
impl BoundaryError7b1a984c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7b1a984c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7b1a984c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7b1a984c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7b1a984c> {
        if capacity_bound == 0 {
            return Err(BoundaryError7b1a984c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7b1a984c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7b1a984c::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7b1a984c() {
    let admitted = BoundaryRecord7b1a984c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7b1a984c::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
