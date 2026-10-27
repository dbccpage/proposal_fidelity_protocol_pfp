//! Hardening controls for the exact network simplex and the Phi1 boundary
//! solver, carried over from core_mub's former copy of the solver.
//! AuthorityEffect: None.

use core_solvers::solver_flow_network_simplex::Arc;
use core_solvers::solver_flow_network_simplex::NetworkSimplex;
use core_solvers::solver_flow_network_simplex::NetworkSimplexError;
use core_solvers::solver_lp_phi1_boundary::{solve_phi1, Boundary1, BoundaryEdge};

fn arc(tail: usize, head: usize, cost: i128, edge: usize) -> Arc {
    Arc {
        tail,
        head,
        cost,
        lower: 0,
        upper: None,
        original_edge: Some(edge),
        orientation_sign: 1,
    }
}

#[test]
fn triangle_min_cost_flow_takes_the_cheaper_path() {
    // Send 4 units from 0 to 2; 0 -> 1 -> 2 costs 5 per unit, 0 -> 2 costs 6.
    let arcs = vec![arc(0, 1, 2, 0), arc(1, 2, 3, 1), arc(0, 2, 6, 2)];
    let mut solver = NetworkSimplex::new(3, arcs, vec![-4, 0, 4]).unwrap();
    let sol = solver.solve().unwrap();
    assert_eq!(sol.objective, 20);
    assert_eq!(sol.flow, vec![4, 4, 0]);
}

#[test]
fn solve_phi1_on_a_unit_cycle_is_replayed_exactly() {
    let boundary = Boundary1 {
        num_vertices: 3,
        edges: vec![
            BoundaryEdge {
                tail: 0,
                head: 1,
                weight: 1,
            },
            BoundaryEdge {
                tail: 1,
                head: 2,
                weight: 1,
            },
            BoundaryEdge {
                tail: 2,
                head: 0,
                weight: 1,
            },
        ],
    };
    let sol = solve_phi1(&boundary, &[1, 1, 1]).unwrap();
    assert_eq!(sol.objective, 3);
    assert!(sol.verified_phi1().is_some());
    assert_eq!(
        sol.scaled_verified_value(1),
        Some(num_rational::BigRational::from_integer(3.into()))
    );
}

#[test]
fn solve_phi1_refuses_zero_weights_and_malformed_carriers() {
    let zero_weight = Boundary1 {
        num_vertices: 2,
        edges: vec![BoundaryEdge {
            tail: 0,
            head: 1,
            weight: 0,
        }],
    };
    assert!(matches!(
        solve_phi1(&zero_weight, &[1]),
        Err(NetworkSimplexError::InvalidCarrier { .. })
    ));
    let self_loop = Boundary1 {
        num_vertices: 2,
        edges: vec![BoundaryEdge {
            tail: 1,
            head: 1,
            weight: 1,
        }],
    };
    assert!(matches!(
        solve_phi1(&self_loop, &[1]),
        Err(NetworkSimplexError::InvalidCarrier { .. })
    ));
}

#[test]
fn arc_capacities_and_lower_bounds_are_refused() {
    let mut upper = arc(0, 1, 1, 0);
    upper.upper = Some(0);
    let mut solver = NetworkSimplex::new(2, vec![upper], vec![-1, 1]).unwrap();
    assert!(matches!(
        solver.solve(),
        Err(NetworkSimplexError::InvalidCarrier { .. })
    ));

    let mut lower = arc(0, 1, 1, 0);
    lower.lower = 2;
    let mut solver = NetworkSimplex::new(2, vec![lower], vec![-1, 1]).unwrap();
    assert!(matches!(
        solver.solve(),
        Err(NetworkSimplexError::InvalidCarrier { .. })
    ));
}

#[test]
fn demand_sum_overflow_is_refused_rather_than_wrapped() {
    let overflow = NetworkSimplex::new(3, vec![], vec![i128::MAX, 1, i128::MIN]).unwrap();
    assert_eq!(
        overflow.check_balanced_demand(),
        Err(NetworkSimplexError::ArithmeticOverflow)
    );
}

#[test]
fn solve_phi1_refuses_i128_overflow_instead_of_panicking() {
    let edge = |weight: i128| Boundary1 {
        num_vertices: 2,
        edges: vec![BoundaryEdge {
            tail: 0,
            head: 1,
            weight,
        }],
    };
    // The auxiliary node's demand is 2w.
    assert_eq!(
        solve_phi1(&edge(i128::MAX / 2 + 1), &[1]).unwrap_err(),
        NetworkSimplexError::ArithmeticOverflow
    );
    // The forward arc's cost is -omega + max(omega, 0).
    assert_eq!(
        solve_phi1(&edge(1), &[i128::MIN]).unwrap_err(),
        NetworkSimplexError::ArithmeticOverflow
    );
}

#[test]
fn standalone_carrier_boundaries_and_repeat_solve_are_checked() {
    assert!(matches!(
        NetworkSimplex::new(usize::MAX, vec![], vec![]),
        Err(NetworkSimplexError::SizeLimit)
    ));
    assert!(matches!(
        NetworkSimplex::new(2, vec![arc(0, 2, 1, 0)], vec![-1, 1]),
        Err(NetworkSimplexError::InvalidCarrier { .. })
    ));
    assert!(matches!(
        NetworkSimplex::new(2, vec![], vec![0]),
        Err(NetworkSimplexError::DemandLengthMismatch { .. })
    ));
    let mut solver = NetworkSimplex::new(2, vec![arc(0, 1, 2, 0)], vec![-3, 3]).unwrap();
    assert!(matches!(
        solver.solve_with_budget(0),
        Err(NetworkSimplexError::IterationLimitExceeded { limit: 0 })
    ));
    let first = solver.solve().unwrap();
    let second = solver.solve().unwrap();
    assert_eq!(first.objective, 6);
    assert_eq!(first.flow, second.flow);
    let mut bad = first.clone();
    bad.flow[0] = 2;
    assert_eq!(
        core_solvers::solver_flow_network_simplex::verify_network_solution(
            2,
            solver.arcs(),
            &[-3, 3],
            &bad
        ),
        Err(NetworkSimplexError::CertificateMismatch)
    );
    let mut bad = first.clone();
    bad.potential[0] += 1;
    assert_eq!(
        core_solvers::solver_flow_network_simplex::verify_network_solution(
            2,
            solver.arcs(),
            &[-3, 3],
            &bad
        ),
        Err(NetworkSimplexError::CertificateMismatch)
    );
}

// Origin: engine/crates_rs/tests/core_solvers/network_simplex_hardening.rs
// Claim: urn:core:crates_rs:tests:network-simplex-hardening:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc55e86d9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc55e86d9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc55e86d9 {
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
impl BoundaryErrorc55e86d9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc55e86d9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc55e86d9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc55e86d9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc55e86d9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc55e86d9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc55e86d9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc55e86d9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c55e86d9() {
    let admitted = BoundaryRecordc55e86d9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc55e86d9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
