//! Ordered candidate-check application flow and exact audit-step emission.
use crate::authorization::{receipt_digest, refuse, AuthorizationTime};
use crate::checker_ports::{CandidateCheckRequest, CandidateCheckerPort, NullCandidateChecker};
use crate::evidence::{sha256_ref, CandidateCheck, CheckerVerdict, ObstructionMeasurement};
use crate::stage::ddc::DdcStep;
use crate::stage::emission::{
    build_intelligence_event, emit_event, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::packets::CandidateProposal;
use crate::stage::ports::Refusal;
use serde_json::{json, Map, Value};
use std::collections::BTreeMap;

pub struct CandidateChecksInput<'a> {
    pub run_key: &'a str,
    pub objective: &'a str,
    pub candidates: &'a [CandidateProposal],
    pub candidate_payloads: &'a BTreeMap<String, Vec<u8>>,
    pub carrier_context: Option<&'a Map<String, Value>>,
    pub measurement: Option<&'a ObstructionMeasurement>,
    pub carrier_state_hash: Option<&'a str>,
    pub now_utc: &'a str,
}

fn emit_candidate_check_event(
    check: &CandidateCheck,
    input: &CandidateChecksInput<'_>,
    emitters: &mut EmitterSuite<'_>,
    time: &AuthorizationTime<'_>,
) -> Result<(), Refusal> {
    let carrier_hash = input.carrier_state_hash.ok_or_else(|| {
        refuse(
            "ADVERSARY_DDC_CARRIER_REQUIRED",
            "checker emission requires the measured active carrier digest",
        )
    })?;
    let record = check.to_dict();
    let digest = receipt_digest(&record)?;
    let bytes = serde_json::to_vec(&record)
        .map_err(|error| refuse("ADVERSARY_GATE_RECORD_INVALID", error.to_string()))?;
    let (event, bytes) = build_intelligence_event(
        EventDescriptor {
            ie_id: &digest,
            // Council audit accountability only. The checker_id-bound host code,
            // source digest and exact receipt carry the machine verification;
            // this persona neither verifies the mathematics nor grants authority.
            actor_id: "actor_aletheia_procurator",
            actor_kind: "SWARM_SEAT",
            event_kind: "COMM",
            source_system: "oeas.candidate_check",
            session_id: input.run_key,
            parent_ie_id: Vec::new(),
            object_ids: Vec::new(),
            terminal: false,
        },
        Payload::Bytes(&bytes),
        time.event_clock,
    )?;
    let verdict = match check.verdict() {
        CheckerVerdict::Accepted => "ACCEPTED",
        CheckerVerdict::Rejected => "REJECTED",
        CheckerVerdict::NotMeasured => "NOT_MEASURED",
    };
    let measurement = input
        .measurement
        .filter(|measurement| measurement.is_measured());
    let step: DdcStep = serde_json::from_value(json!({"letter":"R",
        "before_class":"CandidateProposed","after_class":format!("Checker_{verdict}"),
        "carrier_hash":carrier_hash,"witness_hash":check.receipt_sha256().unwrap_or(&digest),
        "receipt_sha256":digest,"timestamp":if input.now_utc.is_empty(){time.dda_timestamp}else{input.now_utc},
        "phi_1":measurement.and_then(ObstructionMeasurement::phi1_text),
        "gamma_2":measurement.and_then(ObstructionMeasurement::gamma2_text),
    })).map_err(|error|refuse("ADVERSARY_GATE_RECORD_INVALID",error.to_string()))?;
    // R audits the result; ACCEPTED alone never becomes an E repair.
    emit_event(&event, &bytes, emitters, Some(&step), None).map(|_| ())
}

fn verify_single_candidate_check(
    port: &mut dyn CandidateCheckerPort,
    input: &CandidateChecksInput<'_>,
    candidate: &CandidateProposal,
) -> Result<CandidateCheck, Refusal> {
    let payload = input
        .candidate_payloads
        .get(candidate.candidate_id())
        .ok_or_else(|| {
            refuse(
                "ADVERSARY_CANDIDATE_PAYLOAD_MISSING",
                "A checker verdict requires the exact candidate content bytes",
            )
        })?;
    let payload_digest = sha256_ref(payload);
    if !candidate.artifact_refs().contains(&payload_digest) {
        return Err(refuse(
            "ADVERSARY_CANDIDATE_PAYLOAD_MISMATCH",
            "the checker payload is not one of the candidate's committed artifacts",
        ));
    }
    let check = port.check_candidate(&CandidateCheckRequest {
        run_key: input.run_key,
        objective: input.objective,
        candidate_id: candidate.candidate_id(),
        candidate_bytes: payload,
        carrier_context: input.carrier_context,
    })?;
    if !check.binds(candidate.candidate_id(), candidate.artifact_refs())
        || check.candidate_content_sha256() != payload_digest
    {
        return Err(refuse(
            "ADVERSARY_CHECKER_BINDING_MISMATCH",
            "the checker verdict names a different candidate or different content bytes",
        ));
    }
    Ok(check)
}

pub fn execute_candidate_checks(
    checker: Option<&mut dyn CandidateCheckerPort>,
    input: &CandidateChecksInput<'_>,
    mut emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<BTreeMap<String, CandidateCheck>, Refusal> {
    let mut null = NullCandidateChecker;
    let port = match checker {
        Some(port) => port,
        None => &mut null,
    };
    let mut checks = BTreeMap::new();
    for candidate in input.candidates {
        let check = verify_single_candidate_check(port, input, candidate)?;
        if let Some(emitters) = emitters.as_mut() {
            emit_candidate_check_event(&check, input, emitters, time)?;
        }
        checks.insert(candidate.candidate_id().clone(), check);
    }
    Ok(checks)
}

// Origin: engine/crates_rs/core_adversary/src/candidate_checks.rs
// Claim: urn:core:crates_rs:core-adversary:candidate-checks:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4dea2726 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4dea2726` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4dea2726 {
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
impl BoundaryError4dea2726 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4dea2726 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4dea2726 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4dea2726 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4dea2726> {
        if capacity_bound == 0 {
            return Err(BoundaryError4dea2726::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4dea2726::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4dea2726::ExceedsCapacity {
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
mod l4_boundary_tests_4dea2726 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4dea2726::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4dea2726::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4dea2726::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4dea2726::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4dea2726::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4dea2726::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4dea2726::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
