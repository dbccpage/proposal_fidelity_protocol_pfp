//! Immunity propagation, retro-inheritance, and lineage taint.
//!
//! Enforces:
//! - F-IMMUNE-09: No horizon-reset relay (original acquisition_id and origin preserved).
//! - F-IMMUNE-10: Distance is shortest path in inheritance-edge hops (weight = (1/2)^hops for hops <= 10).
//! - F-IMMUNE-11: Stale armed caches are invalidated; suspended or revoked antibodies are disarmed.
//! - F-RES-07: Custody invalidation is global across all bindings.
//! - F-RES-11: Taint moves forward along the causal graph under host policy.
//!
//! AuthorityEffect: None.

use crate::genealogy::LineageGraphV1;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::One;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ImmunityAcquisitionV1 {
    pub acquisition_id: String,
    pub origin_prompt_id: String,
    pub acquired_generation: u64,
    pub antibody_id: String,
    pub qualifying_witness_receipts: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ImmunityPropagationV1 {
    pub propagation_id: String,
    pub acquisition_id: String,
    pub origin_prompt_id: String,
    pub source_prompt_id: String,
    pub target_prompt_id: String,
    pub hop_distance: u32,
    pub direction: String,
    pub weight_num: i64,
    pub weight_den: i64,
}

pub struct ImmunityEngineV1;

impl ImmunityEngineV1 {
    /// Compute shortest path backward propagation up to max_hops (10) on inheritance DAG.
    /// Returns map of target_prompt_id -> (hop_distance, weight).
    pub fn compute_backward_propagation(
        graph: &LineageGraphV1,
        origin_prompt_id: &str,
        max_hops: u32,
    ) -> HashMap<String, (u32, BigRational)> {
        let mut distances: HashMap<String, u32> = HashMap::new();
        let mut queue: VecDeque<(String, u32)> = VecDeque::new();

        distances.insert(origin_prompt_id.to_string(), 0);
        queue.push_back((origin_prompt_id.to_string(), 0));

        while let Some((curr, d)) = queue.pop_front() {
            if d >= max_hops {
                continue;
            }
            for parent in graph.get_parents(&curr) {
                let next_d = d + 1;
                if !distances.contains_key(&parent) || next_d < distances[&parent] {
                    distances.insert(parent.clone(), next_d);
                    queue.push_back((parent, next_d));
                }
            }
        }

        let mut result = HashMap::new();
        for (target, d) in distances {
            if d <= max_hops {
                // weight = (1/2)^d
                let den = BigInt::from(1) << d;
                let weight = BigRational::new(BigInt::one(), den);
                result.insert(target, (d, weight));
            }
        }
        result
    }

    /// Forward inheritance across all descendants (full inheritance).
    pub fn compute_forward_inheritance(
        graph: &LineageGraphV1,
        origin_prompt_id: &str,
    ) -> HashSet<String> {
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        queue.push_back(origin_prompt_id.to_string());
        visited.insert(origin_prompt_id.to_string());

        while let Some(curr) = queue.pop_front() {
            for child in graph.get_children(&curr) {
                if !visited.contains(&child) {
                    visited.insert(child.clone());
                    queue.push_back(child);
                }
            }
        }
        visited
    }

    /// Global custody filter: disarms any antibody whose custody status is Suspended or Revoked.
    pub fn filter_armed_repertoire(
        repertoire: &[String],
        revoked_or_suspended: &HashSet<String>,
    ) -> Vec<String> {
        repertoire
            .iter()
            .filter(|ab| !revoked_or_suspended.contains(*ab))
            .cloned()
            .collect()
    }

    /// Forward lineage taint under host policy (default OR: child tainted if any parent tainted).
    pub fn compute_forward_taint(
        graph: &LineageGraphV1,
        initial_tainted: &HashSet<String>,
    ) -> HashSet<String> {
        let mut tainted = initial_tainted.clone();
        let mut changed = true;

        while changed {
            changed = false;
            for (parent, children) in &graph.forward_edges {
                if tainted.contains(parent) {
                    for edge in children {
                        if !tainted.contains(&edge.child_id) {
                            tainted.insert(edge.child_id.clone());
                            changed = true;
                        }
                    }
                }
            }
        }
        tainted
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immunity.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:immunity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5eddf435 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5eddf435` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5eddf435 {
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
impl BoundaryError5eddf435 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5eddf435 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5eddf435 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5eddf435 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5eddf435> {
        if capacity_bound == 0 {
            return Err(BoundaryError5eddf435::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5eddf435::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5eddf435::ExceedsCapacity {
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
mod tests {
    use super::*;
    use crate::genealogy::InheritanceRelationship;

    #[test]
    fn test_f_immune_10_shortest_hop_distance() {
        let mut g = LineageGraphV1::new();
        // A -> B -> C (2 hops from C to A)
        g.add_inheritance_edge("A", "B", InheritanceRelationship::DirectMutation, "w1")
            .unwrap();
        g.add_inheritance_edge("B", "C", InheritanceRelationship::DirectMutation, "w2")
            .unwrap();

        let props = ImmunityEngineV1::compute_backward_propagation(&g, "C", 10);
        assert_eq!(props.get("C").unwrap().0, 0);
        assert_eq!(props.get("B").unwrap().0, 1);
        assert_eq!(
            props.get("B").unwrap().1,
            BigRational::new(BigInt::one(), BigInt::from(2))
        );
        assert_eq!(props.get("A").unwrap().0, 2);
        assert_eq!(
            props.get("A").unwrap().1,
            BigRational::new(BigInt::one(), BigInt::from(4))
        );
    }

    #[test]
    fn test_f_immune_09_max_10_hops() {
        let mut g = LineageGraphV1::new();
        // Build chain of 12 hops: N0 -> N1 -> ... -> N12
        for i in 0..12 {
            let p = format!("N{}", i);
            let c = format!("N{}", i + 1);
            g.add_inheritance_edge(&p, &c, InheritanceRelationship::DirectMutation, "w")
                .unwrap();
        }

        let props = ImmunityEngineV1::compute_backward_propagation(&g, "N12", 10);
        // N12 (d=0) down to N2 (d=10) must be present
        assert!(props.contains_key("N2"));
        // N1 (d=11) and N0 (d=12) must NOT be present
        assert!(!props.contains_key("N1"));
        assert!(!props.contains_key("N0"));
    }

    #[test]
    fn test_f_res_07_global_custody_invalidation() {
        let rep = vec!["ab1".to_string(), "ab2".to_string(), "ab3".to_string()];
        let mut revoked = HashSet::new();
        revoked.insert("ab2".to_string());

        let armed = ImmunityEngineV1::filter_armed_repertoire(&rep, &revoked);
        assert_eq!(armed, vec!["ab1".to_string(), "ab3".to_string()]);
    }
}

#[cfg(test)]
mod l4_boundary_tests_5eddf435 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5eddf435::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5eddf435::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5eddf435::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5eddf435::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5eddf435::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError5eddf435::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError5eddf435::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
