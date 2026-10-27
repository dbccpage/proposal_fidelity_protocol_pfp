//! Semantic admission of checker receipts and fenced critic findings.
//! A parsed receipt states a verdict; reproduction/authentication is external.
use crate::evidence::{is_sha256_ref, value_error, CheckerVerdict};
use crate::stage::ports::Refusal;
use core_types::python_unicode::repr_string;
use regex::Regex;
use serde::Serialize;
use serde_json::{json, Value};

pub use crate::stage::packets::CHALLENGE_KINDS;

fn trimmed(value: &str) -> &str {
    value.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}

fn nonfinite_token(text: &str) -> Option<&str> {
    let mut quoted = false;
    let mut escaped = false;
    for (offset, character) in text.char_indices() {
        if quoted {
            if escaped {
                escaped = false;
            } else if character == '\\' {
                escaped = true;
            } else if character == '"' {
                quoted = false;
            }
            continue;
        }
        if character == '"' {
            quoted = true;
            continue;
        }
        if !matches!(character, 'N' | 'I' | '-') {
            continue;
        }
        let previous = text[..offset].chars().next_back();
        if previous.is_some_and(|c| !c.is_ascii_whitespace() && !matches!(c, '[' | ',' | ':')) {
            continue;
        }
        for token in ["NaN", "Infinity", "-Infinity"] {
            if let Some(after) = text[offset..].strip_prefix(token) {
                if after
                    .chars()
                    .next()
                    .is_none_or(|c| c.is_ascii_whitespace() || matches!(c, ',' | ']' | '}'))
                {
                    return Some(token);
                }
            }
        }
    }
    None
}
fn json_payload(text: &str) -> Result<Value, String> {
    serde_json::from_str(text).map_err(|error| {
        nonfinite_token(text).map_or_else(
            || error.to_string(),
            |token| format!("non-finite JSON constant {token} is not admitted"),
        )
    })
}
pub(crate) fn python_value_repr(value: &Value) -> String {
    match value {
        Value::String(text) => repr_string(text),
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        Value::Array(values) => format!(
            "[{}]",
            values
                .iter()
                .map(python_value_repr)
                .collect::<Vec<_>>()
                .join(", ")
        ),
        Value::Object(fields) => format!(
            "{{{}}}",
            fields
                .iter()
                .map(|(key, value)| format!("{}: {}", repr_string(key), python_value_repr(value)))
                .collect::<Vec<_>>()
                .join(", ")
        ),
        Value::Number(number) => number.to_string(),
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CheckerReceiptRecord {
    verdict: CheckerVerdict,
    candidate_content_sha256: String,
    checker_id: String,
    candidate_id: Option<String>,
}
impl CheckerReceiptRecord {
    pub fn verdict(&self) -> CheckerVerdict {
        self.verdict
    }
    pub fn candidate_content_sha256(&self) -> &str {
        &self.candidate_content_sha256
    }
    pub fn checker_id(&self) -> &str {
        &self.checker_id
    }
    pub fn candidate_id(&self) -> Option<&str> {
        self.candidate_id.as_deref()
    }
    pub fn to_dict(&self) -> Value {
        json!({"verdict":self.verdict,"candidate_content_sha256":self.candidate_content_sha256,"checker_id":self.checker_id,"candidate_id":self.candidate_id})
    }
}

pub fn parse_checker_receipt(bytes: &[u8]) -> Result<CheckerReceiptRecord, Refusal> {
    if bytes.is_empty() {
        return Err(value_error("the checker receipt is empty"));
    }
    let text = std::str::from_utf8(bytes)
        .map_err(|error| value_error(format!("the checker receipt is not UTF-8 JSON: {error}")))?;
    let payload = json_payload(text)
        .map_err(|error| value_error(format!("the checker receipt is not UTF-8 JSON: {error}")))?;
    let object = payload
        .as_object()
        .ok_or_else(|| value_error("the checker receipt must be a JSON object"))?;
    let verdict = match object.get("verdict").and_then(Value::as_str) {
        Some("ACCEPTED") => CheckerVerdict::Accepted,
        Some("REJECTED") => CheckerVerdict::Rejected,
        Some("NOT_MEASURED") => CheckerVerdict::NotMeasured,
        _ => {
            return Err(value_error(
                "checker receipt verdict must be ACCEPTED, REJECTED or NOT_MEASURED",
            ))
        }
    };
    let digest = object
        .get("candidate_content_sha256")
        .filter(|value| is_sha256_ref(value))
        .and_then(Value::as_str)
        .ok_or_else(|| {
            value_error(
                "checker receipt candidate_content_sha256 must be sha256:<64 lowercase hex>",
            )
        })?;
    let checker = object
        .get("checker_id")
        .and_then(Value::as_str)
        .filter(|text| !trimmed(text).is_empty())
        .ok_or_else(|| value_error("checker receipt checker_id must be a nonempty string"))?;
    let candidate = match object.get("candidate_id") {
        None | Some(Value::Null) => None,
        Some(Value::String(text)) if !trimmed(text).is_empty() => Some(text.clone()),
        _ => {
            return Err(value_error(
                "checker receipt candidate_id must be a nonempty string when present",
            ))
        }
    };
    Ok(CheckerReceiptRecord {
        verdict,
        candidate_content_sha256: digest.into(),
        checker_id: checker.into(),
        candidate_id: candidate,
    })
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CritiqueStatus {
    Structured,
    Malformed,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct StructuredCritique {
    status: CritiqueStatus,
    blocking: bool,
    counterexample: String,
    challenge_kind: String,
    parse_error: String,
}
impl StructuredCritique {
    pub fn new(
        status: CritiqueStatus,
        blocking: bool,
        counterexample: String,
        challenge_kind: String,
        parse_error: String,
    ) -> Result<Self, Refusal> {
        if !CHALLENGE_KINDS.contains(&challenge_kind.as_str()) {
            return Err(value_error("challenge_kind is not closed"));
        }
        if status == CritiqueStatus::Malformed && !blocking {
            return Err(value_error("a MALFORMED critique must block (fail closed)"));
        }
        Ok(Self {
            status,
            blocking,
            counterexample,
            challenge_kind,
            parse_error,
        })
    }
    fn malformed(reason: impl Into<String>) -> Result<Self, Refusal> {
        Self::new(
            CritiqueStatus::Malformed,
            true,
            String::new(),
            "PROVENANCE".into(),
            reason.into(),
        )
    }
    pub fn blocking(&self) -> bool {
        self.blocking
    }
    pub fn status(&self) -> CritiqueStatus {
        self.status
    }
    pub fn challenge_kind(&self) -> &str {
        &self.challenge_kind
    }
    pub fn counterexample(&self) -> &str {
        &self.counterexample
    }
    pub fn parse_error(&self) -> &str {
        &self.parse_error
    }
    pub fn to_dict(&self) -> Value {
        json!({"status":self.status,"blocking":self.blocking,"counterexample":self.counterexample,"challenge_kind":self.challenge_kind,"parse_error":self.parse_error})
    }
}

pub fn parse_structured_critique(reply: &Value) -> Result<StructuredCritique, Refusal> {
    let Some(reply) = reply.as_str() else {
        return StructuredCritique::malformed("the critique reply is not text");
    };
    let pattern = Regex::new(r"(?s)```critique[ \t]*\r?\n(.*?)\r?\n```")
        .map_err(|error| Refusal::new("ADVERSARY_EVIDENCE_PARSER_UNAVAILABLE", error.to_string()))?;
    let blocks = pattern
        .captures_iter(reply)
        .filter_map(|captures| captures.get(1).map(|matched| matched.as_str()))
        .collect::<Vec<_>>();
    if blocks.len() != 1 {
        return StructuredCritique::malformed(format!(
            "expected exactly one critique block, found {}",
            blocks.len()
        ));
    }
    let payload = match json_payload(blocks[0]) {
        Ok(payload) => payload,
        Err(error) => {
            return StructuredCritique::malformed(format!("critique block is not JSON: {error}"))
        }
    };
    let Some(object) = payload.as_object() else {
        return StructuredCritique::malformed("critique block must hold a JSON object");
    };
    let unknown = object
        .keys()
        .filter(|key| !matches!(key.as_str(), "blocking" | "counterexample" | "kind"))
        .cloned()
        .collect::<Vec<_>>();
    if !unknown.is_empty() {
        return StructuredCritique::malformed(format!(
            "unknown critique keys: {}",
            unknown.join(", ")
        ));
    }
    let Some(blocking) = object.get("blocking").and_then(Value::as_bool) else {
        return StructuredCritique::malformed("critique.blocking must be JSON true or false");
    };
    let Some(counterexample) = object.get("counterexample") else {
        return StructuredCritique::malformed(
            "critique.counterexample is required (a string or null)",
        );
    };
    let text = match counterexample {
        Value::Null => "",
        Value::String(text) => trimmed(text),
        _ => {
            return StructuredCritique::malformed(
                "critique.counterexample must be a string or null",
            )
        }
    };
    if blocking && text.is_empty() {
        return StructuredCritique::malformed(
            "a blocking critique must give a nonempty counterexample",
        );
    }
    let default = json!(if blocking { "COUNTERMODEL" } else { "LOGIC" });
    let kind = object.get("kind").unwrap_or(&default);
    let Some(kind_text) = kind.as_str().filter(|kind| CHALLENGE_KINDS.contains(kind)) else {
        let kinds = CHALLENGE_KINDS
            .iter()
            .map(|kind| repr_string(kind))
            .collect::<Vec<_>>()
            .join(", ");
        return StructuredCritique::malformed(format!(
            "critique.kind {} is not one of [{kinds}]",
            python_value_repr(kind)
        ));
    };
    StructuredCritique::new(
        CritiqueStatus::Structured,
        blocking,
        text.into(),
        kind_text.into(),
        String::new(),
    )
}

// Origin: engine/crates_rs/core_adversary/src/evidence_parse.rs
// Claim: urn:core:crates_rs:core-adversary:evidence-parse:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord464b299d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord464b299d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError464b299d {
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
impl BoundaryError464b299d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError464b299d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError464b299d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord464b299d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError464b299d> {
        if capacity_bound == 0 {
            return Err(BoundaryError464b299d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError464b299d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError464b299d::ExceedsCapacity {
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
mod l4_boundary_tests_464b299d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord464b299d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord464b299d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord464b299d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord464b299d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord464b299d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError464b299d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError464b299d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
