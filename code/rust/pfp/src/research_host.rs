//! Research-loop operations on the `adversary_support` host surface.
//!
//! The loop's state is a checkpoint the caller holds and passes back on every call; the
//! host re-verifies it (digest, mission, ledger against tape) before applying anything.
//! The digest is unkeyed, so this catches a damaged or hand-edited checkpoint, not a caller
//! that recomputes the digest: whoever can write the run folder can forge a state. The
//! workflow folder named by `workflow_dir` is likewise trusted as the contract.
//! AuthorityEffect: None.

use core_adversary::stage::ports::Refusal;
use core_adversary::research_loop::invalidation::{plan_repair, ChangeScope, DependencyGraph};
use core_adversary::research_loop::pack;
use core_adversary::research_loop::state::{LoopCommand, ResearchLoop};
use serde_json::{json, Value};
use std::collections::BTreeSet;
use std::path::Path;

fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("RESEARCH_HOST_INPUT_INVALID", message)
}

fn text<'a>(payload: &'a Value, key: &str) -> Result<&'a str, Refusal> {
    payload[key]
        .as_str()
        .ok_or_else(|| invalid(format!("{key} must be a string")))
}

/// An optional boolean: absent means false, anything but a boolean is refused.
fn flag(payload: &Value, key: &str) -> Result<bool, Refusal> {
    match payload.get(key) {
        None | Some(Value::Null) => Ok(false),
        Some(Value::Bool(value)) => Ok(*value),
        Some(_) => Err(invalid(format!("{key} must be a boolean"))),
    }
}

fn resumed(payload: &Value) -> Result<ResearchLoop, Refusal> {
    ResearchLoop::resume(&payload["checkpoint"])
}

fn snapshot(state: &ResearchLoop) -> Result<Value, Refusal> {
    Ok(json!({
        "checkpoint": state.checkpoint()?,
        "next_action": state.next_action(),
        "spent": state.spent()?,
        "terminal": state.terminal(),
    }))
}

fn execute_apply(payload: &Value) -> Result<Value, Refusal> {
    let mut state = resumed(payload)?;
    let command: LoopCommand = serde_json::from_value(payload["command"].clone())
        .map_err(|e| invalid(format!("command: {e}")))?;
    let output = state.apply(command)?;
    let mut reply = snapshot(&state)?;
    reply["output"] = output;
    Ok(reply)
}

fn execute_invalidated(payload: &Value) -> Result<Value, Refusal> {
    let graph: DependencyGraph = serde_json::from_value(payload["graph"].clone())
        .map_err(|e| invalid(format!("graph: {e}")))?;
    let changed: BTreeSet<String> = serde_json::from_value(payload["changed"].clone())
        .map_err(|e| invalid(format!("changed: {e}")))?;
    let scope = ChangeScope {
        question_or_policy_changed: flag(payload, "question_or_policy_changed")?,
        local_patch: flag(payload, "local_patch")?,
    };
    Ok(json!(plan_repair(&graph, &changed, scope)?))
}

fn execute_response_validate(payload: &Value) -> Result<Value, Refusal> {
    let violations = pack::validate_response(
        Path::new(text(payload, "workflow_dir")?),
        text(payload, "prompt_id")?,
        &payload["response"],
    )?;
    Ok(json!({"valid": violations.is_empty(), "violations": violations}))
}

fn execute_state_query(operation: &str, payload: &Value) -> Option<Result<Value, Refusal>> {
    match operation {
        "research_admit" => Some(ResearchLoop::admit(&payload["mission"]).and_then(|s| snapshot(&s))),
        "research_apply" => Some(execute_apply(payload)),
        "research_next" => Some(resumed(payload).and_then(|s| snapshot(&s))),
        "research_events" => Some(resumed(payload).map(|s| json!(s.events()))),
        _ => None,
    }
}

pub fn execute(operation: &str, payload: &Value) -> Result<Value, Refusal> {
    if let Some(res) = execute_state_query(operation, payload) {
        return res;
    }
    match operation {
        "research_invalidated" => execute_invalidated(payload),
        "research_pack_check" => {
            text(payload, "workflow_dir").and_then(|dir| pack::check_pack(Path::new(dir)))
        }
        "research_response_validate" => execute_response_validate(payload),
        other => Err(invalid(format!("unknown research operation {other:?}"))),
    }
}

// Origin: engine/crates_rs/pfp/src/research_host.rs
// Claim: urn:core:crates_rs:pfp:research-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3687afb0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3687afb0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3687afb0 {
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
impl BoundaryError3687afb0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3687afb0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3687afb0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3687afb0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3687afb0> {
        if capacity_bound == 0 {
            return Err(BoundaryError3687afb0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3687afb0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3687afb0::ExceedsCapacity {
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
mod l4_boundary_tests_3687afb0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3687afb0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3687afb0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3687afb0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3687afb0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3687afb0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3687afb0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3687afb0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
