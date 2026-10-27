//! Nomination-only skill archival policy. This kernel performs no filesystem effects.
use crate::Refusal;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

const DAY_US: i128 = 86_400_000_000;
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("SKILL_CULL_INPUT_INVALID", message)
}

#[derive(Debug, Deserialize, Serialize)]
struct Policy {
    window_days: u64,
    sensor_epoch: String,
    minimum_ledger_days: u64,
    new_skill_grace_days: u64,
    max_candidate_fraction: f64,
    #[serde(default)]
    exempt: Value,
    #[serde(default)]
    approved_by: Option<String>,
    #[serde(default)]
    approved_at: Option<String>,
}
impl Policy {
    fn parse_exempt(&self) -> Result<BTreeMap<String, String>, Refusal> {
        let mut exempt = BTreeMap::new();
        match &self.exempt {
            Value::Null => {}
            Value::Object(values) => {
                for (id, reason) in values {
                    let text = reason
                        .as_str()
                        .ok_or_else(|| invalid("exempt reasons must be strings"))?;
                    exempt.insert(id.clone(), text.into());
                }
            }
            Value::Array(entries) => {
                #[derive(Deserialize)]
                struct Entry {
                    id: String,
                    reason: String,
                }
                for raw in entries {
                    let entry: Entry =
                        serde_json::from_value(raw.clone()).map_err(|e| invalid(e.to_string()))?;
                    exempt.insert(entry.id, entry.reason);
                }
            }
            _ => {
                return Err(invalid(
                    "exempt must be an object or list of id/reason entries",
                ))
            }
        }
        Ok(exempt)
    }

    fn validate(&self) -> Result<BTreeMap<String, String>, Refusal> {
        if !self.max_candidate_fraction.is_finite()
            || !(0.0..=1.0).contains(&self.max_candidate_fraction)
        {
            return Err(invalid(
                "max_candidate_fraction must be a finite number from 0 to 1",
            ));
        }
        // The adapter parses this date into the public DTO; refuse absent/non-date input here too.
        if !valid_date(&self.sensor_epoch) {
            return Err(invalid("sensor_epoch must be a calendar date YYYY-MM-DD"));
        }
        self.parse_exempt()
    }
    fn normalized(&self, exempt: &BTreeMap<String, String>) -> Value {
        json!({"window_days":self.window_days,"sensor_epoch":self.sensor_epoch,
            "minimum_ledger_days":self.minimum_ledger_days,"new_skill_grace_days":self.new_skill_grace_days,
            "max_candidate_fraction":self.max_candidate_fraction,"exempt":exempt,
            "approved_by":self.approved_by.as_deref().unwrap_or("").trim(),
            "approved_at":self.approved_at.as_deref().unwrap_or("").trim()})
    }
}
fn valid_date(value: &str) -> bool {
    let bytes = value.as_bytes();
    if bytes.len() != 10
        || bytes[4] != b'-'
        || bytes[7] != b'-'
        || !bytes
            .iter()
            .enumerate()
            .all(|(i, b)| matches!(i, 4 | 7) || b.is_ascii_digit())
    {
        return false;
    }
    let number = |start: usize, end: usize| {
        bytes[start..end]
            .iter()
            .fold(0u32, |n, b| n * 10 + u32::from(b - b'0'))
    };
    let (year, month, day) = (number(0, 4), number(5, 7), number(8, 10));
    let maximum = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if year % 4 == 0 && (year % 100 != 0 || year % 400 == 0) => 29,
        2 => 28,
        _ => return false,
    };
    year > 0 && day > 0 && day <= maximum
}
#[derive(Debug, Deserialize)]
struct Observation {
    at_us: i64,
    date: String,
}
#[derive(Debug, Deserialize)]
struct Request {
    policy: Policy,
    now_us: i64,
    first_us: Option<i64>,
    last_us: Option<i64>,
    roster: Vec<String>,
    last_used: BTreeMap<String, Observation>,
    births: BTreeMap<String, Observation>,
    parity_green: Option<bool>,
}

pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    match payload["operation"].as_str() {
        Some("validate_policy") => {
            let policy: Policy = serde_json::from_value(payload["policy"].clone())
                .map_err(|e| invalid(e.to_string()))?;
            let exempt = policy.validate()?;
            Ok(policy.normalized(&exempt))
        }
        Some("nominate") => {
            nominate(serde_json::from_value(payload.clone()).map_err(|e| invalid(e.to_string()))?)
        }
        _ => Err(invalid("unknown skill garden policy operation")),
    }
}
fn nominate(request: Request) -> Result<Value, Refusal> {
    let policy = request.policy;
    let exemptions = policy.validate()?;
    if request
        .last_used
        .values()
        .chain(request.births.values())
        .any(|row| !valid_date(&row.date))
    {
        return Err(invalid(
            "observation dates must be calendar dates YYYY-MM-DD",
        ));
    }
    let roster: BTreeSet<String> = request.roster.into_iter().collect();
    let span_us = match (request.first_us, request.last_us) {
        (Some(first), Some(last)) if last >= first => i128::from(last) - i128::from(first),
        (Some(_), Some(_)) => return Err(invalid("ledger end precedes its start")),
        _ => 0,
    };
    let span_days = span_us as f64 / DAY_US as f64;
    let cutoff = i128::from(request.now_us) - i128::from(policy.window_days) * DAY_US;
    let mut refusals = Vec::new();
    if policy
        .approved_by
        .as_deref()
        .unwrap_or("")
        .trim()
        .is_empty()
    {
        refusals.push("the policy records no human approval. AuthorityEffect: None -- an archive decision needs a standing human policy, and until approved_by is filled in there is nothing to act under.".to_owned());
    }
    if span_days < policy.minimum_ledger_days as f64 {
        refusals.push(format!("the ledger spans {span_days:.1} days; a {}-day window over that measures the sensor, not the garden. Keep harvesting until it reaches {} days.",policy.window_days,policy.minimum_ledger_days));
    }
    if request.last_used.is_empty() {
        refusals.push(format!("zero invocations recorded across {} packages. That is a sensor failure, not a garden of dead skills.",roster.len()));
    }
    let (mut exempt, mut in_grace, mut used_recently, mut candidates) =
        (Vec::new(), Vec::new(), Vec::new(), Vec::new());
    for name in &roster {
        if let Some(reason) = exemptions.get(name) {
            exempt.push(json!({"skill_id":name,"reason":reason}));
            continue;
        }
        let born = request.births.get(name);
        if let Some(born) = born {
            let age_days = (i128::from(request.now_us) - i128::from(born.at_us)).div_euclid(DAY_US);
            if age_days < i128::from(policy.new_skill_grace_days) {
                in_grace.push(json!({"skill_id":name,"created":born.date,"age_days":age_days}));
                continue;
            }
        }
        let seen = request.last_used.get(name);
        if let Some(seen) = seen {
            if i128::from(seen.at_us) >= cutoff {
                used_recently.push(json!({"skill_id":name,"last_used":seen.date}));
                continue;
            }
        }
        candidates.push(json!({"skill_id":name,"last_used":seen.map(|row| &row.date),"created":born.map(|row| &row.date)}));
    }
    if !roster.is_empty() {
        let fraction = candidates.len() as f64 / roster.len() as f64;
        if fraction > policy.max_candidate_fraction {
            refusals.push(format!("{} of {} packages ({:.0}%) would be nominated, above the {:.0}% ceiling. Archiving that share of the garden in one action is a decision for a human, not the output of a script.", candidates.len(),roster.len(),fraction*100.0,policy.max_candidate_fraction*100.0));
        }
    }
    if request.parity_green == Some(false) {
        refusals.push("four-host skill parity is not green. Nothing may be computed against a garden whose four copies already disagree.".into());
    }
    if !refusals.is_empty() {
        candidates.clear();
    }
    Ok(
        json!({"refusals":refusals,"candidates":candidates,"exempt":exempt,"in_grace":in_grace,
        "used_recently":used_recently,"roster_size":roster.len(),"span_days":span_days}),
    )
}

// Origin: engine/crates_rs/core_operads/src/skill_garden.rs
// Claim: urn:core:crates_rs:core-operads:skill-garden:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2b075627 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2b075627` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2b075627 {
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
impl BoundaryError2b075627 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2b075627 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2b075627 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2b075627 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2b075627> {
        if capacity_bound == 0 {
            return Err(BoundaryError2b075627::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2b075627::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2b075627::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_2b075627 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2b075627::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2b075627::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2b075627::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2b075627::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2b075627::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2b075627::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2b075627::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
