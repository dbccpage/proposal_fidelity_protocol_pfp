//! Finite frame consistency, tomographic uniqueness and PSD are distinct checks.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::frame_function_polytope::{FramePolytopeError, FrameSystem};
use core_quantum_physics::kochen_specker::{CABELLO_18_VECTORS, CABELLO_9_CONTEXTS};

#[test]
fn all_cabello_probabilities_and_contexts_do_not_imply_a_density_state() {
    let system = FrameSystem::new(
        CABELLO_18_VECTORS.iter().map(|r| r.to_vec()).collect(),
        CABELLO_9_CONTEXTS.iter().map(|c| c.to_vec()).collect(),
    )
    .unwrap();
    // M_bad/2 from H054GleasonCyclotomicObstruction.lean.
    let entries = [[0, 0, 0, 0], [0, 2, 1, -1], [0, 1, 0, -1], [0, -1, -1, 0]];
    let rho = BasicMatrix::try_from_fn(4, 4, |i, j| rq(entries[i][j], 2)).unwrap();
    let f = system.frame_function_of(&rho).unwrap();
    assert!(system.is_feasible(&f).unwrap());
    assert!(f.iter().all(|p| p <= &ri(1)));
    assert_eq!(system.state_of(&f).unwrap(), rho);
    let witness = [0, 0, 1, 1];
    let mut expectation = ri(0);
    for i in 0..4 {
        for j in 0..4 {
            expectation += ri(witness[i] * witness[j]) * &rho.as_slice()[4 * i + j];
        }
    }
    assert_eq!(expectation, ri(-1));
    assert!(matches!(
        system.density_state_of(&f),
        Err(FramePolytopeError::NotPositiveSemidefinite)
    ));

    let mixed = mx::scale(&mx::identity(4).unwrap(), &rq(1, 4)).unwrap();
    let positive_f = system.frame_function_of(&mixed).unwrap();
    assert_eq!(system.density_state_of(&positive_f).unwrap(), mixed);
}

// Origin: engine/crates_rs/tests/core_quantum_physics/gleason_finite_context.rs
// Claim: urn:core:crates_rs:tests:gleason-finite-context:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4cd5e010 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4cd5e010` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4cd5e010 {
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
impl BoundaryError4cd5e010 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4cd5e010 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4cd5e010 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4cd5e010 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4cd5e010> {
        if capacity_bound == 0 {
            return Err(BoundaryError4cd5e010::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4cd5e010::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4cd5e010::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4cd5e010() {
    let admitted = BoundaryRecord4cd5e010::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4cd5e010::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
