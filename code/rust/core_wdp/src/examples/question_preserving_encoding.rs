//! JSON-only local driver for the bounded WDP encoding experiment.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3ea91aa2<T> {
    fn checked_invariant_3ea91aa2(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3ea91aa2<T> for Option<T> {
    #[inline]
    fn checked_invariant_3ea91aa2(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3ea91aa2<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3ea91aa2(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::io::{self, Read};

use core_wdp::question_preserving_encoding::{
    experiment, verify_cochain, verify_direct, Task, BOUND,
};
use serde::Deserialize;
use serde_json::{json, Value};

#[derive(Debug, Clone, PartialEq, Eq)]
enum QuestionAdmitError {
    Empty,
    Identity,
    Overflow,
    Length { declared: usize, actual: usize },
}

impl std::fmt::Display for QuestionAdmitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            QuestionAdmitError::Empty => write!(formatter, "empty question"),
            QuestionAdmitError::Identity => write!(formatter, "question id was not preserved"),
            QuestionAdmitError::Overflow => write!(formatter, "question length overflow"),
            QuestionAdmitError::Length { declared, actual } => write!(
                formatter,
                "payload length {actual} does not match declared {declared}"
            ),
        }
    }
}

/// A question admitted only when its canonical id survives encoding and the payload
/// byte length equals the declared length.
#[derive(Debug, Clone, PartialEq, Eq)]
struct PreservedQuestion {
    question_id: String,
    payload_len: usize,
}

fn decimal_digits(value: i64) -> Result<usize, QuestionAdmitError> {
    let mut magnitude = value.unsigned_abs();
    let mut digits = 1usize;
    if value < 0 {
        digits = digits.checked_add(1).ok_or(QuestionAdmitError::Overflow)?;
    }
    while magnitude >= 10 {
        magnitude /= 10;
        digits = digits.checked_add(1).ok_or(QuestionAdmitError::Overflow)?;
    }
    Ok(digits)
}

fn declared_question_len(task: &Task) -> Result<usize, QuestionAdmitError> {
    let slope = decimal_digits(task.derivative[0])?;
    let linear = decimal_digits(task.derivative[1])?;
    let value = decimal_digits(task.value_at_zero)?;
    slope
        .checked_add(1)
        .and_then(|count| count.checked_add(linear))
        .and_then(|count| count.checked_add(1))
        .and_then(|count| count.checked_add(value))
        .ok_or(QuestionAdmitError::Overflow)
}

fn canonical_question_id(task: &Task) -> Result<String, QuestionAdmitError> {
    let question_id = format!(
        "{},{},{}",
        task.derivative[0], task.derivative[1], task.value_at_zero
    );
    if question_id.is_empty() {
        return Err(QuestionAdmitError::Empty);
    }
    Ok(question_id)
}

fn parse_i64(text: &str) -> Result<i64, QuestionAdmitError> {
    let bytes = text.as_bytes();
    let (negative, digits) = match bytes.first() {
        Some(b'-') => (true, bytes.get(1..).ok_or(QuestionAdmitError::Empty)?),
        Some(_) => (false, bytes),
        None => return Err(QuestionAdmitError::Empty),
    };
    if digits.is_empty() {
        return Err(QuestionAdmitError::Empty);
    }
    let mut accumulator = 0i128;
    for byte in digits {
        if !byte.is_ascii_digit() {
            return Err(QuestionAdmitError::Identity);
        }
        let digit = i128::from(byte.checked_sub(b'0').ok_or(QuestionAdmitError::Identity)?);
        accumulator = accumulator
            .checked_mul(10)
            .ok_or(QuestionAdmitError::Overflow)?
            .checked_add(digit)
            .ok_or(QuestionAdmitError::Overflow)?;
    }
    if negative {
        accumulator = accumulator.checked_neg().ok_or(QuestionAdmitError::Overflow)?;
    }
    i64::try_from(accumulator).map_err(|_| QuestionAdmitError::Overflow)
}

fn parse_question_id(question_id: &str) -> Result<(i64, i64, i64), QuestionAdmitError> {
    let mut parts = question_id.split(',');
    let slope = parts.next().ok_or(QuestionAdmitError::Identity)?;
    let linear = parts.next().ok_or(QuestionAdmitError::Identity)?;
    let value = parts.next().ok_or(QuestionAdmitError::Identity)?;
    if parts.next().is_some() || slope.is_empty() || linear.is_empty() || value.is_empty() {
        return Err(QuestionAdmitError::Empty);
    }
    Ok((parse_i64(slope)?, parse_i64(linear)?, parse_i64(value)?))
}

fn byte_len(text: &str) -> Result<usize, QuestionAdmitError> {
    let mut count = 0usize;
    for _ in text.bytes() {
        count = count.checked_add(1).ok_or(QuestionAdmitError::Overflow)?;
    }
    Ok(count)
}

impl PreservedQuestion {
    fn try_admit(task: &Task, payload: &str, declared_len: usize) -> Result<Self, QuestionAdmitError> {
        if payload.is_empty() {
            return Err(QuestionAdmitError::Empty);
        }
        let question_id = canonical_question_id(task)?;
        let declared_id = declared_question_len(task)?;
        if question_id.len() != declared_id {
            return Err(QuestionAdmitError::Length {
                declared: declared_id,
                actual: question_id.len(),
            });
        }
        let parsed = parse_question_id(&question_id)?;
        if parsed != (task.derivative[0], task.derivative[1], task.value_at_zero) {
            return Err(QuestionAdmitError::Identity);
        }
        if payload.len() != declared_len {
            return Err(QuestionAdmitError::Length {
                declared: declared_len,
                actual: payload.len(),
            });
        }
        Ok(Self {
            question_id,
            payload_len: declared_len,
        })
    }

    fn question_id(&self) -> &str {
        &self.question_id
    }

    fn payload_len(&self) -> usize {
        self.payload_len
    }
}

#[derive(Debug, Deserialize)]
struct EmbeddedTask {
    task: Task,
}

fn action_name(raw: &str) -> Result<String, QuestionAdmitError> {
    let value: Value = serde_json::from_str(raw).map_err(|_| QuestionAdmitError::Identity)?;
    match value.get("action").and_then(Value::as_str) {
        Some(name) if !name.is_empty() => Ok(name.to_string()),
        Some(_) => Err(QuestionAdmitError::Empty),
        None => Err(QuestionAdmitError::Identity),
    }
}

fn admit_task_payload(task: &Task, payload: &str) -> Result<PreservedQuestion, QuestionAdmitError> {
    if payload.is_empty() {
        return Err(QuestionAdmitError::Empty);
    }
    let question_id = canonical_question_id(task)?;
    if let Ok(embedded) = serde_json::from_str::<EmbeddedTask>(payload) {
        let embedded_id = canonical_question_id(&embedded.task)?;
        if embedded_id != question_id {
            return Err(QuestionAdmitError::Identity);
        }
    }
    let declared = byte_len(payload)?;
    let admitted = PreservedQuestion::try_admit(task, payload, declared)?;
    if admitted.question_id() != question_id || admitted.payload_len() != declared {
        return Err(QuestionAdmitError::Identity);
    }
    Ok(admitted)
}

fn admit_experiment_corner() -> Result<PreservedQuestion, QuestionAdmitError> {
    let slope = BOUND.checked_mul(2).ok_or(QuestionAdmitError::Overflow)?;
    let lower = BOUND.checked_neg().ok_or(QuestionAdmitError::Overflow)?;
    let corner = Task {
        derivative: [BOUND, slope],
        value_at_zero: lower,
    };
    let encoded = canonical_question_id(&corner)?;
    let declared = declared_question_len(&corner)?;
    PreservedQuestion::try_admit(&corner, &encoded, declared)
}

fn admit_request(request: &Request, raw: &str) -> Result<PreservedQuestion, QuestionAdmitError> {
    if raw.is_empty() {
        return Err(QuestionAdmitError::Empty);
    }
    let action = action_name(raw)?;
    match request {
        Request::Experiment => {
            if action != "experiment" {
                return Err(QuestionAdmitError::Identity);
            }
            admit_experiment_corner()
        }
        Request::VerifyDirect { expected_task, report } => {
            if action != "verify_direct" {
                return Err(QuestionAdmitError::Identity);
            }
            admit_task_payload(expected_task, report)
        }
        Request::VerifyCochain { expected_task, report } => {
            if action != "verify_cochain" {
                return Err(QuestionAdmitError::Identity);
            }
            admit_task_payload(expected_task, report)
        }
    }
}

#[derive(Deserialize)]
#[serde(tag = "action", rename_all = "snake_case", deny_unknown_fields)]
enum Request {
    Experiment,
    VerifyDirect { expected_task: Task, report: String },
    VerifyCochain { expected_task: Task, report: String },
}

fn main() {
    let mut input = String::new();
    if io::stdin().take(4097).read_to_string(&mut input).is_err() || input.len() > 4096 {
        eprintln!("request exceeds input contract");
        std::process::exit(2);
    }
    let request = match serde_json::from_str::<Request>(&input) {
        Ok(request) => request,
        Err(error) => {
            eprintln!("invalid request: {error}");
            std::process::exit(2);
        }
    };
    let admitted = match admit_request(&request, &input) {
        Ok(admitted) => admitted,
        Err(error) => {
            println!(
                "{}",
                json!({"refused": error.to_string(), "authority_effect": "None"})
            );
            std::process::exit(2);
        }
    };
    if admitted.question_id().is_empty() || admitted.payload_len() == 0 {
        println!(
            "{}",
            json!({"refused": QuestionAdmitError::Empty.to_string(), "authority_effect": "None"})
        );
        std::process::exit(2);
    }
    let result = match request {
        Request::Experiment => experiment(),
        Request::VerifyDirect {
            expected_task,
            report,
        } => verify_direct(expected_task, &report)
            .map(|accepted| json!({"accepted":accepted,"authority_effect":"None"})),
        Request::VerifyCochain {
            expected_task,
            report,
        } => verify_cochain(expected_task, &report)
            .map(|accepted| json!({"accepted":accepted,"authority_effect":"None"})),
    };
    match result {
        Ok(value) => println!("{}", serde_json::to_string(&value).checked_invariant_3ea91aa2("JSON value")),
        Err(refusal) => {
            println!("{}", json!({"refused":refusal,"authority_effect":"None"}));
            std::process::exit(2);
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/examples/question_preserving_encoding.rs
// Claim: urn:core:crates_rs:core-wdp:question-preserving-encoding:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod question_admit_tests {
    use super::*;

    #[test]
    fn a_zero_question_round_trips_and_keeps_its_payload_length() -> Result<(), String> {
        let task = Task {
            derivative: [0, 0],
            value_at_zero: 0,
        };
        let admitted = PreservedQuestion::try_admit(&task, "0,0,0", 5).map_err(|error| error.to_string())?;
        if admitted.question_id() != "0,0,0" || admitted.payload_len() != 5 {
            return Err("zero question was not preserved".to_string());
        }
        Ok(())
    }

    #[test]
    fn an_empty_question_or_a_short_payload_is_refused() -> Result<(), String> {
        let task = Task {
            derivative: [-2, 4],
            value_at_zero: -1,
        };
        let empty = PreservedQuestion::try_admit(&task, "", 0);
        let short = PreservedQuestion::try_admit(&task, "-2,4,-1", 6);
        if !matches!(empty, Err(QuestionAdmitError::Empty))
            || !matches!(short, Err(QuestionAdmitError::Length { declared: 6, actual: 7 }))
        {
            return Err("length refusal was not produced".to_string());
        }
        Ok(())
    }

    #[test]
    fn a_report_that_renames_the_task_is_refused() -> Result<(), String> {
        let task = Task {
            derivative: [0, 0],
            value_at_zero: 0,
        };
        let report = r#"{"task":{"derivative":[1,0],"value_at_zero":0}}"#;
        match admit_task_payload(&task, report) {
            Err(QuestionAdmitError::Identity) => Ok(()),
            other => Err(format!("renamed task was admitted: {other:?}")),
        }
    }
}
