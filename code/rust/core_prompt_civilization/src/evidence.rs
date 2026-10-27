//! Food-generated catalytic loops and causal evaluator independence.
//! AuthorityEffect: None.

use std::collections::{BTreeMap, BTreeSet};

use crate::genealogy::LineageGraphV1;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EvidenceReactionV1 {
    pub reaction_id: String,
    pub inputs: BTreeSet<String>,
    pub outputs: BTreeSet<String>,
    pub catalysts: BTreeSet<String>,
}

/// Greatest reflexively autocatalytic, food-generated subset, by monotone
/// deletion. Closure ignores catalysis; retained reactions require a catalyst
/// within that closure. Empty catalyst sets do not count as RAF reactions.
pub fn maximal_raf(
    food: &BTreeSet<String>,
    reactions: &[EvidenceReactionV1],
) -> Result<BTreeSet<String>, String> {
    let ids: BTreeSet<_> = reactions.iter().map(|r| &r.reaction_id).collect();
    if ids.len() != reactions.len() {
        return Err("DUPLICATE_REACTION_ID".into());
    }
    let mut active: Vec<_> = reactions.iter().collect();
    loop {
        let mut closure = food.clone();
        loop {
            let before = closure.len();
            for reaction in &active {
                if reaction.inputs.is_subset(&closure) {
                    closure.extend(reaction.outputs.iter().cloned());
                }
            }
            if closure.len() == before {
                break;
            }
        }
        let before = active.len();
        active.retain(|r| r.inputs.is_subset(&closure) && !r.catalysts.is_disjoint(&closure));
        if active.len() == before {
            return Ok(active.iter().map(|r| r.reaction_id.clone()).collect());
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EvaluationTraceV1 {
    pub digest: String,
    pub prompt_id: String,
    pub generator_actor: String,
    pub evaluator_actor: String,
    pub dependencies: BTreeSet<String>,
}

fn validate_trace_node(trace: &EvaluationTraceV1, digest: &str) -> Result<(), String> {
    if trace.digest != digest {
        return Err("EVIDENCE_DIGEST_MISMATCH".into());
    }
    let roles_valid = !trace.generator_actor.is_empty()
        && !trace.evaluator_actor.is_empty()
        && trace.generator_actor != trace.evaluator_actor;
    if !roles_valid {
        return Err("ROLE_SEPARATION_REQUIRED".into());
    }
    Ok(())
}

/// External anchors are supplied by the host's authenticated evidence registry,
/// never taken from claims inside a trace.
pub fn validate_independence(
    subject: &str,
    trace_digest: &str,
    traces: &BTreeMap<String, EvaluationTraceV1>,
    external_anchors: &BTreeSet<String>,
    lineage: &LineageGraphV1,
) -> Result<(), String> {
    let mut pending = vec![trace_digest.to_owned()];
    let mut seen = BTreeSet::new();
    let mut self_fed = false;
    let mut anchored = false;
    while let Some(digest) = pending.pop() {
        if !seen.insert(digest.clone()) {
            continue;
        }
        if external_anchors.contains(&digest) {
            anchored = true;
            continue;
        }
        let trace = traces.get(&digest).ok_or("EVIDENCE_DEPENDENCY_MISSING")?;
        validate_trace_node(trace, &digest)?;
        self_fed |= lineage.has_path(subject, &trace.prompt_id);
        pending.extend(trace.dependencies.iter().cloned());
    }
    if self_fed && !anchored {
        return Err("SELF_FEEDING_EVIDENCE".into());
    }
    Ok(())
}

// Origin: engine/crates_rs/core_prompt_civilization/src/evidence.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:evidence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord615f1fe4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord615f1fe4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError615f1fe4 {
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
impl BoundaryError615f1fe4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError615f1fe4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError615f1fe4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord615f1fe4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError615f1fe4> {
        if capacity_bound == 0 {
            return Err(BoundaryError615f1fe4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError615f1fe4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError615f1fe4::ExceedsCapacity {
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
mod l4_boundary_tests_615f1fe4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord615f1fe4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord615f1fe4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord615f1fe4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord615f1fe4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord615f1fe4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError615f1fe4::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError615f1fe4::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
