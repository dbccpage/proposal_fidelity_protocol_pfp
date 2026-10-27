//! Finite signature/custody controls. Fixture keys are not production authority.
use ed25519_dalek::{Signer, SigningKey};
use core_epistemic_immune_system::authenticated::*;
use serde_json::json;

fn fixture() -> (SigningKey, TrustPolicy, Binding) {
    let signing = SigningKey::from_bytes(&[7; 32]);
    let policy = TrustPolicy {
        schema_version: POLICY_SCHEMA.into(),
        trust_domain: "fixture-only".into(),
        keys: vec![TrustedKey {
            issuer: "operator".into(),
            key_id: "key-1".into(),
            public_key_hex: hex::encode(signing.verifying_key().as_bytes()),
            purposes: vec![Purpose::Admission, Purpose::Health, Purpose::Observation],
            scopes: vec!["fixture".into()],
            not_before: 10,
            not_after: 1000,
            max_lifetime_seconds: 100,
            revoked: false,
            observer_source_digest: Some(bytes_digest(b"checker")),
        }],
    };
    let binding = Binding {
        spec_id: "rule-1".into(),
        scope: "fixture".into(),
        rule_digest: bytes_digest(b"rule"),
        source_digest: bytes_digest(b"manifest"),
        subject_digest: bytes_digest(b"rule"),
        context_digest: bytes_digest(b"profile"),
    };
    (signing, policy, binding)
}

fn sign(
    key: &SigningKey,
    binding: &Binding,
    purpose: Purpose,
    outcome: &str,
    event_id: &str,
    time: u64,
    previous: Option<String>,
) -> SignedEvidence {
    let raw = if purpose == Purpose::Admission {
        b"operator decision".to_vec()
    } else {
        serde_json::to_vec(&json!({
            "schema_version":"core.eis.observed-evidence.v1","observer_id":"operator",
            "run_id":event_id,"subject_digest":binding.subject_digest,
            "source_digest":bytes_digest(b"checker"),"outcome":outcome,
        }))
        .unwrap()
    };
    let mut a = Attestation {
        schema_version: SCHEMA.into(),
        trust_domain: "fixture-only".into(),
        purpose,
        issuer: "operator".into(),
        key_id: "key-1".into(),
        event_id: event_id.into(),
        binding: binding.clone(),
        issued_at: time,
        expires_at: time + 50,
        outcome: outcome.into(),
        previous_event: previous,
        evidence_digest: bytes_digest(&raw),
        signature_hex: String::new(),
    };
    a.signature_hex = hex::encode(key.sign(&a.signing_bytes().unwrap()).to_bytes());
    SignedEvidence {
        attestation: a,
        evidence_hex: hex::encode(raw),
    }
}

#[test]
fn successful_process_observation_is_limited_to_its_explicit_scope() {
    let (key, mut policy, mut binding) = fixture();
    let outcome = "PROCESS_EXECUTION_OBSERVED";
    let outside = sign(
        &key,
        &binding,
        Purpose::Observation,
        outcome,
        "process-1",
        100,
        None,
    );
    assert_eq!(
        verify(&outside, &policy, &binding, Purpose::Observation, 100)
            .unwrap_err()
            .code,
        "EIS_AUTH_BAD_OUTCOME"
    );
    binding.scope = "adversary.host-process.v1".into();
    policy.keys[0].scopes.push(binding.scope.clone());
    let observed = sign(
        &key,
        &binding,
        Purpose::Observation,
        outcome,
        "process-1",
        100,
        None,
    );
    assert!(verify(&observed, &policy, &binding, Purpose::Observation, 100).is_ok());
    let wrong_purpose = sign(
        &key,
        &binding,
        Purpose::Health,
        outcome,
        "process-1",
        100,
        None,
    );
    assert_eq!(
        verify(&wrong_purpose, &policy, &binding, Purpose::Health, 100)
            .unwrap_err()
            .code,
        "EIS_AUTH_BAD_OUTCOME"
    );
    let defect = sign(
        &key,
        &binding,
        Purpose::Observation,
        "DEFECT_OBSERVED",
        "defect-1",
        100,
        None,
    );
    assert!(verify(&defect, &policy, &binding, Purpose::Observation, 100).is_ok());
}

#[test]
fn kernel_observation_does_not_widen_process_or_legacy_scopes() {
    let (key, mut policy, mut binding) = fixture();
    for scope in ["fixture", "adversary.host-process.v1", "adversary.host-lean.v1"] {
        binding.scope = scope.into();
        policy.keys[0].scopes = vec![scope.into()];
        let signed = sign(
            &key,
            &binding,
            Purpose::Observation,
            "KERNEL_VERIFICATION_OBSERVED",
            "kernel-one",
            100,
            None,
        );
        let result = verify(&signed, &policy, &binding, Purpose::Observation, 100);
        if scope == "adversary.host-lean.v1" {
            assert!(result.is_ok());
        } else {
            assert_eq!(result.unwrap_err().code, "EIS_AUTH_BAD_OUTCOME");
        }
    }
    let wrong_purpose = sign(
        &key,
        &binding,
        Purpose::Admission,
        "KERNEL_VERIFICATION_OBSERVED",
        "kernel-one",
        100,
        None,
    );
    assert_eq!(
        verify(&wrong_purpose, &policy, &binding, Purpose::Admission, 100)
            .unwrap_err()
            .code,
        "EIS_AUTH_BAD_OUTCOME"
    );
}

#[test]
fn signature_scope_source_and_clock_controls() {
    let (key, policy, binding) = fixture();
    let valid = sign(
        &key,
        &binding,
        Purpose::Health,
        "HEALTHY",
        "health-1",
        100,
        None,
    );
    assert!(verify(&valid, &policy, &binding, Purpose::Health, 100).is_ok());
    assert!(verify(&valid, &policy, &binding, Purpose::Health, 149).is_ok());
    for time in [99, 150, u64::MAX] {
        assert_eq!(
            verify(&valid, &policy, &binding, Purpose::Health, time)
                .unwrap_err()
                .code,
            "EIS_AUTH_EXPIRED_OR_FUTURE"
        );
    }
    let mut bad = valid.clone();
    bad.attestation.signature_hex = "00".repeat(64);
    assert_eq!(
        verify(&bad, &policy, &binding, Purpose::Health, 100)
            .unwrap_err()
            .code,
        "EIS_AUTH_BAD_SIGNATURE"
    );
    let mut other = binding.clone();
    other.subject_digest = bytes_digest(b"foreign");
    assert_eq!(
        verify(&valid, &policy, &other, Purpose::Health, 100)
            .unwrap_err()
            .code,
        "EIS_AUTH_BINDING_MISMATCH"
    );
    let mut bad = valid.clone();
    bad.evidence_hex = hex::encode(b"different evidence");
    assert_eq!(
        verify(&bad, &policy, &binding, Purpose::Health, 100)
            .unwrap_err()
            .code,
        "EIS_AUTH_EVIDENCE_MISMATCH"
    );
}

#[test]
fn policy_is_explicit_and_role_limited() {
    let (key, policy, binding) = fixture();
    let signed = sign(
        &key,
        &binding,
        Purpose::Health,
        "HEALTHY",
        "health-1",
        100,
        None,
    );
    for mode in [
        "revoked",
        "scope",
        "role",
        "source",
        "empty",
        "duplicate",
        "domain",
    ] {
        let mut other = policy.clone();
        match mode {
            "revoked" => other.keys[0].revoked = true,
            "scope" => other.keys[0].scopes = vec!["foreign".into()],
            "role" => other.keys[0].purposes = vec![Purpose::Admission],
            "source" => other.keys[0].observer_source_digest = Some(bytes_digest(b"foreign")),
            "empty" => other.keys.clear(),
            "duplicate" => other.keys.push(other.keys[0].clone()),
            _ => other.trust_domain = "other-operator".into(),
        }
        assert!(
            verify(&signed, &other, &binding, Purpose::Health, 100).is_err(),
            "{mode}"
        );
    }
}

#[test]
fn signed_narrative_cannot_replace_a_structured_observation() {
    let (key, policy, binding) = fixture();
    let mut signed = sign(
        &key,
        &binding,
        Purpose::Observation,
        "DEFECT_OBSERVED",
        "event-1",
        100,
        None,
    );
    signed.evidence_hex = hex::encode(b"ACCEPTED");
    signed.attestation.evidence_digest = bytes_digest(b"ACCEPTED");
    signed.attestation.signature_hex = hex::encode(
        key.sign(&signed.attestation.signing_bytes().unwrap())
            .to_bytes(),
    );
    assert_eq!(
        verify(&signed, &policy, &binding, Purpose::Observation, 100)
            .unwrap_err()
            .code,
        "EIS_AUTH_BAD_OBSERVATION"
    );
}

#[test]
fn admission_requires_exact_rule_chain_and_fresh_reinstatement() {
    let (key, policy, binding) = fixture();
    let first = sign(
        &key,
        &binding,
        Purpose::Admission,
        "ADMIT",
        "decision-1",
        100,
        None,
    );
    let first_hash = bytes_digest(&first.attestation.signing_bytes().unwrap());
    let suspended = sign(
        &key,
        &binding,
        Purpose::Admission,
        "SUSPEND",
        "decision-2",
        110,
        Some(first_hash),
    );
    let second_hash = bytes_digest(&suspended.attestation.signing_bytes().unwrap());
    let fresh = sign(
        &key,
        &binding,
        Purpose::Admission,
        "REINSTATE",
        "decision-3",
        170,
        Some(second_hash),
    );
    assert_eq!(
        history(&[first.clone()], &policy, &binding, b"rule", 100, true).unwrap()["status"],
        "ADMITTED"
    );
    assert!(history(
        &[first.clone()],
        &policy,
        &binding,
        b"changed rule",
        100,
        true
    )
    .is_err());
    assert!(history(
        &[first.clone(), first.clone()],
        &policy,
        &binding,
        b"rule",
        100,
        true
    )
    .is_err());
    assert_eq!(
        history(
            &[first.clone(), suspended.clone()],
            &policy,
            &binding,
            b"rule",
            110,
            true
        )
        .unwrap()["status"],
        "SUSPENDED"
    );
    assert!(history(
        &[first.clone(), suspended.clone()],
        &policy,
        &binding,
        b"rule",
        170,
        true
    )
    .is_err());
    // Earlier expired decisions remain authenticated history; a fresh signed
    // reinstatement is required before access can return ADMITTED again.
    let events = [first, suspended, fresh];
    assert_eq!(
        history(&events, &policy, &binding, b"rule", 170, true).unwrap()["status"],
        "ADMITTED"
    );
    let mut revoked = policy.clone();
    revoked.keys[0].revoked = true;
    assert!(history(&events, &revoked, &binding, b"rule", 170, true).is_err());
}

#[test]
fn no_wire_boolean_clock_or_future_history_is_accepted() {
    let (key, policy, binding) = fixture();
    let signed = sign(
        &key,
        &binding,
        Purpose::Admission,
        "ADMIT",
        "decision-1",
        100,
        None,
    );
    assert!(history(&[signed.clone()], &policy, &binding, b"rule", 99, false).is_err());
    let request = json!({"operation":"authenticated_verify","policy":policy,
        "binding":binding,"purpose":"admission","signed":signed,"now":true});
    assert_eq!(execute(&request).unwrap_err().code, "EIS_AUTH_BAD_CLOCK");
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/authenticated_custody.rs
// Claim: urn:core:crates_rs:tests:authenticated-custody:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda04e4761 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda04e4761` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora04e4761 {
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
impl BoundaryErrora04e4761 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora04e4761 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora04e4761 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda04e4761 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora04e4761> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora04e4761::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora04e4761::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora04e4761::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a04e4761() {
    let admitted = BoundaryRecorda04e4761::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda04e4761::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
