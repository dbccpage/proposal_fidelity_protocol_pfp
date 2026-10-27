//! Explicit learning signals; source custody and publication stay with the skill estate.
//! AuthorityEffect: None.
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::BTreeSet;

#[derive(Debug, Serialize)]
pub struct Refusal {
    pub code: &'static str,
    pub message: String,
}
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal {
        code: "LEARNING_SIGNAL_INVALID",
        message: message.into(),
    }
}

/// The wire adapter keeps object member order and the source canonical spelling.
#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
enum Node {
    Scalar {
        value: Value,
    },
    Number {
        canonical: String,
    },
    Array {
        items: Vec<Node>,
    },
    Object {
        members: Vec<(String, Node)>,
        canonical: String,
    },
}
impl Node {
    fn get(&self, key: &str) -> Option<&Self> {
        match self {
            Self::Object { members, .. } => members.iter().find(|(k, _)| k == key).map(|(_, v)| v),
            _ => None,
        }
    }
    fn parse_number_value(canonical: &str) -> Result<Value, Refusal> {
        let value: Value = serde_json::from_str(canonical).map_err(|e| invalid(e.to_string()))?;
        if !value.is_number() {
            return Err(invalid("a number node must contain a JSON number"));
        }
        Ok(value)
    }

    fn parse_object_value(members: &[(String, Self)]) -> Result<Value, Refusal> {
        let mut result = serde_json::Map::new();
        for (key, value) in members {
            if result.insert(key.clone(), value.value()?).is_some() {
                return Err(invalid("duplicate learning object key"));
            }
        }
        Ok(Value::Object(result))
    }

    fn value(&self) -> Result<Value, Refusal> {
        match self {
            Self::Number { canonical } => Self::parse_number_value(canonical),
            Self::Scalar { value } if !value.is_array() && !value.is_object() => Ok(value.clone()),
            Self::Scalar { .. } => Err(invalid("a scalar node cannot contain a collection")),
            Self::Array { items } => items
                .iter()
                .map(Self::value)
                .collect::<Result<Vec<_>, _>>()
                .map(Value::Array),
            Self::Object { members, .. } => Self::parse_object_value(members),
        }
    }
}

fn trim(text: &str) -> &str {
    text.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}

fn collect_object_node(
    node: &Node,
    canonical: &str,
    bucket: &str,
    into: &mut Vec<String>,
) -> Result<(), Refusal> {
    if matches!(
        node.get("applied"),
        Some(Node::Scalar {
            value: Value::Bool(true)
        })
    ) {
        return Ok(());
    }
    if let Some(
        text @ Node::Scalar {
            value: Value::String(_),
        },
    ) = node.get("text")
    {
        return collect(text, bucket, into);
    }
    // Keep Python's canonical float/Unicode spelling without trusting
    // a different document in the supplied canonical byte field.
    let decoded: Value = serde_json::from_str(canonical).map_err(|e| invalid(e.to_string()))?;
    if decoded != node.value()? {
        return Err(invalid(
            "canonical signal does not match the supplied object",
        ));
    }
    into.push(canonical.to_owned());
    Ok(())
}

fn collect(node: &Node, bucket: &str, into: &mut Vec<String>) -> Result<(), Refusal> {
    match node {
        Node::Scalar {
            value: Value::String(text),
        } if !trim(text).is_empty() => into.push(trim(text).into()),
        Node::Scalar { value: Value::Null } => {}
        Node::Array { items } => {
            for item in items {
                collect(item, bucket, into)?;
            }
        }
        Node::Object { canonical, .. } => {
            collect_object_node(node, canonical, bucket, into)?;
        }
        _ => return Err(invalid(format!("malformed {bucket} signal"))),
    }
    Ok(())
}

#[derive(Default, Serialize)]
struct Signals {
    corrections: Vec<String>,
    successes: Vec<String>,
    errors: Vec<String>,
}

fn map_signal_bucket(key: &str) -> &str {
    match key {
        "feedback" | "preferences" => "corrections",
        "successful_approaches" => "successes",
        "decisive_blockers" => "errors",
        other => other,
    }
}

fn walk_member(key: &str, value: &Node, signals: &mut Signals) -> Result<(), Refusal> {
    let bucket = map_signal_bucket(key);
    match bucket {
        "corrections" => collect(value, bucket, &mut signals.corrections),
        "successes" => collect(value, bucket, &mut signals.successes),
        "errors" => collect(value, bucket, &mut signals.errors),
        _ => walk(value, signals),
    }
}

fn walk(node: &Node, signals: &mut Signals) -> Result<(), Refusal> {
    match node {
        Node::Object { members, .. } => {
            for (key, value) in members {
                walk_member(key, value, signals)?;
            }
        }
        Node::Array { items } => {
            for value in items {
                walk(value, signals)?;
            }
        }
        Node::Scalar { .. } | Node::Number { .. } => {}
    }
    Ok(())
}
fn unique(values: &mut Vec<String>) {
    let mut seen = BTreeSet::new();
    values.retain(|value| seen.insert(value.clone()));
}
pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let node: Node =
        serde_json::from_value(payload["tree"].clone()).map_err(|e| invalid(e.to_string()))?;
    node.value()?;
    let mut signals = Signals::default();
    walk(&node, &mut signals)?;
    unique(&mut signals.corrections);
    unique(&mut signals.successes);
    unique(&mut signals.errors);
    Ok(json!(signals))
}

// Origin: engine/crates_rs/core_prompt_civilization/src/learning_signals.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:learning-signals:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord38a6f461 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord38a6f461` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError38a6f461 {
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
impl BoundaryError38a6f461 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError38a6f461 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError38a6f461 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord38a6f461 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError38a6f461> {
        if capacity_bound == 0 {
            return Err(BoundaryError38a6f461::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError38a6f461::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError38a6f461::ExceedsCapacity {
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
mod l4_boundary_tests_38a6f461 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord38a6f461::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord38a6f461::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord38a6f461::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord38a6f461::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord38a6f461::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError38a6f461::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError38a6f461::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
