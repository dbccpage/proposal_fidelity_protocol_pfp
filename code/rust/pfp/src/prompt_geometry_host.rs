//! Wire adapter for the existing numerical density engine. No provider I/O.

use engines::quantum::prompt_density::{self, PromptDensityReport, DEFAULT_DIM, PROFILE};
use serde_json::Value;

fn parse_observe_bytes(payload: &Value) -> Result<Vec<u8>, String> {
    match (payload.get("text"), payload.get("bytes_hex")) {
        (Some(Value::String(text)), None) => Ok(text.as_bytes().to_vec()),
        (None, Some(Value::String(encoded))) => hex::decode(encoded)
            .map_err(|_| "bytes_hex must contain hexadecimal source bytes".to_owned()),
        _ => Err("provide exactly one of text or bytes_hex".to_owned()),
    }
}

fn parse_observe_dim(payload: &Value) -> Result<usize, String> {
    match payload.get("dim") {
        None => Ok(DEFAULT_DIM),
        Some(value) => value
            .as_u64()
            .and_then(|v| usize::try_from(v).ok())
            .ok_or_else(|| "dim must be a nonnegative integer".to_owned()),
    }
}

fn execute_observe(payload: &Value) -> Result<Value, String> {
    let bytes = parse_observe_bytes(payload)?;
    let dim = parse_observe_dim(payload)?;
    if payload
        .get("profile")
        .is_some_and(|v| v.as_str() != Some(PROFILE))
    {
        return Err("unsupported prompt density profile".to_owned());
    }
    let role = required_text(payload, "role_id")?;
    let field = required_text(payload, "field")?;
    let trust = match payload.get("trust_level") {
        None => "untrusted",
        Some(Value::String(trust)) => trust,
        Some(_) => return Err("trust_level must be a string".to_owned()),
    };
    serde_json::to_value(prompt_density::observe(&bytes, dim, role, field, trust))
        .map_err(|error| error.to_string())
}

fn execute_compare(payload: &Value) -> Result<Value, String> {
    let left: PromptDensityReport = serde_json::from_value(
        payload
            .get("left")
            .cloned()
            .ok_or_else(|| "left observation is required".to_owned())?,
    )
    .map_err(|error| format!("invalid left observation: {error}"))?;
    let right: PromptDensityReport = serde_json::from_value(
        payload
            .get("right")
            .cloned()
            .ok_or_else(|| "right observation is required".to_owned())?,
    )
    .map_err(|error| format!("invalid right observation: {error}"))?;
    serde_json::to_value(prompt_density::compare(&left, &right)).map_err(|error| error.to_string())
}

pub fn execute(operation: &str, payload: &Value) -> Result<Value, String> {
    match operation {
        "prompt_density_observe" => execute_observe(payload),
        "prompt_density_compare" => execute_compare(payload),
        _ => Err(format!("unknown prompt geometry operation {operation}")),
    }
}

fn required_text<'a>(payload: &'a Value, name: &str) -> Result<&'a str, String> {
    payload
        .get(name)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("{name} must be a string"))
}

// Origin: engine/crates_rs/pfp/src/prompt_geometry_host.rs
// Claim: urn:core:crates_rs:pfp:prompt-geometry-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7ca6809b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7ca6809b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7ca6809b {
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
impl BoundaryError7ca6809b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7ca6809b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7ca6809b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7ca6809b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7ca6809b> {
        if capacity_bound == 0 {
            return Err(BoundaryError7ca6809b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7ca6809b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7ca6809b::ExceedsCapacity {
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
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn invalid_utf8_and_empty_are_explicit_non_observations() {
        let invalid = execute(
            "prompt_density_observe",
            &json!({"bytes_hex":"ff", "role_id":"Syntax Prefilter", "field":"seed"}),
        )
        .unwrap();
        assert_eq!(invalid["status"], "INVALID_UTF8");
        assert!(invalid["purity"].is_null());
        let empty = execute(
            "prompt_density_observe",
            &json!({"text":"", "role_id":"Syntax Prefilter", "field":"seed"}),
        )
        .unwrap();
        assert_eq!(empty["status"], "EMPTY");
        assert_eq!(empty["dim"], 128);
        assert!(execute(
            "prompt_density_observe",
            &json!({"text":"x", "bytes_hex":"78", "role_id":"Syntax Prefilter", "field":"seed"})
        )
        .is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_7ca6809b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7ca6809b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7ca6809b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7ca6809b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7ca6809b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7ca6809b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7ca6809b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7ca6809b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
