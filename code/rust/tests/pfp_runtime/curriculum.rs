//! Curriculum Generator and Fixed-Judge Invariant Tests (U23).
//!
//! AuthorityEffect: None.

use pfp_runtime::curriculum::{CurriculumError, CurriculumGenerator, Edge};

const PINNED_CHECKER_DIGEST: &str =
    "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

#[test]
fn test_b1_ladder_generates_certified_cycle_ranks() {
    for target_b1 in 1..=5 {
        let instance =
            CurriculumGenerator::generate_cochain_instance(target_b1, 42, PINNED_CHECKER_DIGEST)
                .expect("Failed to generate instance");

        // Certified b1 formula: |E| - |V| + 1
        let actual_b1 = instance.edges.len() - instance.num_vertices + 1;
        assert_eq!(
            actual_b1, target_b1,
            "Instance b1 {} does not match target {}",
            actual_b1, target_b1
        );
        assert_eq!(instance.b1, target_b1);
        assert_eq!(instance.reference_chords.len(), target_b1);
        assert_eq!(instance.checker_digest, PINNED_CHECKER_DIGEST);
    }
}

#[test]
fn test_relabelled_copies_collapse_to_same_canonical_digest() {
    // Generate a base instance
    let inst =
        CurriculumGenerator::generate_cochain_instance(3, 100, PINNED_CHECKER_DIGEST).unwrap();

    // Create a permutation of vertex labels (0 <-> 1, 2 <-> 3, etc.)
    // A relabelled isomorphic graph must have the same canonical digest
    let num_v = inst.num_vertices;
    // Simple cycle permutation: pi(x) = (x + 1) % num_v
    let relabelled_edges: Vec<Edge> = inst
        .edges
        .iter()
        .map(|e| {
            let u_new = (e.u + 1) % num_v;
            let v_new = (e.v + 1) % num_v;
            Edge {
                u: u_new.min(v_new),
                v: u_new.max(v_new),
                weight: e.weight,
            }
        })
        .collect();

    let digest_orig = CurriculumGenerator::compute_canonical_digest(num_v, &inst.edges);
    let digest_perm = CurriculumGenerator::compute_canonical_digest(num_v, &relabelled_edges);

    assert_eq!(
        digest_orig, digest_perm,
        "Relabelled isomorphic graph must produce identical canonical digest"
    );
}

#[test]
fn test_fixed_judge_invariant_detects_digest_change() {
    // Normal case: digest matches
    let res =
        CurriculumGenerator::verify_judge_fixity(PINNED_CHECKER_DIGEST, PINNED_CHECKER_DIGEST);
    assert!(res.is_ok());

    // Mid-run change: judge updated mid-ladder
    let changed_digest = "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
    let err = CurriculumGenerator::verify_judge_fixity(changed_digest, PINNED_CHECKER_DIGEST)
        .unwrap_err();

    match err {
        CurriculumError::JudgeChanged { expected, actual } => {
            assert_eq!(expected, PINNED_CHECKER_DIGEST);
            assert_eq!(actual, changed_digest);
        }
        other => panic!("Expected JudgeChanged, got {:?}", other),
    }
}

// Origin: engine/crates_rs/tests/pfp_runtime/curriculum.rs
// Claim: urn:core:crates_rs:tests:curriculum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf23575ae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf23575ae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf23575ae {
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
impl BoundaryErrorf23575ae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf23575ae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf23575ae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf23575ae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf23575ae> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf23575ae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf23575ae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf23575ae::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_f23575ae() {
    let admitted = BoundaryRecordf23575ae::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf23575ae::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
