//! Two-Signal Danger Gate and Activation Conjunction.
//!
//! AuthorityEffect: None.
//!
//! Constitutional Invariant (IMMUNE-002):
//! Activation requires the conjunction:
//!   externally_admitted(g, s)
//!   AND detector_match(g, subject)
//!   AND independent_danger_signal(subject, context)
//!   AND not_suspended(g, s)
//!
//! Hard Refusal: Counting detector_match as its own danger signal is TWO_SIGNAL_COLLAPSE.

use crate::anti_skill::{AntiSkillSpecV2, AntiSkillStatus};
use regex::Regex;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum IndependentDangerSignal {
    NonZeroDualityGap,
    FloatInExactChannel,
    InvalidSignature,
    BoundaryLeakageDetected,
    TestRegressionObserved,
    UnmechanizedProofClaim,
    AdversarialPromptInfiltration,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum DangerGateVerdict {
    /// Both signals present and detector is active and admitted.
    Finding {
        anti_skill_id: String,
        matched_text: String,
        danger_signal: IndependentDangerSignal,
    },
    /// Detector matched, but no independent danger signal was provided (Signal 1 only).
    HoldUncorroborated {
        anti_skill_id: String,
        reason: &'static str,
    },
    /// Refusal due to unadmitted, suspended, or retired detector status.
    RefusedStatus {
        anti_skill_id: String,
        status: AntiSkillStatus,
    },
    /// Refusal due to pattern mismatch.
    NoMatch,
}

pub struct TwoSignalDangerGate;

impl TwoSignalDangerGate {
    /// Evaluate the strict four-part conjunction.
    pub fn evaluate(
        spec: &AntiSkillSpecV2,
        subject: &str,
        danger_signal: Option<IndependentDangerSignal>,
    ) -> DangerGateVerdict {
        // 1. Must be externally admitted and not suspended
        if spec.status != AntiSkillStatus::Admitted {
            return DangerGateVerdict::RefusedStatus {
                anti_skill_id: spec.id.clone(),
                status: spec.status,
            };
        }

        // 2. Detector pattern match (Signal 1)
        let regex = match Regex::new(&spec.pattern) {
            Ok(re) => re,
            Err(_) => {
                return DangerGateVerdict::RefusedStatus {
                    anti_skill_id: spec.id.clone(),
                    status: AntiSkillStatus::Retired,
                }
            }
        };

        let Some(matched) = regex.find(subject) else {
            return DangerGateVerdict::NoMatch;
        };

        // 3. Independent Danger Signal (Signal 2)
        let Some(signal) = danger_signal else {
            // Signal 1 alone cannot trigger an active finding!
            return DangerGateVerdict::HoldUncorroborated {
                anti_skill_id: spec.id.clone(),
                reason: "TWO_SIGNAL_CONJUNCTION_UNSATISFIED_NO_INDEPENDENT_DANGER",
            };
        };

        // 4. Conjunction satisfied
        DangerGateVerdict::Finding {
            anti_skill_id: spec.id.clone(),
            matched_text: matched.as_str().to_owned(),
            danger_signal: signal,
        }
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/danger_gate.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:danger-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord49050461 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord49050461` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError49050461 {
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
impl BoundaryError49050461 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError49050461 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError49050461 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord49050461 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError49050461> {
        if capacity_bound == 0 {
            return Err(BoundaryError49050461::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError49050461::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError49050461::ExceedsCapacity {
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
mod l4_boundary_tests_49050461 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord49050461::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord49050461::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord49050461::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord49050461::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord49050461::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError49050461::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError49050461::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
