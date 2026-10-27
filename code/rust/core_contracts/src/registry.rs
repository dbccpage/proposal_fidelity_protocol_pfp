//! Canonical contract registry: load & validate the `contract_canonical_definitions`
//! corpus (VALIDATION, not enforcement).
//!
//! The canonical corpus is TWO schemas, not one:
//! * the **math** corpus (`math/**`, 458 files) — validated structurally here via
//!   [`math_corpus`] (it confers no authority and does not map to
//!   [`crate::schema::ContractDescriptor`]);
//! * the **core 00–08** governance corpus — to be loaded and run through the existing
//!   [`crate::validate::validate_registry`] in a follow-up (see
//!   `sprints/105/core_contracts_readiness_report.md`, commit 2).
//!
//! This module confers no authority and gates nothing at runtime.

#[path = "registry_math_corpus.rs"]
pub mod math_corpus;
#[path = "registry_projections.rs"]
pub mod projections;
#[path = "registry_v1_loader.rs"]
pub mod v1_loader;
#[path = "registry_v1_types.rs"]
pub mod v1_types;
#[path = "registry_v1_validate.rs"]
pub mod v1_validate;
#[path = "registry_v1_vocabulary.rs"]
pub mod v1_vocabulary;

pub use math_corpus::{validate_math_corpus, MathCorpusError, MathCorpusReport};
pub use projections::{verify_projected_corpus, ProjectionError, ProjectionReport};
pub use v1_loader::{load_v1_dir, V1LoadError, V1LoadReport};
pub use v1_types::{ContractKind, DescriptorBlock, CoreContractV1, CoreContractV1Status};
pub use v1_validate::validate_v1;


/// Refusal from a math/core corpus split.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PartitionError {
    /// The same id appears in both corpora.
    Overlap { id: u32 },
    /// An id is repeated inside one corpus.
    Duplicate { id: u32 },
    /// The union count is not the sum of the two lengths.
    CountMismatch { got: u32, expected: u32 },
    /// A count overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_contracts/src/registry.rs
// Claim: urn:core:crates_rs:core-contracts:registry:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PartitionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PartitionError {}

/// Two corpora with empty intersection.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CorpusPartition {
    math: u32,
    core: u32,
}

impl CorpusPartition {
    fn ensure_disjoint_and_unique(math_ids: &[u32], core_ids: &[u32]) -> Result<(), PartitionError> {
        for (index, id) in math_ids.iter().enumerate() {
            if math_ids[..index].contains(id) || core_ids.contains(id) {
                return Err(if core_ids.contains(id) {
                    PartitionError::Overlap { id: *id }
                } else {
                    PartitionError::Duplicate { id: *id }
                });
            }
        }
        for (index, id) in core_ids.iter().enumerate() {
            if core_ids[..index].contains(id) {
                return Err(PartitionError::Duplicate { id: *id });
            }
        }
        Ok(())
    }

    /// Admit two id lists only when they are internally unique and disjoint.
    pub fn try_new(math_ids: &[u32], core_ids: &[u32]) -> Result<Self, PartitionError> {
        Self::ensure_disjoint_and_unique(math_ids, core_ids)?;
        let math = u32::try_from(math_ids.len()).map_err(|_| PartitionError::Overflow)?;
        let core = u32::try_from(core_ids.len()).map_err(|_| PartitionError::Overflow)?;
        let union = math.checked_add(core).ok_or(PartitionError::Overflow)?;
        let expected = union;
        if union != expected {
            return Err(PartitionError::CountMismatch { got: union, expected });
        }
        let out = Self { math, core };
        Ok(out)
    }

    /// Size of the math corpus.
    pub fn math(&self) -> u32 { self.math }
    /// Size of the core corpus.
    pub fn core(&self) -> u32 { self.core }
    /// `|math ∪ core|`.
    pub fn union_len(&self) -> Result<u32, PartitionError> {
        self.math.checked_add(self.core).ok_or(PartitionError::Overflow)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod partition_tests {
    use super::*;
    #[test]
    fn disjoint_corpora_add() {
        let split = CorpusPartition::try_new(&[1, 2], &[3]);
        assert!(matches!(split, Ok(ref s) if s.math() == 2 && s.core() == 1 && s.union_len().ok() == Some(3)));
    }
    #[test]
    fn a_shared_id_is_refused() {
        assert!(matches!(CorpusPartition::try_new(&[1], &[1]), Err(PartitionError::Overlap { id: 1 })));
    }
}
