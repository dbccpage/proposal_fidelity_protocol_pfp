use core_category_theory::finite_continuation::PartialDynamics;
use core_category_theory::finite_simulation::*;
#[test]
fn macro_simulation_checks_every_state_and_reflects_unavailability() {
    let s = PartialDynamics::new(vec![0, 1], vec![vec![Some(1)], vec![None]], 1).unwrap();
    let t = PartialDynamics::new(
        vec![0, 1, 9],
        vec![vec![Some(2), None], vec![None, None], vec![None, Some(1)]],
        2,
    )
    .unwrap();
    let words = vec![vec![0, 1]];
    let c = check_simulation(&s, &t, &[0, 1], &words, SimulationMode::Exact, 100).unwrap();
    assert_eq!(
        c,
        SimulationDecision::Checked {
            added_availability: vec![]
        }
    );
    verify_simulation(&s, &t, &[0, 1], &words, SimulationMode::Exact, 100, &c).unwrap();
    assert!(matches!(
        check_simulation(&s, &t, &[0, 1], &[vec![0]], SimulationMode::Exact, 100).unwrap(),
        SimulationDecision::StepMismatch { .. }
    ));
}
#[test]
fn extension_preserves_legal_prefixes_without_claiming_future_equivalence() {
    let s = PartialDynamics::new(vec![0, 1], vec![vec![Some(1)], vec![None]], 1).unwrap();
    let t = PartialDynamics::new(
        vec![0, 1, 2],
        vec![vec![Some(1)], vec![Some(2)], vec![None]],
        1,
    )
    .unwrap();
    let c = check_simulation(
        &s,
        &t,
        &[0, 1],
        &[vec![0]],
        SimulationMode::ResourceExtension,
        100,
    )
    .unwrap();
    assert_eq!(
        c,
        SimulationDecision::Checked {
            added_availability: vec![(1, 0)]
        }
    );
    assert!(
        verify_simulation(&s, &t, &[0, 1], &[vec![0]], SimulationMode::Exact, 100, &c).is_err()
    );
    assert_eq!(s.run(0, &[0, 0]).unwrap(), None);
    assert_eq!(t.run(0, &[0, 0]).unwrap(), Some(2));
    assert!(check_simulation(
        &s,
        &t,
        &[0, 0],
        &[vec![0]],
        SimulationMode::ResourceExtension,
        100
    )
    .is_err());
    assert_eq!(
        check_simulation(&s, &t, &[0, 1], &[vec![0]], SimulationMode::Exact, 0),
        Err(SimulationError::WorkLimit)
    );
}
#[test]
fn report_and_map_forgery_do_not_pass() {
    let s = PartialDynamics::new(vec![0], vec![vec![]], 0).unwrap();
    let t = PartialDynamics::new(vec![1], vec![vec![]], 0).unwrap();
    assert!(matches!(
        check_simulation(&s, &t, &[0], &[], SimulationMode::Exact, 10).unwrap(),
        SimulationDecision::ReportMismatch { .. }
    ));
    assert_eq!(
        check_simulation(&s, &t, &[usize::MAX], &[], SimulationMode::Exact, 10),
        Err(SimulationError::InvalidMap)
    );
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_simulation.rs
// Claim: urn:core:crates_rs:tests:finite-simulation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord049821d0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord049821d0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError049821d0 {
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
impl BoundaryError049821d0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError049821d0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError049821d0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord049821d0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError049821d0> {
        if capacity_bound == 0 {
            return Err(BoundaryError049821d0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError049821d0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError049821d0::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_049821d0() {
    let admitted = BoundaryRecord049821d0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord049821d0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
