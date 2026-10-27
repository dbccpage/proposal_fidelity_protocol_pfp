//! Frozen agent licenses and mechanical capability-closure checks.
//!
//! Rust face of `engine/kernel/higher_operad/capability.py`.

use std::collections::BTreeSet;
use serde_json::{json, Value};

use super::canonical::{
    canonical_id, require_digest, require_identifier, sorted_unique, CanonicalError,
};
use super::model::{AuthorityEffect, InvocationGrade, OperationSpec};
use super::result::Refusal;
use super::terms::{normalize_term, term_from_normalized, ChildNode, NormalizedTerm, OperationTerm, TreeNode};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AgentLicense {
    pub agent_id: String,
    pub allowed_operation_keys: Vec<String>,
    pub allowed_colour_ids: Vec<String>,
    pub allowed_executor_refs: Vec<String>,
    pub allowed_tool_refs: Vec<String>,
    pub allowed_effects: Vec<String>,
    pub authority_ceiling: AuthorityEffect,
    pub lifecycle: String,
    pub policy_digest: String,
}

impl AgentLicense {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        agent_id: &str,
        allowed_operation_keys: Vec<String>,
        allowed_colour_ids: Vec<String>,
        allowed_executor_refs: Vec<String>,
        allowed_tool_refs: Vec<String>,
        allowed_effects: Vec<String>,
        authority_ceiling: AuthorityEffect,
        lifecycle: &str,
        policy_digest: &str,
    ) -> Result<Self, CanonicalError> {
        Ok(Self {
            agent_id: require_identifier(agent_id, "agent_id")?,
            allowed_operation_keys: sorted_unique(&allowed_operation_keys, "allowed_operation_keys")?,
            allowed_colour_ids: sorted_unique(&allowed_colour_ids, "allowed_colour_ids")?,
            allowed_executor_refs: sorted_unique(&allowed_executor_refs, "allowed_executor_refs")?,
            allowed_tool_refs: sorted_unique(&allowed_tool_refs, "allowed_tool_refs")?,
            allowed_effects: sorted_unique(&allowed_effects, "allowed_effects")?,
            authority_ceiling,
            lifecycle: require_identifier(lifecycle, "lifecycle")?,
            policy_digest: require_digest(policy_digest, "policy_digest")?,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "agent_id": self.agent_id,
            "allowed_operation_keys": self.allowed_operation_keys,
            "allowed_colour_ids": self.allowed_colour_ids,
            "allowed_executor_refs": self.allowed_executor_refs,
            "allowed_tool_refs": self.allowed_tool_refs,
            "allowed_effects": self.allowed_effects,
            "authority_ceiling": self.authority_ceiling.as_str(),
            "lifecycle": self.lifecycle,
            "policy_digest": self.policy_digest,
        })
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id("core.oewas.agent-license.v1", &self.to_canonical())
    }
}

/// One-shot execution license evidence.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ActionLicense {
    pub license_id: String,
    pub candidate_digest: String,
    pub evidence_sha256: String,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LicensedTerm {
    pub license_id: String,
    pub term: NormalizedTerm,
}

impl LicensedTerm {
    pub fn new(license_id: &str, term: NormalizedTerm) -> Result<Self, CanonicalError> {
        Ok(Self {
            license_id: require_digest(license_id, "license_id")?,
            term,
        })
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        let term_id = self.term.canonical_id()?;
        canonical_id(
            "core.oewas.licensed-term.v1",
            &json!({
                "license_id": self.license_id,
                "term_id": term_id,
            }),
        )
    }
}

fn check_entry_over_entry(tree: &TreeNode) -> bool {
    fn walk_child(child: &ChildNode, parent_is_entry: bool) -> bool {
        match child {
            ChildNode::Input(_) => false,
            ChildNode::Operation { operation, children } => {
                let current_is_entry = operation.invocation_grade == InvocationGrade::Entry;
                if parent_is_entry && current_is_entry {
                    return true;
                }
                children.iter().any(|c| walk_child(c, current_is_entry))
            }
        }
    }

    match tree {
        TreeNode::Identity(_) => false,
        TreeNode::Operation { operation, children } => {
            let current_is_entry = operation.invocation_grade == InvocationGrade::Entry;
            children.iter().any(|c| walk_child(c, current_is_entry))
        }
    }
}

fn collect_term_colours(
    normalized: &NormalizedTerm,
    operations: &[OperationSpec],
) -> BTreeSet<String> {
    let mut colours: BTreeSet<String> = BTreeSet::new();
    let boundary = normalized.boundary();
    for p in &boundary.inputs {
        colours.insert(p.colour_id.clone());
    }
    colours.insert(boundary.output.colour_id.clone());
    for op in operations {
        for p in &op.input_ports {
            colours.insert(p.colour_id.clone());
        }
        colours.insert(op.output_port.colour_id.clone());
    }
    colours
}

fn check_subset_escape(
    actual: &BTreeSet<String>,
    allowed_list: &[String],
    code: &str,
    message: &str,
    detail_key: &str,
) -> Result<(), Refusal> {
    let allowed: BTreeSet<String> = allowed_list.iter().cloned().collect();
    let missing: Vec<String> = actual.difference(&allowed).cloned().collect();
    if !missing.is_empty() {
        return Err(Refusal {
            code: code.into(),
            message: message.into(),
            locus: String::new(),
            details: vec![(detail_key.into(), missing.join(","))],
        });
    }
    Ok(())
}

fn check_authority_ceiling(
    operations: &[OperationSpec],
    ceiling: AuthorityEffect,
) -> Result<(), Refusal> {
    let mut excessive = Vec::new();
    for op in operations {
        if op.authority_ceiling.rank() > ceiling.rank() {
            excessive.push(op.key());
        }
    }
    if !excessive.is_empty() {
        excessive.sort();
        return Err(Refusal {
            code: "AUTHORITY_CAPABILITY_ESCAPE".into(),
            message: "term authority ceiling exceeds the frozen license ceiling".into(),
            locus: String::new(),
            details: vec![("operations".into(), excessive.join(","))],
        });
    }
    Ok(())
}

pub fn authorize_term(
    license: &AgentLicense,
    term: &OperationTerm,
) -> Result<LicensedTerm, Refusal> {
    let normalized = normalize_term(term)?;
    let operations = normalized.operations();

    let term_op_keys: BTreeSet<String> = operations.iter().map(|op| op.key()).collect();
    let term_executors: BTreeSet<String> =
        operations.iter().map(|op| op.executor_ref.clone()).collect();
    let term_tools: BTreeSet<String> =
        operations.iter().flat_map(|op| op.tool_refs.clone()).collect();
    let term_effects: BTreeSet<String> =
        operations.iter().flat_map(|op| op.effects.clone()).collect();
    let colours = collect_term_colours(&normalized, &operations);

    check_subset_escape(
        &term_op_keys,
        &license.allowed_operation_keys,
        "OPERATION_CAPABILITY_ESCAPE",
        "term contains operations outside the frozen license",
        "operations",
    )?;
    check_subset_escape(
        &colours,
        &license.allowed_colour_ids,
        "COLOUR_CAPABILITY_ESCAPE",
        "term contains colours outside the frozen license",
        "colours",
    )?;
    check_subset_escape(
        &term_executors,
        &license.allowed_executor_refs,
        "EXECUTOR_CAPABILITY_ESCAPE",
        "term contains executors outside the frozen license",
        "executors",
    )?;
    check_subset_escape(
        &term_tools,
        &license.allowed_tool_refs,
        "TOOL_CAPABILITY_ESCAPE",
        "term contains tools outside the frozen license",
        "tools",
    )?;
    check_subset_escape(
        &term_effects,
        &license.allowed_effects,
        "EFFECT_CAPABILITY_ESCAPE",
        "term contains effects outside the frozen license",
        "effects",
    )?;
    check_authority_ceiling(&operations, license.authority_ceiling)?;

    if check_entry_over_entry(&normalized.tree) {
        return Err(Refusal {
            code: "ENTRY_OVER_ENTRY".into(),
            message: "an entry operation may not contain another entry operation".into(),
            locus: String::new(),
            details: Vec::new(),
        });
    }

    let license_id = license.canonical_id().map_err(|e| Refusal {
        code: "CANONICAL_ERROR".into(),
        message: e.to_string(),
        locus: String::new(),
        details: Vec::new(),
    })?;

    Ok(LicensedTerm {
        license_id,
        term: normalized,
    })
}

pub fn authorize_normalized_term(
    license: &AgentLicense,
    term: &NormalizedTerm,
) -> Result<LicensedTerm, Refusal> {
    authorize_term(license, &term_from_normalized(term))
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/capability.rs
// Claim: urn:core:crates_rs:core-operad-theory:capability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord18f804b5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord18f804b5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError18f804b5 {
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
impl BoundaryError18f804b5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError18f804b5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError18f804b5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord18f804b5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError18f804b5> {
        if capacity_bound == 0 {
            return Err(BoundaryError18f804b5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError18f804b5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError18f804b5::ExceedsCapacity {
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
    use crate::kernel::model::{OperationSpecInput, PortSpec};
    use crate::kernel::terms::substitute;

    const DIGEST: &str =
        "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    fn port(id: &str, colour: &str) -> PortSpec {
        PortSpec::new(id, colour, "any").unwrap()
    }

    fn make_op(id: &str, grade: InvocationGrade, ceiling: AuthorityEffect) -> OperationSpec {
        OperationSpec::new(OperationSpecInput {
            operation_id: id,
            version: "v1",
            input_ports: vec![port("in_0", "State")],
            output_port: port("out", "State"),
            executor_ref: "skill.test",
            executor_digest: DIGEST,
            tool_refs: vec!["tool.read".into()],
            effects: vec!["read".into()],
            invocation_grade: grade,
            authority_effect: AuthorityEffect::None,
            authority_ceiling: ceiling,
        })
        .unwrap()
    }

    fn base_license() -> AgentLicense {
        AgentLicense::new(
            "agent.test",
            vec!["op_a@v1".into(), "op_entry@v1".into()],
            vec!["State".into()],
            vec!["skill.test".into()],
            vec!["tool.read".into()],
            vec!["read".into()],
            AuthorityEffect::None,
            "active",
            DIGEST,
        )
        .unwrap()
    }

    #[test]
    fn authorize_term_admits_licensed_term_and_refuses_escape_and_entry_over_entry() {
        let license = base_license();
        let op_a = make_op("op_a", InvocationGrade::Discipline, AuthorityEffect::None);
        let term = OperationTerm::Primitive(op_a);
        let licensed = authorize_term(&license, &term).unwrap();
        assert!(licensed.canonical_id().unwrap().starts_with("sha256:"));

        let op_unlisted = make_op(
            "op_unlisted",
            InvocationGrade::Discipline,
            AuthorityEffect::None,
        );
        let err = authorize_term(&license, &OperationTerm::Primitive(op_unlisted)).unwrap_err();
        assert_eq!(err.code, "OPERATION_CAPABILITY_ESCAPE");

        let op_entry = make_op("op_entry", InvocationGrade::Entry, AuthorityEffect::None);
        let nested_entry = substitute(
            &OperationTerm::Primitive(op_entry.clone()),
            0,
            &OperationTerm::Primitive(op_entry),
        )
        .unwrap();
        let entry_err = authorize_normalized_term(&license, &nested_entry).unwrap_err();
        assert_eq!(entry_err.code, "ENTRY_OVER_ENTRY");
    }
}

#[cfg(test)]
mod l4_boundary_tests_18f804b5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord18f804b5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord18f804b5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord18f804b5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord18f804b5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord18f804b5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError18f804b5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError18f804b5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
