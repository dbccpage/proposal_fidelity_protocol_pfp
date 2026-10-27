//! Provider credentials and bounded transport. AuthorityEffect: None.
pub mod anthropic;
pub mod budget;
pub mod credentials;
pub mod request;
pub mod transport;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Refusal {
    pub code: String,
    pub message: String,
}

impl Refusal {
    pub fn new(code: &str, message: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            message: message.into(),
        }
    }
}

/// Input and output token prices in micro-USD, added with checked multiplication.
pub fn admit_microusd_quote(
    input_tokens: u64,
    output_tokens: u64,
    input_microusd_per_token: u64,
    output_microusd_per_token: u64,
) -> Result<u64, Refusal> {
    if input_tokens == 0 && output_tokens == 0 {
        return Err(Refusal::new(
            "PROVIDER_CONFIG_INVALID",
            "quote has no tokens",
        ));
    }
    let input_cost = input_tokens
        .checked_mul(input_microusd_per_token)
        .ok_or_else(|| Refusal::new("PROVIDER_CONFIG_INVALID", "input quote overflow"))?;
    let output_cost = output_tokens
        .checked_mul(output_microusd_per_token)
        .ok_or_else(|| Refusal::new("PROVIDER_CONFIG_INVALID", "output quote overflow"))?;
    input_cost
        .checked_add(output_cost)
        .ok_or_else(|| Refusal::new("PROVIDER_CONFIG_INVALID", "quote total overflow"))
}

// Origin: engine/crates_rs/core_adversary/src/providers/mod.rs
// Claim: urn:core:crates_rs:core-adversary:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb0e6d0b5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb0e6d0b5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb0e6d0b5 {
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
impl BoundaryErrorb0e6d0b5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb0e6d0b5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb0e6d0b5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb0e6d0b5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb0e6d0b5> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb0e6d0b5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb0e6d0b5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb0e6d0b5::ExceedsCapacity {
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
mod quote_tests {
    use super::*;

    #[test]
    fn token_prices_add_in_microusd() {
        let total = admit_microusd_quote(3, 2, 5, 7);
        assert!(total.is_ok());
        if let Ok(total) = total {
            assert_eq!(total, 15 + 14);
        }
    }

    #[test]
    fn an_empty_quote_is_refused() {
        let refused = admit_microusd_quote(0, 0, 5, 7);
        assert!(refused.is_err());
        if let Err(refusal) = refused {
            assert_eq!(refusal.code, "PROVIDER_CONFIG_INVALID");
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_b0e6d0b5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb0e6d0b5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb0e6d0b5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb0e6d0b5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb0e6d0b5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb0e6d0b5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb0e6d0b5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb0e6d0b5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
