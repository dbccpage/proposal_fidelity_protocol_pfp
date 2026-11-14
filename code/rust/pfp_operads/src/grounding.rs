//! The grounded slots of a solver reply, rechecked against the task's public input.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:grounding:v1
//!
//! For a checker with grounded slots, four slot values must restate public facts exactly: the
//! input values, the arithmetic, the licensed operation applied to those values, and the
//! preservation obligations. Integers are compared as unbounded integers read from their JSON
//! digits, so 17.0 is not 17 here.

use std::collections::{BTreeMap, BTreeSet};

use num_bigint::BigInt;
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::value::RawValue;

use crate::envelope::{typings, Candidate};
use crate::judge::{integer, INTEGER_SUM};
use crate::Refusal;

/// The grounded slots of the integer sum task, in the order they are checked and reported.
pub const SUM_SLOTS: [&str; 4] = [
    "concrete_spans",
    "instantiated_arguments",
    "parameter_bindings",
    "preservation_obligations",
];

/// The slots a checker grounds; none for a checker without grounded slots.
pub fn grounded_slots(checker: &str) -> &'static [&'static str] {
    if checker == INTEGER_SUM {
        &SUM_SLOTS
    } else {
        &[]
    }
}

const UNBOUND: &str = "UNBOUND_INTEGER_LIST_OPERATION";
const MISMATCH: &str = "PUBLIC_BINDING_OR_DECLARED_CONSTRAINT_MISMATCH";

/// A value that is present, whatever it is: `null` is a value, a missing key is not.
fn present<'de, D: Deserializer<'de>>(deserializer: D) -> Result<Option<&'de RawValue>, D::Error> {
    <&RawValue>::deserialize(deserializer).map(Some)
}

/// One row of a keyed slot report; only its value is read.
#[derive(Deserialize)]
struct Row<'a> {
    #[serde(borrow, default, deserialize_with = "present")]
    value: Option<&'a RawValue>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request<'a> {
    checker: String,
    /// The task's public input values.
    #[serde(borrow)]
    values: Vec<&'a RawValue>,
    #[serde(borrow)]
    slot_report: BTreeMap<String, Row<'a>>,
    candidates: Vec<Candidate>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Spans<'a> {
    source: String,
    #[serde(borrow)]
    literal: Vec<&'a RawValue>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Bindings<'a> {
    #[serde(borrow)]
    values: Vec<&'a RawValue>,
    arithmetic: String,
}

/// Just the operation a slot value names, whatever else the value holds.
#[derive(Deserialize)]
struct Named {
    operad_id: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Arguments<'a> {
    #[serde(rename = "operad_id")]
    _operad_id: String,
    #[serde(borrow)]
    arguments: Vec<&'a RawValue>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Obligations {
    all_operands_once: bool,
    signed_integers: bool,
    rounding: String,
}

/// The host's recheck of the grounded slots.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct GroundingReport {
    pub valid: bool,
    pub errors: Vec<String>,
    pub checked_slots: Vec<&'static str>,
}

fn integers(literals: &[&RawValue]) -> Option<Vec<BigInt>> {
    literals.iter().map(|literal| integer(literal)).collect()
}

fn read<'a, T: Deserialize<'a>>(value: &'a RawValue) -> Option<T> {
    serde_json::from_str(value.get()).ok()
}

/// Whether one grounded slot restates the public facts; the error names what it failed.
fn slot_holds(
    slot: &str,
    value: &RawValue,
    values: &[BigInt],
    licensed: &BTreeSet<&str>,
) -> Result<(), &'static str> {
    let same = |literals: &[&RawValue]| integers(literals).as_deref() == Some(values);
    let holds = match slot {
        "concrete_spans" => read::<Spans>(value)
            .is_some_and(|spans| spans.source == "input.values" && same(&spans.literal)),
        "parameter_bindings" => read::<Bindings>(value)
            .is_some_and(|bound| bound.arithmetic == "integer_exact" && same(&bound.values)),
        "instantiated_arguments" => {
            let named = read::<Named>(value)
                .is_some_and(|named| licensed.contains(named.operad_id.as_str()));
            if !named {
                return Err(UNBOUND);
            }
            read::<Arguments>(value).is_some_and(|applied| same(&applied.arguments))
        }
        _ => read::<Obligations>(value).is_some_and(|kept| {
            kept.all_operands_once && kept.signed_integers && kept.rounding == "forbidden"
        }),
    };
    if holds {
        Ok(())
    } else {
        Err(MISMATCH)
    }
}

/// Recheck the grounded slots of one solver reply against the task's public input.
pub fn grounding(text: &str) -> Result<GroundingReport, Refusal> {
    let request: Request = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    let slots = grounded_slots(&request.checker);
    if slots.is_empty() {
        return Err(Refusal::new(
            "UNKNOWN_CHECKER",
            format!("{} grounds no slots", request.checker),
        ));
    }
    let values = integers(&request.values)
        .ok_or_else(|| Refusal::new("BAD_CASE", "the task values are not all integers"))?;
    let typed = typings(&request.candidates, &request.checker)?;
    let licensed: BTreeSet<&str> = typed
        .iter()
        .filter(|typing| typing.licensed_as.is_some())
        .map(|typing| typing.id.as_str())
        .collect();
    let mut errors = Vec::new();
    let mut checked_slots = Vec::new();
    for slot in slots {
        let outcome = match request.slot_report.get(*slot) {
            None => Err("MISSING_SLOT"),
            Some(Row { value: None }) => Err("MISSING_VALUE"),
            Some(Row { value: Some(value) }) => slot_holds(slot, value, &values, &licensed),
        };
        match outcome {
            Ok(()) => checked_slots.push(*slot),
            Err(reason) => errors.push(format!("L2_GROUNDING:{slot}:{reason}")),
        }
    }
    Ok(GroundingReport {
        valid: errors.is_empty(),
        errors,
        checked_slots,
    })
}
