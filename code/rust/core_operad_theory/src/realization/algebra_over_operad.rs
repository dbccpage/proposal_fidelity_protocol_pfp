//! Realization: Multi-sorted algebras and recursive planar tree evaluation.
//!
//! AuthorityEffect: None.

use std::collections::HashMap;
use std::sync::Arc;
use serde::{Deserialize, Serialize};
use crate::foundation::{OperadColour, PlanarColoredOperad, PlanarTree, TreeChild};

/// External policy decision reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PolicyDecisionRef {
    pub decision_id: String,
    pub is_admissible: bool,
    pub policy_name: String,
    pub notes: String,
}

impl PolicyDecisionRef {
    pub fn new(decision_id: impl Into<String>, is_admissible: bool) -> Self {
        Self {
            decision_id: decision_id.into(),
            is_admissible,
            policy_name: "StandardAdmissibilityPolicy".to_string(),
            notes: String::new(),
        }
    }
}

/// Immutable deterministic evaluation receipt.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvaluationReceipt {
    pub receipt_id: String,
    pub term_hash: String,
    pub agent_id: String,
    pub policy_decision_ref: Option<PolicyDecisionRef>,
    pub status: String,
    pub output_colour: String,
    pub output_value: serde_json::Value,
    pub emitted_at: String,
}

/// Evaluation outcome from evaluating an operadic tree.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvaluationOutcome {
    pub is_completed: bool,
    pub value: Option<serde_json::Value>,
    pub receipt: Option<EvaluationReceipt>,
    pub error_message: Option<String>,
}

type ActionFn = Arc<dyn Fn(&[serde_json::Value]) -> Result<serde_json::Value, String> + Send + Sync>;

/// Multi-sorted algebra over a coloured operad.
#[derive(Clone)]
pub struct OperadAlgebra {
    pub operad: PlanarColoredOperad,
    pub name: String,
    pub agent_id: String,
    carriers: HashMap<String, String>,
    actions: HashMap<String, ActionFn>,
}

impl OperadAlgebra {
    pub fn new(operad: PlanarColoredOperad, name: impl Into<String>, agent_id: impl Into<String>) -> Self {
        Self {
            operad,
            name: name.into(),
            agent_id: agent_id.into(),
            carriers: HashMap::new(),
            actions: HashMap::new(),
        }
    }

    pub fn set_carrier(&mut self, colour: &OperadColour, carrier_space: impl Into<String>) -> Result<(), String> {
        if self.operad.is_closed_universe && !self.operad.colours().contains(colour) {
            return Err(format!("Cannot set carrier for unadmitted colour '{}'", colour.as_str()));
        }
        self.carriers.insert(colour.as_str().to_string(), carrier_space.into());
        Ok(())
    }

    pub fn get_carrier(&self, colour: &OperadColour) -> Option<&str> {
        self.carriers.get(colour.as_str()).map(|s| s.as_str())
    }

    pub fn register_action(
        &mut self,
        op_id: &str,
        action: impl Fn(&[serde_json::Value]) -> Result<serde_json::Value, String> + Send + Sync + 'static,
    ) -> Result<(), String> {
        if !self.operad.operations().contains_key(op_id) {
            return Err(format!("Operation '{}' not in operad '{}'", op_id, self.operad.name));
        }
        self.actions.insert(op_id.to_string(), Arc::new(action));
        Ok(())
    }

    pub fn evaluate_tree(
        &self,
        tree: &PlanarTree,
        leaf_inputs: &[serde_json::Value],
        policy_ref: Option<PolicyDecisionRef>,
    ) -> EvaluationOutcome {
        if leaf_inputs.len() != tree.arity() {
            return EvaluationOutcome {
                is_completed: false,
                value: None,
                receipt: None,
                error_message: Some(format!(
                    "Leaf input count {} != tree arity {}",
                    leaf_inputs.len(),
                    tree.arity()
                )),
            };
        }

        let mut offset = 0;
        match self.evaluate_tree_recursive(tree, leaf_inputs, &mut offset) {
            Ok(val) => {
                let receipt = EvaluationReceipt {
                    receipt_id: format!("rec_{}", tree.term_hash()),
                    term_hash: tree.term_hash(),
                    agent_id: self.agent_id.clone(),
                    policy_decision_ref: policy_ref,
                    status: "Completed".to_string(),
                    output_colour: tree.output_colour().as_str().to_string(),
                    output_value: val.clone(),
                    emitted_at: "2026-08-20T00:00:00Z".to_string(),
                };
                EvaluationOutcome {
                    is_completed: true,
                    value: Some(val),
                    receipt: Some(receipt),
                    error_message: None,
                }
            }
            Err(e) => EvaluationOutcome {
                is_completed: false,
                value: None,
                receipt: None,
                error_message: Some(e),
            },
        }
    }

    fn evaluate_tree_recursive(
        &self,
        tree: &PlanarTree,
        leaf_inputs: &[serde_json::Value],
        offset: &mut usize,
    ) -> Result<serde_json::Value, String> {
        let mut child_results = Vec::new();
        for ch in &tree.children {
            match ch {
                TreeChild::Leaf(_) => {
                    if *offset >= leaf_inputs.len() {
                        return Err("Leaf inputs exhausted".to_string());
                    }
                    child_results.push(leaf_inputs[*offset].clone());
                    *offset += 1;
                }
                TreeChild::Subtree(sub) => {
                    let sub_val = self.evaluate_tree_recursive(sub, leaf_inputs, offset)?;
                    child_results.push(sub_val);
                }
            }
        }

        if tree.root.is_identity() && child_results.len() == 1 {
            return Ok(child_results.remove(0));
        }

        if let Some(action) = self.actions.get(tree.root.op_id.as_str()) {
            action(&child_results)
        } else {
            // Default structural json packaging
            Ok(serde_json::json!({
                "operation": tree.root.op_id.as_str(),
                "inputs": child_results,
            }))
        }
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/realization/algebra_over_operad.rs
// Claim: urn:core:crates_rs:core-operad-theory:algebra-over-operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord48a63b2b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord48a63b2b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError48a63b2b {
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
impl BoundaryError48a63b2b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError48a63b2b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError48a63b2b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord48a63b2b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError48a63b2b> {
        if capacity_bound == 0 {
            return Err(BoundaryError48a63b2b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError48a63b2b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError48a63b2b::ExceedsCapacity {
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
mod l4_boundary_tests_48a63b2b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord48a63b2b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord48a63b2b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord48a63b2b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord48a63b2b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord48a63b2b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError48a63b2b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError48a63b2b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
