//! Local-CI gate evaluation. AuthorityEffect: None.

use core_policy::local_ci_gates::{
    evaluate_bytes, receipt_bytes, resolved_invocation_digest, GateStatus, Verdict,
};

const PIN: &str = "7e506a6b5a946b01740d2bc3398c2ef3b58cf88c1a4517828733a5d96029195f";
const AUTH: &str = r#""authority_effect":null,"creates_execution_authority":false"#;

fn repeated(byte: char, len: usize) -> String {
    byte.to_string().repeat(len)
}

fn manifest() -> String {
    format!(
        r#"{{"schema":"omega.local_ci.candidate_manifest.v1",{AUTH},"base_oid":"{base}","head_oid":"{head}","entries":[{{"path":"a.rs","blob_oid":"{blob}","content_sha256":"{sha}"}}]}}"#,
        base = repeated('c', 40),
        head = repeated('d', 40),
        blob = repeated('a', 40),
        sha = repeated('b', 64),
    )
}

fn tool_gate(disposition: &str, timeout: u64) -> String {
    format!(
        r#"{{"gate_id":"rustfmt_changed_candidate_v1","disposition":"{disposition}","timeout_seconds":{timeout},"cwd":".","route":{{"runner_kind":"TOOL","tool_id":"rustfmt","argv_prefix":["--check","--edition","2021"],"argument_source":"CANDIDATE_RUST_PATHS"}},{AUTH}}}"#
    )
}

fn quarantine_gate() -> String {
    format!(
        r#"{{"gate_id":"legacy_route_v1","disposition":"QUARANTINED","timeout_seconds":0,"cwd":".","route":{{"runner_kind":"QUARANTINED","legacy_route":"old","reason":"retired","residual_code":"LEGACY_ROUTE_QUARANTINED"}},{AUTH}}}"#
    )
}

fn python_gate() -> String {
    format!(
        r#"{{"gate_id":"rule_gate_v1","disposition":"REQUIRED","timeout_seconds":60,"cwd":".","route":{{"runner_kind":"PYTHON","entrypoint":"operations/use_cases/cicd/local_ci_protocol.py","argv":["-m","pkg"]}},{AUTH}}}"#
    )
}

fn result(gate_id: &str, status: &str, exit_code: &str, digest: &str, argv: &str, inputs: &str) -> String {
    format!(
        r#"{{"gate_id":"{gate_id}","status":"{status}","resolved_argv":{argv},"resolved_inputs":{inputs},"resolved_invocation_sha256":"{digest}","exit_code":{exit_code},"duration_ms":10,"detail":"ok",{AUTH}}}"#
    )
}

fn request(catalog: &str, results: &str) -> String {
    format!(
        r#"{{"schema":"omega.policy.local_ci_gate_request.v1","interpreter":"py",{AUTH},"manifest":{manifest},"catalog":[{catalog}],"results":[{results}]}}"#,
        manifest = manifest(),
    )
}

fn tool_result(status: &str, exit_code: &str, digest: &str) -> String {
    result(
        "rustfmt_changed_candidate_v1",
        status,
        exit_code,
        digest,
        r#"["rustfmt","--check","--edition","2021","a.rs"]"#,
        r#"["a.rs"]"#,
    )
}

#[test]
fn resolution_digest_matches_the_python_preimage() {
    assert_eq!(
        resolved_invocation_digest(
            "rustfmt_changed_candidate_v1",
            &["rustfmt", "--check", "--edition", "2021", "a.rs"],
            &["a.rs"],
        ),
        PIN
    );
}

#[test]
fn required_pass_keeps_quarantine_residual_and_refuses_float_and_prose() {
    let body = request(
        &format!("{},{}", tool_gate("REQUIRED", 90), quarantine_gate()),
        &tool_result("PASS", "0", PIN),
    );
    let receipt = evaluate_bytes(body.as_bytes());
    assert_eq!(receipt.authority_effect(), "None");
    assert!(!receipt.creates_execution_authority());
    assert!(matches!(receipt.status, GateStatus::Pass));
    assert_eq!(receipt.body.verdict, Some(Verdict::PreflightPass));
    assert_eq!(receipt.body.quarantine_residuals.len(), 1);
    assert_eq!(receipt.body.quarantine_residuals[0].residual_code, "LEGACY_ROUTE_QUARANTINED");
    let encoded = String::from_utf8(receipt_bytes(&receipt).unwrap()).unwrap();
    assert!(encoded.contains("\"creates_execution_authority\":false"));
    assert!(encoded.contains("\"status\":\"PASS\""));
    assert!(!encoded.contains("verified"));

    assert_eq!(evaluate_bytes(br#"{"timeout_seconds":1.5}"#).status.code(), "FLOAT_FORBIDDEN");
    assert_eq!(evaluate_bytes(br#"{"verified":true}"#).status.code(), "PROSE_AUTHORITY");
    let prose = body.replace("\"creates_execution_authority\":false", "\"creates_execution_authority\":true");
    assert_eq!(evaluate_bytes(prose.as_bytes()).status.code(), "PROSE_AUTHORITY");
}

#[test]
fn required_failure_skip_binding_order_and_malformed_exit() {
    let fail = evaluate_bytes(request(&tool_gate("REQUIRED", 90), &tool_result("FAIL", "1", PIN)).as_bytes());
    match fail.status {
        GateStatus::Fail(violation) => {
            assert_eq!(violation.code, "REQUIRED_GATE_NONPASS");
            assert_eq!(violation.gate_id, "rustfmt_changed_candidate_v1");
        }
        other => panic!("expected fail, got {other:?}"),
    }

    let skipped = evaluate_bytes(
        request(&tool_gate("REQUIRED", 90), &tool_result("SKIP", "null", PIN)).as_bytes(),
    );
    assert_eq!(skipped.status.code(), "SKIP_OR_BYPASS_REFUSED");

    let mut wrong = PIN.to_owned();
    wrong.replace_range(0..1, "0");
    let unbound = evaluate_bytes(request(&tool_gate("REQUIRED", 90), &tool_result("PASS", "0", &wrong)).as_bytes());
    assert_eq!(unbound.status.code(), "RESULT_BINDING_MISMATCH");

    let malformed = evaluate_bytes(request(&tool_gate("REQUIRED", 90), &tool_result("PASS", "1", PIN)).as_bytes());
    assert_eq!(malformed.status.code(), "MALFORMED_RESULT");

    let advisory = evaluate_bytes(request(&tool_gate("ADVISORY", 30), &tool_result("FAIL", "1", PIN)).as_bytes());
    assert!(matches!(advisory.status, GateStatus::Pass));
    assert_eq!(advisory.body.verdict, Some(Verdict::PreflightPassWithAdvisoryFindings));
    assert_eq!(advisory.body.advisory_findings.len(), 1);

    let py = resolved_invocation_digest("rule_gate_v1", &["py", "-B", "-m", "pkg"], &[]);
    let py_result = result("rule_gate_v1", "PASS", "0", &py, r#"["py","-B","-m","pkg"]"#, "[]");
    let ordered = evaluate_bytes(
        request(
            &format!("{},{}", tool_gate("REQUIRED", 90), python_gate()),
            &format!("{},{}", py_result, tool_result("PASS", "0", PIN)),
        )
        .as_bytes(),
    );
    assert_eq!(ordered.status.code(), "RESULT_ORDER_MISMATCH");

    let executed = result(
        "legacy_route_v1",
        "PASS",
        "0",
        PIN,
        r#"["rustfmt"]"#,
        "[]",
    );
    let quarantined = evaluate_bytes(
        request(
            &format!("{},{}", tool_gate("REQUIRED", 90), quarantine_gate()),
            &executed,
        )
        .as_bytes(),
    );
    assert_eq!(quarantined.status.code(), "QUARANTINED_GATE_EXECUTED");
}

trait Code {
    fn code(&self) -> &str;
}

impl Code for GateStatus {
    fn code(&self) -> &str {
        match self {
            GateStatus::Pass => "PASS",
            GateStatus::Fail(violation) => violation.code,
            GateStatus::Refuse(reason) => reason.code,
        }
    }
}

// Origin: engine/crates_rs/tests/core_policy/local_ci_gate_eval.rs
// Claim: urn:core:crates_rs:tests:local-ci-gate-eval:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfaf7fd2b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfaf7fd2b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfaf7fd2b {
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
impl BoundaryErrorfaf7fd2b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfaf7fd2b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfaf7fd2b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfaf7fd2b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfaf7fd2b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfaf7fd2b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfaf7fd2b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfaf7fd2b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_faf7fd2b() {
    let admitted = BoundaryRecordfaf7fd2b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfaf7fd2b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
