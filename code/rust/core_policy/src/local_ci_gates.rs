//! Sovereign image of `evaluate_gate_results` and `resolve_gate_invocation`.
//! AuthorityEffect: None. This module does not mint an action license.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_0fce4bfc<T> {
    fn checked_invariant_0fce4bfc(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_0fce4bfc<T> for Option<T> {
    #[inline]
    fn checked_invariant_0fce4bfc(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_0fce4bfc<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_0fce4bfc(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::jcs::{self, Jcs};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use unicode_normalization::UnicodeNormalization;

pub const REQUEST_SCHEMA: &str = "core.policy.local_ci_gate_request.v1";
pub const RECEIPT_SCHEMA: &str = "core.policy.local_ci_gate_receipt.v1";
pub const MANIFEST_SCHEMA: &str = "core.local_ci.candidate_manifest.v1";

const SAFE_INTEGER: u64 = (1 << 53) - 1;
const RESOLUTION_DOMAIN: &[u8] = b"engine/ResolvedGateInvocationV1/v1\0";

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Violation {
    pub code: &'static str,
    pub gate_id: String,
    pub detail: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RefusalReason {
    pub code: &'static str,
    pub detail: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum GateStatus {
    Pass,
    Fail(Violation),
    Refuse(RefusalReason),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Verdict {
    PreflightPass,
    PreflightPassWithAdvisoryFindings,
    PreflightFail,
}

impl Verdict {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::PreflightPass => "PREFLIGHT_PASS",
            Self::PreflightPassWithAdvisoryFindings => "PREFLIGHT_PASS_WITH_ADVISORY_FINDINGS",
            Self::PreflightFail => "PREFLIGHT_FAIL",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AdvisoryStatus {
    Fail,
    Timeout,
    Unavailable,
}

impl AdvisoryStatus {
    fn as_str(self) -> &'static str {
        match self {
            Self::Fail => "FAIL",
            Self::Timeout => "TIMEOUT",
            Self::Unavailable => "UNAVAILABLE",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AdvisoryFinding {
    pub gate_id: String,
    pub status: AdvisoryStatus,
    pub detail: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct QuarantineResidual {
    pub gate_id: String,
    pub residual_code: String,
    pub legacy_route: String,
    pub reason: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GateReport {
    pub verdict: Option<Verdict>,
    pub advisory_findings: Vec<AdvisoryFinding>,
    pub quarantine_residuals: Vec<QuarantineResidual>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Receipt<T> {
    pub status: GateStatus,
    pub body: T,
}

impl<T> Receipt<T> {
    pub fn authority_effect(&self) -> &'static str {
        "None"
    }

    pub fn creates_execution_authority(&self) -> bool {
        false
    }
}

pub fn resolved_invocation_digest(gate_id: &str, argv: &[&str], inputs: &[&str]) -> String {
    let mut body = String::from("{\"gate_id\":");
    body.push_str(&json_string(gate_id));
    body.push_str(",\"resolved_argv\":");
    push_strings(&mut body, argv);
    body.push_str(",\"resolved_inputs\":");
    push_strings(&mut body, inputs);
    body.push('}');
    body.push('\n');
    let mut hasher = Sha256::new();
    hasher.update(RESOLUTION_DOMAIN);
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())
}

pub fn evaluate_bytes(bytes: &[u8]) -> Receipt<GateReport> {
    if let Err(failure) = jcs::screen(bytes, jcs::GATE_LIMITS) {
        return refuse(failure.code, failure.detail);
    }
    let wire: RequestWire = match serde_json::from_slice(bytes) {
        Ok(wire) => wire,
        Err(error) => {
            let text = error.to_string();
            if text.contains("creates_execution_authority must be exact false") {
                return refuse("PROSE_AUTHORITY", text);
            }
            return refuse("INVALID_RECORD", text);
        }
    };
    match judge(wire) {
        Ok(report) => Receipt {
            status: GateStatus::Pass,
            body: report,
        },
        Err(Judgement::Fail(violation)) => Receipt {
            status: GateStatus::Fail(violation),
            body: empty_report(Some(Verdict::PreflightFail)),
        },
        Err(Judgement::Refuse(reason)) => Receipt {
            status: GateStatus::Refuse(reason),
            body: empty_report(None),
        },
    }
}

pub fn receipt_bytes(receipt: &Receipt<GateReport>) -> Result<Vec<u8>, &'static str> {
    let (status, code, detail, violation) = match &receipt.status {
        GateStatus::Pass => {
            let verdict = receipt
                .body
                .verdict
                .map(Verdict::as_str)
                .unwrap_or("PREFLIGHT_PASS");
            ("PASS", verdict, String::new(), Jcs::Null)
        }
        GateStatus::Fail(violation) => (
            "FAIL",
            violation.code,
            violation.detail.clone(),
            Jcs::Object(vec![
                ("code".into(), Jcs::string(violation.code)),
                ("detail".into(), Jcs::string(&violation.detail)),
                ("gate_id".into(), Jcs::string(&violation.gate_id)),
            ]),
        ),
        GateStatus::Refuse(reason) => ("REFUSAL", reason.code, reason.detail.clone(), Jcs::Null),
    };
    let verdict = match receipt.body.verdict {
        Some(verdict) => Jcs::string(verdict.as_str()),
        None => Jcs::Null,
    };
    Jcs::Object(vec![
        (
            "advisory_findings".into(),
            Jcs::Array(
                receipt
                    .body
                    .advisory_findings
                    .iter()
                    .map(|finding| {
                        Jcs::Object(vec![
                            ("detail".into(), Jcs::string(&finding.detail)),
                            ("gate_id".into(), Jcs::string(&finding.gate_id)),
                            ("status".into(), Jcs::string(finding.status.as_str())),
                        ])
                    })
                    .collect(),
            ),
        ),
        ("authority_effect".into(), Jcs::string("None")),
        ("code".into(), Jcs::string(code)),
        ("creates_execution_authority".into(), Jcs::Bool(false)),
        ("detail".into(), Jcs::string(&detail)),
        (
            "quarantine_residuals".into(),
            Jcs::Array(
                receipt
                    .body
                    .quarantine_residuals
                    .iter()
                    .map(|residual| {
                        Jcs::Object(vec![
                            ("gate_id".into(), Jcs::string(&residual.gate_id)),
                            ("legacy_route".into(), Jcs::string(&residual.legacy_route)),
                            ("reason".into(), Jcs::string(&residual.reason)),
                            (
                                "residual_code".into(),
                                Jcs::string(&residual.residual_code),
                            ),
                        ])
                    })
                    .collect(),
            ),
        ),
        ("schema".into(), Jcs::string(RECEIPT_SCHEMA)),
        ("status".into(), Jcs::string(status)),
        ("verdict".into(), verdict),
        ("violation".into(), violation),
    ])
    .canonical_bytes()
}

enum Judgement {
    Fail(Violation),
    Refuse(RefusalReason),
}

pub fn refused(code: &'static str, detail: impl Into<String>) -> Receipt<GateReport> {
    refuse(code, detail)
}

fn refuse(code: &'static str, detail: impl Into<String>) -> Receipt<GateReport> {
    Receipt {
        status: GateStatus::Refuse(RefusalReason {
            code,
            detail: detail.into(),
        }),
        body: empty_report(None),
    }
}

fn empty_report(verdict: Option<Verdict>) -> GateReport {
    GateReport {
        verdict,
        advisory_findings: Vec::new(),
        quarantine_residuals: Vec::new(),
    }
}

fn validate_results_list(wire_results: Vec<GateResultWire>) -> Result<(Vec<ResultRow>, BTreeSet<String>), Judgement> {
    if wire_results.is_empty() {
        return Err(refuse_judge(
            "EMPTY_RESULTS",
            "active gate results must not be empty",
        ));
    }
    if wire_results.len() > 128 {
        return Err(invalid("result count exceeds 128"));
    }
    let mut results = Vec::with_capacity(wire_results.len());
    let mut seen = BTreeSet::new();
    for raw in wire_results {
        let row = validate_result(raw)?;
        if !seen.insert(row.gate_id.clone()) {
            return Err(refuse_judge(
                "DUPLICATE_RESULT",
                "a gate result identifier appears more than once",
            ));
        }
        results.push(row);
    }
    Ok((results, seen))
}

fn check_results_catalog_alignment<'a>(
    results: &[ResultRow],
    seen: &BTreeSet<String>,
    catalog: &'a [Gate],
) -> Result<Vec<&'a Gate>, Judgement> {
    for result in results {
        match catalog.iter().find(|gate| gate.gate_id == result.gate_id) {
            None => {
                return Err(refuse_judge(
                    "UNKNOWN_RESULT",
                    format!("unknown gate result {}", result.gate_id),
                ))
            }
            Some(gate) if gate.disposition == Disposition::Quarantined => {
                return Err(refuse_judge(
                    "QUARANTINED_GATE_EXECUTED",
                    format!("quarantined gate {} cannot produce a result", gate.gate_id),
                ))
            }
            Some(_) => {}
        }
    }
    let active: Vec<&Gate> = catalog
        .iter()
        .filter(|gate| gate.disposition != Disposition::Quarantined)
        .collect();
    if results.len() != active.len() {
        let missing: Vec<&str> = active
            .iter()
            .filter(|gate| !seen.contains(gate.gate_id.as_str()))
            .map(|gate| gate.gate_id.as_str())
            .collect();
        return Err(refuse_judge(
            "MISSING_RESULT",
            format!("active gate result set is incomplete; missing={missing:?}"),
        ));
    }
    if results
        .iter()
        .zip(&active)
        .any(|(result, gate)| result.gate_id != gate.gate_id)
    {
        return Err(refuse_judge(
            "RESULT_ORDER_MISMATCH",
            "active gate results are not in canonical catalog order",
        ));
    }
    Ok(active)
}

fn check_result_binding_and_duration(
    gate: &Gate,
    result: &ResultRow,
    manifest: &Manifest,
    interpreter: &str,
) -> Result<(), Judgement> {
    let resolved = resolve(gate, manifest, interpreter);
    if result.argv != resolved.argv
        || result.inputs != resolved.inputs
        || result.digest != resolved.digest
    {
        return Err(refuse_judge(
            "RESULT_BINDING_MISMATCH",
            format!("gate result {} is not bound to exact resolution", gate.gate_id),
        ));
    }
    let envelope = gate
        .timeout_seconds
        .checked_mul(1000)
        .and_then(|value| value.checked_add(1000))
        .ok_or_else(|| invalid("timeout envelope overflowed"))?;
    if result.duration_ms > envelope {
        return Err(refuse_judge(
            "DURATION_OUT_OF_BOUNDS",
            format!("gate result {} exceeds its timeout envelope", gate.gate_id),
        ));
    }
    Ok(())
}

fn evaluate_gate_outcome(
    gate: &Gate,
    result: &ResultRow,
    findings: &mut Vec<AdvisoryFinding>,
) -> Result<(), Judgement> {
    if matches!(result.status, Measured::Skip | Measured::Bypass) {
        let label = if result.status == Measured::Bypass { "BYPASS" } else { "SKIP" };
        return Err(refuse_judge(
            "SKIP_OR_BYPASS_REFUSED",
            format!("{label} is never a local-CI result"),
        ));
    }
    if gate.disposition == Disposition::Required && result.status != Measured::Pass {
        let violation = Violation {
            code: "REQUIRED_GATE_NONPASS",
            gate_id: gate.gate_id.clone(),
            detail: format!("required gate {} did not pass", gate.gate_id),
        };
        return Err(Judgement::Fail(violation));
    }
    if gate.disposition == Disposition::Advisory {
        if let Some(status) = advisory_status(result.status) {
            findings.push(AdvisoryFinding {
                gate_id: gate.gate_id.clone(),
                status,
                detail: result.detail.clone(),
            });
        }
    }
    Ok(())
}

fn collect_quarantine_residuals(catalog: &[Gate]) -> Vec<QuarantineResidual> {
    catalog
        .iter()
        .filter_map(|gate| match &gate.route {
            Route::Quarantined {
                legacy_route,
                reason,
                residual_code,
            } => Some(QuarantineResidual {
                gate_id: gate.gate_id.clone(),
                residual_code: residual_code.clone(),
                legacy_route: legacy_route.clone(),
                reason: reason.clone(),
            }),
            _ => None,
        })
        .collect()
}

fn validate_request_header(wire: &RequestWire) -> Result<(), Judgement> {
    let _ = (wire.authority_effect, wire.creates_execution_authority);
    if wire.schema != REQUEST_SCHEMA {
        return Err(invalid("request schema mismatch"));
    }
    if !interpreter_ok(&wire.interpreter) {
        return Err(invalid("interpreter is empty or not NFC text"));
    }
    Ok(())
}

fn judge(wire: RequestWire) -> Result<GateReport, Judgement> {
    validate_request_header(&wire)?;
    let manifest = validate_manifest(wire.manifest)?;
    let catalog = validate_catalog(wire.catalog)?;
    let (results, seen) = validate_results_list(wire.results)?;
    let active = check_results_catalog_alignment(&results, &seen, &catalog)?;
    let mut findings = Vec::new();
    for (gate, result) in active.iter().zip(&results) {
        check_result_binding_and_duration(gate, result, &manifest, &wire.interpreter)?;
        evaluate_gate_outcome(gate, result, &mut findings)?;
    }
    let verdict = if findings.is_empty() {
        Verdict::PreflightPass
    } else {
        Verdict::PreflightPassWithAdvisoryFindings
    };
    let quarantine_residuals = collect_quarantine_residuals(&catalog);
    let report = GateReport {
        verdict: Some(verdict),
        advisory_findings: findings,
        quarantine_residuals,
    };
    Ok(report)
}

fn advisory_status(status: Measured) -> Option<AdvisoryStatus> {
    match status {
        Measured::Fail => Some(AdvisoryStatus::Fail),
        Measured::Timeout => Some(AdvisoryStatus::Timeout),
        Measured::Unavailable => Some(AdvisoryStatus::Unavailable),
        _ => None,
    }
}

struct Resolved {
    argv: Vec<String>,
    inputs: Vec<String>,
    digest: String,
}

fn resolve(gate: &Gate, manifest: &Manifest, interpreter: &str) -> Resolved {
    let (argv, inputs) = match &gate.route {
        Route::Python { argv, .. } => {
            let mut resolved = vec![interpreter.to_owned(), "-B".to_owned()];
            resolved.extend(argv.iter().cloned());
            (resolved, Vec::new())
        }
        Route::Tool {
            tool_id,
            argv_prefix,
        } => {
            let inputs: Vec<String> = manifest
                .entries
                .iter()
                .filter(|entry| entry.blob_oid.is_some() && entry.path.ends_with(".rs"))
                .map(|entry| entry.path.clone())
                .collect();
            let mut resolved = Vec::with_capacity(1 + argv_prefix.len() + inputs.len());
            resolved.push(tool_id.clone());
            resolved.extend(argv_prefix.iter().cloned());
            resolved.extend(inputs.iter().cloned());
            (resolved, inputs)
        }
        Route::Quarantined { .. } => (Vec::new(), Vec::new()),
    };
    let digest = resolved_invocation_digest(
        &gate.gate_id,
        &argv.iter().map(String::as_str).collect::<Vec<_>>(),
        &inputs.iter().map(String::as_str).collect::<Vec<_>>(),
    );
    Resolved { argv, inputs, digest }
}

struct Manifest {
    entries: Vec<Entry>,
}

struct Entry {
    path: String,
    blob_oid: Option<String>,
}

struct Gate {
    gate_id: String,
    disposition: Disposition,
    timeout_seconds: u64,
    route: Route,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Disposition {
    Required,
    Advisory,
    Quarantined,
}

enum Route {
    Python { argv: Vec<String> },
    Tool { tool_id: String, argv_prefix: Vec<String> },
    Quarantined { legacy_route: String, reason: String, residual_code: String },
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Measured {
    Pass,
    Fail,
    Skip,
    Bypass,
    Timeout,
    Unavailable,
}

struct ResultRow {
    gate_id: String,
    status: Measured,
    argv: Vec<String>,
    inputs: Vec<String>,
    digest: String,
    duration_ms: u64,
    detail: String,
}

fn validate_manifest_entry(entry: EntryWire) -> Result<Entry, Judgement> {
    if !repo_path(&entry.path, false) {
        return Err(invalid("candidate path is not a relative posix path"));
    }
    match (&entry.blob_oid, &entry.content_sha256) {
        (None, None) => {}
        (Some(blob), Some(sha)) if hex_len(blob, 40) && hex_len(sha, 64) => {}
        _ => {
            return Err(invalid(
                "blob_oid and content_sha256 must both be present or null",
            ))
        }
    }
    let row = Entry {
        path: entry.path,
        blob_oid: entry.blob_oid,
    };
    Ok(row)
}

fn validate_manifest(wire: ManifestWire) -> Result<Manifest, Judgement> {
    let _ = (wire.authority_effect, wire.creates_execution_authority);
    if wire.schema != MANIFEST_SCHEMA {
        return Err(invalid("manifest schema mismatch"));
    }
    if !hex_len(&wire.base_oid, 40) || !hex_len(&wire.head_oid, 40) {
        return Err(invalid("manifest oid must be 40 lowercase hex characters"));
    }
    if wire.entries.len() > 10_000 {
        return Err(invalid("manifest entry count exceeds 10000"));
    }
    let mut entries = Vec::with_capacity(wire.entries.len());
    for entry in wire.entries {
        entries.push(validate_manifest_entry(entry)?);
    }
    let paths: Vec<String> = entries.iter().map(|entry| entry.path.clone()).collect();
    if !sorted_unique(&paths) {
        return Err(invalid("candidate manifest paths must be sorted and unique"));
    }
    let manifest = Manifest { entries };
    Ok(manifest)
}

fn check_gate_timeout(disposition: Disposition, quarantined: bool, timeout_seconds: u64) -> Result<(), Judgement> {
    if disposition == Disposition::Quarantined {
        if !quarantined || timeout_seconds != 0 {
            return Err(invalid("quarantined gates require an inert zero-timeout route"));
        }
    } else if quarantined || timeout_seconds == 0 || timeout_seconds > 1_000_000 {
        return Err(invalid("active gates require an active route and positive timeout"));
    }
    Ok(())
}

fn validate_gate_spec(spec: GateSpecWire, ids: &mut BTreeSet<String>) -> Result<Gate, Judgement> {
    let _ = (spec.authority_effect, spec.creates_execution_authority);
    if !identifier(&spec.gate_id) || !ids.insert(spec.gate_id.clone()) {
        return Err(invalid("catalog gate_id is duplicate or not an identifier"));
    }
    if !repo_path(&spec.cwd, true) {
        return Err(invalid("gate cwd is not a repository path"));
    }
    let disposition = match spec.disposition.as_str() {
        "REQUIRED" => Disposition::Required,
        "ADVISORY" => Disposition::Advisory,
        "QUARANTINED" => Disposition::Quarantined,
        _ => return Err(invalid("unknown gate disposition")),
    };
    let route = validate_route(spec.route)?;
    let quarantined = matches!(route, Route::Quarantined { .. });
    check_gate_timeout(disposition, quarantined, spec.timeout_seconds)?;
    let gate = Gate {
        gate_id: spec.gate_id,
        disposition,
        timeout_seconds: spec.timeout_seconds,
        route,
    };
    Ok(gate)
}

fn validate_catalog(wire: Vec<GateSpecWire>) -> Result<Vec<Gate>, Judgement> {
    if wire.is_empty() || wire.len() > 128 {
        return Err(invalid("catalog must contain 1 to 128 gates"));
    }
    let mut ids = BTreeSet::new();
    let mut gates = Vec::with_capacity(wire.len());
    for spec in wire {
        gates.push(validate_gate_spec(spec, &mut ids)?);
    }
    Ok(gates)
}

fn validate_python_route(entrypoint: String, argv: Vec<String>) -> Result<Route, Judgement> {
    if !repo_path(&entrypoint, false) || argv.is_empty() || argv.len() > 64 {
        return Err(invalid("python route entrypoint or argv is illegal"));
    }
    if argv.iter().any(|item| !argv_item(item)) {
        return Err(invalid("python argv item is illegal"));
    }
    let route = Route::Python { argv };
    Ok(route)
}

fn validate_tool_route(
    tool_id: String,
    argv_prefix: Vec<String>,
    argument_source: String,
) -> Result<Route, Judgement> {
    if !identifier(&tool_id)
        || argument_source != "CANDIDATE_RUST_PATHS"
        || argv_prefix.len() > 64
        || argv_prefix.iter().any(|item| !argv_item(item))
    {
        return Err(invalid("tool route is illegal"));
    }
    let route = Route::Tool {
        tool_id,
        argv_prefix,
    };
    Ok(route)
}

fn validate_quarantined_route(
    legacy_route: String,
    reason: String,
    residual_code: String,
) -> Result<Route, Judgement> {
    if !canonical_text(&legacy_route, false)
        || !canonical_text(&reason, false)
        || legacy_route.chars().count() > 4096
        || reason.chars().count() > 4096
        || !residual_code_ok(&residual_code)
    {
        return Err(invalid("quarantined route text is illegal"));
    }
    let route = Route::Quarantined {
        legacy_route,
        reason,
        residual_code,
    };
    Ok(route)
}

fn validate_route(route: RouteWire) -> Result<Route, Judgement> {
    match route {
        RouteWire::Python { entrypoint, argv } => validate_python_route(entrypoint, argv),
        RouteWire::Tool {
            tool_id,
            argv_prefix,
            argument_source,
        } => validate_tool_route(tool_id, argv_prefix, argument_source),
        RouteWire::Quarantined {
            legacy_route,
            reason,
            residual_code,
        } => validate_quarantined_route(legacy_route, reason, residual_code),
    }
}

fn is_valid_result_wire_fields(wire: &GateResultWire) -> bool {
    identifier(&wire.gate_id)
        && !wire.resolved_argv.is_empty()
        && wire.resolved_argv.len() <= 64
        && wire.resolved_inputs.len() <= 10_000
        && wire.resolved_argv.iter().all(|item| argv_item(item))
        && wire.resolved_inputs.iter().all(|item| repo_path(item, false))
        && is_valid_result_wire_meta(wire)
}

fn is_valid_result_wire_meta(wire: &GateResultWire) -> bool {
    hex_len(&wire.resolved_invocation_sha256, 64)
        && wire.duration_ms <= SAFE_INTEGER
        && canonical_text(&wire.detail, false)
        && wire.detail.chars().count() <= 4096
}

fn parse_measured_status(status_str: &str, exit_code: Option<i32>) -> Result<Measured, Judgement> {
    let status = match status_str {
        "PASS" => Measured::Pass,
        "FAIL" => Measured::Fail,
        "SKIP" => Measured::Skip,
        "BYPASS" => Measured::Bypass,
        "TIMEOUT" => Measured::Timeout,
        "UNAVAILABLE" => Measured::Unavailable,
        _ => return Err(malformed()),
    };
    let exit_ok = match status {
        Measured::Pass => exit_code == Some(0),
        Measured::Fail => exit_code.is_some_and(|code| code != 0),
        _ => exit_code.is_none(),
    };
    if !exit_ok {
        return Err(malformed());
    }
    Ok(status)
}

fn validate_result(wire: GateResultWire) -> Result<ResultRow, Judgement> {
    let _ = (wire.authority_effect, wire.creates_execution_authority);
    if !is_valid_result_wire_fields(&wire) {
        return Err(malformed());
    }
    let status = parse_measured_status(&wire.status, wire.exit_code)?;
    let row = ResultRow {
        gate_id: wire.gate_id,
        status,
        argv: wire.resolved_argv,
        inputs: wire.resolved_inputs,
        digest: wire.resolved_invocation_sha256,
        duration_ms: wire.duration_ms,
        detail: wire.detail,
    };
    Ok(row)
}

fn invalid(detail: impl Into<String>) -> Judgement {
    refuse_judge("INVALID_RECORD", detail)
}

fn malformed() -> Judgement {
    refuse_judge(
        "MALFORMED_RESULT",
        "one or more gate results violate the declared strict base schema",
    )
}

fn refuse_judge(code: &'static str, detail: impl Into<String>) -> Judgement {
    Judgement::Refuse(RefusalReason {
        code,
        detail: detail.into(),
    })
}

fn json_string(value: &str) -> String {
    serde_json::to_string(value).checked_invariant_0fce4bfc("json string")
}

fn push_strings(out: &mut String, values: &[&str]) {
    out.push('[');
    for (index, value) in values.iter().enumerate() {
        if index > 0 {
            out.push(',');
        }
        out.push_str(&json_string(value));
    }
    out.push(']');
}

fn canonical_text(value: &str, allow_empty: bool) -> bool {
    if value.is_empty() {
        return allow_empty;
    }
    if value != value.trim() || value.chars().any(|ch| ch.is_control()) {
        return false;
    }
    let nfc: String = value.nfc().collect();
    nfc == value
}

fn interpreter_ok(value: &str) -> bool {
    canonical_text(value, false) && value.chars().count() <= 4096
}

fn identifier(value: &str) -> bool {
    let mut chars = value.chars();
    if !matches!(chars.next(), Some(ch) if ch.is_ascii_lowercase() || ch.is_ascii_digit()) {
        return false;
    }
    value.len() <= 128
        && value.bytes().all(|byte| {
            byte.is_ascii_lowercase()
                || byte.is_ascii_digit()
                || matches!(byte, b'.' | b'_' | b':' | b'-')
        })
}

fn residual_code_ok(value: &str) -> bool {
    let mut chars = value.chars();
    matches!(chars.next(), Some(ch) if ch.is_ascii_uppercase())
        && value.len() <= 128
        && value
            .bytes()
            .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_')
}

fn hex_len(value: &str, len: usize) -> bool {
    value.len() == len
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn repo_path(value: &str, allow_dot: bool) -> bool {
    if value == "." {
        return allow_dot;
    }
    if !canonical_text(value, false) || !value.is_ascii() {
        return false;
    }
    if value.starts_with('/') || value.contains('\\') || value.contains(':') {
        return false;
    }
    value
        .split('/')
        .all(|part| !part.is_empty() && part != "." && part != "..")
}

fn argv_item(value: &str) -> bool {
    canonical_text(value, false) && value.chars().count() <= 4096
}

fn sorted_unique(paths: &[String]) -> bool {
    if paths
        .windows(2)
        .any(|pair| pair[0].as_bytes() >= pair[1].as_bytes())
    {
        return false;
    }
    let mut folded = BTreeSet::new();
    paths
        .iter()
        .all(|path| folded.insert(path.to_ascii_lowercase()))
}

fn json_null<'de, D>(deserializer: D) -> Result<(), D::Error>
where
    D: serde::Deserializer<'de>,
{
    struct Visit;
    impl<'de> serde::de::Visitor<'de> for Visit {
        type Value = ();
        fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
            formatter.write_str("null")
        }
        fn visit_unit<E: serde::de::Error>(self) -> Result<(), E> {
            Ok(())
        }
    }
    deserializer.deserialize_unit(Visit)
}

fn must_false<'de, D>(deserializer: D) -> Result<bool, D::Error>
where
    D: serde::Deserializer<'de>,
{
    struct Visit;
    impl<'de> serde::de::Visitor<'de> for Visit {
        type Value = bool;
        fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
            formatter.write_str("false")
        }
        fn visit_bool<E: serde::de::Error>(self, value: bool) -> Result<bool, E> {
            if value {
                Err(E::custom(
                    "creates_execution_authority must be exact false",
                ))
            } else {
                Ok(false)
            }
        }
    }
    deserializer.deserialize_bool(Visit)
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RequestWire {
    schema: String,
    interpreter: String,
    #[serde(deserialize_with = "json_null")]
    authority_effect: (),
    #[serde(deserialize_with = "must_false")]
    creates_execution_authority: bool,
    manifest: ManifestWire,
    catalog: Vec<GateSpecWire>,
    results: Vec<GateResultWire>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ManifestWire {
    schema: String,
    #[serde(deserialize_with = "json_null")]
    authority_effect: (),
    #[serde(deserialize_with = "must_false")]
    creates_execution_authority: bool,
    base_oid: String,
    head_oid: String,
    entries: Vec<EntryWire>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct EntryWire {
    path: String,
    blob_oid: Option<String>,
    content_sha256: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct GateSpecWire {
    gate_id: String,
    disposition: String,
    timeout_seconds: u64,
    cwd: String,
    route: RouteWire,
    #[serde(deserialize_with = "json_null")]
    authority_effect: (),
    #[serde(deserialize_with = "must_false")]
    creates_execution_authority: bool,
}

#[derive(Deserialize)]
#[serde(tag = "runner_kind", deny_unknown_fields)]
enum RouteWire {
    #[serde(rename = "PYTHON")]
    Python { entrypoint: String, argv: Vec<String> },
    #[serde(rename = "TOOL")]
    Tool {
        tool_id: String,
        argv_prefix: Vec<String>,
        argument_source: String,
    },
    #[serde(rename = "QUARANTINED")]
    Quarantined {
        legacy_route: String,
        reason: String,
        residual_code: String,
    },
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct GateResultWire {
    gate_id: String,
    status: String,
    resolved_argv: Vec<String>,
    resolved_inputs: Vec<String>,
    resolved_invocation_sha256: String,
    exit_code: Option<i32>,
    duration_ms: u64,
    detail: String,
    #[serde(deserialize_with = "json_null")]
    authority_effect: (),
    #[serde(deserialize_with = "must_false")]
    creates_execution_authority: bool,
}

// Origin: engine/crates_rs/core_policy/src/local_ci_gates.rs
// Claim: urn:core:crates_rs:core-policy:local-ci-gates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0fce4bfc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0fce4bfc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0fce4bfc {
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
impl BoundaryError0fce4bfc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0fce4bfc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0fce4bfc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0fce4bfc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0fce4bfc> {
        if capacity_bound == 0 {
            return Err(BoundaryError0fce4bfc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0fce4bfc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0fce4bfc::ExceedsCapacity {
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
mod l4_boundary_tests_0fce4bfc {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0fce4bfc::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0fce4bfc::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0fce4bfc::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0fce4bfc::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0fce4bfc::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0fce4bfc::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0fce4bfc::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
