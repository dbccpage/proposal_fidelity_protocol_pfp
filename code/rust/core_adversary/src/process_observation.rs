//! Finite owning-host process observations authenticated relative to configured EIS trust.
//! This verifies signed bytes and bindings, not process-tree safety or an OS sandbox.
use super::{err, hold, Fields, GateResult, Spec};
use crate::evidence::{is_sha256_ref, sha256_ref};
use core_epistemic_immune_system::authenticated::{
    self, Binding, Purpose, SignedEvidence, TrustPolicy,
};
use serde::Deserialize;
use serde_json::{json, Value};

pub const PROFILE: &str = authenticated::HOST_PROCESS_SCOPE;
const MAX_BYTES: usize = 64 * 1024;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Record {
    schema_version: String,
    run_id: String,
    task_id: String,
    action_id: String,
    source_digest: String,
    candidate_sha256: String,
    checker_id: String,
    requested_argv: Vec<String>,
    argv: Vec<String>,
    executable_path: String,
    executable_sha256: String,
    checker_source_paths: Vec<(String, String)>,
    artifacts: Vec<(String, String)>,
    stdout_hex: String,
    stdout_sha256: String,
    stderr_hex: String,
    stderr_sha256: String,
    exit_code: i64,
    direct_child_completed: bool,
    shell: bool,
    started_at_ms: u64,
    completed_at_ms: u64,
    observer_source_digest: String,
    authority_effect: String,
}

#[derive(Debug, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
struct Expected {
    run_id: String,
    task_id: String,
    action_id: String,
    source_digest: String,
    candidate_sha256: String,
    checker_id: String,
    requested_argv: Vec<String>,
    argv: Vec<String>,
    executable_path: String,
    executable_sha256: String,
    checker_source_paths: Vec<(String, String)>,
    artifacts: Vec<(String, String)>,
    observer_source_digest: String,
}

impl Record {
    fn expected(&self) -> Expected {
        Expected {
            run_id: self.run_id.clone(),
            task_id: self.task_id.clone(),
            action_id: self.action_id.clone(),
            source_digest: self.source_digest.clone(),
            candidate_sha256: self.candidate_sha256.clone(),
            checker_id: self.checker_id.clone(),
            requested_argv: self.requested_argv.clone(),
            argv: self.argv.clone(),
            executable_path: self.executable_path.clone(),
            executable_sha256: self.executable_sha256.clone(),
            checker_source_paths: self.checker_source_paths.clone(),
            artifacts: self.artifacts.clone(),
            observer_source_digest: self.observer_source_digest.clone(),
        }
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Envelope {
    record_hex: String,
    signed: SignedEvidence,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Observation {
    schema_version: String,
    observer_id: String,
    run_id: String,
    subject_digest: String,
    source_digest: String,
    outcome: String,
}

fn invalid(message: &str) -> crate::stage::ports::Refusal {
    err("PROCESS_OBSERVATION_INVALID", message)
}
fn bytes(value: &str) -> Result<Vec<u8>, crate::stage::ports::Refusal> {
    if value.len() > MAX_BYTES * 2
        || value.len() % 2 != 0
        || !value
            .bytes()
            .all(|v| v.is_ascii_digit() || (b'a'..=b'f').contains(&v))
    {
        return Err(invalid("Require bounded lowercase hexadecimal bytes"));
    }
    hex::decode(value).map_err(|_| invalid("Malformed hexadecimal bytes"))
}
fn identifier(value: &str) -> bool {
    !value.trim().is_empty() && value.len() <= 4096 && !value.chars().any(char::is_control)
}
fn pairs(values: &[(String, String)]) -> bool {
    values
        .iter()
        .all(|(p, h)| identifier(p) && is_sha256_ref(&Value::String(h.clone())))
        && values.windows(2).all(|w| w[0].0 < w[1].0)
}

pub(super) fn evaluate(spec: &Spec, p: &Fields) -> GateResult {
    if p.get("process_profile").and_then(Value::as_str) != Some(PROFILE) {
        return Err(err(
            "PROCESS_PROFILE_UNSUPPORTED",
            "Unknown owning-host process profile",
        ));
    }
    let envelope = p
        .get("process_observation")
        .filter(|v| !v.is_null())
        .ok_or_else(|| hold("authenticated owning-host process observation"))?;
    let envelope: Envelope = serde_json::from_value(envelope.clone())
        .map_err(|_| invalid("Require exact record_hex and signed EIS evidence"))?;
    let raw = bytes(&envelope.record_hex)?;
    let r: Record = serde_json::from_slice(&raw).map_err(|_| {
        invalid("Process record has duplicate, unknown, missing or ill-typed fields")
    })?;
    let expected: Expected =
        serde_json::from_value(p.get("process_expected").cloned().unwrap_or(Value::Null))
            .map_err(|_| invalid("Require host-selected exact current process bindings"))?;
    if r.expected() != expected {
        return Err(err(
            "PROCESS_OBSERVATION_BINDING_MISMATCH",
            "Observation differs from the current host-selected task/checker/candidate/command",
        ));
    }
    let now = p
        .get("now")
        .and_then(Value::as_u64)
        .ok_or_else(|| invalid("Require host UTC seconds"))?;
    if r.schema_version != PROFILE
        || r.authority_effect != "None"
        || ![
            &r.run_id,
            &r.task_id,
            &r.action_id,
            &r.checker_id,
            &r.executable_path,
        ]
        .into_iter()
        .all(|v| identifier(v))
        || ![
            &r.source_digest,
            &r.candidate_sha256,
            &r.executable_sha256,
            &r.observer_source_digest,
            &r.stdout_sha256,
            &r.stderr_sha256,
        ]
        .into_iter()
        .all(|v| is_sha256_ref(&Value::String(v.clone())))
        || !pairs(&r.checker_source_paths)
        || !pairs(&r.artifacts)
        || r.requested_argv.is_empty()
        || !identifier(&r.requested_argv[0])
        || r.argv.is_empty()
        || r.argv[0] != r.executable_path
        || r.argv[1..] != r.requested_argv[1..]
        || r.argv.iter().any(|v| v.contains('\0'))
        || r.requested_argv.iter().any(|v| v.contains('\0'))
        || r.shell
        || !r.direct_child_completed
        || r.started_at_ms > r.completed_at_ms
        || u128::from(r.completed_at_ms) > u128::from(now) * 1000 + 999
        || u128::from(r.completed_at_ms)
            > u128::from(envelope.signed.attestation.issued_at) * 1000 + 999
    {
        return Err(invalid(
            "Process record is not a completed, ordered, bound shell-free command observation",
        ));
    }
    if sha256_ref(&bytes(&r.stdout_hex)?) != r.stdout_sha256
        || sha256_ref(&bytes(&r.stderr_hex)?) != r.stderr_sha256
    {
        return Err(err(
            "PROCESS_OUTPUT_HASH_MISMATCH",
            "Exact captured stdout/stderr bytes do not match their digests",
        ));
    }
    let policy: TrustPolicy = serde_json::from_value(
        p.get("process_trust_policy")
            .cloned()
            .unwrap_or(Value::Null),
    )
    .map_err(|_| {
        err(
            "PROCESS_TRUST_UNCONFIGURED",
            "Require owning-host configured EIS trust policy",
        )
    })?;
    let context = serde_json::to_vec(&json!([
        r.run_id,
        r.task_id,
        r.action_id,
        r.source_digest,
        r.candidate_sha256,
        r.checker_id,
        r.requested_argv,
        r.checker_source_paths,
        r.artifacts
    ]))
    .map_err(|_| invalid("Process context cannot be encoded"))?;
    let binding = Binding {
        spec_id: spec.id.into(),
        scope: PROFILE.into(),
        rule_digest: sha256_ref(spec.bytes),
        source_digest: r.source_digest.clone(),
        subject_digest: sha256_ref(&raw),
        context_digest: sha256_ref(&context),
    };
    let observation: Observation =
        serde_json::from_slice(&bytes(&envelope.signed.evidence_hex)?)
            .map_err(|_| invalid("Require exact EIS observed-evidence fields"))?;
    if observation.schema_version != "core.eis.observed-evidence.v1"
        || observation.observer_id != envelope.signed.attestation.issuer
        || observation.run_id != r.run_id
        || observation.subject_digest != binding.subject_digest
        || observation.source_digest != r.observer_source_digest
        || observation.outcome != authenticated::PROCESS_OBSERVED
        || envelope.signed.attestation.outcome != authenticated::PROCESS_OBSERVED
    {
        return Err(err(
            "PROCESS_OBSERVATION_BINDING_MISMATCH",
            "Signed observer/run/record identity differs from this process record",
        ));
    }
    authenticated::verify(
        &envelope.signed,
        &policy,
        &binding,
        Purpose::Observation,
        now,
    )
    .map_err(|e| err(&e.code, e.message))?;
    if r.exit_code != 0 {
        return Err(err(
            "PROCESS_EXECUTION_FAILED",
            "The authenticated direct child returned a nonzero exit code",
        ));
    }
    Ok(
        json!({"process_profile":PROFILE,"run_id":r.run_id,"task_id":r.task_id,"action_id":r.action_id,
        "record_sha256":binding.subject_digest,"candidate_sha256":r.candidate_sha256,
        "checker_id":r.checker_id,"executable_sha256":r.executable_sha256,
        "stdout_sha256":r.stdout_sha256,"stderr_sha256":r.stderr_sha256,"exit_code":r.exit_code,
        "direct_child_completed":true,"process_tree_verified":false,"sandbox_verified":false,
        "scope":"configured owning host observed this exact waited command; no general program-safety or semantic-correctness proof"}),
    )
}

// Origin: engine/crates_rs/core_adversary/src/process_observation.rs
// Claim: urn:core:crates_rs:core-adversary:process-observation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd7ac1849 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd7ac1849` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord7ac1849 {
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
impl BoundaryErrord7ac1849 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord7ac1849 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord7ac1849 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd7ac1849 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord7ac1849> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord7ac1849::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord7ac1849::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord7ac1849::ExceedsCapacity {
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
mod l4_boundary_tests_d7ac1849 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd7ac1849::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd7ac1849::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd7ac1849::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd7ac1849::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd7ac1849::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrord7ac1849::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrord7ac1849::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
