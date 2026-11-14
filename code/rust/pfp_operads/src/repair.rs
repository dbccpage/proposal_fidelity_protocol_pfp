//! Bounded code repair: one supplied patch, fixed checks, six stages, one record.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:repair:v1
//!
//! A request fixes an objective, the SHA-256 of every source file, the files a patch may change,
//! the patch and the check commands. The host then runs six stages in order:
//!
//! * `C` capture: read the declared sources, compare their hashes, make a working copy.
//! * `R` observe: run every check on the working copy for a baseline.
//! * `E` evaluate: apply the patch to the working copy and run the same checks again.
//! * `I` incorporate: decide whether the candidate is at fault, for the failure ledger.
//! * `M` disposition: compare the two sets of failing checks.
//! * `T` terminal: confirm the original sources still have the declared hashes.
//!
//! The letters name the stages of this slice. They are spelled like DDC letters and are not the
//! calculus: no descent law is claimed for the word. The original sources are never written, and
//! `REPAIRED` is a statement about the supplied checks only.
//!
//! Everything that touches a file or starts a process goes through [`Bench`], so the decisions here
//! can be tested without either. [`crate::workshop`] is the bench the `pfp_operad` binary uses.

use std::collections::{BTreeMap, BTreeSet};

use regex::Regex;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::host::Outcome;
use crate::ledger::Record;
use crate::patch::{self, FilePatch};
use crate::Refusal;

/// The six stages, in order, with the name of each.
pub const STAGES: [(&str, &str); 6] = [
    ("C", "capture"),
    ("R", "observe"),
    ("E", "evaluate"),
    ("I", "incorporate"),
    ("M", "disposition"),
    ("T", "terminal"),
];
/// The files kept in the run folder beside the working copy.
pub const REQUEST_FILE: &str = "request.json";
pub const PATCH_FILE: &str = "candidate.patch";
pub const RECORD_FILE: &str = "record.json";

/// Canon failure class of a patch that left a declared failing check failing.
pub const COUNTERFEIT: &str = "CounterfeitExactness";
/// Canon failure class of a patch that broke a check that passed before it.
pub const LEAK: &str = "BoundaryLeakage";
/// Canon failure class of a patch that does not fit the sources or the write set.
pub const MISFIT: &str = "StructuralNonFit";

pub const MAX_SOURCES: usize = 64;
pub const MAX_WRITE_PATHS: usize = 32;
pub const MAX_CHECKS: usize = 16;
pub const MAX_ARGUMENTS: usize = 32;
pub const MAX_TIMEOUT_SECONDS: u32 = 60;
pub const MAX_PATCH_BYTES: usize = 65536;
pub const MAX_OBJECTIVE_CHARS: usize = 2048;

const RUN_KEY: &str = "^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$";
const CHECK_ID: &str = "^[a-z][a-z0-9_-]{0,63}$";
const DEVICES: [&str; 4] = ["CON", "PRN", "AUX", "NUL"];
const CASE_DOMAIN: &str = "pfp.operads.repair.case.v1";
const REQUEST_DOMAIN: &str = "pfp.operads.repair.request.v1";
const EVIDENCE_DOMAIN: &str = "pfp.operads.repair.evidence.v1";

fn refuse<T>(code: &'static str, message: impl Into<String>) -> Result<T, Refusal> {
    Err(Refusal::new(code, message))
}

fn sha256(parts: &[&[u8]]) -> String {
    let mut hasher = Sha256::new();
    for part in parts {
        hasher.update(part);
    }
    hex::encode(hasher.finalize())
}

fn encoded<T: Serialize>(value: &T) -> Result<Vec<u8>, Refusal> {
    serde_json::to_vec(value).map_err(|error| Refusal::new("ENCODING", error.to_string()))
}

fn matches(pattern: &str, text: &str) -> bool {
    Regex::new(pattern).is_ok_and(|compiled| compiled.is_match(text))
}

fn default_timeout() -> u32 {
    20
}

fn default_workflow() -> String {
    "bounded_repair".to_owned()
}

/// One fixed local command. Exit 0 passes; any other exit fails.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Check {
    pub check_id: String,
    /// The program and its arguments, passed as written. No shell reads them.
    pub argv: Vec<String>,
    #[serde(default = "default_timeout")]
    pub timeout_seconds: u32,
}

/// What a repair run is asked to do. Field order is the order the request digest hashes.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub run_key: String,
    pub objective: String,
    /// Every source file the run may read, by relative path, with its SHA-256 in lowercase hex.
    pub sources: BTreeMap<String, String>,
    /// The sources the patch may change.
    pub write_paths: Vec<String>,
    pub checks: Vec<Check>,
    pub candidate_patch: String,
    /// The workflow named in a failure record.
    #[serde(default = "default_workflow")]
    pub workflow: String,
}

fn device(part: &str) -> bool {
    let stem = part
        .split('.')
        .next()
        .unwrap_or_default()
        .to_ascii_uppercase();
    let numbered = |prefix| {
        stem.strip_prefix(prefix)
            .is_some_and(|rest| matches!(rest.as_bytes(), [b'1'..=b'9']))
    };
    DEVICES.contains(&stem.as_str()) || numbered("COM") || numbered("LPT")
}

/// A relative path of plain names that means the same file on every platform.
pub fn relative_file(path: &str) -> Result<(), Refusal> {
    let odd = path
        .chars()
        .any(|c| matches!(c, '\\' | ':' | '\0' | '\r' | '\n' | '\t'));
    let bad_part = |part: &str| {
        matches!(part, "" | "." | "..")
            || part.eq_ignore_ascii_case(".git")
            || part.ends_with(['.', ' '])
            || device(part)
    };
    if odd || path.split('/').any(bad_part) {
        return refuse(
            "SOURCE_PATH_REFUSED",
            format!("{path:?} is not a plain relative path"),
        );
    }
    Ok(())
}

fn is_sha256(text: &str) -> bool {
    text.len() == 64 && text.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
}

impl Check {
    fn valid(&self) -> Result<(), Refusal> {
        let arguments = (1..=MAX_ARGUMENTS).contains(&self.argv.len())
            && self
                .argv
                .iter()
                .all(|arg| !arg.is_empty() && !arg.contains('\0'));
        if !matches(CHECK_ID, &self.check_id)
            || !arguments
            || !(1..=MAX_TIMEOUT_SECONDS).contains(&self.timeout_seconds)
        {
            return refuse(
                "CHECK_REFUSED",
                format!("check {:?} is not well formed", self.check_id),
            );
        }
        Ok(())
    }
}

impl Request {
    /// Read a request and refuse one that is out of bounds.
    pub fn read(text: &str) -> Result<Self, Refusal> {
        let request: Self = serde_json::from_str(text)
            .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
        request.named()?;
        request.scoped()?;
        request.checks.iter().try_for_each(Check::valid)?;
        Ok(request)
    }

    fn named(&self) -> Result<(), Refusal> {
        if !matches(RUN_KEY, &self.run_key) {
            return refuse(
                "RUN_KEY_REFUSED",
                "a run key is 1 to 80 letters, digits, _ or -",
            );
        }
        let words = [&self.objective, &self.workflow];
        if words
            .iter()
            .any(|text| text.trim().is_empty() || text.chars().count() > MAX_OBJECTIVE_CHARS)
        {
            return refuse(
                "OBJECTIVE_REFUSED",
                "objective and workflow need 1 to 2048 characters",
            );
        }
        if !(1..=MAX_PATCH_BYTES).contains(&self.candidate_patch.len()) {
            return refuse(patch::REFUSED, "a patch is 1 to 65536 bytes");
        }
        Ok(())
    }

    fn scoped(&self) -> Result<(), Refusal> {
        for (name, digest) in &self.sources {
            relative_file(name)?;
            if !is_sha256(digest) {
                return refuse(
                    "SOURCE_DIGEST_REFUSED",
                    format!("{name} needs 64 lowercase hex digits"),
                );
            }
        }
        let folded: BTreeSet<String> = self
            .sources
            .keys()
            .map(|name| name.to_lowercase())
            .collect();
        let writes: BTreeSet<&String> = self.write_paths.iter().collect();
        let checks: BTreeSet<&String> = self.checks.iter().map(|check| &check.check_id).collect();
        let counted = (1..=MAX_SOURCES).contains(&self.sources.len())
            && (1..=MAX_WRITE_PATHS).contains(&self.write_paths.len())
            && (1..=MAX_CHECKS).contains(&self.checks.len());
        let distinct = folded.len() == self.sources.len()
            && writes.len() == self.write_paths.len()
            && checks.len() == self.checks.len();
        if !counted || !distinct || !writes.iter().all(|path| self.sources.contains_key(*path)) {
            return refuse(
                "REPAIR_SCOPE_REFUSED",
                "sources, write paths and checks must be nonempty, bounded and distinct, and every write path a source",
            );
        }
        Ok(())
    }

    /// The identity of the candidate: the SHA-256 of the patch bytes.
    pub fn candidate_id(&self) -> String {
        format!("sha256:{}", sha256(&[self.candidate_patch.as_bytes()]))
    }

    /// The identity of the whole request. The same patch under other sources or checks differs.
    pub fn digest(&self) -> Result<String, Refusal> {
        Ok(format!(
            "sha256:{}",
            sha256(&[REQUEST_DOMAIN.as_bytes(), b"\n", &encoded(self)?])
        ))
    }

    /// The name of the task without its candidate: the sources and the checks.
    pub fn case(&self) -> Result<String, Refusal> {
        let digest = sha256(&[
            CASE_DOMAIN.as_bytes(),
            b"\n",
            &encoded(&self.sources)?,
            b"\n",
            &encoded(&self.checks)?,
        ]);
        Ok(format!("r{}", digest.get(..16).unwrap_or_default()))
    }
}

/// One output stream of a check: the hash of all of it and the start of its text.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize)]
pub struct Stream {
    pub sha256: String,
    pub head: String,
    pub truncated: bool,
}

/// What a check did when the bench ran it.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize)]
pub struct Exit {
    pub code: i32,
    pub stdout: Stream,
    pub stderr: Stream,
}

/// One check's result in a baseline or after the patch.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Observation {
    pub check_id: String,
    #[serde(flatten)]
    pub exit: Exit,
}

/// Every effect a repair run has. A refusal's code is reported as the bench gives it.
pub trait Bench {
    /// The bytes of one declared file in the original source tree.
    fn source(&mut self, path: &str) -> Result<Vec<u8>, Refusal>;
    /// Make the run folder with a working copy of exactly `files`, and keep `kept` beside it.
    fn open(
        &mut self,
        files: &BTreeMap<String, Vec<u8>>,
        kept: &[(&str, Vec<u8>)],
    ) -> Result<(), Refusal>;
    /// The bytes of one file in the working copy.
    fn copy(&mut self, path: &str) -> Result<Vec<u8>, Refusal>;
    /// Replace one file of the working copy.
    fn write(&mut self, path: &str, bytes: &[u8]) -> Result<(), Refusal>;
    /// Run one check in the working copy.
    fn run(&mut self, check: &Check) -> Result<Exit, Refusal>;
    /// Keep one more file in the run folder.
    fn keep(&mut self, name: &str, bytes: &[u8]) -> Result<(), Refusal>;
}

/// How the candidate did against the checks.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Disposition {
    /// Every check that failed now passes, and no other check fails.
    Repaired,
    /// Some failing checks now pass, some still fail, none was broken.
    Partial,
    /// The same checks fail as before.
    Ineffective,
    /// A check that passed before the patch fails after it.
    Regression,
    /// No check failed before the patch, so the patch was not applied.
    NoRepairNeeded,
    /// A stage refused; see the record's refusal.
    Refused,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum StageStatus {
    Done,
    Skipped,
    Refused,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct StageReport {
    pub stage: &'static str,
    pub name: &'static str,
    pub status: StageStatus,
}

/// The first refusal of a run and the stage it came from.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct StageRefusal {
    pub stage: &'static str,
    pub code: &'static str,
    pub message: String,
}

/// The record of one run. The fences at the end are fixed: this slice grants nothing.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Terminal {
    pub run_key: String,
    pub candidate_id: String,
    pub request_digest: String,
    pub case: String,
    /// The letters of the stages that took effect, in order.
    pub trace: String,
    pub stages: Vec<StageReport>,
    pub outcome: Disposition,
    pub refusal: Option<StageRefusal>,
    pub source_manifest: BTreeMap<String, String>,
    /// SHA-256 of each source in the working copy at the end of the run.
    pub working_manifest: BTreeMap<String, String>,
    pub changed_paths: Vec<String>,
    pub baseline: Vec<Observation>,
    pub after: Vec<Observation>,
    /// The record for `ledger append` when the candidate is at fault; otherwise nothing.
    pub failure: Option<Record>,
    /// Whether the original sources had the declared hashes when the run ended.
    pub source_intact: bool,
    pub source_application: &'static str,
    pub admission: &'static str,
    pub production_activation: &'static str,
    pub evidence_scope: &'static str,
    pub mathematical_measurement: &'static str,
    pub authority_effect: &'static str,
}

fn failing(observations: &[Observation]) -> BTreeSet<&str> {
    observations
        .iter()
        .filter(|seen| seen.exit.code != 0)
        .map(|seen| seen.check_id.as_str())
        .collect()
}

/// Compare the checks that failed before the patch with the ones that fail after it.
pub fn assess(refused: bool, baseline: &[Observation], after: &[Observation]) -> Disposition {
    let (before, after) = (failing(baseline), failing(after));
    if refused {
        Disposition::Refused
    } else if before.is_empty() {
        Disposition::NoRepairNeeded
    } else if !after.is_subset(&before) {
        Disposition::Regression
    } else if after.is_empty() {
        Disposition::Repaired
    } else if after.len() < before.len() {
        Disposition::Partial
    } else {
        Disposition::Ineffective
    }
}

enum Ran {
    Done,
    Skipped,
}

struct Run<'a> {
    request: &'a Request,
    bench: &'a mut dyn Bench,
    stages: Vec<StageReport>,
    refusal: Option<StageRefusal>,
    working: BTreeMap<String, String>,
    changed: Vec<String>,
    baseline: Vec<Observation>,
    after: Vec<Observation>,
    fault: Option<&'static str>,
    outcome: Disposition,
    source_intact: bool,
}

type Stage<'a> = fn(&mut Run<'a>) -> Result<Ran, Refusal>;

impl<'a> Run<'a> {
    /// Run one stage. After a refusal only the stages marked `always` still run.
    fn step(&mut self, index: usize, action: Stage<'a>, always: bool) {
        let (stage, name) = STAGES.get(index).copied().unwrap_or_default();
        let status = if self.refusal.is_some() && !always {
            StageStatus::Skipped
        } else {
            match action(self) {
                Ok(Ran::Done) => StageStatus::Done,
                Ok(Ran::Skipped) => StageStatus::Skipped,
                Err(refusal) => {
                    self.refusal.get_or_insert(StageRefusal {
                        stage,
                        code: refusal.code,
                        message: refusal.message,
                    });
                    StageStatus::Refused
                }
            }
        };
        self.stages.push(StageReport {
            stage,
            name,
            status,
        });
    }

    /// The declared sources as they are now, refused unless every hash is the declared one.
    fn sources(&mut self) -> Result<BTreeMap<String, Vec<u8>>, Refusal> {
        let mut files = BTreeMap::new();
        for (name, declared) in &self.request.sources {
            let bytes = self.bench.source(name)?;
            if &sha256(&[&bytes]) != declared {
                return refuse(
                    "SOURCE_CHANGED",
                    format!("{name} does not have its declared hash"),
                );
            }
            files.insert(name.clone(), bytes);
        }
        Ok(files)
    }

    fn copy_intact(&mut self) -> Result<(), Refusal> {
        for (name, expected) in &self.working {
            if &sha256(&[&self.bench.copy(name)?]) != expected {
                return refuse(
                    "WORKING_COPY_CHANGED",
                    format!("{name} changed in the working copy outside the patch"),
                );
            }
        }
        Ok(())
    }

    /// Run every check, with the working copy compared before and after each one.
    fn checks(&mut self) -> Result<Vec<Observation>, Refusal> {
        let mut seen = Vec::new();
        for check in &self.request.checks {
            self.copy_intact()?;
            let exit = self.bench.run(check)?;
            self.copy_intact()?;
            seen.push(Observation {
                check_id: check.check_id.clone(),
                exit,
            });
        }
        Ok(seen)
    }

    fn capture(&mut self) -> Result<Ran, Refusal> {
        let files = self.sources()?;
        let kept = [
            (REQUEST_FILE, encoded(self.request)?),
            (
                PATCH_FILE,
                self.request.candidate_patch.clone().into_bytes(),
            ),
        ];
        self.bench.open(&files, &kept)?;
        self.working = self.request.sources.clone();
        Ok(Ran::Done)
    }

    fn observe(&mut self) -> Result<Ran, Refusal> {
        self.sources()?;
        self.baseline = self.checks()?;
        Ok(Ran::Done)
    }

    /// The patch's edits, refused unless each names a file of the write set.
    fn edits(&self) -> Result<Vec<FilePatch>, Refusal> {
        let edits = patch::parse(&self.request.candidate_patch)?;
        if edits.is_empty() {
            return refuse(patch::SCOPE_REFUSED, "the patch edits no file");
        }
        match edits
            .iter()
            .find(|edit| !self.request.write_paths.contains(&edit.path))
        {
            Some(edit) => refuse(
                patch::SCOPE_REFUSED,
                format!("{} is not in the write set", edit.path),
            ),
            None => Ok(edits),
        }
    }

    fn evaluate(&mut self) -> Result<Ran, Refusal> {
        self.sources()?;
        if failing(&self.baseline).is_empty() {
            return Ok(Ran::Skipped);
        }
        let mut patched = Vec::new();
        for edit in self.edits()? {
            let Ok(text) = String::from_utf8(self.bench.copy(&edit.path)?) else {
                return refuse(patch::REFUSED, format!("{} is not UTF-8 text", edit.path));
            };
            let new = edit.apply(&text)?;
            if new != text {
                patched.push((edit.path, new));
            }
        }
        if patched.is_empty() {
            return refuse(patch::REFUSED, "the patch changes no byte");
        }
        for (path, text) in patched {
            self.bench.write(&path, text.as_bytes())?;
            self.working
                .insert(path.clone(), sha256(&[text.as_bytes()]));
            self.changed.push(path);
        }
        self.after = self.checks()?;
        Ok(Ran::Done)
    }

    /// Whether the candidate itself is at fault, and with which canon failure class.
    fn incorporate(&mut self) -> Result<Ran, Refusal> {
        let patch_refused =
            |refusal: &StageRefusal| [patch::REFUSED, patch::SCOPE_REFUSED].contains(&refusal.code);
        self.fault = match (&self.refusal, assess(false, &self.baseline, &self.after)) {
            (Some(refusal), _) if patch_refused(refusal) => Some(MISFIT),
            (None, Disposition::Regression) => Some(LEAK),
            (None, Disposition::Partial | Disposition::Ineffective) => Some(COUNTERFEIT),
            _ => None,
        };
        Ok(Ran::Done)
    }

    fn dispose(&mut self) -> Result<Ran, Refusal> {
        self.outcome = assess(self.refusal.is_some(), &self.baseline, &self.after);
        Ok(Ran::Done)
    }

    fn terminal(&mut self) -> Result<Ran, Refusal> {
        let intact = self.sources();
        self.source_intact = intact.is_ok();
        if !self.source_intact {
            self.fault = None;
            self.outcome = Disposition::Refused;
        }
        intact.map(|_| Ran::Done)
    }

    fn exits(observations: &[Observation]) -> Vec<(&str, i32)> {
        observations
            .iter()
            .map(|seen| (seen.check_id.as_str(), seen.exit.code))
            .collect()
    }

    fn failure(&self, case: &str, digest: &str, trace: &str) -> Result<Option<Record>, Refusal> {
        let Some(class) = self.fault else {
            return Ok(None);
        };
        let seen = encoded(&(
            digest,
            self.refusal.as_ref().map(|refusal| refusal.code),
            Self::exits(&self.baseline),
            Self::exits(&self.after),
        ))?;
        Ok(Some(Record::Failure {
            id: format!("{case}@{}", self.request.run_key),
            workflow: self.request.workflow.clone(),
            run: self.request.run_key.clone(),
            failure_class: class.to_owned(),
            ddc_trace: trace.to_owned(),
            evidence_sha256: sha256(&[EVIDENCE_DOMAIN.as_bytes(), b"\n", &seen]),
        }))
    }

    fn record(self) -> Result<Terminal, Refusal> {
        let trace: String = self
            .stages
            .iter()
            .filter(|report| report.status == StageStatus::Done)
            .map(|report| report.stage)
            .collect();
        let case = self.request.case()?;
        let request_digest = self.request.digest()?;
        Ok(Terminal {
            failure: self.failure(&case, &request_digest, &trace)?,
            run_key: self.request.run_key.clone(),
            candidate_id: self.request.candidate_id(),
            request_digest,
            case,
            trace,
            stages: self.stages,
            outcome: self.outcome,
            refusal: self.refusal,
            source_manifest: self.request.sources.clone(),
            working_manifest: self.working,
            changed_paths: self.changed,
            baseline: self.baseline,
            after: self.after,
            source_intact: self.source_intact,
            source_application: "NOT_PERFORMED",
            admission: "Unadmitted",
            production_activation: "HOLD",
            evidence_scope: "FIXED_LOCAL_COMMANDS",
            mathematical_measurement: "NOT_MEASURED",
            authority_effect: "None",
        })
    }
}

/// Run the six stages on one request and keep the record in the run folder.
///
/// A run without a refusal exists only with its record kept: if the bench cannot keep it, the
/// call is refused. A run that already carries a refusal is returned even when it cannot be kept.
pub fn repair(text: &str, bench: &mut dyn Bench) -> Result<Terminal, Refusal> {
    let request = Request::read(text)?;
    let mut run = Run {
        request: &request,
        bench,
        stages: Vec::new(),
        refusal: None,
        working: BTreeMap::new(),
        changed: Vec::new(),
        baseline: Vec::new(),
        after: Vec::new(),
        fault: None,
        outcome: Disposition::Refused,
        source_intact: false,
    };
    let plan: [(Stage, bool); 6] = [
        (Run::capture, false),
        (Run::observe, false),
        (Run::evaluate, false),
        (Run::incorporate, true),
        (Run::dispose, true),
        (Run::terminal, true),
    ];
    for (index, (action, always)) in plan.into_iter().enumerate() {
        run.step(index, action, always);
    }
    let record = run.record()?;
    let kept = bench.keep(RECORD_FILE, &encoded(&record)?);
    if record.refusal.is_none() {
        kept?;
    }
    Ok(record)
}

/// The host's outcome for a repair run. `PASS` means `REPAIRED`; any other record is a `FAIL`
/// that carries the record; `REFUSED` means the request was not run and no record exists.
pub fn respond(text: &str, bench: &mut dyn Bench) -> Outcome {
    match repair(text, bench).and_then(|record| Ok((record.outcome, encoded(&record)?))) {
        Err(refusal) => Outcome::Refused { refusal },
        Ok((outcome, bytes)) => match serde_json::from_slice(&bytes) {
            Ok(result) if outcome == Disposition::Repaired => Outcome::Pass { result },
            Ok(result) => Outcome::Fail { result },
            Err(error) => Outcome::Refused {
                refusal: Refusal::new("ENCODING", error.to_string()),
            },
        },
    }
}
