//! A reply's operad candidates, run by the host on the task's own input.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:running:v1
//!
//! A candidate in the full-slot workflows is a signature and a sentence, so the host can type it
//! and no more. Here a candidate also names a body from the closed list in [`crate::term`]. The
//! host types it by the canon's `task_value_colour`, feeds it the public input of every case, and
//! compares what the body gives with the result of its own judge (see [`crate::judge`]). The
//! caller supplies no expected value.
//!
//! `HOST_VERIFIED` means the body reproduced the judge's result on every case given. It is not a
//! proof that the candidate is the licensed operation on every input.

use std::collections::BTreeSet;

use num_bigint::BigInt;
use serde::{Deserialize, Serialize};
use serde_json::value::RawValue;

use crate::envelope::{TaskValueColour, COLOUR_TYPE};
use crate::host::{Disposition, OperationWire};
use crate::judge::reference;
use crate::term::{Body, Operation, Term, Value};
use crate::Refusal;

/// The verdict when at least one candidate is verified and none is refused.
pub const VERIFIED: &str = "CANDIDATE_VERIFIED";
/// The verdict when a candidate is ill typed or gave a result the judge's does not equal.
pub const REFUSED: &str = "CANDIDATE_REFUSED";
/// The verdict when nothing was refused and nothing could be verified.
pub const NONE_VERIFIED: &str = "NO_VERIFIED_CANDIDATE";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RunRequest<'a> {
    checker: String,
    /// The public input of each case: the task's own, then any the host keeps as probes.
    #[serde(borrow)]
    cases: Vec<&'a RawValue>,
    candidates: Vec<OperationWire>,
}

/// What the host found for one candidate. `code` and `message` say why it is not verified.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Ran {
    pub id: String,
    pub disposition: Disposition,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub code: Option<&'static str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
}

/// The host's reading of every candidate, and the one verdict a workflow routes on.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct RunReport {
    pub accepted: bool,
    pub verdict: &'static str,
    /// The ids of the verified candidates, in request order.
    pub verified: Vec<String>,
    pub candidates: Vec<Ran>,
}

/// One case as the term evaluator sees it: its values, and the judge's result on them.
struct Probe {
    values: Vec<i64>,
    result: BigInt,
}

fn probe(checker: &str, case: &RawValue) -> Result<Probe, Refusal> {
    let read = reference(checker, case)?;
    let values: Option<Vec<i64>> = read
        .values
        .iter()
        .map(|value| i64::try_from(value).ok())
        .collect();
    match values {
        Some(values) => Ok(Probe {
            values,
            result: read.result,
        }),
        None => Err(Refusal::new(
            "CASE_OUT_OF_RANGE",
            "a candidate is run on 64-bit integers and a case value does not fit",
        )),
    }
}

/// The case's values in the shape the operation's inputs ask for: one list, or one integer each.
fn arguments(operation: &Operation, values: &[i64]) -> Option<Vec<Value>> {
    let integers: Vec<Value> = values.iter().copied().map(Value::Int).collect();
    let names: Vec<&str> = operation
        .sources()
        .iter()
        .map(|colour| colour.name())
        .collect();
    if names == [TaskValueColour::IntegerList.as_str()] {
        Some(vec![Value::List(integers)])
    } else if names.len() == values.len()
        && names
            .iter()
            .all(|name| *name == TaskValueColour::Integer.as_str())
    {
        Some(integers)
    } else {
        None
    }
}

type Why = (Disposition, &'static str, String);

/// Run one typed candidate on every case; `Err` says why it is not verified.
fn examine(operation: &Operation, probes: &[Probe]) -> Result<(), Why> {
    if operation.body() == Body::Opaque {
        return Err((
            Disposition::UnverifiedCandidate,
            "NO_BODY",
            "the candidate names no body, so there is nothing to run".to_owned(),
        ));
    }
    let term = Term::corolla(operation);
    let mut unfit = None;
    for (index, probe) in probes.iter().enumerate() {
        let Some(inputs) = arguments(operation, &probe.values) else {
            unfit = unfit.or(Some(index));
            continue;
        };
        match term.eval(&inputs) {
            Ok(Value::Int(number)) if BigInt::from(number) == probe.result => {}
            Ok(value) => {
                let shown = serde_json::to_string(&value).unwrap_or_default();
                return Err((
                    Disposition::Refused,
                    "RESULT_DIFFERS",
                    format!("case {index}: the body gives {shown}, not the judge's result"),
                ));
            }
            Err(refusal) => {
                return Err((
                    Disposition::Refused,
                    refusal.code,
                    format!("case {index}: {}", refusal.message),
                ))
            }
        }
    }
    match unfit {
        None => Ok(()),
        Some(index) => Err((
            Disposition::UnverifiedCandidate,
            "DOES_NOT_FIT_CASE",
            format!("case {index}: the candidate's inputs do not take the case's values"),
        )),
    }
}

fn ran(id: &str, found: Result<(), Why>) -> Ran {
    match found {
        Ok(()) => Ran {
            id: id.to_owned(),
            disposition: Disposition::HostVerified,
            code: None,
            message: None,
        },
        Err((disposition, code, message)) => Ran {
            id: id.to_owned(),
            disposition,
            code: Some(code),
            message: Some(message),
        },
    }
}

fn refused(refusal: Refusal) -> Why {
    (Disposition::Refused, refusal.code, refusal.message)
}

/// Type every candidate, run each one that has a body on every case, and compare with the judge.
pub fn run(text: &str) -> Result<RunReport, Refusal> {
    let request: RunRequest = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    if request.cases.is_empty() {
        return Err(Refusal::new(
            "NO_CASES",
            "a candidate is verified on at least one case",
        ));
    }
    let mut probes = Vec::new();
    for case in &request.cases {
        probes.push(probe(&request.checker, case)?);
    }
    let mut seen = BTreeSet::new();
    let repeated: BTreeSet<&str> = request
        .candidates
        .iter()
        .map(|wire| wire.id.as_str())
        .filter(|id| !seen.insert(*id))
        .collect();
    let candidates: Vec<Ran> = request
        .candidates
        .iter()
        .map(|wire| {
            let found = if repeated.contains(wire.id.as_str()) {
                Err(refused(Refusal::new(
                    "DUPLICATE_OPERATION",
                    "the id is used twice",
                )))
            } else {
                wire.build(COLOUR_TYPE)
                    .map_err(refused)
                    .and_then(|operation| examine(&operation, &probes))
            };
            ran(&wire.id, found)
        })
        .collect();
    let verified: Vec<String> = candidates
        .iter()
        .filter(|candidate| candidate.disposition == Disposition::HostVerified)
        .map(|candidate| candidate.id.clone())
        .collect();
    let verdict = if candidates
        .iter()
        .any(|candidate| candidate.disposition == Disposition::Refused)
    {
        REFUSED
    } else if verified.is_empty() {
        NONE_VERIFIED
    } else {
        VERIFIED
    };
    Ok(RunReport {
        accepted: verdict == VERIFIED,
        verdict,
        verified,
        candidates,
    })
}
