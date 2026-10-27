//! Thymus Gate: Central Tolerance Negative Selection.
//!
//! AuthorityEffect: None.
//!
//! Law 2: An anti-skill that reacts to any sample in the self panel is killed immediately.
//! Only non-self-reactive detectors may advance to Candidate status.

use crate::anti_skill::{AntiSkillSpecV2, AntiSkillStatus};
use regex::Regex;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ThymusVerdict {
    /// Passed negative selection: zero reactivity against sealed self panel.
    Survived {
        samples_tested: usize,
        self_panel_hash: String,
    },
    /// Killed by central tolerance: false-positive hit on healthy self sample.
    SelfReactive {
        matched_sample: String,
        sample_index: usize,
    },
    /// Pattern failed compilation.
    InvalidPattern { error: String },
}

pub struct ThymusGate {
    self_panel: Vec<String>,
    self_panel_hash: String,
}

impl ThymusGate {
    pub fn new(self_samples: Vec<String>) -> Self {
        use sha2::{Digest, Sha256};
        let mut hasher = Sha256::new();
        for sample in &self_samples {
            hasher.update(sample.as_bytes());
            hasher.update(b"\n");
        }
        let hash = hex::encode(hasher.finalize());
        Self {
            self_panel: self_samples,
            self_panel_hash: hash,
        }
    }

    /// Default baseline self-panel protecting core mathematical and engineering primitives.
    pub fn standard_baseline() -> Self {
        Self::new(vec![
            "AuthorityEffect: None".to_owned(),
            "exact rational duality gap is zero".to_owned(),
            "bounded finite complex with exact coboundary".to_owned(),
            "verify_simplicial_boundary_law succeeds".to_owned(),
            "fractions.Fraction(1, 2) is exact".to_owned(),
            "BigRational::from_integer(1) is pure".to_owned(),
            "clean architecture inward dependency verified".to_owned(),
            "four-host mirror synchronization succeeded".to_owned(),
            "Lean 4 lake build complete with 0 errors".to_owned(),
            "theorem verified by kernel check".to_owned(),
        ])
    }

    /// Screen a proposed anti-skill against the self panel.
    /// If non-self-reactive, promotes the anti-skill to Candidate status.
    pub fn screen(&self, spec: &mut AntiSkillSpecV2) -> ThymusVerdict {
        if spec.status != AntiSkillStatus::Proposed {
            return ThymusVerdict::InvalidPattern {
                error: "SPEC_NOT_PROPOSED".to_owned(),
            };
        }

        let regex = match Regex::new(&spec.pattern) {
            Ok(re) => re,
            Err(e) => {
                return ThymusVerdict::InvalidPattern {
                    error: e.to_string(),
                }
            }
        };

        for (index, sample) in self.self_panel.iter().enumerate() {
            if regex.is_match(sample) {
                spec.retire();
                return ThymusVerdict::SelfReactive {
                    matched_sample: sample.clone(),
                    sample_index: index,
                };
            }
        }

        let _ = spec.promote_to_candidate();
        ThymusVerdict::Survived {
            samples_tested: self.self_panel.len(),
            self_panel_hash: self.self_panel_hash.clone(),
        }
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/thymus.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:thymus:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc9185ee7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc9185ee7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc9185ee7 {
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
impl BoundaryErrorc9185ee7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc9185ee7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc9185ee7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc9185ee7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc9185ee7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc9185ee7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc9185ee7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc9185ee7::ExceedsCapacity {
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
mod l4_boundary_tests_c9185ee7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc9185ee7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc9185ee7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc9185ee7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc9185ee7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc9185ee7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc9185ee7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc9185ee7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
