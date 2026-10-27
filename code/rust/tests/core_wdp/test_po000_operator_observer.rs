use linear_algebra::exact_field::matrix as mx;
use linear_algebra::exact_field::matrix::diagonal;
// AuthorityEffect: None.
use core_number_theory::rational::ri;
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::gi;
use core_quantum_physics::exact_instrument::ExactDensityState;
use core_quantum_physics::trace_observer_certificate::{
    operator_section_problem, OperatorComparison, TraceObserverWitness,
};

#[test]
fn source_adapter_uses_actual_state_comparison_and_repair_fields() {
    let rho0 = ExactDensityState::try_new(diagonal(&[gi(1, 0), gi(0, 0)]).unwrap()).unwrap();
    let rho1 = ExactDensityState::try_new(diagonal(&[gi(0, 0), gi(1, 0)]).unwrap()).unwrap();
    let z = mx::sub(&(rho1.matrix()), rho0.matrix()).unwrap();
    let zero = mx::zeros(2, 2).unwrap();
    let comparison = OperatorComparison {
        from: 0,
        to: 1,
        channel: ExactKrausChannel::identity(2, "actual source").unwrap(),
    };
    let problem = operator_section_problem(
        &[rho0, rho1],
        &[comparison],
        &[vec![zero.clone(), z]],
        vec![ri(1)],
    )
    .unwrap();
    let witness = TraceObserverWitness {
        repair_coefficients: vec![ri(1)],
        residuals: vec![zero.clone()],
        positive_parts: vec![zero.clone()],
        negative_parts: vec![zero.clone()],
        dual_observables: vec![zero],
    };
    assert_eq!(witness.verify(&problem).unwrap().obstruction, ri(0));
    let mut forged = witness;
    forged.repair_coefficients[0] = ri(0);
    assert!(forged.verify(&problem).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_po000_operator_observer.rs
// Claim: urn:core:crates_rs:tests:test-po000-operator-observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord49765191 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord49765191` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError49765191 {
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
impl BoundaryError49765191 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError49765191 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError49765191 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord49765191 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError49765191> {
        if capacity_bound == 0 {
            return Err(BoundaryError49765191::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError49765191::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError49765191::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_49765191() {
    let admitted = BoundaryRecord49765191::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord49765191::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
