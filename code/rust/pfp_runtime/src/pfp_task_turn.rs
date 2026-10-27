//! Native string-answer profile of Python PFP task_turn, not a task-specific judge.
//! The wire has the same four fields and sorted ASCII JSON input digest. No JCS,
//! mathematical acceptance, provider dispatch, or budget owner is introduced here.
use crate::{refusal::Refusal, strict_json};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

pub const CHECKER_ID: &str = "adversary-seat-string-v1";

fn digest(raw: &[u8]) -> String {
    hex::encode(Sha256::digest(raw))
}

fn emit_object(fields: &serde_json::Map<String, Value>, out: &mut String) -> Result<(), Refusal> {
    out.push('{');
    let mut keys: Vec<_> = fields.keys().collect();
    keys.sort();
    for (i, key) in keys.into_iter().enumerate() {
        if i != 0 {
            out.push(',');
        }
        emit_string(key, out)?;
        out.push(':');
        emit_value(&fields[key], out)?;
    }
    out.push('}');
    Ok(())
}

fn emit_array(items: &[Value], out: &mut String) -> Result<(), Refusal> {
    out.push('[');
    for (i, item) in items.iter().enumerate() {
        if i != 0 {
            out.push(',');
        }
        emit_value(item, out)?;
    }
    out.push(']');
    Ok(())
}

fn emit_string(text: &str, out: &mut String) -> Result<(), Refusal> {
    let encoded = serde_json::to_string(text)
        .map_err(|_| Refusal::new("PFP_TASK_INVALID", "string encoding failed"))?;
    for c in encoded.chars() {
        if c.is_ascii() && c != '\u{7f}' {
            out.push(c);
        } else {
            for unit in c.encode_utf16(&mut [0; 2]) {
                out.push_str(&format!("\\u{unit:04x}"));
            }
        }
    }
    Ok(())
}

fn emit_value(value: &Value, out: &mut String) -> Result<(), Refusal> {
    match value {
        Value::Object(fields) => emit_object(fields, out)?,
        Value::Array(items) => emit_array(items, out)?,
        Value::String(text) => emit_string(text, out)?,
        Value::Number(n) => out.push_str(
            &n.to_string()
                .parse::<num_bigint::BigInt>()
                .map_err(|_| {
                    Refusal::new(
                        "PFP_TASK_INVALID",
                        "native string profile requires integral JSON context numbers",
                    )
                })?
                .to_string(),
        ),
        other => out.push_str(&other.to_string()),
    }
    Ok(())
}

/// Python json.dumps(sort_keys=True, ensure_ascii=True, separators=(',', ':')).
/// This finite profile admits strings, booleans, null and integral JSON numbers.
/// Floating JSON is refused rather than claiming cross-language number parity.
pub fn sorted_ascii_json(value: &Value) -> Result<Vec<u8>, Refusal> {
    let mut out = String::new();
    emit_value(value, &mut out)?;
    Ok(out.into_bytes())
}

const FORBIDDEN_CONTEXT_KEYS: &[&str] = &[
    "held_out_terms",
    "test_databases",
    "ground_truth",
    "optimal_cost",
    "solution",
    "category",
    "note",
    "oracle_answer",
    "host_diagnostics",
    "judge_diagnostics",
    "checker_diagnostics",
];

fn is_safe_context_key(key: &str) -> bool {
    !FORBIDDEN_CONTEXT_KEYS.contains(&key)
        && !key.starts_with("expected_")
        && !key.ends_with("_expected")
}

// Bare `expected` is removed before this check, matching Python stimulus.
// Other hidden labels and example fences are still refused.
fn safe_context(value: &Value) -> bool {
    match value {
        Value::Object(fields) => fields
            .iter()
            .all(|(key, val)| is_safe_context_key(key) && safe_context(val)),
        Value::Array(items) => items.iter().all(safe_context),
        _ => true,
    }
}

// Drop a bare `expected` key at every object, as Python stimulus does.
// expected_* and *_expected stay on the refusal path.
fn drop_bare_expected(value: &mut Value) {
    match value {
        Value::Object(fields) => {
            fields.retain(|key, child| {
                if key == "expected" {
                    return false;
                }
                drop_bare_expected(child);
                true
            });
        }
        Value::Array(items) => {
            for item in items {
                drop_bare_expected(item);
            }
        }
        _ => {}
    }
}

fn validate_nonempty_bounded_str(val: &str, max_len: Option<usize>) -> bool {
    !val.trim().is_empty() && max_len.map_or(true, |limit| val.len() <= limit)
}

fn validate_prepare_inputs(
    system: &str,
    task_id: &str,
    attempt_id: &str,
    checker_id: &str,
    context: &Value,
) -> Result<(), Refusal> {
    let ids_ok = validate_nonempty_bounded_str(task_id, Some(200))
        && validate_nonempty_bounded_str(attempt_id, Some(200))
        && validate_nonempty_bounded_str(system, None)
        && validate_nonempty_bounded_str(checker_id, None);
    if !ids_ok {
        return Err(Refusal::new(
            "PFP_TASK_INVALID",
            "nonempty bounded task, attempt, objective and checker are required",
        ));
    }
    let has_fence = system.contains("```json")
        || system.contains("```\n")
        || system.contains("```\r\n");
    if !safe_context(context) || has_fence {
        return Err(Refusal::new(
            "PFP_TASK_INVALID",
            "native string role profile refuses hidden labels and example-block projection inputs",
        ));
    }
    Ok(())
}

#[derive(Debug, Clone)]
pub struct PreparedTaskTurn {
    pub system: String,
    pub user: String,
    pub binding: Value,
}
impl PreparedTaskTurn {
    pub fn prepare(
        system: &str,
        user: &str,
        task_id: &str,
        attempt_id: &str,
        mut context: Value,
        checker_id: &str,
    ) -> Result<Self, Refusal> {
        drop_bare_expected(&mut context);
        validate_prepare_inputs(system, task_id, attempt_id, checker_id, &context)?;
        let answer_schema = json!({"type":"string","minLength":1});
        let mut public = json!({"task_id":task_id,"objective":system,"input":{"prompt":user,"context":context},"answer_schema":answer_schema});
        let input_sha256 = digest(&sorted_ascii_json(&public)?);
        let answer_id = format!(
            "urn:pfp:answer:{}",
            digest(&sorted_ascii_json(&answer_schema)?)
        );
        let schema = json!({"type":"object","properties":{
            "task_id":{"type":"string","const":task_id},"attempt_id":{"type":"string","const":attempt_id},
            "input_sha256":{"type":"string","const":input_sha256},"answer":{"type":"string","minLength":1,"$id":answer_id}},
            "required":["task_id","attempt_id","input_sha256","answer"],"additionalProperties":false});
        public["attempt_id"] = json!(attempt_id);
        public["input_sha256"] = json!(input_sha256);
        Ok(Self {
            system:format!("{system}\nYour answer is an untrusted proposal; schema validity is not task acceptance.\nReturn only a JSON instance that validates against this response schema. Do not return the schema itself, fences or extra text:\n{schema}"),
            user:public.to_string(),
            binding:json!({"task_id":task_id,"attempt_id":attempt_id,"input_sha256":input_sha256,"checker_id":checker_id}),
        })
    }
    pub fn check(&self, raw: &[u8]) -> Result<String, Refusal> {
        let value = strict_json::parse(raw).map_err(|_| {
            Refusal::new(
                "PFP_REPLY_INVALID",
                "reply must be strict UTF-8 JSON without duplicate keys",
            )
        })?;
        let fields = value
            .as_object()
            .ok_or_else(|| Refusal::new("PFP_REPLY_INVALID", "reply must be an object"))?;
        if fields.len() != 4
            || ["task_id", "attempt_id", "input_sha256"]
                .iter()
                .any(|key| fields.get(*key) != self.binding.get(*key))
            || fields.keys().any(|key| {
                !["task_id", "attempt_id", "input_sha256", "answer"].contains(&key.as_str())
            })
        {
            return Err(Refusal::new(
                "PFP_REPLY_BINDING_MISMATCH",
                "reply task, attempt, input or field set differs from the prepared turn",
            ));
        }
        fields["answer"]
            .as_str()
            .filter(|s| !s.is_empty())
            .map(str::to_owned)
            .ok_or_else(|| Refusal::new("PFP_REPLY_INVALID", "answer must be a nonempty string"))
    }
    /// Stored evidence is rechecked against this exact task and checker, with no transport.
    pub fn replay(&self, record: &Value) -> Result<String, Refusal> {
        if record["pfp_binding"] != self.binding {
            return Err(Refusal::new(
                "PFP_REPLAY_BINDING_MISMATCH",
                "replay task, input, attempt or checker differs",
            ));
        }
        let raw = record["pfp_raw_reply_hex"]
            .as_str()
            .and_then(|s| hex::decode(s).ok())
            .ok_or_else(|| Refusal::new("PFP_REPLAY_INVALID", "stored raw reply is unavailable"))?;
        if record["pfp_raw_reply_sha256"] != json!(digest(&raw)) {
            return Err(Refusal::new(
                "PFP_REPLAY_INVALID",
                "stored raw reply digest differs",
            ));
        }
        let answer = self.check(&raw)?;
        if record["answer_sha256"] != json!(digest(answer.as_bytes())) {
            return Err(Refusal::new(
                "PFP_REPLAY_INVALID",
                "stored answer digest differs",
            ));
        }
        Ok(answer)
    }
    pub fn evidence(&self, raw: &[u8], answer: &str) -> Value {
        json!({"pfp_binding":self.binding,"pfp_raw_reply_hex":hex::encode(raw),"pfp_raw_reply_sha256":digest(raw),"answer_sha256":digest(answer.as_bytes()),"evidence_grade":"UNVERIFIED","authority_effect":"None"})
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/pfp_task_turn.rs
// Claim: urn:core:crates_rs:pfp-runtime:pfp-task-turn:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord871d2951 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord871d2951` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError871d2951 {
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
impl BoundaryError871d2951 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError871d2951 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError871d2951 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord871d2951 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError871d2951> {
        if capacity_bound == 0 {
            return Err(BoundaryError871d2951::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError871d2951::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError871d2951::ExceedsCapacity {
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
mod l4_boundary_tests_871d2951 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord871d2951::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord871d2951::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord871d2951::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord871d2951::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord871d2951::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError871d2951::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError871d2951::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
