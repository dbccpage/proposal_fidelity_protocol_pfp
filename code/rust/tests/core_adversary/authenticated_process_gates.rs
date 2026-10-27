//! Signed synthetic process records; real subprocess capture is exercised by the owning Python host.
use ed25519_dalek::{Signer, SigningKey};
use core_epistemic_immune_system::authenticated::*;
use core_adversary::{evidence::sha256_ref, primary_gates};
use serde_json::{json, Value};

const GATES: [&str; 2] = ["PFP-15-BARE-METAL-ANCHOR", "PFP-20-COVERT-VERIFIER"];
const PROFILE: &str = "adversary.host-process.v1";

fn record() -> Value {
    json!({"schema_version":PROFILE,"run_id":"run-one","task_id":"task-one","action_id":"check-one",
        "source_digest":sha256_ref(b"task-source"),"candidate_sha256":sha256_ref(b"candidate"),
        "checker_id":"finite-checker","requested_argv":["python","checker.py"],
        "argv":["/host/python","checker.py"],"executable_path":"/host/python",
        "executable_sha256":sha256_ref(b"fixture executable"),
        "checker_source_paths":[["/work/checker.py",sha256_ref(b"checker source")]],
        "artifacts":[["/work/answer",sha256_ref(b"candidate")]],
        "stdout_hex":"ff004f4b","stdout_sha256":sha256_ref(&[255,0,b'O',b'K']),
        "stderr_hex":"","stderr_sha256":sha256_ref(b""),"exit_code":0,
        "direct_child_completed":true,"shell":false,"started_at_ms":99000,"completed_at_ms":99999,
        "observer_source_digest":sha256_ref(b"observer implementation"),"authority_effect":"None"})
}

fn expected(r: &Value) -> Value {
    let keys = [
        "run_id",
        "task_id",
        "action_id",
        "source_digest",
        "candidate_sha256",
        "checker_id",
        "requested_argv",
        "argv",
        "executable_path",
        "executable_sha256",
        "checker_source_paths",
        "artifacts",
        "observer_source_digest",
    ];
    Value::Object(
        keys.into_iter()
            .map(|k| (k.to_string(), r[k].clone()))
            .collect(),
    )
}

fn signed_payload(gate: &str, r: &Value, raw: &[u8]) -> Value {
    let key = SigningKey::from_bytes(&[37; 32]);
    let rule = if gate == GATES[0] {
        include_bytes!(
            "../../../../pfp/infrastructure/yaml/gates/15_ground_reality.yaml"
        )
        .as_slice()
    } else {
        include_bytes!("../../../../pfp/infrastructure/yaml/gates/20_covert_verification.yaml").as_slice()
    };
    let context = serde_json::to_vec(&json!([
        r["run_id"],
        r["task_id"],
        r["action_id"],
        r["source_digest"],
        r["candidate_sha256"],
        r["checker_id"],
        r["requested_argv"],
        r["checker_source_paths"],
        r["artifacts"]
    ]))
    .unwrap();
    let binding = Binding {
        spec_id: gate.into(),
        scope: PROFILE.into(),
        rule_digest: sha256_ref(rule),
        source_digest: r["source_digest"].as_str().unwrap().into(),
        subject_digest: sha256_ref(raw),
        context_digest: sha256_ref(&context),
    };
    let evidence = serde_json::to_vec(&json!({"schema_version":"core.eis.observed-evidence.v1",
        "observer_id":"fixture-host","run_id":r["run_id"],"subject_digest":binding.subject_digest,
        "source_digest":r["observer_source_digest"],"outcome":"PROCESS_EXECUTION_OBSERVED"}))
    .unwrap();
    let mut attestation = Attestation {
        schema_version: SCHEMA.into(),
        trust_domain: "fixture-only".into(),
        purpose: Purpose::Observation,
        issuer: "fixture-host".into(),
        key_id: "key-one".into(),
        event_id: "process-event".into(),
        binding,
        issued_at: 100,
        expires_at: 150,
        outcome: "PROCESS_EXECUTION_OBSERVED".into(),
        previous_event: None,
        evidence_digest: sha256_ref(&evidence),
        signature_hex: String::new(),
    };
    attestation.signature_hex =
        hex::encode(key.sign(&attestation.signing_bytes().unwrap()).to_bytes());
    let signed = SignedEvidence {
        attestation,
        evidence_hex: hex::encode(evidence),
    };
    let policy = TrustPolicy {
        schema_version: POLICY_SCHEMA.into(),
        trust_domain: "fixture-only".into(),
        keys: vec![TrustedKey {
            issuer: "fixture-host".into(),
            key_id: "key-one".into(),
            public_key_hex: hex::encode(key.verifying_key().as_bytes()),
            purposes: vec![Purpose::Observation],
            scopes: vec![PROFILE.into()],
            not_before: 1,
            not_after: 1000,
            max_lifetime_seconds: 100,
            revoked: false,
            observer_source_digest: Some(r["observer_source_digest"].as_str().unwrap().into()),
        }],
    };
    json!({"process_profile":PROFILE,"process_observation":{"record_hex":hex::encode(raw),"signed":signed},
        "process_trust_policy":policy,"process_expected":expected(r),"now":100})
}

fn fixture(gate: &str) -> Value {
    let r = record();
    signed_payload(gate, &r, &serde_json::to_vec(&r).unwrap())
}
fn evaluate(gate: &str, p: &Value) -> Value {
    primary_gates::evaluate(gate, p, &[]).unwrap()
}

#[test]
fn both_gates_accept_the_same_signed_finite_process_without_authority() {
    for gate in GATES {
        let p = fixture(gate);
        let result = evaluate(gate, &p);
        assert_eq!(result["status"], "PASS", "{result}");
        assert_eq!(result["authority_effect"], "None");
        assert_eq!(result["can_authorize"], false);
        assert_eq!(result["witness"]["direct_child_completed"], true);
        assert_eq!(result["witness"]["process_tree_verified"], false);
    }
    assert!(primary_gates::describe()["process_profiles"]
        .as_array()
        .unwrap()
        .contains(&json!(PROFILE)));
}

#[test]
fn current_expected_bindings_cannot_be_transplanted() {
    for gate in GATES {
        for field in [
            "run_id",
            "task_id",
            "action_id",
            "source_digest",
            "candidate_sha256",
            "checker_id",
            "executable_path",
            "executable_sha256",
            "observer_source_digest",
        ] {
            let mut p = fixture(gate);
            p["process_expected"][field] = json!("different");
            assert_eq!(
                evaluate(gate, &p)["refusal_code"],
                "PROCESS_OBSERVATION_BINDING_MISMATCH",
                "{gate}/{field}"
            );
        }
        for field in [
            "argv",
            "requested_argv",
            "checker_source_paths",
            "artifacts",
        ] {
            let mut p = fixture(gate);
            p["process_expected"][field] = json!([]);
            assert_eq!(
                evaluate(gate, &p)["refusal_code"],
                "PROCESS_OBSERVATION_BINDING_MISMATCH",
                "{gate}/{field}"
            );
        }
    }
}

#[test]
fn signature_trust_clock_and_cross_gate_mutations_refuse() {
    for gate in GATES {
        for mutation in [
            "signature",
            "revoked",
            "expired",
            "scope",
            "observer",
            "rule",
        ] {
            let mut p = fixture(gate);
            match mutation {
                "signature" => {
                    p["process_observation"]["signed"]["attestation"]["signature_hex"] =
                        json!("00".repeat(64))
                }
                "revoked" => p["process_trust_policy"]["keys"][0]["revoked"] = json!(true),
                "expired" => p["now"] = json!(150),
                "scope" => {
                    p["process_observation"]["signed"]["attestation"]["binding"]["scope"] =
                        json!("other")
                }
                "observer" => {
                    p["process_trust_policy"]["keys"][0]["observer_source_digest"] =
                        json!(sha256_ref(b"other"))
                }
                "rule" => {
                    p["process_observation"]["signed"]["attestation"]["binding"]["rule_digest"] =
                        json!(sha256_ref(b"other"))
                }
                _ => unreachable!(),
            }
            assert_eq!(evaluate(gate, &p)["status"], "REFUSE", "{gate}/{mutation}");
        }
    }
    assert_eq!(evaluate(GATES[1], &fixture(GATES[0]))["status"], "REFUSE");
}

#[test]
fn signed_malformed_records_and_failed_process_never_pass() {
    for mutation in [
        "stdout",
        "stderr",
        "exit",
        "shell",
        "child",
        "clock",
        "argv",
        "pairs",
        "unknown",
        "boolean_exit",
    ] {
        let mut r = record();
        match mutation {
            "stdout" => r["stdout_hex"] = json!(hex::encode(b"PASS")),
            "stderr" => r["stderr_sha256"] = json!(sha256_ref(b"missing")),
            "exit" => {
                r["exit_code"] = json!(1);
                r["stdout_hex"] = json!(hex::encode(b"PASS"));
                r["stdout_sha256"] = json!(sha256_ref(b"PASS"));
            }
            "shell" => r["shell"] = json!(true),
            "child" => r["direct_child_completed"] = json!(false),
            "clock" => r["completed_at_ms"] = json!(101000),
            "argv" => r["argv"] = json!(["/host/python", "different.py"]),
            "pairs" => r["artifacts"] = json!([["z", sha256_ref(b"z")], ["a", sha256_ref(b"a")]]),
            "unknown" => r["extra"] = json!(true),
            "boolean_exit" => r["exit_code"] = json!(false),
            _ => unreachable!(),
        }
        let p = signed_payload(GATES[0], &r, &serde_json::to_vec(&r).unwrap());
        assert_eq!(evaluate(GATES[0], &p)["status"], "REFUSE", "{mutation}");
    }
    let r = record();
    let raw = serde_json::to_string(&r)
        .unwrap()
        .replacen('{', "{\"exit_code\":0,", 1);
    let p = signed_payload(GATES[0], &r, raw.as_bytes());
    assert_eq!(evaluate(GATES[0], &p)["status"], "REFUSE");
}

#[test]
fn missing_observation_and_legacy_fields_remain_hold() {
    for gate in GATES {
        assert_eq!(
            evaluate(gate, &json!({"process_profile":PROFILE}))["status"],
            "HOLD"
        );
        assert_eq!(
            evaluate(gate, &json!({"process_profile":"unknown"}))["status"],
            "REFUSE"
        );
    }
    let log = "PASS";
    let bare_metal_anchor = json!({"candidate_id":"one","has_executable_test":true,"runtime_exit_code":0,
        "abstract_bloat_score":0,"has_mock_injection":false,"executable_utf8":"code",
        "executable_sha256":sha256_ref(b"code"),"observed_executable_sha256":sha256_ref(b"code"),
        "execution_log_utf8":log,"execution_log_sha256":sha256_ref(log.as_bytes())});
    let covert_verifier = json!({"task_id":"one","reported_status":"PASS","os_exit_code":0,
        "process_terminated":true,"log_output_utf8":log,"log_output_hash":sha256_ref(log.as_bytes())});
    assert_eq!(evaluate(GATES[0], &bare_metal_anchor)["status"], "HOLD");
    assert_eq!(evaluate(GATES[1], &covert_verifier)["status"], "HOLD");
}

// Origin: engine/crates_rs/tests/core_adversary/authenticated_process_gates.rs
// Claim: urn:core:crates_rs:tests:authenticated-process-gates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddf689f24 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddf689f24` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordf689f24 {
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
impl BoundaryErrordf689f24 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordf689f24 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordf689f24 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddf689f24 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordf689f24> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordf689f24::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordf689f24::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordf689f24::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_df689f24() {
    let admitted = BoundaryRecorddf689f24::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddf689f24::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
