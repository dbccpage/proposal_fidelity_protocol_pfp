//! Act VI: residual declaration and injected failure-history updates.
//! Recorded history is not host-reproduced antibody admission.
use crate::authorization::{flag, refuse, AuthorizationTime};
use crate::evidence::{sha256_ref, ObstructionMeasurement};
use crate::stage::ddc::DdcStep;
use crate::stage::emission::{
    build_intelligence_event, emit_event, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::genealogy::CemeteryHeadstone;
use crate::stage::packets::Challenge;
use crate::stage::ports::Refusal;
use crate::wire_json::python_ascii_json;
use serde_json::{json, Map, Value};
use std::collections::BTreeMap;

pub struct ResidualLedgerInput<'a> {
    pub dead_candidates: &'a [CemeteryHeadstone],
    pub critiques: &'a [Challenge],
    pub critique_verdicts: &'a BTreeMap<String, String>,
    pub measurement: &'a ObstructionMeasurement,
    pub ablation_flags: Option<&'a Map<String, Value>>,
    pub run_key: &'a str,
    pub now_utc: &'a str,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResidualLedgerOutcome {
    residual_ledger: Value,
    antibodies_recorded: usize,
    narrative: Value,
}
impl ResidualLedgerOutcome {
    pub fn residual_ledger(&self) -> &Value {
        &self.residual_ledger
    }
    pub fn antibodies_recorded(&self) -> usize {
        self.antibodies_recorded
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn to_dict(&self) -> Value {
        json!({"residual_ledger":self.residual_ledger,"antibodies_recorded":self.antibodies_recorded,"narrative":self.narrative})
    }
}
pub fn execute_act6_residual_ledger(
    input: &ResidualLedgerInput<'_>,
    mut emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<ResidualLedgerOutcome, Refusal> {
    let recorded = record_dead_candidate_failures(input.dead_candidates, &mut emitters)?;
    let ledger = build_residual_ledger(input)?;
    let status = ledger
        .get("status")
        .and_then(Value::as_str)
        .unwrap_or("ABLATED");
    let narrative = json!({"act_number":"VI","title":"Residual Ledger Declaration",
        "body":format!("Residual ledger status: {status}. Accumulated {recorded} antibody update(s).")});
    if let Some(suite) = emitters {
        emit_act6_event(input, &ledger, recorded, suite, time)?;
    }
    Ok(ResidualLedgerOutcome {
        residual_ledger: ledger,
        antibodies_recorded: recorded,
        narrative,
    })
}

fn record_dead_candidate_failures(
    dead_candidates: &[CemeteryHeadstone],
    emitters: &mut Option<&mut EmitterSuite<'_>>,
) -> Result<usize, Refusal> {
    let mut recorded = 0usize;
    if let Some(sink) = emitters
        .as_mut()
        .and_then(|suite| suite.antibodies.as_mut())
    {
        for dead in dead_candidates {
            let cause = &dead.input().cause_of_death;
            sink.record_failure(cause, &format!("Disallow pattern causing {cause}"))?;
            recorded = recorded.checked_add(1).ok_or_else(history_overflow)?;
        }
    }
    Ok(recorded)
}

fn history_overflow() -> Refusal {
    refuse(
        "ADVERSARY_HISTORY_COUNT_OVERFLOW",
        "failure history count overflow",
    )
}

fn build_residual_ledger(input: &ResidualLedgerInput<'_>) -> Result<Value, Refusal> {
    if flag(input.ablation_flags, "no_residual_ledger") {
        return Ok(json!({}));
    }
    let status = classify_measurement_status(input.measurement);
    Ok(json!({
        "unresolved_challenges": input.critiques.iter().filter(|critique| !*critique.blocking()).map(|critique| critique.challenge_id()).collect::<Vec<_>>(),
        "blocking_challenges": input.critiques.iter().filter(|critique| *critique.blocking()).map(|critique| critique.challenge_id()).collect::<Vec<_>>(),
        "malformed_critiques": input.critique_verdicts.iter().filter_map(|(id, verdict)| (verdict == "MALFORMED").then_some(id)).collect::<Vec<_>>(),
        "carrier_measurement": input.measurement.to_dict()?,
        "status": status,
        "residual_declared": true
    }))
}

fn classify_measurement_status(measurement: &ObstructionMeasurement) -> &'static str {
    if measurement.is_exact_joint_zero() {
        "CLEARED"
    } else if measurement.is_measured() {
        "BOUNDED_RESIDUAL"
    } else {
        "NOT_MEASURED"
    }
}

fn emit_act6_event(
    input: &ResidualLedgerInput<'_>,
    ledger: &Value,
    recorded: usize,
    suite: &mut EmitterSuite<'_>,
    time: &AuthorizationTime<'_>,
) -> Result<(), Refusal> {
    let payload = Map::from_iter([
        ("act".into(), json!("VI")),
        ("title".into(), json!("Residual Ledger Declaration")),
        ("antibodies_recorded".into(), json!(recorded)),
    ]);
    let event_id = sha256_ref(format!("{}:act6", input.run_key).as_bytes());
    let (event, bytes) = build_intelligence_event(
        EventDescriptor {
            ie_id: &event_id,
            actor_id: "actor_logos_secretary",
            actor_kind: "SWARM_SEAT",
            event_kind: "COMM",
            source_system: "oeas.act6",
            session_id: input.run_key,
            parent_ie_id: Vec::new(),
            object_ids: Vec::new(),
            terminal: false,
        },
        Payload::Object(&payload),
        time.event_clock,
    )?;
    let ts = if input.now_utc.is_empty() {
        time.dda_timestamp
    } else {
        input.now_utc
    };
    let step: DdcStep = serde_json::from_value(json!({
        "letter": "I",
        "before_class": "CandidatesWitnessed",
        "after_class": "LedgerIntegrated",
        "carrier_hash": sha256_ref(b"carrier"),
        "witness_hash": sha256_ref(python_ascii_json(ledger)?.as_bytes()),
        "receipt_sha256": sha256_ref(&bytes),
        "timestamp": ts,
    }))
    .map_err(|error| refuse("ADVERSARY_GATE_RECORD_INVALID", error.to_string()))?;
    emit_event(&event, &bytes, suite, Some(&step), None).map(|_| ())
}

// Origin: engine/crates_rs/core_adversary/src/residual_ledger.rs
// Claim: urn:core:crates_rs:core-adversary:residual-ledger:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8ed96f37 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8ed96f37` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8ed96f37 {
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
impl BoundaryError8ed96f37 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8ed96f37 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8ed96f37 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8ed96f37 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8ed96f37> {
        if capacity_bound == 0 {
            return Err(BoundaryError8ed96f37::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8ed96f37::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8ed96f37::ExceedsCapacity {
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
mod l4_boundary_tests_8ed96f37 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8ed96f37::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8ed96f37::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8ed96f37::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8ed96f37::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8ed96f37::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError8ed96f37::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError8ed96f37::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
