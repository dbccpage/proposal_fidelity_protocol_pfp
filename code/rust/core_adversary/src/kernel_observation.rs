//! Authenticated, source-bound Lake execution; the existing native audit owns axiom parsing.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2bb251ad<T> {
    fn checked_invariant_2bb251ad(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2bb251ad<T> for Option<T> {
    #[inline]
    fn checked_invariant_2bb251ad(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2bb251ad<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2bb251ad(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::{err, hold, Fields, GateResult, Spec};
use crate::evidence::{is_sha256_ref, sha256_ref};
use core_epistemic_immune_system::authenticated::{
    self, Binding, Purpose, SignedEvidence, TrustPolicy,
};
use pfp_runtime::lean_verify::{
    audit_lean_verification, scan_lean_sources, LeanAuditRequest, SourceFileEntry,
};
use regex::Regex;
use serde::Deserialize;
use serde_json::{json, Value};
use std::collections::BTreeMap;

pub const PROFILE: &str = authenticated::HOST_LEAN_SCOPE;
const MODULE: &str = "Discrete4DBianchiSpectralContraction";
const LAKEFILE: &str = "import Lake\nopen Lake DSL\n\npackage «Discrete4DBianchiSpectralContraction» where\n  version := v!\"0.1.0\"\n\nlean_lib «Discrete4DBianchiSpectralContraction» where\n  srcDir := \".\"\n";
type Refusal = crate::stage::ports::Refusal;

#[derive(Debug, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
struct Context {
    run_id: String,
    task_id: String,
    action_id: String,
    source_digest: String,
    candidate_sha256: String,
    proof_artifact_path: String,
    proof_artifact_sha256: String,
    checker_id: String,
    required_declarations: Vec<(String, String)>,
    axiom_policy: Vec<String>,
    toolchain_pin: String,
    lake_binary_path: String,
    lake_binary_sha256: String,
}

impl Context {
    fn digest(&self) -> String {
        sha256_ref(
            &serde_json::to_vec(&json!([
                self.run_id,
                self.task_id,
                self.action_id,
                self.source_digest,
                self.candidate_sha256,
                self.proof_artifact_path,
                self.proof_artifact_sha256,
                self.checker_id,
                self.required_declarations,
                self.axiom_policy,
                self.toolchain_pin,
                self.lake_binary_path,
                self.lake_binary_sha256
            ]))
            .checked_invariant_2bb251ad("string-only context"),
        )
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Record {
    schema_version: String,
    context: Context,
    lake_receipt_hex: String,
    observer_source_digest: String,
    authority_effect: String,
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
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Receipt {
    schema_version: String,
    authority_effect: String,
    run_key: String,
    candidate_id: String,
    candidate_content_sha256: String,
    candidate_content_hex: String,
    lean_source_sha256: String,
    lean_source_hex: String,
    extraction_profile: String,
    objective_sha256: String,
    checker_id: String,
    toolchain_pin: String,
    lake_binary_path: String,
    lake_binary_sha256: String,
    required_declarations: Vec<(String, String)>,
    axiom_policy: Vec<String>,
    package_manifest: Vec<(String, String)>,
    harness_source_hex: String,
    harness_source_sha256: String,
    processes: Vec<Process>,
    lean_receipt: LeanReceipt,
    verdict: String,
    reason: String,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Process {
    label: String,
    argv: Vec<String>,
    cwd: String,
    exit_code: Option<i64>,
    stdout_hex: Option<String>,
    stdout_sha256: Option<String>,
    stderr_hex: Option<String>,
    stderr_sha256: Option<String>,
    started_at_ms: u64,
    completed_at_ms: Option<u64>,
    direct_child_completed: bool,
    shell: bool,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct LeanReceipt {
    status: String,
    build_success: bool,
    harness_elaborated: bool,
    refusal_code: Option<String>,
    axioms: Vec<(String, Vec<String>)>,
}
fn invalid(message: &str) -> Refusal {
    err("KERNEL_OBSERVATION_INVALID", message)
}
fn binding_error(message: &str) -> Refusal {
    err("KERNEL_OBSERVATION_BINDING_MISMATCH", message)
}
fn digest(value: &str) -> bool {
    is_sha256_ref(&Value::String(value.to_owned()))
}
fn identifier(value: &str) -> bool {
    !value.trim().is_empty() && value.len() <= 4096 && !value.chars().any(char::is_control)
}
fn bytes(value: &str) -> Result<Vec<u8>, Refusal> {
    if value.len() > 128 * 1024
        || value.len() % 2 != 0
        || !value
            .bytes()
            .all(|v| v.is_ascii_digit() || (b'a'..=b'f').contains(&v))
    {
        return Err(invalid("Require bounded lowercase hexadecimal bytes"));
    }
    hex::decode(value).map_err(|_| invalid("Invalid hexadecimal bytes"))
}
fn text(raw: &[u8]) -> Result<&str, Refusal> {
    std::str::from_utf8(raw).map_err(|_| invalid("Require exact UTF-8 source and process text"))
}
fn absolute(value: &str) -> bool {
    value.starts_with('/')
        || value.starts_with("\\\\")
        || (value.as_bytes().get(1) == Some(&b':')
            && matches!(value.as_bytes().get(2), Some(b'/') | Some(b'\\')))
}

fn line_starts_at(candidate: &str, pos: usize) -> bool {
    pos == 0 || candidate.as_bytes()[pos - 1] == b'\n'
}

fn extract_fenced_lean(
    candidate: &str,
    start: usize,
    close: usize,
) -> Result<(&str, &'static str), Refusal> {
    if !line_starts_at(candidate, start) || !line_starts_at(candidate, close) {
        return Err(invalid("Lean fences must occupy their own lines"));
    }
    let end = candidate[start..]
        .find('\n')
        .map(|i| start + i)
        .ok_or_else(|| invalid("Incomplete Lean opening fence"))?;
    let opener = candidate[start..end]
        .trim_end_matches('\r')
        .trim_end_matches([' ', '\t']);
    if opener != "```lean" && opener != "```lean4" {
        return Err(invalid("Unsupported Lean fence language"));
    }
    let closing_end = candidate[close..]
        .find('\n')
        .map(|i| close + i)
        .unwrap_or(candidate.len());
    let closing = candidate[close..closing_end]
        .trim_end_matches('\r')
        .trim_end_matches([' ', '\t']);
    if closing != "```" || close <= end || candidate[end + 1..close].trim().is_empty() {
        return Err(invalid("Incomplete or empty Lean source fence"));
    }
    Ok((&candidate[end + 1..close], "single-lean-fence-v1"))
}

// This is the owning adapter's explicit extraction profile, not a proof-language heuristic.
fn extract(candidate: &str) -> Result<(&str, &'static str), Refusal> {
    let markers = Regex::new(r"(?m)^```[^\r\n]*(?:\r?\n|\z)")
        .map_err(|_| invalid("Invalid fixed extraction profile"))?;
    let positions: Vec<_> = markers.find_iter(candidate).map(|m| m.start()).collect();
    if positions.is_empty() {
        if candidate.trim().is_empty() {
            return Err(invalid("Empty submitted Lean source"));
        }
        return Ok((candidate, "raw-lean-v1"));
    }
    if positions.len() != 2 {
        return Err(invalid("Require one complete Lean fence"));
    }
    extract_fenced_lean(candidate, positions[0], positions[1])
}

fn harness(declarations: &[(String, String)]) -> String {
    let mut out = format!("-- Auto-generated Judge Verification Harness\nimport {MODULE}\n");
    for (i, (name, statement)) in declarations.iter().enumerate() {
        out.push_str(&format!(
            "theorem judge_check_{} : {} := {}\n#print axioms judge_check_{}\n",
            i + 1,
            statement,
            name,
            i + 1
        ));
    }
    out
}
fn stream(encoded: &Option<String>, expected: &Option<String>) -> Result<Vec<u8>, Refusal> {
    let raw = bytes(
        encoded
            .as_deref()
            .ok_or_else(|| invalid("Missing captured stream"))?,
    )?;
    if Some(sha256_ref(&raw)).as_ref() != expected.as_ref() {
        return Err(err(
            "KERNEL_OUTPUT_HASH_MISMATCH",
            "Captured process stream differs from its digest",
        ));
    }
    Ok(raw)
}

fn receipt_header_matches(receipt: &Receipt, c: &Context) -> bool {
    receipt.schema_version == "core.adversary.lake-check.v2"
        && receipt.authority_effect == "None"
        && receipt.run_key == c.run_id
        && receipt.candidate_id == c.action_id
        && receipt.candidate_content_sha256 == c.proof_artifact_sha256
        && receipt.checker_id == "lake_sandbox_adapter"
}

fn receipt_policy_matches(receipt: &Receipt, c: &Context) -> bool {
    digest(&receipt.objective_sha256)
        && receipt.required_declarations == c.required_declarations
        && receipt.axiom_policy == c.axiom_policy
        && receipt.toolchain_pin == c.toolchain_pin
        && receipt.lake_binary_path == c.lake_binary_path
        && receipt.lake_binary_sha256 == c.lake_binary_sha256
}

fn verify_harness_and_manifest(
    receipt: &Receipt,
    c: &Context,
    source: &str,
) -> Result<String, Refusal> {
    let harness_src = harness(&c.required_declarations);
    if bytes(&receipt.harness_source_hex)? != harness_src.as_bytes()
        || receipt.harness_source_sha256 != sha256_ref(harness_src.as_bytes())
    {
        return Err(binding_error(
            "Judge harness does not state the configured required declarations",
        ));
    }
    let manifest = vec![
        (format!("{MODULE}.lean"), sha256_ref(source.as_bytes())),
        ("Verify.lean".into(), sha256_ref(harness_src.as_bytes())),
        ("lakefile.lean".into(), sha256_ref(LAKEFILE.as_bytes())),
        (
            "lean-toolchain".into(),
            sha256_ref(format!("{}\n", c.toolchain_pin).as_bytes()),
        ),
    ];
    if receipt.package_manifest != manifest {
        return Err(binding_error(
            "Lake package bytes or source inventory changed",
        ));
    }
    Ok(harness_src)
}

fn verify_receipt_sources_and_manifest(
    receipt: &Receipt,
    c: &Context,
) -> Result<(String, String), Refusal> {
    let candidate = bytes(&receipt.candidate_content_hex)?;
    if sha256_ref(&candidate) != c.proof_artifact_sha256 {
        return Err(binding_error("Submitted proof bytes changed"));
    }
    let (source, profile) = extract(text(&candidate)?)?;
    if profile != receipt.extraction_profile
        || bytes(&receipt.lean_source_hex)? != source.as_bytes()
        || sha256_ref(source.as_bytes()) != receipt.lean_source_sha256
    {
        return Err(binding_error(
            "Compiled Lean source is not the exact declared extraction of the submitted proof",
        ));
    }
    let harness_src = verify_harness_and_manifest(receipt, c, source)?;
    Ok((source.to_owned(), harness_src))
}

fn process_shape_valid(
    p: &Process,
    expected_label: &str,
    expected_argv: &[String],
    cwd: &str,
) -> bool {
    p.label == expected_label
        && p.argv == expected_argv
        && p.cwd == cwd
        && absolute(cwd)
        && !p.shell
        && p.direct_child_completed
}

fn process_timing_valid(
    started_at_ms: u64,
    completed: u64,
    previous_end: u64,
    now: u64,
    issued_at: u64,
) -> bool {
    started_at_ms >= previous_end
        && completed >= started_at_ms
        && u128::from(completed) <= u128::from(now) * 1000 + 999
        && u128::from(completed) <= u128::from(issued_at) * 1000 + 999
}

fn verify_single_process(
    i: usize,
    p: &Process,
    c: &Context,
    cwd: &str,
    previous_end: u64,
    now: u64,
    issued_at: u64,
) -> Result<(Vec<u8>, Vec<u8>, i64, u64), Refusal> {
    let arguments = [
        vec!["env", "lean", "--version"],
        vec!["build", "+Discrete4DBianchiSpectralContraction:olean"],
        vec!["env", "lean", "Verify.lean"],
    ];
    let labels = ["toolchain", "build", "elaborate"];
    let argv: Vec<_> = std::iter::once(c.lake_binary_path.clone())
        .chain(arguments[i].iter().map(|s| s.to_string()))
        .collect();
    let completed = p
        .completed_at_ms
        .ok_or_else(|| invalid("Uncompleted Lake process"))?;
    if !process_shape_valid(p, labels[i], &argv, cwd)
        || !process_timing_valid(p.started_at_ms, completed, previous_end, now, issued_at)
    {
        return Err(invalid(
            "Lake process command, order, clock or completion differs from the owned execution",
        ));
    }
    let out = stream(&p.stdout_hex, &p.stdout_sha256)?;
    let err_out = stream(&p.stderr_hex, &p.stderr_sha256)?;
    let exit = p
        .exit_code
        .ok_or_else(|| invalid("Unmeasured Lake exit status"))?;
    Ok((out, err_out, exit, completed))
}

fn verify_processes_sequence(
    receipt: &Receipt,
    c: &Context,
    now: u64,
    issued_at: u64,
) -> Result<(Vec<(Vec<u8>, Vec<u8>)>, Option<usize>), Refusal> {
    if !(2..=3).contains(&receipt.processes.len()) {
        return Err(invalid(
            "Require the exact toolchain/build prefix, with elaboration only after a successful build",
        ));
    }
    let mut captures = Vec::new();
    let mut previous_end = 0;
    let mut failed_process = None;
    let cwd = &receipt.processes[0].cwd;
    for (i, p) in receipt.processes.iter().enumerate() {
        let (out, err_out, exit, completed) =
            verify_single_process(i, p, c, cwd, previous_end, now, issued_at)?;
        captures.push((out, err_out));
        if exit != 0 {
            if i == 0 {
                return Err(invalid(
                    "Failed toolchain discovery is not a submitted-certificate failure",
                ));
            }
            if i + 1 != receipt.processes.len() {
                return Err(binding_error(
                    "A later process was recorded after the first failed required process",
                ));
            }
            failed_process = Some(i);
        }
        previous_end = completed;
    }
    Ok((captures, failed_process))
}

fn verify_toolchain_version(stdout: &[u8], toolchain_pin: &str) -> Result<(), Refusal> {
    let version = text(stdout)?;
    let requested_version = toolchain_pin
        .strip_prefix("leanprover/lean4:v")
        .ok_or_else(|| invalid("Require a pinned leanprover/lean4 version"))?;
    let observed_version = version
        .trim()
        .strip_prefix("Lean (version ")
        .and_then(|s| s.split([',', ')']).next());
    if observed_version != Some(requested_version) {
        return Err(binding_error(
            "Actual Lean version differs from the pinned toolchain",
        ));
    }
    Ok(())
}

fn verify_failed_process_rejection(receipt: &Receipt, index: usize) -> Result<Value, Refusal> {
    let lr = &receipt.lean_receipt;
    let valid_rejection = receipt.verdict == "REJECTED"
        && !receipt.reason.trim().is_empty()
        && lr.status == "FAIL"
        && lr.build_success == (index == 2)
        && !lr.harness_elaborated
        && !lr.refusal_code.as_deref().map_or(true, str::is_empty);
    if !valid_rejection {
        return Err(binding_error(
            "Failed-process prefix disagrees with the submitted-certificate rejection summary",
        ));
    }
    Err(err(
        "KERNEL_EXECUTION_FAILED",
        "The exact submitted certificate failed a completed build/elaboration attempt under the pinned successful toolchain; no theorem-falsity conclusion",
    ))
}

fn accepted_summary_matches(
    receipt: &Receipt,
    expected_axioms: &BTreeMap<String, Vec<String>>,
) -> bool {
    let lr = &receipt.lean_receipt;
    let summary: BTreeMap<_, _> = lr.axioms.iter().cloned().collect();
    receipt.verdict == "ACCEPTED"
        && !receipt.reason.trim().is_empty()
        && lr.status == "PASS"
        && lr.build_success
        && lr.harness_elaborated
        && lr.refusal_code.is_none()
        && summary.len() == lr.axioms.len()
        && &summary == expected_axioms
}

fn verify_accepted_elaboration(
    receipt: &Receipt,
    c: &Context,
    source: String,
    harness_src: String,
    captures: &[(Vec<u8>, Vec<u8>)],
) -> Result<Value, Refusal> {
    let scan = scan_lean_sources(
        &[
            SourceFileEntry {
                file: format!("{MODULE}.lean"),
                content: source,
            },
            SourceFileEntry {
                file: "Verify.lean".into(),
                content: harness_src,
            },
        ],
        &[],
    );
    let judges: Vec<_> = (1..=c.required_declarations.len())
        .map(|i| format!("judge_check_{i}"))
        .collect();
    let audit = audit_lean_verification(&LeanAuditRequest {
        axioms_output: format!("{}\n{}", text(&captures[2].0)?, text(&captures[2].1)?),
        policy: c.axiom_policy.clone(),
        required_declarations: judges.clone(),
        build_success: true,
        harness_elaborated: true,
        forbidden_findings: scan.findings,
    });
    // The older auditor's empty policy means defaults. This profile instead pins an exact policy,
    // including an explicitly empty set, without changing that historical ABI.
    let policy_violated = judges.iter().any(|name| {
        audit
            .axioms_by_declaration
            .get(name)
            .map_or(true, |axioms| {
                axioms.iter().any(|a| !c.axiom_policy.contains(a))
            })
    });
    if audit.status != "PASS" || policy_violated {
        return Err(err(
            "KERNEL_AUDIT_FAILED",
            "Native source and required-declaration axiom audit refused the observed elaboration",
        ));
    }
    if !accepted_summary_matches(receipt, &audit.axioms_by_declaration) {
        return Err(binding_error(
            "Lake receipt summary differs from independent native replay of its captured results",
        ));
    }
    Ok(
        json!({"required_declarations":c.required_declarations,"axiom_policy":c.axiom_policy,
        "axioms":audit.axioms_by_declaration,"proof_artifact_sha256":c.proof_artifact_sha256,
        "lean_source_sha256":receipt.lean_source_sha256,"toolchain_pin":c.toolchain_pin,
        "lake_binary_sha256":c.lake_binary_sha256,"completed_processes":3}),
    )
}

fn audit_receipt(r: &Record, now: u64, issued_at: u64) -> Result<Value, Refusal> {
    let c = &r.context;
    let receipt: Receipt = serde_json::from_slice(&bytes(&r.lake_receipt_hex)?)
        .map_err(|_| invalid("Require exact v2 Lake receipt fields and types"))?;
    if !receipt_header_matches(&receipt, c) || !receipt_policy_matches(&receipt, c) {
        return Err(binding_error(
            "Lake receipt does not bind the selected proof, statements, policy and executable",
        ));
    }
    let (source, harness_src) = verify_receipt_sources_and_manifest(&receipt, c)?;
    let (captures, failed_process) = verify_processes_sequence(&receipt, c, now, issued_at)?;
    verify_toolchain_version(&captures[0].0, &c.toolchain_pin)?;
    if let Some(index) = failed_process {
        return verify_failed_process_rejection(&receipt, index);
    }
    if receipt.processes.len() != 3 {
        return Err(invalid(
            "Successful build without the required elaboration is unavailable verification",
        ));
    }
    verify_accepted_elaboration(&receipt, c, source, harness_src, &captures)
}

fn record_identities_valid(record: &Record) -> bool {
    let c = &record.context;
    let ids_ok = [
        &c.run_id,
        &c.task_id,
        &c.action_id,
        &c.checker_id,
        &c.proof_artifact_path,
        &c.toolchain_pin,
        &c.lake_binary_path,
    ]
    .into_iter()
    .all(|v| identifier(v));
    let digests_ok = [
        &c.source_digest,
        &c.candidate_sha256,
        &c.proof_artifact_sha256,
        &c.lake_binary_sha256,
        &record.observer_source_digest,
    ]
    .into_iter()
    .all(|v| digest(v));
    record.schema_version == PROFILE
        && record.authority_effect == "None"
        && ids_ok
        && digests_ok
        && absolute(&c.lake_binary_path)
}

fn declarations_and_policy_valid(c: &Context) -> bool {
    !c.required_declarations.is_empty()
        && !c
            .required_declarations
            .iter()
            .any(|(name, stmt)| !identifier(name) || stmt.trim().is_empty() || stmt.contains('\0'))
        && c.axiom_policy.iter().all(|a| identifier(a))
}

fn observation_matches_binding(
    observation: &Observation,
    envelope: &Envelope,
    record: &Record,
    binding: &Binding,
) -> bool {
    let c = &record.context;
    observation.schema_version == "core.eis.observed-evidence.v1"
        && observation.observer_id == envelope.signed.attestation.issuer
        && observation.run_id == c.run_id
        && observation.subject_digest == binding.subject_digest
        && observation.source_digest == record.observer_source_digest
        && observation.outcome == authenticated::KERNEL_OBSERVED
        && envelope.signed.attestation.outcome == authenticated::KERNEL_OBSERVED
}

fn parse_kernel_envelope_and_record(p: &Fields) -> Result<(Envelope, Vec<u8>, Record), Refusal> {
    let envelope: Envelope = serde_json::from_value(
        p.get("kernel_observation")
            .filter(|v| !v.is_null())
            .ok_or_else(|| hold("authenticated owning-host Lean observation"))?
            .clone(),
    )
    .map_err(|_| invalid("Require exact record_hex and signed EIS evidence"))?;
    let raw = bytes(&envelope.record_hex)?;
    let record: Record = serde_json::from_slice(&raw).map_err(|_| {
        invalid("Kernel record has duplicate, unknown, missing or ill-typed fields")
    })?;
    let expected: Context =
        serde_json::from_value(p.get("kernel_expected").cloned().unwrap_or(Value::Null))
            .map_err(|_| invalid("Require host-selected exact current kernel bindings"))?;
    if record.context != expected {
        return Err(binding_error(
            "Kernel observation differs from current host-selected proof/task/checker",
        ));
    }
    if !record_identities_valid(&record) || !declarations_and_policy_valid(&record.context) {
        return Err(invalid(
            "Kernel record requires nonempty statements and exact source/toolchain identities",
        ));
    }
    Ok((envelope, raw, record))
}

fn verify_signed_kernel_observation(
    envelope: &Envelope,
    record: &Record,
    binding: &Binding,
    policy: &TrustPolicy,
    now: u64,
) -> Result<(), Refusal> {
    let observation: Observation =
        serde_json::from_slice(&bytes(&envelope.signed.evidence_hex)?)
            .map_err(|_| invalid("Require exact EIS observed-evidence fields"))?;
    if !observation_matches_binding(&observation, envelope, record, binding) {
        return Err(binding_error(
            "Signed observer, run or record identity differs from the kernel observation",
        ));
    }
    authenticated::verify(&envelope.signed, policy, binding, Purpose::Observation, now)
        .map(|_| ())
        .map_err(|e| err(&e.code, e.message))
}

pub(super) fn evaluate(spec: &Spec, p: &Fields) -> GateResult {
    if p.get("kernel_profile").and_then(Value::as_str) != Some(PROFILE) {
        return Err(err(
            "KERNEL_PROFILE_UNSUPPORTED",
            "Unknown owning-host Lean profile",
        ));
    }
    let (envelope, raw, record) = parse_kernel_envelope_and_record(p)?;
    let c = &record.context;
    let now = p
        .get("now")
        .and_then(Value::as_u64)
        .ok_or_else(|| invalid("Require host UTC seconds"))?;
    let policy: TrustPolicy =
        serde_json::from_value(p.get("kernel_trust_policy").cloned().unwrap_or(Value::Null))
            .map_err(|_| {
                err(
                    "KERNEL_TRUST_UNCONFIGURED",
                    "Require configured owning-host EIS trust policy",
                )
            })?;
    let binding = Binding {
        spec_id: spec.id.into(),
        scope: PROFILE.into(),
        rule_digest: sha256_ref(spec.bytes),
        source_digest: c.source_digest.clone(),
        subject_digest: sha256_ref(&raw),
        context_digest: c.digest(),
    };
    verify_signed_kernel_observation(&envelope, &record, &binding, &policy, now)?;
    let audit = audit_receipt(&record, now, envelope.signed.attestation.issued_at)?;
    Ok(
        json!({"kernel_profile":PROFILE,"record_sha256":binding.subject_digest,"run_id":c.run_id,
        "task_id":c.task_id,"action_id":c.action_id,"candidate_sha256":c.candidate_sha256,
        "checker_id":c.checker_id,"audit":audit,"sandbox_verified":false,"general_theorem_verified":false}),
    )
}

// Origin: engine/crates_rs/core_adversary/src/kernel_observation.rs
// Claim: urn:core:crates_rs:core-adversary:kernel-observation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2bb251ad {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2bb251ad` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2bb251ad {
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
impl BoundaryError2bb251ad {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2bb251ad {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2bb251ad {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2bb251ad {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2bb251ad> {
        if capacity_bound == 0 {
            return Err(BoundaryError2bb251ad::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2bb251ad::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2bb251ad::ExceedsCapacity {
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
mod tests {
    use super::*;

    fn observed_prefix(exits: &[i64]) -> Record {
        let source = "theorem observed_truth : True := by trivial\n";
        let declarations = vec![("observed_truth".to_string(), "True".to_string())];
        let judge = harness(&declarations);
        let pin = "leanprover/lean4:v4.34.0";
        let lake = "/fixture/lake";
        let labels = ["toolchain", "build", "elaborate"];
        let arguments = [
            vec!["env", "lean", "--version"],
            vec!["build", "+Discrete4DBianchiSpectralContraction:olean"],
            vec!["env", "lean", "Verify.lean"],
        ];
        let streams = [
            "Lean (version 4.34.0, fixture)\n",
            "build output\n",
            "'judge_check_1' does not depend on any axioms\n",
        ];
        let processes = exits.iter().enumerate().map(|(i, exit)| json!({
            "label":labels[i], "argv":std::iter::once(lake).chain(arguments[i].iter().copied()).collect::<Vec<_>>(),
            "cwd":"/fixture/package", "exit_code":exit, "stdout_hex":hex::encode(streams[i]),
            "stdout_sha256":sha256_ref(streams[i].as_bytes()), "stderr_hex":"",
            "stderr_sha256":sha256_ref(b""), "started_at_ms":i as u64 * 2,
            "completed_at_ms":i as u64 * 2 + 1, "direct_child_completed":true, "shell":false
        })).collect::<Vec<_>>();
        let build = exits.get(1) == Some(&0);
        let complete = build && exits.get(2) == Some(&0);
        let receipt = json!({"schema_version":"core.adversary.lake-check.v2", "authority_effect":"None",
            "run_key":"run", "candidate_id":"action", "candidate_content_sha256":sha256_ref(source.as_bytes()),
            "candidate_content_hex":hex::encode(source), "lean_source_sha256":sha256_ref(source.as_bytes()),
            "lean_source_hex":hex::encode(source), "extraction_profile":"raw-lean-v1",
            "objective_sha256":sha256_ref(b"original task"), "checker_id":"lake_sandbox_adapter",
            "toolchain_pin":pin, "lake_binary_path":lake, "lake_binary_sha256":sha256_ref(b"lake"),
            "required_declarations":declarations, "axiom_policy":["propext","Quot.sound"],
            "package_manifest":[[format!("{MODULE}.lean"),sha256_ref(source.as_bytes())],
                ["Verify.lean",sha256_ref(judge.as_bytes())],
                ["lakefile.lean",sha256_ref(LAKEFILE.as_bytes())],
                ["lean-toolchain",sha256_ref(format!("{pin}\n").as_bytes())]],
            "harness_source_hex":hex::encode(judge.as_bytes()), "harness_source_sha256":sha256_ref(judge.as_bytes()),
            "processes":processes, "lean_receipt":{"status":if complete {"PASS"} else {"FAIL"},
                "build_success":build,"harness_elaborated":complete,
                "refusal_code":if complete {Value::Null} else {json!("LEAN_BUILD_FAILED")},
                "axioms":if complete {json!([["judge_check_1",[]]])} else {json!([])}},
            "verdict":if complete {"ACCEPTED"} else {"REJECTED"}, "reason":"actual observed fixture attempt"});
        Record {
            schema_version: PROFILE.into(),
            context: Context {
                run_id: "run".into(),
                task_id: "task".into(),
                action_id: "action".into(),
                source_digest: sha256_ref(b"source"),
                candidate_sha256: sha256_ref(b"candidate"),
                proof_artifact_path: "/fixture/proof.lean".into(),
                proof_artifact_sha256: sha256_ref(source.as_bytes()),
                checker_id: "checker".into(),
                required_declarations: declarations,
                axiom_policy: vec!["propext".into(), "Quot.sound".into()],
                toolchain_pin: pin.into(),
                lake_binary_path: lake.into(),
                lake_binary_sha256: sha256_ref(b"lake"),
            },
            lake_receipt_hex: hex::encode(serde_json::to_vec(&receipt).unwrap()),
            observer_source_digest: sha256_ref(b"observer"),
            authority_effect: "None".into(),
        }
    }

    fn change_receipt(record: &mut Record, change: impl FnOnce(&mut Value)) {
        let mut receipt: Value =
            serde_json::from_slice(&hex::decode(&record.lake_receipt_hex).unwrap()).unwrap();
        change(&mut receipt);
        record.lake_receipt_hex = hex::encode(serde_json::to_vec(&receipt).unwrap());
    }

    #[test]
    fn completed_certificate_failures_require_exact_verified_prefixes() {
        for exits in [&[0, 1][..], &[0, 0, 1][..]] {
            assert_eq!(
                audit_receipt(&observed_prefix(exits), 10, 10)
                    .unwrap_err()
                    .code,
                "KERNEL_EXECUTION_FAILED"
            );
        }
        assert!(audit_receipt(&observed_prefix(&[0, 0, 0]), 10, 10).is_ok());
        for exits in [&[0, 0][..], &[1, 1][..], &[0, 1, 0][..]] {
            assert_ne!(
                audit_receipt(&observed_prefix(exits), 10, 10)
                    .unwrap_err()
                    .code,
                "KERNEL_EXECUTION_FAILED"
            );
        }
        let mut bad_stream = observed_prefix(&[0, 1]);
        change_receipt(&mut bad_stream, |r| {
            r["processes"][1]["stdout_sha256"] = json!(sha256_ref(b"changed"))
        });
        assert_eq!(
            audit_receipt(&bad_stream, 10, 10).unwrap_err().code,
            "KERNEL_OUTPUT_HASH_MISMATCH"
        );
        let mut bad_summary = observed_prefix(&[0, 1]);
        change_receipt(&mut bad_summary, |r| r["verdict"] = json!("ACCEPTED"));
        assert_eq!(
            audit_receipt(&bad_summary, 10, 10).unwrap_err().code,
            "KERNEL_OBSERVATION_BINDING_MISMATCH"
        );
        let mut wrong_toolchain = observed_prefix(&[0, 1]);
        change_receipt(&mut wrong_toolchain, |r| {
            let raw = b"Lean (version 4.35.0, wrong)\n";
            r["processes"][0]["stdout_hex"] = json!(hex::encode(raw));
            r["processes"][0]["stdout_sha256"] = json!(sha256_ref(raw));
        });
        assert_eq!(
            audit_receipt(&wrong_toolchain, 10, 10).unwrap_err().code,
            "KERNEL_OBSERVATION_BINDING_MISMATCH"
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_2bb251ad {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2bb251ad::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2bb251ad::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2bb251ad::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2bb251ad::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2bb251ad::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError2bb251ad::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError2bb251ad::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
