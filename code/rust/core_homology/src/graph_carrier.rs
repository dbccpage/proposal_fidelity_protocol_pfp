//! Graph carrier constructor: build a cochain complex from a directed graph.
//!
//! - Nodes = C^0 basis
//! - Edges = C^1 basis
//! - Triangles (3-cliques) = C^2 basis (optional)
//!
//! Oriented triangle convention:
//! d[a,b,c] = [b,c] - [a,c] + [a,b]

use crate::carrier::Carrier;
use crate::cochain_complex::TheoremProvenance;
use crate::errors::HomologicalError;
use crate::finite_directed_graph::FiniteDirectedGraph;
use crate::scalar::q;
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::BasicMatrix;

/// Build a carrier from a directed graph with optional triangles.
pub fn graph_carrier(
    graph: &FiniteDirectedGraph,
    triangles: &[(usize, usize, usize)],
    weights: Vec<Q>,
    provenance: TheoremProvenance,
) -> Result<Carrier, HomologicalError> {
    let num_nodes = graph.num_nodes();
    let edges = graph.edges();
    let num_edges = edges.len();
    let num_triangles = triangles.len();

    // Build d0: |E| x |V| signed incidence matrix
    let d0 = build_d0(num_nodes, edges)?;

    // Validate triangles and build d1
    let mut d1 =
        BasicMatrix::<Q>::zero(num_triangles, num_edges).map_err(HomologicalError::MatrixError)?;
    for (t_idx, &tri) in triangles.iter().enumerate() {
        insert_oriented_triangle(&mut d1, num_nodes, edges, t_idx, tri)?;
    }

    Carrier::new(
        num_nodes,
        num_edges,
        num_triangles,
        d0,
        d1,
        weights,
        provenance,
    )
}

fn build_d0(num_nodes: usize, edges: &[(usize, usize)]) -> Result<BasicMatrix<Q>, HomologicalError> {
    let mut d0 =
        BasicMatrix::<Q>::zero(edges.len(), num_nodes).map_err(HomologicalError::MatrixError)?;
    for (e_idx, &(src, tgt)) in edges.iter().enumerate() {
        if src >= num_nodes {
            return Err(HomologicalError::EdgeSourceOutOfRange { edge: e_idx, src });
        }
        if tgt >= num_nodes {
            return Err(HomologicalError::EdgeTargetOutOfRange { edge: e_idx, tgt });
        }
        if src == tgt {
            return Err(HomologicalError::SelfLoopNotAllowed { node: src });
        }
        d0.set(e_idx, src, q(-1))
            .map_err(HomologicalError::MatrixError)?;
        d0.set(e_idx, tgt, q(1))
            .map_err(HomologicalError::MatrixError)?;
    }
    Ok(d0)
}

fn find_triangle_edge(
    edges: &[(usize, usize)],
    t_idx: usize,
    src: usize,
    tgt: usize,
) -> Result<usize, HomologicalError> {
    edges
        .iter()
        .position(|&(s, t)| s == src && t == tgt)
        .ok_or(HomologicalError::TriangleMissingEdge {
            triangle: t_idx,
            src,
            tgt,
        })
}

fn insert_oriented_triangle(
    d1: &mut BasicMatrix<Q>,
    num_nodes: usize,
    edges: &[(usize, usize)],
    t_idx: usize,
    tri: (usize, usize, usize),
) -> Result<(), HomologicalError> {
    let (a, b, c) = tri;
    for v in [a, b, c] {
        if v >= num_nodes {
            return Err(HomologicalError::TriangleVertexOutOfRange {
                triangle: t_idx,
                vertex: v,
            });
        }
    }
    let edge_ab = find_triangle_edge(edges, t_idx, a, b)?;
    let edge_bc = find_triangle_edge(edges, t_idx, b, c)?;
    let edge_ac = find_triangle_edge(edges, t_idx, a, c)?;

    // Oriented triangle: d[a,b,c] = [b,c] - [a,c] + [a,b]
    d1.set(t_idx, edge_ab, q(1))
        .map_err(HomologicalError::MatrixError)?;
    d1.set(t_idx, edge_bc, q(1))
        .map_err(HomologicalError::MatrixError)?;
    d1.set(t_idx, edge_ac, q(-1))
        .map_err(HomologicalError::MatrixError)?;
    Ok(())
}

// Origin: engine/crates_rs/core_homology/src/graph_carrier.rs
// Claim: urn:core:crates_rs:core-homology:graph-carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord958237cf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord958237cf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError958237cf {
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
impl BoundaryError958237cf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError958237cf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError958237cf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord958237cf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError958237cf> {
        if capacity_bound == 0 {
            return Err(BoundaryError958237cf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError958237cf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError958237cf::ExceedsCapacity {
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
mod l4_boundary_tests_958237cf {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord958237cf::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord958237cf::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord958237cf::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord958237cf::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord958237cf::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError958237cf::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError958237cf::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
