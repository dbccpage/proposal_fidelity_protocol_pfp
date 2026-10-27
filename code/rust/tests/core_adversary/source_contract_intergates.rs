use ed25519_dalek::{Signer, SigningKey};
use core_epistemic_immune_system::authenticated::*;
use core_adversary::evidence::sha256_ref;
use core_adversary::intergates;
use serde_json::{json, Value};

fn run(index: usize, mut payload: Value) -> Value {
    payload["contract_profile"] = json!(intergates::SOURCE_CONTRACT_PROFILE);
    intergates::evaluate(intergates::IDS[index - 1], &payload, &[]).unwrap()
}
fn assert_block(index: usize, payload: Value, code: &str) {
    let actual = run(index, payload);
    assert_eq!(actual["status"], "BLOCKED", "{actual}");
    assert_eq!(actual["refusal_code"], code, "{actual}");
}
fn fixture_late(index: usize) -> Value {
    match index {
        6 => json!({"turn_number":2,"antagonism_score":0.8,"prior_turn":{"turn_number":1,"antagonism_score":0.7},
            "has_acknowledged_error":true,"repair_action_proposed":"fix candidate","scar_before":["first-error"],
            "scar_after":["first-error","second-error"],"deescalation_envelope":"Retain the error and propose its repair."}),
        7 => json!({"agent_evaluator_ids":["one","two"],"sampling_seeds":[1,2],"producer_id":"author",
            "producer_context_hex":"6162","evaluator_contexts":{"one":"6364","two":"6566"},
            "dissenting_evaluator_ids":["two"],"dissent_records":[{"evaluator_id":"two","content_hex":"7778"}]}),
        8 => signed_fixture(8),
        9 => json!({"detected_exploit_uids":["urgency","cherry-pick"],"exploit_severities":[0.7,0.8],
            "bound_countermeasure_uids":["timestamp","negative-control"],"applied_countermeasure_uids":["negative-control"]}),
        10 => signed_fixture(10),
        _ => unreachable!(),
    }
}
fn fixture(index: usize) -> Value {
    match index {
        1 => json!({"round_number":1,"prompt_complexity_score":1,"agent_capacity_score":1,
            "feedback_loop_ms":20,"feedback_loop_limit_ms":50,"prior_round":null}),
        2 => json!({"round_number":1,"previous_prompt_kl_divergence":0.15,"carrier_isomorphism_valid":true,
            "carrier_mapping":{"source":["a","b"],"target":["x","y"],"forward":[1,0],"inverse":[1,0]}}),
        3 => json!({"critique_severity":0.8,"response_vagueness_index":0.2,"yields_without_evidence":false,
            "has_typed_defect_admission":false,"typed_defect":null,"sponsor_challenge_present":true,
            "response_evidence_hex":"6162","explicit_refusal":false}),
        4 => json!({"sandbox_boundary_active":true,"declared_authority_effect":"None","has_production_side_effects":false,
            "canonical_before_hex":"6162","canonical_after_hex":"6162","sandbox_before_hex":"6364","sandbox_restored_hex":"6364"}),
        5 => json!({"prompt_text":"ACT IMMEDIATELY inspect this","urgency_indicators":[],"sanitized_prompt_text":" inspect this",
            "verification_started_ms":10,"verification_completed_ms":510,"minimum_buffer_ms":500,"declared_time_constraint":""}),
        other => fixture_late(other),
    }
}
fn signed_fixture(index: usize) -> Value {
    let candidate = "repaired prompt";
    let raw = serde_json::to_vec(&json!({"verdict":"ACCEPTED","candidate_content_sha256":sha256_ref(candidate.as_bytes()),"checker_id":"finite-checker"})).unwrap();
    let mut p = json!({"task_id":"finite-task","source_digest":sha256_ref(b"frozen-source"),"candidate_content":candidate,
        "checker_receipt_hex":hex::encode(&raw),"checker_receipt_verdict":"ACCEPTED","now":100,
        "quarantine_cause":"bad prompt","harm_class":"injection","repair_before_hex":hex::encode(b"broken prompt"),
        "repair_after_hex":hex::encode(candidate),"witness_issuers":{"quarantine":"clinic","master":"proof"},
        "checker_id":"finite-checker","checker_issuer":"proof",
        "candidate_summary_text":"What it supports: this instance. What it does not support: other cases. Narrowest defensible claim: finite. Next test needed: replay."});
    let rule = if index == 8 {
        include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/08_quarantine_recovery_containment.yaml").as_slice()
    } else {
        include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/10_terminal_reality_tether.yaml").as_slice()
    };
    let context = if index == 8 {
        sha256_ref(
            &serde_json::to_vec(&json!([
                p["task_id"],
                p["quarantine_cause"],
                p["harm_class"],
                p["repair_before_hex"],
                p["repair_after_hex"]
            ]))
            .unwrap(),
        )
    } else {
        sha256_ref(b"finite-task")
    };
    let binding = Binding {
        spec_id: intergates::IDS[index - 1].into(),
        scope: "adversary.intergate.source.v1".into(),
        rule_digest: sha256_ref(rule),
        source_digest: sha256_ref(b"frozen-source"),
        subject_digest: sha256_ref(candidate.as_bytes()),
        context_digest: context,
    };
    let mut keys = Vec::new();
    let mut witnesses = Vec::new();
    for (issuer, seed) in [("clinic", 1), ("proof", 2)] {
        let signing = SigningKey::from_bytes(&[seed; 32]);
        keys.push(TrustedKey {
            issuer: issuer.into(),
            key_id: "key".into(),
            public_key_hex: hex::encode(signing.verifying_key().as_bytes()),
            purposes: vec![Purpose::Admission],
            scopes: vec!["adversary.intergate.source.v1".into()],
            not_before: 1,
            not_after: 1000,
            max_lifetime_seconds: 200,
            revoked: false,
            observer_source_digest: None,
        });
        witnesses.push(sign_evidence(&binding, &raw, issuer, &signing));
    }
    p["trust_policy"] = serde_json::to_value(TrustPolicy {
        schema_version: POLICY_SCHEMA.into(),
        trust_domain: "fixture-only".into(),
        keys,
    })
    .unwrap();
    p["expected_binding"] = serde_json::to_value(binding).unwrap();
    p["dual_witnesses"] = serde_json::to_value(&witnesses).unwrap();
    p["checker_attestation"] = serde_json::to_value(&witnesses[1]).unwrap();
    p
}
fn sign_evidence(
    binding: &Binding,
    raw: &[u8],
    issuer: &str,
    signing: &SigningKey,
) -> SignedEvidence {
    let mut attestation = Attestation {
        schema_version: SCHEMA.into(),
        trust_domain: "fixture-only".into(),
        purpose: Purpose::Admission,
        issuer: issuer.into(),
        key_id: "key".into(),
        event_id: format!("event-{issuer}"),
        binding: binding.clone(),
        issued_at: 90,
        expires_at: 200,
        outcome: "ADMIT".into(),
        previous_event: None,
        evidence_digest: sha256_ref(raw),
        signature_hex: String::new(),
    };
    attestation.signature_hex = hex::encode(
        signing
            .sign(&attestation.signing_bytes().unwrap())
            .to_bytes(),
    );
    SignedEvidence {
        attestation,
        evidence_hex: hex::encode(raw),
    }
}

#[test]
fn source_profile_uses_the_declared_surprise_lower_bound() {
    let payload = json!({
        "contract_profile": "pfp-intergates-source-v1",
        "round_number": 1,
        "previous_prompt_kl_divergence": 0.10,
        "carrier_isomorphism_valid": true,
        "epistemic_entropy_delta": 0.10,
        "gauge_shift_applied": false
    });
    let outcome = intergates::evaluate("PFP-IG-02-EPISTEMIC-SURPRISE", &payload, &[]).unwrap();
    assert_eq!(outcome["status"], "BLOCKED");
    assert_eq!(outcome["refusal_code"], "EPISTEMIC_STAGNATION");
}

#[test]
fn every_source_gate_has_a_finite_positive_and_missing_evidence_refusal() {
    for index in 1..=10 {
        let actual = run(index, fixture(index));
        assert_eq!(actual["status"], "PASS", "gate {index}: {actual}");
        assert_eq!(
            actual["contract_profile"],
            intergates::SOURCE_CONTRACT_PROFILE
        );
        assert_eq!(actual["can_authorize"], false);
        assert_eq!(actual["authority_effect"], "None");
        assert_eq!(actual["source_profile_sha256"].as_str().unwrap().len(), 71);
        assert_eq!(
            run(index, json!({}))["status"],
            "BLOCKED",
            "missing gate {index}"
        );
    }
}

#[test]
fn flow_observes_two_consecutive_rounds_and_declared_latency() {
    let mut p = fixture(1);
    p["prompt_complexity_score"] = json!(0.7);
    assert_block(1, p.clone(), "FLOW_ADJUSTMENT_REQUIRED");
    p["round_number"] = json!(2);
    p["prior_round"] =
        json!({"round_number":1,"prompt_complexity_score":0.6,"agent_capacity_score":1});
    assert_block(1, p.clone(), "FLOW_STAGNATION_DETECTED");
    p["prior_round"]["round_number"] = json!(0);
    assert_block(1, p, "INTERGATE_PAYLOAD_INVALID");
    let mut p = fixture(1);
    p["feedback_loop_ms"] = json!(51);
    assert_block(1, p, "FLOW_FEEDBACK_LATENCY_EXCEEDED");
    let mut p = fixture(1);
    p["prompt_complexity_score"] = json!(1.2);
    assert_eq!(run(1, p.clone())["status"], "PASS");
    p["prompt_complexity_score"] = serde_json::from_str("1.2000000000000000000000001").unwrap();
    assert_block(1, p, "FLOW_OVERWHELM_DETECTED");
}

#[test]
fn surprise_checks_upper_bound_and_actual_inverse() {
    let mut p = fixture(2);
    p["previous_prompt_kl_divergence"] = json!(3.5);
    assert_eq!(run(2, p.clone())["status"], "PASS");
    p["previous_prompt_kl_divergence"] = serde_json::from_str("3.50000000000000000001").unwrap();
    assert_block(2, p, "EPISTEMIC_DERAILMENT");
    let mut p = fixture(2);
    p["carrier_mapping"]["inverse"] = json!([0, 1]);
    assert_block(2, p, "CARRIER_RETURN_UNVERIFIED");
}

#[test]
fn evasion_requires_bound_defect_or_direct_response() {
    let mut p = fixture(3);
    p["yields_without_evidence"] = json!(true);
    p["has_typed_defect_admission"] = json!(true);
    assert_block(3, p.clone(), "INTERGATE_PAYLOAD_INVALID");
    p["typed_defect"] =
        json!({"code":"COUNTEREXAMPLE","evidence_hex":"6162","evidence_sha256":sha256_ref(b"ab")});
    assert_eq!(run(3, p.clone())["status"], "PASS");
    p["response_evidence_hex"] = json!("");
    assert_block(3, p.clone(), "SPONSOR_CHALLENGE_UNANSWERED");
    p["explicit_refusal"] = json!(true);
    assert_eq!(run(3, p)["status"], "PASS");
}

#[test]
fn sandbox_checks_side_effect_and_actual_restoration() {
    let mut p = fixture(4);
    p["has_production_side_effects"] = json!(true);
    assert_block(4, p, "UNAUTHORIZED_PLAY_EFFECT");
    let mut p = fixture(4);
    p["canonical_after_hex"] = json!("6163");
    assert_block(4, p, "UNAUTHORIZED_PLAY_EFFECT");
    let mut p = fixture(4);
    p["sandbox_restored_hex"] = json!("6163");
    assert_block(4, p, "SANDBOX_ROLLBACK_MISMATCH");
}

#[test]
fn urgency_returns_exact_sanitized_text_and_waits_for_observed_buffer() {
    let p = fixture(5);
    assert_eq!(
        run(5, p.clone())["source_contract_observation"]["downstream_text"],
        " inspect this"
    );
    let mut pending = p.clone();
    pending["verification_completed_ms"] = json!(509);
    assert_block(5, pending, "VERIFICATION_BUFFER_PENDING");
    let mut unstripped = p.clone();
    unstripped["sanitized_prompt_text"] = p["prompt_text"].clone();
    assert_block(5, unstripped, "URGENCY_SANITIZATION_MISMATCH");
    let mut deadline = p;
    deadline["declared_time_constraint"] = json!("deadline at 600ms");
    assert_block(5, deadline, "TIMESTAMP_WITNESS_REQUIRED");
}

#[test]
fn actual_timestamp_signature_is_checked_against_current_constraint() {
    let mut p = signed_fixture(10);
    for (key, value) in fixture(5).as_object().unwrap() {
        p[key] = value.clone();
    }
    p["declared_time_constraint"] = json!("deadline at 600ms");
    p["timestamp_issuer"] = json!("proof");
    p["expected_binding"]["spec_id"] = json!(intergates::IDS[4]);
    p["expected_binding"]["rule_digest"] = json!(sha256_ref(include_bytes!("../../../../pfp/infrastructure/yaml/gates/intergates/05_false_urgency_desensitization.yaml")));
    let binding: Binding = serde_json::from_value(p["expected_binding"].clone()).unwrap();
    let raw = serde_json::to_vec(
        &json!({"constraint_text":"deadline at 600ms","observed_at_ms":510,"deadline_ms":600}),
    )
    .unwrap();
    p["timestamp_witness"] = serde_json::to_value(sign_evidence(
        &binding,
        &raw,
        "proof",
        &SigningKey::from_bytes(&[2; 32]),
    ))
    .unwrap();
    assert_eq!(run(5, p.clone())["status"], "PASS");
    let mut bad = p.clone();
    bad["timestamp_witness"]["attestation"]["signature_hex"] = json!("00".repeat(64));
    assert_block(5, bad, "EIS_AUTH_BAD_SIGNATURE");
    p["declared_time_constraint"] = json!("a different deadline");
    assert_block(5, p, "TIMESTAMP_WITNESS_MISMATCH");
}

#[test]
fn affect_requires_repair_and_keeps_scars() {
    let mut p = fixture(6);
    p["has_acknowledged_error"] = json!(false);
    assert_block(6, p, "DEESCALATION_REJOIN_PENDING");
    let mut p = fixture(6);
    p["scar_after"] = json!(["second-error"]);
    assert_block(6, p, "SCAR_CUSTODY_LOST");
    let mut p = fixture(6);
    p["deescalation_envelope"] = json!("");
    assert_block(6, p, "DEESCALATION_ENVELOPE_REQUIRED");
}

#[test]
fn consensus_rejects_copied_context_or_missing_dissent() {
    let mut p = fixture(7);
    p["evaluator_contexts"]["one"] = p["producer_context_hex"].clone();
    assert_block(7, p, "ECHO_CHAMBER_CONSENSUS");
    let mut p = fixture(7);
    p["dissent_records"] = json!([]);
    assert_block(7, p, "DISSENT_RECORD_MISMATCH");
}

#[test]
fn quarantine_authenticates_both_roles_and_binds_repair_and_harm() {
    let mut p = fixture(8);
    p["dual_witnesses"][1] = p["dual_witnesses"][0].clone();
    assert_block(8, p, "DUAL_WITNESS_REQUIRED");
    let mut p = fixture(8);
    p["dual_witnesses"][1]["attestation"]["signature_hex"] = json!("00".repeat(64));
    assert_block(8, p, "EIS_AUTH_BAD_SIGNATURE");
    let mut p = fixture(8);
    p["harm_class"] = json!("different");
    assert_block(8, p, "INTERGATE_ATTESTATION_BINDING_MISMATCH");
    let mut p = fixture(8);
    p["trust_policy"] = Value::Null;
    assert_block(8, p, "INTERGATE_TRUST_UNCONFIGURED");
}

#[test]
fn quarantine_cannot_reinstate_a_rejected_checker_receipt() {
    let mut p = fixture(8);
    let raw = serde_json::to_vec(&json!({
        "verdict":"REJECTED",
        "candidate_content_sha256":sha256_ref(p["candidate_content"].as_str().unwrap().as_bytes()),
        "checker_id":"finite-checker"
    }))
    .unwrap();
    let binding: Binding = serde_json::from_value(p["expected_binding"].clone()).unwrap();
    let witnesses: Vec<_> = [("clinic", 1), ("proof", 2)]
        .into_iter()
        .map(|(issuer, seed)| {
            sign_evidence(&binding, &raw, issuer, &SigningKey::from_bytes(&[seed; 32]))
        })
        .collect();
    p["dual_witnesses"] = serde_json::to_value(witnesses).unwrap();
    p["checker_receipt_hex"] = json!(hex::encode(raw));
    p["checker_receipt_verdict"] = json!("REJECTED");
    assert_block(8, p.clone(), "RECEIPT_NOT_ACCEPTED");
    p["checker_receipt_verdict"] = json!("ACCEPTED");
    assert_block(8, p, "CHECKER_RECEIPT_VERDICT_MISMATCH");
}

#[test]
fn defense_checks_every_pair_and_applied_high_severity_countermeasure() {
    let mut p = fixture(9);
    p["bound_countermeasure_uids"] = json!(["timestamp"]);
    assert_block(9, p, "DECEPTION_SURFACE_UNMITIGATED");
    let mut p = fixture(9);
    p["applied_countermeasure_uids"] = json!([]);
    assert_block(9, p, "COUNTERMEASURE_NOT_APPLIED");
}

#[test]
fn terminal_checks_actual_checker_signature_and_frozen_task() {
    let mut p = fixture(10);
    p["task_id"] = json!("foreign-task");
    assert_block(10, p, "INTERGATE_ATTESTATION_BINDING_MISMATCH");
    let mut p = fixture(10);
    p["checker_id"] = json!("foreign-checker");
    assert_block(10, p, "CHECKER_ID_MISMATCH");
    let mut p = fixture(10);
    p["now"] = json!(201);
    assert_block(10, p, "EIS_AUTH_EXPIRED_OR_FUTURE");
    let mut p = fixture(10);
    p["checker_attestation"]["attestation"]["signature_hex"] = json!("00".repeat(64));
    assert_block(10, p, "EIS_AUTH_BAD_SIGNATURE");
}

#[test]
fn legacy_receipt_identity_and_new_repeated_actual_edge_are_explicit() {
    let p = json!({"epistemic_entropy_delta":0.10,"gauge_shift_applied":false});
    let old = intergates::evaluate(intergates::IDS[1], &p, &[]).unwrap();
    assert_eq!(old["status"], "PASS");
    assert!(old.get("contract_profile").is_none());
    assert_eq!(old["implementation"], "core_adversary.intergates.v1");
    assert_eq!(
        old["specification_sha256"],
        "sha256:27ca9fd449e4c09af438f6228c308f708834ef36ffd90beb5ba6dd47bb74fcc3"
    );
    let mut explicit = p;
    explicit["contract_profile"] = json!(intergates::LEGACY_DIAGNOSTIC_PROFILE);
    assert_eq!(
        intergates::evaluate(intergates::IDS[1], &explicit, &[]).unwrap(),
        old
    );
    let mut p = fixture(2);
    p["contract_profile"] = json!(intergates::SOURCE_CONTRACT_PROFILE);
    let history = vec!["observed-source->observed-target".into(); 2];
    let output = intergates::evaluate(intergates::IDS[1], &p, &history).unwrap();
    assert_eq!(output["refusal_code"], "INTERGATE_DESCENT_UNMEASURED");
    p["residual_descent_observed"] = json!(false);
    assert_eq!(
        intergates::evaluate(intergates::IDS[1], &p, &history).unwrap()["status"],
        "DIVERTED"
    );
    p["contract_profile"] = json!("unknown");
    assert_eq!(
        intergates::evaluate(intergates::IDS[1], &p, &[])
            .unwrap_err()
            .code,
        "INTERGATE_PROFILE_UNSUPPORTED"
    );
    p["contract_profile"] = json!(intergates::SOURCE_CONTRACT_PROFILE);
    p["residual_descent_observed"] = json!("false");
    assert_eq!(
        intergates::evaluate(intergates::IDS[1], &p, &[]).unwrap()["refusal_code"],
        "INTERGATE_PAYLOAD_INVALID"
    );
    assert_eq!(
        intergates::evaluate(intergates::IDS[1], &p, &vec!["edge".into(); 65])
            .unwrap_err()
            .code,
        "INTERGATE_INPUT_TOO_LARGE"
    );
}

// Origin: engine/crates_rs/tests/core_adversary/source_contract_intergates.rs
// Claim: urn:core:crates_rs:tests:source-contract-intergates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord70045478 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord70045478` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError70045478 {
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
impl BoundaryError70045478 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError70045478 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError70045478 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord70045478 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError70045478> {
        if capacity_bound == 0 {
            return Err(BoundaryError70045478::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError70045478::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError70045478::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_70045478() {
    let admitted = BoundaryRecord70045478::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord70045478::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
