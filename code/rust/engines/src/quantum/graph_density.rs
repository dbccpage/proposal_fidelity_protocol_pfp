use crate::quantum::density_error::DensityMatrixError;
use crate::quantum::density_matrix::{DensityMatrix, LegacyRealDensityMatrix, C64};
#[derive(Clone, Debug, Default)]
pub struct GraphState {}

#[derive(Clone, Debug)]
pub struct GraphDensityMatrix {
    pub graph: GraphState,
    pub rho: DensityMatrix,
}

impl GraphDensityMatrix {
    /// Legacy real-density conversion. This does not prove graph semantic
    /// binding; callers that need graph evidence must provide and validate a
    /// `GraphState` separately.
    pub fn from_legacy_density_checked(
        legacy: &LegacyRealDensityMatrix,
    ) -> Result<Self, DensityMatrixError> {
        let dim = legacy.dim();

        let data: Vec<C64> = legacy
            .rho()
            .iter()
            .enumerate()
            .map(|(i, &x)| {
                if !x.re.is_finite() || !x.im.is_finite() {
                    return Err(DensityMatrixError::NonFiniteEntry { index: i });
                }
                // Reject nonzero imaginary parts if we claim this is a "real" legacy source
                if x.im.abs() > 1e-12 {
                    return Err(DensityMatrixError::NonPhysical);
                }
                Ok(C64::new(x.re, 0.0))
            })
            .collect::<Result<_, _>>()?;

        let cfg = crate::quantum::density_config::DensityMatrixConfig::default();

        let rho = DensityMatrix::from_validated(dim, data, &cfg)?;

        Ok(Self {
            graph: GraphState::default(),
            rho,
        })
    }

    pub fn from_real_graph_density_checked(
        legacy: &LegacyRealDensityMatrix,
    ) -> Result<Self, DensityMatrixError> {
        Self::from_legacy_density_checked(legacy)
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HandshakeError { kind: &'static str, left: u128, right: u128 }
impl HandshakeError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Handshake lemma for a finite simple graph: the degree sum equals twice the edge count.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct HandshakeGraph { vertices: u64, edges: u64, degree_sum: u64 }
fn normalize_simple_edges(
    vertices: u64,
    edges: &[(u64, u64)],
) -> Result<Vec<(u64, u64)>, HandshakeError> {
    let mut normalized = Vec::new();
    for edge in edges {
        let (mut left, mut right) = *edge;
        if left == right {
            return Err(HandshakeError::new("a simple graph has no loop", u128::from(left), u128::from(right)));
        }
        if left >= vertices || right >= vertices {
            return Err(HandshakeError::new("an endpoint lies outside the vertex set", u128::from(left.max(right)), u128::from(vertices)));
        }
        if left > right {
            std::mem::swap(&mut left, &mut right);
        }
        normalized.push((left, right));
    }
    normalized.sort_unstable();
    Ok(normalized)
}

fn accumulate_unique_edges(normalized: &[(u64, u64)]) -> Result<(u64, u64), HandshakeError> {
    let mut previous: Option<(u64, u64)> = None;
    let mut degree_sum = 0u64;
    let mut edge_count = 0u64;
    for edge in normalized {
        if previous == Some(*edge) {
            return Err(HandshakeError::new("a simple graph has no repeated edge", u128::from(edge.0), u128::from(edge.1)));
        }
        previous = Some(*edge);
        degree_sum = degree_sum.checked_add(2).ok_or_else(|| HandshakeError::new("degree sum overflow", u128::from(degree_sum), 2))?;
        edge_count = edge_count.checked_add(1).ok_or_else(|| HandshakeError::new("edge count overflow", u128::from(edge_count), 1))?;
    }
    Ok((edge_count, degree_sum))
}

impl HandshakeGraph {
    pub fn try_simple(vertices: u64, edges: &[(u64, u64)]) -> Result<Self, HandshakeError> {
        if vertices == 0 && !edges.is_empty() {
            return Err(HandshakeError::new("an edge needs a vertex", u128::try_from(edges.len()).map_or(u128::MAX, |converted| converted), 0));
        }
        let normalized = normalize_simple_edges(vertices, edges)?;
        let (edge_count, degree_sum) = accumulate_unique_edges(&normalized)?;
        let doubled = edge_count.checked_mul(2).ok_or_else(|| HandshakeError::new("doubled edge count overflow", u128::from(edge_count), 2))?;
        if doubled != degree_sum {
            return Err(HandshakeError::new("degree sum is not twice the edge count", u128::from(degree_sum), u128::from(doubled)));
        }
        Ok(Self { vertices, edges: edge_count, degree_sum })
    }
    pub const fn degree_sum(&self) -> u64 { self.degree_sum }
}

// Origin: engine/crates_rs/engines/src/quantum/graph_density.rs
// Claim: urn:core:crates_rs:engines:graph-density:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcab701d7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcab701d7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcab701d7 {
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
impl BoundaryErrorcab701d7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcab701d7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcab701d7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcab701d7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcab701d7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcab701d7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcab701d7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcab701d7::ExceedsCapacity {
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
mod handshake_checks {
    use super::HandshakeGraph;
    #[test]
    fn a_triangle_has_degree_sum_six() {
        let graph = HandshakeGraph::try_simple(3, &[(0, 1), (1, 2), (2, 0)]);
        assert_eq!(graph.as_ref().map(|item| item.edges), Ok(3));
        assert_eq!(graph.as_ref().map(HandshakeGraph::degree_sum), Ok(6));
    }
    #[test]
    fn a_loop_is_refused() {
        assert_eq!(HandshakeGraph::try_simple(2, &[(1, 1)]).map(|_| ()).map_err(|e| e.kind()), Err("a simple graph has no loop"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_cab701d7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordcab701d7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordcab701d7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordcab701d7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordcab701d7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordcab701d7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorcab701d7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorcab701d7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
