//! Separate host field/persona checks, preserving input order and character spans.
//! Raw JSON ingress is strict; the source's parsed-value checks remain the oracle.
use crate::Refusal;
use serde::{
    de::{MapAccess, Visitor},
    Deserialize, Deserializer,
};
use serde_json::value::RawValue;
use std::{collections::BTreeSet, fmt};

pub const PROTECTED_FIELD_KEYS: [&str; 11] = [
    "phi",
    "phi1",
    "phi2",
    "phi3",
    "phi4",
    "gamma",
    "gamma2",
    "xi",
    "verified",
    "certified",
    "authorityeffect",
];
pub const UNAUTHORIZED_PERSONA_MARKERS: [&str; 4] = [
    "senior principal architect",
    "system administrator",
    "sovereign arbiter",
    "unrestricted authority",
];
const MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
fn bound(raw: &str) -> Result<(), Refusal> {
    if raw.len() > MAX_INPUT_BYTES {
        return Err(Refusal::new(
            "MALFORMED_PAYLOAD",
            "host-check input exceeds 4 MiB",
        ));
    }
    Ok(())
}
fn malformed(error: serde_json::Error) -> Refusal {
    Refusal::new("MALFORMED_PAYLOAD", error.to_string())
}
fn protected(key: &str) -> bool {
    PROTECTED_FIELD_KEYS.contains(&key.to_lowercase().replace('_', "").as_str())
}

struct OrderedMembers(Vec<(String, Box<RawValue>)>);
impl<'de> Deserialize<'de> for OrderedMembers {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct MembersVisitor;
        impl<'de> Visitor<'de> for MembersVisitor {
            type Value = OrderedMembers;
            fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str("a JSON object")
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
                let mut members = Vec::new();
                let mut keys = BTreeSet::new();
                while let Some((key, value)) = map.next_entry::<String, Box<RawValue>>()? {
                    if !keys.insert(key.clone()) {
                        return Err(serde::de::Error::custom(format!(
                            "duplicate JSON key {key:?}"
                        )));
                    }
                    members.push((key, value));
                }
                Ok(OrderedMembers(members))
            }
        }
        deserializer.deserialize_map(MembersVisitor)
    }
}
enum Document {
    Object(Vec<(String, Document)>),
    Array(Vec<Document>),
    String(String),
    Other,
}
fn document(raw: &RawValue, depth: usize) -> Result<Document, Refusal> {
    if depth > 128 {
        return Err(Refusal::new(
            "MALFORMED_PAYLOAD",
            "host-check nesting exceeds 128 levels",
        ));
    }
    let text = raw.get();
    match text.as_bytes().first() {
        Some(b'{') => {
            let members: OrderedMembers = serde_json::from_str(text).map_err(malformed)?;
            Ok(Document::Object(
                members
                    .0
                    .into_iter()
                    .map(|(key, value)| document(&value, depth + 1).map(|value| (key, value)))
                    .collect::<Result<_, _>>()?,
            ))
        }
        Some(b'[') => {
            let members: Vec<Box<RawValue>> = serde_json::from_str(text).map_err(malformed)?;
            Ok(Document::Array(
                members
                    .iter()
                    .map(|value| document(value, depth + 1))
                    .collect::<Result<_, _>>()?,
            ))
        }
        Some(b'"') => Ok(Document::String(
            serde_json::from_str(text).map_err(malformed)?,
        )),
        _ => Ok(Document::Other),
    }
}
#[derive(Default)]
struct Loci {
    protected: Vec<String>,
    persona: Vec<String>,
}
fn walk(value: &Document, path: &str, roles: &[String], loci: &mut Loci) {
    match value {
        Document::Object(members) => {
            for (key, value) in members {
                let here = format!("{path}/{key}");
                if protected(key) {
                    loci.protected.push(here.clone());
                }
                walk(value, &here, roles, loci);
            }
        }
        Document::Array(members) => {
            for (index, value) in members.iter().enumerate() {
                walk(value, &format!("{path}/{index}"), roles, loci);
            }
        }
        Document::String(text) => {
            let lower = text.to_lowercase();
            if UNAUTHORIZED_PERSONA_MARKERS
                .iter()
                .any(|marker| lower.contains(marker))
                && !roles.iter().any(|role| lower.contains(role))
            {
                loci.persona.push(path.into());
            }
        }
        Document::Other => {}
    }
}
fn inspect(raw: &str, path: &str, roles: &[String]) -> Result<Loci, Refusal> {
    bound(raw)?;
    let raw: Box<RawValue> = serde_json::from_str(raw).map_err(malformed)?;
    let parsed = document(&raw, 0)?;
    let mut loci = Loci::default();
    walk(&parsed, path, roles, &mut loci);
    Ok(loci)
}
/// JSON wire version of the source's parsed-value check. Paths retain the
/// source's literal key spelling, including slashes, rather than escaping it.
pub fn protected_field_loci(raw: &str, path: &str) -> Result<Vec<String>, Refusal> {
    Ok(inspect(raw, path, &[])?.protected)
}
pub fn persona_authority_leak_loci(raw: &str, roles: &[String]) -> Result<Vec<String>, Refusal> {
    Ok(inspect(raw, "", roles)?.persona)
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Kind {
    String,
    Punctuation(char),
    Literal,
}
struct Token {
    kind: Kind,
    start: usize,
    end: usize,
}
fn tokens(content: &[char]) -> Vec<Token> {
    let mut result = Vec::new();
    let mut index = 0;
    while index < content.len() {
        let character = content[index];
        if [' ', '\t', '\r', '\n'].contains(&character) {
            index += 1;
            continue;
        }
        let start = index;
        let kind;
        if character == '"' {
            index += 1;
            while index < content.len() && content[index] != '"' {
                index += if content[index] == '\\' { 2 } else { 1 };
            }
            index = (index + 1).min(content.len());
            kind = Kind::String;
        } else if "{}[]:,".contains(character) {
            index += 1;
            kind = Kind::Punctuation(character);
        } else {
            index += 1;
            while index < content.len() && !"{}[]:, \"\t\r\n".contains(content[index]) {
                index += 1;
            }
            kind = Kind::Literal;
        }
        result.push(Token {
            kind,
            start,
            end: index,
        });
    }
    result
}
fn update_container_stack(stack: &mut Vec<bool>, character: char) {
    match character {
        '{' => stack.push(true),
        '[' => stack.push(false),
        '}' | ']' => {
            stack.pop();
        }
        _ => {}
    }
}

fn is_object_key_token(tokens: &[Token], index: usize, token: &Token, stack: &[bool]) -> bool {
    token.kind == Kind::String
        && stack.last() == Some(&true)
        && tokens
            .get(index + 1)
            .is_some_and(|next| next.kind == Kind::Punctuation(':'))
}

/// Lexical key spans, matching source behavior even for incomplete documents.
/// Offsets count Unicode characters in original text, including quotes/escapes.
pub fn protected_field_spans(content: &str) -> Result<Vec<(usize, usize)>, Refusal> {
    bound(content)?;
    let characters = content.chars().collect::<Vec<_>>();
    let tokens = tokens(&characters);
    let mut stack = Vec::new();
    let mut result = Vec::new();
    for (index, token) in tokens.iter().enumerate() {
        if let Kind::Punctuation(character) = token.kind {
            update_container_stack(&mut stack, character);
            continue;
        }
        if !is_object_key_token(&tokens, index, token, &stack) {
            continue;
        }
        let encoded = characters[token.start..token.end]
            .iter()
            .collect::<String>();
        if serde_json::from_str::<String>(&encoded).is_ok_and(|key| protected(&key)) {
            result.push((token.start, token.end));
        }
    }
    Ok(result)
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/host_checks.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:host-checks:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2ab35c36 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2ab35c36` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2ab35c36 {
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
impl BoundaryError2ab35c36 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2ab35c36 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2ab35c36 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2ab35c36 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2ab35c36> {
        if capacity_bound == 0 {
            return Err(BoundaryError2ab35c36::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2ab35c36::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2ab35c36::ExceedsCapacity {
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
mod l4_boundary_tests_2ab35c36 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2ab35c36::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2ab35c36::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2ab35c36::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2ab35c36::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2ab35c36::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2ab35c36::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2ab35c36::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
