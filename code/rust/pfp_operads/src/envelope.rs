//! The reply envelope of the full-slot workflows: a slot report, operad candidates and DDC moves.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:envelope:v1
//!
//! The structure rules and their error codes are the ones these workflows have always applied, in
//! the same order, so a recorded reply keeps its verdict. Two readings are added and neither
//! changes the verdict: each candidate is typed against the canon's `task_value_colour`, and a
//! typed candidate whose signature is one the task licenses is bound to that licensed operation.
//!
//! A candidate stays unverified. Its meaning is free text, so the host can run the licensed
//! operation (see [`crate::judge`]) but not the candidate.

use std::collections::{BTreeMap, BTreeSet};

use core_operad_canon::DdcOp;
use serde::{Deserialize, Serialize};
use serde_json::Value as Json;

use crate::{canon_values, Refusal};

/// The canon type whose values are the colours a candidate may be typed by.
pub const COLOUR_TYPE: &str = "task_value_colour";

/// A witness reference every reply may use: the task's own result.
pub const TASK_RESULT: &str = "task_result";

/// The value sorts a finite task's operations consume and produce.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskValueColour {
    Integer,
    IntegerList,
}

impl TaskValueColour {
    pub const ALL: [TaskValueColour; 2] = [TaskValueColour::Integer, TaskValueColour::IntegerList];

    pub fn as_str(self) -> &'static str {
        match self {
            TaskValueColour::Integer => "Integer",
            TaskValueColour::IntegerList => "IntegerList",
        }
    }
}

/// An operation a task checker licenses, by signature.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Licensed {
    pub name: &'static str,
    pub checker: &'static str,
    pub sources: &'static [TaskValueColour],
    pub target: TaskValueColour,
}

/// Every licensed operation. The host runs these itself in [`crate::judge`].
pub const LICENSED: &[Licensed] = &[Licensed {
    name: "integer_list_sum",
    checker: "integer_sum_v1",
    sources: &[TaskValueColour::IntegerList],
    target: TaskValueColour::Integer,
}];

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "snake_case")]
enum Disposition {
    Provided,
    NotApplicable,
    Unresolved,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SlotRow {
    slot: String,
    disposition: Disposition,
    value: String,
    reason: String,
}

/// A quotation from one of the texts a reply may cite.
#[derive(PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Quote {
    pub(crate) kind: String,
    pub(crate) quote: String,
}

impl Quote {
    /// The quote occurs in the source it names.
    pub(crate) fn found_in(&self, sources: &BTreeMap<String, String>) -> bool {
        sources
            .get(&self.kind)
            .is_some_and(|text| text.contains(&self.quote))
    }
}

/// An operad candidate as a reply writes it. Two candidates are equal when every field is.
#[derive(PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Candidate {
    pub(crate) id: String,
    #[serde(rename = "operation")]
    _operation: String,
    pub(crate) source_colours: Vec<String>,
    pub(crate) target_colour: String,
    arity: Json,
    pub(crate) source: Quote,
    pub(crate) witness_refs: Vec<String>,
}

impl Candidate {
    /// The stated arity is the number of source colours. JSON Schema reads 1.0 as the integer 1,
    /// and so did the earlier host.
    pub(crate) fn arity_agrees(&self) -> bool {
        self.arity.as_f64() == Some(self.source_colours.len() as f64)
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Move {
    id: String,
    op: String,
    operad_id: Option<String>,
    #[serde(rename = "before")]
    _before: String,
    #[serde(rename = "after")]
    _after: String,
    local_log: Option<String>,
    refusal: Option<String>,
    witness_refs: Vec<String>,
}

/// The three record lists of a reply. Other fields of the answer are not read here.
#[derive(Deserialize)]
struct Answer {
    slot_report: Vec<SlotRow>,
    operad_candidates: Vec<Candidate>,
    ddc_moves: Vec<Move>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    /// Every slot id of the pinned catalogue.
    catalogue: Vec<String>,
    /// The slots a reply must provide.
    required: Vec<String>,
    /// The texts a candidate may quote, by kind.
    sources: BTreeMap<String, String>,
    /// The task's checker; it decides which operations are licensed.
    checker: String,
    answer: Answer,
}

/// How the host reads one candidate, in reply order.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CandidateTyping {
    pub id: String,
    /// Every colour of the candidate is a canon task value colour.
    pub typed: bool,
    /// The licensed operation whose signature this candidate has, if any. A candidate whose
    /// stated arity disagrees with its source colours has no signature.
    pub licensed_as: Option<&'static str>,
}

/// The host's reading of one reply envelope.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct EnvelopeReport {
    pub accepted: bool,
    pub errors: Vec<String>,
    pub candidates: Vec<CandidateTyping>,
    pub ddc_trace: String,
}

/// Blank as the earlier host read it: nothing but white space or the four ASCII separators.
fn blank(text: &str) -> bool {
    text.chars()
        .all(|c| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}

fn distinct<'a>(ids: impl Iterator<Item = &'a str>) -> (BTreeSet<&'a str>, usize) {
    let mut count = 0;
    let set = ids.inspect(|_| count += 1).collect();
    (set, count)
}

fn slot_errors(request: &Request, slots: &BTreeSet<&str>, errors: &mut Vec<String>) {
    let rows = &request.answer.slot_report;
    let (named, count) = distinct(rows.iter().map(|row| row.slot.as_str()));
    if named.len() != count || &named != slots {
        errors.push("SLOT_COVERAGE_OR_DUPLICATES".to_owned());
    }
    for row in rows {
        let provided = row.disposition == Disposition::Provided;
        if provided && blank(&row.value) {
            errors.push(format!("EMPTY_PROVIDED_SLOT:{}", row.slot));
        }
        if !provided && (!row.value.is_empty() || blank(&row.reason)) {
            errors.push(format!("MISSING_SLOT_REASON:{}", row.slot));
        }
        if !provided && request.required.contains(&row.slot) {
            errors.push(format!("REQUIRED_SLOT_UNRESOLVED:{}", row.slot));
        }
    }
}

fn unknown_reference(refs: &[String], known: &BTreeSet<&str>) -> bool {
    refs.iter().any(|name| !known.contains(name.as_str()))
}

fn candidate_errors(request: &Request, known: &BTreeSet<&str>, errors: &mut Vec<String>) {
    for candidate in &request.answer.operad_candidates {
        if !candidate.arity_agrees() {
            errors.push(format!("ARITY_MISMATCH:{}", candidate.id));
        }
        if !candidate.source.found_in(&request.sources) {
            errors.push(format!("SOURCE_QUOTE_MISSING:{}", candidate.id));
        }
        if unknown_reference(&candidate.witness_refs, known) {
            errors.push(format!("UNKNOWN_WITNESS_REF:{}", candidate.id));
        }
    }
}

/// The DDC word of the reply, with an error for every move the rules refuse.
fn move_errors(
    request: &Request,
    ids: &BTreeSet<&str>,
    known: &BTreeSet<&str>,
    errors: &mut Vec<String>,
) -> String {
    let moves = &request.answer.ddc_moves;
    let (named, count) = distinct(moves.iter().map(|step| step.id.as_str()));
    if named.len() != count {
        errors.push("DUPLICATE_DDC_ID".to_owned());
    }
    let mut trace = String::new();
    for step in moves {
        let logged = [&step.local_log, &step.refusal]
            .iter()
            .any(|text| text.as_deref().is_some_and(|text| !blank(text)));
        if !logged {
            errors.push(format!("DDC_LOG_OR_REFUSAL_REQUIRED:{}", step.id));
        }
        if step
            .operad_id
            .as_deref()
            .is_some_and(|id| !ids.contains(id))
        {
            errors.push(format!("UNKNOWN_OPERAD_REF:{}", step.id));
        }
        if unknown_reference(&step.witness_refs, known) {
            errors.push(format!("UNKNOWN_WITNESS_REF:{}", step.id));
        }
        if DdcOp::LETTERS.contains(&step.op.as_str()) {
            trace.push_str(&step.op);
        } else {
            errors.push(format!("UNKNOWN_DDC_LETTER:{}", step.id));
        }
    }
    trace
}

fn licensed_as(candidate: &Candidate, checker: &str) -> Option<&'static str> {
    LICENSED
        .iter()
        .find(|licensed| {
            licensed.checker == checker
                && candidate.arity_agrees()
                && candidate.target_colour == licensed.target.as_str()
                && candidate
                    .source_colours
                    .iter()
                    .map(String::as_str)
                    .eq(licensed.sources.iter().map(|colour| colour.as_str()))
        })
        .map(|licensed| licensed.name)
}

/// The canon typing of each candidate, in the order given.
pub(crate) fn typings(
    candidates: &[Candidate],
    checker: &str,
) -> Result<Vec<CandidateTyping>, Refusal> {
    let colours = canon_values(COLOUR_TYPE)?;
    Ok(candidates
        .iter()
        .map(|candidate| CandidateTyping {
            id: candidate.id.clone(),
            typed: candidate
                .source_colours
                .iter()
                .chain([&candidate.target_colour])
                .all(|name| colours.contains(&name.as_str())),
            licensed_as: licensed_as(candidate, checker),
        })
        .collect())
}

/// Read one reply envelope: the structure errors in their fixed order, then the canon typing.
pub fn envelope(text: &str) -> Result<EnvelopeReport, Refusal> {
    let request: Request = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    let slots: BTreeSet<&str> = request.catalogue.iter().map(String::as_str).collect();
    let mut errors = Vec::new();
    slot_errors(&request, &slots, &mut errors);
    let candidates = &request.answer.operad_candidates;
    let (ids, count) = distinct(candidates.iter().map(|candidate| candidate.id.as_str()));
    if ids.len() != count {
        errors.push("DUPLICATE_OPERAD_ID".to_owned());
    }
    let mut known = slots.clone();
    known.extend(ids.iter().copied());
    known.insert(TASK_RESULT);
    candidate_errors(&request, &known, &mut errors);
    let ddc_trace = move_errors(&request, &ids, &known, &mut errors);
    Ok(EnvelopeReport {
        accepted: errors.is_empty(),
        errors,
        candidates: typings(candidates, &request.checker)?,
        ddc_trace,
    })
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TypingRequest {
    checker: String,
    candidates: Vec<Candidate>,
}

/// The canon typing of a list of candidates, with no structure check.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct TypingReport {
    pub candidates: Vec<CandidateTyping>,
}

/// Type candidates against the canon and bind the ones with the checker's licensed signature.
pub fn typing(text: &str) -> Result<TypingReport, Refusal> {
    let request: TypingRequest = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    Ok(TypingReport {
        candidates: typings(&request.candidates, &request.checker)?,
    })
}
