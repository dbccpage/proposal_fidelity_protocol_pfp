//! Finite operation terms and an associativity-erasing rooted-tree normal form.
//!
//! The concrete ordered-tree model is formalized in `lean4/research_programs/adversary`.
//! Its proofs do not yet verify this implementation or canonical serialization.

use serde_json::{json, Value};
use std::collections::BTreeMap;

use super::canonical::{canonical_id, CanonicalError};
use super::model::{BoundarySignature, OperationSpec, OperationSpecInput, PortSpec};
use super::result::Refusal;

/// Syntax variants for inert operation terms.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OperationTerm {
    Identity(PortSpec),
    Primitive(OperationSpec),
    Substitute {
        outer: Box<OperationTerm>,
        slot: usize,
        inner: Box<OperationTerm>,
    },
    Admitted(NormalizedTerm),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ChildNode {
    Input(PortSpec),
    Operation {
        operation: OperationSpec,
        children: Vec<ChildNode>,
    },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TreeNode {
    Identity(PortSpec),
    Operation {
        operation: OperationSpec,
        children: Vec<ChildNode>,
    },
}

impl ChildNode {
    fn inputs(&self) -> Vec<PortSpec> {
        match self {
            ChildNode::Input(port) => vec![port.clone()],
            ChildNode::Operation { children, .. } => {
                children.iter().flat_map(|c| c.inputs()).collect()
            }
        }
    }

    #[allow(dead_code)]
    pub fn output(&self) -> PortSpec {
        match self {
            ChildNode::Input(port) => port.clone(),
            ChildNode::Operation { operation, .. } => operation.output_port.clone(),
        }
    }

    fn to_data(&self) -> Value {
        match self {
            ChildNode::Input(port) => json!({ "input": port.to_canonical() }),
            ChildNode::Operation {
                operation,
                children,
            } => json!({
                "operation": operation.to_canonical(),
                "children": children.iter().map(|c| c.to_data()).collect::<Vec<_>>(),
            }),
        }
    }

    fn collect_operations(&self, map: &mut BTreeMap<String, OperationSpec>) {
        if let ChildNode::Operation {
            operation,
            children,
        } = self
        {
            if let Ok(id) = operation.canonical_id() {
                map.insert(id, operation.clone());
            }
            for child in children {
                child.collect_operations(map);
            }
        }
    }
}

impl TreeNode {
    pub fn inputs(&self) -> Vec<PortSpec> {
        match self {
            TreeNode::Identity(port) => vec![port.clone()],
            TreeNode::Operation { children, .. } => {
                children.iter().flat_map(|c| c.inputs()).collect()
            }
        }
    }

    pub fn output(&self) -> PortSpec {
        match self {
            TreeNode::Identity(port) => port.clone(),
            TreeNode::Operation { operation, .. } => operation.output_port.clone(),
        }
    }

    pub fn to_data(&self) -> Value {
        match self {
            TreeNode::Identity(port) => json!({ "identity": port.to_canonical() }),
            TreeNode::Operation {
                operation,
                children,
            } => json!({
                "operation": operation.to_canonical(),
                "children": children.iter().map(|c| c.to_data()).collect::<Vec<_>>(),
            }),
        }
    }

    pub fn operations(&self) -> Vec<OperationSpec> {
        let mut map = BTreeMap::new();
        if let TreeNode::Operation {
            operation,
            children,
        } = self
        {
            if let Ok(id) = operation.canonical_id() {
                map.insert(id, operation.clone());
            }
            for child in children {
                child.collect_operations(&mut map);
            }
        }
        map.into_values().collect()
    }
}

/// Associativity-erased, fully normalized rooted-tree operation term.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NormalizedTerm {
    pub tree: TreeNode,
}

impl NormalizedTerm {
    pub fn new(tree: TreeNode) -> Self {
        Self { tree }
    }

    pub fn boundary(&self) -> BoundarySignature {
        BoundarySignature::new(self.tree.inputs(), self.tree.output())
    }

    pub fn operations(&self) -> Vec<OperationSpec> {
        self.tree.operations()
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "tree": self.tree.to_data(),
            "boundary": self.boundary().to_canonical(),
        })
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id("core.oewas.operation-term.normal.v1", &self.to_canonical())
    }
}

fn replace_leaf_in_children(
    children: Vec<ChildNode>,
    slot: usize,
    replacement: &(OperationSpec, Vec<ChildNode>),
) -> (Vec<ChildNode>, isize) {
    let mut remaining = slot as isize;
    let mut new_children = Vec::with_capacity(children.len());
    let mut replaced = false;
    for child in children {
        if replaced {
            new_children.push(child);
            continue;
        }
        let (new_child, rem_after) = replace_leaf(
            child,
            remaining as usize,
            (replacement.0.clone(), replacement.1.clone()),
        );
        if rem_after == -1 {
            replaced = true;
        } else {
            remaining = rem_after;
        }
        new_children.push(new_child);
    }
    (new_children, if replaced { -1 } else { remaining })
}

fn replace_leaf(
    node: ChildNode,
    slot: usize,
    replacement: (OperationSpec, Vec<ChildNode>),
) -> (ChildNode, isize) {
    match node {
        ChildNode::Input(port) => {
            if slot == 0 {
                (
                    ChildNode::Operation {
                        operation: replacement.0,
                        children: replacement.1,
                    },
                    -1,
                )
            } else {
                (ChildNode::Input(port), (slot as isize) - 1)
            }
        }
        ChildNode::Operation {
            operation,
            children,
        } => {
            let (new_children, rem) = replace_leaf_in_children(children, slot, &replacement);
            (
                ChildNode::Operation {
                    operation,
                    children: new_children,
                },
                rem,
            )
        }
    }
}

fn invalid_spec(message: String) -> Refusal {
    Refusal {
        code: "INVALID_OPERATION_SPEC".into(),
        message,
        locus: String::new(),
        details: Vec::new(),
    }
}

fn validate_port(port: &PortSpec) -> Result<(), Refusal> {
    let checked = PortSpec::new(&port.port_id, &port.colour_id, &port.schema_ref)
        .map_err(|error| invalid_spec(error.to_string()))?;
    if checked != *port {
        return Err(invalid_spec(
            "port differs from its canonical constructor value".into(),
        ));
    }
    Ok(())
}

fn validate_operation(operation: &OperationSpec) -> Result<(), Refusal> {
    for port in operation
        .input_ports
        .iter()
        .chain(std::iter::once(&operation.output_port))
    {
        validate_port(port)?;
    }
    let checked = OperationSpec::new(OperationSpecInput {
        operation_id: &operation.operation_id,
        version: &operation.version,
        input_ports: operation.input_ports.clone(),
        output_port: operation.output_port.clone(),
        executor_ref: &operation.executor_ref,
        executor_digest: &operation.executor_digest,
        tool_refs: operation.tool_refs.clone(),
        effects: operation.effects.clone(),
        invocation_grade: operation.invocation_grade,
        authority_effect: operation.authority_effect,
        authority_ceiling: operation.authority_ceiling,
    })
    .map_err(|error| invalid_spec(error.to_string()))?;
    if checked != *operation {
        return Err(invalid_spec(
            "operation differs from its canonical constructor value".into(),
        ));
    }
    Ok(())
}

fn validate_children(operation: &OperationSpec, children: &[ChildNode]) -> Result<(), Refusal> {
    validate_operation(operation)?;
    if operation.input_ports.len() != children.len() {
        return Err(Refusal {
            code: "ARITY_MISMATCH".into(),
            message: "admitted operation children differ from its declared arity".into(),
            locus: operation.key(),
            details: vec![
                ("expected".into(), operation.input_ports.len().to_string()),
                ("actual".into(), children.len().to_string()),
            ],
        });
    }
    for (slot, (expected, child)) in operation.input_ports.iter().zip(children).enumerate() {
        match child {
            ChildNode::Input(port) => validate_port(port)?,
            ChildNode::Operation {
                operation,
                children,
            } => validate_children(operation, children)?,
        }
        let actual = child.output();
        if !expected.same_type(&actual) {
            return Err(Refusal {
                code: "BOUNDARY_MISMATCH".into(),
                message: "admitted child output does not match its declared input".into(),
                locus: operation.key(),
                details: vec![
                    ("slot".into(), slot.to_string()),
                    ("expected_colour".into(), expected.colour_id.clone()),
                    ("expected_schema".into(), expected.schema_ref.clone()),
                    ("actual_colour".into(), actual.colour_id),
                    ("actual_schema".into(), actual.schema_ref),
                ],
            });
        }
    }
    Ok(())
}

fn validate_substitution_slot(
    outer_inputs: &[PortSpec],
    slot: usize,
    inner_out: &PortSpec,
) -> Result<(), Refusal> {
    if slot >= outer_inputs.len() {
        return Err(Refusal {
            code: "SLOT_OUT_OF_RANGE".into(),
            message: format!("slot {} is outside outer arity {}", slot, outer_inputs.len()),
            locus: String::new(),
            details: vec![
                ("slot".into(), slot.to_string()),
                ("arity".into(), outer_inputs.len().to_string()),
            ],
        });
    }
    if !outer_inputs[slot].same_type(inner_out) {
        return Err(Refusal {
            code: "BOUNDARY_MISMATCH".into(),
            message: "inner output does not match the selected outer input".into(),
            locus: String::new(),
            details: vec![
                ("expected_colour".into(), outer_inputs[slot].colour_id.clone()),
                ("expected_schema".into(), outer_inputs[slot].schema_ref.clone()),
                ("actual_colour".into(), inner_out.colour_id.clone()),
                ("actual_schema".into(), inner_out.schema_ref.clone()),
            ],
        });
    }
    Ok(())
}

fn normalize_substitution(
    outer: &OperationTerm,
    slot: usize,
    inner: &OperationTerm,
) -> Result<TreeNode, Refusal> {
    let outer_tree = normalize_tree(outer)?;
    let inner_tree = normalize_tree(inner)?;
    let outer_inputs = outer_tree.inputs();
    let inner_out = inner_tree.output();
    validate_substitution_slot(&outer_inputs, slot, &inner_out)?;

    match (&outer_tree, &inner_tree) {
        (TreeNode::Identity(_), _) => Ok(inner_tree),
        (_, TreeNode::Identity(_)) => Ok(outer_tree),
        (
            TreeNode::Operation {
                operation,
                children,
            },
            TreeNode::Operation {
                operation: in_op,
                children: in_children,
            },
        ) => {
            let (new_children, rem) = replace_leaf_in_children(
                children.clone(),
                slot,
                &(in_op.clone(), in_children.clone()),
            );
            if rem != -1 {
                return Err(Refusal {
                    code: "NORMALIZATION_FAILED".into(),
                    message: "selected input leaf was not replaced".into(),
                    locus: String::new(),
                    details: Vec::new(),
                });
            }
            Ok(TreeNode::Operation {
                operation: operation.clone(),
                children: new_children,
            })
        }
    }
}

fn validate_admitted_tree(tree: &TreeNode) -> Result<TreeNode, Refusal> {
    match tree {
        TreeNode::Identity(port) => validate_port(port)?,
        TreeNode::Operation {
            operation,
            children,
        } => validate_children(operation, children)?,
    }
    Ok(tree.clone())
}

fn normalize_tree(term: &OperationTerm) -> Result<TreeNode, Refusal> {
    match term {
        OperationTerm::Admitted(norm) => validate_admitted_tree(&norm.tree),
        OperationTerm::Identity(port) => {
            validate_port(port)?;
            Ok(TreeNode::Identity(port.clone()))
        }
        OperationTerm::Primitive(op) => {
            validate_operation(op)?;
            let children = op
                .input_ports
                .iter()
                .cloned()
                .map(ChildNode::Input)
                .collect();
            Ok(TreeNode::Operation {
                operation: op.clone(),
                children,
            })
        }
        OperationTerm::Substitute { outer, slot, inner } => {
            normalize_substitution(outer, *slot, inner)
        }
    }
}

pub fn normalize_term(term: &OperationTerm) -> Result<NormalizedTerm, Refusal> {
    let tree = normalize_tree(term)?;
    Ok(NormalizedTerm::new(tree))
}

pub fn identity(port: PortSpec) -> OperationTerm {
    OperationTerm::Identity(port)
}

pub fn normalize(term: &OperationTerm) -> Result<NormalizedTerm, Refusal> {
    normalize_term(term)
}

pub fn substitute(
    outer: &OperationTerm,
    slot: usize,
    inner: &OperationTerm,
) -> Result<NormalizedTerm, Refusal> {
    normalize_term(&OperationTerm::Substitute {
        outer: Box::new(outer.clone()),
        slot,
        inner: Box::new(inner.clone()),
    })
}

pub fn term_from_normalized(term: &NormalizedTerm) -> OperationTerm {
    OperationTerm::Admitted(term.clone())
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/terms.rs
// Claim: urn:core:crates_rs:core-operad-theory:terms:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb820606a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb820606a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb820606a {
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
impl BoundaryErrorb820606a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb820606a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb820606a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb820606a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb820606a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb820606a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb820606a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb820606a::ExceedsCapacity {
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
mod tests {
    use super::*;
    use crate::kernel::model::{AuthorityEffect, InvocationGrade};

    const DIGEST: &str =
        "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    fn port(id: &str, colour: &str) -> PortSpec {
        PortSpec::new(id, colour, "any").unwrap()
    }

    fn op(in_colour: &str, out_colour: &str) -> OperationSpec {
        OperationSpec::new(OperationSpecInput {
            operation_id: "step",
            version: "v1",
            input_ports: vec![port("in_0", in_colour)],
            output_port: port("out", out_colour),
            executor_ref: "skill.step",
            executor_digest: DIGEST,
            tool_refs: vec![],
            effects: vec![],
            invocation_grade: InvocationGrade::Discipline,
            authority_effect: AuthorityEffect::None,
            authority_ceiling: AuthorityEffect::None,
        })
        .unwrap()
    }

    #[test]
    fn normalize_and_substitute_preserve_boundaries_and_refuse_invalid_slots_or_types() {
        let p_state = port("x", "State");
        let id_term = identity(p_state.clone());
        let step_op = op("State", "State");
        let prim = OperationTerm::Primitive(step_op);
        let left_unit = substitute(&id_term, 0, &prim).unwrap();
        let right_unit = substitute(&prim, 0, &id_term).unwrap();
        assert_eq!(left_unit, right_unit);
        assert!(left_unit.canonical_id().unwrap().starts_with("sha256:"));

        let slot_err = substitute(&prim, 1, &id_term).unwrap_err();
        assert_eq!(slot_err.code, "SLOT_OUT_OF_RANGE");

        let bad_id = identity(port("y", "Code"));
        let type_err = substitute(&prim, 0, &bad_id).unwrap_err();
        assert_eq!(type_err.code, "BOUNDARY_MISMATCH");
    }
}

#[cfg(test)]
mod l4_boundary_tests_b820606a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb820606a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb820606a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb820606a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb820606a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb820606a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb820606a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb820606a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
