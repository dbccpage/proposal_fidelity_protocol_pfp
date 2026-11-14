//! The host's own answer to a finite task, compared with the answer in a reply.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:judge:v1
//!
//! A judge runs the operation its checker licenses on the task's public input and accepts the
//! reply only if the two answers are equal. Integers are unbounded and are read from their JSON
//! digits, so nothing is rounded and nothing overflows. A number written with a fraction or an
//! exponent is not an integer here, whatever its value.

use std::collections::BTreeMap;

use num_bigint::BigInt;
use serde::{Deserialize, Serialize};
use serde_json::value::RawValue;

use crate::Refusal;

/// The checker of the integer sum task: the answer is `{"total": n}` with `n` the exact sum.
pub const INTEGER_SUM: &str = "integer_sum_v1";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request<'a> {
    checker: String,
    /// The task's public input.
    #[serde(borrow)]
    case: &'a RawValue,
    /// The reply's task result, exactly as the reply gave it.
    #[serde(borrow)]
    answer: &'a RawValue,
}

/// The parts of an integer sum case the judge reads; a case may carry more.
#[derive(Deserialize)]
struct SumCase<'a> {
    #[serde(borrow)]
    values: Vec<&'a RawValue>,
}

/// The judge's verdict and the sentence recorded with it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Verdict {
    pub accepted: bool,
    pub reason: &'static str,
}

/// The integer a JSON number denotes, if it is written as one: an optional minus, then digits.
pub(crate) fn integer(literal: &RawValue) -> Option<BigInt> {
    let text = literal.get();
    let digits = text.strip_prefix('-').unwrap_or(text);
    if !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    text.parse().ok()
}

fn sum_case(case: &RawValue) -> Result<BigInt, Refusal> {
    let case: SumCase = serde_json::from_str(case.get())
        .map_err(|error| Refusal::new("BAD_CASE", error.to_string()))?;
    let mut total = BigInt::from(0);
    for literal in case.values {
        total += integer(literal).ok_or_else(|| {
            Refusal::new("BAD_CASE", format!("{} is not an integer", literal.get()))
        })?;
    }
    Ok(total)
}

/// The total a reply states, if its answer is exactly `{"total": integer}`.
fn stated_total(answer: &RawValue) -> Option<BigInt> {
    let fields: BTreeMap<String, &RawValue> = serde_json::from_str(answer.get()).ok()?;
    match (fields.len(), fields.get("total")) {
        (1, Some(total)) => integer(total),
        _ => None,
    }
}

/// Judge one reply's task result against the host's own computation.
pub fn judge(text: &str) -> Result<Verdict, Refusal> {
    let request: Request = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    if request.checker != INTEGER_SUM {
        return Err(Refusal::new(
            "UNKNOWN_CHECKER",
            format!("no judge is registered for {}", request.checker),
        ));
    }
    let accepted = stated_total(request.answer) == Some(sum_case(request.case)?);
    Ok(Verdict {
        accepted,
        reason: if accepted {
            "Exact integer sum agrees."
        } else {
            "Incorrect integer sum."
        },
    })
}
