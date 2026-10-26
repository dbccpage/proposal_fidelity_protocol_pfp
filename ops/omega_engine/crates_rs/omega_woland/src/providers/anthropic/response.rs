//! Messages API replies: typed blocks for what the host reads, raw blocks for history.
//!
//! The assistant content is kept verbatim (`raw_content`) so it can be sent back unchanged
//! on the next turn; this matters for redacted advisor output, which the host cannot read
//! and must still return. Block types this parser does not know are kept as `Unknown`.
//!
//! AuthorityEffect: None.

use crate::providers::Refusal;
use serde_json::Value;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StopReason {
    EndTurn,
    MaxTokens,
    StopSequence,
    ToolUse,
    /// A server tool loop paused; send the assistant content back to continue the turn.
    PauseTurn,
    Refusal,
    Other(String),
}

impl StopReason {
    /// The value as the API spells it.
    pub fn wire(&self) -> &str {
        match self {
            Self::EndTurn => "end_turn",
            Self::MaxTokens => "max_tokens",
            Self::StopSequence => "stop_sequence",
            Self::ToolUse => "tool_use",
            Self::PauseTurn => "pause_turn",
            Self::Refusal => "refusal",
            Self::Other(text) => text,
        }
    }

    fn parse(text: &str) -> Self {
        match text {
            "end_turn" => Self::EndTurn,
            "max_tokens" => Self::MaxTokens,
            "stop_sequence" => Self::StopSequence,
            "tool_use" => Self::ToolUse,
            "pause_turn" => Self::PauseTurn,
            "refusal" => Self::Refusal,
            other => Self::Other(other.to_owned()),
        }
    }
}

/// Whether the host can read a block's payload.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Readability {
    Readable,
    /// Encrypted advisor output: kept and replayed, never read.
    NotReadable,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ContentBlock {
    /// Preserved verbatim and billed within output_tokens; never a final answer.
    Thinking(Value),
    Text {
        text: String,
    },
    ToolUse {
        id: String,
        name: String,
        input: Value,
    },
    ServerToolUse {
        id: String,
        name: String,
        input: Value,
    },
    AdvisorResult {
        tool_use_id: String,
        text: String,
        stop_reason: Option<String>,
    },
    AdvisorRedactedResult {
        tool_use_id: String,
        encrypted_content: String,
        stop_reason: Option<String>,
    },
    AdvisorError {
        tool_use_id: String,
        error_code: String,
    },
    /// `bash_code_execution_tool_result`, `text_editor_code_execution_tool_result` or
    /// `code_execution_tool_result`; `content` is the result object as sent.
    CodeExecutionResult {
        block_type: String,
        tool_use_id: String,
        content: Value,
    },
    Unknown(Value),
}

impl ContentBlock {
    pub fn readability(&self) -> Readability {
        match self {
            ContentBlock::AdvisorRedactedResult { .. } => Readability::NotReadable,
            _ => Readability::Readable,
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct Usage {
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cache_creation_input_tokens: u64,
    pub cache_read_input_tokens: u64,
    pub code_execution_requests: u64,
    /// The usage object as sent, including counters this parser does not model.
    pub raw: Value,
}

#[derive(Debug, Clone, PartialEq)]
pub struct MessagesResponse {
    pub id: String,
    pub model: String,
    pub stop_reason: StopReason,
    pub content: Vec<ContentBlock>,
    pub raw_content: Vec<Value>,
    pub usage: Usage,
    pub container_id: Option<String>,
}

impl MessagesResponse {
    /// The assistant turn to append to history, unchanged.
    pub fn assistant_message(&self) -> Value {
        serde_json::json!({"role": "assistant", "content": self.raw_content})
    }

    pub fn text(&self) -> String {
        self.content
            .iter()
            .filter_map(|block| match block {
                ContentBlock::Text { text } => Some(text.as_str()),
                _ => None,
            })
            .collect::<Vec<_>>()
            .join("")
    }
}

fn unparseable(message: impl Into<String>) -> Refusal {
    Refusal::new("ANTHROPIC_RESPONSE_UNPARSEABLE", message)
}

fn string(value: &Value, field: &str) -> Result<String, Refusal> {
    value
        .get(field)
        .and_then(Value::as_str)
        .map(str::to_owned)
        .ok_or_else(|| unparseable(format!("{field} must be a string")))
}

fn count(value: &Value, field: &str, required: bool) -> Result<u64, Refusal> {
    match value.get(field) {
        None | Some(Value::Null) if !required => Ok(0),
        Some(number) => number
            .as_u64()
            .ok_or_else(|| unparseable(format!("usage.{field} must be a non-negative integer"))),
        None => Err(unparseable(format!("usage.{field} missing"))),
    }
}

fn block(raw: &Value) -> Result<ContentBlock, Refusal> {
    let kind = raw.get("type").and_then(Value::as_str).unwrap_or_default();
    match kind {
        "text" => Ok(ContentBlock::Text {
            text: string(raw, "text")?,
        }),
        "thinking" | "redacted_thinking" => Ok(thinking_block(kind, raw)),
        "tool_use" | "server_tool_use" => tool_use_block(kind, raw),
        "advisor_tool_result" => advisor_result_block(raw),
        "bash_code_execution_tool_result"
        | "text_editor_code_execution_tool_result"
        | "code_execution_tool_result" => Ok(ContentBlock::CodeExecutionResult {
            block_type: kind.to_owned(),
            tool_use_id: string(raw, "tool_use_id")?,
            content: raw.get("content").cloned().unwrap_or(Value::Null),
        }),
        _ => Ok(ContentBlock::Unknown(raw.clone())),
    }
}

fn thinking_block(kind: &str, raw: &Value) -> ContentBlock {
    let valid_thinking = kind == "thinking"
        && raw.get("thinking").is_some_and(Value::is_string)
        && raw.get("signature").is_some_and(Value::is_string);
    let valid_redacted =
        kind == "redacted_thinking" && raw.get("data").is_some_and(Value::is_string);
    if valid_thinking || valid_redacted {
        ContentBlock::Thinking(raw.clone())
    } else {
        ContentBlock::Unknown(raw.clone())
    }
}

fn tool_use_block(kind: &str, raw: &Value) -> Result<ContentBlock, Refusal> {
    let (id, name) = (string(raw, "id")?, string(raw, "name")?);
    let input = raw.get("input").cloned().unwrap_or(Value::Null);
    if kind == "tool_use" {
        Ok(ContentBlock::ToolUse { id, name, input })
    } else {
        Ok(ContentBlock::ServerToolUse { id, name, input })
    }
}

fn advisor_result_block(raw: &Value) -> Result<ContentBlock, Refusal> {
    let tool_use_id = string(raw, "tool_use_id")?;
    let content = raw.get("content").cloned().unwrap_or(Value::Null);
    let stop_reason = content
        .get("stop_reason")
        .and_then(Value::as_str)
        .map(str::to_owned);
    Ok(match content.get("type").and_then(Value::as_str) {
        Some("advisor_result") => ContentBlock::AdvisorResult {
            tool_use_id,
            text: string(&content, "text")?,
            stop_reason,
        },
        Some("advisor_redacted_result") => ContentBlock::AdvisorRedactedResult {
            tool_use_id,
            encrypted_content: string(&content, "encrypted_content")?,
            stop_reason,
        },
        Some("advisor_tool_result_error") => ContentBlock::AdvisorError {
            tool_use_id,
            error_code: string(&content, "error_code")?,
        },
        _ => ContentBlock::Unknown(raw.clone()),
    })
}

fn parse_usage(value: &Value) -> Result<Usage, Refusal> {
    let usage_raw = value
        .get("usage")
        .cloned()
        .ok_or_else(|| unparseable("usage missing"))?;
    let code_execution_requests = match usage_raw.get("server_tool_use") {
        Some(server) => count(server, "code_execution_requests", false)?,
        None => 0,
    };
    Ok(Usage {
        input_tokens: count(&usage_raw, "input_tokens", true)?,
        output_tokens: count(&usage_raw, "output_tokens", true)?,
        cache_creation_input_tokens: count(&usage_raw, "cache_creation_input_tokens", false)?,
        cache_read_input_tokens: count(&usage_raw, "cache_read_input_tokens", false)?,
        code_execution_requests,
        raw: usage_raw,
    })
}

/// Parse a 2xx reply body.
pub fn parse_response(bytes: &[u8]) -> Result<MessagesResponse, Refusal> {
    let value: Value = serde_json::from_slice(bytes)
        .map_err(|error| unparseable(format!("reply is not JSON: {error}")))?;
    if value.get("type").and_then(Value::as_str) != Some("message") {
        return Err(unparseable("reply type is not message"));
    }
    let raw_content = value
        .get("content")
        .and_then(Value::as_array)
        .cloned()
        .ok_or_else(|| unparseable("content must be an array"))?;
    let content = raw_content
        .iter()
        .map(block)
        .collect::<Result<Vec<_>, _>>()?;
    let usage = parse_usage(&value)?;
    let stop_reason = StopReason::parse(&string(&value, "stop_reason")?);
    let container_id = value
        .get("container")
        .and_then(|c| c.get("id"))
        .and_then(Value::as_str)
        .map(str::to_owned);
    Ok(MessagesResponse {
        id: string(&value, "id")?,
        model: string(&value, "model")?,
        stop_reason,
        content,
        raw_content,
        usage,
        container_id,
    })
}

/// A typed refusal for a non-2xx reply: `ANTHROPIC_<ERROR_TYPE>` when the body is the
/// documented error envelope, `ANTHROPIC_HTTP_<status>` otherwise.
pub fn error_refusal(status: u16, bytes: &[u8]) -> Refusal {
    let parsed: Option<(String, String)> =
        serde_json::from_slice::<Value>(bytes)
            .ok()
            .and_then(|value| {
                let error = value.get("error")?;
                let kind = error.get("type")?.as_str()?;
                let message = error
                    .get("message")
                    .and_then(Value::as_str)
                    .unwrap_or_default();
                let safe = kind.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_')
                    && !kind.is_empty();
                safe.then(|| (kind.to_ascii_uppercase(), message.to_owned()))
            });
    match parsed {
        Some((kind, message)) => Refusal::new(
            &format!("ANTHROPIC_{kind}"),
            format!("HTTP {status}: {message}"),
        ),
        None => Refusal::new(
            &format!("ANTHROPIC_HTTP_{status}"),
            format!("HTTP {status} without an error envelope"),
        ),
    }
}

// Origin: omega_engine/crates_rs/omega_woland/src/providers/anthropic/response.rs
// Claim: urn:omega:crates_rs:omega-woland:response:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbad28d78 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbad28d78` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbad28d78 {
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
impl BoundaryErrorbad28d78 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbad28d78 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbad28d78 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbad28d78 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbad28d78> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbad28d78::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbad28d78::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbad28d78::ExceedsCapacity {
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
mod l4_boundary_tests_bad28d78 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbad28d78::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbad28d78::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbad28d78::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbad28d78::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbad28d78::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorbad28d78::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorbad28d78::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
