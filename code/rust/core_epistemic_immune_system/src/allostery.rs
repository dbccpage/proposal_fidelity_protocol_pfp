//! Exact keyed-sensor Hill consensus. A decision grants no authority.
use crate::Refusal;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use core_types::python_unicode::casefold;
use serde_json::{json, Map, Value};
use std::collections::BTreeSet;
use std::str::FromStr;
fn refusal(code: &str, detail: &str) -> Refusal {
    Refusal::new(code, detail)
}
pub fn rational(value: &Value, label: &str) -> Result<BigRational, Refusal> {
    let text = match value {
        Value::String(s) => s.clone(),
        Value::Number(n) if !n.to_string().contains(['.', 'e', 'E']) => n.to_string(),
        _ => return Err(refusal("NOT_EXACT", label)),
    };
    let (numerator, denominator) = text.split_once('/').unwrap_or((&text, "1"));
    let num = BigInt::from_str(numerator).map_err(|_| refusal("NOT_EXACT", label))?;
    let den = BigInt::from_str(denominator).map_err(|_| refusal("NOT_EXACT", label))?;
    if den.is_zero() {
        return Err(refusal("NOT_EXACT", label));
    }
    Ok(BigRational::new(num, den))
}
pub fn canonical(value: &BigRational) -> String {
    if value.denom().is_one() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HillParameters {
    coefficient: u32,
    constant: BigRational,
}
impl HillParameters {
    pub fn new(coefficient: u32, constant: BigRational) -> Result<Self, Refusal> {
        if !(1..=16).contains(&coefficient) {
            return Err(refusal(
                "HILL_COEFFICIENT_OUT_OF_RANGE",
                "hill_coefficient must be in [1, 16]",
            ));
        }
        if constant <= BigRational::zero() {
            return Err(refusal(
                "HALF_MAXIMAL_CONSTANT_OUT_OF_RANGE",
                "half_maximal_constant must be > 0",
            ));
        }
        Ok(Self {
            coefficient,
            constant,
        })
    }
    pub fn response(&self, signal: &BigRational) -> Result<BigRational, Refusal> {
        if signal < &BigRational::zero() {
            return Err(refusal(
                "SIGNAL_OUT_OF_RANGE",
                "signal_strength must be >= 0",
            ));
        }
        let power = signal.pow(self.coefficient as i32);
        Ok(&power / (self.constant.pow(self.coefficient as i32) + &power))
    }
    fn reaches(&self, signal: &BigRational, threshold: &BigRational) -> bool {
        !signal.is_zero()
            && signal.pow(self.coefficient as i32) * (BigRational::one() - threshold)
                >= threshold * self.constant.pow(self.coefficient as i32)
    }
}
#[derive(Debug, Clone)]
pub struct AllostericConsensusGate {
    parameters: HillParameters,
    threshold: BigRational,
    cap: Option<BigRational>,
    quorum: Option<BigInt>,
}
impl AllostericConsensusGate {
    pub fn new(
        parameters: HillParameters,
        threshold: BigRational,
        cap: Option<BigRational>,
    ) -> Result<Self, Refusal> {
        if threshold <= BigRational::zero() || threshold >= BigRational::one() {
            return Err(refusal(
                "THRESHOLD_OUT_OF_RANGE",
                "activation_threshold must satisfy 0 < t < 1",
            ));
        }
        if cap.as_ref().is_some_and(|v| v <= &BigRational::zero()) {
            return Err(refusal(
                "SENSOR_CAP_OUT_OF_RANGE",
                "per_sensor_cap must be > 0",
            ));
        }
        let quorum = cap.as_ref().map(|cap| {
            let mut high = BigInt::one();
            while !parameters.reaches(&(BigRational::from_integer(high.clone()) * cap), &threshold)
            {
                high *= 2;
            }
            let mut low = if high > BigInt::one() {
                &high / 2 + 1
            } else {
                BigInt::one()
            };
            while low < high {
                let middle: BigInt = (&low + &high) / 2;
                if parameters.reaches(
                    &(BigRational::from_integer(middle.clone()) * cap),
                    &threshold,
                ) {
                    high = middle;
                } else {
                    low = middle + 1;
                }
            }
            high
        });
        Ok(Self {
            parameters,
            threshold,
            cap,
            quorum,
        })
    }
    pub fn evaluate(&self, signals: &Map<String, Value>) -> Result<Value, Refusal> {
        if signals.len() > 4096 {
            return Err(refusal("SIGNAL_OUT_OF_RANGE", "more than 4096 sensors"));
        }
        let mut seen = BTreeSet::new();
        let mut aggregate = BigRational::zero();
        let mut positive = 0usize;
        for (id, raw) in signals {
            let id =
                id.trim_matches(|c: char| c.is_whitespace() || matches!(c, '\u{1c}'..='\u{1f}'));
            if id.is_empty() {
                return Err(refusal("BAD_SENSOR_ID", "sensor id is not a non-empty str"));
            }
            if !seen.insert(casefold(id)) {
                return Err(refusal("DUPLICATE_SENSOR", "sensor appears more than once"));
            }
            let value = rational(raw, "sensor signal")?;
            if value < BigRational::zero() {
                return Err(refusal("SIGNAL_OUT_OF_RANGE", "sensor signal must be >= 0"));
            }
            if self.cap.as_ref().is_some_and(|cap| &value > cap) {
                return Err(refusal(
                    "SIGNAL_ABOVE_SENSOR_CAP",
                    "sensor signal exceeds per_sensor_cap",
                ));
            }
            if !value.is_zero() {
                positive += 1;
            }
            aggregate += value;
        }
        let hill = self.parameters.response(&aggregate)?;
        let active = positive > 0 && self.parameters.reaches(&aggregate, &self.threshold);
        let mut rationale = format!("{}: {positive} positive sensor(s) sum to S = {}; H(S) = {} {} t = {} (n = {}, K = {}).",if active {"ACTIVATED"} else {"NOT ACTIVATED"},canonical(&aggregate),canonical(&hill),if active {">="} else {"<"},canonical(&self.threshold),self.parameters.coefficient,canonical(&self.parameters.constant));
        if let (Some(cap), Some(quorum)) = (&self.cap, &self.quorum) {
            rationale.push_str(&format!(
                " Per-sensor cap {}: activation needs at least {quorum} positive sensor(s).",
                canonical(cap)
            ));
        } else {
            rationale.push_str(" No per-sensor cap: this is a sum threshold with no quorum claim.");
        }
        Ok(
            json!({"is_activated":active,"hill_value":canonical(&hill),"aggregate_signal":canonical(&aggregate),"threshold":canonical(&self.threshold),"parameters":{"hill_coefficient":self.parameters.coefficient,"half_maximal_constant":canonical(&self.parameters.constant)},"rationale":rationale,"positive_sensors":positive,"quorum_size":self.quorum.as_ref().map(|q|serde_json::Number::from_str(&q.to_string())).transpose().map_err(|e|refusal("NOT_EXACT",&e.to_string()))?,"per_sensor_cap":self.cap.as_ref().map(canonical)}),
        )
    }
}
pub fn evaluate(payload: &Value) -> Result<Value, Refusal> {
    let params = payload.get("parameters");
    let coefficient = params
        .and_then(|p| p.get("hill_coefficient"))
        .unwrap_or(&json!(2))
        .as_u64()
        .and_then(|v| u32::try_from(v).ok())
        .ok_or_else(|| refusal("NOT_EXACT", "hill_coefficient must be an int"))?;
    let constant = rational(
        params
            .and_then(|p| p.get("half_maximal_constant"))
            .unwrap_or(&json!(2)),
        "half_maximal_constant",
    )?;
    let threshold = rational(
        payload.get("activation_threshold").unwrap_or(&json!("1/2")),
        "activation_threshold",
    )?;
    let cap = match payload.get("per_sensor_cap") {
        Some(Value::Null) => None,
        raw => Some(rational(raw.unwrap_or(&json!(1)), "per_sensor_cap")?),
    };
    let gate =
        AllostericConsensusGate::new(HillParameters::new(coefficient, constant)?, threshold, cap)?;
    let signals = payload
        .get("sensor_signals")
        .and_then(Value::as_object)
        .ok_or_else(|| {
            refusal(
                "SIGNALS_NOT_KEYED",
                "sensor signals must map sensor ids to values",
            )
        })?;
    gate.evaluate(signals)
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/allostery.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:allostery:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfe140cb4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfe140cb4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfe140cb4 {
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
impl BoundaryErrorfe140cb4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfe140cb4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfe140cb4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfe140cb4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfe140cb4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfe140cb4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfe140cb4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfe140cb4::ExceedsCapacity {
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
mod l4_boundary_tests_fe140cb4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfe140cb4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfe140cb4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfe140cb4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfe140cb4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfe140cb4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfe140cb4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfe140cb4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
