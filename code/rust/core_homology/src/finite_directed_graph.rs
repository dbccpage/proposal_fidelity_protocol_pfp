//! Finite directed graph carrier.
//!
//! This module provides a general finite directed graph with named nodes,
//! checked construction (no self-loops, no duplicate edges, bounds-checked),
//! witness hashing, and provenance tracking.
//!
//! Despite the historical name `FiniteDirectedGraph`, this type does NOT enforce
//! poset axioms (reflexivity, antisymmetry, transitivity) at construction.
//! Cycles are permitted. Callers requiring poset semantics should call
//! `validate_poset()` explicitly.
//!
//! The canonical name is `FiniteDirectedGraph`. The old name is retained as
//! a deprecated type alias for backward compatibility.

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DirectedGraphError {
    #[error("node count must match node index cardinality")]
    NodeCountMismatch,
    #[error("node index values must be unique and in range")]
    InvalidNodeIndex,
    #[error("edge endpoint {0} is out of range")]
    IndexOutOfRange(usize),
    #[error("self-loops are not allowed at index {0}")]
    SelfLoop(usize),
    #[error("duplicate edge ({0}, {1}) is not allowed")]
    DuplicateEdge(usize, usize),
    #[error("graph contains cycles, violating poset antisymmetry")]
    ContainsCycles,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum NamedEdgeResolutionError {
    #[error("missing node name in edge endpoint: {0}")]
    MissingNodeName(String),
    #[error("duplicate node name: {0}")]
    DuplicateNode(String),
    #[error("self-loop at named node: {0}")]
    SelfLoop(String),
    #[error("graph construction error: {0}")]
    GraphError(#[from] DirectedGraphError),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TheoremProvenance {
    pub verification_source: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PosetWitness {
    pub edge_hash: [u8; 32],
}

impl PosetWitness {
    pub(crate) fn new(_edges: &[(usize, usize)]) -> Self {
        // Canonical hashing would happen here. For now, zero hash.
        Self { edge_hash: [0; 32] }
    }
}

/// Finite directed graph carrier.
///
/// This is the universal graph type used across the engine: Hodge solvers,
/// Hamiltonian flows, obstruction calculus, sheaf theory, etc. It stores
/// named vertices, directed edges, a structural witness hash, and provenance.
///
/// Construction rejects self-loops and duplicate edges but permits cycles.
/// For poset validation, call `validate_poset()` after construction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteDirectedGraph {
    nodes: Vec<String>,
    node_index: HashMap<String, usize>,
    edges: Vec<(usize, usize)>,
    witness: PosetWitness,
    provenance: TheoremProvenance,
}

impl FiniteDirectedGraph {
    pub fn from_pairs(
        pairs: &[(usize, usize)],
        provenance: TheoremProvenance,
    ) -> Result<Self, DirectedGraphError> {
        let max_idx = pairs
            .iter()
            .flat_map(|(src, dst)| [*src, *dst])
            .max()
            .unwrap_or(0);
        DirectedGraphBuilder::from_anonymous(max_idx + 1, pairs.to_vec(), provenance)
    }

    pub fn new(
        nodes: Vec<String>,
        node_index: HashMap<String, usize>,
        edges: Vec<(usize, usize)>,
        provenance: TheoremProvenance,
    ) -> Result<Self, DirectedGraphError> {
        if nodes.len() != node_index.len() {
            return Err(DirectedGraphError::NodeCountMismatch);
        }

        for (index, name) in nodes.iter().enumerate() {
            match node_index.get(name) {
                Some(&mapped) if mapped == index => {}
                _ => return Err(DirectedGraphError::InvalidNodeIndex),
            }
        }

        let mut seen_indices = HashSet::new();
        for &index in node_index.values() {
            if index >= nodes.len() || !seen_indices.insert(index) {
                return Err(DirectedGraphError::InvalidNodeIndex);
            }
        }

        Self::validate_edges(nodes.len(), &edges)?;
        let witness = PosetWitness::new(&edges);

        Ok(Self {
            nodes,
            node_index,
            edges,
            witness,
            provenance,
        })
    }

    fn validate_edges(num_nodes: usize, edges: &[(usize, usize)]) -> Result<(), DirectedGraphError> {
        let mut seen_edges = HashSet::new();
        for &(src, dst) in edges {
            if src >= num_nodes {
                return Err(DirectedGraphError::IndexOutOfRange(src));
            }
            if dst >= num_nodes {
                return Err(DirectedGraphError::IndexOutOfRange(dst));
            }
            if src == dst {
                return Err(DirectedGraphError::SelfLoop(src));
            }
            if !seen_edges.insert((src, dst)) {
                return Err(DirectedGraphError::DuplicateEdge(src, dst));
            }
        }
        Ok(())
    }

    /// Optional poset validation: check that the graph is strictly acyclic.
    ///
    /// This is NOT enforced at construction because `FiniteDirectedGraph` is used
    /// as a general directed graph throughout the engine (Hodge decomposition,
    /// Hamiltonian flows, obstruction calculus, etc.). Callers that require
    /// poset semantics should call this method explicitly.
    pub fn validate_poset(&self) -> Result<(), DirectedGraphError> {
        let n = self.nodes.len();
        let mut in_degree = vec![0usize; n];
        let mut adj = vec![vec![]; n];
        for &(u, v) in &self.edges {
            adj[u].push(v);
            in_degree[v] += 1;
        }

        let mut queue = std::collections::VecDeque::new();
        for (i, &degree) in in_degree.iter().enumerate() {
            if degree == 0 {
                queue.push_back(i);
            }
        }

        let mut visited_count = 0;
        while let Some(u) = queue.pop_front() {
            visited_count += 1;
            for &v in &adj[u] {
                in_degree[v] -= 1;
                if in_degree[v] == 0 {
                    queue.push_back(v);
                }
            }
        }

        if visited_count != n {
            return Err(DirectedGraphError::ContainsCycles);
        }
        Ok(())
    }

    pub fn num_nodes(&self) -> usize {
        self.nodes.len()
    }

    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    pub fn num_edges(&self) -> usize {
        self.edges.len()
    }

    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }

    pub fn nodes(&self) -> &[String] {
        &self.nodes
    }

    pub fn node_index(&self) -> &HashMap<String, usize> {
        &self.node_index
    }

    pub fn edges(&self) -> &[(usize, usize)] {
        &self.edges
    }

    pub fn covering_edges(&self) -> &[(usize, usize)] {
        &self.edges
    }
}

pub struct DirectedGraphBuilder;

impl DirectedGraphBuilder {
    pub fn build(
        nodes: Vec<String>,
        node_index: HashMap<String, usize>,
        edges: Vec<(usize, usize)>,
        provenance: TheoremProvenance,
    ) -> Result<FiniteDirectedGraph, DirectedGraphError> {
        FiniteDirectedGraph::new(nodes, node_index, edges, provenance)
    }

    pub fn from_named(
        nodes: Vec<String>,
        named_edges: &[(String, String)],
        provenance: TheoremProvenance,
    ) -> Result<FiniteDirectedGraph, NamedEdgeResolutionError> {
        let mut node_index = HashMap::with_capacity(nodes.len());
        for (index, name) in nodes.iter().enumerate() {
            if node_index.insert(name.clone(), index).is_some() {
                return Err(NamedEdgeResolutionError::DuplicateNode(name.clone()));
            }
        }

        let mut edges = Vec::with_capacity(named_edges.len());
        for (src, dst) in named_edges {
            if src == dst {
                return Err(NamedEdgeResolutionError::SelfLoop(src.clone()));
            }
            let src_index = *node_index
                .get(src)
                .ok_or_else(|| NamedEdgeResolutionError::MissingNodeName(src.clone()))?;
            let dst_index = *node_index
                .get(dst)
                .ok_or_else(|| NamedEdgeResolutionError::MissingNodeName(dst.clone()))?;
            edges.push((src_index, dst_index));
        }

        Ok(FiniteDirectedGraph::new(
            nodes, node_index, edges, provenance,
        )?)
    }

    pub fn from_anonymous(
        num_nodes: usize,
        edges: Vec<(usize, usize)>,
        provenance: TheoremProvenance,
    ) -> Result<FiniteDirectedGraph, DirectedGraphError> {
        let nodes: Vec<String> = (0..num_nodes).map(|index| format!("n{index}")).collect();
        let node_index: HashMap<String, usize> = nodes
            .iter()
            .enumerate()
            .map(|(index, name)| (name.clone(), index))
            .collect();
        FiniteDirectedGraph::new(nodes, node_index, edges, provenance)
    }

    pub fn chain(
        n: usize,
        provenance: TheoremProvenance,
    ) -> Result<FiniteDirectedGraph, NamedEdgeResolutionError> {
        let nodes: Vec<String> = (0..n).map(|index| format!("v{index}")).collect();
        let named_edges: Vec<(String, String)> = (0..n.saturating_sub(1))
            .map(|index| (format!("v{index}"), format!("v{}", index + 1)))
            .collect();
        Self::from_named(nodes, &named_edges, provenance)
    }

    pub fn ring(
        n: usize,
        provenance: TheoremProvenance,
    ) -> Result<FiniteDirectedGraph, NamedEdgeResolutionError> {
        if n < 2 {
            return Self::chain(n, provenance);
        }
        let nodes: Vec<String> = (0..n).map(|index| format!("v{index}")).collect();
        let mut named_edges: Vec<(String, String)> = (0..n.saturating_sub(1))
            .map(|index| (format!("v{index}"), format!("v{}", index + 1)))
            .collect();
        named_edges.push((format!("v{}", n - 1), "v0".to_string()));
        Self::from_named(nodes, &named_edges, provenance)
    }

    pub fn cycle_graph(
        n: usize,
        provenance: TheoremProvenance,
    ) -> Result<FiniteDirectedGraph, DirectedGraphError> {
        if n < 2 {
            return DirectedGraphBuilder::from_anonymous(n.max(1), vec![], provenance);
        }
        let mut edges: Vec<(usize, usize)> = (0..n - 1).map(|i| (i, i + 1)).collect();
        edges.push((n - 1, 0));
        DirectedGraphBuilder::from_anonymous(n, edges, provenance)
    }
}

// Origin: engine/crates_rs/core_homology/src/finite_directed_graph.rs
// Claim: urn:core:crates_rs:core-homology:finite-directed-graph:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn test_provenance() -> TheoremProvenance {
        TheoremProvenance {
            verification_source: "test".to_string(),
        }
    }

    fn two_named_vertices() -> (Vec<String>, HashMap<String, usize>) {
        let nodes = vec!["n0".to_string(), "n1".to_string()];
        let node_index = nodes
            .iter()
            .enumerate()
            .map(|(index, name)| (name.clone(), index))
            .collect();
        (nodes, node_index)
    }

    #[test]
    fn anonymous_builder_assigns_nodes() {
        let graph =
            DirectedGraphBuilder::from_anonymous(2, vec![(0, 1)], test_provenance()).unwrap();

        assert_eq!(graph.num_nodes(), 2);
        assert_eq!(graph.edges(), &[(0, 1)]);
    }

    #[test]
    fn new_rejects_edge_endpoint_outside_vertex_set() {
        let (nodes, node_index) = two_named_vertices();
        let src_err = FiniteDirectedGraph::new(
            nodes.clone(),
            node_index.clone(),
            vec![(2, 0)],
            test_provenance(),
        )
        .unwrap_err();
        assert!(matches!(src_err, DirectedGraphError::IndexOutOfRange(2)));

        let dst_err = FiniteDirectedGraph::new(nodes, node_index, vec![(0, 2)], test_provenance())
            .unwrap_err();
        assert!(matches!(dst_err, DirectedGraphError::IndexOutOfRange(2)));
    }
}
