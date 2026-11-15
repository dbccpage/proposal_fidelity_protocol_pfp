//! Falsifier parity integration tests for PCIV Support Policies, Fixtures, and Admission Boundaries.
//!
//! AuthorityEffect: None.
//!
//! Covers:
//! - F-SUPPORT-01: Support count is independent of observation ingestion order.
//! - F-SUPPORT-02: Non-transitive overlap case yields maximum independent set = 2.
//! - F-SUPPORT-03: Support is feasible without relabelling.
//! - F-SUPPORT-04: Support calculation is monotone.
//! - F-PHARM-01: Duplicate collapse: replays of the same event yield support = 1.
//! - F-RES-05: Inherited or propagated references are never observations.

use core_epistemic_immune_system::admission::{support, RawObservation};

#[test]
fn test_f_support_01_support_is_independent_of_ingestion_order() {
    // Three observations with independent host-bound correlation keys
    let obs1 = RawObservation {
        occurrence_id: "occ_1".to_string(),
        generating_model_id: "model_claude_3_5".to_string(),
        scaffold_digest: "scaffold_sha_1".to_string(),
        precedent_set_digest: "precedent_sha_1".to_string(),
        inheritance_root: "lineage_root_1".to_string(),
        is_propagated_reference: false,
    };
    let obs2 = RawObservation {
        occurrence_id: "occ_2".to_string(),
        generating_model_id: "model_gpt_4o".to_string(),
        scaffold_digest: "scaffold_sha_2".to_string(),
        precedent_set_digest: "precedent_sha_2".to_string(),
        inheritance_root: "lineage_root_2".to_string(),
        is_propagated_reference: false,
    };
    let obs3 = RawObservation {
        occurrence_id: "occ_3".to_string(),
        generating_model_id: "model_g_pro".to_string(),
        scaffold_digest: "scaffold_sha_3".to_string(),
        precedent_set_digest: "precedent_sha_3".to_string(),
        inheritance_root: "lineage_root_3".to_string(),
        is_propagated_reference: false,
    };

    let order_a = vec![obs1.clone(), obs2.clone(), obs3.clone()];
    let order_b = vec![obs3.clone(), obs1.clone(), obs2.clone()];
    let order_c = vec![obs2.clone(), obs3.clone(), obs1.clone()];

    let support_a = support(&order_a).expect("support computation must succeed");
    let support_b = support(&order_b).expect("support computation must succeed");
    let support_c = support(&order_c).expect("support computation must succeed");

    assert_eq!(support_a["support_count"], 3);
    assert_eq!(support_a["support_count"], support_b["support_count"]);
    assert_eq!(support_b["support_count"], support_c["support_count"]);
    assert_eq!(support_a["eligible_for_provisional"], true);
}

#[test]
fn test_f_support_02_non_transitive_overlap_case() {
    // A shares model with B; B shares scaffold with C; A and C share nothing
    let obs_a = RawObservation {
        occurrence_id: "occ_a".to_string(),
        generating_model_id: "model_shared_ab".to_string(),
        scaffold_digest: "scaffold_unique_a".to_string(),
        precedent_set_digest: "precedent_unique_a".to_string(),
        inheritance_root: "lineage_unique_a".to_string(),
        is_propagated_reference: false,
    };
    let obs_b = RawObservation {
        occurrence_id: "occ_b".to_string(),
        generating_model_id: "model_shared_ab".to_string(), // Shares model with A
        scaffold_digest: "scaffold_shared_bc".to_string(),  // Shares scaffold with C
        precedent_set_digest: "precedent_unique_b".to_string(),
        inheritance_root: "lineage_unique_b".to_string(),
        is_propagated_reference: false,
    };
    let obs_c = RawObservation {
        occurrence_id: "occ_c".to_string(),
        generating_model_id: "model_unique_c".to_string(),
        scaffold_digest: "scaffold_shared_bc".to_string(), // Shares scaffold with B
        precedent_set_digest: "precedent_unique_c".to_string(),
        inheritance_root: "lineage_unique_c".to_string(),
        is_propagated_reference: false,
    };

    let result =
        support(&[obs_a, obs_b, obs_c]).expect("support computation on overlap graph must succeed");
    // Maximum independent set of graph (A-B-C) is {A, C}, which has size 2.
    assert_eq!(result["support_count"], 2);
    assert_eq!(
        result["eligible_for_provisional"], false,
        "Support 2 does not meet threshold 3"
    );
}

#[test]
fn test_f_support_03_support_is_feasible_without_relabelling() {
    // Two observations derived from the same sealed receipt
    let obs_base = RawObservation {
        occurrence_id: "occ_orig".to_string(),
        generating_model_id: "model_1".to_string(),
        scaffold_digest: "scaffold_1".to_string(),
        precedent_set_digest: "prec_1".to_string(),
        inheritance_root: "root_1".to_string(),
        is_propagated_reference: false,
    };
    // Caller attempts to fake independence by changing arbitrary string metadata (occurrence_id)
    let obs_relabeled = RawObservation {
        occurrence_id: "occ_relabeled_fake".to_string(),
        generating_model_id: "model_1".to_string(),
        scaffold_digest: "scaffold_1".to_string(),
        precedent_set_digest: "prec_1".to_string(),
        inheritance_root: "root_1".to_string(),
        is_propagated_reference: false,
    };

    let result = support(&[obs_base, obs_relabeled]).expect("support must compute");
    assert_eq!(
        result["support_count"], 1,
        "Relabelled identical receipt keys must not increase support"
    );
}

#[test]
fn test_f_support_04_support_is_monotone() {
    let obs_a = RawObservation {
        occurrence_id: "occ_a".to_string(),
        generating_model_id: "m1".to_string(),
        scaffold_digest: "s1".to_string(),
        precedent_set_digest: "p1".to_string(),
        inheritance_root: "r1".to_string(),
        is_propagated_reference: false,
    };
    let obs_c = RawObservation {
        occurrence_id: "occ_c".to_string(),
        generating_model_id: "m2".to_string(),
        scaffold_digest: "s2".to_string(),
        precedent_set_digest: "p2".to_string(),
        inheritance_root: "r2".to_string(),
        is_propagated_reference: false,
    };
    let initial_support = support(&[obs_a.clone(), obs_c.clone()]).unwrap()["support_count"]
        .as_u64()
        .unwrap();
    assert_eq!(initial_support, 2);

    // Add bridging observation B (correlated with both A and C)
    let obs_b_bridging = RawObservation {
        occurrence_id: "occ_b".to_string(),
        generating_model_id: "m1".to_string(), // shares with A
        scaffold_digest: "s2".to_string(),     // shares with C
        precedent_set_digest: "p3".to_string(),
        inheritance_root: "r3".to_string(),
        is_propagated_reference: false,
    };

    let new_support = support(&[obs_a, obs_c, obs_b_bridging]).unwrap()["support_count"]
        .as_u64()
        .unwrap();
    assert!(
        new_support >= initial_support,
        "Adding observations must be monotone (never decrease support)"
    );
}

#[test]
fn test_f_pharm_01_duplicate_collapse_replays_count_as_one() {
    // 10 replays of the same event (same occurrence_id and keys)
    let replays = vec![
        RawObservation {
            occurrence_id: "occ_single_defect".to_string(),
            generating_model_id: "model_fixed".to_string(),
            scaffold_digest: "scaffold_fixed".to_string(),
            precedent_set_digest: "precedent_fixed".to_string(),
            inheritance_root: "root_fixed".to_string(),
            is_propagated_reference: false,
        };
        10
    ];

    let result = support(&replays).expect("support must compute");
    assert_eq!(result["support_count"], 1);
    assert_eq!(result["eligible_for_provisional"], false);
}

#[test]
fn test_f_res_05_propagated_references_are_never_observations() {
    let inherited_ref = RawObservation {
        occurrence_id: "occ_inherited".to_string(),
        generating_model_id: "model_inherited".to_string(),
        scaffold_digest: "scaffold_inherited".to_string(),
        precedent_set_digest: "prec_inherited".to_string(),
        inheritance_root: "root_inherited".to_string(),
        is_propagated_reference: true, // Propagated reference!
    };

    let err = support(&[inherited_ref]).expect_err("propagated reference must be refused");
    assert_eq!(err.code, "PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION");
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/support_falsifiers_parity.rs
// Claim: urn:core:crates_rs:tests:support-falsifiers-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord086bbf92 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord086bbf92` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError086bbf92 {
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
impl BoundaryError086bbf92 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError086bbf92 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError086bbf92 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord086bbf92 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError086bbf92> {
        if capacity_bound == 0 {
            return Err(BoundaryError086bbf92::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError086bbf92::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError086bbf92::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_086bbf92() {
    let record = BoundaryRecord086bbf92::try_admit(2, 5).unwrap();
    assert_eq!(record.admitted_items(), 2);
    assert_eq!(record.capacity_bound(), 5);
    assert_eq!(record.remaining_capacity(), 3);

    assert_eq!(
        BoundaryRecord086bbf92::try_admit(0, 5).unwrap_err(),
        BoundaryError086bbf92::EmptyAdmission
    );
    assert_eq!(
        BoundaryRecord086bbf92::try_admit(2, 0).unwrap_err(),
        BoundaryError086bbf92::CapacityZero
    );
    assert_eq!(
        BoundaryRecord086bbf92::try_admit(6, 5).unwrap_err(),
        BoundaryError086bbf92::ExceedsCapacity {
            admitted_items: 6,
            capacity_bound: 5
        }
    );
}
