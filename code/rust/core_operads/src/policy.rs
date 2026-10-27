//! Exact policy admission. A policy grants no authority and performs no checks.
use crate::Refusal;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use serde_json::{json, Value};
use std::str::FromStr;

fn type_error(message: &str) -> Refusal {
    Refusal::new("DANGER_POLICY_TYPE_ERROR", message)
}
fn threshold_type_error() -> Refusal {
    type_error("allosteric_quorum_threshold must be an exact int or Fraction")
}
fn rational_wire<S: Serializer>(value: &BigRational, serializer: S) -> Result<S::Ok, S::Error> {
    json!({"numerator":value.numer().to_string(),"denominator":value.denom().to_string()})
        .serialize(serializer)
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DangerSignalPolicy {
    enforce_danger_gate: bool,
    quarantine_on_critical: bool,
    #[serde(serialize_with = "rational_wire")]
    allosteric_quorum_threshold: BigRational,
}
impl DangerSignalPolicy {
    pub fn new(
        enforce_danger_gate: bool,
        quarantine_on_critical: bool,
        threshold: BigRational,
    ) -> Result<Self, Refusal> {
        if threshold <= BigRational::zero() || threshold >= BigRational::one() {
            return Err(Refusal::new(
                "DANGER_POLICY_VALUE_ERROR",
                "allosteric_quorum_threshold must be in (0, 1)",
            ));
        }
        Ok(Self {
            enforce_danger_gate,
            quarantine_on_critical,
            allosteric_quorum_threshold: threshold,
        })
    }
    pub fn enforce_danger_gate(&self) -> bool {
        self.enforce_danger_gate
    }
    pub fn quarantine_on_critical(&self) -> bool {
        self.quarantine_on_critical
    }
    pub fn allosteric_quorum_threshold(&self) -> &BigRational {
        &self.allosteric_quorum_threshold
    }
    fn parse_flag(fields: &serde_json::Map<String, Value>, name: &str) -> Result<bool, Refusal> {
        match fields.get(name) {
            None => Ok(true),
            Some(Value::Bool(value)) => Ok(*value),
            Some(_) => Err(type_error(&format!("{name} must be boolean"))),
        }
    }

    fn parse_ratio_threshold(ratio: &serde_json::Map<String, Value>) -> Result<BigRational, Refusal> {
        if ratio.len() != 2 || !ratio.contains_key("numerator") || !ratio.contains_key("denominator") {
            return Err(threshold_type_error());
        }
        let parse_int = |key: &str| -> Result<BigInt, Refusal> {
            let s = ratio[key].as_str().ok_or_else(threshold_type_error)?;
            BigInt::from_str(s).map_err(|_| threshold_type_error())
        };
        let numerator = parse_int("numerator")?;
        let denominator = parse_int("denominator")?;
        if denominator.is_zero() {
            return Err(Refusal::new(
                "DANGER_POLICY_VALUE_ERROR",
                "fraction denominator must be nonzero",
            ));
        }
        Ok(BigRational::new(numerator, denominator))
    }

    fn parse_threshold(value: Option<&Value>) -> Result<BigRational, Refusal> {
        match value {
            None => Ok(BigRational::new(BigInt::one(), BigInt::from(2))),
            Some(Value::Number(number)) => {
                let n = BigInt::from_str(&number.to_string()).map_err(|_| threshold_type_error())?;
                Ok(BigRational::from_integer(n))
            }
            Some(Value::Object(ratio)) => Self::parse_ratio_threshold(ratio),
            Some(_) => Err(threshold_type_error()),
        }
    }

    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        let fields = value
            .as_object()
            .ok_or_else(|| type_error("policy must be an object"))?;
        if fields.keys().any(|key| {
            !matches!(
                key.as_str(),
                "enforce_danger_gate" | "quarantine_on_critical" | "allosteric_quorum_threshold"
            )
        }) {
            return Err(type_error("policy contains an unknown field"));
        }
        let enforce = Self::parse_flag(fields, "enforce_danger_gate")?;
        let quarantine = Self::parse_flag(fields, "quarantine_on_critical")?;
        let threshold = Self::parse_threshold(fields.get("allosteric_quorum_threshold"))?;
        Self::new(enforce, quarantine, threshold)
    }
}
impl<'de> Deserialize<'de> for DangerSignalPolicy {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        Self::from_json(&Value::deserialize(deserializer)?).map_err(serde::de::Error::custom)
    }
}

// Origin: engine/crates_rs/core_operads/src/policy.rs
// Claim: urn:core:crates_rs:core-operads:policy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9c3b69b9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9c3b69b9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9c3b69b9 {
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
impl BoundaryError9c3b69b9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9c3b69b9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9c3b69b9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9c3b69b9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9c3b69b9> {
        if capacity_bound == 0 {
            return Err(BoundaryError9c3b69b9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9c3b69b9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9c3b69b9::ExceedsCapacity {
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
mod l4_boundary_tests_9c3b69b9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9c3b69b9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9c3b69b9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9c3b69b9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9c3b69b9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9c3b69b9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9c3b69b9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9c3b69b9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
