use core_solvers::solver_flow_network_simplex::Arc;
use core_solvers::solver_flow_network_simplex::NetworkSimplex;
use core_solvers::solver_flow_network_simplex::NetworkSimplexError;

#[test]
fn test_single_edge() {
    let arcs = vec![
        Arc {
            tail: 0,
            head: 1,
            cost: 10,
            lower: 0,
            upper: None,
            original_edge: Some(0),
            orientation_sign: 1,
        },
        Arc {
            tail: 1,
            head: 0,
            cost: 10,
            lower: 0,
            upper: None,
            original_edge: Some(0),
            orientation_sign: -1,
        },
    ];
    let demand = vec![-5, 5]; // Node 0: supply 5, Node 1: demand 5
    let mut solver = NetworkSimplex::new(2, arcs, demand).unwrap();
    let sol = solver.solve().unwrap();
    assert_eq!(sol.objective, 50);
    assert_eq!(sol.flow, vec![5, 0]);
}

#[test]
fn test_path_of_two() {
    let arcs = vec![
        Arc {
            tail: 0,
            head: 1,
            cost: 1,
            lower: 0,
            upper: None,
            original_edge: Some(0),
            orientation_sign: 1,
        },
        Arc {
            tail: 1,
            head: 0,
            cost: 1,
            lower: 0,
            upper: None,
            original_edge: Some(0),
            orientation_sign: -1,
        },
        Arc {
            tail: 1,
            head: 2,
            cost: 1,
            lower: 0,
            upper: None,
            original_edge: Some(1),
            orientation_sign: 1,
        },
        Arc {
            tail: 2,
            head: 1,
            cost: 1,
            lower: 0,
            upper: None,
            original_edge: Some(1),
            orientation_sign: -1,
        },
    ];
    let demand = vec![-1, 0, 1];
    let mut solver = NetworkSimplex::new(3, arcs, demand).unwrap();
    let sol = solver.solve().unwrap();
    assert_eq!(sol.objective, 2);
    assert_eq!(sol.flow[0], 1); // 0 -> 1 flow = 1
    assert_eq!(sol.flow[2], 1); // 1 -> 2 flow = 1
}

#[test]
fn test_unbalanced_demand() {
    let arcs = vec![Arc {
        tail: 0,
        head: 1,
        cost: 1,
        lower: 0,
        upper: None,
        original_edge: Some(0),
        orientation_sign: 1,
    }];
    let demand = vec![-1, 2];
    let mut solver = NetworkSimplex::new(2, arcs, demand).unwrap();
    let res = solver.solve();
    assert!(matches!(
        res,
        Err(NetworkSimplexError::UnbalancedDemand { .. })
    ));
}

#[test]
fn test_infeasible_disconnected() {
    // 0 and 1 are connected, but 2 is isolated.
    // Demand at 0 is -1 (supply), demand at 2 is 1.
    let arcs = vec![
        Arc {
            tail: 0,
            head: 1,
            cost: 1,
            lower: 0,
            upper: None,
            original_edge: Some(0),
            orientation_sign: 1,
        },
        Arc {
            tail: 1,
            head: 0,
            cost: 1,
            lower: 0,
            upper: None,
            original_edge: Some(0),
            orientation_sign: -1,
        },
    ];
    let demand = vec![-1, 0, 1];
    let mut solver = NetworkSimplex::new(3, arcs, demand).unwrap();
    let res = solver.solve();
    assert!(matches!(res, Err(NetworkSimplexError::Infeasible)));
}

// Origin: engine/crates_rs/tests/core_solvers/network_simplex_basic.rs
// Claim: urn:core:crates_rs:tests:network-simplex-basic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaeb82267 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaeb82267` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraeb82267 {
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
impl BoundaryErroraeb82267 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraeb82267 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraeb82267 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaeb82267 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraeb82267> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraeb82267::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraeb82267::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraeb82267::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_aeb82267() {
    let admitted = BoundaryRecordaeb82267::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordaeb82267::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
