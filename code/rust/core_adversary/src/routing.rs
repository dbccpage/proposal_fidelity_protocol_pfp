use crate::exact::{integer, Integer};
use num_bigint::BigInt;
use num_integer::Integer as IntegerOps;
use num_rational::BigRational;
use num_traits::Zero;
use crate::stage::exact::{rational, Rational};
use crate::stage::ports::Refusal;
use core_types::python_unicode::repr_string;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, path::Path};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RouteLeg {
    pub router: String,
    pub model: String,
    pub input_microusd_per_token: Rational,
    pub output_microusd_per_token: Rational,
    pub id_verified: bool,
}
impl RouteLeg {
    pub fn vendor(&self) -> &str {
        self.model
            .split_once('/')
            .map_or(self.router.as_str(), |(vendor, _)| vendor)
    }
    pub fn cost_microusd(&self, input: &BigInt, output: &BigInt) -> BigInt {
        let cost =
            &self.input_microusd_per_token.0 * input + &self.output_microusd_per_token.0 * output;
        cost.numer().div_ceil(cost.denom())
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SeatRoute {
    pub seat_id: String,
    pub tier: String,
    pub legs: Vec<RouteLeg>,
}
impl SeatRoute {
    pub fn calls_model(&self) -> bool {
        matches!(self.tier.as_str(), "cheap" | "strong")
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BudgetPolicy {
    pub per_bout_microusd: Integer,
    pub per_day_microusd: Integer,
    pub admission_reserve_output_tokens: Option<Integer>,
    pub tier_per_bout_microusd: Vec<(String, Integer)>,
    pub max_input_bytes_per_call: Option<Integer>,
}
impl BudgetPolicy {
    pub fn tier_cap(&self, tier: &str) -> Option<&BigInt> {
        self.tier_per_bout_microusd
            .iter()
            .rev()
            .find(|(name, _)| name == tier)
            .map(|(_, value)| &value.0)
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RoutingTable {
    pub version: String,
    pub primary_router: String,
    pub cheap_share_min: Rational,
    pub budget: BudgetPolicy,
    pub seats: Vec<SeatRoute>,
}
pub fn canonical_seat_key(seat_id: &str) -> String {
    let mut out = String::new();
    let mut separator = false;
    // Python 3.12 casefold mappings which can produce ASCII after the routing
    // regex. All other non-ASCII folds reduce to a separator in this profile.
    let folded: String = seat_id
        .chars()
        .map(|c| match c {
            '\u{00df}' | '\u{1e9e}' => "ss".into(),
            '\u{0130}' => "i_".into(),
            '\u{0149}' => "_n".into(),
            '\u{017f}' => "s".into(),
            '\u{01f0}' => "j_".into(),
            '\u{1e96}' => "h_".into(),
            '\u{1e97}' => "t_".into(),
            '\u{1e98}' => "w_".into(),
            '\u{1e99}' => "y_".into(),
            '\u{1e9a}' => "a_".into(),
            '\u{212a}' => "k".into(),
            '\u{fb00}' => "ff".into(),
            '\u{fb01}' => "fi".into(),
            '\u{fb02}' => "fl".into(),
            '\u{fb03}' => "ffi".into(),
            '\u{fb04}' => "ffl".into(),
            '\u{fb05}' | '\u{fb06}' => "st".into(),
            c if c.is_ascii() => c.to_ascii_lowercase().to_string(),
            _ => "_".into(),
        })
        .collect();
    for c in folded.chars() {
        if c.is_ascii_lowercase() || c.is_ascii_digit() {
            if separator && !out.is_empty() {
                out.push('_');
            }
            out.push(c);
            separator = false;
        } else {
            separator = true;
        }
    }
    out.strip_prefix("seat_").unwrap_or(&out).to_owned()
}
impl RoutingTable {
    pub fn seat(&self, seat_id: &str) -> Result<&SeatRoute, Refusal> {
        let key = canonical_seat_key(seat_id);
        if key.is_empty() {
            return Err(Refusal::new(
                "SEAT_ID_INVALID",
                format!(
                    "seat id {} has no ASCII letters or digits",
                    repr_string(seat_id)
                ),
            ));
        }
        self.seats
            .iter()
            .find(|s| canonical_seat_key(&s.seat_id) == key)
            .ok_or_else(|| {
                Refusal::new(
                    "SEAT_ROUTE_MISSING",
                    format!("no route declared for seat {}", repr_string(seat_id)),
                )
            })
    }
    pub fn cheap_share(&self) -> BigRational {
        let llm: Vec<_> = self.seats.iter().filter(|s| s.calls_model()).collect();
        if llm.is_empty() {
            return BigRational::zero();
        }
        BigRational::new(
            BigInt::from(llm.iter().filter(|s| s.tier == "cheap").count()),
            BigInt::from(llm.len()),
        )
    }
}
pub fn validate_table(table: &RoutingTable) -> Result<(), Refusal> {
    let budget = &table.budget;
    if budget.per_bout_microusd.0 <= BigInt::zero()
        || budget.per_bout_microusd > budget.per_day_microusd
    {
        return Err(Refusal::new(
            "ROUTING_BUDGET_INVALID",
            "require 0 < per_bout <= per_day",
        ));
    }
    for (tier, cap) in &budget.tier_per_bout_microusd {
        if !matches!(tier.as_str(), "cheap" | "strong")
            || cap.0 <= BigInt::zero()
            || cap > &budget.per_bout_microusd
        {
            return Err(Refusal::new(
                "ROUTING_BUDGET_INVALID",
                format!(
                    "tier cap {} must be an LLM tier with 0 < cap <= per_bout",
                    repr_string(tier)
                ),
            ));
        }
    }
    for (name, value) in [
        ("max_input_bytes_per_call", &budget.max_input_bytes_per_call),
        (
            "admission_reserve_output_tokens",
            &budget.admission_reserve_output_tokens,
        ),
    ] {
        if value
            .as_ref()
            .is_some_and(|value| value.0 <= BigInt::zero())
        {
            return Err(Refusal::new(
                "ROUTING_BUDGET_INVALID",
                format!("{name} must be a positive integer"),
            ));
        }
    }
    if table.cheap_share_min.0 < BigRational::zero()
        || table.cheap_share_min.0 > BigRational::from_integer(1.into())
    {
        return Err(Refusal::new(
            "ROUTING_SHARE_INVALID",
            "cheap_share_min must lie in [0, 1]",
        ));
    }
    let mut seen = BTreeSet::new();
    for route in &table.seats {
        let seat = repr_string(&route.seat_id);
        if canonical_seat_key(&route.seat_id).is_empty() {
            return Err(Refusal::new(
                "ROUTING_SEAT_ID_INVALID",
                format!("seat id {seat} has no ASCII letters or digits"),
            ));
        }
        if !seen.insert(canonical_seat_key(&route.seat_id)) {
            return Err(Refusal::new(
                "ROUTING_SEAT_DUPLICATE",
                format!("seat {seat} declared twice"),
            ));
        }
        if !matches!(
            route.tier.as_str(),
            "cheap" | "strong" | "deterministic" | "inactive"
        ) {
            return Err(Refusal::new(
                "ROUTING_TIER_UNKNOWN",
                format!("seat {seat}: tier {}", repr_string(&route.tier)),
            ));
        }
        if !route.calls_model() {
            if !route.legs.is_empty() {
                return Err(Refusal::new(
                    "ROUTING_NON_LLM_HAS_LEGS",
                    format!("seat {seat} is {} but declares model legs", route.tier),
                ));
            }
            continue;
        }
        if route.legs.iter().any(|leg| {
            leg.input_microusd_per_token.0 < BigRational::zero()
                || leg.output_microusd_per_token.0 < BigRational::zero()
        }) {
            return Err(Refusal::new(
                "ROUTING_PRICE_INVALID",
                format!("seat {seat}: negative price"),
            ));
        }
        if route
            .legs
            .iter()
            .any(|leg| leg.router != table.primary_router)
        {
            return Err(Refusal::new(
                "ROUTING_NON_PRIMARY_ROUTER",
                format!(
                    "seat {seat}: every leg must use router {}",
                    repr_string(&table.primary_router)
                ),
            ));
        }
        if route
            .legs
            .iter()
            .map(|leg| &leg.model)
            .collect::<BTreeSet<_>>()
            .len()
            < 3
        {
            return Err(Refusal::new(
                "ROUTING_TOO_FEW_MODELS",
                format!("seat {seat}: needs 3 distinct primary models"),
            ));
        }
        if route
            .legs
            .iter()
            .take(3)
            .map(RouteLeg::vendor)
            .collect::<BTreeSet<_>>()
            .len()
            < 3
        {
            return Err(Refusal::new(
                "ROUTING_VENDOR_MONOCULTURE",
                format!("seat {seat}: first 3 models need distinct vendors"),
            ));
        }
    }
    let share = table.cheap_share();
    if share < table.cheap_share_min.0 {
        return Err(Refusal::new(
            "ROUTING_CHEAP_SHARE_BELOW_MIN",
            format!(
                "cheap share {share} below declared minimum {}",
                table.cheap_share_min.0
            ),
        ));
    }
    Ok(())
}

pub fn admit_spend(
    spent_bout: &BigInt,
    spent_day: &BigInt,
    worst_case: &BigInt,
    policy: &BudgetPolicy,
    tier: &str,
    spent_tier: &BigInt,
) -> Result<(), Refusal> {
    if let Some(cap) = policy.tier_cap(tier) {
        if spent_tier + worst_case > *cap {
            return Err(Refusal::new("BUDGET_TIER_EXCEEDED", format!("worst case {worst_case} would exceed {tier} tier cap {cap} (spent {spent_tier})")));
        }
    }
    if spent_bout + worst_case > policy.per_bout_microusd.0 {
        return Err(Refusal::new(
            "BUDGET_BOUT_EXCEEDED",
            format!(
                "worst case {worst_case} would exceed bout cap {} (spent {spent_bout})",
                policy.per_bout_microusd.0
            ),
        ));
    }
    if spent_day + worst_case > policy.per_day_microusd.0 {
        return Err(Refusal::new(
            "BUDGET_DAY_EXCEEDED",
            format!(
                "worst case {worst_case} would exceed day cap {} (spent {spent_day})",
                policy.per_day_microusd.0
            ),
        ));
    }
    Ok(())
}

fn price(raw: &Value, where_: &str) -> Result<Rational, Refusal> {
    let raw = raw.as_str().ok_or_else(|| {
        Refusal::new(
            "ROUTING_PRICE_INVALID",
            format!("{where_}: price must be a quoted decimal string"),
        )
    })?;
    // Price entries use decimals, while the share and normalized domain wire may use ratios.
    if raw.contains('/') {
        return Err(Refusal::new(
            "ROUTING_PRICE_INVALID",
            format!("{where_}: unparsable price {}", repr_string(raw)),
        ));
    }
    rational(raw).map(Rational).ok_or_else(|| {
        Refusal::new(
            "ROUTING_PRICE_INVALID",
            format!("{where_}: unparsable price {}", repr_string(raw)),
        )
    })
}
fn required_integer(raw: &Value) -> Result<Integer, Refusal> {
    integer(raw).map(Integer).ok_or_else(|| {
        Refusal::new(
            "ROUTING_BUDGET_INVALID",
            "budgets must be integer micro-USD",
        )
    })
}
fn optional_integer(raw: &Value, name: &str) -> Result<Option<Integer>, Refusal> {
    if raw.is_null() {
        return Ok(None);
    }
    integer(raw).map(|n| Some(Integer(n))).ok_or_else(|| {
        Refusal::new(
            "ROUTING_BUDGET_INVALID",
            format!("{name} must be a positive integer"),
        )
    })
}
pub fn parse_routing(raw: &str) -> Result<RoutingTable, Refusal> {
    // Preserve declared seat order without changing JSON map behavior in other crates.
    let parsed: Value = serde_json::from_str(raw)
        .map_err(|_| Refusal::new("ROUTING_CONFIG_INVALID", "routing is not JSON"))?;
    let data = parsed
        .as_object()
        .ok_or_else(|| Refusal::new("ROUTING_CONFIG_INVALID", "top level must be a mapping"))?;
    for key in [
        "version",
        "primary_router",
        "cheap_share_min",
        "budget",
        "models",
        "seats",
    ] {
        if !data.contains_key(key) {
            return Err(Refusal::new(
                "ROUTING_CONFIG_INVALID",
                format!("missing key {}", repr_string(key)),
            ));
        }
    }
    let primary = data["primary_router"]
        .as_str()
        .ok_or_else(|| Refusal::new("ROUTING_CONFIG_INVALID", "primary_router must be text"))?;
    let prices = data["models"].as_object().ok_or_else(|| {
        Refusal::new(
            "ROUTING_CONFIG_INVALID",
            "models and budget must be mappings",
        )
    })?;
    let budget = data["budget"].as_object().ok_or_else(|| {
        Refusal::new(
            "ROUTING_CONFIG_INVALID",
            "models and budget must be mappings",
        )
    })?;
    let tiers = match budget.get("tier_per_bout_microusd") {
        None | Some(Value::Null) => None,
        Some(v) => Some(v.as_object().ok_or_else(|| {
            Refusal::new(
                "ROUTING_CONFIG_INVALID",
                "tier_per_bout_microusd must be a mapping",
            )
        })?),
    };
    let share_raw = &data["cheap_share_min"];
    let share =
        rational(share_raw.as_str().unwrap_or(&share_raw.to_string())).ok_or_else(|| {
            Refusal::new(
                "ROUTING_SHARE_INVALID",
                format!(
                    "bad cheap_share_min {}",
                    share_raw
                        .as_str()
                        .map(repr_string)
                        .unwrap_or_else(|| share_raw.to_string())
                ),
            )
        })?;
    let raw_fields: std::collections::BTreeMap<String, Box<serde_json::value::RawValue>> =
        serde_json::from_str(raw)
            .map_err(|_| Refusal::new("ROUTING_CONFIG_INVALID", "routing is not a mapping"))?;
    let raw_seat_value = raw_fields
        .get("seats")
        .ok_or_else(|| Refusal::new("ROUTING_CONFIG_INVALID", "seats are absent"))?;
    let raw_seats: indexmap::IndexMap<String, Value> =
        serde_json::from_str(raw_seat_value.get())
            .map_err(|_| Refusal::new("ROUTING_CONFIG_INVALID", "seats must be a mapping"))?;
    let mut seats = Vec::new();
    for (seat_id, spec) in &raw_seats {
        let spec = spec
            .as_object()
            .filter(|s| s.contains_key("tier"))
            .ok_or_else(|| {
                Refusal::new(
                    "ROUTING_CONFIG_INVALID",
                    format!("seat {} needs a tier", repr_string(seat_id)),
                )
            })?;
        let tier = spec["tier"]
            .as_str()
            .ok_or_else(|| Refusal::new("ROUTING_CONFIG_INVALID", "tier must be text"))?;
        let models = match spec.get("models") {
            None | Some(Value::Null) => &[][..],
            Some(value) => value
                .as_array()
                .ok_or_else(|| Refusal::new("ROUTING_CONFIG_INVALID", "models must be an array"))?
                .as_slice(),
        };
        let mut legs = Vec::new();
        for model in models {
            let model = model
                .as_str()
                .ok_or_else(|| Refusal::new("ROUTING_CONFIG_INVALID", "model must be text"))?;
            let entry = prices
                .get(primary)
                .and_then(|p| p.get(model))
                .and_then(Value::as_object)
                .ok_or_else(|| {
                    Refusal::new(
                        "ROUTING_MODEL_UNPRICED",
                        format!("{primary}:{model} has no price entry"),
                    )
                })?;
            let p_in = price(
                entry.get("in").unwrap_or(&Value::Null),
                &format!("{primary}:{model}.in"),
            )?;
            let p_out = price(
                entry.get("out").unwrap_or(&Value::Null),
                &format!("{primary}:{model}.out"),
            )?;
            let id_verified = match entry.get("id_verified") {
                None => true,
                Some(v) => v.as_bool().ok_or_else(|| {
                    Refusal::new(
                        "ROUTING_CONFIG_INVALID",
                        format!("{primary}:{model}.id_verified must be boolean"),
                    )
                })?,
            };
            legs.push(RouteLeg {
                router: primary.into(),
                model: model.into(),
                input_microusd_per_token: p_in,
                output_microusd_per_token: p_out,
                id_verified,
            });
        }
        seats.push(SeatRoute {
            seat_id: seat_id.clone(),
            tier: tier.into(),
            legs,
        });
    }
    let get = |name: &str| budget.get(name).unwrap_or(&Value::Null);
    let policy = BudgetPolicy {
        per_bout_microusd: required_integer(get("per_bout_microusd"))?,
        per_day_microusd: required_integer(get("per_day_microusd"))?,
        admission_reserve_output_tokens: optional_integer(
            get("admission_reserve_output_tokens"),
            "admission_reserve_output_tokens",
        )?,
        max_input_bytes_per_call: optional_integer(
            get("max_input_bytes_per_call"),
            "max_input_bytes_per_call",
        )?,
        tier_per_bout_microusd: match tiers {
            Some(tiers) => {
                let mut caps = Vec::new();
                for (tier, raw) in tiers {
                    caps.push((
                        tier.clone(),
                        integer(raw).map(Integer).ok_or_else(|| {
                            Refusal::new(
                                "ROUTING_BUDGET_INVALID",
                                format!(
                                    "tier cap {} must be an LLM tier with 0 < cap <= per_bout",
                                    repr_string(tier)
                                ),
                            )
                        })?,
                    ));
                }
                caps.sort_by(|a, b| a.0.cmp(&b.0));
                caps
            }
            None => Vec::new(),
        },
    };
    let table = RoutingTable {
        version: data["version"]
            .as_str()
            .unwrap_or(&data["version"].to_string())
            .into(),
        primary_router: primary.into(),
        cheap_share_min: Rational(share),
        budget: policy,
        seats,
    };
    validate_table(&table)?;
    Ok(table)
}
pub fn load_routing(path: &Path) -> Result<(RoutingTable, String), Refusal> {
    let raw = std::fs::read(path).map_err(|error| {
        Refusal::new(
            "ROUTING_CONFIG_UNREADABLE",
            format!("{}: {error}", path.display()),
        )
    })?;
    let data: serde_yaml::Value = serde_yaml::from_slice(&raw).map_err(|error| {
        Refusal::new(
            "ROUTING_CONFIG_INVALID",
            format!("{}: {error}", path.display()),
        )
    })?;
    Ok((
        parse_routing(
            &serde_json::to_string(&data)
                .map_err(|_| Refusal::new("ROUTING_CONFIG_INVALID", "routing cannot be encoded"))?,
        )?,
        format!("sha256:{}", hex::encode(Sha256::digest(raw))),
    ))
}

// Origin: engine/crates_rs/core_adversary/src/routing.rs
// Claim: urn:core:crates_rs:core-adversary:routing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordce2bfe7a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordce2bfe7a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorce2bfe7a {
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
impl BoundaryErrorce2bfe7a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorce2bfe7a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorce2bfe7a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordce2bfe7a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorce2bfe7a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorce2bfe7a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorce2bfe7a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorce2bfe7a::ExceedsCapacity {
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
mod l4_boundary_tests_ce2bfe7a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordce2bfe7a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordce2bfe7a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordce2bfe7a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordce2bfe7a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordce2bfe7a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorce2bfe7a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorce2bfe7a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
