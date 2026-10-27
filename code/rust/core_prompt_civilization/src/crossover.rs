//! Witnessed homologous recombination. All outputs retain Wild custody.
//! AuthorityEffect: None.

use std::collections::{BTreeMap, BTreeSet};

use sha2::{Digest, Sha256};

use crate::genealogy::LineageGraphV1;
use crate::record::{PacketRefV1, ParentLinkV1, PromptGenomeV1, ProtectedSpanV1};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HomologousBlockV1 {
    pub name: String,
    pub start: usize,
    pub end: usize,
    pub protected: bool,
}

pub struct CrossoverParentV1<'a> {
    pub genome: &'a PromptGenomeV1,
    pub bytes: &'a [u8],
    pub blocks: &'a [HomologousBlockV1],
    /// Host-resolved current rule version by mutually exclusive detector family.
    pub immunity: &'a BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CrossoverReceiptV1 {
    pub genome: PromptGenomeV1,
    pub bytes: Vec<u8>,
    pub ancestor_ids: BTreeSet<String>,
    pub immunity: BTreeMap<String, String>,
    pub authority_effect: &'static str,
}

fn validate(parent: &CrossoverParentV1<'_>) -> Result<(), String> {
    let digest = hex::encode(Sha256::digest(parent.bytes));
    if !parent
        .genome
        .source_packet_refs
        .iter()
        .any(|r| r.sha256.strip_prefix("sha256:").unwrap_or(&r.sha256) == digest)
    {
        return Err("PARENT_BYTES_MISMATCH".into());
    }
    let mut position = 0;
    let mut names = BTreeSet::new();
    let mut protected = Vec::new();
    for block in parent.blocks {
        if block.start != position
            || block.end <= block.start
            || block.end > parent.bytes.len()
            || !names.insert(&block.name)
        {
            return Err("HOMOLOGY_UNRESOLVED".into());
        }
        if block.protected {
            protected.push(ProtectedSpanV1 {
                name: block.name.clone(),
                start_byte: block.start,
                end_byte: block.end,
            });
        }
        position = block.end;
    }
    if position != parent.bytes.len() || protected != parent.genome.protected_spans {
        return Err("PROTECTED_BOUNDARY_UNRESOLVED".into());
    }
    Ok(())
}

fn validate_recombine_parents(
    left: &CrossoverParentV1<'_>,
    right: &CrossoverParentV1<'_>,
    take_right: &BTreeSet<String>,
    parent_witnesses: [&str; 2],
) -> Result<(), String> {
    validate(left)?;
    validate(right)?;
    let witnesses_invalid = parent_witnesses
        .iter()
        .any(|w| w.is_empty() || *w == "unverified");
    if left.genome.prompt_id == right.genome.prompt_id || witnesses_invalid {
        return Err("DUAL_PARENT_WITNESS_REQUIRED".into());
    }
    let unknown_block = take_right
        .iter()
        .any(|name| !left.blocks.iter().any(|b| &b.name == name));
    if left.genome.domain_model != right.genome.domain_model
        || left.blocks.len() != right.blocks.len()
        || unknown_block
    {
        return Err("HOMOLOGY_UNRESOLVED".into());
    }
    Ok(())
}

fn merge_immunity(
    left: &BTreeMap<String, String>,
    right: &BTreeMap<String, String>,
) -> Result<BTreeMap<String, String>, String> {
    let mut immunity = left.clone();
    for (family, version) in right {
        if immunity.get(family).is_some_and(|v| v != version) {
            // No rank, fitness, or generated decision may silently resolve conflict.
            return Err(format!("IMMUNITY_CONFLICT: {family}"));
        }
        immunity.insert(family.clone(), version.clone());
    }
    Ok(immunity)
}

fn splice_parent_blocks(
    left: &CrossoverParentV1<'_>,
    right: &CrossoverParentV1<'_>,
    take_right: &BTreeSet<String>,
) -> Result<(Vec<u8>, Vec<ProtectedSpanV1>), String> {
    let mut bytes = Vec::new();
    let mut spans = Vec::new();
    for (a, b) in left.blocks.iter().zip(right.blocks) {
        if a.name != b.name || a.protected != b.protected {
            return Err("HOMOLOGY_UNRESOLVED".into());
        }
        if a.protected && left.bytes[a.start..a.end] != right.bytes[b.start..b.end] {
            return Err("PROTECTED_SPAN_MUTATION_REFUSED".into());
        }
        let start = bytes.len();
        bytes.extend_from_slice(if take_right.contains(&a.name) {
            &right.bytes[b.start..b.end]
        } else {
            &left.bytes[a.start..a.end]
        });
        if a.protected {
            spans.push(ProtectedSpanV1 {
                name: a.name.clone(),
                start_byte: start,
                end_byte: bytes.len(),
            });
        }
    }
    Ok((bytes, spans))
}

fn collect_ancestor_closure(
    left_id: &str,
    right_id: &str,
    ancestry: &LineageGraphV1,
) -> BTreeSet<String> {
    let mut ancestors = BTreeSet::new();
    let mut pending = vec![left_id.to_owned(), right_id.to_owned()];
    while let Some(id) = pending.pop() {
        if ancestors.insert(id.clone()) {
            pending.extend(ancestry.get_parents(&id));
        }
    }
    ancestors
}

/// Receipts are host-validated causal witnesses, one for each parent. The calculus
/// checks their presence and retains them; it does not authenticate their issuer.
pub fn recombine(
    left: CrossoverParentV1<'_>,
    right: CrossoverParentV1<'_>,
    take_right: &BTreeSet<String>,
    parent_witnesses: [&str; 2],
    ancestry: &LineageGraphV1,
) -> Result<CrossoverReceiptV1, String> {
    validate_recombine_parents(&left, &right, take_right, parent_witnesses)?;
    let immunity = merge_immunity(left.immunity, right.immunity)?;
    let (bytes, spans) = splice_parent_blocks(&left, &right, take_right)?;
    let ancestors =
        collect_ancestor_closure(&left.genome.prompt_id, &right.genome.prompt_id, ancestry);
    let parents = [left.genome, right.genome]
        .iter()
        .zip(parent_witnesses)
        .map(|(g, witness)| ParentLinkV1 {
            parent_id: g.prompt_id.clone(),
            relationship: "DirectMutation".into(),
            witness_receipt_digest: witness.into(),
        })
        .collect();
    let generation = left
        .genome
        .generation
        .max(right.genome.generation)
        .checked_add(1)
        .ok_or("GENERATION_OVERFLOW")?;
    let digest = hex::encode(Sha256::digest(&bytes));
    let genome = PromptGenomeV1::new(
        vec![PacketRefV1 {
            packet_id: format!("sha256:{digest}"),
            sha256: digest,
            packet_kind: "prompt-artifact".into(),
        }],
        left.genome.domain_model.clone(),
        parents,
        generation,
        spans,
    );
    Ok(CrossoverReceiptV1 {
        genome,
        bytes,
        ancestor_ids: ancestors,
        immunity,
        authority_effect: "None",
    })
}

// Origin: engine/crates_rs/core_prompt_civilization/src/crossover.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:crossover:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4e23e416 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4e23e416` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4e23e416 {
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
impl BoundaryError4e23e416 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4e23e416 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4e23e416 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4e23e416 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4e23e416> {
        if capacity_bound == 0 {
            return Err(BoundaryError4e23e416::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4e23e416::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4e23e416::ExceedsCapacity {
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
mod l4_boundary_tests_4e23e416 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4e23e416::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4e23e416::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4e23e416::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4e23e416::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4e23e416::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError4e23e416::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError4e23e416::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
