//! Workflow families: the host side of a workflow run, from the task to the verdict.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families:v1
//!
//! A run is a public task, a sealed part only the host reads, and the model's replies so far.
//! The host walks the family's steps over them. At each step it writes the prompt itself and
//! refuses to hand it out if it carries a sealed value (see [`sealed`]). When a step has no reply
//! yet the walk stops there, and [`next`] returns that step's stage and prompt. When every step
//! has its reply, [`judge`] returns the verdict with the predicates the host recorded.
//!
//! The caller asks the model and brings the reply back; it checks nothing. The walk is a pure
//! function of the request, so the same request always gives the same answer.
//!
//! Verdicts:
//!
//! * `HOST_CERTIFIED`: at least one predicate was recorded and every one passed.
//! * `TYPED_REFUSAL`: the reply refused with a code, and the host's own test gives that code.
//! * `REFUSED`: a predicate failed, a reply was missing, or a reply could not be read.
//!
//! A certified verdict covers the predicates listed with it and nothing else. Whatever a
//! family's walk returns, a certified verdict or a typed refusal stands only when at least one
//! predicate was recorded and every one passed; otherwise the host refuses the run.

pub mod sealed;
pub mod wf07;
pub mod wf30;
pub mod wf31;

use serde::{Deserialize, Serialize};
use serde_json::value::RawValue;
use serde_json::Value as Json;
use sha2::{Digest, Sha256};

use crate::datum::Datum;
use crate::host::Outcome;
use crate::Refusal;

use sealed::Guard;

pub const CERTIFIED: &str = "HOST_CERTIFIED";
pub const TYPED_REFUSAL: &str = "TYPED_REFUSAL";
pub const REFUSED: &str = "REFUSED";

/// The code of a certified verdict when a family names no other.
pub const CERTIFIED_CODE: &str = "CERTIFIED";
/// The code when the step that needed a reply got none.
pub const NO_REPLY: &str = "NO_ADMISSIBLE_REPLY";
/// The code when a reply could not be read as the family's candidate.
pub const MALFORMED: &str = "MALFORMED_CANDIDATE";
/// The code when nothing was recorded, so nothing can be certified.
pub const NO_PREDICATE: &str = "NO_HOST_PREDICATE";

fn sha256_hex(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// One workflow family: its registry names and its two host functions.
pub struct Family {
    pub workflow: &'static str,
    pub name: &'static str,
    pub host_check: &'static str,
    /// Say what is wrong with a task or sealed part the walk cannot read.
    pub validate: fn(task: &Datum, sealed: &Datum) -> Result<(), String>,
    /// Walk the steps over the replies so far, to a verdict or to the step that needs a reply.
    pub walk: fn(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop>,
}

/// Every family this host checks, in workflow order.
pub const FAMILIES: &[&Family] = &[&wf07::FAMILY, &wf30::FAMILY, &wf31::FAMILY];

/// A question the host wants put to the model.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Ask {
    pub stage: String,
    pub prompt: String,
    pub prompt_sha256: String,
}

/// A step that already has its reply.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Asked {
    pub stage: String,
    pub prompt_sha256: String,
}

/// Why a walk stopped before a verdict.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Stop {
    /// This step has no reply yet.
    Ask(Ask),
    /// A reply could not be read as a candidate. The text says why.
    Malformed(String),
    /// The run itself is refused.
    Refuse(Refusal),
}

/// `Stop::Malformed` unless the condition holds.
pub fn require(condition: bool, reason: &str) -> Result<(), Stop> {
    if condition {
        Ok(())
    } else {
        Err(Stop::Malformed(reason.to_owned()))
    }
}

/// One run as a family's walk sees it.
pub struct Run<'a> {
    pub family: &'a Family,
    pub task: &'a Datum,
    pub sealed: &'a Datum,
    replies: &'a [Option<Datum>],
    asked: Vec<Asked>,
    guard: Guard,
}

impl<'a> Run<'a> {
    /// The family's default prompt: its id and name, the task's statement, then the rest of the
    /// task as canonical JSON.
    pub fn prompt(&self) -> String {
        let statement = match self.task.get("statement") {
            Some(Datum::Text(text)) => text.clone(),
            Some(other) => other.canonical(),
            None => String::new(),
        };
        let rest = match self.task {
            Datum::Map(map) => Datum::Map(
                map.iter()
                    .filter(|(key, _)| key.as_str() != "statement")
                    .map(|(key, value)| (key.clone(), value.clone()))
                    .collect(),
            ),
            other => other.clone(),
        };
        format!(
            "{} {}. {}\n{}",
            self.family.workflow,
            self.family.name,
            statement,
            rest.canonical()
        )
    }

    /// The reply to this step, or nothing if the model gave none. Stops the walk when the step
    /// has not been put to the model yet, and refuses the run when the prompt carries a sealed
    /// value.
    pub fn ask(&mut self, stage: &str, prompt: String) -> Result<Option<&'a Datum>, Stop> {
        if self.guard.leaks(&prompt) {
            return Err(Stop::Refuse(Refusal::new(
                "SEALED_LEAK",
                format!("the prompt of stage {stage} contains a sealed value"),
            )));
        }
        let prompt_sha256 = sha256_hex(&prompt);
        let stage = stage.to_owned();
        match self.replies.get(self.asked.len()) {
            Some(reply) => {
                self.asked.push(Asked {
                    stage,
                    prompt_sha256,
                });
                Ok(reply.as_ref())
            }
            None => Err(Stop::Ask(Ask {
                stage,
                prompt,
                prompt_sha256,
            })),
        }
    }
}

/// One fact the host checked, with the digest of what it looked at.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Predicate {
    pub name: String,
    pub passed: bool,
    pub evidence_sha256: String,
}

/// The predicates of one run, in the order the host recorded them.
#[derive(Debug, Default)]
pub struct Checks {
    rows: Vec<Predicate>,
}

impl Checks {
    /// Record one predicate and return whether it passed. A name is written once: a second
    /// record under the same name is kept as a failed predicate, so the run cannot certify.
    pub fn record(&mut self, name: &str, passed: bool, evidence: &Datum) -> bool {
        let repeated = self.rows.iter().any(|row| row.name == name);
        let passed = passed && !repeated;
        self.rows.push(Predicate {
            name: if repeated {
                format!("repeated:{name}")
            } else {
                name.to_owned()
            },
            passed,
            evidence_sha256: sha256_hex(&evidence.canonical()),
        });
        passed
    }

    fn failed(&self) -> Vec<&str> {
        self.rows
            .iter()
            .filter(|row| !row.passed)
            .map(|row| row.name.as_str())
            .collect()
    }

    /// True when at least one predicate was recorded and every one passed.
    pub fn certified(&self) -> bool {
        !self.rows.is_empty() && self.failed().is_empty()
    }

    /// Certified under `code` when every recorded predicate passed. Otherwise refused under the
    /// first failed predicate's name in capitals, with the failed names added to the detail.
    pub fn judge(&self, code: &str, detail: Datum) -> Verdict {
        if self.certified() {
            return certified(code, detail);
        }
        let failed = self.failed();
        let code = failed
            .first()
            .map_or_else(|| NO_PREDICATE.to_owned(), |name| name.to_uppercase());
        let mut entries = match detail {
            Datum::Map(map) => map,
            _ => Default::default(),
        };
        entries.insert("failed".to_owned(), Datum::from(failed));
        refused(&code, Datum::Map(entries))
    }
}

/// What a walk concludes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Verdict {
    pub verdict: &'static str,
    pub code: String,
    pub detail: Datum,
}

pub fn certified(code: &str, detail: Datum) -> Verdict {
    Verdict {
        verdict: CERTIFIED,
        code: code.to_owned(),
        detail,
    }
}

pub fn typed_refusal(code: &str, detail: Datum) -> Verdict {
    Verdict {
        verdict: TYPED_REFUSAL,
        code: code.to_owned(),
        detail,
    }
}

pub fn refused(code: &str, detail: Datum) -> Verdict {
    Verdict {
        verdict: REFUSED,
        code: code.to_owned(),
        detail,
    }
}

/// The verdict of a step whose reply never came.
pub fn no_reply() -> Verdict {
    refused(NO_REPLY, Datum::map([]))
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request<'a> {
    workflow: String,
    #[serde(borrow)]
    task: &'a RawValue,
    #[serde(borrow, default)]
    sealed: Option<&'a RawValue>,
    #[serde(borrow, default)]
    replies: Vec<&'a RawValue>,
}

/// What the host says about a run that is waiting for a reply or has all of them.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Turn {
    pub workflow: &'static str,
    /// The step to put to the model, or nothing when every step has its reply.
    pub ask: Option<Ask>,
    /// The steps that already have a reply.
    pub asked: Vec<Asked>,
}

/// The verdict of a finished run and everything the host recorded on the way.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct Report {
    pub workflow: &'static str,
    pub verdict: &'static str,
    pub code: String,
    pub detail: Json,
    pub predicates: Vec<Predicate>,
    /// True when at least one predicate was recorded and none failed. The verdict can still be
    /// refused, for example when the reply a later step needed never came.
    pub every_predicate_passed: bool,
    pub asked: Vec<Asked>,
}

/// One registry row, for a caller that lists what this host checks.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Listed {
    pub workflow: &'static str,
    pub name: &'static str,
    pub host_check: &'static str,
}

enum End {
    Ask(Ask),
    Verdict(Verdict),
}

struct Walked {
    family: &'static Family,
    asked: Vec<Asked>,
    checks: Checks,
    end: End,
}

fn bad_request(message: impl Into<String>) -> Refusal {
    Refusal::new("BAD_REQUEST", message)
}

/// A reply as the caller sends it: `null` when the model gave none, else `{"content": ...}`.
fn reply(raw: &RawValue) -> Result<Option<Datum>, Refusal> {
    match Datum::parse(raw.get())? {
        Datum::Null => Ok(None),
        Datum::Map(mut map) if map.len() == 1 => map
            .remove("content")
            .map(Some)
            .ok_or_else(|| bad_request("a reply is null or an object with the one key content")),
        _ => Err(bad_request(
            "a reply is null or an object with the one key content",
        )),
    }
}

fn family(registry: &[&'static Family], workflow: &str) -> Result<&'static Family, Refusal> {
    registry
        .iter()
        .copied()
        .find(|family| family.workflow == workflow)
        .ok_or_else(|| {
            Refusal::new(
                "UNKNOWN_WORKFLOW",
                format!("this host checks no family named {workflow}"),
            )
        })
}

/// The verdict a walk's conclusion stands as. A verdict that is not a refusal needs at least one
/// recorded predicate and no failed one; without that it becomes the refusal [`Checks::judge`]
/// gives, with the walk's code and detail kept beside the failed names.
fn settle(verdict: Verdict, checks: &Checks) -> Verdict {
    if verdict.verdict == REFUSED || checks.certified() {
        return verdict;
    }
    let claimed = Datum::map([
        ("claimed_verdict", Datum::from(verdict.verdict)),
        ("claimed_code", Datum::text(verdict.code)),
        ("claimed_detail", verdict.detail),
    ]);
    checks.judge(CERTIFIED_CODE, claimed)
}

fn walk(registry: &[&'static Family], text: &str) -> Result<Walked, Refusal> {
    let request: Request =
        serde_json::from_str(text).map_err(|error| bad_request(error.to_string()))?;
    let family = family(registry, &request.workflow)?;
    let task = Datum::parse(request.task.get())?;
    let sealed = match request.sealed {
        Some(raw) => Datum::parse(raw.get())?,
        None => Datum::map([]),
    };
    if !sealed.is_map() {
        return Err(bad_request("sealed must be an object"));
    }
    let replies: Vec<Option<Datum>> = request
        .replies
        .iter()
        .map(|raw| reply(raw))
        .collect::<Result<_, _>>()?;
    if !task.is_map() {
        return Err(Refusal::new("BAD_TASK", "the task must be an object"));
    }
    (family.validate)(&task, &sealed).map_err(|reason| Refusal::new("BAD_TASK", reason))?;
    let mut run = Run {
        family,
        task: &task,
        sealed: &sealed,
        replies: &replies,
        asked: Vec::new(),
        guard: Guard::new(&sealed),
    };
    let mut checks = Checks::default();
    let end = match (family.walk)(&mut run, &mut checks) {
        Ok(verdict) => End::Verdict(settle(verdict, &checks)),
        Err(Stop::Ask(ask)) => End::Ask(ask),
        Err(Stop::Malformed(reason)) => End::Verdict(refused(
            MALFORMED,
            Datum::map([("reason", Datum::text(reason))]),
        )),
        Err(Stop::Refuse(refusal)) => return Err(refusal),
    };
    if matches!(end, End::Verdict(_)) && run.asked.len() < replies.len() {
        return Err(bad_request(format!(
            "the run ends after {} replies and {} were sent",
            run.asked.len(),
            replies.len()
        )));
    }
    Ok(Walked {
        family,
        asked: run.asked,
        checks,
        end,
    })
}

fn pass<T: Serialize>(value: &T) -> Outcome {
    match serde_json::to_value(value) {
        Ok(result) => Outcome::Pass { result },
        Err(error) => Outcome::Refused {
            refusal: Refusal::new("ENCODING", error.to_string()),
        },
    }
}

/// The step to put to the model next, or nothing when the run has every reply it needs.
pub fn next(request: &str) -> Outcome {
    next_in(FAMILIES, request)
}

/// [`next`] over the families of `registry`.
pub fn next_in(registry: &[&'static Family], request: &str) -> Outcome {
    match walk(registry, request) {
        Ok(walked) => pass(&Turn {
            workflow: walked.family.workflow,
            ask: match walked.end {
                End::Ask(ask) => Some(ask),
                End::Verdict(_) => None,
            },
            asked: walked.asked,
        }),
        Err(refusal) => Outcome::Refused { refusal },
    }
}

/// The verdict of a run that has every reply. `PASS` for a certified verdict or a typed
/// refusal, `FAIL` for a refused one, and a refusal when a step still waits for its reply.
pub fn judge(request: &str) -> Outcome {
    judge_in(FAMILIES, request)
}

/// [`judge`] over the families of `registry`.
pub fn judge_in(registry: &[&'static Family], request: &str) -> Outcome {
    let walked = match walk(registry, request) {
        Ok(walked) => walked,
        Err(refusal) => return Outcome::Refused { refusal },
    };
    let verdict = match walked.end {
        End::Verdict(verdict) => verdict,
        End::Ask(ask) => {
            return Outcome::Refused {
                refusal: Refusal::new(
                    "REPLIES_INCOMPLETE",
                    format!("stage {} has no reply yet", ask.stage),
                ),
            }
        }
    };
    let held = verdict.verdict != REFUSED;
    let report = pass(&Report {
        workflow: walked.family.workflow,
        verdict: verdict.verdict,
        code: verdict.code,
        detail: verdict.detail.to_json(),
        every_predicate_passed: walked.checks.certified(),
        predicates: walked.checks.rows,
        asked: walked.asked,
    });
    match report {
        Outcome::Pass { result } if !held => Outcome::Fail { result },
        other => other,
    }
}

/// The families this host checks.
pub fn list() -> Outcome {
    let families: Vec<Listed> = FAMILIES
        .iter()
        .map(|family| Listed {
            workflow: family.workflow,
            name: family.name,
            host_check: family.host_check,
        })
        .collect();
    pass(&serde_json::json!({ "families": families }))
}
