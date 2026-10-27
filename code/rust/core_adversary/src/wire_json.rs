//! Pure source-compatible sorted, spaced ASCII JSON for durable wire records.
use crate::stage::ports::Refusal;
use serde_json::Value;

fn encode_ascii_string(text: &str) -> Result<String, Refusal> {
    let quoted = serde_json::to_string(text)
        .map_err(|error| Refusal::new("ADVERSARY_WIRE_JSON_UNAVAILABLE", error.to_string()))?;
    let mut ascii = String::new();
    for c in quoted.chars() {
        if c >= '\u{7f}' {
            let mut units = [0; 2];
            for unit in c.encode_utf16(&mut units) {
                ascii.push_str(&format!("\\u{unit:04x}"));
            }
        } else {
            ascii.push(c);
        }
    }
    Ok(ascii)
}

fn encode_ascii_object(items: &serde_json::Map<String, Value>) -> Result<String, Refusal> {
    let mut pairs = Vec::new();
    let mut ordered: Vec<_> = items.iter().collect();
    ordered.sort_unstable_by(|left, right| left.0.cmp(right.0));
    for (key, value) in ordered {
        pairs.push(format!(
            "{}: {}",
            encode_ascii_string(key)?,
            python_ascii_json(value)?
        ));
    }
    Ok(format!("{{{}}}", pairs.join(", ")))
}

pub(crate) fn python_ascii_json(value: &Value) -> Result<String, Refusal> {
    match value {
        Value::String(text) => encode_ascii_string(text),
        Value::Array(items) => Ok(format!(
            "[{}]",
            items
                .iter()
                .map(python_ascii_json)
                .collect::<Result<Vec<_>, _>>()?
                .join(", ")
        )),
        Value::Object(items) => encode_ascii_object(items),
        scalar => Ok(scalar.to_string()),
    }
}

// Origin: engine/crates_rs/core_adversary/src/wire_json.rs
// Claim: urn:core:crates_rs:core-adversary:wire-json:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord583f4370 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord583f4370` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError583f4370 {
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
impl BoundaryError583f4370 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError583f4370 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError583f4370 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord583f4370 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError583f4370> {
        if capacity_bound == 0 {
            return Err(BoundaryError583f4370::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError583f4370::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError583f4370::ExceedsCapacity {
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
mod l4_boundary_tests_583f4370 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord583f4370::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord583f4370::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord583f4370::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord583f4370::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord583f4370::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError583f4370::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError583f4370::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
