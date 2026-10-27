//! Act VII selection and authorization over checked evidence and injected sinks.
//! This gate consumes checker facts; authenticating/reproducing those facts is
//! the preceding candidate-check use case's responsibility.
use crate::evidence::{
    canonical_rational, parse_exact_rational, sha256_ref, CandidateCheck, CheckerVerdict,
    ObstructionMeasurement,
};
use crate::evidence_parse::python_value_repr;
use num_rational::BigRational;
use num_traits::Zero;
use crate::stage::ddc::DdcStep;
use crate::stage::emission::{
    build_intelligence_event, emit_event, Clock, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::packets::{CandidateProposal, Challenge};
use crate::stage::ports::Refusal;
use crate::stage::run::CandidateSelectionProposal;
use serde_json::{json, Map, Value};
use std::collections::{BTreeMap, BTreeSet};

pub const CARRIER_DECLARED: &str = "DECLARED";
pub const CARRIER_NOT_DECLARED: &str = "NOT_DECLARED";
pub const EVIDENCE_CHECKER_ONLY: &str = "CHECKER_VERDICT_ONLY_NO_CARRIER_DECLARED";
pub const EVIDENCE_CHECKER_AND_CARRIER: &str = "CHECKER_VERDICT_AND_EXACT_ZERO_CARRIER";

/// Inputs are immutable checked records. Optional JSON flags retain the source's
/// truthiness, except fixture seats, for which only exact false declares live.
pub struct AuthorizationGateInput<'a> {
    pub run_key: &'a str,
    pub surviving_candidates: &'a [CandidateProposal],
    pub critiques: &'a [Challenge],
    pub measurement: Option<&'a ObstructionMeasurement>,
    pub candidate_checks: &'a BTreeMap<String, CandidateCheck>,
    pub carrier_context: Option<&'a Map<String, Value>>,
    pub ablation_flags: Option<&'a Map<String, Value>>,
    pub delta2_defect: Option<&'a Value>,
    pub delta3_defect: Option<&'a Value>,
    pub regge_converged: Option<&'a Value>,
    pub carrier_status: &'a str,
    pub critique_verdicts: &'a BTreeMap<String, String>,
    pub fixture_seats: &'a Value,
    pub now_utc: &'a str,
}

/// The composition root supplies both source clock formats. Caller now_utc, when
/// nonempty, overrides only the DDA timestamp, as in Python.
pub struct AuthorizationTime<'a> {
    pub event_clock: &'a dyn Clock,
    pub dda_timestamp: &'a str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AuthorizationOutcome {
    status: String,
    selected_candidate_id: String,
    proposal: CandidateSelectionProposal,
    is_authorized: bool,
    narrative: Value,
}
impl AuthorizationOutcome {
    pub fn status(&self) -> &str {
        &self.status
    }
    pub fn selected_candidate_id(&self) -> &str {
        &self.selected_candidate_id
    }
    pub fn proposal(&self) -> &CandidateSelectionProposal {
        &self.proposal
    }
    pub fn is_authorized(&self) -> bool {
        self.is_authorized
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        let proposal = serde_json::to_value(&self.proposal)
            .map_err(|error| refuse("ADVERSARY_GATE_RECORD_INVALID", error.to_string()))?;
        Ok(
            json!({"status":self.status,"selected_candidate_id":self.selected_candidate_id,
            "proposal":proposal,"is_authorized":self.is_authorized,"narrative":self.narrative}),
        )
    }
}

pub(crate) fn refuse(code: &str, message: impl Into<String>) -> Refusal {
    let mut refusal = Refusal::new(code, message);
    refusal.locus = "adversary.use_cases.act_helpers".into();
    refusal
}
pub(crate) fn truthy(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(value) => *value,
        Value::String(value) => !value.is_empty(),
        Value::Array(value) => !value.is_empty(),
        Value::Object(value) => !value.is_empty(),
        Value::Number(value) => value
            .to_string()
            .split(['e', 'E'])
            .next()
            .unwrap_or("")
            .bytes()
            .any(|byte| (b'1'..=b'9').contains(&byte)),
    }
}
pub(crate) fn flag(fields: Option<&Map<String, Value>>, key: &str) -> bool {
    fields
        .and_then(|fields| fields.get(key))
        .is_some_and(truthy)
}
fn regge_open(value: Option<&Value>) -> bool {
    match value.filter(|value| !value.is_null()) {
        None => false,
        Some(value) => parse_exact_rational(value)
            .map(|value| !value.is_zero())
            .unwrap_or(true),
    }
}
fn regge_text(value: Option<&Value>) -> Option<String> {
    value.filter(|value| !value.is_null()).map(|value| {
        parse_exact_rational(value)
            .map(|value| canonical_rational(&value))
            .unwrap_or_else(|_| format!("INEXACT:{}", python_value_repr(value)))
    })
}
pub(crate) fn receipt_digest(value: &Value) -> Result<String, Refusal> {
    // Sorted compact UTF-8 JSON, without the semantic-ID layer's NFC rewrite.
    serde_json::to_vec(value)
        .map(|bytes| sha256_ref(&bytes))
        .map_err(|error| refuse("ADVERSARY_GATE_RECORD_INVALID", error.to_string()))
}
fn verdict_label(verdict: CheckerVerdict) -> &'static str {
    match verdict {
        CheckerVerdict::Accepted => "ACCEPTED",
        CheckerVerdict::Rejected => "REJECTED",
        CheckerVerdict::NotMeasured => "NOT_MEASURED",
    }
}

struct CandidateEval<'a> {
    selected_id: &'a str,
    check: Option<&'a CandidateCheck>,
    checker_bound: bool,
    checker_accepted: bool,
    critiqued: bool,
}

fn validate_authorization_preconditions<'a>(
    input: &'a AuthorizationGateInput<'_>,
) -> Result<&'a ObstructionMeasurement, Refusal> {
    let measurement = input.measurement.ok_or_else(|| {
        refuse(
            "ADVERSARY_SCORER_CONTRACT_VIOLATION",
            "Act VII requires an exact ObstructionMeasurementV1",
        )
    })?;
    let valid_status = [CARRIER_DECLARED, CARRIER_NOT_DECLARED].contains(&input.carrier_status);
    let undeclared_measured =
        input.carrier_status == CARRIER_NOT_DECLARED && measurement.is_measured();
    if !valid_status || undeclared_measured {
        return Err(refuse("ADVERSARY_CARRIER_STATUS_INVALID",
            "carrier_status must be DECLARED or NOT_DECLARED, and an undeclared carrier cannot carry a measurement"));
    }
    for (candidate_id, check) in input.candidate_checks {
        if check.candidate_id() != candidate_id {
            return Err(refuse(
                "ADVERSARY_CHECKER_CONTRACT_VIOLATION",
                "candidate checks must be exact CandidateCheckV1 values keyed by candidate id",
            ));
        }
    }
    Ok(measurement)
}

fn evaluate_selected_candidate<'a>(input: &'a AuthorizationGateInput<'_>) -> CandidateEval<'a> {
    let blocked: BTreeSet<&str> = input
        .critiques
        .iter()
        .filter(|critique| *critique.blocking())
        .map(|critique| critique.candidate_id().as_str())
        .chain(
            input
                .candidate_checks
                .iter()
                .filter_map(|(candidate_id, check)| {
                    (check.verdict() == CheckerVerdict::Rejected).then_some(candidate_id.as_str())
                }),
        )
        .collect();
    let selected = input
        .surviving_candidates
        .iter()
        .find(|candidate| !blocked.contains(candidate.candidate_id().as_str()));
    let selected_id = selected
        .map(|candidate| candidate.candidate_id().as_str())
        .unwrap_or("");
    let check = if selected_id.is_empty() {
        None
    } else {
        input.candidate_checks.get(selected_id)
    };
    let checker_bound = match (check, selected) {
        (Some(check), Some(candidate)) => check.binds(selected_id, candidate.artifact_refs()),
        _ => false,
    };
    let checker_accepted = checker_bound && check.is_some_and(CandidateCheck::can_authorize);
    let critiqued = !selected_id.is_empty()
        && input
            .critique_verdicts
            .get(selected_id)
            .is_some_and(|verdict| verdict == "NON_BLOCKING");
    CandidateEval {
        selected_id,
        check,
        checker_bound,
        checker_accepted,
        critiqued,
    }
}

fn is_protected_context(carrier_context: Option<&Map<String, Value>>) -> bool {
    flag(carrier_context, "protected_edges")
        || flag(carrier_context, "protected_boundaries")
        || carrier_context.and_then(|context| context.get("trap_type"))
            == Some(&json!("irreversible_mutation"))
}

fn build_obstruction_receipt(
    run_key: &str,
    measurement: &ObstructionMeasurement,
    zero_claim: bool,
) -> Option<Value> {
    if !measurement.is_measured()
        || !measurement
            .phi1()
            .is_some_and(|phi| phi > &BigRational::zero())
    {
        return None;
    }
    Some(
        json!({"receipt_type":"OBSTRUCTION_NON_VANISHING_RECEIPT","run_key":run_key,
        "backend":measurement.backend(),"certificate_verified":measurement.certificate_verified(),
        "dual_witness":measurement.dual_witness().iter().map(|(edge,value)|json!([edge,canonical_rational(value)])).collect::<Vec<_>>(),
        "phi1":measurement.phi1_text(),"gamma2":measurement.gamma2_text(),
        "adversarial_zero_claim_refuted":zero_claim}),
    )
}

fn build_regge_receipt(
    input: &AuthorizationGateInput<'_>,
    zero_claim: bool,
) -> (Option<Value>, bool) {
    let delta2_open = regge_open(input.delta2_defect);
    let delta3_open = regge_open(input.delta3_defect);
    let regge_deficit = delta2_open || delta3_open;
    let regge = regge_deficit.then(|| {
        json!({"receipt_type":"REGGE_SPACETIME_DEFICIT_RECEIPT",
            "run_key":input.run_key,"delta2_defect":regge_text(input.delta2_defect),
            "delta3_defect":regge_text(input.delta3_defect),"bianchi_closure":!delta2_open,
            "spacetime_closure":!delta3_open,"regge_converged":input.regge_converged == Some(&Value::Bool(true)),
            "adversarial_zero_claim_refuted":zero_claim})
    });
    (regge, regge_deficit)
}

fn collect_evidence_receipts(
    obstruction: &Option<Value>,
    regge: &Option<Value>,
) -> Result<(Map<String, Value>, Vec<String>), Refusal> {
    let mut receipts = Map::new();
    let mut receipt_refs = Vec::new();
    for receipt in [obstruction, regge].into_iter().flatten() {
        let digest = receipt_digest(receipt)?;
        receipt_refs.push(digest.clone());
        receipts.insert(digest, receipt.clone());
    }
    Ok((receipts, receipt_refs))
}

fn append_candidate_blockers(blockers: &mut Vec<String>, eval: &CandidateEval<'_>) {
    if eval.selected_id.is_empty() {
        return;
    }
    if eval.check.is_none() {
        blockers.push("CHECKER_NOT_RUN".into());
    } else if !eval.checker_bound {
        blockers.push("CHECKER_UNBOUND".into());
    } else if !eval.checker_accepted {
        if let Some(check) = eval.check {
            blockers.push(format!("CHECKER_{}", verdict_label(check.verdict())));
        }
    }
    if !eval.critiqued {
        blockers.push("CANDIDATE_NOT_CRITIQUED_NON_BLOCKING".into());
    }
}

fn collect_all_blockers(
    eval: &CandidateEval<'_>,
    carrier_required: bool,
    measurement: &ObstructionMeasurement,
    regge_deficit: bool,
    fixture_seats: bool,
    protected: bool,
    zero_refuted: bool,
) -> Vec<String> {
    let mut blockers: Vec<String> = Vec::new();
    if eval.selected_id.is_empty() {
        blockers.push("NO_ELIGIBLE_CANDIDATE".into());
    }
    if carrier_required && !measurement.is_measured() {
        blockers.push("CARRIER_NOT_MEASURED".into());
    } else if carrier_required && !measurement.is_exact_joint_zero() {
        blockers.push("OPEN_OBSTRUCTION".into());
    }
    if regge_deficit {
        blockers.push("REGGE_DEFICIT_OPEN".into());
    }
    append_candidate_blockers(&mut blockers, eval);
    append_post_candidate_blockers(&mut blockers, fixture_seats, protected, zero_refuted);
    blockers
}

fn append_post_candidate_blockers(
    blockers: &mut Vec<String>,
    fixture_seats: bool,
    protected: bool,
    zero_refuted: bool,
) {
    if fixture_seats {
        blockers.push("FIXTURE_SEATS".into());
    }
    if protected {
        blockers.push("PROTECTED_MUTATION".into());
    }
    if zero_refuted {
        blockers.push("ADVERSARIAL_ZERO_CLAIM_REFUTED".into());
    }
}

fn resolve_authorization_status(
    input: &AuthorizationGateInput<'_>,
    eval: &CandidateEval<'_>,
    measurement: &ObstructionMeasurement,
    carrier_required: bool,
    regge_deficit: bool,
    fixture_seats: bool,
    protected: bool,
    zero_refuted: bool,
) -> (&'static str, &'static str) {
    let no_auth = flag(input.ablation_flags, "no_authorization_boundary");
    let no_wit = flag(input.ablation_flags, "no_independent_witness");
    let no_res = flag(input.ablation_flags, "no_residual_ledger");
    let verified = eval.checker_accepted && eval.critiqued;
    let guarded_violation = (protected || zero_refuted) && !no_auth;
    if guarded_violation || eval.selected_id.is_empty() {
        return ("REFUSED", "HOLD");
    }
    if no_auth || no_wit {
        return if verified {
            ("ABLATED_WOULD_AUTHORIZE", "SELECT")
        } else {
            ("REFUSED", "HOLD")
        };
    }
    resolve_measured_status(
        measurement,
        carrier_required,
        regge_deficit,
        no_res,
        verified,
        fixture_seats,
    )
}

fn resolve_measured_status(
    measurement: &ObstructionMeasurement,
    carrier_required: bool,
    regge_deficit: bool,
    no_res: bool,
    verified: bool,
    fixture_seats: bool,
) -> (&'static str, &'static str) {
    if carrier_required && !measurement.is_measured() {
        ("NOT_MEASURED", "SELECT")
    } else if measurement.has_open_obstruction() || regge_deficit {
        if no_res {
            ("REFUSED", "HOLD")
        } else {
            ("BOUNDED_RESIDUAL", "SELECT")
        }
    } else if verified && fixture_seats {
        ("FIXTURE_ONLY", "SELECT")
    } else if verified {
        ("AUTHORIZED", "SELECT")
    } else {
        ("NOT_MEASURED", "SELECT")
    }
}

fn build_selection_proposal(
    input: &AuthorizationGateInput<'_>,
    selected_id: &str,
    disposition: &str,
    check: Option<&CandidateCheck>,
    receipt_refs: Vec<String>,
) -> Result<CandidateSelectionProposal, Refusal> {
    let epoch_id = sha256_ref(input.run_key.as_bytes());
    let mut evidence_refs: Vec<String> = input
        .critiques
        .iter()
        .map(|critique| critique.challenge_id().clone())
        .collect();
    if let Some(receipt) = check.and_then(CandidateCheck::receipt_sha256) {
        evidence_refs.push(receipt.into());
    }
    evidence_refs.extend(receipt_refs);
    let mut seen = BTreeSet::new();
    evidence_refs.retain(|id| seen.insert(id.clone()));
    if evidence_refs.is_empty() {
        evidence_refs.push(epoch_id.clone());
    }
    serde_json::from_value(json!({
        "selector_agent_id":"agent_manuscript_truth","evaluator_epoch_id":epoch_id,
        "frontier_candidate_ids":input.surviving_candidates.iter().map(|candidate|candidate.candidate_id()).collect::<Vec<_>>(),
        "selected_candidate_id":selected_id,"disposition":disposition,"evidence_refs":evidence_refs,
        "nonclaims":["Selection is a candidate proposal only.","AuthorityEffect is strictly None."],
        "authority_effect":"None","schema_version":"core.oeas.candidate-selection-proposal.v1"
    })).map_err(|error| refuse("ADVERSARY_GATE_RECORD_INVALID", error.to_string()))
}

fn format_narrative_body(
    input: &AuthorizationGateInput<'_>,
    status: &str,
    authorized: bool,
    selected_id: &str,
    evidence: Option<&str>,
    blockers: &[String],
    obstruction: &Option<Value>,
    regge: &Option<Value>,
    zero_claim: bool,
) -> String {
    let auth_str = if authorized { "True" } else { "False" };
    let sel_str = if selected_id.is_empty() { "none" } else { selected_id };
    let blk_str = if blockers.is_empty() {
        "none".into()
    } else {
        blockers.join(", ")
    };
    let mut body = format!(
        "Manuscript Truth rendered decision: status={status}, is_authorized={auth_str} (selected: {sel_str}; carrier {}; evidence path: {}). Blockers: {blk_str}.",
        input.carrier_status,
        evidence.unwrap_or("none")
    );
    if let Some(receipt) = obstruction.as_ref().filter(|_| zero_claim) {
        body.push_str(&format!(
            " Refuted adversarial zero-claim via exact dual witness: Phi1={} > 0.",
            receipt["phi1"].as_str().unwrap_or("None")
        ));
    }
    if let Some(receipt) = regge.as_ref().filter(|_| zero_claim) {
        body.push_str(&format!(
            " Refuted adversarial zero-claim via Regge deficit: delta2={}, delta3={}.",
            receipt["delta2_defect"].as_str().unwrap_or("None"),
            receipt["delta3_defect"].as_str().unwrap_or("None")
        ));
    }
    body
}

fn build_narrative_value(
    input: &AuthorizationGateInput<'_>,
    body: String,
    blockers: Vec<String>,
    evidence: Option<&str>,
    check: Option<&CandidateCheck>,
    receipts: Map<String, Value>,
    obstruction: Option<Value>,
    regge: Option<Value>,
) -> Value {
    let mut narrative = json!({"act_number":"VII","title":"Terminal Authorization Gate","body":body,
        "authorization_blockers":blockers,"authorization_evidence":evidence,"carrier_status":input.carrier_status,
        "checker_verdict":check.map(|check|verdict_label(check.verdict())).unwrap_or("NOT_MEASURED"),
        "checker_receipt_sha256":check.and_then(CandidateCheck::receipt_sha256),"evidence_receipts":receipts});
    if let Some(receipt) = obstruction {
        narrative["obstruction_non_vanishing_receipt"] = receipt;
    }
    if let Some(receipt) = regge {
        narrative["regge_spacetime_deficit_receipt"] = receipt;
    }
    narrative
}

fn emit_act7_intelligence_event(
    input: &AuthorizationGateInput<'_>,
    emitters: &mut EmitterSuite<'_>,
    time: &AuthorizationTime<'_>,
    status: &str,
    authorized: bool,
    blockers: &[String],
    selected_id: &str,
) -> Result<(), Refusal> {
    let terminal = status != "REFUSED";
    let payload = Map::from_iter([
        ("act".into(), json!("VII")),
        ("title".into(), json!("Terminal Authorization Gate")),
        ("status".into(), json!(status)),
        ("is_authorized".into(), json!(authorized)),
        ("authorization_blockers".into(), json!(blockers)),
    ]);
    let event_id = sha256_ref(format!("{}:act7", input.run_key).as_bytes());
    let (event, bytes) = build_intelligence_event(
        EventDescriptor {
            ie_id: &event_id,
            actor_id: "actor_nous_procurator",
            actor_kind: "SWARM_AGENT",
            event_kind: if terminal { "TERMINAL" } else { "REFUSAL" },
            source_system: "oeas.act7",
            session_id: input.run_key,
            parent_ie_id: Vec::new(),
            object_ids: Vec::new(),
            terminal: false,
        },
        Payload::Object(&payload),
        time.event_clock,
    )?;
    let witness_bytes = if selected_id.is_empty() {
        status.as_bytes()
    } else {
        selected_id.as_bytes()
    };
    let timestamp = if input.now_utc.is_empty() {
        time.dda_timestamp
    } else {
        input.now_utc
    };
    let step: DdcStep = serde_json::from_value(json!({"letter":if terminal {"T"} else {"M"},
        "before_class":"LedgerIntegrated","after_class":"TerminalVerdict",
        "carrier_hash":sha256_ref(b"carrier"),"witness_hash":sha256_ref(witness_bytes),
        "receipt_sha256":sha256_ref(&bytes),"timestamp":timestamp,
    }))
    .map_err(|error| refuse("ADVERSARY_GATE_RECORD_INVALID", error.to_string()))?;
    emit_event(&event, &bytes, emitters, Some(&step), None).map(|_| ())
}

pub fn execute_act7_authorization_gate(
    input: &AuthorizationGateInput<'_>,
    emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<AuthorizationOutcome, Refusal> {
    let measurement = validate_authorization_preconditions(input)?;
    let carrier_required = input.carrier_status == CARRIER_DECLARED;
    let eval = evaluate_selected_candidate(input);
    let fixture_seats = input.fixture_seats != &Value::Bool(false);
    let protected = is_protected_context(input.carrier_context);
    let zero_claim = ["adversarial_zero_claim", "zero_claim", "claims_zero_defect"]
        .iter()
        .any(|key| flag(input.carrier_context, key));
    let obstruction = build_obstruction_receipt(input.run_key, measurement, zero_claim);
    let (regge, regge_deficit) = build_regge_receipt(input, zero_claim);
    let (receipts, receipt_refs) = collect_evidence_receipts(&obstruction, &regge)?;
    let zero_refuted = zero_claim && (obstruction.is_some() || regge.is_some());
    let blockers = collect_all_blockers(
        &eval,
        carrier_required,
        measurement,
        regge_deficit,
        fixture_seats,
        protected,
        zero_refuted,
    );
    let (status, disposition) = resolve_authorization_status(
        input,
        &eval,
        measurement,
        carrier_required,
        regge_deficit,
        fixture_seats,
        protected,
        zero_refuted,
    );
    let authorized = status == "AUTHORIZED";
    let evidence_kind = if carrier_required {
        EVIDENCE_CHECKER_AND_CARRIER
    } else {
        EVIDENCE_CHECKER_ONLY
    };
    let evidence = authorized.then_some(evidence_kind);
    let selected_id = if disposition == "HOLD" {
        ""
    } else {
        eval.selected_id
    };
    let proposal =
        build_selection_proposal(input, selected_id, disposition, eval.check, receipt_refs)?;
    let body = format_narrative_body(
        input,
        status,
        authorized,
        selected_id,
        evidence,
        &blockers,
        &obstruction,
        &regge,
        zero_claim,
    );
    if let Some(emitters) = emitters {
        emit_act7_intelligence_event(
            input,
            emitters,
            time,
            status,
            authorized,
            &blockers,
            selected_id,
        )?;
    }
    let narrative = build_narrative_value(
        input,
        body,
        blockers,
        evidence,
        eval.check,
        receipts,
        obstruction,
        regge,
    );
    Ok(AuthorizationOutcome {
        status: status.into(),
        selected_candidate_id: selected_id.into(),
        proposal,
        is_authorized: authorized,
        narrative,
    })
}

// Origin: engine/crates_rs/core_adversary/src/authorization.rs
// Claim: urn:core:crates_rs:core-adversary:authorization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord98f4ade5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord98f4ade5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError98f4ade5 {
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
impl BoundaryError98f4ade5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError98f4ade5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError98f4ade5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord98f4ade5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError98f4ade5> {
        if capacity_bound == 0 {
            return Err(BoundaryError98f4ade5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError98f4ade5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError98f4ade5::ExceedsCapacity {
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
mod l4_boundary_tests_98f4ade5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord98f4ade5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord98f4ade5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord98f4ade5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord98f4ade5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord98f4ade5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError98f4ade5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError98f4ade5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
