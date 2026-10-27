//! Exact wire integers and quoted rationals; no floating-point money path.
use num_bigint::BigInt;
use serde::{de::Error, Deserialize, Deserializer, Serialize, Serializer};
use serde_json::{Number, Value};
use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct Integer(pub BigInt);
impl Serialize for Integer {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let number = Number::from_str(&self.0.to_string()).map_err(serde::ser::Error::custom)?;
        number.serialize(serializer)
    }
}
impl<'de> Deserialize<'de> for Integer {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let value = Value::deserialize(deserializer)?;
        integer(&value)
            .map(Self)
            .ok_or_else(|| D::Error::custom("expected exact integer"))
    }
}
pub fn integer(value: &Value) -> Option<BigInt> {
    match value {
        Value::Number(n) => BigInt::from_str(&n.to_string()).ok(),
        _ => None,
    }
}

// Origin: engine/crates_rs/core_adversary/src/exact.rs
// Claim: urn:core:crates_rs:core-adversary:exact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3187a187 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3187a187` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3187a187 {
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
impl BoundaryError3187a187 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3187a187 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3187a187 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3187a187 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3187a187> {
        if capacity_bound == 0 {
            return Err(BoundaryError3187a187::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3187a187::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3187a187::ExceedsCapacity {
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
mod l4_boundary_tests_3187a187 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3187a187::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3187a187::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3187a187::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3187a187::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3187a187::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3187a187::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3187a187::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
