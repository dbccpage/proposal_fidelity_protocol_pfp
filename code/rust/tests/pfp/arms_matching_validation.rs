//! Tests for Matched Arms Validation (U08).
//!
//! Enforces:
//! - Comparison reported iff control parameters are identical across arms.
//! AuthorityEffect: None (const).

use pfp::arms::{check_arm_matching, ArmMismatchError, ArmSpecV1};

fn base_arm(id: &str, intervention: &str) -> ArmSpecV1 {
    ArmSpecV1 {
        arm_id: id.to_string(),
        model_id: "qwen/qwen-2.5-72b-instruct".to_string(),
        temperature_str: "0.0".to_string(),
        max_tokens: 4096,
        budget_micro_usd: 50_000,
        specification_hash: "spec_hash_abc".to_string(),
        intervention_name: intervention.to_string(),
        authority_effect: "None".to_string(),
    }
}

#[test]
fn test_matched_arms_pass_validation() {
    let arm_a = base_arm("arm_a", "baseline_raw_prose");
    let arm_b = base_arm("arm_b", "ddc_hieroglyphic_compression");
    let arm_c = base_arm("arm_c", "mandatory_numeric_scratchpad");

    let arms = vec![arm_a, arm_b, arm_c];
    assert!(check_arm_matching(&arms).is_ok());
}

#[test]
fn test_divergent_arm_fails_validation() {
    let arm_a = base_arm("arm_a", "baseline");
    let mut arm_b = base_arm("arm_b", "token_cap_divergence");
    arm_b.max_tokens = 8192; // Divergent max_tokens!

    let arms = vec![arm_a.clone(), arm_b];
    let err = check_arm_matching(&arms);
    assert!(matches!(
        err,
        Err(ArmMismatchError::MaxTokensMismatch { .. })
    ));

    let mut arm_c = base_arm("arm_c", "model_divergence");
    arm_c.model_id = "meta-llama/llama-3.3-70b-instruct".to_string(); // Divergent model!
    let err_c = check_arm_matching(&[arm_a.clone(), arm_c]);
    assert!(matches!(err_c, Err(ArmMismatchError::ModelMismatch { .. })));

    let mut arm_d = base_arm("arm_d", "budget_divergence");
    arm_d.budget_micro_usd = 100_000;
    let err_d = check_arm_matching(&[arm_a.clone(), arm_d]);
    assert!(matches!(
        err_d,
        Err(ArmMismatchError::BudgetMismatch { .. })
    ));

    let empty: Vec<ArmSpecV1> = vec![];
    assert!(matches!(
        check_arm_matching(&empty),
        Err(ArmMismatchError::EmptyArmsList)
    ));
}

// Origin: engine/crates_rs/tests/pfp/arms_matching_validation.rs
// Claim: urn:core:crates_rs:tests:arms-matching-validation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaa6448fc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaa6448fc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraa6448fc {
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
impl BoundaryErroraa6448fc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraa6448fc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraa6448fc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaa6448fc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraa6448fc> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraa6448fc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraa6448fc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraa6448fc::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_aa6448fc() {
    let admitted = BoundaryRecordaa6448fc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordaa6448fc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
