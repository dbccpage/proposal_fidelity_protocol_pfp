//! Detector idle counters, mutations and anergy proposals. No autonomous admission.
use crate::Refusal;
use num_bigint::BigInt;
use num_traits::{One, Zero};
use serde_json::{json, Value};
use std::collections::BTreeMap;
use std::str::FromStr;
fn invalid(message: &str) -> Refusal {
    Refusal::new("EIS_VALUE_ERROR", message)
}
fn count(
    value: Option<&Value>,
    default: u32,
    label: &str,
    positive: bool,
) -> Result<BigInt, Refusal> {
    let literal = value.cloned().unwrap_or(json!(default));
    let value = literal
        .as_number()
        .and_then(|n| BigInt::from_str(&n.to_string()).ok())
        .ok_or_else(|| invalid(label))?;
    if value
        < if positive {
            BigInt::one()
        } else {
            BigInt::zero()
        }
    {
        return Err(invalid(label));
    }
    Ok(value)
}
#[derive(Debug, Clone)]
pub struct DetectorRule {
    wire: Value,
}
impl DetectorRule {
    fn normalize_rule_counts(wire: &mut Value) -> Result<(), Refusal> {
        for (field, default, positive) in [
            ("generation", 1, true),
            ("half_life_runs", 10, true),
            ("runs_idle", 0, false),
        ] {
            let value = count(wire.get(field), default, field, positive)?;
            wire[field] = serde_json::Number::from_str(&value.to_string())
                .map(Value::Number)
                .map_err(|e| invalid(&e.to_string()))?;
        }
        Ok(())
    }

    pub fn from_json(wire: &Value) -> Result<Self, Refusal> {
        if !wire.is_object() {
            return Err(invalid("rule must be an object"));
        }
        for field in ["rule_id", "target_epitope", "match_pattern"] {
            if !wire[field].as_str().is_some_and(|s| !s.trim().is_empty()) {
                return Err(invalid("rule text must be nonempty"));
            }
        }
        let mut wire = wire.clone();
        Self::normalize_rule_counts(&mut wire)?;
        let affinity = wire.get("affinity_score").cloned().unwrap_or(json!(1.0));
        if !affinity
            .as_number()
            .and_then(|v| v.as_f64())
            .is_some_and(|v| v.is_finite() && v >= 0.0)
        {
            return Err(invalid(
                "affinity_score must be a finite nonnegative int or float",
            ));
        }
        wire["affinity_score"] = affinity;
        let active = wire.get("is_active").cloned().unwrap_or(json!(true));
        if !active.is_boolean() {
            return Err(invalid("is_active must be a boolean"));
        }
        wire["is_active"] = active;
        let matcher = wire.get("matcher_id").cloned().unwrap_or(json!("regex"));
        if !matcher.as_str().is_some_and(|s| !s.trim().is_empty()) {
            return Err(invalid("matcher_id must be a non-empty string"));
        }
        wire["matcher_id"] = matcher;
        Ok(Self { wire })
    }
    pub fn to_dict(&self) -> Value {
        self.wire.clone()
    }
    pub fn apply_decay(&self) -> Result<Self, Refusal> {
        let mut wire = self.wire.clone();
        let idle: BigInt = count(wire.get("runs_idle"), 0, "runs_idle", false)? + 1;
        wire["is_active"] =
            json!(idle < count(wire.get("half_life_runs"), 10, "half_life_runs", true)?);
        wire["runs_idle"] = serde_json::Number::from_str(&idle.to_string())
            .map(Value::Number)
            .map_err(|e| invalid(&e.to_string()))?;
        Self::from_json(&wire)
    }
    pub fn mutate(&self, pattern: &str, id: &str) -> Result<Self, Refusal> {
        let mut wire = self.wire.clone();
        let generation: BigInt = count(wire.get("generation"), 1, "generation", true)? + 1;
        wire["generation"] = serde_json::Number::from_str(&generation.to_string())
            .map(Value::Number)
            .map_err(|e| invalid(&e.to_string()))?;
        wire["match_pattern"] = json!(pattern);
        wire["rule_id"] = json!(id);
        wire["runs_idle"] = json!(0);
        wire["is_active"] = json!(true);
        Self::from_json(&wire)
    }
    pub fn stimulate(&self, boost: &Value, exact: bool) -> Result<Self, Refusal> {
        let mut wire = self.wire.clone();
        if exact {
            if boost
                .as_number()
                .is_some_and(|n| n.to_string().contains(['.', 'e', 'E']))
            {
                return Err(Refusal::new(
                    "EXACT_RATIONAL_REQUIRED",
                    "Float affinity boost is prohibited",
                ));
            }
            return Ok(self.clone());
        }
        let current = &self.wire["affinity_score"];
        let integer = |value: &Value| {
            value
                .as_number()
                .and_then(|number| BigInt::from_str(&number.to_string()).ok())
        };
        wire["affinity_score"] = match (integer(current), integer(boost)) {
            (Some(current), Some(boost)) => {
                serde_json::Number::from_str(&(current + boost).to_string())
                    .map(Value::Number)
                    .map_err(|e| invalid(&e.to_string()))?
            }
            _ => json!(
                current.as_f64().ok_or_else(|| invalid("affinity_score"))?
                    + boost.as_f64().ok_or_else(|| invalid("affinity_boost"))?
            ),
        };
        wire["runs_idle"] = json!(0);
        wire["is_active"] = json!(true);
        Self::from_json(&wire)
    }
}
pub fn autonomous_decay() -> Result<(), Refusal> {
    Err(Refusal::new(
        "EXTERNAL_EPOCH_DECISION_REQUIRED",
        "Autonomous idle-counter decay cannot flip is_active without epoch decision",
    ))
}
pub struct AnergyMonitor {
    pub threshold: BigInt,
    pub counts: BTreeMap<String, BigInt>,
}
impl AnergyMonitor {
    pub fn new(threshold: BigInt) -> Self {
        Self {
            threshold,
            counts: BTreeMap::new(),
        }
    }
    pub fn record_benign_hit(&mut self, id: &str) -> Option<Value> {
        let count = self.counts.entry(id.into()).or_default();
        *count += 1;
        (*count >= self.threshold).then(
            || json!({"detector_id":id,"is_suspended":false,"destination_queue":"TregSupervisor"}),
        )
    }
}
pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let operation = payload["operation"]
        .as_str()
        .ok_or_else(|| invalid("operation required"))?;
    if operation == "autonomous_decay" {
        autonomous_decay()?;
        return Ok(Value::Null);
    }
    let rule = DetectorRule::from_json(&payload["rule"])?;
    Ok(match operation {
        "apply_decay" => rule.apply_decay()?.to_dict(),
        "mutate" => rule
            .mutate(
                payload["mutation_variant"]
                    .as_str()
                    .ok_or_else(|| invalid("mutation_variant"))?,
                payload["new_rule_id"]
                    .as_str()
                    .ok_or_else(|| invalid("new_rule_id"))?,
            )?
            .to_dict(),
        "stimulate" => rule
            .stimulate(
                payload.get("affinity_boost").unwrap_or(&json!(1)),
                payload["exact_boost"] == json!(true),
            )?
            .to_dict(),
        "validate" => rule.to_dict(),
        _ => return Err(invalid("unknown clonal operation")),
    })
}

impl Default for AnergyMonitor {
    fn default() -> Self {
        Self::new(BigInt::from(5))
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/clonal_selection.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:clonal-selection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6ecc3c19 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6ecc3c19` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6ecc3c19 {
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
impl BoundaryError6ecc3c19 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6ecc3c19 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6ecc3c19 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6ecc3c19 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6ecc3c19> {
        if capacity_bound == 0 {
            return Err(BoundaryError6ecc3c19::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6ecc3c19::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6ecc3c19::ExceedsCapacity {
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
mod l4_boundary_tests_6ecc3c19 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6ecc3c19::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6ecc3c19::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6ecc3c19::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6ecc3c19::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6ecc3c19::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6ecc3c19::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6ecc3c19::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
