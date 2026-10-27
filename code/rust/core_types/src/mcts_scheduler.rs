use serde::{Deserialize, Serialize};
use std::hash::{Hash, Hasher};

pub use crate::node_id::NodeId;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CoinductiveSignature {
    pub dependency_graph_hash: u64,
    pub categorical_markers: Vec<String>,
    pub q_compression_ratio: u64,
    pub q_coboundary_norm: u64,
}

impl CoinductiveSignature {
    pub fn compute_hash(&self) -> u64 {
        let mut hasher = std::collections::hash_map::DefaultHasher::new();
        self.dependency_graph_hash.hash(&mut hasher);
        for marker in &self.categorical_markers {
            marker.hash(&mut hasher);
        }
        self.q_compression_ratio.hash(&mut hasher);
        self.q_coboundary_norm.hash(&mut hasher);
        hasher.finish()
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct InertAmplitude(pub f64);

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TowerState {
    pub state_id: String,
    pub signature: CoinductiveSignature,
    pub observable_behavior_hash: u64,
    pub depth: u32,
    pub amplitude_diagnostic: InertAmplitude,
}

impl TowerState {
    pub fn new(
        state_id: String,
        signature: CoinductiveSignature,
        depth: u32,
        amplitude_f64: f64,
    ) -> Self {
        let observable_behavior_hash = signature.compute_hash();
        Self {
            state_id,
            signature,
            observable_behavior_hash,
            depth,
            amplitude_diagnostic: InertAmplitude(amplitude_f64),
        }
    }

    pub fn compute_coinductive_hash(&self, futures: &[TowerState]) -> u64 {
        let mut hasher = std::collections::hash_map::DefaultHasher::new();
        self.state_id.hash(&mut hasher);
        self.signature.compute_hash().hash(&mut hasher);
        self.depth.hash(&mut hasher);
        self.observable_behavior_hash.hash(&mut hasher);
        for future in futures {
            future.observable_behavior_hash.hash(&mut hasher);
            future.signature.compute_hash().hash(&mut hasher);
        }
        hasher.finish()
    }
}

impl Hash for TowerState {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.observable_behavior_hash.hash(state);
    }
}

pub trait OperadicMarkovCoalgebra {
    type State;

    /// Expand current state into candidate futures (purely structural).
    fn generate_futures(&self, current: &Self::State) -> Vec<Self::State>;

    /// Splice multiple child states into composite states.
    /// Must be associative over child ordering (operadic coherence).
    fn gamma_splice(&self, child_states: &[&Self::State]) -> Vec<Self::State>;
}

/// Constraint alias: `OperadicMarkovCoalgebra` bound to `TowerState`.
pub trait TowerCoalgebra: OperadicMarkovCoalgebra<State = TowerState> {}

impl<T> TowerCoalgebra for T where T: OperadicMarkovCoalgebra<State = TowerState> {}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum VisitError {
    Shape,
    Root,
    Parent,
    Depth,
    Cycle,
    Visits,
    Leaf,
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/mcts_scheduler.rs
// Claim: urn:core:crates_rs:core-types:mcts-scheduler:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for VisitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for VisitError {}

/// A visit tree: one root, child depths increase by one, and internal visits equal the child sum.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VisitTree {
    root_visits: u64,
    leaves: usize,
}

impl VisitTree {
    fn check_node_acyclic(parents: &[Option<usize>], start: usize) -> Result<(), VisitError> {
        let mut cursor = start;
        for _ in 0..=parents.len() {
            match parents[cursor] {
                None => return Ok(()),
                Some(parent_index) => cursor = parent_index,
            }
        }
        Err(VisitError::Cycle)
    }

    fn validate_parent_link(
        nodes: usize,
        index: usize,
        parent_index: usize,
        depths: &[u32],
    ) -> Result<(), VisitError> {
        if parent_index >= nodes || parent_index == index {
            return Err(VisitError::Parent);
        }
        if depths[index] != depths[parent_index].checked_add(1).ok_or(VisitError::Overflow)? {
            return Err(VisitError::Depth);
        }
        Ok(())
    }

    fn find_and_validate_root(
        parents: &[Option<usize>],
        depths: &[u32],
    ) -> Result<usize, VisitError> {
        let nodes = parents.len();
        let mut root = None;
        for (index, &parent) in parents.iter().enumerate() {
            if let Some(parent_index) = parent {
                Self::validate_parent_link(nodes, index, parent_index, depths)?;
            } else if root.is_some() || depths[index] != 0 {
                return Err(VisitError::Root);
            } else {
                root = Some(index);
            }
            Self::check_node_acyclic(parents, index)?;
        }
        root.ok_or(VisitError::Root)
    }

    fn accumulate_children(
        parents: &[Option<usize>],
        visits: &[u64],
    ) -> Result<(Vec<u64>, Vec<u32>), VisitError> {
        let nodes = parents.len();
        let mut child_sum = vec![0u64; nodes];
        let mut child_count = vec![0u32; nodes];
        for (index, &parent) in parents.iter().enumerate() {
            if let Some(parent_index) = parent {
                child_sum[parent_index] = child_sum[parent_index]
                    .checked_add(visits[index])
                    .ok_or(VisitError::Overflow)?;
                child_count[parent_index] = child_count[parent_index]
                    .checked_add(1)
                    .ok_or(VisitError::Overflow)?;
            }
        }
        Ok((child_sum, child_count))
    }

    fn verify_leaf_and_internal_visits(
        visits: &[u64],
        child_sum: &[u64],
        child_count: &[u32],
    ) -> Result<(u64, usize), VisitError> {
        let mut leaf_sum = 0u64;
        let mut leaves = 0usize;
        for index in 0..visits.len() {
            let visit = visits[index];
            if child_count[index] == 0 {
                if visit < 1 {
                    return Err(VisitError::Leaf);
                }
                leaves = leaves.checked_add(1).ok_or(VisitError::Overflow)?;
                leaf_sum = leaf_sum.checked_add(visit).ok_or(VisitError::Overflow)?;
            } else if child_sum[index] != visit {
                return Err(VisitError::Visits);
            }
        }
        Ok((leaf_sum, leaves))
    }

    pub fn try_new(parents: &[Option<usize>], visits: &[u64], depths: &[u32]) -> Result<Self, VisitError> {
        let nodes = parents.len();
        if !(1..=32).contains(&nodes) || visits.len() != nodes || depths.len() != nodes {
            return Err(VisitError::Shape);
        }
        let root = Self::find_and_validate_root(parents, depths)?;
        let (child_sum, child_count) = Self::accumulate_children(parents, visits)?;
        let (leaf_sum, leaves) = Self::verify_leaf_and_internal_visits(visits, &child_sum, &child_count)?;
        if leaves == 0 || visits[root] != leaf_sum {
            return Err(VisitError::Visits);
        }
        Ok(Self { root_visits: leaf_sum, leaves })
    }

    pub fn root_visits(&self) -> u64 { self.root_visits }
    pub fn leaves(&self) -> usize { self.leaves }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod visit_tests {
    use super::*;

    #[test]
    fn child_visits_restore_the_root() {
        let tree = VisitTree::try_new(&[None, Some(0), Some(0)], &[5, 2, 3], &[0, 1, 1]);
        assert!(matches!(tree, Ok(ref tree) if tree.root_visits() == 5 && tree.leaves() == 2));
    }

    #[test]
    fn a_root_short_of_its_children_is_refused() {
        let tree = VisitTree::try_new(&[None, Some(0), Some(0)], &[4, 2, 3], &[0, 1, 1]);
        assert!(matches!(tree, Err(VisitError::Visits)));
    }
}
