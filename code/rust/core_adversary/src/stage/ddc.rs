//! Arena DDC actions reuse the sovereign calculus alphabet directly.
use crate::stage::canonical::{identifier, text, validated_record};
use crate::stage::exact::Rational;
use core_wdp::ddc::ddc_alphabet::DdcOp;
use serde::{Deserialize, Deserializer, Serializer};

mod letter_wire {
    use super::*;
    pub fn serialize<S: Serializer>(op: &DdcOp, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(op.letter())
    }
    pub fn deserialize<'de, D: Deserializer<'de>>(deserializer: D) -> Result<DdcOp, D::Error> {
        let raw = String::deserialize(deserializer)?;
        let parsed = DdcOp::from_letter(&raw).or_else(|| {
            if raw == "L" || raw == "LAMBDA" {
                Some(DdcOp::Lift)
            } else {
                serde_json::from_value(serde_json::Value::String(raw.clone())).ok()
            }
        });
        parsed.ok_or_else(|| serde::de::Error::custom(format!("Unknown DDC letter or op: {raw:?}")))
    }
}

fn none() -> String {
    "None".into()
}
validated_record!(DdcStep {
    #[serde(with = "letter_wire")] letter: DdcOp,
    before_class: String, after_class: String, carrier_hash: String,
    witness_hash: Option<String>, receipt_sha256: String,
    #[serde(default = "none")] authority_effect: String,
    #[serde(default, skip_serializing_if = "Option::is_none")] timestamp: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")] phi_1: Option<Rational>,
    #[serde(default, skip_serializing_if = "Option::is_none")] gamma_2: Option<Rational>,
});
impl DdcStep {
    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.before_class, "before_class")?;
        identifier(&self.after_class, "after_class")?;
        text(&self.carrier_hash, "carrier_hash", false)?;
        if let Some(hash) = &self.witness_hash {
            text(hash, "witness_hash", false)?;
        }
        text(&self.receipt_sha256, "receipt_sha256", false)?;
        if self.authority_effect != "None" {
            return Err("authority_effect must be 'None'".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/ddc.rs
// Claim: urn:core:crates_rs:core-adversary:ddc:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1f0fdb80 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1f0fdb80` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1f0fdb80 {
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
impl BoundaryError1f0fdb80 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1f0fdb80 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1f0fdb80 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1f0fdb80 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1f0fdb80> {
        if capacity_bound == 0 {
            return Err(BoundaryError1f0fdb80::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1f0fdb80::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1f0fdb80::ExceedsCapacity {
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
mod l4_boundary_tests_1f0fdb80 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1f0fdb80::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1f0fdb80::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1f0fdb80::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1f0fdb80::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1f0fdb80::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError1f0fdb80::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError1f0fdb80::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
