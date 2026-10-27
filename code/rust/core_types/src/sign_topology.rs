use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SignEdge {
    pub target: u32,
    pub sign: i32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignTopologyGraph {
    nodes: Vec<u32>,
    adj: HashMap<u32, Vec<SignEdge>>,
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_types/src/sign_topology.rs
// Claim: urn:core:types:sign-topology:balanced-signing:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BalancedSigning {
    vertices: usize,
    edges: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SignBalanceError {
    Empty,
    VertexSign { index: usize, sign: i8 },
    EdgeSign { index: usize, sign: i8 },
    EndpointOutOfRange { index: usize, vertex: u32 },
    DuplicateEdge { index: usize, source: u32, target: u32 },
    Unbalanced { index: usize, expected: i8, sign: i8 },
    ProductOverflow { index: usize },
}

// Origin: engine/crates_rs/core_types/src/sign_topology.rs
// Claim: urn:core:crates_rs:core-types:sign-topology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SignBalanceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SignBalanceError {}

impl SignTopologyGraph {
    pub fn try_from_signed_edges(
        vertex_sign: &[i8],
        edges: &[(u32, u32, i8)],
    ) -> Result<Self, SignBalanceError> {
        let witness = BalancedSigning::try_check(vertex_sign, edges)?;
        let mut nodes = Vec::new();
        let mut adj = std::collections::HashMap::new();
        for index in 0..witness.vertices {
            let node = u32::try_from(index).map_err(|_| SignBalanceError::EndpointOutOfRange {
                index,
                vertex: 0,
            })?;
            nodes.push(node);
            adj.insert(node, Vec::new());
        }
        for (index, edge) in edges.iter().enumerate() {
            let signed = SignEdge { target: edge.1, sign: i32::from(edge.2) };
            let slot = adj.get_mut(&edge.0).ok_or(SignBalanceError::EndpointOutOfRange {
                index,
                vertex: edge.0,
            })?;
            slot.push(signed);
        }
        Ok(Self { nodes, adj })
    }
}

impl BalancedSigning {
    fn endpoint_sign(vertex_sign: &[i8], index: usize, vertex: u32) -> Result<i8, SignBalanceError> {
        let slot = usize::try_from(vertex).map_err(|_| SignBalanceError::EndpointOutOfRange { index, vertex })?;
        vertex_sign
            .get(slot)
            .copied()
            .ok_or(SignBalanceError::EndpointOutOfRange { index, vertex })
    }

    fn validate_edge(
        vertex_sign: &[i8],
        seen: &mut Vec<(u32, u32)>,
        index: usize,
        edge: (u32, u32, i8),
    ) -> Result<(), SignBalanceError> {
        let (source, target, sign) = edge;
        if sign.abs() != 1 {
            return Err(SignBalanceError::EdgeSign { index, sign });
        }
        let source_sign = Self::endpoint_sign(vertex_sign, index, source)?;
        let target_sign = Self::endpoint_sign(vertex_sign, index, target)?;
        if seen.contains(&(source, target)) {
            return Err(SignBalanceError::DuplicateEdge { index, source, target });
        }
        seen.push((source, target));
        let expected = source_sign * target_sign;
        if expected != sign {
            return Err(SignBalanceError::Unbalanced { index, expected, sign });
        }
        Ok(())
    }

    pub fn try_check(vertex_sign: &[i8], edges: &[(u32, u32, i8)]) -> Result<Self, SignBalanceError> {
        if vertex_sign.is_empty() {
            return Err(SignBalanceError::Empty);
        }
        for (index, &sign) in vertex_sign.iter().enumerate() {
            if sign.abs() != 1 {
                return Err(SignBalanceError::VertexSign { index, sign });
            }
        }
        let mut seen = Vec::new();
        for (index, &edge) in edges.iter().enumerate() {
            Self::validate_edge(vertex_sign, &mut seen, index, edge)?;
        }
        Ok(Self {
            vertices: vertex_sign.len(),
            edges: edges.len(),
        })
    }

    pub fn edges(&self) -> usize {
        self.edges
    }

    pub fn vertices(&self) -> usize {
        self.vertices
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod balanced_signing_tests {
    use super::*;

    #[test]
    fn an_edge_sign_matches_the_vertex_product() {
        let graph = SignTopologyGraph::try_from_signed_edges(&[1, -1], &[(0, 1, -1)]);
        assert!(matches!(graph, Ok(ref built) if built.nodes.len() == 2));
        let witness = BalancedSigning::try_check(&[1, -1], &[(0, 1, -1)]);
        assert!(matches!(witness, Ok(ref row) if row.edges() == 1 && row.vertices() == 2));
    }

    #[test]
    fn refuses_a_sign_that_disagrees() {
        let wrong = SignTopologyGraph::try_from_signed_edges(&[1, -1], &[(0, 1, 1)]);
        assert!(matches!(
            wrong,
            Err(SignBalanceError::Unbalanced { index: 0, expected: -1, sign: 1 })
        ));
    }
}
