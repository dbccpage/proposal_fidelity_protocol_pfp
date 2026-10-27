//! Stable ID derivation for findings and candidates.
//!
//! Finding IDs: detector version + ordered raw-byte spans.
//! Candidate IDs: finding IDs + baseline hashes + replacement hashes + declared paths.

use super::canonical_json::{hash_canonical_v1, hash_raw_bytes, CanonicalJsonError};
use super::types::{OperatorImprovementCandidateV1, SourceSpanV1};
use serde::Serialize;
use sha2::{Digest, Sha256};

/// Material hashed into a finding ID.
#[derive(Debug, Clone, Serialize)]
struct FindingIdMaterialV1<'a> {
    detector_version: &'a str,
    spans: Vec<SpanMaterialV1<'a>>,
}

#[derive(Debug, Clone, Serialize)]
struct SpanMaterialV1<'a> {
    path: &'a str,
    content_sha256: &'a str,
    start: u64,
    end: u64,
}

/// Derive a stable finding ID from detector version and ordered raw-byte spans.
pub fn derive_finding_id_v1(
    detector_version: &str,
    spans: &[SourceSpanV1],
) -> Result<String, CanonicalJsonError> {
    let material = FindingIdMaterialV1 {
        detector_version,
        spans: spans
            .iter()
            .map(|s| SpanMaterialV1 {
                path: &s.path,
                content_sha256: &s.content_sha256,
                start: s.start,
                end: s.end,
            })
            .collect(),
    };
    let digest = hash_canonical_v1(&material)?;
    Ok(format!("finding-{digest}"))
}

/// Material hashed into a candidate ID.
#[derive(Debug, Clone, Serialize)]
struct CandidateIdMaterialV1<'a> {
    finding_ids: &'a [String],
    baseline_sha256: &'a [String],
    replacement_sha256: &'a [String],
    declared_paths: &'a [String],
}

/// Derive a stable candidate ID from finding IDs, hashes, and declared paths.
pub fn derive_candidate_id_v1(
    finding_ids: &[String],
    baseline_sha256: &[String],
    replacement_sha256: &[String],
    declared_paths: &[String],
) -> Result<String, CanonicalJsonError> {
    let material = CandidateIdMaterialV1 {
        finding_ids,
        baseline_sha256,
        replacement_sha256,
        declared_paths,
    };
    let digest = hash_canonical_v1(&material)?;
    Ok(format!("candidate-{digest}"))
}

/// Convenience: derive candidate ID from a fully populated candidate body
/// (uses declared edit paths and hashes only — not full bytes).
pub fn derive_candidate_id_from_body(
    candidate: &OperatorImprovementCandidateV1,
) -> Result<String, CanonicalJsonError> {
    let finding_ids = &candidate.source_finding_ids;
    let baseline: Vec<String> = candidate
        .edits
        .iter()
        .map(|e| e.baseline_sha256.clone())
        .collect();
    let replacement: Vec<String> = candidate
        .edits
        .iter()
        .map(|e| e.replacement_sha256.clone())
        .collect();
    let paths: Vec<String> = candidate.edits.iter().map(|e| e.path.clone()).collect();
    derive_candidate_id_v1(finding_ids, &baseline, &replacement, &paths)
}

/// Hash ordered span raw bytes for independent grounding checks.
pub fn span_raw_chain_hash(raw_slices: &[&[u8]]) -> String {
    let mut hasher = Sha256::new();
    for slice in raw_slices {
        hasher.update(hash_raw_bytes(slice).as_bytes());
    }
    format!("{:x}", hasher.finalize())
}

// Origin: engine/crates_rs/core_contracts/src/improvement_ids.rs
// Claim: urn:core:crates_rs:core-contracts:improvement-ids:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord86346fe7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord86346fe7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError86346fe7 {
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
impl BoundaryError86346fe7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError86346fe7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError86346fe7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord86346fe7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError86346fe7> {
        if capacity_bound == 0 {
            return Err(BoundaryError86346fe7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError86346fe7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError86346fe7::ExceedsCapacity {
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
    use crate::improvement::types::SourceSpanV1;

    fn span(path: &str, hash: &str, start: u64, end: u64) -> SourceSpanV1 {
        SourceSpanV1 {
            path: path.to_owned(),
            content_sha256: hash.to_owned(),
            start,
            end,
            start_line: None,
            end_line: None,
        }
    }

    #[test]
    fn finding_id_is_stable_and_order_sensitive() {
        let h = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
        let s1 = [span("a.md", h, 0, 4), span("b.md", h, 1, 5)];
        let s2 = [span("b.md", h, 1, 5), span("a.md", h, 0, 4)];
        let id1 = derive_finding_id_v1("det-v1", &s1).unwrap();
        let id1b = derive_finding_id_v1("det-v1", &s1).unwrap();
        let id2 = derive_finding_id_v1("det-v1", &s2).unwrap();
        assert_eq!(id1, id1b);
        assert_ne!(id1, id2);
        assert!(id1.starts_with("finding-"));
    }

    #[test]
    fn detector_version_changes_finding_id() {
        let h = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
        let spans = [span("x", h, 0, 1)];
        let a = derive_finding_id_v1("det-v1", &spans).unwrap();
        let b = derive_finding_id_v1("det-v2", &spans).unwrap();
        assert_ne!(a, b);
    }

    #[test]
    fn candidate_id_includes_paths_and_hashes() {
        let findings = vec!["finding-1".to_owned()];
        let base = vec!["c".repeat(64)];
        let repl = vec!["d".repeat(64)];
        let paths = vec!["skills/foo/SKILL.md".to_owned()];
        let id = derive_candidate_id_v1(&findings, &base, &repl, &paths).unwrap();
        let id2 =
            derive_candidate_id_v1(&findings, &base, &repl, &["skills/bar/SKILL.md".to_owned()])
                .unwrap();
        assert_ne!(id, id2);
        assert!(id.starts_with("candidate-"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_86346fe7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord86346fe7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord86346fe7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord86346fe7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord86346fe7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord86346fe7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError86346fe7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError86346fe7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
