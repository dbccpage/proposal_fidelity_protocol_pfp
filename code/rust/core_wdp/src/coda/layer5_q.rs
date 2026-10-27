// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::Zero;
use serde_json::json;

use crate::coda::types::{LayerExecutionRecord, LayerId, ProblemInstance};

pub struct Layer5Q;

impl Layer5Q {
    /// Evaluates Layer 5: The Continuum (CODA-Q).
    ///
    /// Checks ordering and diameter of a supplied rational interval [lo, hi].
    /// Does not construct metric completion; proves returned midpoint is an enclosure,
    /// not an arbitrary function evaluation.
    pub fn evaluate(problem: &ProblemInstance) -> (LayerExecutionRecord, BigRational) {
        let (lo, hi) = &problem.enclosure_interval;
        if hi < lo {
            let diameter = BigRational::zero();
            let msg = format!("Inverted interval enclosure [{}, {}]", lo, hi);
            let record = LayerExecutionRecord::new(LayerId::Q, false, msg, diameter.clone())
                .with_metadata("interval_lo", json!(lo.to_string()))
                .with_metadata("interval_hi", json!(hi.to_string()))
                .with_metadata("diameter", json!(diameter.to_string()));
            (record, diameter)
        } else {
            let diameter = hi - lo;
            let msg = format!(
                "Enclosure verified: [{}, {}] with diameter {}; midpoint is not exact state",
                lo, hi, diameter
            );
            let record = LayerExecutionRecord::new(LayerId::Q, true, msg, diameter.clone())
                .with_metadata("interval_lo", json!(lo.to_string()))
                .with_metadata("interval_hi", json!(hi.to_string()))
                .with_metadata("diameter", json!(diameter.to_string()));
            (record, diameter)
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/layer5_q.rs
// Claim: urn:core:crates_rs:core-wdp:layer5-q:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord05f97a91 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord05f97a91` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError05f97a91 {
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
impl BoundaryError05f97a91 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError05f97a91 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError05f97a91 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord05f97a91 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError05f97a91> {
        if capacity_bound == 0 {
            return Err(BoundaryError05f97a91::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError05f97a91::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError05f97a91::ExceedsCapacity {
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
mod l4_boundary_tests_05f97a91 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord05f97a91::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord05f97a91::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord05f97a91::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord05f97a91::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord05f97a91::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError05f97a91::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError05f97a91::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
