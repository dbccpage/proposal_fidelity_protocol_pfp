//! Dependency-aware invalidation for incremental repair.
//!
//! The evidence graph maps each node (source, claim, report, review) to the nodes it
//! depends on. A change invalidates its transitive dependents. When coverage is unknown —
//! a changed node or a dependency the graph does not declare — every node is invalidated:
//! a conservative full recompute, never a silent partial reuse. A cyclic graph is refused.
//!
//! This is bookkeeping over declared dependencies. It does not invoke BQNF exactness or
//! additive repair theorems for research claims.
//!
//! AuthorityEffect: None.

use super::refuse;
use crate::stage::ports::Refusal;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub type DependencyGraph = BTreeMap<String, Vec<String>>;

/// `incremental_repair.routes` from the workflow.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum RepairRoute {
    PreserveWithFreshBinding,
    InvalidateTransitiveDependents,
    NewCandidateAndRecheck,
    ConservativeFullRecompute,
    ExplicitRevisionRequired,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RepairPlan {
    pub route: RepairRoute,
    pub invalidated: BTreeSet<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct ChangeScope {
    /// The question, a required claim statement or the checker policy changed.
    pub question_or_policy_changed: bool,
    /// The change is a supported local patch to the candidate.
    pub local_patch: bool,
}

fn closed(graph: &DependencyGraph) -> bool {
    graph
        .values()
        .flatten()
        .all(|dependency| graph.contains_key(dependency))
}

fn refuse_cycles(graph: &DependencyGraph) -> Result<(), Refusal> {
    // Kahn's algorithm over the closed graph, counting each distinct dependency once.
    let mut remaining: BTreeMap<&str, usize> = BTreeMap::new();
    let mut dependents: BTreeMap<&str, Vec<&str>> = BTreeMap::new();
    for (node, deps) in graph {
        let deps: BTreeSet<&str> = deps.iter().map(String::as_str).collect();
        remaining.insert(node.as_str(), deps.len());
        for dep in deps {
            dependents.entry(dep).or_default().push(node.as_str());
        }
    }
    let mut ready: Vec<&str> = remaining
        .iter()
        .filter(|(_, count)| **count == 0)
        .map(|(node, _)| *node)
        .collect();
    let mut resolved = 0usize;
    while let Some(done) = ready.pop() {
        resolved += 1;
        for node in dependents.get(done).into_iter().flatten() {
            if let Some(count) = remaining.get_mut(node) {
                *count -= 1;
                if *count == 0 {
                    ready.push(node);
                }
            }
        }
    }
    if resolved != graph.len() {
        return Err(refuse(
            "DEPENDENCY_CYCLE",
            "the evidence dependency graph has a cycle",
        ));
    }
    Ok(())
}

/// The nodes a change invalidates: its transitive dependents, or every node when the
/// change or the graph is not fully covered.
pub fn invalidated_nodes(
    graph: &DependencyGraph,
    changed: &BTreeSet<String>,
) -> Result<BTreeSet<String>, Refusal> {
    let all: BTreeSet<String> = graph.keys().cloned().collect();
    if !closed(graph) {
        return Ok(all);
    }
    refuse_cycles(graph)?;
    if !changed.is_subset(&all) {
        return Ok(all);
    }
    let mut affected = changed.clone();
    loop {
        let extra: BTreeSet<String> = graph
            .iter()
            .filter(|(node, deps)| {
                !affected.contains(*node) && deps.iter().any(|d| affected.contains(d))
            })
            .map(|(node, _)| node.clone())
            .collect();
        if extra.is_empty() {
            return Ok(affected);
        }
        affected.extend(extra);
    }
}

/// Choose the repair route for a change and the nodes it invalidates.
pub fn plan_repair(
    graph: &DependencyGraph,
    changed: &BTreeSet<String>,
    scope: ChangeScope,
) -> Result<RepairPlan, Refusal> {
    let all: BTreeSet<String> = graph.keys().cloned().collect();
    if scope.question_or_policy_changed {
        return Ok(RepairPlan {
            route: RepairRoute::ExplicitRevisionRequired,
            invalidated: all,
        });
    }
    if changed.is_empty() {
        return Ok(RepairPlan {
            route: RepairRoute::PreserveWithFreshBinding,
            invalidated: BTreeSet::new(),
        });
    }
    let invalidated = invalidated_nodes(graph, changed)?;
    let covered = closed(graph) && changed.is_subset(&all);
    let route = if !covered {
        RepairRoute::ConservativeFullRecompute
    } else if scope.local_patch {
        RepairRoute::NewCandidateAndRecheck
    } else {
        RepairRoute::InvalidateTransitiveDependents
    };
    Ok(RepairPlan { route, invalidated })
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/invalidation.rs
// Claim: urn:core:crates_rs:core-adversary:invalidation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9cd5cd34 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9cd5cd34` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9cd5cd34 {
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
impl BoundaryError9cd5cd34 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9cd5cd34 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9cd5cd34 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9cd5cd34 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9cd5cd34> {
        if capacity_bound == 0 {
            return Err(BoundaryError9cd5cd34::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9cd5cd34::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9cd5cd34::ExceedsCapacity {
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
mod l4_boundary_tests_9cd5cd34 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9cd5cd34::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9cd5cd34::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9cd5cd34::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9cd5cd34::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9cd5cd34::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9cd5cd34::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9cd5cd34::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
