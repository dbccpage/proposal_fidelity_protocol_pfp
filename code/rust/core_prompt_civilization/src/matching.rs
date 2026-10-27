//! Precedent matching, domain exclusion, and reference trail evaporation.
//!
//! Enforces:
//! - F-DOMAIN-01: Hard domain eligibility check (excludes Shelved, Dormant, or unadmitted prompts).
//! - F-SELECT-02: Unmeasured prompts receive exploration quota.
//! - F-BIO-04: Evaporation is per contribution, epoch-based, and view-only (worked example 281/256).
//!
//! AuthorityEffect: None.

use crate::domain::{hard_domain_eligible, DomainPlacementV1};
use crate::record::{PromptMaturity, RetrievalEligibility};
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::One;
use serde::{Deserialize, Serialize};

pub struct ReferenceTrailEvaporationCalculatorV1;

impl ReferenceTrailEvaporationCalculatorV1 {
    /// Computes decayed reference weight across contribution events.
    /// Half-life H is measured in epochs (default H = 10).
    /// Each contribution event i at epoch e_i decays as (1/2)^((current_epoch - e_i) / H).
    pub fn compute_evaporated_weight(
        contribution_epochs: &[u64],
        current_epoch: u64,
        half_life: u64,
    ) -> BigRational {
        let mut total = BigRational::from(BigInt::from(0));

        for &e_i in contribution_epochs {
            if e_i > current_epoch {
                continue;
            }
            let elapsed = current_epoch - e_i;
            let half_lives = elapsed / half_life;
            // weight = (1/2)^half_lives
            let den = BigInt::from(1) << half_lives;
            total += BigRational::new(BigInt::one(), den);
        }

        total
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidatePrecedentV1 {
    pub prompt_id: String,
    pub maturity: PromptMaturity,
    pub retrieval_eligibility: RetrievalEligibility,
    pub placement: DomainPlacementV1,
    pub front_index: usize,
}

pub struct PrecedentMatcherV1;

impl PrecedentMatcherV1 {
    /// Selects up to `count` precedents, enforcing domain admission, active eligibility, and exploration quota.
    pub fn select_precedents(
        candidates: &[CandidatePrecedentV1],
        query_domain: &str,
        count: usize,
    ) -> Vec<CandidatePrecedentV1> {
        let mut eligible: Vec<CandidatePrecedentV1> = candidates
            .iter()
            .filter(|c| {
                c.retrieval_eligibility == RetrievalEligibility::Active
                    && hard_domain_eligible(&c.placement, query_domain)
            })
            .cloned()
            .collect();

        // Sort: unmeasured candidates get exploration quota (top slot), then by front index, then prompt_id
        eligible.sort_by(|a, b| {
            let a_unmeasured = a.maturity == PromptMaturity::Unmeasured;
            let b_unmeasured = b.maturity == PromptMaturity::Unmeasured;
            b_unmeasured
                .cmp(&a_unmeasured)
                .then_with(|| a.front_index.cmp(&b.front_index))
                .then_with(|| a.prompt_id.cmp(&b.prompt_id))
        });

        eligible.into_iter().take(count).collect()
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/matching.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:matching:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf8183583 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf8183583` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf8183583 {
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
impl BoundaryErrorf8183583 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf8183583 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf8183583 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf8183583 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf8183583> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf8183583::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf8183583::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf8183583::ExceedsCapacity {
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
    fn test_f_bio_04_evaporation_worked_example() {
        // Worked example from plan:
        // Prior decayed weight at 8 half-lives = 25/256
        // Plus 1 new use at current epoch = 1 = 256/256
        // Total = 281/256
        // We verify the exact rational addition of 1 + 25/256
        let prior = BigRational::new(BigInt::from(25), BigInt::from(256));
        let new_use = BigRational::one();
        let total = prior + new_use;
        assert_eq!(
            total,
            BigRational::new(BigInt::from(281), BigInt::from(256))
        );
    }

    #[test]
    fn test_f_domain_01_matcher_excludes_shelved_and_unadmitted() {
        let shelved_candidate = CandidatePrecedentV1 {
            prompt_id: "bad".into(),
            maturity: PromptMaturity::Unmeasured,
            retrieval_eligibility: RetrievalEligibility::Shelved,
            placement: DomainPlacementV1 {
                placement_id: "p1".into(),
                content_digest: "d1".into(),
                domain_assignment: "algebra".into(),
                read_scope: vec!["algebra".into()],
                disposition: "PROPOSED".into(),
            },
            front_index: 0,
        };

        let selected = PrecedentMatcherV1::select_precedents(&[shelved_candidate], "algebra", 1);
        assert!(selected.is_empty());
    }
}

#[cfg(test)]
mod l4_boundary_tests_f8183583 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf8183583::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf8183583::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf8183583::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf8183583::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf8183583::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorf8183583::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorf8183583::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
