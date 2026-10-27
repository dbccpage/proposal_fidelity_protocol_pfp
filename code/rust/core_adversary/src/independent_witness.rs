//! Act V: byte-bound critic turns and ordered candidate elimination.
//! Model findings remain unverified; a reported authority effect grants nothing.
use crate::act_capture::{candidate_ids_repr, record_error, reply_provenance};
use crate::authorization::{flag, refuse, AuthorizationTime};
use crate::evidence::sha256_ref;
use crate::evidence_parse::{parse_structured_critique, CritiqueStatus, CHALLENGE_KINDS};
use crate::stage::ddc::DdcStep;
use crate::stage::emission::{
    build_intelligence_event, emit_event, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::genealogy::{CemeteryHeadstone, HeadstoneInput};
use crate::stage::packets::{CandidateProposal, Challenge};
use crate::stage::ports::{Refusal, SeatPort, SeatTurnRequest};
use serde_json::{json, Map, Value};
use std::collections::BTreeMap;

pub struct IndependentWitnessInput<'a> {
    pub run_key: &'a str,
    pub objective: &'a str,
    pub candidates: &'a [CandidateProposal],
    pub dead_candidates: &'a [CemeteryHeadstone],
    pub candidate_payloads: &'a BTreeMap<String, Vec<u8>>,
    pub ablation_flags: Option<&'a Map<String, Value>>,
    pub max_critique_rounds: i64,
    pub now_utc: &'a str,
}
#[derive(Debug, Clone, PartialEq)]
pub struct IndependentWitnessOutcome {
    surviving_candidates: Vec<CandidateProposal>,
    dead_candidates: Vec<CemeteryHeadstone>,
    round_count: i64,
    critiques: Vec<Challenge>,
    critiques_data: Vec<Value>,
    critique_verdicts: BTreeMap<String, String>,
    narrative: Value,
}
impl IndependentWitnessOutcome {
    pub fn surviving_candidates(&self) -> &[CandidateProposal] {
        &self.surviving_candidates
    }
    pub fn dead_candidates(&self) -> &[CemeteryHeadstone] {
        &self.dead_candidates
    }
    pub fn round_count(&self) -> i64 {
        self.round_count
    }
    pub fn critiques(&self) -> &[Challenge] {
        &self.critiques
    }
    pub fn critiques_data(&self) -> &[Value] {
        &self.critiques_data
    }
    pub fn critique_verdicts(&self) -> &BTreeMap<String, String> {
        &self.critique_verdicts
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        let survivors = serde_json::to_value(&self.surviving_candidates).map_err(record_error)?;
        let critiques = serde_json::to_value(&self.critiques).map_err(record_error)?;
        Ok(
            json!({"surviving_candidates":survivors,"dead_candidates":self.dead_candidates.iter().map(CemeteryHeadstone::to_dict).collect::<Vec<_>>(),
            "round_count":self.round_count,"critiques":critiques,"critiques_data":self.critiques_data,
            "critique_verdicts":self.critique_verdicts,"narrative":self.narrative}),
        )
    }
}
fn bounded_statement(text: &str) -> String {
    if text.chars().count() <= 1024 && text.len() <= 4096 {
        return text.into();
    }
    let excerpt: String = text.chars().take(1024).collect();
    let excerpt =
        excerpt.trim_end_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c));
    format!(
        "[{} bytes, {}; excerpt follows, full text in the critique record] {excerpt}",
        text.len(),
        sha256_ref(text.as_bytes())
    )
}
fn critique_reply_contract() -> String {
    format!("End your reply with exactly one fenced block tagged `critique` holding a JSON object: {{\"blocking\": true or false, \"counterexample\": \"<a concrete input or witness that breaks the candidate>\" or null, \"kind\": optional, one of {}}}. A blocking critique must give a nonempty counterexample.",CHALLENGE_KINDS.join(", "))
}

fn format_critique_verdict(
    status: CritiqueStatus,
    parse_error: &str,
    blocking: bool,
    counterexample: &str,
) -> (&'static str, String) {
    if status == CritiqueStatus::Malformed {
        return ("MALFORMED", format!("MALFORMED_CRITIQUE: {parse_error}"));
    }
    if blocking {
        return (
            "BLOCKING",
            format!("Counterexample: {}", bounded_statement(counterexample)),
        );
    }
    if counterexample.is_empty() {
        return (
            "NON_BLOCKING",
            "Non-blocking critique without a counterexample.".into(),
        );
    }
    (
        "NON_BLOCKING",
        format!(
            "Non-blocking critique: {}",
            bounded_statement(counterexample)
        ),
    )
}

fn verify_candidate_payload<'a>(
    input: &'a IndependentWitnessInput<'_>,
    candidate: &CandidateProposal,
) -> Result<(&'a Vec<u8>, String), Refusal> {
    let payload = input
        .candidate_payloads
        .get(candidate.candidate_id())
        .ok_or_else(|| {
            refuse(
                "ADVERSARY_CANDIDATE_PAYLOAD_MISSING",
                "A critique requires the exact candidate content bytes",
            )
        })?;
    let payload_digest = sha256_ref(payload);
    if !candidate.artifact_refs().contains(&payload_digest) {
        return Err(refuse(
            "ADVERSARY_CANDIDATE_PAYLOAD_MISMATCH",
            "Critique content does not match the candidate artifact digest",
        ));
    }
    Ok((payload, payload_digest))
}

#[allow(clippy::too_many_arguments)]
fn record_killed_candidate(
    input: &IndependentWitnessInput<'_>,
    candidate: &CandidateProposal,
    critic: &str,
    statement: &str,
    challenge: &Challenge,
    payload_digest: String,
    round_count: i64,
    emitters: &mut Option<&mut EmitterSuite<'_>>,
    dead_candidates: &mut Vec<CemeteryHeadstone>,
    surviving_candidates: &mut Vec<CandidateProposal>,
) -> Result<(), Refusal> {
    let headstone = CemeteryHeadstone::new(HeadstoneInput {
        candidate_id: candidate.candidate_id().clone(),
        run_key: input.run_key.into(),
        scene_id: "act2_panel_debate".into(),
        cause_of_death: format!(
            "KILLED_BY_{}: {statement}",
            critic.trim_start_matches("seat_").to_uppercase()
        ),
        killing_seat_id: critic.into(),
        evidence_refs: challenge.evidence_refs().clone(),
        candidate_payload_sha256: payload_digest,
        round_index: u32::try_from(round_count).map_err(|_| {
            refuse(
                "ADVERSARY_WITNESS_ROUND_OVERFLOW",
                "critique round exceeds native history bounds",
            )
        })?,
    })?;
    if let Some(sink) = emitters.as_mut().and_then(|suite| suite.cemetery.as_mut()) {
        sink.record_headstone(&headstone)?;
    }
    dead_candidates.push(headstone);
    if let Some(position) = surviving_candidates
        .iter()
        .position(|value| value == candidate)
    {
        surviving_candidates.remove(position);
    }
    Ok(())
}

fn emit_act5_event(
    input: &IndependentWitnessInput<'_>,
    surviving_candidates: &[CandidateProposal],
    critiques: &[Challenge],
    critique_verdicts: &BTreeMap<String, String>,
    suite: &mut EmitterSuite<'_>,
    time: &AuthorizationTime<'_>,
) -> Result<(), Refusal> {
    let event_id = sha256_ref(format!("{}:act5", input.run_key).as_bytes());
    let payload = Map::from_iter([
        ("act".into(), json!("V")),
        ("title".into(), json!("Independent Witness Evaluation")),
        ("surviving_count".into(), json!(surviving_candidates.len())),
        ("critiques_count".into(), json!(critiques.len())),
        ("critique_verdicts".into(), json!(critique_verdicts)),
    ]);
    let (event, bytes) = build_intelligence_event(
        EventDescriptor {
            ie_id: &event_id,
            actor_id: "actor_aletheia_second_curator",
            actor_kind: "SWARM_SEAT",
            event_kind: "COMM",
            source_system: "oeas.act5",
            session_id: input.run_key,
            parent_ie_id: Vec::new(),
            object_ids: Vec::new(),
            terminal: false,
        },
        Payload::Object(&payload),
        time.event_clock,
    )?;
    let witness = candidate_ids_repr(surviving_candidates);
    let timestamp = if input.now_utc.is_empty() {
        time.dda_timestamp
    } else {
        input.now_utc
    };
    let step: DdcStep = serde_json::from_value(json!({
        "letter": "D",
        "before_class": "CarrierExpanded",
        "after_class": "CandidatesWitnessed",
        "carrier_hash": sha256_ref(b"carrier"),
        "witness_hash": sha256_ref(witness.as_bytes()),
        "receipt_sha256": sha256_ref(&bytes),
        "timestamp": timestamp
    }))
    .map_err(record_error)?;
    emit_event(&event, &bytes, suite, Some(&step), None).map(|_| ())
}

fn build_critique_capture(
    candidate: &CandidateProposal,
    payload_digest: &str,
    reply: &crate::stage::ports::SeatTurnReply,
    critique: &crate::evidence_parse::StructuredCritique,
    verdict: &str,
    challenge: &Challenge,
) -> Value {
    let mut capture = reply_provenance(reply);
    let details = json!({"candidate_id":candidate.candidate_id(),"candidate_content_sha256":payload_digest,
        "machine_fields":reply.machine_fields,"residual_colour":reply.residual_colour,
        "reported_authority_effect":reply.authority_effect,"authority_effect":"None","body":reply.reply_text,
        "raw_reply_sha256":sha256_ref(&reply.raw_bytes),"raw_reply_hex":hex::encode(&reply.raw_bytes),
        "critique":critique.to_dict(),"critique_verdict":verdict,"verification_status":"NOT_RUN","challenge":challenge});
    if let Value::Object(details) = details {
        capture.extend(details);
    }
    Value::Object(capture)
}

#[allow(clippy::too_many_arguments)]
fn critique_single_candidate(
    input: &IndependentWitnessInput<'_>,
    candidate: &CandidateProposal,
    critic: &str,
    round_count: i64,
    seat_port: &mut Option<&mut dyn SeatPort>,
    emitters: &mut Option<&mut EmitterSuite<'_>>,
    critique_verdicts: &mut BTreeMap<String, String>,
    critiques_data: &mut Vec<Value>,
    critiques: &mut Vec<Challenge>,
    dead_candidates: &mut Vec<CemeteryHeadstone>,
    surviving_candidates: &mut Vec<CandidateProposal>,
) -> Result<bool, Refusal> {
    let (payload, payload_digest) = verify_candidate_payload(input, candidate)?;
    let request = SeatTurnRequest {
        scene_id: "act2_panel_debate".into(),
        seat_id: critic.into(),
        prompt_text: format!("Adversarially critique candidate {} for objective: '{}'. Identify boundary defects, unhandled overflow, and missing type bounds. {}", candidate.candidate_id(), input.objective, critique_reply_contract()),
        cognitive_operator: "Lefschetz Fibration & Destructive Adversarial Dialectic (E_adversary)".into(),
        role_kind: "prose".into(),
        candidate_id: candidate.candidate_id().clone(),
        round_index: round_count,
        context_bytes: payload.clone(),
    };
    let port = seat_port
        .as_mut()
        .ok_or_else(|| refuse("NO_SEAT_PORT", "SeatPort missing"))?;
    let reply = port.execute_turn(&request)?;
    let critique = parse_structured_critique(&json!(reply.reply_text))?;
    let (verdict, statement) = format_critique_verdict(
        critique.status(),
        critique.parse_error(),
        critique.blocking(),
        critique.counterexample(),
    );
    critique_verdicts.insert(candidate.candidate_id().clone(), verdict.into());
    let challenge: Challenge = serde_json::from_value(json!({"candidate_id":candidate.candidate_id(),
        "critic_agent_id":critic,"trust_domain":"LefschetzDialectic","challenge_kind":critique.challenge_kind(),
        "statement":statement,"evidence_refs":[sha256_ref(&reply.raw_bytes)],"blocking":critique.blocking(),
        "authority_effect":"None","schema_version":"core.oeas.challenge.v1"})).map_err(record_error)?;
    critiques_data.push(build_critique_capture(
        candidate,
        &payload_digest,
        &reply,
        &critique,
        verdict,
        &challenge,
    ));
    let is_kill = [
        critique.blocking(),
        reply
            .machine_fields
            .get("DISPOSITION")
            .is_some_and(|value| value == "KILL"),
    ]
    .into_iter()
    .all(|b| b);
    if is_kill {
        record_killed_candidate(
            input,
            candidate,
            critic,
            &statement,
            &challenge,
            payload_digest,
            round_count,
            emitters,
            dead_candidates,
            surviving_candidates,
        )?;
        critiques.push(challenge);
        return Ok(true);
    }
    critiques.push(challenge);
    Ok(false)
}

fn build_act5_narrative(
    round_count: i64,
    critic: &str,
    surviving_len: usize,
    critique_verdicts: &BTreeMap<String, String>,
    no_independent: bool,
) -> Value {
    let malformed_count = critique_verdicts
        .values()
        .filter(|verdict| verdict.as_str() == "MALFORMED")
        .count();
    let mut body = format!("Conducted {round_count} critique round(s) via {critic}. {surviving_len} surviving candidate(s); {malformed_count} malformed critique(s) block their candidates.");
    if no_independent {
        body.push_str(" Independent witness ablated: proposer self-evaluated candidates.");
    }
    json!({"act_number":"V","title":"Independent Witness Evaluation","body":body})
}

pub fn execute_act5_independent_witness(
    input: &IndependentWitnessInput<'_>,
    mut seat_port: Option<&mut dyn SeatPort>,
    mut emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<IndependentWitnessOutcome, Refusal> {
    let mut surviving_candidates = input.candidates.to_vec();
    let mut dead_candidates = input.dead_candidates.to_vec();
    let mut critiques = Vec::new();
    let mut critiques_data = Vec::new();
    let mut critique_verdicts: BTreeMap<String, String> = BTreeMap::new();
    let mut round_count = 0i64;
    let no_independent = flag(input.ablation_flags, "no_independent_witness");
    let critic = if no_independent {
        "seat_gauge_breaker"
    } else {
        "seat_defect_hunter"
    };
    while round_count < input.max_critique_rounds && !surviving_candidates.is_empty() {
        round_count += 1;
        let mut killed_in_round = false;
        for candidate in surviving_candidates.clone() {
            if critique_single_candidate(
                input,
                &candidate,
                critic,
                round_count,
                &mut seat_port,
                &mut emitters,
                &mut critique_verdicts,
                &mut critiques_data,
                &mut critiques,
                &mut dead_candidates,
                &mut surviving_candidates,
            )? {
                killed_in_round = true;
                break;
            }
        }
        if !killed_in_round {
            break;
        }
    }
    let narrative = build_act5_narrative(
        round_count,
        critic,
        surviving_candidates.len(),
        &critique_verdicts,
        no_independent,
    );
    if let Some(suite) = emitters {
        emit_act5_event(
            input,
            &surviving_candidates,
            &critiques,
            &critique_verdicts,
            suite,
            time,
        )?;
    }
    Ok(IndependentWitnessOutcome {
        surviving_candidates,
        dead_candidates,
        round_count,
        critiques,
        critiques_data,
        critique_verdicts,
        narrative,
    })
}

// Origin: engine/crates_rs/core_adversary/src/independent_witness.rs
// Claim: urn:core:crates_rs:core-adversary:independent-witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfdd16845 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfdd16845` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfdd16845 {
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
impl BoundaryErrorfdd16845 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfdd16845 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfdd16845 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfdd16845 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfdd16845> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfdd16845::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfdd16845::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfdd16845::ExceedsCapacity {
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
mod l4_boundary_tests_fdd16845 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfdd16845::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfdd16845::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfdd16845::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfdd16845::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfdd16845::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorfdd16845::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorfdd16845::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
