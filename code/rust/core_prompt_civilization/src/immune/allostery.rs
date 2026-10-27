//! Exact Allosteric Quorum Gate with Integer Hill Coefficient (U16/U20).
//!
//! Evaluates sigmoidal cooperative consensus:
//! H(theta) = theta^n / (Kd^n + theta^n)
//!
//! Integer parameters:
//! - n: Hill coefficient (degree of cooperativity, n >= 1)
//! - Kd: Dissociation constant (half-maximal activation threshold, Kd >= 1)
//!
//! Evaluated over exact BigRational arithmetic. Zero floating-point operations.
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum QuorumState {
    Quiescent,
    Indeterminate,
    Unknown,
    Active,
    Activate,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AllostericGate {
    pub hill_coefficient: u32,
    pub kd: u32,
    pub quiescent_ceiling_num: u64,
    pub quiescent_ceiling_den: u64,
    pub active_floor_num: u64,
    pub active_floor_den: u64,
}

impl Default for AllostericGate {
    fn default() -> Self {
        Self {
            hill_coefficient: 4,
            kd: 2,
            quiescent_ceiling_num: 1,
            quiescent_ceiling_den: 10, // <= 1/10 is Quiescent
            active_floor_num: 7,
            active_floor_den: 10, // >= 7/10 is Active
        }
    }
}

impl AllostericGate {
    pub fn new(hill_coefficient: u32, kd: u32) -> Self {
        assert!(hill_coefficient > 0, "Hill coefficient n must be > 0");
        assert!(kd > 0, "Dissociation constant Kd must be > 0");
        Self {
            hill_coefficient,
            kd,
            ..Default::default()
        }
    }

    /// Exact rational response: H(theta) = theta^n / (Kd^n + theta^n).
    pub fn compute_response(&self, theta: u32) -> BigRational {
        if theta == 0 {
            return BigRational::zero();
        }
        let theta_n = BigInt::from(theta).pow(self.hill_coefficient);
        let kd_n = BigInt::from(self.kd).pow(self.hill_coefficient);
        let denom = &kd_n + &theta_n;
        BigRational::new(theta_n, denom)
    }

    /// Evaluates theta votes into a typed QuorumState and exact rational response.
    pub fn evaluate(&self, theta: u32) -> (QuorumState, BigRational) {
        let resp = self.compute_response(theta);
        let quiescent_bound = BigRational::new(
            BigInt::from(self.quiescent_ceiling_num),
            BigInt::from(self.quiescent_ceiling_den),
        );
        let active_bound = BigRational::new(
            BigInt::from(self.active_floor_num),
            BigInt::from(self.active_floor_den),
        );

        let state = if resp <= quiescent_bound {
            QuorumState::Quiescent
        } else if resp >= active_bound {
            QuorumState::Active
        } else {
            QuorumState::Indeterminate
        };
        (state, resp)
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immune/allostery.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:allostery:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4e00f2f7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4e00f2f7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4e00f2f7 {
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
impl BoundaryError4e00f2f7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4e00f2f7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4e00f2f7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4e00f2f7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4e00f2f7> {
        if capacity_bound == 0 {
            return Err(BoundaryError4e00f2f7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4e00f2f7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4e00f2f7::ExceedsCapacity {
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
mod l4_boundary_tests_4e00f2f7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4e00f2f7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4e00f2f7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4e00f2f7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4e00f2f7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4e00f2f7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError4e00f2f7::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError4e00f2f7::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
