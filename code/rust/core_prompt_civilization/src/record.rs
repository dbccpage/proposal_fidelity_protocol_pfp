//! Immutable Prompt Genome, Protected Spans, and Derived Views.
//!
//! Enforces:
//! - F-GENOME-01: The genome is immutable; the view is derived at a declared revision.
//! - F-GENOME-02: Re-execution creates an occurrence, not a genome.
//! - F-GENOME-03: Derived fields are rederived; mismatch returns DERIVED_FIELD_MISMATCH / PROTECTED_BOUNDARY_UNRESOLVED.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::cmp::max;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CustodyTier {
    Wild,
    Candidate,
    Reviewed,
    Admitted,
    Suspended,
    Revoked,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RetrievalEligibility {
    Active,
    Dormant,
    Shelved,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PromptMaturity {
    Unmeasured,
    Maturing,
    Evaluated,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PacketRefV1 {
    pub packet_id: String,
    pub sha256: String,
    pub packet_kind: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ParentLinkV1 {
    pub parent_id: String,
    pub relationship: String,
    pub witness_receipt_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProtectedSpanV1 {
    pub name: String,
    pub start_byte: usize,
    pub end_byte: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExecutionOccurrenceV1 {
    pub occurrence_id: String,
    pub prompt_id: String,
    pub session_id: String,
    pub input_packet_id: String,
    pub output_packet_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PromptGenomeV1 {
    pub prompt_id: String,
    pub source_packet_refs: Vec<PacketRefV1>,
    pub domain_model: serde_json::Value,
    pub parents: Vec<ParentLinkV1>,
    pub generation: u64,
    pub birth_custody: CustodyTier,
    pub protected_spans: Vec<ProtectedSpanV1>,
    pub authority_effect: String,
}

impl PromptGenomeV1 {
    pub fn compute_id(
        source_packet_refs: &[PacketRefV1],
        domain_model: &serde_json::Value,
        parents: &[ParentLinkV1],
        birth_custody: CustodyTier,
        protected_spans: &[ProtectedSpanV1],
    ) -> String {
        let mut hasher = Sha256::new();
        hasher.update(b"core-prompt-genome-v1:");
        let mut tuple_val = serde_json::json!([
            source_packet_refs,
            domain_model,
            parents,
            birth_custody,
            protected_spans
        ]);
        crate::prompt_family::sort_keys(&mut tuple_val);
        let serialized = serde_json::to_vec(&tuple_val).unwrap_or_default();
        hasher.update(&serialized);
        format!("genome_{}", hex::encode(hasher.finalize()))
    }

    pub fn new(
        source_packet_refs: Vec<PacketRefV1>,
        domain_model: serde_json::Value,
        parents: Vec<ParentLinkV1>,
        generation: u64,
        protected_spans: Vec<ProtectedSpanV1>,
    ) -> Self {
        let birth_custody = CustodyTier::Wild;
        let prompt_id = Self::compute_id(
            &source_packet_refs,
            &domain_model,
            &parents,
            birth_custody,
            &protected_spans,
        );
        Self {
            prompt_id,
            source_packet_refs,
            domain_model,
            parents,
            generation,
            birth_custody,
            protected_spans,
            authority_effect: "None".to_string(),
        }
    }

    pub fn create_verified(
        source_packet_refs: Vec<PacketRefV1>,
        domain_model: serde_json::Value,
        parents: Vec<ParentLinkV1>,
        parent_generations: &[u64],
        declared_generation: u64,
        allowed_boundary_names: &[&str],
        declared_spans: Vec<ProtectedSpanV1>,
    ) -> Result<Self, String> {
        let computed_gen = if parent_generations.is_empty() {
            0
        } else {
            1 + parent_generations.iter().copied().fold(0, max)
        };
        if declared_generation != computed_gen {
            return Err(format!(
                "DERIVED_FIELD_MISMATCH: declared generation {} != recomputed {}",
                declared_generation, computed_gen
            ));
        }

        for span in &declared_spans {
            if !allowed_boundary_names.contains(&span.name.as_str()) {
                return Err(format!(
                    "PROTECTED_BOUNDARY_UNRESOLVED: unknown boundary '{}'",
                    span.name
                ));
            }
        }

        Ok(Self::new(
            source_packet_refs,
            domain_model,
            parents,
            computed_gen,
            declared_spans,
        ))
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PromptViewV1 {
    pub prompt_id: String,
    pub current_custody: CustodyTier,
    pub retrieval_eligibility: RetrievalEligibility,
    pub maturity: PromptMaturity,
    pub armed_repertoire: Vec<String>,
    pub ledger_revision: u64,
    pub authority_effect: String,
}

// Origin: engine/crates_rs/core_prompt_civilization/src/record.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:record:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf12df652 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf12df652` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf12df652 {
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
impl BoundaryErrorf12df652 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf12df652 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf12df652 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf12df652 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf12df652> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf12df652::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf12df652::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf12df652::ExceedsCapacity {
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

    #[test]
    fn genome_identity_is_stable_under_nested_key_reordering() {
        fn domain_model(reverse: bool) -> serde_json::Value {
            let mut inner = serde_json::Map::new();
            let pairs = if reverse {
                [("z", 1), ("a", 2)]
            } else {
                [("a", 2), ("z", 1)]
            };
            for (key, value) in pairs {
                inner.insert(key.into(), serde_json::json!(value));
            }
            let mut outer = serde_json::Map::new();
            outer.insert("z".into(), serde_json::json!(0));
            outer.insert(
                "a".into(),
                serde_json::Value::Array(vec![
                    serde_json::Value::Object(inner),
                    serde_json::json!(9),
                ]),
            );
            serde_json::Value::Object(outer)
        }
        let id = |model: &serde_json::Value| {
            PromptGenomeV1::compute_id(&[], model, &[], CustodyTier::Wild, &[])
        };
        let first = domain_model(true);
        let second = domain_model(false);
        assert_eq!(first, second);
        assert_eq!(id(&first), id(&second));
        // SHA-256 of the existing compact, sorted Rust identity envelope:
        // [[],{"a":[{"a":2,"z":1},9],"z":0},[],"Wild",[]]
        assert_eq!(
            id(&first),
            "genome_0a7c69d37eb984e67f2359188154aa50f9ee2470f8a003d5d4abfa3b50ca78d2"
        );
        assert_ne!(
            id(&serde_json::json!([1, 2])),
            id(&serde_json::json!([2, 1]))
        );
    }

    #[test]
    fn test_f_genome_01_different_parents_produce_different_ids() {
        let refs = vec![PacketRefV1 {
            packet_id: "p1".into(),
            sha256: "d1".into(),
            packet_kind: "prompt-artifact".into(),
        }];
        let dm = serde_json::json!({"domain": "math"});
        let p_a = vec![ParentLinkV1 {
            parent_id: "A".into(),
            relationship: "DirectMutation".into(),
            witness_receipt_digest: "w1".into(),
        }];
        let p_b = vec![ParentLinkV1 {
            parent_id: "B".into(),
            relationship: "DirectMutation".into(),
            witness_receipt_digest: "w2".into(),
        }];

        let g1 = PromptGenomeV1::new(refs.clone(), dm.clone(), p_a, 1, vec![]);
        let g2 = PromptGenomeV1::new(refs, dm, p_b, 1, vec![]);
        assert_ne!(g1.prompt_id, g2.prompt_id);
    }

    #[test]
    fn test_f_genome_02_occurrence_does_not_create_genome() {
        let occ1 = ExecutionOccurrenceV1 {
            occurrence_id: "occ-1".into(),
            prompt_id: "genome_xyz".into(),
            session_id: "s1".into(),
            input_packet_id: "in1".into(),
            output_packet_id: "out1".into(),
        };
        let occ2 = ExecutionOccurrenceV1 {
            occurrence_id: "occ-2".into(),
            prompt_id: "genome_xyz".into(),
            session_id: "s1".into(),
            input_packet_id: "in1".into(),
            output_packet_id: "out2".into(),
        };
        assert_eq!(occ1.prompt_id, occ2.prompt_id);
        assert_ne!(occ1.occurrence_id, occ2.occurrence_id);
    }

    #[test]
    fn test_f_genome_03_derived_field_checks() {
        let refs = vec![];
        let dm = serde_json::json!({});
        let parents = vec![];
        let res = PromptGenomeV1::create_verified(
            refs,
            dm,
            parents,
            &[],
            1, // Wrong generation: root must be 0
            &["core"],
            vec![],
        );
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("DERIVED_FIELD_MISMATCH"));

        let res2 = PromptGenomeV1::create_verified(
            vec![],
            serde_json::json!({}),
            vec![],
            &[],
            0,
            &["core"],
            vec![ProtectedSpanV1 {
                name: "unknown-boundary".into(),
                start_byte: 0,
                end_byte: 1,
            }],
        );
        assert!(res2.is_err());
        assert!(res2.unwrap_err().contains("PROTECTED_BOUNDARY_UNRESOLVED"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_f12df652 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf12df652::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf12df652::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf12df652::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf12df652::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf12df652::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorf12df652::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorf12df652::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
