//! Synthetic signed execution fixtures. The Python owner exercises actual Lake processes.
use ed25519_dalek::{Signer, SigningKey};
use core_epistemic_immune_system::authenticated::*;
use core_adversary::{evidence::sha256_ref, primary_gates};
use serde_json::{json, Value};

const GATE: &str = "PFP-07-MANUSCRIPT-TRUTH";
const PROFILE: &str = "adversary.host-lean.v1";
const SOURCE: &str = "theorem submitted : True := True.intro\n";
const HARNESS: &str = "-- Auto-generated Judge Verification Harness\nimport Discrete4DBianchiSpectralContraction\ntheorem judge_check_1 : True := submitted\n#print axioms judge_check_1\n";
const LAKEFILE: &str = "import Lake\nopen Lake DSL\n\npackage «Discrete4DBianchiSpectralContraction» where\n  version := v!\"0.1.0\"\n\nlean_lib «Discrete4DBianchiSpectralContraction» where\n  srcDir := \".\"\n";

fn process(label: &str, args: &[&str], output: &str, i: u64) -> Value {
    let argv: Vec<_> = std::iter::once("/host/lake")
        .chain(args.iter().copied())
        .collect();
    json!({"label":label,"argv":argv,"cwd":"/work/package","exit_code":0,
        "stdout_hex":hex::encode(output),"stdout_sha256":sha256_ref(output.as_bytes()),
        "stderr_hex":"","stderr_sha256":sha256_ref(b""),"started_at_ms":90000+i*1000,
        "completed_at_ms":90999+i*1000,"direct_child_completed":true,"shell":false})
}
fn context() -> Value {
    json!({"run_id":"run-one","task_id":"task-one","action_id":"kernel-check-one",
        "source_digest":sha256_ref(b"original task"),"candidate_sha256":sha256_ref(b"candidate prose"),
        "proof_artifact_path":"/work/submitted.lean","proof_artifact_sha256":sha256_ref(SOURCE.as_bytes()),
        "checker_id":"original-task-check","required_declarations":[["submitted","True"]],
        "axiom_policy":[],"toolchain_pin":"leanprover/lean4:v4.24.0",
        "lake_binary_path":"/host/lake","lake_binary_sha256":sha256_ref(b"synthetic lake binary")})
}
fn receipt() -> Value {
    json!({"schema_version":"core.adversary.lake-check.v2","authority_effect":"None",
        "run_key":"run-one","candidate_id":"kernel-check-one",
        "candidate_content_sha256":sha256_ref(SOURCE.as_bytes()),"candidate_content_hex":hex::encode(SOURCE),
        "lean_source_sha256":sha256_ref(SOURCE.as_bytes()),"lean_source_hex":hex::encode(SOURCE),
        "extraction_profile":"raw-lean-v1","objective_sha256":sha256_ref(b"original objective"),
        "checker_id":"lake_sandbox_adapter","toolchain_pin":"leanprover/lean4:v4.24.0",
        "lake_binary_path":"/host/lake","lake_binary_sha256":sha256_ref(b"synthetic lake binary"),
        "required_declarations":[["submitted","True"]],"axiom_policy":[],
        "package_manifest":[["Discrete4DBianchiSpectralContraction.lean",sha256_ref(SOURCE.as_bytes())],
            ["Verify.lean",sha256_ref(HARNESS.as_bytes())],["lakefile.lean",sha256_ref(LAKEFILE.as_bytes())],
            ["lean-toolchain",sha256_ref(b"leanprover/lean4:v4.24.0\n")]],
        "harness_source_hex":hex::encode(HARNESS),"harness_source_sha256":sha256_ref(HARNESS.as_bytes()),
        "processes":[process("toolchain",&["env","lean","--version"],"Lean (version 4.24.0, x86_64, Release)\n",0),
            process("build",&["build","+Discrete4DBianchiSpectralContraction:olean"],"Build completed.\n",1),
            process("elaborate",&["env","lean","Verify.lean"],"'judge_check_1' does not depend on any axioms\n",2)],
        "lean_receipt":{"status":"PASS","build_success":true,"harness_elaborated":true,
            "refusal_code":null,"axioms":[["judge_check_1",[]]]},"verdict":"ACCEPTED","reason":"Scoped observed elaboration"})
}
fn payload(c: Value, receipt: Value) -> Value {
    let record = json!({"schema_version":PROFILE,"context":c,"lake_receipt_hex":hex::encode(serde_json::to_vec(&receipt).unwrap()),
        "observer_source_digest":sha256_ref(b"observer source"),"authority_effect":"None"});
    signed_record(&record, &serde_json::to_vec(&record).unwrap())
}
fn signed_record(record: &Value, raw: &[u8]) -> Value {
    let key = SigningKey::from_bytes(&[43; 32]);
    let c = &record["context"];
    let context_bytes = serde_json::to_vec(&json!([
        c["run_id"],
        c["task_id"],
        c["action_id"],
        c["source_digest"],
        c["candidate_sha256"],
        c["proof_artifact_path"],
        c["proof_artifact_sha256"],
        c["checker_id"],
        c["required_declarations"],
        c["axiom_policy"],
        c["toolchain_pin"],
        c["lake_binary_path"],
        c["lake_binary_sha256"]
    ]))
    .unwrap();
    let binding = Binding {spec_id:GATE.into(),scope:PROFILE.into(),
        rule_digest:sha256_ref(include_bytes!("../../../../pfp/infrastructure/yaml/gates/07_manuscript_truth_manuscript_truth.yaml")),
        source_digest:c["source_digest"].as_str().unwrap().into(),subject_digest:sha256_ref(raw),context_digest:sha256_ref(&context_bytes)};
    let evidence = serde_json::to_vec(&json!({"schema_version":"core.eis.observed-evidence.v1",
        "observer_id":"fixture-host","run_id":c["run_id"],"subject_digest":binding.subject_digest,
        "source_digest":record["observer_source_digest"],"outcome":KERNEL_OBSERVED}))
    .unwrap();
    let mut a = Attestation {
        schema_version: SCHEMA.into(),
        trust_domain: "fixture-only".into(),
        purpose: Purpose::Observation,
        issuer: "fixture-host".into(),
        key_id: "key-one".into(),
        event_id: "kernel-event".into(),
        binding,
        issued_at: 100,
        expires_at: 150,
        outcome: KERNEL_OBSERVED.into(),
        previous_event: None,
        evidence_digest: sha256_ref(&evidence),
        signature_hex: String::new(),
    };
    a.signature_hex = hex::encode(key.sign(&a.signing_bytes().unwrap()).to_bytes());
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
            observer_source_digest: Some(record["observer_source_digest"].as_str().unwrap().into()),
        }],
    };
    json!({"kernel_profile":PROFILE,"kernel_observation":{"record_hex":hex::encode(raw),
        "signed":SignedEvidence{attestation:a,evidence_hex:hex::encode(evidence)}},"kernel_expected":c,"kernel_trust_policy":policy,"now":100})
}
fn evaluate(p: &Value) -> Value {
    primary_gates::evaluate(GATE, p, &[]).unwrap()
}

#[test]
fn signed_exact_required_statement_accepts_with_explicit_empty_axiom_policy() {
    let result = evaluate(&payload(context(), receipt()));
    assert_eq!(result["status"], "PASS", "{result}");
    assert_eq!(result["can_authorize"], false);
    assert_eq!(result["general_theorem_verified"], false);
    assert_eq!(
        result["witness"]["audit"]["axioms"]["judge_check_1"],
        json!([])
    );
    assert!(primary_gates::describe()["kernel_profiles"]
        .as_array()
        .unwrap()
        .contains(&json!(PROFILE)));
}

#[test]
fn different_current_task_candidate_claim_or_executable_refuses_transplant() {
    for field in [
        "run_id",
        "task_id",
        "action_id",
        "source_digest",
        "candidate_sha256",
        "proof_artifact_path",
        "proof_artifact_sha256",
        "checker_id",
        "toolchain_pin",
        "lake_binary_path",
        "lake_binary_sha256",
    ] {
        let mut p = payload(context(), receipt());
        p["kernel_expected"][field] = json!("other");
        assert_eq!(
            evaluate(&p)["refusal_code"],
            "KERNEL_OBSERVATION_BINDING_MISMATCH",
            "{field}"
        );
    }
    for (field, value) in [
        ("required_declarations", json!([["submitted", "False"]])),
        ("axiom_policy", json!(["propext"])),
    ] {
        let mut p = payload(context(), receipt());
        p["kernel_expected"][field] = value;
        assert_eq!(evaluate(&p)["status"], "REFUSE", "{field}");
    }
}

#[test]
fn forged_expired_revoked_or_wrong_scope_observation_refuses() {
    for mutation in ["signature", "expired", "revoked", "scope", "source", "rule"] {
        let mut p = payload(context(), receipt());
        match mutation {
            "signature" => {
                p["kernel_observation"]["signed"]["attestation"]["signature_hex"] =
                    json!("00".repeat(64))
            }
            "expired" => p["now"] = json!(150),
            "revoked" => p["kernel_trust_policy"]["keys"][0]["revoked"] = json!(true),
            "scope" => {
                p["kernel_observation"]["signed"]["attestation"]["binding"]["scope"] =
                    json!(HOST_PROCESS_SCOPE)
            }
            "source" => {
                p["kernel_trust_policy"]["keys"][0]["observer_source_digest"] =
                    json!(sha256_ref(b"other"))
            }
            "rule" => {
                p["kernel_observation"]["signed"]["attestation"]["binding"]["rule_digest"] =
                    json!(sha256_ref(b"other"))
            }
            _ => unreachable!(),
        }
        assert_eq!(evaluate(&p)["status"], "REFUSE", "{mutation}");
    }
}

fn apply_process_mutation(r: &mut Value, mutation: &str) {
    match mutation {
        "version" => {
            let s = "Lean (version 4.23.0, Release)\n";
            r["processes"][0]["stdout_hex"] = json!(hex::encode(s));
            r["processes"][0]["stdout_sha256"] = json!(sha256_ref(s.as_bytes()));
        }
        "clock" => r["processes"][2]["completed_at_ms"] = json!(101000),
        "missing_process" => {
            r["processes"].as_array_mut().unwrap().pop();
        }
        "missing_judge" | "axioms" => {
            let s = if mutation == "axioms" {
                "'judge_check_1' depends on axioms: [propext]\n"
            } else {
                "PASS\n"
            };
            r["processes"][2]["stdout_hex"] = json!(hex::encode(s));
            r["processes"][2]["stdout_sha256"] = json!(sha256_ref(s.as_bytes()));
        }
        "summary" => r["lean_receipt"]["axioms"] = json!([]),
        "unknown" => r["caller_proof"] = json!(true),
        _ => unreachable!(),
    }
}

fn apply_receipt_mutation(r: &mut Value, mutation: &str) {
    match mutation {
        "source" => r["lean_source_hex"] = json!(hex::encode("theorem substituted : True := True.intro\n")),
        "harness" => r["harness_source_hex"] = json!(hex::encode("#check True\n")),
        "manifest" => r["package_manifest"][0][1] = json!(sha256_ref(b"other")),
        "argv" => r["processes"][2]["argv"][3] = json!("Different.lean"),
        "cwd" => r["processes"][2]["cwd"] = json!("/work/other"),
        "exit" => r["processes"][1]["exit_code"] = json!(1),
        "stream" => r["processes"][2]["stdout_hex"] = json!(hex::encode("PASS")),
        other => apply_process_mutation(r, other),
    }
}

#[test]
fn signed_capture_mutations_cannot_substitute_pass_labels_for_kernel_evidence() {
    for mutation in [
        "source",
        "harness",
        "manifest",
        "argv",
        "cwd",
        "exit",
        "stream",
        "version",
        "clock",
        "missing_process",
        "missing_judge",
        "axioms",
        "summary",
        "unknown",
    ] {
        let mut r = receipt();
        apply_receipt_mutation(&mut r, mutation);
        let result = evaluate(&payload(context(), r));
        assert_eq!(result["status"], "REFUSE", "{mutation}: {result}");
    }
}

#[test]
fn fenced_source_preserves_exact_body_and_rejects_ambiguous_fences() {
    for prefix in [
        "-- Inline ``` is valid comment text.\n",
        "def ticks : String := \"```\"\n",
    ] {
        let raw = format!("{prefix}{SOURCE}");
        let mut raw_context = context();
        let mut raw_receipt = receipt();
        let hash = json!(sha256_ref(raw.as_bytes()));
        raw_context["proof_artifact_sha256"] = hash.clone();
        raw_receipt["candidate_content_sha256"] = hash.clone();
        raw_receipt["lean_source_sha256"] = hash.clone();
        raw_receipt["package_manifest"][0][1] = hash;
        raw_receipt["candidate_content_hex"] = json!(hex::encode(&raw));
        raw_receipt["lean_source_hex"] = json!(hex::encode(&raw));
        assert_eq!(
            evaluate(&payload(raw_context, raw_receipt))["status"],
            "PASS",
            "{prefix}"
        );
    }
    let candidate = format!("Explanation\n```lean4\r\n{SOURCE}```\n");
    let mut c = context();
    let mut r = receipt();
    c["proof_artifact_sha256"] = json!(sha256_ref(candidate.as_bytes()));
    r["candidate_content_sha256"] = c["proof_artifact_sha256"].clone();
    r["candidate_content_hex"] = json!(hex::encode(&candidate));
    r["extraction_profile"] = json!("single-lean-fence-v1");
    assert_eq!(evaluate(&payload(c.clone(), r.clone()))["status"], "PASS");
    let extra = format!("{candidate}```lean\n{SOURCE}```\n");
    c["proof_artifact_sha256"] = json!(sha256_ref(extra.as_bytes()));
    r["candidate_content_sha256"] = c["proof_artifact_sha256"].clone();
    r["candidate_content_hex"] = json!(hex::encode(extra));
    assert_eq!(evaluate(&payload(c, r))["status"], "REFUSE");
}

#[test]
fn signed_duplicate_record_fields_are_not_last_value_wins() {
    let p = payload(context(), receipt());
    let raw = hex::decode(p["kernel_observation"]["record_hex"].as_str().unwrap()).unwrap();
    let record: Value = serde_json::from_slice(&raw).unwrap();
    let duplicate = format!(
        "{{\"schema_version\":\"{PROFILE}\",{}",
        &String::from_utf8(raw).unwrap()[1..]
    );
    let result = evaluate(&signed_record(&record, duplicate.as_bytes()));
    assert_eq!(result["refusal_code"], "KERNEL_OBSERVATION_INVALID");
}

#[test]
fn old_claimed_kernel_and_unmeasured_new_profile_hold() {
    let old = json!({"claim_statement":"True","has_mechanized_proof":true,"proof_kernel":"lean4",
        "proof_artifact_utf8":SOURCE,"proof_artifact_sha256":sha256_ref(SOURCE.as_bytes()),
        "proof_execution":{"exit_code":0,"artifact_sha256":sha256_ref(SOURCE.as_bytes()),
            "claim_sha256":sha256_ref(b"True"),"log_utf8":"PASS","log_sha256":sha256_ref(b"PASS")}});
    assert_eq!(evaluate(&old)["status"], "HOLD");
    assert_eq!(
        evaluate(&json!({"kernel_profile":PROFILE}))["status"],
        "HOLD"
    );
    for profile in [json!(null), json!("other")] {
        assert_eq!(
            evaluate(&json!({"kernel_profile":profile}))["status"],
            "REFUSE"
        );
    }
}

// Origin: engine/crates_rs/tests/core_adversary/authenticated_kernel_gate.rs
// Claim: urn:core:crates_rs:tests:authenticated-kernel-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda844c718 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda844c718` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora844c718 {
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
impl BoundaryErrora844c718 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora844c718 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora844c718 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda844c718 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora844c718> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora844c718::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora844c718::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora844c718::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a844c718() {
    let admitted = BoundaryRecorda844c718::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda844c718::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
