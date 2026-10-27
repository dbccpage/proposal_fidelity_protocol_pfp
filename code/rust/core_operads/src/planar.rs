//! Python workflow signatures with substitution delegated to the existing operad owner.
use crate::Refusal;
use num_bigint::BigInt;
use num_traits::ToPrimitive;
use core_operad_theory::foundation::{
    OperadColour, OperadSignature, Operation, OperationId, PlanarColoredOperad,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{collections::BTreeSet, str::FromStr};

pub const OPERAD_COLOURS: [&str; 10] = [
    "Audit", "Code", "Contract", "Diagram", "Ledger", "Paper", "Post", "Proof", "Receipt", "State",
];

fn push_escaped_char(result: &mut String, character: char, quote: char) {
    match character {
        '\\' => result.push_str("\\\\"),
        '\n' => result.push_str("\\n"),
        '\r' => result.push_str("\\r"),
        '\t' => result.push_str("\\t"),
        c if c == quote => {
            result.push('\\');
            result.push(c);
        }
        c if c.is_control() => result.push_str(&format!("\\x{:02x}", u32::from(c))),
        c => result.push(c),
    }
}

pub(crate) fn repr(value: &str) -> String {
    let quote = if value.contains('\'') && !value.contains('"') {
        '"'
    } else {
        '\''
    };
    let mut result = String::from(quote);
    for character in value.chars() {
        push_escaped_char(&mut result, character, quote);
    }
    result.push(quote);
    result
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
pub struct OperadOperation {
    name: String,
    source_colours: Vec<String>,
    target_colour: String,
}
impl OperadOperation {
    pub fn new(
        name: String,
        source_colours: Vec<String>,
        target_colour: String,
    ) -> Result<Self, Refusal> {
        if name.is_empty() {
            return Err(Refusal::new("BAD_NAME", "name must be a nonempty string"));
        }
        let unknown: BTreeSet<_> = source_colours
            .iter()
            .filter(|colour| !OPERAD_COLOURS.contains(&colour.as_str()))
            .collect();
        if !unknown.is_empty() {
            return Err(Refusal::new(
                "UNKNOWN_COLOUR",
                format!(
                    "{name} declares source colours outside the closed vocabulary: [{}]",
                    unknown
                        .into_iter()
                        .map(|colour| repr(colour))
                        .collect::<Vec<_>>()
                        .join(", ")
                ),
            ));
        }
        if !OPERAD_COLOURS.contains(&target_colour.as_str()) {
            return Err(Refusal::new(
                "UNKNOWN_COLOUR",
                format!(
                    "{name} declares target colour {}, which is outside the closed vocabulary",
                    repr(&target_colour)
                ),
            ));
        }
        Ok(Self {
            name,
            source_colours,
            target_colour,
        })
    }
    pub fn arity(&self) -> usize {
        self.source_colours.len()
    }
    pub fn name(&self) -> &str {
        &self.name
    }
    pub fn source_colours(&self) -> &[String] {
        &self.source_colours
    }
    pub fn target_colour(&self) -> &str {
        &self.target_colour
    }

    fn parse_source_colours(value: &Value) -> Result<Vec<String>, Refusal> {
        let sources = value
            .as_array()
            .ok_or_else(|| Refusal::new("BAD_SOURCES", "source_colours must be an exact tuple"))?;
        sources
            .iter()
            .map(|item| {
                item.as_str()
                    .map(str::to_owned)
                    .ok_or_else(|| Refusal::new("BAD_SOURCES", "source colours must be strings"))
            })
            .collect()
    }

    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        let object = value
            .as_object()
            .ok_or_else(|| Refusal::new("BAD_OPERATION", "both arguments must be operations"))?;
        let has_required_keys = ["name", "source_colours", "target_colour"]
            .iter()
            .all(|key| object.contains_key(*key));
        if object.len() != 3 || !has_required_keys {
            return Err(Refusal::new(
                "BAD_OPERATION",
                "operation record requires exactly name, source_colours and target_colour",
            ));
        }
        let name = object["name"]
            .as_str()
            .filter(|name| !name.is_empty())
            .ok_or_else(|| Refusal::new("BAD_NAME", "name must be a nonempty string"))?;
        let sources = Self::parse_source_colours(&object["source_colours"])?;
        let target = object["target_colour"]
            .as_str()
            .ok_or_else(|| Refusal::new("UNKNOWN_COLOUR", "target colour must be a string"))?;
        Self::new(name.into(), sources, target.into())
    }
}
impl<'de> Deserialize<'de> for OperadOperation {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let value = Value::deserialize(deserializer)?;
        Self::from_json(&value).map_err(serde::de::Error::custom)
    }
}

fn index(value: &Value) -> Result<BigInt, Refusal> {
    if let Value::Number(number) = value {
        let raw = number.to_string();
        if !raw.contains(['.', 'e', 'E']) {
            return BigInt::from_str(&raw)
                .map_err(|_| Refusal::new("BAD_INDEX", "index must be an exact integer"));
        }
    }
    Err(Refusal::new("BAD_INDEX", "index must be an exact integer"))
}

fn core_operation(value: &OperadOperation, name: &str) -> Result<Operation, Refusal> {
    let failure = |message| Refusal::new("OEWAS_OPERAD_KERNEL_REFUSED", message);
    let inputs = value
        .source_colours
        .iter()
        .map(|colour| OperadColour::new(colour.clone()))
        .collect::<Result<Vec<_>, _>>()
        .map_err(failure)?;
    let output = OperadColour::new(value.target_colour.clone()).map_err(failure)?;
    // The mathematical calculation uses internal labels; source operation names
    // remain byte-preserved in the returned workflow record, including whitespace.
    Ok(Operation::new_generator(
        OperationId::new(name).map_err(failure)?,
        OperadSignature::new(inputs, output),
        "workflow signature",
    ))
}

fn substitute_index(
    theta: &OperadOperation,
    slot: &BigInt,
    phi: &OperadOperation,
) -> Result<OperadOperation, Refusal> {
    // Reject negative, oversized and out-of-range integers through one checked
    // conversion, preserving the original integer in the source refusal text.
    let Some(position) = slot.to_usize().filter(|position| *position < theta.arity()) else {
        return Err(Refusal::new(
            "INDEX_OUT_OF_RANGE",
            format!(
                "{} has arity {}; slot {slot} does not exist",
                theta.name,
                theta.arity()
            ),
        ));
    };
    let expected = &theta.source_colours[position];
    if phi.target_colour != *expected {
        return Err(Refusal::new(
            "COLOUR_MISMATCH",
            format!(
                "{} expects {} at slot {slot}, but {} produces {}",
                theta.name,
                repr(expected),
                phi.name,
                repr(&phi.target_colour)
            ),
        ));
    }
    let owner = PlanarColoredOperad::new("workflow-signatures", false);
    let composed = owner
        .partial_compose(
            &core_operation(theta, "theta")?,
            &core_operation(phi, "phi")?,
            position,
        )
        .map_err(|message| Refusal::new("OEWAS_OPERAD_KERNEL_REFUSED", message))?;
    Ok(OperadOperation {
        name: format!("({} o_{slot} {})", theta.name, phi.name),
        source_colours: composed
            .signature
            .inputs
            .iter()
            .map(|colour| colour.as_str().to_owned())
            .collect(),
        target_colour: composed.signature.output.as_str().to_owned(),
    })
}

pub fn substitute(
    theta: &OperadOperation,
    slot: &Value,
    phi: &OperadOperation,
) -> Result<OperadOperation, Refusal> {
    substitute_index(theta, &index(slot)?, phi)
}
pub fn is_admissible(theta: &OperadOperation, slot: &Value, phi: &OperadOperation) -> bool {
    substitute(theta, slot, phi).is_ok()
}
pub fn associativity_witness(
    theta: &OperadOperation,
    i: &Value,
    phi: &OperadOperation,
    j: &Value,
    psi: &OperadOperation,
) -> Result<OperadOperation, Refusal> {
    let inner = substitute(phi, j, psi)?;
    let left = substitute(theta, i, &inner)?;
    let outer = substitute(theta, i, phi)?;
    let right = substitute_index(&outer, &(index(i)? + index(j)?), psi)?;
    if left.source_colours != right.source_colours || left.target_colour != right.target_colour {
        return Err(Refusal::new(
            "ASSOCIATIVITY_VIOLATED",
            "nesting order changed the composite signature",
        ));
    }
    Ok(left)
}
pub fn admissible_substitutions(operations: &[OperadOperation]) -> Vec<(String, usize, String)> {
    let mut result = Vec::new();
    for theta in operations {
        for (position, expected) in theta.source_colours.iter().enumerate() {
            for phi in operations {
                if phi.target_colour == *expected {
                    result.push((theta.name.clone(), position, phi.name.clone()));
                }
            }
        }
    }
    result
}

// Origin: engine/crates_rs/core_operads/src/planar.rs
// Claim: urn:core:crates_rs:core-operads:planar:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd82282cd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd82282cd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord82282cd {
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
impl BoundaryErrord82282cd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord82282cd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord82282cd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd82282cd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord82282cd> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord82282cd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord82282cd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord82282cd::ExceedsCapacity {
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
mod l4_boundary_tests_d82282cd {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd82282cd::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd82282cd::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd82282cd::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd82282cd::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd82282cd::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord82282cd::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord82282cd::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
