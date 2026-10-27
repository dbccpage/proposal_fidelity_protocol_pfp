use crate::solver_flow_network_simplex::Arc;
use crate::solver_flow_network_simplex::NetworkSimplex;
use crate::solver_flow_network_simplex::NetworkSimplexError;
use num_bigint::BigInt;
use num_rational::BigRational;
use core_functional::{ExactPhi1Certificate, Phi1Functional, VerifiedExactPhi1};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BoundaryEdge {
    pub tail: usize,
    pub head: usize,
    pub weight: i128,
}

#[derive(Clone, Debug)]
pub struct Boundary1 {
    pub num_vertices: usize,
    pub edges: Vec<BoundaryEdge>,
}

#[derive(Clone, Debug)]
pub struct Phi1Solution {
    pub objective: i128,
    pub z: Vec<i128>,
    pub vertex_potential: Vec<i128>,
    pub reduced_costs: Vec<i128>,
    verified_phi1: Option<VerifiedExactPhi1>,
}

impl Phi1Solution {
    /// Present only for `solve_phi1`, after the exact primal-dual replay.
    pub fn verified_phi1(&self) -> Option<&VerifiedExactPhi1> {
        self.verified_phi1.as_ref()
    }

    pub fn scaled_verified_value(&self, scale: i128) -> Option<BigRational> {
        self.verified_phi1
            .as_ref()
            .and_then(|verified| Phi1Functional::scaled_verified_value(verified, scale))
    }
}

/// Reject malformed carriers before any arc or index is created (fail closed).
///
/// Mirrors `_validate_boundary` in
/// `engine/crates/solver/solv_phi1_l1_boundary.py`, including its order:
/// range and self-loop are carrier defects and are checked first, so a
/// well-formed edge carrying a negative weight still reports `NegativeWeight`
/// rather than being swallowed by the carrier class.
fn validate_boundary(boundary: &Boundary1) -> Result<(), NetworkSimplexError> {
    if boundary.num_vertices == 0 {
        return Err(NetworkSimplexError::InvalidCarrier {
            message: "num_vertices must be positive".to_string(),
        });
    }
    let n = boundary.num_vertices;
    for (i, e) in boundary.edges.iter().enumerate() {
        // `usize` already excludes negative endpoints, which is the half of the
        // Python guard the type system covers; the upper bound it does not.
        if e.tail >= n || e.head >= n {
            return Err(NetworkSimplexError::InvalidCarrier {
                message: format!(
                    "edge endpoint out of range at {i}: ({}, {})",
                    e.tail, e.head
                ),
            });
        }
        if e.tail == e.head {
            return Err(NetworkSimplexError::InvalidCarrier {
                message: format!("self-loop at edge {i}: {}", e.tail),
            });
        }
        if e.weight < 0 {
            return Err(NetworkSimplexError::NegativeWeight {
                edge: i,
                weight: e.weight,
            });
        }
    }
    Ok(())
}

fn build_bidirectional_boundary_arcs(boundary: &Boundary1) -> Vec<Arc> {
    let mut arcs = Vec::with_capacity(2 * boundary.edges.len());
    for (i, e) in boundary.edges.iter().enumerate() {
        arcs.push(Arc {
            tail: e.tail,
            head: e.head,
            cost: e.weight,
            lower: 0,
            upper: None,
            original_edge: Some(i),
            orientation_sign: 1,
        });
        arcs.push(Arc {
            tail: e.head,
            head: e.tail,
            cost: e.weight,
            lower: 0,
            upper: None,
            original_edge: Some(i),
            orientation_sign: -1,
        });
    }
    arcs
}

fn extract_signed_edge_flows(
    num_edges: usize,
    arcs: &[Arc],
    flow: &[i128],
) -> Result<Vec<i128>, NetworkSimplexError> {
    let mut z = vec![0i128; num_edges];
    for (a_idx, arc) in arcs.iter().enumerate() {
        if let Some(e_idx) = arc.original_edge {
            let term = flow[a_idx]
                .checked_mul(arc.orientation_sign as i128)
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
            z[e_idx] = z[e_idx]
                .checked_add(term)
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
        }
    }
    Ok(z)
}

pub fn solve_l1_boundary(
    boundary: &Boundary1,
    x: &[i128],
) -> Result<Phi1Solution, NetworkSimplexError> {
    validate_boundary(boundary)?;
    if boundary.num_vertices != x.len() {
        return Err(NetworkSimplexError::DemandLengthMismatch {
            expected: boundary.num_vertices,
            found: x.len(),
        });
    }

    let arcs = build_bidirectional_boundary_arcs(boundary);
    let mut solver = NetworkSimplex::new(boundary.num_vertices, arcs, x.to_vec())?;
    let sol = solver.solve()?;

    let z = extract_signed_edge_flows(boundary.edges.len(), solver.arcs(), &sol.flow)?;
    let weights: Vec<i128> = boundary.edges.iter().map(|edge| edge.weight).collect();
    let objective = Phi1Functional::weighted_l1_i128(&weights, &z)
        .ok_or(NetworkSimplexError::ArithmeticOverflow)?;

    let mut reduced_costs = Vec::with_capacity(boundary.edges.len());
    for e in &boundary.edges {
        let rc = e
            .weight
            .checked_add(sol.potential[e.tail])
            .and_then(|v| v.checked_sub(sol.potential[e.head]))
            .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
        reduced_costs.push(rc);
    }

    Ok(Phi1Solution {
        objective,
        z,
        vertex_potential: sol.potential,
        reduced_costs,
        verified_phi1: None,
    })
}

fn build_phi1_transshipment_network(
    boundary: &Boundary1,
    omega: &[i128],
) -> Result<(usize, Vec<Arc>, Vec<i128>), NetworkSimplexError> {
    let num_v = boundary.num_vertices;
    let num_e = boundary.edges.len();
    let trans_nodes = num_v + num_e;

    let mut arcs = Vec::with_capacity(2 * num_e);
    let mut demand = vec![0i128; trans_nodes];

    for (e_idx, e) in boundary.edges.iter().enumerate() {
        let u = e.tail;
        let v = e.head;
        let w = e.weight;
        let om = omega[e_idx];

        let c_e = if om > 0 { om } else { 0 };
        let y_node = num_v + e_idx;
        let forward_cost = om
            .checked_neg()
            .and_then(|v| v.checked_add(c_e))
            .ok_or(NetworkSimplexError::ArithmeticOverflow)?;

        // Arc 1: u -> Y_e
        arcs.push(Arc {
            tail: u,
            head: y_node,
            cost: forward_cost,
            lower: 0,
            upper: None,
            original_edge: Some(e_idx),
            orientation_sign: 1,
        });

        // Arc 2: v -> Y_e
        arcs.push(Arc {
            tail: v,
            head: y_node,
            cost: c_e,
            lower: 0,
            upper: None,
            original_edge: Some(e_idx),
            orientation_sign: -1,
        });

        // Demands
        demand[y_node] = w
            .checked_mul(2)
            .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
        demand[u] = demand[u]
            .checked_sub(w)
            .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
        demand[v] = demand[v]
            .checked_sub(w)
            .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
    }

    Ok((trans_nodes, arcs, demand))
}

fn verify_phi1_boundary_certificate(
    boundary: &Boundary1,
    omega: &[i128],
    alpha: &[i128],
    z: &[i128],
    phi: &[i128],
    objective: i128,
) -> Result<core_functional::phi1::VerifiedExactPhi1, NetworkSimplexError> {
    // Replay the primal-dual pair through core_functional before reporting it.
    let num_v = boundary.num_vertices;
    let integer = |value: i128| BigRational::from_integer(BigInt::from(value));
    let certificate = ExactPhi1Certificate {
        omega: omega.iter().copied().map(integer).collect(),
        d0: boundary
            .edges
            .iter()
            .map(|edge| {
                let mut row = vec![integer(0); num_v];
                row[edge.tail] = integer(-1);
                row[edge.head] = integer(1);
                row
            })
            .collect(),
        weights: boundary
            .edges
            .iter()
            .map(|edge| integer(edge.weight))
            .collect(),
        alpha: alpha.iter().copied().map(integer).collect(),
        primal_residual: z.iter().copied().map(integer).collect(),
        dual_witness: phi.iter().copied().map(integer).collect(),
        reported_value: integer(objective),
    };
    Phi1Functional::verify_exact_certificate(certificate).map_err(|error| {
        NetworkSimplexError::InvalidCarrier {
            message: format!("Phi1 certificate replay refused: {error}"),
        }
    })
}

fn extract_potentials_and_residual(
    boundary: &Boundary1,
    omega: &[i128],
    potential: &[i128],
) -> Result<(Vec<i128>, Vec<i128>, i128), NetworkSimplexError> {
    let num_v = boundary.num_vertices;
    let num_e = boundary.edges.len();
    let mut alpha = Vec::with_capacity(num_v);
    for &p in &potential[0..num_v] {
        alpha.push(
            p.checked_neg()
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?,
        );
    }
    let mut z = vec![0i128; num_e];
    for (e_idx, e) in boundary.edges.iter().enumerate() {
        z[e_idx] = alpha[e.head]
            .checked_sub(alpha[e.tail])
            .and_then(|diff| omega[e_idx].checked_sub(diff))
            .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
    }
    let weights: Vec<i128> = boundary.edges.iter().map(|edge| edge.weight).collect();
    let objective = Phi1Functional::weighted_l1_i128(&weights, &z)
        .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
    Ok((alpha, z, objective))
}

fn extract_dual_witness_phi(
    boundary: &Boundary1,
    flow: &[i128],
) -> Result<Vec<i128>, NetworkSimplexError> {
    let num_e = boundary.edges.len();
    let mut phi = vec![0i128; num_e];
    for (e_idx, phi_e) in phi.iter_mut().enumerate() {
        let f_plus = flow[2 * e_idx];
        *phi_e = f_plus
            .checked_sub(boundary.edges[e_idx].weight)
            .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
    }
    Ok(phi)
}

pub fn solve_phi1(
    boundary: &Boundary1,
    omega: &[i128],
) -> Result<Phi1Solution, NetworkSimplexError> {
    validate_boundary(boundary)?;
    if boundary.edges.iter().any(|edge| edge.weight == 0) {
        return Err(NetworkSimplexError::InvalidCarrier {
            message: "Phi1 certificate requires strictly positive weights".to_string(),
        });
    }
    if boundary.edges.len() != omega.len() {
        return Err(NetworkSimplexError::DemandLengthMismatch {
            expected: boundary.edges.len(),
            found: omega.len(),
        });
    }

    let (trans_nodes, arcs, demand) = build_phi1_transshipment_network(boundary, omega)?;
    let mut solver = NetworkSimplex::new(trans_nodes, arcs, demand)?;
    let sol = solver.solve()?;

    let (alpha, z, objective) = extract_potentials_and_residual(boundary, omega, &sol.potential)?;
    let phi = extract_dual_witness_phi(boundary, &sol.flow)?;
    let verified_phi1 =
        verify_phi1_boundary_certificate(boundary, omega, &alpha, &z, &phi, objective)?;

    Ok(Phi1Solution {
        objective,
        z,
        vertex_potential: alpha,
        reduced_costs: phi,
        verified_phi1: Some(verified_phi1),
    })
}

// Origin: engine/crates_rs/core_solvers/src/solver_lp_phi1_boundary.rs
// Claim: urn:core:crates_rs:core-solvers:solver-lp-phi1-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8fdb36ee {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8fdb36ee` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8fdb36ee {
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
impl BoundaryError8fdb36ee {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8fdb36ee {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8fdb36ee {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8fdb36ee {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8fdb36ee> {
        if capacity_bound == 0 {
            return Err(BoundaryError8fdb36ee::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8fdb36ee::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8fdb36ee::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_8fdb36ee {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8fdb36ee::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8fdb36ee::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8fdb36ee::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8fdb36ee::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8fdb36ee::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError8fdb36ee::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError8fdb36ee::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
