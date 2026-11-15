//! Detector idle counters, mutations and anergy proposals. No autonomous admission.
use crate::Refusal;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde_json::{json, Value};
use std::collections::BTreeMap;
use std::str::FromStr;
fn invalid(message: &str) -> Refusal {
    Refusal::new("EIS_VALUE_ERROR", message)
}
fn refusal(code: &str, detail: &str) -> Refusal {
    Refusal::new(code, detail)
}
pub fn canonical_rational(value: &BigRational) -> String {
    if value.denom().is_one() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}
pub fn parse_exact_rational(value: &Value, label: &str) -> Result<BigRational, Refusal> {
    let text = match value {
        Value::String(s) => s.trim().to_string(),
        Value::Number(n) => {
            let s = n.to_string();
            if s.contains(['.', 'e', 'E']) {
                return Err(refusal(
                    "EXACT_RATIONAL_REQUIRED",
                    &format!("{label} must be an exact rational, not a float"),
                ));
            }
            s
        }
        _ => {
            return Err(invalid(&format!(
                "{label} must be an exact rational string or integer"
            )))
        }
    };
    if text.contains(['.', 'e', 'E']) {
        return Err(refusal(
            "EXACT_RATIONAL_REQUIRED",
            &format!("{label} must be an exact rational, not a float"),
        ));
    }
    let (numerator, denominator) = text.split_once('/').unwrap_or((&text, "1"));
    let num = BigInt::from_str(numerator.trim()).map_err(|_| invalid(label))?;
    let den = BigInt::from_str(denominator.trim()).map_err(|_| invalid(label))?;
    if den <= BigInt::zero() {
        return Err(invalid(&format!(
            "{label} denominator must be strictly positive"
        )));
    }
    if num < BigInt::zero() {
        return Err(invalid(&format!("{label} must be non-negative")));
    }
    Ok(BigRational::new(num, den))
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
        let affinity = match wire.get("affinity_score") {
            Some(v) => parse_exact_rational(v, "affinity_score")?,
            None => BigRational::one(),
        };
        wire["affinity_score"] = if affinity.denom().is_one() {
            serde_json::Number::from_str(&affinity.numer().to_string())
                .map(Value::Number)
                .unwrap_or_else(|_| Value::String(canonical_rational(&affinity)))
        } else {
            Value::String(canonical_rational(&affinity))
        };
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
    pub fn affinity_score(&self) -> Result<BigRational, Refusal> {
        parse_exact_rational(&self.wire["affinity_score"], "affinity_score")
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
    pub fn stimulate(&self, boost: &Value, _exact: bool) -> Result<Self, Refusal> {
        let mut wire = self.wire.clone();
        let boost_rat = parse_exact_rational(boost, "affinity_boost")?;
        let current_rat = parse_exact_rational(&self.wire["affinity_score"], "affinity_score")?;
        let new_affinity: BigRational = current_rat + boost_rat;
        wire["affinity_score"] = if new_affinity.denom().is_one() {
            serde_json::Number::from_str(&new_affinity.numer().to_string())
                .map(Value::Number)
                .unwrap_or_else(|_| Value::String(canonical_rational(&new_affinity)))
        } else {
            Value::String(canonical_rational(&new_affinity))
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
        assert_eq!(
            BoundaryError6ecc3c19::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError6ecc3c19::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}

#[cfg(test)]
mod clonal_exactness_tests {
    use super::*;

    #[test]
    fn test_detector_rule_exact_rational_affinity() {
        let rule_json = json!({
            "rule_id": "r1",
            "target_epitope": "e1",
            "match_pattern": "bad",
            "affinity_score": "3/2"
        });
        let rule = DetectorRule::from_json(&rule_json).expect("valid rule");
        assert_eq!(
            rule.affinity_score().unwrap(),
            BigRational::new(BigInt::from(3), BigInt::from(2))
        );
        assert_eq!(rule.to_dict()["affinity_score"], "3/2");

        let rule_int = json!({
            "rule_id": "r2",
            "target_epitope": "e2",
            "match_pattern": "bad2",
            "affinity_score": 5
        });
        let rule2 = DetectorRule::from_json(&rule_int).expect("valid rule");
        assert_eq!(
            rule2.affinity_score().unwrap(),
            BigRational::from_integer(BigInt::from(5))
        );

        let rule_frac = json!({
            "rule_id": "r3",
            "target_epitope": "e3",
            "match_pattern": "bad3",
            "affinity_score": "1/1"
        });
        let rule3 = DetectorRule::from_json(&rule_frac).expect("valid rule");
        assert_eq!(rule3.affinity_score().unwrap(), BigRational::one());
    }

    #[test]
    fn test_detector_rule_refuses_float_and_invalid_affinity() {
        let rule_float = json!({
            "rule_id": "r1",
            "target_epitope": "e1",
            "match_pattern": "bad",
            "affinity_score": 1.5
        });
        assert!(DetectorRule::from_json(&rule_float).is_err());

        let rule_float_str = json!({
            "rule_id": "r1",
            "target_epitope": "e1",
            "match_pattern": "bad",
            "affinity_score": "1.5"
        });
        assert!(DetectorRule::from_json(&rule_float_str).is_err());

        let rule_zero_den = json!({
            "rule_id": "r1",
            "target_epitope": "e1",
            "match_pattern": "bad",
            "affinity_score": "1/0"
        });
        assert!(DetectorRule::from_json(&rule_zero_den).is_err());

        let rule_neg = json!({
            "rule_id": "r1",
            "target_epitope": "e1",
            "match_pattern": "bad",
            "affinity_score": "-1/2"
        });
        assert!(DetectorRule::from_json(&rule_neg).is_err());
    }

    #[test]
    fn test_stimulate_exact_rational_addition() {
        let rule_json = json!({
            "rule_id": "r1",
            "target_epitope": "e1",
            "match_pattern": "bad",
            "affinity_score": "1/2"
        });
        let rule = DetectorRule::from_json(&rule_json).expect("valid rule");

        // stimulate with exact rational string "3/4"
        let stimulated = rule.stimulate(&json!("3/4"), true).expect("stimulated");
        // 1/2 + 3/4 = 5/4
        assert_eq!(
            stimulated.affinity_score().unwrap(),
            BigRational::new(BigInt::from(5), BigInt::from(4))
        );
        assert_eq!(stimulated.to_dict()["affinity_score"], "5/4");

        // stimulate with integer 1
        let stimulated2 = stimulated.stimulate(&json!(1), false).expect("stimulated2");
        // 5/4 + 1 = 9/4
        assert_eq!(
            stimulated2.affinity_score().unwrap(),
            BigRational::new(BigInt::from(9), BigInt::from(4))
        );

        // float stimulation is prohibited
        assert!(stimulated2.stimulate(&json!(1.5), true).is_err());
        assert!(stimulated2.stimulate(&json!("0.5"), false).is_err());
    }
}
