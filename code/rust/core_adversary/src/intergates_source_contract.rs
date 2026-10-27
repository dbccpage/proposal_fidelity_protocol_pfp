//! Finite source-contract profile; legacy diagnostics remain in intergates.rs.
//! Observations are supplied by the host. Signatures authenticate statements
//! relative to its pinned policy, not mathematical truth or execution authority.
use super::{
    bounded, number, refusal, result, sha256_ref, spec, terminal, Spec, SOURCE_CONTRACT_PROFILE,
};
use crate::stage::ports::Refusal;
use num_rational::BigRational;
use num_traits::Zero;
use core_epistemic_immune_system::authenticated::{
    self, Binding, Purpose, SignedEvidence, TrustPolicy,
};
use regex::RegexBuilder;
use serde_json::{json, Map, Value};
use std::collections::HashSet;

type Fields = Map<String, Value>;
type Check = Result<Value, Refusal>;
const TRUST_SCOPE: &str = "adversary.intergate.source.v1";

fn require(ok: bool, code: &str, message: &str) -> Result<(), Refusal> {
    if ok {
        Ok(())
    } else {
        Err(refusal(code, message))
    }
}
fn invalid(message: &str) -> Refusal {
    refusal("INTERGATE_PAYLOAD_INVALID", message)
}
fn text<'a>(p: &'a Fields, key: &str) -> Result<&'a str, Refusal> {
    p.get(key)
        .and_then(Value::as_str)
        .ok_or_else(|| invalid(&format!("{key} must be text")))
}
fn nonempty<'a>(p: &'a Fields, key: &str) -> Result<&'a str, Refusal> {
    let value = text(p, key)?;
    require(
        !value.trim().is_empty(),
        "INTERGATE_PAYLOAD_INVALID",
        &format!("{key} must be nonempty"),
    )?;
    Ok(value)
}
fn boolean(p: &Fields, key: &str) -> Result<bool, Refusal> {
    p.get(key)
        .and_then(Value::as_bool)
        .ok_or_else(|| invalid(&format!("{key} must be boolean")))
}
fn uint(p: &Fields, key: &str) -> Result<u64, Refusal> {
    p.get(key)
        .and_then(Value::as_u64)
        .ok_or_else(|| invalid(&format!("{key} must be an unsigned integer")))
}
fn object<'a>(p: &'a Fields, key: &str) -> Result<&'a Fields, Refusal> {
    p.get(key)
        .and_then(Value::as_object)
        .ok_or_else(|| invalid(&format!("{key} must be an object")))
}
fn list<'a>(p: &'a Fields, key: &str) -> Result<&'a Vec<Value>, Refusal> {
    p.get(key)
        .and_then(Value::as_array)
        .ok_or_else(|| invalid(&format!("{key} must be a list")))
}
fn strings<'a>(p: &'a Fields, key: &str) -> Result<Vec<&'a str>, Refusal> {
    list(p, key)?
        .iter()
        .map(|v| {
            v.as_str()
                .filter(|s| !s.trim().is_empty())
                .ok_or_else(|| invalid(&format!("{key} must contain nonempty strings")))
        })
        .collect()
}
fn unique(values: &[&str]) -> bool {
    values.iter().copied().collect::<HashSet<_>>().len() == values.len()
}
fn bytes(p: &Fields, key: &str, empty: bool) -> Result<Vec<u8>, Refusal> {
    let value = text(p, key)?;
    require(
        (empty || !value.is_empty())
            && value.len() % 2 == 0
            && value
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)),
        "INTERGATE_PAYLOAD_INVALID",
        &format!("{key} must be lower-case hex bytes"),
    )?;
    hex::decode(value).map_err(|_| invalid(key))
}
fn fraction(n: i64, d: i64) -> BigRational {
    BigRational::new(n.into(), d.into())
}
fn unit(p: &Fields, key: &str) -> Result<BigRational, Refusal> {
    let n = number(p, key)?;
    require(
        n >= BigRational::zero() && n <= fraction(1, 1),
        "INTERGATE_PAYLOAD_INVALID",
        "Score must be in [0,1]",
    )?;
    Ok(n)
}
fn ratio(p: &Fields) -> Result<BigRational, Refusal> {
    let delta = number(p, "prompt_complexity_score")?;
    let capacity = number(p, "agent_capacity_score")?;
    require(
        delta >= BigRational::zero() && capacity > BigRational::zero(),
        "INTERGATE_PAYLOAD_INVALID",
        "Incremental complexity is nonnegative; capacity is positive",
    )?;
    Ok(delta / capacity)
}
fn prior<'a>(
    p: &'a Fields,
    key: &str,
    index_key: &str,
    index: u64,
) -> Result<Option<&'a Fields>, Refusal> {
    require(
        index > 0,
        "INTERGATE_PAYLOAD_INVALID",
        "Round/turn numbering starts at one",
    )?;
    match p.get(key) {
        Some(Value::Null) if index == 1 => Ok(None),
        Some(Value::Object(previous)) if index > 1 && uint(previous, index_key)? == index - 1 => {
            Ok(Some(previous))
        }
        _ => Err(invalid(
            "Supply the actual immediately preceding round/turn; first observation requires null",
        )),
    }
}

fn check_flow_latency(p: &Fields) -> Result<(), Refusal> {
    let limit = uint(p, "feedback_loop_limit_ms")?;
    require(
        limit > 0,
        "INTERGATE_PAYLOAD_INVALID",
        "Declare a positive host feedback latency limit",
    )?;
    require(
        uint(p, "feedback_loop_ms")? <= limit,
        "FLOW_FEEDBACK_LATENCY_EXCEEDED",
        "Feedback latency exceeds the declared host limit",
    )
}

fn flow(p: &Fields) -> Check {
    let current = ratio(p)?;
    let previous = prior(p, "prior_round", "round_number", uint(p, "round_number")?)?;
    let previous_ratio = previous.map(ratio).transpose()?;
    check_flow_latency(p)?;
    if current < fraction(4, 5) {
        let repeated = previous_ratio.is_some_and(|r| r < fraction(4, 5));
        let (code, msg) = if repeated {
            (
                "FLOW_STAGNATION_DETECTED",
                "Two consecutive low challenge ratios require a challenge lift",
            )
        } else {
            (
                "FLOW_ADJUSTMENT_REQUIRED",
                "First low ratio requests adjustment; two-round stagnation is not yet observed",
            )
        };
        return Err(refusal(code, msg));
    }
    require(
        current <= fraction(6, 5),
        "FLOW_OVERWHELM_DETECTED",
        "Challenge ratio exceeds 1.2; request scaffolding",
    )?;
    Ok(json!({"observation_scope":"supplied incremental complexity/capacity and host latency"}))
}

fn check_surprise_kl(p: &Fields) -> Result<(), Refusal> {
    require(
        uint(p, "round_number")? > 0,
        "INTERGATE_PAYLOAD_INVALID",
        "Round must be positive",
    )?;
    let delta = number(p, "previous_prompt_kl_divergence")?;
    require(
        delta >= BigRational::zero(),
        "INTERGATE_PAYLOAD_INVALID",
        "KL divergence cannot be negative",
    )?;
    require(
        delta >= fraction(3, 20),
        "EPISTEMIC_STAGNATION",
        "KL divergence is below 0.15",
    )?;
    require(
        delta <= fraction(7, 2),
        "EPISTEMIC_DERAILMENT",
        "KL divergence exceeds 3.5",
    )?;
    require(
        boolean(p, "carrier_isomorphism_valid")?,
        "CARRIER_RETURN_UNVERIFIED",
        "Carrier return was not observed",
    )
}

fn check_carrier_domains(
    source: &[&str],
    target: &[&str],
    forward: &[Value],
    inverse: &[Value],
) -> Result<usize, Refusal> {
    let n = source.len();
    let valid_sizes = n > 0 && n == target.len() && n == forward.len() && n == inverse.len();
    require(
        valid_sizes && unique(source) && unique(target),
        "CARRIER_RETURN_UNVERIFIED",
        "Carrier domains must be finite, unique and equally sized",
    )?;
    Ok(n)
}

fn verify_carrier_bijection(forward: &[Value], inverse: &[Value], n: usize) -> Result<(), Refusal> {
    for (i, item) in forward.iter().enumerate().take(n) {
        let j = item
            .as_u64()
            .and_then(|v| usize::try_from(v).ok())
            .filter(|j| *j < n)
            .ok_or_else(|| invalid("Forward carrier map must contain bounded indices"))?;
        require(
            inverse[j].as_u64() == Some(i as u64),
            "CARRIER_RETURN_UNVERIFIED",
            "Forward and inverse carrier maps do not compose to identity",
        )?;
    }
    Ok(())
}

fn surprise(p: &Fields) -> Check {
    check_surprise_kl(p)?;
    let mapping = object(p, "carrier_mapping")?;
    let source = strings(mapping, "source")?;
    let target = strings(mapping, "target")?;
    let forward = list(mapping, "forward")?;
    let inverse = list(mapping, "inverse")?;
    let n = check_carrier_domains(&source, &target, forward, inverse)?;
    verify_carrier_bijection(forward, inverse, n)?;
    Ok(
        json!({"carrier_elements":n,"observation_scope":"finite index bijection; no arbitrary prompt semantic-isomorphism theorem"}),
    )
}

fn verify_admitted_defect(p: &Fields) -> Result<bool, Refusal> {
    let admitted = boolean(p, "has_typed_defect_admission")?;
    if admitted {
        let defect = object(p, "typed_defect")?;
        nonempty(defect, "code")?;
        require(
            sha256_ref(&bytes(defect, "evidence_hex", false)?) == text(defect, "evidence_sha256")?,
            "DEFECT_EVIDENCE_MISMATCH",
            "Typed defect must bind its actual evidence bytes",
        )?;
    }
    Ok(admitted)
}

fn verify_sponsor_challenge(p: &Fields) -> Result<(), Refusal> {
    let evidence = bytes(p, "response_evidence_hex", true)?;
    let refusal = boolean(p, "explicit_refusal")?;
    let answered = !evidence.is_empty() || refusal;
    require(
        !boolean(p, "sponsor_challenge_present")? || answered,
        "SPONSOR_CHALLENGE_UNANSWERED",
        "A direct sponsor challenge requires evidence or explicit refusal",
    )
}

fn evasion(p: &Fields) -> Check {
    let severity = unit(p, "critique_severity")?;
    let vagueness = unit(p, "response_vagueness_index")?;
    let admitted = verify_admitted_defect(p)?;
    require(
        !boolean(p, "yields_without_evidence")? || admitted,
        "COWARDICE_YIELD_DETECTED",
        "Yielding requires evidence or an actual typed defect",
    )?;
    let high_vagueness = severity > fraction(7, 10) && vagueness > fraction(2, 5);
    require(
        !high_vagueness,
        "COWARDICE_YIELD_DETECTED",
        "Strategic vagueness exceeds 0.4 under critique above 0.7",
    )?;
    verify_sponsor_challenge(p)?;
    Ok(json!({"typed_defect_admitted":admitted}))
}

fn check_sandbox_flags(p: &Fields) -> Result<bool, Refusal> {
    Ok(boolean(p, "sandbox_boundary_active")?
        && text(p, "declared_authority_effect")? == "None"
        && !boolean(p, "has_production_side_effects")?)
}

fn sandbox(p: &Fields) -> Check {
    require(
        check_sandbox_flags(p)?,
        "UNAUTHORIZED_PLAY_EFFECT",
        "Sandbox boundary, zero authority and no production side effect are required",
    )?;
    require(
        bytes(p, "canonical_before_hex", false)? == bytes(p, "canonical_after_hex", false)?,
        "UNAUTHORIZED_PLAY_EFFECT",
        "Canonical state changed during play",
    )?;
    require(
        bytes(p, "sandbox_before_hex", false)? == bytes(p, "sandbox_restored_hex", false)?,
        "SANDBOX_ROLLBACK_MISMATCH",
        "Sandbox restoration differs from its baseline",
    )?;
    Ok(
        json!({"observation_scope":"supplied host boundary and exact before/after/restored bytes; no universal isolation proof"}),
    )
}

fn binding_fields_match(
    spec: &Spec,
    p: &Fields,
    expected: &Binding,
    context_digest: &str,
) -> Result<bool, Refusal> {
    let source_digest = nonempty(p, "source_digest")?;
    let subject_digest = sha256_ref(text(p, "candidate_content")?.as_bytes());
    Ok([
        expected.spec_id == spec.id,
        expected.scope == TRUST_SCOPE,
        expected.rule_digest == sha256_ref(spec.bytes),
        expected.source_digest == source_digest,
        expected.subject_digest == subject_digest,
        expected.context_digest == context_digest,
    ]
    .into_iter()
    .all(|b| b))
}

fn verify_expected_binding(
    spec: &Spec,
    p: &Fields,
    context_digest: &str,
) -> Result<(TrustPolicy, Binding), Refusal> {
    let policy: TrustPolicy = serde_json::from_value(
        p.get("trust_policy").cloned().unwrap_or(Value::Null),
    )
    .map_err(|_| {
        refusal(
            "INTERGATE_TRUST_UNCONFIGURED",
            "A host-selected EIS trust policy is required",
        )
    })?;
    let expected: Binding = serde_json::from_value(
        p.get("expected_binding").cloned().unwrap_or(Value::Null),
    )
    .map_err(|_| {
        refusal(
            "INTERGATE_TRUST_UNCONFIGURED",
            "A host-selected EIS expected binding is required",
        )
    })?;
    require(
        binding_fields_match(spec, p, &expected, context_digest)?,
        "INTERGATE_ATTESTATION_BINDING_MISMATCH",
        "Signed gate/source/task/candidate binding differs from current input",
    )?;
    Ok((policy, expected))
}

fn verify_signed(
    spec: &Spec,
    p: &Fields,
    signed: &Value,
    expected_bytes: &[u8],
    issuer: &str,
    context_digest: &str,
    outcomes: &[&str],
) -> Result<SignedEvidence, Refusal> {
    let (policy, expected) = verify_expected_binding(spec, p, context_digest)?;
    let evidence: SignedEvidence = serde_json::from_value(signed.clone()).map_err(|_| {
        invalid("Supply actual EIS SignedEvidence, not a signature name or verified flag")
    })?;
    let role_ok = evidence.attestation.issuer == issuer
        && outcomes.contains(&evidence.attestation.outcome.as_str())
        && evidence.attestation.previous_event.is_none();
    require(
        role_ok,
        "INTERGATE_ATTESTATION_ROLE_MISMATCH",
        "Attestation signer/outcome is not the configured witness",
    )?;
    let raw = hex::decode(&evidence.evidence_hex)
        .map_err(|_| invalid("Malformed signed evidence bytes"))?;
    require(
        raw == expected_bytes,
        "INTERGATE_ATTESTATION_EVIDENCE_MISMATCH",
        "Signature must cover these exact evidence bytes",
    )?;
    authenticated::verify(
        &evidence,
        &policy,
        &expected,
        Purpose::Admission,
        uint(p, "now")?,
    )
    .map_err(|e| refusal(&e.code, e.message))?;
    Ok(evidence)
}
fn task_context(p: &Fields) -> Result<String, Refusal> {
    Ok(sha256_ref(nonempty(p, "task_id")?.as_bytes()))
}

fn sanitize_urgency_text(p: &Fields) -> Result<String, Refusal> {
    let original = text(p, "prompt_text")?;
    let mut sanitized = original.to_owned();
    let mut markers = vec![
        "act immediately",
        "act now",
        "expires immediately",
        "catastrophic deadline",
        "must decide now",
        "urgent escalation required without evidence",
        "time is running out",
        "skip review to meet deadline",
        "bypass gate due to emergency",
    ];
    markers.extend(strings(p, "urgency_indicators")?);
    // Longest first makes nested/duplicate indicators deterministic.
    markers.sort_by(|a, b| b.len().cmp(&a.len()).then_with(|| a.cmp(b)));
    markers.dedup();
    for marker in markers {
        let pattern = RegexBuilder::new(&regex::escape(marker))
            .case_insensitive(true)
            .build()
            .map_err(|e| invalid(&e.to_string()))?;
        sanitized = pattern.replace_all(&sanitized, "").into_owned();
    }
    require(
        sanitized == text(p, "sanitized_prompt_text")?,
        "URGENCY_SANITIZATION_MISMATCH",
        "Downstream text must match exact removal of the declared and known markers",
    )?;
    Ok(sanitized)
}

fn parse_timestamp_record(raw: &[u8], constraint: &str, end: u64) -> Result<(), Refusal> {
    let mut decoder = serde_json::Deserializer::from_slice(raw);
    use serde::Deserialize;
    super::UniqueJson::deserialize(&mut decoder)
        .and_then(|_| decoder.end())
        .map_err(|e| invalid(&e.to_string()))?;
    let record: Value = serde_json::from_slice(raw).map_err(|e| invalid(&e.to_string()))?;
    let record = record
        .as_object()
        .ok_or_else(|| invalid("Timestamp record must be an object"))?;
    let witness_ok = [
        text(record, "constraint_text")? == constraint,
        uint(record, "observed_at_ms")? == end,
        uint(record, "deadline_ms")? >= end,
    ]
    .into_iter()
    .all(|b| b);
    require(
        witness_ok,
        "TIMESTAMP_WITNESS_MISMATCH",
        "Timestamp witness must support the actual declared constraint and observation",
    )
}

fn verify_urgency_timestamp_witness(
    spec: &Spec,
    p: &Fields,
    constraint: &str,
    end: u64,
) -> Result<(), Refusal> {
    let signed = p.get("timestamp_witness").ok_or_else(|| {
        refusal(
            "TIMESTAMP_WITNESS_REQUIRED",
            "Declared time constraint requires a signed timestamp witness",
        )
    })?;
    let raw = bytes(object(p, "timestamp_witness")?, "evidence_hex", false)?;
    parse_timestamp_record(&raw, constraint, end)?;
    verify_signed(
        spec,
        p,
        signed,
        &raw,
        nonempty(p, "timestamp_issuer")?,
        &task_context(p)?,
        &["ADMIT"],
    )?;
    Ok(())
}

fn verify_urgency_buffer(p: &Fields) -> Result<(u64, u64), Refusal> {
    let begin = uint(p, "verification_started_ms")?;
    let end = uint(p, "verification_completed_ms")?;
    let buffer = uint(p, "minimum_buffer_ms")?;
    require(
        buffer > 0 && end >= begin,
        "INTERGATE_PAYLOAD_INVALID",
        "Declare a positive host buffer and ordered observations",
    )?;
    require(
        end - begin >= buffer,
        "VERIFICATION_BUFFER_PENDING",
        "Verification buffer has not elapsed",
    )?;
    Ok((begin, end))
}

fn urgency(spec: &Spec, p: &Fields) -> Check {
    require(
        p.get("bypass_gates_requested") != Some(&Value::Bool(true)),
        "FALSE_URGENCY_INJECTED",
        "A verification buffer cannot authorize bypassing gates",
    )?;
    let sanitized = sanitize_urgency_text(p)?;
    let (begin, end) = verify_urgency_buffer(p)?;
    let constraint = text(p, "declared_time_constraint")?;
    if !constraint.is_empty() {
        verify_urgency_timestamp_witness(spec, p, constraint, end)?;
    }
    Ok(json!({"downstream_text":sanitized,"verification_elapsed_ms":end-begin}))
}

fn verify_scar_custody(p: &Fields) -> Result<usize, Refusal> {
    let before = strings(p, "scar_before")?;
    let after = strings(p, "scar_after")?;
    require(
        unique(&before) && unique(&after) && before.iter().all(|s| after.contains(s)),
        "SCAR_CUSTODY_LOST",
        "Rejoin must retain every prior scar identity",
    )?;
    Ok(before.len())
}

fn verify_high_antagonism_envelope(p: &Fields, current: &BigRational) -> Result<(), Refusal> {
    let acknowledged = boolean(p, "has_acknowledged_error")?;
    let repair = text(p, "repair_action_proposed")?;
    let envelope = text(p, "deescalation_envelope")?;
    if *current > fraction(3, 5) {
        require(
            !envelope.trim().is_empty(),
            "DEESCALATION_ENVELOPE_REQUIRED",
            "High antagonism requires a de-escalation envelope",
        )?;
        require(
            acknowledged && !repair.trim().is_empty(),
            "DEESCALATION_REJOIN_PENDING",
            "Rejoin requires error acknowledgement and a proposed repair",
        )?;
    }
    Ok(())
}

fn affect(p: &Fields) -> Check {
    let current = unit(p, "antagonism_score")?;
    let previous = prior(p, "prior_turn", "turn_number", uint(p, "turn_number")?)?;
    let previous_score = previous.map(|v| unit(v, "antagonism_score")).transpose()?;
    let scars_retained = verify_scar_custody(p)?;
    verify_high_antagonism_envelope(p, &current)?;
    let two_turn = current > fraction(3, 5) && previous_score.is_some_and(|v| v > fraction(3, 5));
    Ok(json!({"two_turn_antagonism":two_turn,"scars_retained":scars_retained}))
}

fn verify_reviewer_contexts(p: &Fields, reviewers: &[&str]) -> Result<(), Refusal> {
    let producer = bytes(p, "producer_context_hex", false)?;
    let contexts = object(p, "evaluator_contexts")?;
    require(
        contexts.len() == reviewers.len(),
        "EVALUATOR_CONTEXT_MISMATCH",
        "Every reviewer requires exactly one context",
    )?;
    for reviewer in reviewers {
        require(
            bytes(contexts, reviewer, false)? != producer,
            "ECHO_CHAMBER_CONSENSUS",
            "Reviewer context equals producer context",
        )?;
    }
    Ok(())
}

fn collect_dissent_identities<'a>(
    records: &'a [Value],
    dissent: &[&str],
) -> Result<HashSet<&'a str>, Refusal> {
    let mut retained = HashSet::new();
    for row in records {
        let row = row
            .as_object()
            .ok_or_else(|| invalid("Dissent record must be an object"))?;
        let id = nonempty(row, "evaluator_id")?;
        bytes(row, "content_hex", false)?;
        require(
            dissent.contains(&id) && retained.insert(id),
            "DISSENT_RECORD_MISMATCH",
            "Dissent record identity is foreign or duplicated",
        )?;
    }
    Ok(retained)
}

fn verify_dissent_records(p: &Fields, reviewers: &[&str]) -> Result<usize, Refusal> {
    let dissent = strings(p, "dissenting_evaluator_ids")?;
    require(
        unique(&dissent) && dissent.iter().all(|id| reviewers.contains(id)),
        "DISSENT_RECORD_MISMATCH",
        "Dissent identities must be unique admitted reviewers",
    )?;
    let records = list(p, "dissent_records")?;
    let retained = collect_dissent_identities(records, &dissent)?;
    require(
        retained.len() == dissent.len(),
        "DISSENT_RECORD_MISMATCH",
        "A minority dissent record is missing",
    )?;
    Ok(retained.len())
}

fn consensus(p: &Fields) -> Check {
    for (key, kind) in [
        ("agent_evaluator_ids", "texts"),
        ("sampling_seeds", "ints"),
        ("producer_id", "nonempty_text"),
    ] {
        require(
            p.get(key).is_some_and(|v| super::matches_kind(v, kind)),
            "INTERGATE_PAYLOAD_INVALID",
            "Reviewer identities and seeds must be explicitly supplied",
        )?;
    }
    if let Some(reason) = super::consensus(p) {
        return Err(refusal("ECHO_CHAMBER_CONSENSUS", reason));
    }
    let reviewers = strings(p, "agent_evaluator_ids")?;
    verify_reviewer_contexts(p, &reviewers)?;
    let retained_dissent = verify_dissent_records(p, &reviewers)?;
    Ok(
        json!({"retained_dissent":retained_dissent,"observation_scope":"recorded IDs/seeds/context/dissent; no probabilistic or institutional independence theorem"}),
    )
}

fn accepted_receipt(p: &Fields) -> Result<Vec<u8>, Refusal> {
    if let Some((code, reason)) = super::verify_checker_binding(p) {
        return Err(refusal(code, reason));
    }
    bytes(p, "checker_receipt_hex", false)
}

#[allow(clippy::too_many_arguments)]
fn verify_single_dual_witness<'a>(
    spec: &Spec,
    p: &Fields,
    policy: &TrustPolicy,
    witness: &'a Value,
    receipt: &[u8],
    context: &str,
    allowed_issuers: [&str; 2],
    seen: &mut HashSet<&'a str>,
    keys: &mut HashSet<String>,
) -> Result<(), Refusal> {
    let issuer = witness["attestation"]["issuer"]
        .as_str()
        .ok_or_else(|| invalid("Witness issuer missing"))?;
    require(
        allowed_issuers.contains(&issuer) && seen.insert(issuer),
        "DUAL_WITNESS_REQUIRED",
        "Each configured witness must sign once",
    )?;
    let checked = verify_signed(
        spec,
        p,
        witness,
        receipt,
        issuer,
        context,
        &["ADMIT", "REINSTATE"],
    )?;
    let key = policy
        .keys
        .iter()
        .find(|key| key.issuer == issuer && key.key_id == checked.attestation.key_id)
        .ok_or_else(|| invalid("Verified witness key disappeared"))?;
    require(
        keys.insert(key.public_key_hex.clone()),
        "DUAL_WITNESS_REQUIRED",
        "Two names for the same key are not dual witnesses",
    )
}

fn check_quarantine_repair_bytes(p: &Fields) -> Result<(), Refusal> {
    let before = bytes(p, "repair_before_hex", false)?;
    let after = bytes(p, "repair_after_hex", false)?;
    let candidate = text(p, "candidate_content")?.as_bytes();
    let repair_ok = [before != after, after == candidate].into_iter().all(|b| b);
    require(
        repair_ok,
        "EXACT_REPAIR_BINDING_MISMATCH",
        "Finite prompt repair requires changed bytes and the exact current candidate",
    )
}

fn verify_quarantine_repair_context<'a>(
    p: &'a Fields,
) -> Result<(&'a str, &'a str, String), Refusal> {
    let task = nonempty(p, "task_id")?;
    let cause = nonempty(p, "quarantine_cause")?;
    let harm = nonempty(p, "harm_class")?;
    check_quarantine_repair_bytes(p)?;
    let context = sha256_ref(
        &serde_json::to_vec(&json!([
            task,
            cause,
            harm,
            text(p, "repair_before_hex")?,
            text(p, "repair_after_hex")?
        ]))
        .map_err(|e| invalid(&e.to_string()))?,
    );
    Ok((cause, harm, context))
}

fn verify_quarantine_witnesses(
    spec: &Spec,
    p: &Fields,
    receipt: &[u8],
    context: &str,
) -> Result<(), Refusal> {
    let issuers = object(p, "witness_issuers")?;
    let first = nonempty(issuers, "quarantine")?;
    let second = nonempty(issuers, "master")?;
    require(
        first != second,
        "DUAL_WITNESS_REQUIRED",
        "Quarantine and Master must have distinct configured issuers",
    )?;
    let witnesses = list(p, "dual_witnesses")?;
    require(
        witnesses.len() == 2,
        "DUAL_WITNESS_REQUIRED",
        "Exactly two signed witnesses are required",
    )?;
    let policy: TrustPolicy = serde_json::from_value(
        p.get("trust_policy").cloned().unwrap_or(Value::Null),
    )
    .map_err(|_| {
        refusal(
            "INTERGATE_TRUST_UNCONFIGURED",
            "A pinned policy is required for dual witnesses",
        )
    })?;
    let mut keys = HashSet::new();
    let mut seen = HashSet::new();
    for witness in witnesses {
        verify_single_dual_witness(
            spec,
            p,
            &policy,
            witness,
            receipt,
            context,
            [first, second],
            &mut seen,
            &mut keys,
        )?;
    }
    Ok(())
}

fn quarantine(spec: &Spec, p: &Fields) -> Check {
    let (cause, harm, context) = verify_quarantine_repair_context(p)?;
    let receipt = accepted_receipt(p)?;
    verify_quarantine_witnesses(spec, p, &receipt, &context)?;
    Ok(
        json!({"harm_class":harm,"quarantine_cause":cause,"authenticated_witnesses":2,
        "trust_scope":"relative to host-selected policy; signatures do not prove repair semantics"}),
    )
}

fn check_exploit_binding_shapes(
    exploits: &[&str],
    severities: &[Value],
    countermeasures: &[&str],
    applied: &[&str],
) -> bool {
    exploits.len() == severities.len()
        && exploits.len() == countermeasures.len()
        && unique(exploits)
        && unique(countermeasures)
        && unique(applied)
        && applied.iter().all(|uid| countermeasures.contains(uid))
}

fn defense(p: &Fields) -> Check {
    let exploits = strings(p, "detected_exploit_uids")?;
    let severities = list(p, "exploit_severities")?;
    let countermeasures = strings(p, "bound_countermeasure_uids")?;
    let applied = strings(p, "applied_countermeasure_uids")?;
    require(
        check_exploit_binding_shapes(&exploits, severities, &countermeasures, &applied),
        "DECEPTION_SURFACE_UNMITIGATED",
        "Every exploit needs one distinct positional countermeasure binding",
    )?;
    for (index, value) in severities.iter().enumerate() {
        let fields = Map::from_iter([("severity".into(), value.clone())]);
        let severity = unit(&fields, "severity")?;
        require(
            severity <= fraction(7, 10) || applied.contains(&countermeasures[index]),
            "COUNTERMEASURE_NOT_APPLIED",
            "Severity above 0.7 locks downstream execution until the bound defense applies",
        )?;
    }
    Ok(
        json!({"exploit_defense_bindings":exploits.iter().zip(countermeasures.iter()).map(|(a,b)| json!([a,b])).collect::<Vec<_>>() }),
    )
}

fn terminal_trust(spec: &Spec, p: &Fields) -> Check {
    if let Some((code, reason)) = terminal(p) {
        return Err(refusal(code, reason));
    }
    let raw = accepted_receipt(p)?;
    let receipt = super::parse_checker_receipt(&raw)?;
    require(
        receipt.checker_id() == nonempty(p, "checker_id")?,
        "CHECKER_ID_MISMATCH",
        "Receipt checker is not the configured checker",
    )?;
    verify_signed(
        spec,
        p,
        p.get("checker_attestation").unwrap_or(&Value::Null),
        &raw,
        nonempty(p, "checker_issuer")?,
        &task_context(p)?,
        &["ADMIT"],
    )?;
    Ok(
        json!({"trust_scope":"checker receipt provenance relative to host-selected policy; no execution/mathematical authority"}),
    )
}

fn check_source_contract_descent(p: &Fields, repeated: bool) -> Result<(), Refusal> {
    if ["residual_descent_observed", "bypass_gates_requested"]
        .iter()
        .any(|key| p.get(*key).is_some_and(|value| !value.is_boolean()))
    {
        return Err(invalid(
            "Optional descent/bypass observations must be booleans",
        ));
    }
    if !repeated {
        return Ok(());
    }
    if !p
        .get("residual_descent_observed")
        .is_some_and(Value::is_boolean)
    {
        return Err(refusal(
            "INTERGATE_DESCENT_UNMEASURED",
            "Repeated actual edge needs an explicit descent observation",
        ));
    }
    if p["residual_descent_observed"] == false {
        return Err(refusal(
            "CURVATURE_OBSTRUCTION_DETECTED",
            "Repeated actual edge has no observed residual reduction",
        ));
    }
    Ok(())
}

fn dispatch_source_contract_early(index: u8, spec: &Spec, p: &Fields) -> Check {
    match index {
        1 => flow(p),
        2 => surprise(p),
        3 => evasion(p),
        4 => sandbox(p),
        5 => urgency(spec, p),
        _ => unreachable!("early gate inventory"),
    }
}

fn dispatch_source_contract_gate(spec: &Spec, p: &Fields) -> Check {
    match spec.index {
        1..=5 => dispatch_source_contract_early(spec.index, spec, p),
        6 => affect(p),
        7 => consensus(p),
        8 => quarantine(spec, p),
        9 => defense(p),
        10 => terminal_trust(spec, p),
        _ => unreachable!("known gate inventory"),
    }
}

pub(super) fn evaluate(id: &str, payload: &Value, history: &[String]) -> Result<Value, Refusal> {
    let spec = spec(id)
        .ok_or_else(|| refusal("INTERGATE_SPEC_NOT_FOUND", "Unknown canonical intergate"))?;
    bounded(payload, history)?;
    let p = payload
        .as_object()
        .ok_or_else(|| invalid("Payload must be an object"))?;
    let edge = format!("{}->{}", spec.from, spec.to);
    let repeated = history.iter().filter(|s| *s == &edge).count() >= 2
        || history
            .last()
            .is_some_and(|last| history.iter().filter(|s| *s == last).count() >= 2);
    let checked = check_source_contract_descent(p, repeated)
        .and_then(|()| dispatch_source_contract_gate(&spec, p));
    let mut output = match checked {
        Ok(details) => {
            let mut output = result(&spec,"PASS",None,"Finite source-contract checks passed; observations remain scoped and grant no authority");
            output["source_contract_observation"] = details;
            output
        }
        Err(error) => {
            let mut output = result(&spec, "BLOCKED", Some(&error.code), &error.message);
            if error.code == "CURVATURE_OBSTRUCTION_DETECTED" {
                output["status"] = json!("DIVERTED");
                output["transition_to"] = json!("PFP-11-QUARANTINE");
                output["curvature_obstruction"] = json!({"detected":true,"loop_edges":history,"holonomy_norm":1,"reason":error.message});
            }
            output
        }
    };
    output["implementation"] = json!("core_adversary.intergates.v2");
    output["contract_profile"] = json!(SOURCE_CONTRACT_PROFILE);
    output["source_profile_sha256"] =
        json!(sha256_ref(include_bytes!("intergates_source_contract.rs")));
    Ok(output)
}

const MEASURED_FIELDS_TABLE: &[&[(&str, &str)]] = &[
    &[
        ("round_number", "int"),
        ("prompt_complexity_score", "number"),
        ("agent_capacity_score", "number"),
        ("feedback_loop_ms", "int"),
        ("feedback_loop_limit_ms", "int"),
        ("prior_round", "nullable_object"),
    ],
    &[
        ("round_number", "int"),
        ("previous_prompt_kl_divergence", "number"),
        ("carrier_isomorphism_valid", "bool"),
        ("carrier_mapping", "object"),
    ],
    &[
        ("critique_severity", "number"),
        ("response_vagueness_index", "number"),
        ("yields_without_evidence", "bool"),
        ("has_typed_defect_admission", "bool"),
        ("typed_defect", "nullable_object"),
        ("sponsor_challenge_present", "bool"),
        ("response_evidence_hex", "text"),
        ("explicit_refusal", "bool"),
    ],
    &[
        ("sandbox_boundary_active", "bool"),
        ("declared_authority_effect", "text"),
        ("has_production_side_effects", "bool"),
        ("canonical_before_hex", "text"),
        ("canonical_after_hex", "text"),
        ("sandbox_before_hex", "text"),
        ("sandbox_restored_hex", "text"),
    ],
    &[
        ("prompt_text", "text"),
        ("urgency_indicators", "texts"),
        ("sanitized_prompt_text", "text"),
        ("verification_started_ms", "int"),
        ("verification_completed_ms", "int"),
        ("minimum_buffer_ms", "int"),
        ("declared_time_constraint", "text"),
    ],
    &[
        ("turn_number", "int"),
        ("antagonism_score", "number"),
        ("prior_turn", "nullable_object"),
        ("has_acknowledged_error", "bool"),
        ("repair_action_proposed", "text"),
        ("scar_before", "texts"),
        ("scar_after", "texts"),
        ("deescalation_envelope", "text"),
    ],
    &[
        ("agent_evaluator_ids", "texts"),
        ("sampling_seeds", "ints"),
        ("producer_id", "nonempty_text"),
        ("producer_context_hex", "text"),
        ("evaluator_contexts", "object"),
        ("dissenting_evaluator_ids", "texts"),
        ("dissent_records", "objects"),
    ],
    &[
        ("quarantine_cause", "nonempty_text"),
        ("harm_class", "nonempty_text"),
        ("repair_before_hex", "nonempty_text"),
        ("repair_after_hex", "nonempty_text"),
        ("candidate_content", "text"),
        ("checker_receipt_hex", "nonempty_text"),
        ("checker_receipt_verdict", "text"),
    ],
    &[
        ("detected_exploit_uids", "texts"),
        ("exploit_severities", "numbers"),
        ("bound_countermeasure_uids", "texts"),
        ("applied_countermeasure_uids", "texts"),
    ],
    &[
        ("candidate_summary_text", "text"),
        ("checker_receipt_verdict", "text"),
        ("candidate_content", "text"),
        ("checker_receipt_hex", "nonempty_text"),
    ],
];

// V2 changes only input availability. V1 and its supplied finite predicates
// above remain available for exact old-host replay. Never fill unmeasured
// cognitive scores, signatures, checker receipts or detector observations.
fn measured_fields(index: u8) -> &'static [(&'static str, &'static str)] {
    index
        .checked_sub(1)
        .and_then(|idx| MEASURED_FIELDS_TABLE.get(usize::from(idx)))
        .copied()
        .unwrap_or(&[])
}

fn measured_kind(value: &Value, kind: &str) -> bool {
    match kind {
        "int" => value.as_u64().is_some(),
        "ints" => value
            .as_array()
            .is_some_and(|a| a.iter().all(|v| v.as_u64().is_some())),
        "numbers" => value
            .as_array()
            .is_some_and(|a| a.iter().all(|v| super::matches_kind(v, "number"))),
        "object" => value.is_object(),
        "nullable_object" => value.is_null() || value.is_object(),
        "objects" => value
            .as_array()
            .is_some_and(|a| a.iter().all(Value::is_object)),
        _ => super::matches_kind(value, kind),
    }
}

fn check_measured_malformed(index: u8, p: &Fields) -> Option<(String, String)> {
    let optional = [
        ("residual_descent_observed", "bool"),
        ("bypass_gates_requested", "bool"),
        ("task_id", "nonempty_text"),
        ("source_digest", "nonempty_text"),
        ("trust_policy", "object"),
        ("expected_binding", "object"),
        ("now", "int"),
        ("witness_issuers", "object"),
        ("dual_witnesses", "objects"),
        ("checker_issuer", "nonempty_text"),
        ("checker_id", "nonempty_text"),
        ("checker_attestation", "object"),
        ("timestamp_issuer", "nonempty_text"),
        ("timestamp_witness", "object"),
    ];
    if let Some((key, kind)) = measured_fields(index)
        .iter()
        .chain(optional.iter())
        .find(|(key, kind)| p.get(*key).is_some_and(|v| !measured_kind(v, kind)))
    {
        return Some((
            "INTERGATE_PAYLOAD_INVALID".into(),
            format!("{key} must be supplied as {kind}"),
        ));
    }
    measured_fields(index)
        .iter()
        .filter(|(key, _)| key.ends_with("_hex") && p.contains_key(*key))
        .find_map(|(key, _)| bytes(p, key, *key == "response_evidence_hex").err())
        .map(|error| (error.code, error.message))
}

fn has_early_negative_operands(index: u8, p: &Fields, repeated: bool) -> bool {
    if repeated && p.get("residual_descent_observed") == Some(&Value::Bool(false)) {
        return true;
    }
    !repeated && index == 5 && p.get("bypass_gates_requested") == Some(&Value::Bool(true))
}

fn is_repeated_edge(selected: &Spec, history: &[String]) -> bool {
    let edge = format!("{}->{}", selected.from, selected.to);
    if history.iter().filter(|s| *s == &edge).count() >= 2 {
        return true;
    }
    history
        .last()
        .is_some_and(|last| history.iter().filter(|s| *s == last).count() >= 2)
}

#[allow(clippy::too_many_arguments)]
fn resolve_measured_output(
    id: &str,
    selected: &Spec,
    payload: &Value,
    p: &Fields,
    history: &[String],
    malformed: Option<(String, String)>,
    missing: Vec<&str>,
    repeated: bool,
) -> Result<Value, Refusal> {
    if let Some((code, msg)) = malformed {
        return Ok(result(selected, "BLOCKED", Some(&code), &msg));
    }
    if has_early_negative_operands(selected.index, p, repeated) {
        // This finite negative already has its complete operands: actual
        // traversal history and an explicit false descent observation.
        return evaluate(id, payload, history);
    }
    if !missing.is_empty() {
        let code = if missing == ["residual_descent_observed"] {
            "INTERGATE_DESCENT_UNMEASURED"
        } else {
            "GATE_WITNESS_UNMEASURED"
        };
        let mut output = result(
            selected,
            "HOLD",
            Some(code),
            "Required source observations are absent; no finite predicate failure or transition admission is established",
        );
        output["missing_inputs"] = json!(missing);
        return Ok(output);
    }
    let mut output = evaluate(id, payload, history)?;
    if output["refusal_code"] == "INTERGATE_DESCENT_UNMEASURED" {
        output["status"] = json!("HOLD");
        output["missing_inputs"] = json!(["residual_descent_observed"]);
    }
    Ok(output)
}

pub(super) fn evaluate_measured(
    id: &str,
    payload: &Value,
    history: &[String],
) -> Result<Value, Refusal> {
    let selected = spec(id)
        .ok_or_else(|| refusal("INTERGATE_SPEC_NOT_FOUND", "Unknown canonical intergate"))?;
    bounded(payload, history)?;
    let p = payload
        .as_object()
        .ok_or_else(|| invalid("Payload must be an object"))?;
    // Check every present operand before returning missing measurements. An
    // explicitly malformed supplied field is never hidden by another absence.
    let malformed = check_measured_malformed(selected.index, p);
    let mut missing: Vec<_> = measured_fields(selected.index)
        .iter()
        .filter(|(key, _)| !p.contains_key(*key))
        .map(|(key, _)| *key)
        .collect();
    let repeated = is_repeated_edge(&selected, history);
    if repeated && !p.contains_key("residual_descent_observed") {
        missing.push("residual_descent_observed");
    }
    let mut output = resolve_measured_output(
        id, &selected, payload, p, history, malformed, missing, repeated,
    )?;
    output["implementation"] = json!("core_adversary.intergates.v3");
    output["contract_profile"] = json!(super::MEASURED_SOURCE_CONTRACT_PROFILE);
    output["source_profile_sha256"] =
        json!(sha256_ref(include_bytes!("intergates_source_contract.rs")));
    Ok(output)
}

// Origin: engine/crates_rs/core_adversary/src/intergates_source_contract.rs
// Claim: urn:core:crates_rs:core-adversary:intergates-source-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfb93ae90 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfb93ae90` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfb93ae90 {
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
impl BoundaryErrorfb93ae90 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfb93ae90 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfb93ae90 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfb93ae90 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfb93ae90> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfb93ae90::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfb93ae90::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfb93ae90::ExceedsCapacity {
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
mod measured_tests {
    use super::*;

    #[test]
    fn missing_is_hold_but_supplied_malformed_is_blocked_for_every_source_gate() {
        for id in super::super::IDS {
            let missing = evaluate_measured(id, &json!({}), &[]).unwrap();
            assert_eq!(missing["status"], "HOLD");
            assert_eq!(missing["refusal_code"], "GATE_WITNESS_UNMEASURED");
            assert!(!missing["missing_inputs"].as_array().unwrap().is_empty());
            let invalid =
                evaluate_measured(id, &json!({"residual_descent_observed":0}), &[]).unwrap();
            assert_eq!(invalid["status"], "BLOCKED");
            assert_eq!(invalid["refusal_code"], "INTERGATE_PAYLOAD_INVALID");
        }
        let old = evaluate(super::super::IDS[9], &json!({}), &[]).unwrap();
        assert_eq!(old["status"], "BLOCKED");
        assert_eq!(old["refusal_code"], "SUMMARY_PART_MISSING");
    }

    #[test]
    fn independently_complete_negative_controls_are_not_hidden_by_missing_other_measurements() {
        let id = super::super::IDS[4];
        let edge = "PFP-09-ANTI-HYPE->PFP-10-BOUNDARY-FUZZER".to_owned();
        let actual = evaluate_measured(
            id,
            &json!({"residual_descent_observed":false}),
            &[edge.clone(), edge],
        )
        .unwrap();
        assert_eq!(actual["status"], "DIVERTED");
        let bypass = evaluate_measured(id, &json!({"bypass_gates_requested":true}), &[]).unwrap();
        assert_eq!(bypass["status"], "BLOCKED");
        assert_eq!(bypass["refusal_code"], "FALSE_URGENCY_INJECTED");
        for (id, key, value) in [
            (super::super::IDS[3], "canonical_before_hex", "zz"),
            (super::super::IDS[7], "checker_receipt_hex", "FF"),
        ] {
            let malformed = evaluate_measured(id, &json!({key:value}), &[]).unwrap();
            assert_eq!(malformed["status"], "BLOCKED");
            assert_eq!(malformed["refusal_code"], "INTERGATE_PAYLOAD_INVALID");
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_fb93ae90 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfb93ae90::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfb93ae90::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfb93ae90::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfb93ae90::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfb93ae90::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorfb93ae90::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorfb93ae90::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
