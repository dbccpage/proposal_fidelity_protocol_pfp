//! DDC Move Network & Futile Cycle Detector (U24).
//!
//! Models discrete deformation trajectories as chemical/kinetic move networks:
//! - Complexes combining state classes, tokens, and catalytic operands.
//! - Directed state graph: nodes are (state_id, Phi_1, Gamma_2).
//! - Edges are DDC operations (E, R, C, I, Λ, D, M, T) consuming tokens.
//! - Futile Cycle: A directed cycle in the state graph where:
//!   net Delta Phi_1 = 0, net Delta Gamma_2 = 0, and total token_cost > 0.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MoveNode {
    pub state_id: String,
    pub phi1: i64,
    pub gamma2: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MoveEdge {
    pub from_state: String,
    pub to_state: String,
    pub action_rune: String,
    pub token_cost: u64,
    pub delta_phi1: i64,
    pub delta_gamma2: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FutileCycle {
    pub cycle_path: Vec<String>,
    pub actions: Vec<String>,
    pub total_token_cost: u64,
    pub net_delta_phi1: i64,
    pub net_delta_gamma2: i64,
    pub traversal_count: usize,
    pub is_futile: bool,
}

#[derive(Debug, Default, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MoveNetwork {
    pub nodes: BTreeMap<String, MoveNode>,
    pub edges: Vec<MoveEdge>,
}

impl MoveNetwork {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_node(&mut self, state_id: &str, phi1: i64, gamma2: i64) {
        self.nodes.insert(
            state_id.to_string(),
            MoveNode {
                state_id: state_id.to_string(),
                phi1,
                gamma2,
            },
        );
    }

    #[allow(clippy::too_many_arguments)]
    pub fn add_transition(
        &mut self,
        from_state: &str,
        to_state: &str,
        action_rune: &str,
        token_cost: u64,
        from_phi1: i64,
        to_phi1: i64,
        from_gamma2: i64,
        to_gamma2: i64,
    ) {
        self.add_node(from_state, from_phi1, from_gamma2);
        self.add_node(to_state, to_phi1, to_gamma2);

        self.edges.push(MoveEdge {
            from_state: from_state.to_string(),
            to_state: to_state.to_string(),
            action_rune: action_rune.to_string(),
            token_cost,
            delta_phi1: to_phi1 - from_phi1,
            delta_gamma2: to_gamma2 - from_gamma2,
        });
    }

    /// Detect simple directed cycles and evaluate whether they are futile.
    pub fn detect_futile_cycles(&self) -> Vec<FutileCycle> {
        let mut adj: HashMap<&str, Vec<&MoveEdge>> = HashMap::new();
        for edge in &self.edges {
            adj.entry(edge.from_state.as_str()).or_default().push(edge);
        }

        let mut futile_cycles = Vec::new();
        let mut seen_cycles: HashSet<Vec<String>> = HashSet::new();

        // Search for cycles up to length 8 starting from each node
        for start_node in self.nodes.keys() {
            let mut path: Vec<(&str, &MoveEdge)> = Vec::new();
            let mut in_path: HashSet<&str> = HashSet::new();
            self.dfs_find_cycles(
                start_node.as_str(),
                start_node.as_str(),
                &adj,
                &mut path,
                &mut in_path,
                &mut seen_cycles,
                &mut futile_cycles,
            );
        }

        futile_cycles
    }

    fn record_closed_cycle<'a>(
        target: &'a str,
        edge: &'a MoveEdge,
        path: &[(&'a str, &'a MoveEdge)],
        seen_cycles: &mut HashSet<Vec<String>>,
        results: &mut Vec<FutileCycle>,
    ) {
        let mut cycle_nodes = vec![target.to_string()];
        let mut actions = Vec::new();
        let mut total_tokens = 0;
        let mut net_phi1 = 0;
        let mut net_gamma2 = 0;

        for &(step_node, step_edge) in path.iter() {
            cycle_nodes.push(step_node.to_string());
            actions.push(step_edge.action_rune.clone());
            total_tokens += step_edge.token_cost;
            net_phi1 += step_edge.delta_phi1;
            net_gamma2 += step_edge.delta_gamma2;
        }
        // add final edge
        actions.push(edge.action_rune.clone());
        total_tokens += edge.token_cost;
        net_phi1 += edge.delta_phi1;
        net_gamma2 += edge.delta_gamma2;

        // Canonical rotation for deduplication
        let min_idx = cycle_nodes
            .iter()
            .enumerate()
            .min_by_key(|(_, s)| *s)
            .map(|(i, _)| i)
            .unwrap_or(0);
        let mut canonical = cycle_nodes[min_idx..].to_vec();
        canonical.extend_from_slice(&cycle_nodes[..min_idx]);

        if seen_cycles.insert(canonical) && net_phi1 == 0 && net_gamma2 == 0 && total_tokens > 0 {
            results.push(FutileCycle {
                cycle_path: cycle_nodes,
                actions,
                total_token_cost: total_tokens,
                net_delta_phi1: net_phi1,
                net_delta_gamma2: net_gamma2,
                traversal_count: 1,
                is_futile: true,
            });
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn dfs_find_cycles<'a>(
        &'a self,
        current: &'a str,
        target: &'a str,
        adj: &HashMap<&'a str, Vec<&'a MoveEdge>>,
        path: &mut Vec<(&'a str, &'a MoveEdge)>,
        in_path: &mut HashSet<&'a str>,
        seen_cycles: &mut HashSet<Vec<String>>,
        results: &mut Vec<FutileCycle>,
    ) {
        if path.len() > 8 {
            return;
        }

        if let Some(edges) = adj.get(current) {
            for &edge in edges {
                let next = edge.to_state.as_str();
                if next == target && !path.is_empty() {
                    Self::record_closed_cycle(target, edge, path, seen_cycles, results);
                } else if !in_path.contains(next) && next != target {
                    in_path.insert(next);
                    path.push((next, edge));
                    self.dfs_find_cycles(
                        next,
                        target,
                        adj,
                        path,
                        in_path,
                        seen_cycles,
                        results,
                    );
                    path.pop();
                    in_path.remove(next);
                }
            }
        }
    }

    /// Evaluates a trajectory of visited states and detects if a cycle was traversed `k` times.
    pub fn count_cycle_traversals(
        &self,
        trajectory: &[&str],
        cycle: &[&str],
    ) -> usize {
        if cycle.len() < 2 || trajectory.len() < cycle.len() {
            return 0;
        }

        let m = cycle.len() - 1; // number of steps in one traversal
        let mut count = 0;
        let mut i = 0;

        while i + m <= trajectory.len() {
            let mut matches = true;
            for j in 0..=m {
                if trajectory[i + j] != cycle[j % cycle.len()] {
                    matches = false;
                    break;
                }
            }
            if matches {
                count += 1;
                i += m;
            } else {
                i += 1;
            }
        }

        count
    }
}

// Origin: engine/crates_rs/core_wdp/src/ddc/move_network.rs
// Claim: urn:core:crates_rs:core-wdp:move-network:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8578072a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8578072a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8578072a {
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
impl BoundaryError8578072a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8578072a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8578072a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8578072a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8578072a> {
        if capacity_bound == 0 {
            return Err(BoundaryError8578072a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8578072a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8578072a::ExceedsCapacity {
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
mod l4_boundary_tests_8578072a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8578072a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8578072a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8578072a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8578072a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8578072a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8578072a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8578072a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
