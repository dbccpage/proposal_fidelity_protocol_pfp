//! What the bounded repair loops share: one assessed attempt, the trail of attempts, the limit
//! on them, and a fuel counter several loops can draw from.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-attempts:v1
//!
//! A repair loop puts the task to the model, assesses the reply, and on rejection asks again
//! with the host's residual added to the prompt. The residual says what is still wrong and never
//! what the answer is. A reply the host cannot read is an attempt like any other: its residual
//! is the reason, and it has no measure.

use num_bigint::BigInt;
use num_traits::One;

use crate::datum::Datum;

/// The host's finding on one attempt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Assessment {
    pub accepted: bool,
    /// What the next prompt may say about this attempt.
    pub residual: Datum,
    /// The size of what is still wrong: an integer or `p/q` text where smaller is better, or
    /// `null` when the reply could not be read.
    pub measure: Datum,
}

/// The assessment of a reply that could not be read.
pub fn unread(reason: String) -> Assessment {
    Assessment {
        accepted: false,
        residual: Datum::map([("malformed", Datum::text(reason))]),
        measure: Datum::Null,
    }
}

/// One row of a trail: the attempt's number, its measure and its residual.
pub fn row(attempt: usize, assessment: &Assessment) -> Datum {
    Datum::map([
        ("attempt", Datum::from(attempt)),
        ("measure", assessment.measure.clone()),
        ("residual", assessment.residual.clone()),
    ])
}

/// The number of attempts a task allows: its `max_attempts`, an exact integer from 1 to
/// `ceiling`, or `default` when the task names none.
pub fn limit(task: &Datum, default: usize, ceiling: usize) -> Result<usize, String> {
    let Some(stated) = task.get("max_attempts") else {
        return Ok(default);
    };
    if stated.as_int().is_none() {
        return Err("max_attempts must be an exact int".to_owned());
    }
    stated
        .as_count()
        .filter(|limit| (1..=ceiling).contains(limit))
        .ok_or_else(|| format!("max_attempts must be in 1..{ceiling}"))
}

/// A prompt with the host's residual on a new line under it.
pub fn with_residual(prompt: &str, residual: &Datum) -> String {
    format!("{prompt}\nHost residual: {}", residual.canonical())
}

/// A counter that only goes down, one unit for each question put to the model.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Fuel {
    left: BigInt,
    trace: Vec<BigInt>,
}

impl Fuel {
    pub fn new(units: BigInt) -> Self {
        Fuel {
            trace: vec![units.clone()],
            left: units,
        }
    }

    /// Take one unit. False, and nothing taken, when none is left.
    pub fn draw(&mut self) -> bool {
        if self.left < BigInt::one() {
            return false;
        }
        self.left -= 1;
        self.trace.push(self.left.clone());
        true
    }

    pub fn left(&self) -> &BigInt {
        &self.left
    }

    /// The starting amount and the amount after each draw.
    pub fn trace(&self) -> Datum {
        Datum::List(self.trace.iter().cloned().map(Datum::Int).collect())
    }
}
