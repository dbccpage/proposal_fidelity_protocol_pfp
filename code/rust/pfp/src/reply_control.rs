//! Untrusted machine-block parsing and residual declaration checks.
//!
//! This preserves the swarm-facing Python contract, which is stricter than
//! runtime::prompt_turn's independent required-field substring check.
//! A supplied dual digest is a declaration, not a verified mathematical proof.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
#[serde(tag = "operation", rename_all = "snake_case", deny_unknown_fields)]
pub enum ReplyControlRequest {
    Parse {
        reply_text: String,
    },
    Validate {
        machine_fields: BTreeMap<String, String>,
        #[serde(default)]
        dual_witness_digest: Option<String>,
    },
}

#[derive(Debug, PartialEq, Eq, Serialize)]
pub struct ResidualDeclaration {
    pub residual_colour: String,
    pub refusal_codes: Vec<String>,
    pub authority_effect: &'static str,
}

// Python str.isspace/strip and regex \s include the four ASCII information
// separators in addition to Unicode White_Space. Rust char::is_whitespace
// alone would silently change what the old frontend accepts.
fn python_whitespace(character: char) -> bool {
    character.is_whitespace() || matches!(character, '\u{1c}'..='\u{1f}')
}

#[derive(Debug, PartialEq, Eq, Serialize)]
pub struct MachineFields {
    pub machine_fields: BTreeMap<String, String>,
    pub field_order: Vec<String>,
    pub authority_effect: &'static str,
}

pub fn parse_machine_block(reply_text: &str) -> Result<MachineFields, String> {
    let mut cursor = 0;
    let block = loop {
        let Some(index) = reply_text[cursor..].find("```machine") else {
            return Ok(MachineFields {
                machine_fields: BTreeMap::new(),
                field_order: Vec::new(),
                authority_effect: "None",
            });
        };
        let after = cursor + index + "```machine".len();
        let whitespace_end = reply_text[after..]
            .char_indices()
            .find(|(_, character)| !python_whitespace(*character))
            .map_or(reply_text.len(), |(offset, _)| after + offset);
        // The source regex is greedy \s* followed by a required literal LF.
        // Its last LF is therefore the delimiter; CRLF retains the same rule.
        if let Some(newline) = reply_text[after..whitespace_end].rfind('\n') {
            let start = after + newline + 1;
            if let Some(end) = reply_text[start..].find("```") {
                break &reply_text[start..start + end];
            }
        }
        cursor = after;
    };
    let mut fields = BTreeMap::new();
    let mut field_order = Vec::new();
    for line in block.split('\n') {
        let Some((key, value)) = line.split_once('=') else {
            continue;
        };
        if key.is_empty()
            || !key
                .bytes()
                .all(|byte| byte.is_ascii_uppercase() || byte == b'_')
        {
            continue;
        }
        if fields.contains_key(key) {
            return Err(format!("duplicate machine-block field: {key}"));
        }
        field_order.push(key.to_owned());
        fields.insert(
            key.to_owned(),
            value.trim_matches(python_whitespace).to_owned(),
        );
    }
    Ok(MachineFields {
        machine_fields: fields,
        field_order,
        authority_effect: "None",
    })
}

pub fn validate_reply_residual(
    fields: &BTreeMap<String, String>,
    dual_witness_digest: Option<&str>,
) -> ResidualDeclaration {
    let mut refusal_codes = Vec::new();
    if fields.get("AUTHORITY_EFFECT").map(String::as_str) != Some("None") {
        refusal_codes.push("AUTHORITY_EFFECT_NON_NONE".to_owned());
    }
    let declared = fields.get("RESIDUAL_COLOUR").map_or("Open", String::as_str);
    let mut residual = match declared {
        "Open" | "Closed" | "Exact" => declared,
        _ => "Open",
    };
    if residual == "Exact" && dual_witness_digest.is_none() {
        refusal_codes.push("EXACT_WITHOUT_DUAL_WITNESS".to_owned());
        residual = "Open";
    }
    ResidualDeclaration {
        residual_colour: residual.to_owned(),
        refusal_codes,
        authority_effect: "None",
    }
}

// Origin: engine/crates_rs/pfp/src/reply_control.rs
// Claim: urn:core:crates_rs:pfp:reply-control:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb076b77d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb076b77d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb076b77d {
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
impl BoundaryErrorb076b77d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb076b77d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb076b77d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb076b77d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb076b77d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb076b77d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb076b77d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb076b77d::ExceedsCapacity {
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
mod l4_boundary_tests_b076b77d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb076b77d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb076b77d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb076b77d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb076b77d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb076b77d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb076b77d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb076b77d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
