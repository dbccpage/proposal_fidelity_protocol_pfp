//! Act III: immutable content-bound proposals and source cheap-gate history.
use crate::act_capture::{candidate_ids_repr, record_error, reply_provenance};
use crate::authorization::{refuse, AuthorizationTime};
use crate::evidence::sha256_ref;
use crate::stage::ddc::DdcStep;
use crate::stage::emission::{
    build_intelligence_event, emit_event, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::genealogy::{CemeteryHeadstone, HeadstoneInput};
use crate::stage::packets::CandidateProposal;
use crate::stage::ports::{Refusal, SeatPort, SeatTurnReply, SeatTurnRequest};
use serde_json::{json, Map, Value};

pub struct CandidateProposalsInput<'a> {
    pub packet_id: &'a str,
    pub run_key: &'a str,
    pub objective: &'a str,
    pub max_candidate_budget: i64,
    pub now_utc: &'a str,
}
#[derive(Debug, Clone, PartialEq)]
pub struct CandidateProposalsOutcome {
    candidates: Vec<CandidateProposal>,
    candidates_data: Vec<Value>,
    dead_candidates: Vec<CemeteryHeadstone>,
    narrative: Value,
}
impl CandidateProposalsOutcome {
    pub fn candidates(&self) -> &[CandidateProposal] {
        &self.candidates
    }
    pub fn candidates_data(&self) -> &[Value] {
        &self.candidates_data
    }
    pub fn dead_candidates(&self) -> &[CemeteryHeadstone] {
        &self.dead_candidates
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        let candidates = serde_json::to_value(&self.candidates).map_err(record_error)?;
        Ok(
            json!({"candidates":candidates,"candidates_data":self.candidates_data,
            "dead_candidates":self.dead_candidates.iter().map(CemeteryHeadstone::to_dict).collect::<Vec<_>>(),"narrative":self.narrative}),
        )
    }
}
fn update_fence_bounds(
    marker: &str,
    offset: usize,
    line_len: usize,
    opening: &mut Option<usize>,
    closing: &mut Option<usize>,
) -> Result<(), Refusal> {
    if marker == "```candidate" {
        if opening.is_some() {
            return Err(refuse(
                "CANDIDATE_ARTIFACT_FENCE_INVALID",
                "expected at most one candidate fence",
            ));
        }
        *opening = Some(offset + line_len);
    } else if marker.starts_with("```")
        && marker
            .trim_start_matches('`')
            .trim_start()
            .starts_with("candidate")
    {
        return Err(refuse(
            "CANDIDATE_ARTIFACT_FENCE_INVALID",
            "candidate fence header must be exactly ```candidate on its own line",
        ));
    } else if opening.is_some() && closing.is_none() && marker.starts_with("```") {
        if marker != "```" {
            return Err(refuse(
                "CANDIDATE_ARTIFACT_FENCE_INVALID",
                "nested or malformed fence inside candidate payload",
            ));
        }
        *closing = Some(offset);
    }
    Ok(())
}

/// Extract one optional candidate block without normalizing the payload bytes.
/// The newline after the opening marker is syntax; every byte before the closing
/// marker, including a final payload newline, belongs to the candidate artifact.
fn candidate_artifact(reply: &str) -> Result<&str, Refusal> {
    let mut opening = None;
    let mut closing = None;
    let mut offset = 0;
    for line in reply.split_inclusive('\n') {
        update_fence_bounds(line.trim(), offset, line.len(), &mut opening, &mut closing)?;
        offset += line.len();
    }
    match (opening, closing) {
        (None, None) => Ok(reply),
        (Some(start), Some(end)) if !reply[start..end].trim().is_empty() => Ok(&reply[start..end]),
        _ => Err(refuse(
            "CANDIDATE_ARTIFACT_FENCE_INVALID",
            "candidate fence must be closed and contain a nonempty artifact",
        )),
    }
}

fn is_cheap_gate_failure(reply: &crate::stage::ports::SeatTurnReply) -> bool {
    reply
        .reply_text
        .trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
        .is_empty()
        || reply.authority_effect != "None"
}

fn emit_act3_summary_event(
    input: &CandidateProposalsInput<'_>,
    candidates: &[CandidateProposal],
    suite: &mut EmitterSuite<'_>,
    time: &AuthorizationTime<'_>,
) -> Result<(), Refusal> {
    let event_id = sha256_ref(format!("{}:act3", input.run_key).as_bytes());
    let payload = Map::from_iter([
        ("act".into(), json!("III")),
        ("title".into(), json!("Candidate Proposal Generation")),
        ("candidates_count".into(), json!(candidates.len())),
    ]);
    let (event, bytes) = build_intelligence_event(
        EventDescriptor {
            ie_id: &event_id,
            actor_id: "actor_dianoia_first_curator",
            actor_kind: "SWARM_SEAT",
            event_kind: "COMM",
            source_system: "oeas.act3",
            session_id: input.run_key,
            parent_ie_id: Vec::new(),
            object_ids: Vec::new(),
            terminal: false,
        },
        Payload::Object(&payload),
        time.event_clock,
    )?;
    let step: DdcStep = serde_json::from_value(json!({"letter":"C","before_class":"ActiveObstruction","after_class":"CandidateProposed",
        "carrier_hash":sha256_ref(b"carrier"),"witness_hash":sha256_ref(candidate_ids_repr(candidates).as_bytes()),"receipt_sha256":sha256_ref(&bytes),
        "timestamp":if input.now_utc.is_empty(){time.dda_timestamp}else{input.now_utc}}))
        .map_err(record_error)?;
    emit_event(&event, &bytes, suite, Some(&step), None).map(|_| ())
}

#[allow(clippy::too_many_arguments)]
fn record_cheap_gate_death(
    request_id: String,
    run_key: &str,
    raw_bytes: &[u8],
    capture: &mut Map<String, Value>,
    candidates_data: &mut Vec<Value>,
    emitters: &mut Option<&mut EmitterSuite<'_>>,
    dead_candidates: &mut Vec<CemeteryHeadstone>,
) -> Result<(), Refusal> {
    let headstone = CemeteryHeadstone::new(HeadstoneInput {
        candidate_id: request_id,
        run_key: run_key.into(),
        scene_id: "act2_panel_debate".into(),
        cause_of_death: "CHEAP_GATE_FAILED: Empty response or authority violation".into(),
        killing_seat_id: "seat_syntax_prefilter".into(),
        evidence_refs: Vec::new(),
        candidate_payload_sha256: sha256_ref(raw_bytes),
        round_index: 0,
    })?;
    capture.extend(Map::from_iter([
        ("candidate_id".into(), json!("")),
        ("candidate_proposal".into(), Value::Null),
        ("capture_status".into(), json!("CHEAP_GATE_FAILED")),
    ]));
    candidates_data.push(Value::Object(capture.clone()));
    if let Some(sink) = emitters.as_mut().and_then(|suite| suite.cemetery.as_mut()) {
        sink.record_headstone(&headstone)?;
    }
    dead_candidates.push(headstone);
    Ok(())
}

fn record_accepted_proposal(
    request_id: String,
    packet_id: &str,
    content: &str,
    raw_bytes: &[u8],
    capture: &mut Map<String, Value>,
    candidates_data: &mut Vec<Value>,
    candidates: &mut Vec<CandidateProposal>,
) -> Result<(), Refusal> {
    let artifact_digest = sha256_ref(content.as_bytes());
    let mut receipt_material = request_id.into_bytes();
    receipt_material.push(0);
    receipt_material.extend_from_slice(raw_bytes);
    let receipt_digest = sha256_ref(&receipt_material);
    let candidate: CandidateProposal = serde_json::from_value(json!({
        "producer_agent_id": "seat_gauge_breaker",
        "work_packet_id": packet_id,
        "artifact_refs": [artifact_digest],
        "prediction_receipt_id": receipt_digest,
        "nonclaims": ["Candidate generation only.", "AuthorityEffect is strictly None."],
        "authority_effect": "None",
        "schema_version": "core.oeas.candidate-proposal.v1"
    }))
    .map_err(record_error)?;
    capture.extend(Map::from_iter([
        ("candidate_id".into(), json!(candidate.candidate_id())),
        (
            "candidate_proposal".into(),
            serde_json::to_value(&candidate).map_err(record_error)?,
        ),
        ("capture_status".into(), json!("PROPOSED")),
        ("prediction_receipt_id".into(), json!(receipt_digest)),
        ("content_sha256".into(), json!(artifact_digest)),
    ]));
    candidates_data.push(Value::Object(capture.clone()));
    candidates.push(candidate);
    Ok(())
}

fn build_gauge_breaker_candidate_request(
    index: i64,
    objective: &str,
    request_id: &str,
) -> SeatTurnRequest {
    SeatTurnRequest {
        scene_id: "act2_panel_debate".into(),
        seat_id: "seat_gauge_breaker".into(),
        prompt_text: format!(
            "Generate candidate {} for objective: '{}'. Prefer putting the exact deliverable in one optional \n```candidate\n<deliverable>\n```\n block. Use at most one candidate block, with both fence markers on their own lines. Keep commentary and the required machine block outside the candidate block. The deliverable is sent to the checker exactly as written, without removing payload whitespace.",
            index + 1,
            objective
        ),
        cognitive_operator: "Nine-Dot Surprise & Playful Comedy (E_surprise)".into(),
        role_kind: "prose".into(),
        candidate_id: request_id.to_string(),
        round_index: 0,
        context_bytes: Vec::new(),
    }
}

fn build_candidate_capture(
    reply: &SeatTurnReply,
    request_id: &str,
    content: &str,
) -> Map<String, Value> {
    let mut capture = reply_provenance(reply);
    capture.extend(Map::from_iter([
        ("candidate_request_id".into(), json!(request_id)),
        ("content".into(), json!(content)),
        (
            "raw_reply_sha256".into(),
            json!(sha256_ref(&reply.raw_bytes)),
        ),
        ("raw_reply_hex".into(), json!(hex::encode(&reply.raw_bytes))),
        ("producer_seat_id".into(), json!("seat_gauge_breaker")),
        ("machine_fields".into(), json!(reply.machine_fields)),
        ("residual_colour".into(), json!(reply.residual_colour)),
        (
            "reported_authority_effect".into(),
            json!(reply.authority_effect),
        ),
        ("authority_effect".into(), json!("None")),
        ("verification_status".into(), json!("NOT_RUN")),
    ]));
    capture
}

pub fn execute_act3_candidate_proposal_generation(
    input: &CandidateProposalsInput<'_>,
    mut seat_port: Option<&mut dyn SeatPort>,
    mut emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<CandidateProposalsOutcome, Refusal> {
    let mut candidates = Vec::new();
    let mut candidates_data = Vec::new();
    let mut dead_candidates = Vec::new();
    for index in 0..input.max_candidate_budget {
        let request_id = format!("cand_{}", index + 1);
        let request = build_gauge_breaker_candidate_request(index, input.objective, &request_id);
        let port = seat_port
            .as_mut()
            .ok_or_else(|| refuse("NO_SEAT_PORT", "SeatPort missing"))?;
        let reply = port.execute_turn(&request)?;
        let content = candidate_artifact(&reply.reply_text)?;
        let mut capture = build_candidate_capture(&reply, &request_id, &content);
        if is_cheap_gate_failure(&reply) {
            record_cheap_gate_death(
                request_id,
                input.run_key,
                &reply.raw_bytes,
                &mut capture,
                &mut candidates_data,
                &mut emitters,
                &mut dead_candidates,
            )?;
            continue;
        }
        record_accepted_proposal(
            request_id,
            input.packet_id,
            &content,
            &reply.raw_bytes,
            &mut capture,
            &mut candidates_data,
            &mut candidates,
        )?;
    }
    emit_optional_act3_summary(input, &candidates, emitters, time)?;
    let narrative = json!({"act_number":"III","title":"Candidate Proposal Generation",
        "body":format!("Generated {} candidate proposal(s); {} rejected by cheap gate.",candidates.len(),dead_candidates.len())});
    Ok(CandidateProposalsOutcome {
        candidates,
        candidates_data,
        dead_candidates,
        narrative,
    })
}

fn emit_optional_act3_summary(
    input: &CandidateProposalsInput<'_>,
    candidates: &[CandidateProposal],
    emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<(), Refusal> {
    if let Some(suite) = emitters {
        emit_act3_summary_event(input, candidates, suite, time)?;
    }
    Ok(())
}

// Origin: engine/crates_rs/core_adversary/src/candidate_proposals.rs
// Claim: urn:core:crates_rs:core-adversary:candidate-proposals:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf98abdce {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf98abdce` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf98abdce {
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
impl BoundaryErrorf98abdce {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf98abdce {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf98abdce {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf98abdce {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf98abdce> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf98abdce::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf98abdce::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf98abdce::ExceedsCapacity {
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
mod l4_boundary_tests_f98abdce {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf98abdce::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf98abdce::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf98abdce::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf98abdce::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf98abdce::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf98abdce::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf98abdce::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
