//! The JSON entry points a workflow calls. Text in, one typed outcome out; no file is touched here.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:host:v1

use std::collections::{BTreeMap, BTreeSet};

use core_operad_canon::render::SCHEMA_VERSION;
use core_operad_canon::DdcOp;
use serde::{Deserialize, Serialize};
use serde_json::Value as Json;

use crate::envelope::{envelope, typing};
use crate::grounding::grounding;
use crate::judge::judge;
use crate::laws::{run_battery, Panel};
use crate::learning::{trial, witness};
use crate::ledger::{Ledger, Record};
use crate::loading::{load, loaded};
use crate::mining::{mining, reuse};
use crate::running::run;
use crate::term::{Body, Colour, Operation, Term, Value, Variant};
use crate::turns::{trial_turns, witness_turn};
use crate::Refusal;

/// An operation as a workflow writes it. Colours are names in the request's `colour_type`.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OperationWire {
    pub id: String,
    pub sources: Vec<String>,
    pub target: String,
    #[serde(default)]
    pub body: Option<Body>,
    #[serde(default)]
    pub variant: Option<Variant>,
    #[serde(default)]
    pub cost: u64,
}

impl OperationWire {
    pub(crate) fn build(&self, colour_type: &str) -> Result<Operation, Refusal> {
        let sources: Result<Vec<Colour>, Refusal> = self
            .sources
            .iter()
            .map(|name| Colour::new(colour_type, name))
            .collect();
        Operation::new(
            &self.id,
            sources?,
            Colour::new(colour_type, &self.target)?,
            self.body.unwrap_or(Body::Opaque),
            self.variant.unwrap_or(Variant::Planar),
            self.cost,
        )
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct LawsRequest {
    colour_type: String,
    operations: Vec<OperationWire>,
    panel: BTreeMap<String, Vec<Value>>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct MoveWire {
    id: String,
    op: String,
    #[serde(default)]
    operad_id: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CheckWire {
    operation: String,
    inputs: Vec<Value>,
    expected: Value,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CandidateRequest {
    colour_type: String,
    operations: Vec<OperationWire>,
    #[serde(default)]
    ddc_moves: Vec<MoveWire>,
    #[serde(default)]
    checks: Vec<CheckWire>,
}

/// One thing wrong with a candidate, and what it is about.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Finding {
    pub code: &'static str,
    /// What `subject` names: `operation` or `ddc_move`.
    pub scope: &'static str,
    pub subject: String,
    pub message: String,
}

/// What the host established about one proposed operation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Disposition {
    /// It has a body and every host check of it passed (at least one).
    HostVerified,
    /// It is well typed, but the host ran nothing against it.
    UnverifiedCandidate,
    /// It is ill typed, or a host check of it failed.
    Refused,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct OperationStatus {
    pub id: String,
    pub disposition: Disposition,
}

/// The host's reading of a model's operad candidates and DDC moves.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CandidateReport {
    pub accepted: bool,
    pub operations: Vec<OperationStatus>,
    pub ddc_trace: String,
    pub findings: Vec<Finding>,
}

/// One request to the host.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Command {
    Laws(String),
    Check(String),
    LedgerVerify(String),
    LedgerAdmitted(String),
    LedgerAppend { ledger: String, record: String },
    LedgerLoad { ledger: String, request: String },
    LedgerLoaded { ledger: String, request: String },
    LedgerTrial { ledger: String, request: String },
    Envelope(String),
    Judge(String),
    Mining(String),
    Typing(String),
    Grounding(String),
    Reuse(String),
    Witness(String),
    Trial(String),
    WitnessTurn(String),
    Run(String),
    Version,
}

/// The host's answer. `Fail` means the check ran and did not hold; `Refused` means it could not run.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(tag = "status", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Outcome {
    Pass { result: Json },
    Fail { result: Json },
    Refused { refusal: Refusal },
}

fn parse<'a, T: Deserialize<'a>>(text: &'a str) -> Result<T, Refusal> {
    serde_json::from_str(text).map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))
}

fn encode<T: Serialize>(value: &T) -> Result<Json, Refusal> {
    serde_json::to_value(value).map_err(|error| Refusal::new("ENCODING", error.to_string()))
}

const OPERATION: &str = "operation";
const DDC_MOVE: &str = "ddc_move";

fn finding(
    code: &'static str,
    scope: &'static str,
    subject: &str,
    message: impl Into<String>,
) -> Finding {
    Finding {
        code,
        scope,
        subject: subject.to_owned(),
        message: message.into(),
    }
}

/// Type every operation, run the law battery on the request's panel.
pub fn laws(text: &str) -> Result<crate::laws::LawReport, Refusal> {
    let request: LawsRequest = parse(text)?;
    let operations: Result<Vec<Operation>, Refusal> = request
        .operations
        .iter()
        .map(|wire| wire.build(&request.colour_type))
        .collect();
    let mut panel = Panel::default();
    for (name, samples) in request.panel {
        panel.insert(Colour::new(&request.colour_type, &name)?, samples);
    }
    run_battery(&operations?, &panel)
}

fn typed_operations(
    request: &CandidateRequest,
    findings: &mut Vec<Finding>,
) -> BTreeMap<String, Operation> {
    let mut typed = BTreeMap::new();
    let mut seen = BTreeSet::new();
    for wire in &request.operations {
        if !seen.insert(wire.id.as_str()) {
            findings.push(finding(
                "DUPLICATE_OPERATION",
                OPERATION,
                &wire.id,
                "the id is used twice",
            ));
            typed.remove(&wire.id);
            continue;
        }
        match wire.build(&request.colour_type) {
            Ok(operation) => {
                typed.insert(wire.id.clone(), operation);
            }
            Err(refusal) => {
                findings.push(finding(refusal.code, OPERATION, &wire.id, refusal.message))
            }
        }
    }
    typed
}

fn read_moves(
    request: &CandidateRequest,
    known: &BTreeMap<String, Operation>,
    findings: &mut Vec<Finding>,
) -> String {
    let mut trace = String::new();
    let mut seen = BTreeSet::new();
    for step in &request.ddc_moves {
        if !seen.insert(step.id.as_str()) {
            findings.push(finding(
                "DUPLICATE_DDC_MOVE",
                DDC_MOVE,
                &step.id,
                "the id is used twice",
            ));
        }
        if DdcOp::LETTERS.contains(&step.op.as_str()) {
            trace.push_str(&step.op);
        } else {
            findings.push(finding(
                "UNKNOWN_DDC_LETTER",
                DDC_MOVE,
                &step.id,
                format!("{} is not a DDC letter", step.op),
            ));
        }
        if step
            .operad_id
            .as_ref()
            .is_some_and(|id| !known.contains_key(id))
        {
            findings.push(finding(
                "UNKNOWN_OPERATION",
                DDC_MOVE,
                &step.id,
                "the move names an operation that is not well typed here",
            ));
        }
    }
    trace
}

/// The operations with at least one host check, after every check has run.
fn run_checks(
    request: &CandidateRequest,
    known: &BTreeMap<String, Operation>,
    findings: &mut Vec<Finding>,
) -> BTreeSet<String> {
    let mut checked = BTreeSet::new();
    for check in &request.checks {
        let Some(operation) = known.get(&check.operation) else {
            findings.push(finding(
                "UNKNOWN_OPERATION",
                OPERATION,
                &check.operation,
                "a check names an operation that is not well typed here",
            ));
            continue;
        };
        checked.insert(check.operation.clone());
        match Term::corolla(operation).eval(&check.inputs) {
            Ok(value) if value == check.expected => {}
            Ok(value) => findings.push(finding(
                "CHECK_FAILED",
                OPERATION,
                &check.operation,
                format!(
                    "on {:?} the host computed {value:?}, not {:?}",
                    check.inputs, check.expected
                ),
            )),
            Err(refusal) => findings.push(finding(
                refusal.code,
                OPERATION,
                &check.operation,
                refusal.message,
            )),
        }
    }
    checked
}

/// Type a model's operad candidates against the canon and run the host's checks of them.
pub fn check(text: &str) -> Result<CandidateReport, Refusal> {
    let request: CandidateRequest = parse(text)?;
    let mut findings = Vec::new();
    let typed = typed_operations(&request, &mut findings);
    let ddc_trace = read_moves(&request, &typed, &mut findings);
    let checked = run_checks(&request, &typed, &mut findings);
    let blamed: BTreeSet<&str> = findings
        .iter()
        .filter(|found| found.scope == OPERATION)
        .map(|found| found.subject.as_str())
        .collect();
    let mut listed = BTreeSet::new();
    let operations = request
        .operations
        .iter()
        .filter(|wire| listed.insert(wire.id.as_str()))
        .map(|wire| OperationStatus {
            id: wire.id.clone(),
            disposition: match typed.get(&wire.id) {
                Some(_) if blamed.contains(wire.id.as_str()) => Disposition::Refused,
                Some(operation)
                    if operation.body() != Body::Opaque && checked.contains(&wire.id) =>
                {
                    Disposition::HostVerified
                }
                Some(_) => Disposition::UnverifiedCandidate,
                None => Disposition::Refused,
            },
        })
        .collect();
    Ok(CandidateReport {
        accepted: findings.is_empty(),
        operations,
        ddc_trace,
        findings,
    })
}

fn verdict<T: Serialize>(holds: bool, report: &T) -> Result<(bool, Json), Refusal> {
    Ok((holds, encode(report)?))
}

fn appended(ledger: &str, record: &str) -> Result<(bool, Json), Refusal> {
    let mut ledger = Ledger::from_lines(ledger)?;
    let record: Record = parse(record)?;
    verdict(true, ledger.append(record)?)
}

/// Which host and which canon this is; a workflow binds every run to it.
fn version() -> Json {
    serde_json::json!({
        "name": env!("CARGO_PKG_NAME"),
        "version": env!("CARGO_PKG_VERSION"),
        "canon": SCHEMA_VERSION,
    })
}

fn answer(command: &Command) -> Result<(bool, Json), Refusal> {
    match command {
        Command::Laws(text) => laws(text).and_then(|report| verdict(report.holds(), &report)),
        Command::Check(text) => check(text).and_then(|report| verdict(report.accepted, &report)),
        Command::Envelope(text) => {
            envelope(text).and_then(|report| verdict(report.accepted, &report))
        }
        Command::Judge(text) => judge(text).and_then(|found| verdict(found.accepted, &found)),
        Command::Mining(text) => mining(text).and_then(|report| verdict(report.accepted, &report)),
        Command::Typing(text) => typing(text).and_then(|report| verdict(true, &report)),
        Command::Grounding(text) => {
            grounding(text).and_then(|report| verdict(report.valid, &report))
        }
        Command::Reuse(text) => reuse(text).and_then(|report| verdict(true, &report)),
        Command::Witness(text) => witness(text).and_then(|found| verdict(true, &found)),
        Command::Trial(text) => trial(text).and_then(|scored| verdict(true, &scored)),
        Command::WitnessTurn(text) => witness_turn(text).and_then(|found| verdict(true, &found)),
        Command::Run(text) => run(text).and_then(|report| verdict(report.accepted, &report)),
        Command::LedgerVerify(text) => Ledger::from_lines(text).map(|ledger| {
            (
                true,
                serde_json::json!({ "entries": ledger.entries().len() }),
            )
        }),
        Command::LedgerAdmitted(text) => {
            Ledger::from_lines(text).and_then(|ledger| verdict(true, &ledger.admitted()))
        }
        Command::LedgerAppend { ledger, record } => appended(ledger, record),
        Command::LedgerLoad { ledger, request } => {
            load(ledger, request).and_then(|seed| verdict(true, &seed))
        }
        Command::LedgerLoaded { ledger, request } => {
            loaded(ledger, request).and_then(|check| verdict(check.accepted, &check))
        }
        Command::LedgerTrial { ledger, request } => {
            trial_turns(ledger, request).and_then(|scored| verdict(true, &scored))
        }
        Command::Version => Ok((true, version())),
    }
}

/// Answer one request. For `LedgerAppend` the result is the entry to add to the file as one line.
pub fn respond(command: &Command) -> Outcome {
    match answer(command) {
        Ok((true, result)) => Outcome::Pass { result },
        Ok((false, result)) => Outcome::Fail { result },
        Err(refusal) => Outcome::Refused { refusal },
    }
}
