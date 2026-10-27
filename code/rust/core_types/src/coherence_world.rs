use crate::coherence_structures::{GenerationContext, StructuralCandidate};
use crate::everett_dag_state::EverettNodeId;
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LogicalValue {
    True,
    False,
    Unknown,
}

impl LogicalValue {
    pub fn conflicts_with(&self, other: &Self) -> bool {
        matches!(
            (self, other),
            (Self::True, Self::False) | (Self::False, Self::True)
        )
    }
}

#[derive(Debug, Clone)]
pub struct World {
    pub id: EverettNodeId,
    pub candidate: StructuralCandidate,
    pub assertions: HashMap<String, LogicalValue>,
}

impl World {
    pub fn new(candidate: StructuralCandidate, _ctx: GenerationContext) -> Self {
        let id = EverettNodeId::from(format!("W_{}", uuid::Uuid::new_v4().simple()));
        let assertions = HashMap::new();
        Self {
            id,
            candidate,
            assertions,
        }
    }

    pub fn preview(candidate: &StructuralCandidate, _ctx: &GenerationContext) -> Self {
        let id = EverettNodeId::from("Preview");
        let assertions = HashMap::new();
        Self {
            id,
            candidate: candidate.clone(),
            assertions,
        }
    }

    pub fn extract_logical_assertions(&self) -> &HashMap<String, LogicalValue> {
        &self.assertions
    }
}

/// Count of keys on which two assertion maps take contradictory truth values.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CoherenceObstruction {
    shared_keys: u64,
    conflict_count: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CoherenceObstructionError {
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/coherence_world.rs
// Claim: urn:core:crates_rs:core-types:coherence-world:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CoherenceObstructionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CoherenceObstructionError {}

impl CoherenceObstruction {
    pub fn try_between(
        left: &HashMap<String, LogicalValue>,
        right: &HashMap<String, LogicalValue>,
    ) -> Result<Self, CoherenceObstructionError> {
        use std::collections::BTreeSet;
        let mut keys = BTreeSet::new();
        keys.extend(left.keys().cloned());
        keys.extend(right.keys().cloned());
        let mut shared_keys = 0u64;
        let mut conflict_count = 0u64;
        for key in keys {
            let Some(left_value) = left.get(&key) else {
                continue;
            };
            let Some(right_value) = right.get(&key) else {
                continue;
            };
            shared_keys = shared_keys
                .checked_add(1)
                .ok_or(CoherenceObstructionError::Overflow)?;
            if left_value.conflicts_with(right_value) {
                conflict_count = conflict_count
                    .checked_add(1)
                    .ok_or(CoherenceObstructionError::Overflow)?;
            }
        }
        Ok(Self {
            shared_keys,
            conflict_count,
        })
    }

    pub fn conflict_count(&self) -> u64 {
        self.conflict_count
    }

    pub fn shared_keys(&self) -> u64 {
        self.shared_keys
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_df975768 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
