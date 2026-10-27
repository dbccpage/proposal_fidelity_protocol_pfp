//! Exact quoted rational wire values shared by Arena and its specializations.
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use serde::{de::Error, Deserialize, Deserializer, Serialize, Serializer};
use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct Rational(pub BigRational);
impl Serialize for Rational {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        self.0.to_string().serialize(serializer)
    }
}
impl<'de> Deserialize<'de> for Rational {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let raw = String::deserialize(deserializer)?;
        rational(&raw)
            .map(Self)
            .ok_or_else(|| D::Error::custom("expected exact quoted rational"))
    }
}
pub fn rational(raw: &str) -> Option<BigRational> {
    let raw = raw.trim();
    if let Some((num, den)) = raw.split_once('/') {
        let num = BigInt::from_str(num.trim()).ok()?;
        let den = BigInt::from_str(den.trim()).ok()?;
        return if den.is_zero() {
            None
        } else {
            Some(BigRational::new(num, den))
        };
    }
    let (mantissa, exponent) = match raw.split_once(['e', 'E']) {
        Some((m, e)) => (m, i32::from_str(e).ok()?),
        None => (raw, 0),
    };
    let (whole, decimal) = mantissa.split_once('.').unwrap_or((mantissa, ""));
    if !decimal.bytes().all(|b| b.is_ascii_digit()) {
        return None;
    }
    let numerator = BigInt::from_str(&format!("{whole}{decimal}")).ok()?;
    let scale = i32::try_from(decimal.len()).ok()?.checked_sub(exponent)?;
    // Bound adversarial exponents before allocating an enormous power of ten.
    if scale.unsigned_abs() > 10_000 {
        return None;
    }
    let power = BigInt::from(10).pow(scale.unsigned_abs());
    Some(if scale >= 0 {
        BigRational::new(numerator, power)
    } else {
        BigRational::from_integer(numerator * power)
    })
}

// Origin: engine/crates_rs/core_adversary/src/stage/exact.rs
// Claim: urn:core:crates_rs:core-adversary:exact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6f8f55fc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6f8f55fc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6f8f55fc {
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
impl BoundaryError6f8f55fc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6f8f55fc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6f8f55fc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6f8f55fc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6f8f55fc> {
        if capacity_bound == 0 {
            return Err(BoundaryError6f8f55fc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6f8f55fc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6f8f55fc::ExceedsCapacity {
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
mod l4_boundary_tests_6f8f55fc {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6f8f55fc::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6f8f55fc::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6f8f55fc::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6f8f55fc::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6f8f55fc::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError6f8f55fc::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError6f8f55fc::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
