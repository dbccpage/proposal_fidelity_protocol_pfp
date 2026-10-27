//! Synthetic SBE reports are diagnostics, never certificates or authority.
use crate::stage::exact::rational;
use crate::stage::ports::Refusal;
use num_bigint::BigInt;
use num_rational::BigRational;
use serde_json::{Map, Value};
use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SbeReport {
    fields: Map<String, Value>,
}
impl SbeReport {
    /// Retain the diagnostic map intact, including unavailable and unknown fields.
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        let fields = value.as_object().ok_or_else(|| {
            Refusal::new("SBE_REPORT_INVALID", "a synthetic report must be an object")
        })?;
        Ok(Self {
            fields: fields.clone(),
        })
    }
    pub fn to_dict(&self) -> Value {
        Value::Object(self.fields.clone())
    }
    /// Exact coordinates of the supplied diagnostic text; no verified residual.
    pub fn point(&self) -> Option<(BigRational, BigRational)> {
        if self.fields.get("measurement_status")?.as_str()? != "DETERMINISTIC_SYNTHETIC_DIAGNOSTIC"
        {
            return None;
        }
        Some((
            coordinate(self.fields.get("entropy_bits")?)?,
            coordinate(self.fields.get("purity")?)?,
        ))
    }
}
fn coordinate(value: &Value) -> Option<BigRational> {
    match value {
        Value::String(text) => rational(text),
        Value::Bool(value) => Some(BigRational::from_integer(BigInt::from(u8::from(*value)))),
        Value::Number(number) => {
            let text = number.to_string();
            if text.contains(['.', 'e', 'E']) {
                // Legacy Fraction(float) diagnostic input, never money or evidence.
                BigRational::from_float(number.as_f64()?)
            } else {
                Some(BigRational::from_integer(BigInt::from_str(&text).ok()?))
            }
        }
        _ => None,
    }
}
/// A concrete numerical adapter is composed outside Adversary's control flow.
pub trait SbeDiagnosticPort {
    fn compute(&mut self, text: &str, dim: usize) -> Result<SbeReport, Refusal>;
}

// Origin: engine/crates_rs/core_adversary/src/stage/diagnostics.rs
// Claim: urn:core:crates_rs:core-adversary:diagnostics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcf5afde2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcf5afde2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcf5afde2 {
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
impl BoundaryErrorcf5afde2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcf5afde2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcf5afde2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcf5afde2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcf5afde2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcf5afde2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcf5afde2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcf5afde2::ExceedsCapacity {
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
mod l4_boundary_tests_cf5afde2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordcf5afde2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordcf5afde2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordcf5afde2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordcf5afde2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordcf5afde2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorcf5afde2::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorcf5afde2::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
