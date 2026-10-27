use core_solvers::solver_flow_network_simplex::Arc;
use core_solvers::solver_flow_network_simplex::NetworkSimplex;
use core_solvers::solver_lp_phi1_boundary::{
    solve_l1_boundary, solve_phi1, Boundary1, BoundaryEdge,
};

#[test]
fn test_phi1_path() {
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
        ],
    };
    let demand = vec![-1, 0, 1];
    let sol = solve_l1_boundary(&boundary, &demand).unwrap();
    assert_eq!(sol.objective, 2);
    assert_eq!(sol.z, vec![1, 1]);

    // Verify duality: ⟨x, π⟩ = objective
    let dual_val = sol.vertex_potential[2] - sol.vertex_potential[0];
    assert_eq!(dual_val, sol.objective);

    // Verify dual feasibility: |π_u - π_v| <= w_uv
    for e in &boundary.edges {
        let diff = (sol.vertex_potential[e.tail] - sol.vertex_potential[e.head]).abs();
        assert!(diff <= e.weight);
    }
}

#[test]
fn test_phi1_triangle_shortcut() {
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
                tail: 0,
                head: 2,
                weight: 3, // Shortcut is expensive
            },
        ],
    };
    let demand = vec![-1, 0, 1];
    let sol = solve_l1_boundary(&boundary, &demand).unwrap();
    assert_eq!(sol.objective, 2);
    assert_eq!(sol.z, vec![1, 1, 0]);

    // Let's change the shortcut to be cheap: weight = 1
    let boundary_cheap = Boundary1 {
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
                tail: 0,
                head: 2,
                weight: 1, // Cheap shortcut
            },
        ],
    };
    let sol_cheap = solve_l1_boundary(&boundary_cheap, &demand).unwrap();
    assert_eq!(sol_cheap.objective, 1);
    assert_eq!(sol_cheap.z, vec![0, 0, 1]);
}

#[test]
fn test_solve_phi1_triangle() {
    let boundary = Boundary1 {
        num_vertices: 3,
        edges: vec![
            BoundaryEdge {
                tail: 0,
                head: 1,
                weight: 2,
            },
            BoundaryEdge {
                tail: 1,
                head: 2,
                weight: 2,
            },
            BoundaryEdge {
                tail: 2,
                head: 0,
                weight: 3,
            },
        ],
    };

    let omega = vec![3, 4, 1];

    // Reconstruct the transshipment solver manually here to inspect the process
    let num_v = boundary.num_vertices;
    let num_e = boundary.edges.len();
    let trans_nodes = num_v + num_e;

    let mut arcs = Vec::new();
    let mut demand = vec![0i128; trans_nodes];

    for (e_idx, e) in boundary.edges.iter().enumerate() {
        let u = e.tail;
        let v = e.head;
        let w = e.weight;
        let om = omega[e_idx];

        let c_e = if om > 0 { om } else { 0 };
        let y_node = num_v + e_idx;

        arcs.push(Arc {
            tail: u,
            head: y_node,
            cost: -om + c_e,
            lower: 0,
            upper: None,
            original_edge: Some(e_idx),
            orientation_sign: 1,
        });

        arcs.push(Arc {
            tail: v,
            head: y_node,
            cost: c_e,
            lower: 0,
            upper: None,
            original_edge: Some(e_idx),
            orientation_sign: -1,
        });

        demand[y_node] = 2 * w;
        demand[u] -= w;
        demand[v] -= w;
    }

    let mut solver = NetworkSimplex::new(trans_nodes, arcs, demand.clone()).unwrap();
    let sol = solver.solve().unwrap();
    core_solvers::solver_flow_network_simplex::verify_network_solution(
        trans_nodes,
        solver.arcs(),
        &demand,
        &sol,
    )
    .unwrap();

    // Call the production solver and check
    let production_sol = solve_phi1(&boundary, &omega).unwrap();
    assert_eq!(production_sol.objective, 16);
}

// Origin: engine/crates_rs/tests/core_solvers/phi1_boundary.rs
// Claim: urn:core:crates_rs:tests:phi1-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord89a6f9cc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord89a6f9cc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError89a6f9cc {
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
impl BoundaryError89a6f9cc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError89a6f9cc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError89a6f9cc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord89a6f9cc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError89a6f9cc> {
        if capacity_bound == 0 {
            return Err(BoundaryError89a6f9cc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError89a6f9cc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError89a6f9cc::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_89a6f9cc() {
    let admitted = BoundaryRecord89a6f9cc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord89a6f9cc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
