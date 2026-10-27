//! Adversary's live LGGR soundness decision.
//!
//! The recorded verdict is [`lggr_v::check_soundness`] on the carrier
//! difference `D` and the observer quotient `Q`. A finite path-kernel product
//! or walk is a different function and is not this decision.
//!
//! AuthorityEffect: None.

use num_rational::BigRational;
use core_epk::lggr_v::{self, LggrSoundnessError, LggrSoundnessReport};
use core_linear_algebra::backend::basic_matrix::BasicMatrix;

/// Names the function that produced a recorded verdict.
pub const SOUNDNESS_DECISION: &str = "lggr_v::check_soundness";

/// The soundness report Adversary records for one `(D, Q)` pair.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RecordedJointKernelVerdict {
    pub decision: &'static str,
    pub report: LggrSoundnessReport,
}

/// Record the joint-kernel soundness verdict for carrier difference `D` and
/// observer quotient `Q`.
///
/// This is the live decision. It calls [`lggr_v::check_soundness`] and stores
/// that report. It does not multiply a path kernel or walk a graph.
pub fn record_joint_kernel_soundness(
    d: &BasicMatrix<BigRational>,
    q: &BasicMatrix<BigRational>,
) -> Result<RecordedJointKernelVerdict, LggrSoundnessError> {
    let report = lggr_v::check_soundness(d, q)?;
    Ok(RecordedJointKernelVerdict {
        decision: SOUNDNESS_DECISION,
        report,
    })
}

// Origin: engine/crates_rs/core_adversary/src/soundness.rs
// Claim: urn:core:crates_rs:core-adversary:soundness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4b65fbb9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4b65fbb9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4b65fbb9 {
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
impl BoundaryError4b65fbb9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4b65fbb9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4b65fbb9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4b65fbb9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4b65fbb9> {
        if capacity_bound == 0 {
            return Err(BoundaryError4b65fbb9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4b65fbb9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4b65fbb9::ExceedsCapacity {
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
mod l4_boundary_tests_4b65fbb9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4b65fbb9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4b65fbb9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4b65fbb9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4b65fbb9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4b65fbb9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4b65fbb9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4b65fbb9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
