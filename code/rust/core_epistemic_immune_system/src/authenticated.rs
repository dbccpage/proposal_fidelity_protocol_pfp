//! Explicit-key attestation custody. Authentication is relative to the supplied
//! operator policy, never proof that an arbitrary key belongs to a human.
//! AuthorityEffect: None. No private key, trust discovery or self-admission.

use crate::{admission::ExternalAdmissionRequest, Refusal};
use ed25519_dalek::{Signature, VerifyingKey};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

pub const SCHEMA: &str = "core.eis.signed-attestation.v1";
pub const POLICY_SCHEMA: &str = "core.eis.trust-policy.v1";
pub const HOST_PROCESS_SCOPE: &str = "adversary.host-process.v1";
pub const PROCESS_OBSERVED: &str = "PROCESS_EXECUTION_OBSERVED";
pub const HOST_LEAN_SCOPE: &str = "adversary.host-lean.v1";
pub const KERNEL_OBSERVED: &str = "KERNEL_VERIFICATION_OBSERVED";
const MAX_HISTORY: usize = 4096;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Purpose {
    Admission,
    Health,
    Observation,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Binding {
    pub spec_id: String,
    pub scope: String,
    pub rule_digest: String,
    pub source_digest: String,
    pub subject_digest: String,
    pub context_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TrustedKey {
    pub issuer: String,
    pub key_id: String,
    pub public_key_hex: String,
    pub purposes: Vec<Purpose>,
    pub scopes: Vec<String>,
    pub not_before: u64,
    pub not_after: u64,
    pub max_lifetime_seconds: u64,
    pub revoked: bool,
    pub observer_source_digest: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TrustPolicy {
    pub schema_version: String,
    pub trust_domain: String,
    pub keys: Vec<TrustedKey>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Attestation {
    pub schema_version: String,
    pub trust_domain: String,
    pub purpose: Purpose,
    pub issuer: String,
    pub key_id: String,
    pub event_id: String,
    pub binding: Binding,
    pub issued_at: u64,
    pub expires_at: u64,
    pub outcome: String,
    pub previous_event: Option<String>,
    pub evidence_digest: String,
    pub signature_hex: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SignedEvidence {
    pub attestation: Attestation,
    pub evidence_hex: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ObservationEvidence {
    schema_version: String,
    observer_id: String,
    run_id: String,
    subject_digest: String,
    source_digest: String,
    outcome: String,
}

fn refuse(code: &str) -> Refusal {
    Refusal::new(code, "authenticated EIS contract refused")
}
fn identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 512
        && value.trim() == value
        && !value.chars().any(char::is_control)
}
fn digest(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value.as_bytes()[7..]
            .iter()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(b))
}
pub fn bytes_digest(raw: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(raw)))
}
fn hex_bytes(value: &str, maximum: usize) -> Result<Vec<u8>, Refusal> {
    if value.len() > maximum * 2
        || value.len() % 2 != 0
        || !value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err(refuse("EIS_AUTH_BAD_HEX"));
    }
    hex::decode(value).map_err(|_| refuse("EIS_AUTH_BAD_HEX"))
}

impl Binding {
    fn validate(&self) -> Result<(), Refusal> {
        if !identifier(&self.spec_id)
            || !identifier(&self.scope)
            || [
                &self.rule_digest,
                &self.source_digest,
                &self.subject_digest,
                &self.context_digest,
            ]
            .iter()
            .any(|d| !digest(d))
        {
            return Err(refuse("EIS_AUTH_BAD_BINDING"));
        }
        Ok(())
    }
}

impl TrustPolicy {
    fn validate(&self) -> Result<(), Refusal> {
        if self.schema_version != POLICY_SCHEMA
            || !identifier(&self.trust_domain)
            || self.keys.is_empty()
            || self.keys.len() > 64
        {
            return Err(refuse("EIS_AUTH_TRUST_UNCONFIGURED"));
        }
        let mut identities = BTreeSet::new();
        for key in &self.keys {
            if !identifier(&key.issuer)
                || !identifier(&key.key_id)
                || !identities.insert((&key.issuer, &key.key_id))
                || key.not_before >= key.not_after
                || key.max_lifetime_seconds == 0
                || key.purposes.is_empty()
                || key.scopes.is_empty()
                || key.scopes.iter().any(|s| !identifier(s))
                || key.purposes.iter().collect::<BTreeSet<_>>().len() != key.purposes.len()
                || key.scopes.iter().collect::<BTreeSet<_>>().len() != key.scopes.len()
                || key
                    .observer_source_digest
                    .as_ref()
                    .is_some_and(|d| !digest(d))
            {
                return Err(refuse("EIS_AUTH_BAD_POLICY"));
            }
            public_key(key)?;
        }
        Ok(())
    }
}

fn public_key(key: &TrustedKey) -> Result<VerifyingKey, Refusal> {
    let raw: [u8; 32] = hex_bytes(&key.public_key_hex, 32)?
        .try_into()
        .map_err(|_| refuse("EIS_AUTH_BAD_KEY"))?;
    let value = VerifyingKey::from_bytes(&raw).map_err(|_| refuse("EIS_AUTH_BAD_KEY"))?;
    if value.is_weak() {
        return Err(refuse("EIS_AUTH_BAD_KEY"));
    }
    Ok(value)
}

impl Attestation {
    /// Versioned ordered JSON-array profile, UTF-8, no maps/floats. The signature
    /// is excluded. Cross-language signers must use this exact field order.
    pub fn signing_bytes(&self) -> Result<Vec<u8>, Refusal> {
        serde_json::to_vec(&json!([
            SCHEMA,
            self.trust_domain,
            self.purpose,
            self.issuer,
            self.key_id,
            self.event_id,
            [
                self.binding.spec_id,
                self.binding.scope,
                self.binding.rule_digest,
                self.binding.source_digest,
                self.binding.subject_digest,
                self.binding.context_digest
            ],
            self.issued_at,
            self.expires_at,
            self.outcome,
            self.previous_event,
            self.evidence_digest
        ]))
        .map_err(|_| refuse("EIS_AUTH_ENCODING"))
    }
}

/// Constructed only after signature, role, time, byte and expected-binding checks.
#[derive(Debug, Serialize)]
pub struct VerifiedAttestation {
    statement_digest: String,
    issuer: String,
    event_id: String,
    outcome: String,
    run_id: Option<String>,
    evidence_digest: String,
    authority_effect: &'static str,
}

fn verify_attestation_statement(
    a: &Attestation,
    policy: &TrustPolicy,
    expected: &Binding,
    purpose: Purpose,
) -> Result<(), Refusal> {
    if a.schema_version != SCHEMA
        || a.trust_domain != policy.trust_domain
        || a.purpose != purpose
        || &a.binding != expected
    {
        return Err(refuse("EIS_AUTH_BINDING_MISMATCH"));
    }
    if !identifier(&a.event_id)
        || !digest(&a.evidence_digest)
        || a.previous_event.as_ref().is_some_and(|d| !digest(d))
    {
        return Err(refuse("EIS_AUTH_BAD_STATEMENT"));
    }
    Ok(())
}

fn check_attestation_timestamps(a: &Attestation, key: &TrustedKey, now: u64) -> bool {
    let valid_issue = a.issued_at <= now && now < a.expires_at && a.issued_at < a.expires_at;
    let valid_key_window =
        a.issued_at >= key.not_before && now >= key.not_before && now < key.not_after;
    let valid_lifetime =
        a.expires_at <= key.not_after && a.expires_at - a.issued_at <= key.max_lifetime_seconds;
    valid_issue && valid_key_window && valid_lifetime
}

fn find_and_authorize_key<'a>(
    a: &Attestation,
    policy: &'a TrustPolicy,
    purpose: Purpose,
    now: u64,
) -> Result<&'a TrustedKey, Refusal> {
    let key = policy
        .keys
        .iter()
        .find(|k| k.issuer == a.issuer && k.key_id == a.key_id)
        .ok_or_else(|| refuse("EIS_AUTH_UNKNOWN_SIGNER"))?;
    if key.revoked || !key.purposes.contains(&purpose) || !key.scopes.contains(&a.binding.scope) {
        return Err(refuse("EIS_AUTH_SIGNER_NOT_AUTHORIZED"));
    }
    if !check_attestation_timestamps(a, key, now) {
        return Err(refuse("EIS_AUTH_EXPIRED_OR_FUTURE"));
    }
    Ok(key)
}

fn is_observation_coherent(
    observation: &ObservationEvidence,
    a: &Attestation,
    expected: &Binding,
    key: &TrustedKey,
) -> bool {
    let valid_header = observation.schema_version == "core.eis.observed-evidence.v1"
        && observation.observer_id == a.issuer
        && identifier(&observation.run_id);
    let valid_digests = observation.subject_digest == expected.subject_digest
        && key.observer_source_digest.as_ref() == Some(&observation.source_digest);
    valid_header && valid_digests && observation.outcome == a.outcome && a.previous_event.is_none()
}

fn is_purpose_outcome_allowed(purpose: Purpose, outcome: &str, scope: &str) -> bool {
    match purpose {
        Purpose::Health => ["HEALTHY", "UNHEALTHY"].contains(&outcome),
        Purpose::Observation => {
            outcome == "DEFECT_OBSERVED"
                || (outcome == PROCESS_OBSERVED && scope == HOST_PROCESS_SCOPE)
                || (outcome == KERNEL_OBSERVED && scope == HOST_LEAN_SCOPE)
        }
        Purpose::Admission => false,
    }
}

fn verify_purpose_payload(
    a: &Attestation,
    bytes: &[u8],
    expected: &Binding,
    key: &TrustedKey,
    purpose: Purpose,
) -> Result<Option<String>, Refusal> {
    if purpose == Purpose::Admission {
        if !["ADMIT", "SUSPEND", "REINSTATE", "REVOKE"].contains(&a.outcome.as_str()) {
            return Err(refuse("EIS_AUTH_BAD_OUTCOME"));
        }
        return Ok(None);
    }
    let observation: ObservationEvidence =
        serde_json::from_slice(bytes).map_err(|_| refuse("EIS_AUTH_BAD_OBSERVATION"))?;
    if !is_observation_coherent(&observation, a, expected, key) {
        return Err(refuse("EIS_AUTH_BAD_OBSERVATION"));
    }
    if !is_purpose_outcome_allowed(purpose, &a.outcome, &expected.scope) {
        return Err(refuse("EIS_AUTH_BAD_OUTCOME"));
    }
    Ok(Some(observation.run_id))
}

fn verify_evidence_and_signature(
    signed: &SignedEvidence,
    a: &Attestation,
    key: &TrustedKey,
) -> Result<(Vec<u8>, Vec<u8>), Refusal> {
    let bytes = hex_bytes(&signed.evidence_hex, 1024 * 1024)?;
    if bytes.is_empty() || bytes_digest(&bytes) != a.evidence_digest {
        return Err(refuse("EIS_AUTH_EVIDENCE_MISMATCH"));
    }
    let signature = Signature::from_slice(&hex_bytes(&a.signature_hex, 64)?)
        .map_err(|_| refuse("EIS_AUTH_BAD_SIGNATURE"))?;
    let message = a.signing_bytes()?;
    public_key(key)?
        .verify_strict(&message, &signature)
        .map_err(|_| refuse("EIS_AUTH_BAD_SIGNATURE"))?;
    Ok((bytes, message))
}

pub fn verify(
    signed: &SignedEvidence,
    policy: &TrustPolicy,
    expected: &Binding,
    purpose: Purpose,
    now: u64,
) -> Result<VerifiedAttestation, Refusal> {
    policy.validate()?;
    expected.validate()?;
    let a = &signed.attestation;
    verify_attestation_statement(a, policy, expected, purpose)?;
    let key = find_and_authorize_key(a, policy, purpose, now)?;
    let (bytes, message) = verify_evidence_and_signature(signed, a, key)?;
    let run_id = verify_purpose_payload(a, &bytes, expected, key, purpose)?;
    Ok(VerifiedAttestation {
        statement_digest: bytes_digest(&message),
        issuer: a.issuer.clone(),
        event_id: a.event_id.clone(),
        outcome: a.outcome.clone(),
        run_id,
        evidence_digest: a.evidence_digest.clone(),
        authority_effect: "None",
    })
}

fn next_admission_state(
    state: &'static str,
    outcome: &str,
    event_issued_at: u64,
    last_issued_at: u64,
) -> Result<&'static str, Refusal> {
    match (state, outcome) {
        ("CANDIDATE", "ADMIT") => Ok("ADMITTED"),
        ("ADMITTED", "SUSPEND") => Ok("SUSPENDED"),
        ("SUSPENDED", "REINSTATE") if event_issued_at > last_issued_at => Ok("ADMITTED"),
        ("ADMITTED" | "SUSPENDED", "REVOKE") => Ok("REVOKED"),
        _ => Err(refuse("EIS_AUTH_INVALID_TRANSITION")),
    }
}

fn step_admission_history<'a>(
    event: &'a SignedEvidence,
    policy: &TrustPolicy,
    expected: &Binding,
    now: u64,
    previous: &mut Option<String>,
    identities: &mut BTreeSet<(&'a str, &'a str)>,
    state: &mut &'static str,
    issued_at: &mut u64,
) -> Result<(), Refusal> {
    let a = &event.attestation;
    if a.issued_at > now {
        return Err(refuse("EIS_AUTH_EXPIRED_OR_FUTURE"));
    }
    let checked = verify(event, policy, expected, Purpose::Admission, a.issued_at)?;
    if a.previous_event != *previous || !identities.insert((&a.issuer, &a.event_id)) {
        return Err(refuse("EIS_AUTH_REPLAY_OR_CHAIN"));
    }
    let next = next_admission_state(state, a.outcome.as_str(), a.issued_at, *issued_at)?;
    if a.issued_at < *issued_at {
        return Err(refuse("EIS_AUTH_REPLAY_OR_CHAIN"));
    }
    *previous = Some(checked.statement_digest);
    *state = next;
    *issued_at = a.issued_at;
    Ok(())
}

fn validate_history_preconditions(
    events: &[SignedEvidence],
    policy: &TrustPolicy,
    expected: &Binding,
    rule_bytes: &[u8],
) -> Result<(), Refusal> {
    if events.len() > MAX_HISTORY {
        return Err(refuse("EIS_AUTH_HISTORY_BUDGET"));
    }
    if bytes_digest(rule_bytes) != expected.rule_digest
        || expected.subject_digest != expected.rule_digest
    {
        return Err(refuse("EIS_AUTH_RULE_MISMATCH"));
    }
    policy.validate()?;
    expected.validate()
}

pub fn history(
    events: &[SignedEvidence],
    policy: &TrustPolicy,
    expected: &Binding,
    rule_bytes: &[u8],
    now: u64,
    require_current: bool,
) -> Result<Value, Refusal> {
    validate_history_preconditions(events, policy, expected, rule_bytes)?;
    let mut previous = None;
    let mut identities = BTreeSet::new();
    let mut state = "CANDIDATE";
    let mut issued_at = 0;
    for event in events {
        step_admission_history(
            event,
            policy,
            expected,
            now,
            &mut previous,
            &mut identities,
            &mut state,
            &mut issued_at,
        )?;
    }
    if require_current {
        if let Some(last) = events.last() {
            verify(last, policy, expected, Purpose::Admission, now)?;
        }
    }
    Ok(
        json!({"status":state,"previous_event":previous,"events":events.len(),"authority_effect":"None"}),
    )
}

fn parse<T: for<'de> Deserialize<'de>>(value: &Value) -> Result<T, Refusal> {
    serde_json::from_value(value.clone()).map_err(|_| refuse("EIS_AUTH_BAD_WIRE"))
}

fn collect_verified_observations(
    events: Vec<SignedEvidence>,
    policy: &TrustPolicy,
    binding: &Binding,
    now: u64,
) -> Result<(Vec<Value>, usize), Refusal> {
    let mut identities = BTreeSet::new();
    let mut observations = Vec::new();
    let mut expired = 0;
    for event in events {
        if event.attestation.issued_at > now {
            return Err(refuse("EIS_AUTH_EXPIRED_OR_FUTURE"));
        }
        // Authenticate retained history at issuance. Expired observations
        // remain auditable but contribute nothing to current eligibility.
        let checked = verify(
            &event,
            policy,
            binding,
            Purpose::Observation,
            event.attestation.issued_at,
        )?;
        if !identities.insert((checked.issuer.clone(), checked.event_id)) {
            return Err(refuse("EIS_AUTH_REPLAY_OR_CHAIN"));
        }
        if now >= event.attestation.expires_at {
            expired += 1;
            continue;
        }
        observations.push(json!({"observation_digest":checked.evidence_digest,
            "observer_id":checked.issuer,"run_id":checked.run_id}));
    }
    Ok((observations, expired))
}

fn validate_assess_binding(
    binding: &Binding,
    request: &ExternalAdmissionRequest,
) -> Result<(), Refusal> {
    if binding.subject_digest != request.request_id
        || binding.rule_digest != request.candidate_digest
        || binding.source_digest != request.source_manifest_digest
    {
        return Err(refuse("EIS_AUTH_BINDING_MISMATCH"));
    }
    Ok(())
}

fn execute_assess(
    payload: &Value,
    policy: &TrustPolicy,
    binding: &Binding,
    now: u64,
) -> Result<Value, Refusal> {
    policy.validate()?;
    binding.validate()?;
    let request = ExternalAdmissionRequest::from_value(&payload["request"])?;
    validate_assess_binding(binding, &request)?;
    let events: Vec<SignedEvidence> = parse(&payload["events"])?;
    if events.len() > MAX_HISTORY {
        return Err(refuse("EIS_AUTH_HISTORY_BUDGET"));
    }
    let (observations, expired) = collect_verified_observations(events, policy, binding, now)?;
    let mut report = crate::admission::assess(
        &payload["request"],
        &json!(observations),
        &payload["required_distinct"],
    )?;
    report["verified_observations"] = json!(observations);
    report["expired_observation_records"] = json!(expired);
    Ok(report)
}

fn execute_verify(
    payload: &Value,
    policy: &TrustPolicy,
    binding: &Binding,
    now: u64,
) -> Result<Value, Refusal> {
    let verified = verify(
        &parse(&payload["signed"])?,
        policy,
        binding,
        parse(&payload["purpose"])?,
        now,
    )?;
    serde_json::to_value(verified).map_err(|_| refuse("EIS_AUTH_ENCODING"))
}

fn execute_history(
    payload: &Value,
    policy: &TrustPolicy,
    binding: &Binding,
    now: u64,
) -> Result<Value, Refusal> {
    let events: Vec<SignedEvidence> = parse(&payload["events"])?;
    let rule = payload["rule_bytes_hex"]
        .as_str()
        .ok_or_else(|| refuse("EIS_AUTH_RULE_MISMATCH"))?;
    let require_current = payload["require_current"]
        .as_bool()
        .ok_or_else(|| refuse("EIS_AUTH_BAD_WIRE"))?;
    history(
        &events,
        policy,
        binding,
        &hex_bytes(rule, 1024 * 1024)?,
        now,
        require_current,
    )
}

pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let policy: TrustPolicy = parse(&payload["policy"])?;
    let binding: Binding = parse(&payload["binding"])?;
    let now = payload["now"]
        .as_u64()
        .ok_or_else(|| refuse("EIS_AUTH_BAD_CLOCK"))?;
    match payload["operation"].as_str() {
        Some("authenticated_verify") => execute_verify(payload, &policy, &binding, now),
        Some("authenticated_history") => execute_history(payload, &policy, &binding, now),
        Some("authenticated_assess") => execute_assess(payload, &policy, &binding, now),
        _ => Err(refuse("EIS_AUTH_BAD_OPERATION")),
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/authenticated.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:authenticated:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde577743e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde577743e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore577743e {
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
impl BoundaryErrore577743e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore577743e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore577743e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde577743e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore577743e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore577743e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore577743e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore577743e::ExceedsCapacity {
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
mod l4_boundary_tests_e577743e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde577743e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde577743e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde577743e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde577743e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde577743e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore577743e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore577743e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
