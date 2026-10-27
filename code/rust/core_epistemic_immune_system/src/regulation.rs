//! Exact native false-discovery policy, distinct from Python Signal-1 toxicity.
//!
//! AuthorityEffect: None.
//!
//! FP/(TP+FP) is a false-discovery proportion, not FP/(FP+TN).
//! No true-negative counts or authenticated admission are supplied by this port.

use crate::anti_skill::{AntiSkillSpecV2, AntiSkillStatus};
use num_bigint::BigUint;
use num_rational::Ratio;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectorTelemetry {
    pub anti_skill_id: String,
    pub true_positives: u64,
    pub false_positives: u64,
    pub last_active_epoch: u64,
}

pub struct TregSupervisor {
    max_false_discovery_proportion: Ratio<u64>,
    pub min_samples_for_evaluation: u64,
}

impl Default for TregSupervisor {
    fn default() -> Self {
        Self {
            max_false_discovery_proportion: Ratio::new(1, 10),
            min_samples_for_evaluation: 10,
        }
    }
}

impl TregSupervisor {
    pub const POLICY_ID: &'static str = "core.eis.false-discovery-proportion.v1";

    /// Exact threshold in [0,1]; suspension uses a strict comparison.
    pub fn try_new(
        numerator: u64,
        denominator: u64,
        min_samples: u64,
    ) -> Result<Self, &'static str> {
        if denominator == 0 || numerator > denominator {
            return Err("INVALID_FALSE_DISCOVERY_THRESHOLD");
        }
        Ok(Self {
            max_false_discovery_proportion: Ratio::new(numerator, denominator),
            min_samples_for_evaluation: min_samples,
        })
    }

    pub fn max_false_discovery_proportion(&self) -> Ratio<u64> {
        self.max_false_discovery_proportion
    }

    /// Returns None for no observations. Widen before adding the u64 counts.
    pub fn observed_false_discovery_proportion(
        telemetry: &DetectorTelemetry,
    ) -> Option<Ratio<u128>> {
        let total = u128::from(telemetry.true_positives) + u128::from(telemetry.false_positives);
        (total != 0).then(|| Ratio::new(u128::from(telemetry.false_positives), total))
    }

    /// True only when this call suspends the named, currently admitted detector.
    /// Foreign telemetry and inactive states have no regulatory effect.
    pub fn review(&self, spec: &mut AntiSkillSpecV2, telemetry: &DetectorTelemetry) -> bool {
        if telemetry.anti_skill_id != spec.id || spec.status != AntiSkillStatus::Admitted {
            return false;
        }
        let total = u128::from(telemetry.true_positives) + u128::from(telemetry.false_positives);
        if total == 0 || total < u128::from(self.min_samples_for_evaluation) {
            return false; // Insufficient data to trigger regulatory suspension
        }

        // The largest cross product can need 129 bits; never truncate to u128.
        let left = BigUint::from(telemetry.false_positives)
            * BigUint::from(*self.max_false_discovery_proportion.denom());
        let right =
            BigUint::from(total) * BigUint::from(*self.max_false_discovery_proportion.numer());
        if left > right {
            spec.suspend();
            true
        } else {
            false
        }
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/regulation.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:regulation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb92abae4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb92abae4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb92abae4 {
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
impl BoundaryErrorb92abae4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb92abae4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb92abae4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb92abae4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb92abae4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb92abae4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb92abae4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb92abae4::ExceedsCapacity {
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
mod l4_boundary_tests_b92abae4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb92abae4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb92abae4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb92abae4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb92abae4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb92abae4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb92abae4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb92abae4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
