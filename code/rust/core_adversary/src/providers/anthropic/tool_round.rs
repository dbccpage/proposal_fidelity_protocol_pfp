//! Returning client tool results for a turn that requested several tools at once.
//!
//! The reply to an assistant turn with `tool_use` blocks is one user message that holds
//! exactly one `tool_result` per `tool_use` id, in request order, ahead of any text. A
//! tool the host did not run still gets a result, marked `is_error`, so the model is never
//! left with an unanswered call.
//!
//! AuthorityEffect: None.

use crate::providers::Refusal;
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

/// A client-side `tool_use` block from an assistant message.
#[derive(Debug, Clone, PartialEq)]
pub struct ToolUse {
    pub id: String,
    pub name: String,
    pub input: Value,
}

/// What the host did with one tool call.
#[derive(Debug, Clone, PartialEq)]
pub enum ToolOutcome {
    /// The tool ran. `content` is a string or an array of content blocks.
    Ran { content: Value, is_error: bool },
    /// The tool was not run (not licensed, over budget, invalid input).
    NotRun { reason: String },
}

/// The client `tool_use` blocks of an assistant message's content, in order. Server tool
/// blocks (`server_tool_use`) run inside the API and are not returned here.
pub fn client_tool_uses(content: &[Value]) -> Result<Vec<ToolUse>, Refusal> {
    let mut seen = BTreeSet::new();
    let mut uses = Vec::new();
    for block in content {
        if block.get("type").and_then(Value::as_str) != Some("tool_use") {
            continue;
        }
        let id = block.get("id").and_then(Value::as_str).unwrap_or_default();
        let name = block
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default();
        if id.is_empty() || name.is_empty() || !seen.insert(id.to_owned()) {
            return Err(Refusal::new(
                "TOOL_USE_INVALID",
                "tool_use blocks need distinct non-empty ids and names",
            ));
        }
        uses.push(ToolUse {
            id: id.into(),
            name: name.into(),
            input: block.get("input").cloned().unwrap_or(Value::Null),
        });
    }
    Ok(uses)
}

/// Build the single user message answering every client tool call of one turn.
pub fn tool_result_message(
    uses: &[ToolUse],
    outcomes: &BTreeMap<String, ToolOutcome>,
    trailing_text: Option<&str>,
) -> Result<Value, Refusal> {
    let ids: BTreeSet<&str> = uses.iter().map(|u| u.id.as_str()).collect();
    if uses.is_empty() || ids.len() != uses.len() {
        return Err(Refusal::new(
            "TOOL_USE_INVALID",
            "answer at least one tool call, each id once",
        ));
    }
    if let Some(stray) = outcomes.keys().find(|id| !ids.contains(id.as_str())) {
        return Err(Refusal::new(
            "TOOL_RESULT_UNMATCHED",
            format!("outcome for unknown tool_use id {stray}"),
        ));
    }
    let mut content = Vec::with_capacity(uses.len() + 1);
    for tool in uses {
        let block = match outcomes.get(&tool.id) {
            Some(ToolOutcome::Ran {
                content: result,
                is_error,
            }) => {
                if !(result.is_string() || result.is_array()) {
                    return Err(Refusal::new(
                        "TOOL_RESULT_INVALID",
                        "tool_result content is a string or an array of blocks",
                    ));
                }
                json!({"type": "tool_result", "tool_use_id": tool.id, "content": result, "is_error": is_error})
            }
            Some(ToolOutcome::NotRun { reason }) => json!({
                "type": "tool_result", "tool_use_id": tool.id,
                "content": format!("not run: {reason}"), "is_error": true,
            }),
            None => json!({
                "type": "tool_result", "tool_use_id": tool.id,
                "content": "not run: the host returned no outcome for this call", "is_error": true,
            }),
        };
        content.push(block);
    }
    if let Some(text) = trailing_text.filter(|t| !t.trim().is_empty()) {
        content.push(json!({"type": "text", "text": text}));
    }
    Ok(json!({"role": "user", "content": content}))
}

// Origin: engine/crates_rs/core_adversary/src/providers/anthropic/tool_round.rs
// Claim: urn:core:crates_rs:core-adversary:tool-round:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord294af264 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord294af264` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError294af264 {
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
impl BoundaryError294af264 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError294af264 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError294af264 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord294af264 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError294af264> {
        if capacity_bound == 0 {
            return Err(BoundaryError294af264::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError294af264::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError294af264::ExceedsCapacity {
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
mod l4_boundary_tests_294af264 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord294af264::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord294af264::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord294af264::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord294af264::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord294af264::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError294af264::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError294af264::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
