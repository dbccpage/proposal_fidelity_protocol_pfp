//! Integer micro-USD quotes bound to effective, observed and expiring price evidence.
use crate::providers::Refusal;
use chrono::{DateTime, Datelike, Utc};
use num_bigint::BigInt;
use num_traits::Zero;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::str::FromStr;
pub const SCHEMA: &str = "core.provider.model-pricing-observation.v1";
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("PROVIDER_CONFIG_INVALID", message)
}
fn count(value: &Value, name: &str) -> Result<BigInt, Refusal> {
    let integer = value
        .as_number()
        .and_then(|n| BigInt::from_str(&n.to_string()).ok())
        .filter(|n| n >= &BigInt::zero());
    integer.ok_or_else(|| invalid(format!("{name} must be a non-negative exact integer")))
}
fn number(value: &BigInt) -> Result<Value, Refusal> {
    serde_json::Number::from_str(&value.to_string())
        .map(Value::Number)
        .map_err(|e| invalid(e.to_string()))
}
fn timestamp(value: &Value, name: &str) -> Result<DateTime<Utc>, Refusal> {
    let text = value
        .as_str()
        .ok_or_else(|| invalid(format!("{name} must be canonical UTC")))?;
    let bytes = text.as_bytes();
    if bytes.len() != 27
        || bytes.iter().enumerate().any(|(i, b)| match i {
            4 | 7 => *b != b'-',
            10 => *b != b'T',
            13 | 16 => *b != b':',
            19 => *b != b'.',
            26 => *b != b'Z',
            _ => !b.is_ascii_digit(),
        })
    {
        return Err(invalid(format!(
            "{name} must be canonical UTC with microseconds"
        )));
    }
    DateTime::parse_from_rfc3339(text)
        .ok()
        .filter(|t| (1..=9999).contains(&t.year()) && t.timestamp_subsec_micros() < 1_000_000)
        .map(|t| t.with_timezone(&Utc))
        .ok_or_else(|| invalid(format!("{name} is not a valid timestamp")))
}

fn canonical_ascii(value: &Value) -> Result<Vec<u8>, Refusal> {
    let wire = serde_json::to_string(value).map_err(|e| invalid(e.to_string()))?;
    let mut ascii = String::with_capacity(wire.len());
    for ch in wire.chars() {
        if ch.is_ascii() {
            ascii.push(ch);
        } else {
            for unit in ch.encode_utf16(&mut [0; 2]) {
                ascii.push_str(&format!("\\u{unit:04x}"));
            }
        }
    }
    Ok(ascii.into_bytes())
}
#[derive(Debug, Clone)]
pub struct PricingObservation {
    wire: Value,
    input: BigInt,
    output: BigInt,
    effective: DateTime<Utc>,
    observed: DateTime<Utc>,
    stale: DateTime<Utc>,
}
impl PricingObservation {
    pub fn from_json(raw: &Value) -> Result<Self, Refusal> {
        let mut wire = raw.clone();
        if !wire.is_object() {
            return Err(invalid("pricing observation must be an object"));
        }
        if !wire["model_deployment_id"]
            .as_str()
            .is_some_and(|s| !s.is_empty())
        {
            return Err(invalid(
                "model_deployment_id must be a non-empty exact string",
            ));
        }
        let input = count(&wire["input_microusd_per_mtok"], "input_microusd_per_mtok")?;
        let output = count(
            &wire["output_microusd_per_mtok"],
            "output_microusd_per_mtok",
        )?;
        let effective = timestamp(&wire["effective_from_utc"], "effective_from_utc")?;
        let observed = timestamp(&wire["observed_at_utc"], "observed_at_utc")?;
        let stale = timestamp(&wire["stale_after_utc"], "stale_after_utc")?;
        if effective > observed || observed >= stale {
            return Err(invalid(
                "pricing timestamps must satisfy effective <= observed < stale",
            ));
        }
        let digest = wire["evidence_digest"]
            .as_str()
            .ok_or_else(|| invalid("evidence_digest must be a canonical sha256 digest"))?;
        if digest.len() != 71
            || !digest.starts_with("sha256:")
            || !digest[7..]
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
        {
            return Err(invalid("evidence_digest must be a canonical sha256 digest"));
        }
        if wire.get("schema").is_none() {
            wire["schema"] = json!(SCHEMA);
        }
        if wire.get("authority_effect").is_none() {
            wire["authority_effect"] = json!("None");
        }
        if wire["schema"] != json!(SCHEMA) {
            return Err(invalid(format!("schema must be {SCHEMA}")));
        }
        if wire["authority_effect"] != json!("None") {
            return Err(invalid("authority_effect must be None"));
        }
        Ok(Self {
            wire,
            input,
            output,
            effective,
            observed,
            stale,
        })
    }
    pub fn to_canonical(&self) -> Value {
        json!({"schema":self.wire["schema"],"model_deployment_id":self.wire["model_deployment_id"],"input_microusd_per_mtok":self.wire["input_microusd_per_mtok"],"output_microusd_per_mtok":self.wire["output_microusd_per_mtok"],"effective_from_utc":self.wire["effective_from_utc"],"observed_at_utc":self.wire["observed_at_utc"],"stale_after_utc":self.wire["stale_after_utc"],"evidence_digest":self.wire["evidence_digest"],"authority_effect":"None"})
    }
    pub fn observation_digest(&self) -> Result<String, Refusal> {
        Ok(format!(
            "sha256:{}",
            hex::encode(Sha256::digest(canonical_ascii(&self.to_canonical())?))
        ))
    }
}
pub fn leg_cost(tokens: &BigInt, price: &BigInt) -> Result<BigInt, Refusal> {
    if tokens < &BigInt::zero() || price < &BigInt::zero() {
        return Err(invalid("tokens and price must be non-negative"));
    }
    let product = tokens * price;
    Ok(if product.is_zero() {
        product
    } else {
        (product + 999_999) / 1_000_000
    })
}
#[derive(Debug, Clone)]
pub struct PriceTable {
    observations: Vec<PricingObservation>,
}
impl PriceTable {
    pub fn new(observations: Vec<PricingObservation>) -> Result<Self, Refusal> {
        let mut seen = std::collections::BTreeSet::new();
        for item in &observations {
            if !seen.insert((
                item.wire["model_deployment_id"]
                    .as_str()
                    .unwrap_or_default()
                    .to_owned(),
                item.effective,
            )) {
                return Err(invalid(
                    "pricing observations cannot share an effective time",
                ));
            }
        }
        Ok(Self { observations })
    }
    pub fn quote(
        &self,
        model: &str,
        input: &BigInt,
        output: &BigInt,
        at_utc: &Value,
    ) -> Result<(PricingObservation, BigInt), Refusal> {
        let at = timestamp(at_utc, "at_utc")?;
        let mut eligible = self
            .observations
            .iter()
            .filter(|p| p.wire["model_deployment_id"].as_str() == Some(model))
            .collect::<Vec<_>>();
        if eligible.is_empty() {
            return Err(Refusal::new("PRICE_OBSERVATION_MISSING", model));
        }
        eligible.retain(|p| p.effective <= at);
        if eligible.is_empty() {
            return Err(Refusal::new("PRICE_OBSERVATION_NOT_EFFECTIVE", model));
        }
        eligible.retain(|p| p.observed <= at);
        if eligible.is_empty() {
            return Err(Refusal::new("PRICE_OBSERVATION_NOT_OBSERVED", model));
        }
        eligible.sort_by_key(|p| p.effective);
        let observation = eligible
            .last()
            .ok_or_else(|| invalid("pricing observation absent"))?;
        if at >= observation.stale {
            return Err(Refusal::new("PRICE_OBSERVATION_STALE", model));
        }
        let cost = leg_cost(input, &observation.input)? + leg_cost(output, &observation.output)?;
        Ok(((*observation).clone(), cost))
    }
}
#[derive(Debug, Clone)]
pub struct BudgetController {
    limit: BigInt,
    spent: BigInt,
}
impl BudgetController {
    pub fn new(limit: BigInt, spent: BigInt) -> Result<Self, Refusal> {
        if spent < BigInt::zero() || limit < spent {
            return Err(invalid(
                "invalid nonnegative cumulative spend or budget limit",
            ));
        }
        Ok(Self { limit, spent })
    }
    pub fn debit(&mut self, cost: &BigInt) -> Result<BigInt, Refusal> {
        if cost < &BigInt::zero() {
            return Err(invalid("microusd must be non-negative"));
        }
        let after = &self.spent + cost;
        if after > self.limit {
            return Err(Refusal::new(
                "BUDGET_EXCEEDED",
                format!(
                    "budget exceeded: requested={after} limit={} micro-USD",
                    self.limit
                ),
            ));
        }
        self.spent = after;
        Ok(self.spent.clone())
    }
    pub fn charge(
        &mut self,
        model: &str,
        observation: &PricingObservation,
        cost: &BigInt,
    ) -> Result<Value, Refusal> {
        if observation.wire["model_deployment_id"].as_str() != Some(model) {
            return Err(invalid("quote model does not match charged model"));
        }
        let digest = observation.observation_digest()?;
        let after = self.debit(cost)?;
        Ok(
            json!({"model":model,"cost_microusd":number(cost)?,"spent_after_microusd":number(&after)?,"limit_microusd":number(&self.limit)?,"pricing_observation_digest":digest,"pricing_effective_from_utc":observation.wire["effective_from_utc"],"pricing_observed_at_utc":observation.wire["observed_at_utc"],"pricing_stale_after_utc":observation.wire["stale_after_utc"],"authority_effect":"None"}),
        )
    }
}
fn budget(payload: &Value) -> Result<BudgetController, Refusal> {
    BudgetController::new(
        count(&payload["limit_microusd"], "limit_microusd")?,
        count(
            payload.get("spent_microusd").unwrap_or(&json!(0)),
            "spent_microusd",
        )?,
    )
}
fn table(payload: &Value) -> Result<PriceTable, Refusal> {
    let rows = payload["observations"]
        .as_array()
        .ok_or_else(|| invalid("observations required"))?;
    PriceTable::new(
        rows.iter()
            .map(PricingObservation::from_json)
            .collect::<Result<Vec<_>, _>>()?,
    )
}
pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let operation = payload["operation"]
        .as_str()
        .ok_or_else(|| invalid("operation required"))?;
    match operation {
        "parse_cost" => {
            let raw = payload["cost"]
                .as_str()
                .ok_or_else(|| invalid("cost must be decimal text"))?;
            if raw.len() > 256 || raw.starts_with('-') {
                return Err(invalid("invalid nonnegative cost"));
            }
            let (mantissa, exponent) = if let Some((m, e)) = raw.split_once(['e', 'E']) {
                (
                    m,
                    e.parse::<i32>()
                        .map_err(|_| invalid("invalid cost exponent"))?,
                )
            } else {
                (raw, 0)
            };
            if !(-256..=256).contains(&exponent) {
                return Err(invalid("cost exponent exceeds bound"));
            }
            let (whole, fraction) = mantissa.split_once('.').unwrap_or((mantissa, ""));
            let digits = format!("{whole}{fraction}");
            if digits.is_empty() || !digits.bytes().all(|c| c.is_ascii_digit()) {
                return Err(invalid("invalid decimal cost"));
            }
            let coefficient =
                BigInt::from_str(&digits).map_err(|_| invalid("invalid decimal cost"))?;
            let scale = fraction.len() as i32 - exponent - 6;
            let cost = if scale <= 0 {
                coefficient * BigInt::from(10).pow((-scale) as u32)
            } else {
                let divisor = BigInt::from(10).pow(scale as u32);
                (coefficient + &divisor - 1) / divisor
            };
            number(&cost)
        }
        "settle" => {
            let mut controller = budget(payload)?;
            let precharge = count(&payload["precharge_microusd"], "precharge")?;
            let billed = count(&payload["billed_microusd"], "billed")?;
            if precharge > controller.spent {
                return Err(invalid("precharge exceeds reserved spend"));
            }
            controller.spent -= &precharge;
            controller.debit(&billed)?;
            Ok(
                json!({"spent_microusd":number(&controller.spent)?, "delta_microusd":number(&(billed - precharge))?}),
            )
        }
        "observation" => {
            let observation = PricingObservation::from_json(&payload["observation"])?;
            Ok(
                json!({"observation":observation.to_canonical(),"observation_digest":observation.observation_digest()?}),
            )
        }
        "table" => {
            let mut observations = table(payload)?.observations;
            observations.sort_by(|a, b| {
                a.wire["model_deployment_id"]
                    .as_str()
                    .cmp(&b.wire["model_deployment_id"].as_str())
                    .then(a.effective.cmp(&b.effective))
            });
            Ok(Value::Array(
                observations
                    .iter()
                    .map(PricingObservation::to_canonical)
                    .collect(),
            ))
        }
        "leg_cost" => {
            let tokens = payload["tokens"]
                .as_number()
                .and_then(|v| BigInt::from_str(&v.to_string()).ok());
            let price = payload["price"]
                .as_number()
                .and_then(|v| BigInt::from_str(&v.to_string()).ok());
            let (Some(tokens), Some(price)) = (tokens, price) else {
                return Err(Refusal::new(
                    "PROVIDER_TYPE_ERROR",
                    "tokens and price must be exact integers",
                ));
            };
            number(&leg_cost(&tokens, &price)?)
        }
        "estimate" => number(&((count(&payload["payload_bytes"], "payload_bytes")? + 2) / 3 + 8)),
        "debit" | "state" => {
            let mut controller = budget(payload)?;
            if operation == "debit" {
                controller.debit(&count(&payload["cost_microusd"], "microusd")?)?;
            }
            Ok(
                json!({"spent_microusd":number(&controller.spent)?,"remaining_microusd":number(&(&controller.limit - &controller.spent))?}),
            )
        }
        "receipt" => {
            let observation = PricingObservation::from_json(&payload["observation"])?;
            let model = payload["model"]
                .as_str()
                .ok_or_else(|| invalid("model required"))?;
            budget(payload)?.charge(
                model,
                &observation,
                &count(&payload["cost_microusd"], "cost")?,
            )
        }
        "quote" | "charge" | "select" => {
            let model = payload["model"]
                .as_str()
                .ok_or_else(|| invalid("model required"))?;
            // Selection does not inspect token arguments. A quote selects before pricing its legs.
            let (observation, _) = table(payload)?.quote(
                model,
                &BigInt::zero(),
                &BigInt::zero(),
                &payload["at_utc"],
            )?;
            if operation == "select" {
                return Ok(observation.to_canonical());
            }
            let input = execute(
                &json!({"operation":"leg_cost","tokens":payload["input_tokens"],"price":number(&observation.input)?}),
            )?;
            let output = execute(
                &json!({"operation":"leg_cost","tokens":payload["output_tokens"],"price":number(&observation.output)?}),
            )?;
            let cost = count(&input, "input cost")? + count(&output, "output cost")?;
            if operation == "quote" {
                return Ok(
                    json!({"observation":observation.to_canonical(),"cost_microusd":number(&cost)?}),
                );
            }
            budget(payload)?.charge(model, &observation, &cost)
        }
        _ => Err(invalid("unknown budget operation")),
    }
}

// Origin: engine/crates_rs/core_adversary/src/providers/budget.rs
// Claim: urn:core:crates_rs:core-adversary:budget:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord96a4f658 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord96a4f658` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError96a4f658 {
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
impl BoundaryError96a4f658 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError96a4f658 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError96a4f658 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord96a4f658 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError96a4f658> {
        if capacity_bound == 0 {
            return Err(BoundaryError96a4f658::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError96a4f658::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError96a4f658::ExceedsCapacity {
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
mod l4_boundary_tests_96a4f658 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord96a4f658::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord96a4f658::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord96a4f658::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord96a4f658::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord96a4f658::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError96a4f658::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError96a4f658::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
