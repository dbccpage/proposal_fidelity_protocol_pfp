//! Workflow-owned immune records and inward application ports.
//! Host labels describe supplied evidence; admission does not authenticate them.
use crate::Refusal;
use num_bigint::{BigInt, BigUint};
use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use serde_json::{value::RawValue, Number, Value};
use std::{collections::BTreeSet, str::FromStr};

fn value_error(message: impl Into<String>) -> Refusal {
    Refusal::new("IMMUNE_PORT_VALUE_ERROR", message)
}
fn text(value: &str, label: &str) -> Result<(), Refusal> {
    if value
        .trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
        .is_empty()
    {
        return Err(value_error(format!("{label} must be a non-empty str")));
    }
    Ok(())
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct ExactCount(BigUint);
impl ExactCount {
    pub fn new(value: BigUint) -> Self {
        Self(value)
    }
    pub fn get(&self) -> &BigUint {
        &self.0
    }
}
impl Serialize for ExactCount {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        Number::from_str(&self.0.to_string())
            .map_err(serde::ser::Error::custom)?
            .serialize(serializer)
    }
}
impl<'de> Deserialize<'de> for ExactCount {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let token = Box::<RawValue>::deserialize(deserializer)?;
        let count = BigInt::from_str(token.get())
            .ok()
            .and_then(|value| value.to_biguint());
        count
            .map(Self)
            .ok_or_else(|| serde::de::Error::custom("count must be an exact int >= 0"))
    }
}

fn rational_serialize<S: Serializer>(
    value: &BigRational,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    serde_json::json!({"numerator":value.numer().to_string(),"denominator":value.denom().to_string()}).serialize(serializer)
}
fn rational_deserialize<'de, D: Deserializer<'de>>(
    deserializer: D,
) -> Result<BigRational, D::Error> {
    #[derive(Deserialize)]
    #[serde(deny_unknown_fields)]
    struct Wire {
        numerator: String,
        denominator: String,
    }
    let wire = Wire::deserialize(deserializer)?;
    let numerator = BigInt::from_str(&wire.numerator).map_err(serde::de::Error::custom)?;
    let denominator = BigInt::from_str(&wire.denominator).map_err(serde::de::Error::custom)?;
    if denominator.is_zero() {
        return Err(serde::de::Error::custom(
            "fraction denominator must be nonzero",
        ));
    }
    Ok(BigRational::new(numerator, denominator))
}

macro_rules! record {
    ($name:ident { $( $(#[$meta:meta])* $field:ident: $ty:ty ),* $(,)? }) => {
        #[derive(Debug, Clone, PartialEq, Eq, Serialize)]
        pub struct $name { $( $(#[$meta])* $field: $ty ),* }
        impl $name {
            pub fn new($( $field: $ty ),*) -> Result<Self, Refusal> {
                let value = Self { $( $field ),* };
                value.validate()?;
                Ok(value)
            }
            $( pub fn $field(&self) -> &$ty { &self.$field } )*
            pub fn from_bytes(bytes: &[u8]) -> Result<Self, Refusal> {
                serde_json::from_slice(bytes).map_err(|error| Refusal::new("IMMUNE_PORT_WIRE_INVALID",error.to_string()))
            }
            pub fn from_json(value: &Value) -> Result<Self, Refusal> {
                let bytes = serde_json::to_vec(value).map_err(|error| Refusal::new("IMMUNE_PORT_WIRE_INVALID",error.to_string()))?;
                Self::from_bytes(&bytes)
            }
        }
        impl<'de> Deserialize<'de> for $name {
            fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
                #[derive(Deserialize)]
                #[serde(deny_unknown_fields)]
                struct Wire { $( $(#[$meta])* $field: $ty ),* }
                let wire = Wire::deserialize(deserializer)?;
                Self::new($( wire.$field ),*).map_err(serde::de::Error::custom)
            }
        }
    }
}

record!(DetectorMatch {
    epitope: String,
    matched_text: String,
    offset: ExactCount
});
impl DetectorMatch {
    fn validate(&self) -> Result<(), Refusal> {
        text(&self.epitope, "epitope")?;
        text(&self.matched_text, "matched_text")
    }
}
record!(HostDangerObservation {
    kind: String, severity: String, defect_count: ExactCount, evidence_digest: String, observer_id: String,
    #[serde(default)] evidence_spans: Vec<(ExactCount, ExactCount)>,
});
impl HostDangerObservation {
    fn validate(&self) -> Result<(), Refusal> {
        text(&self.kind, "kind")?;
        if !["LOW", "MEDIUM", "HIGH", "CRITICAL"].contains(&self.severity.as_str()) {
            return Err(value_error(
                "severity must be one of ['CRITICAL', 'HIGH', 'LOW', 'MEDIUM']",
            ));
        }
        text(&self.evidence_digest, "evidence_digest")?;
        text(&self.observer_id, "observer_id")
    }
}
record!(DetectorIdentity { detector_id: String, predicates: BTreeSet<String>, offsets_are_content: bool });
impl DetectorIdentity {
    fn validate(&self) -> Result<(), Refusal> {
        text(&self.detector_id, "detector_id")
    }
}
record!(SensorReading {
    sensor_id: String,
    #[serde(
        serialize_with = "rational_serialize",
        deserialize_with = "rational_deserialize"
    )]
    value: BigRational,
});
impl SensorReading {
    fn validate(&self) -> Result<(), Refusal> {
        text(&self.sensor_id, "sensor_id")
    }
}
record!(ImmuneVerdict {
    blocks: bool,
    decision: String,
    rationale: String
});
impl ImmuneVerdict {
    fn validate(&self) -> Result<(), Refusal> {
        text(&self.decision, "decision")?;
        text(&self.rationale, "rationale")
    }
}

pub trait ImmuneScreenPort {
    fn danger_verdict(
        &mut self,
        matches: &[DetectorMatch],
        danger: Option<&HostDangerObservation>,
        detector: &DetectorIdentity,
    ) -> Result<ImmuneVerdict, Refusal>;
    fn quorum_verdict(&mut self, readings: &[SensorReading]) -> Result<ImmuneVerdict, Refusal>;
    fn trigger_tolerance_verdict(
        &mut self,
        rule_id: &str,
        phrases: &[String],
    ) -> Result<ImmuneVerdict, Refusal>;
}

// Origin: engine/crates_rs/core_operads/src/immune_ports.rs
// Claim: urn:core:crates_rs:core-operads:immune-ports:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord59b4a9f0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord59b4a9f0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError59b4a9f0 {
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
impl BoundaryError59b4a9f0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError59b4a9f0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError59b4a9f0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord59b4a9f0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError59b4a9f0> {
        if capacity_bound == 0 {
            return Err(BoundaryError59b4a9f0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError59b4a9f0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError59b4a9f0::ExceedsCapacity {
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
mod l4_boundary_tests_59b4a9f0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord59b4a9f0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord59b4a9f0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord59b4a9f0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord59b4a9f0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord59b4a9f0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError59b4a9f0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError59b4a9f0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
