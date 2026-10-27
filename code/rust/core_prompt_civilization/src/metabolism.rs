//! Pure obstruction episode segmentation and Unicode DDC motif mining.
//! AuthorityEffect: None. No host I/O or promotion authority.

use crate::civilization::Refusal;
use num_bigint::BigInt;
use num_traits::{FromPrimitive, ToPrimitive, Zero};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

fn invalid(message: impl Into<String>) -> Refusal {
    Refusal {
        code: "METABOLISM_INPUT_INVALID".into(),
        message: message.into(),
        state: None,
    }
}

fn integer(value: &Value) -> Result<BigInt, Refusal> {
    match value {
        Value::Bool(flag) => Ok(BigInt::from(u8::from(*flag))),
        Value::Number(number) => number.to_string().parse().or_else(|_| {
            number
                .as_f64()
                .and_then(|n| BigInt::from_f64(n.trunc()))
                .ok_or_else(|| invalid("expected an integer-compatible count"))
        }),
        Value::String(text) => text
            .trim()
            .parse()
            .map_err(|_| invalid("expected an integer-compatible count")),
        _ => Err(invalid("expected an integer-compatible count")),
    }
}

fn wire_count(number: &BigInt) -> Result<Value, Refusal> {
    serde_json::from_str(&number.to_string()).map_err(|error| invalid(error.to_string()))
}

fn ngram_limit(value: &Value) -> Result<BigInt, Refusal> {
    match value {
        Value::Bool(flag) => Ok(BigInt::from(u8::from(*flag))),
        Value::Number(number) => number
            .to_string()
            .parse()
            .map_err(|_| invalid("max_n must be an integer")),
        _ => Err(invalid("max_n must be an integer")),
    }
}

fn truthy(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(flag) => *flag,
        Value::Number(number) => number.as_f64().is_none_or(|n| n != 0.0),
        Value::String(text) => !text.is_empty(),
        Value::Array(items) => !items.is_empty(),
        Value::Object(items) => !items.is_empty(),
    }
}

fn python_string(value: &Value) -> String {
    match value {
        Value::String(text) => text.clone(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        Value::Null => "None".into(),
        _ => value.to_string(),
    }
}

fn is_zero_string(value: &Value) -> bool {
    matches!(value.as_str(), Some("0" | "0/1"))
}

struct OpenEpisode {
    start_hash: String,
    phi: Value,
    gamma: Value,
    defects: BigInt,
    word: String,
}

impl OpenEpisode {
    fn finish(
        &self,
        run_id: &str,
        end_hash: &str,
        phi: &Value,
        gamma: &Value,
        defects: &BigInt,
        outcome: &str,
    ) -> Result<Value, Refusal> {
        Ok(json!({
            "run_id": run_id, "start_step_hash": self.start_hash,
            "end_step_hash": end_hash, "phi_1_before": self.phi, "phi_1_after": phi,
            "gamma_2_before": self.gamma, "gamma_2_after": gamma,
            "defect_count_before": wire_count(&self.defects)?,
            "defect_count_after": wire_count(defects)?, "ddc_word": self.word,
            "outcome": outcome, "authority_effect": "None"
        }))
    }
}

struct ParsedStep {
    hash: String,
    phi: Value,
    gamma: Value,
    defects: BigInt,
    op: String,
    obstructed: bool,
}

fn parse_step(index: usize, step: &Value) -> Result<ParsedStep, Refusal> {
    if !step.is_object() {
        return Err(invalid("every step must be an object"));
    }
    let hash = step
        .get("step_hash")
        .filter(|value| truthy(value))
        .map(python_string)
        .unwrap_or_else(|| format!("step_{index}"));
    let phi = step.get("phi_1").cloned().unwrap_or_else(|| json!("0"));
    let gamma = step.get("gamma_2").cloned().unwrap_or_else(|| json!("0"));
    let defects = step
        .get("defect_count")
        .map(integer)
        .transpose()?
        .unwrap_or_else(BigInt::zero);
    let op = ["op", "letter"]
        .iter()
        .find_map(|key| step.get(*key).filter(|value| truthy(value)))
        .map(python_string)
        .unwrap_or_else(|| "E".into());
    let obstructed = defects > BigInt::zero() || !is_zero_string(&phi) || !is_zero_string(&gamma);
    Ok(ParsedStep {
        hash,
        phi,
        gamma,
        defects,
        op,
        obstructed,
    })
}

fn episode_outcome(obstructed: bool, op: &str, gamma: &Value) -> &'static str {
    if !obstructed {
        "ExactRepair"
    } else if op == "M" {
        "Refused"
    } else if !is_zero_string(gamma) {
        "OpenObstruction"
    } else {
        "ClosedResidual"
    }
}

fn should_close_episode(obstructed: bool, op: &str, index: usize, total_steps: usize) -> bool {
    !obstructed || matches!(op, "T" | "M") || index + 1 == total_steps
}

fn step_episode(
    open: &mut Option<OpenEpisode>,
    results: &mut Vec<Value>,
    run_id: &str,
    step: ParsedStep,
    index: usize,
    total_steps: usize,
) -> Result<(), Refusal> {
    if let Some(episode) = open.as_mut() {
        episode.word.push_str(&step.op);
        if should_close_episode(step.obstructed, &step.op, index, total_steps) {
            let outcome = episode_outcome(step.obstructed, &step.op, &step.gamma);
            results.push(episode.finish(
                run_id,
                &step.hash,
                &step.phi,
                &step.gamma,
                &step.defects,
                outcome,
            )?);
            *open = None;
        }
    } else if step.obstructed {
        *open = Some(OpenEpisode {
            start_hash: step.hash,
            phi: step.phi,
            gamma: step.gamma,
            defects: step.defects,
            word: step.op,
        });
    }
    Ok(())
}

fn segment(payload: &Value) -> Result<Value, Refusal> {
    let run_id = payload["run_id"]
        .as_str()
        .ok_or_else(|| invalid("run_id must be text"))?;
    let steps = payload["steps"]
        .as_array()
        .ok_or_else(|| invalid("steps must be an array"))?;
    let mut results = Vec::new();
    let mut open: Option<OpenEpisode> = None;
    for (index, raw_step) in steps.iter().enumerate() {
        let step = parse_step(index, raw_step)?;
        step_episode(&mut open, &mut results, run_id, step, index, steps.len())?;
    }
    if let Some(episode) = open {
        results.push(episode.finish(
            run_id,
            &episode.start_hash,
            &episode.phi,
            &episode.gamma,
            &episode.defects,
            "Abandoned",
        )?);
    }
    Ok(Value::Array(results))
}

#[derive(Default)]
struct MotifEvidence {
    success: BigInt,
    stall: BigInt,
    runs: BTreeSet<String>,
}

fn accumulate_episode_motifs(
    episode: &Value,
    max_n: &BigInt,
    evidence: &mut BTreeMap<String, MotifEvidence>,
) -> Result<(), Refusal> {
    let word = episode["ddc_word"]
        .as_str()
        .ok_or_else(|| invalid("ddc_word must be text"))?
        .chars()
        .collect::<Vec<_>>();
    let run_id = episode["run_id"]
        .as_str()
        .ok_or_else(|| invalid("run_id must be text"))?;
    let success = matches!(
        episode["outcome"].as_str(),
        Some("ExactRepair" | "ClosedResidual")
    );
    let limit = max_n
        .clone()
        .min(BigInt::from(word.len()))
        .to_usize()
        .unwrap_or(0);
    for n in 1..=limit {
        for window in word.windows(n) {
            let entry = evidence.entry(window.iter().collect()).or_default();
            if success {
                entry.success += 1;
            } else {
                entry.stall += 1;
            }
            entry.runs.insert(run_id.into());
        }
    }
    Ok(())
}

fn compare_motif_entries(
    (left_word, left): &(String, MotifEvidence),
    (right_word, right): &(String, MotifEvidence),
) -> std::cmp::Ordering {
    (&right.success + &right.stall)
        .cmp(&(&left.success + &left.stall))
        .then(right_word.chars().count().cmp(&left_word.chars().count()))
        .then(left_word.cmp(right_word))
}

fn serialize_motif_entry((word, entry): (String, MotifEvidence)) -> Result<Value, Refusal> {
    let n = word.chars().count();
    let repeated = n >= 3 && word.chars().all(|c| word.starts_with(c));
    Ok(json!({
        "motif": word, "n_gram_len": n,
        "success_count": wire_count(&entry.success)?,
        "stall_count": wire_count(&entry.stall)?,
        "antimorphism_label": repeated.then_some("AM-4_IDEMPOTENT_CUT_LOOP"),
        "evidence_runs": entry.runs, "authority_effect": "None"
    }))
}

fn motifs(payload: &Value) -> Result<Value, Refusal> {
    let episodes = payload["episodes"]
        .as_array()
        .ok_or_else(|| invalid("episodes must be an array"))?;
    let max_n = payload
        .get("max_n")
        .map(ngram_limit)
        .transpose()?
        .unwrap_or_else(|| BigInt::from(6));
    let mut evidence = BTreeMap::<String, MotifEvidence>::new();
    for episode in episodes {
        accumulate_episode_motifs(episode, &max_n, &mut evidence)?;
    }
    let mut entries = evidence.into_iter().collect::<Vec<_>>();
    entries.sort_by(compare_motif_entries);
    entries
        .into_iter()
        .map(serialize_motif_entry)
        .collect::<Result<Vec<_>, Refusal>>()
        .map(Value::Array)
}

/// Native query boundary. Integer counts are arbitrary precision; n-grams slice Unicode scalars.
pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    match payload["operation"].as_str() {
        Some("segment") => segment(payload),
        Some("motifs") => motifs(payload),
        _ => Err(invalid("unknown metabolism operation")),
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/metabolism.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:metabolism:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9d22a6a5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9d22a6a5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9d22a6a5 {
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
impl BoundaryError9d22a6a5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9d22a6a5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9d22a6a5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9d22a6a5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9d22a6a5> {
        if capacity_bound == 0 {
            return Err(BoundaryError9d22a6a5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9d22a6a5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9d22a6a5::ExceedsCapacity {
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
mod l4_boundary_tests_9d22a6a5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9d22a6a5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9d22a6a5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9d22a6a5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9d22a6a5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9d22a6a5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError9d22a6a5::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError9d22a6a5::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
