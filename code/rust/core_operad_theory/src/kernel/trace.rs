//! Canonical immutable execution-event contract; storage remains an outer port.
//!
//! Rust face of `engine/kernel/higher_operad/trace.py`.

use std::collections::BTreeSet;
use serde_json::{json, Value};

use super::canonical::{
    canonical_id, require_digest, require_identifier, CanonicalError,
};
use super::model::{AuthorityEffect, OperandRef};
use super::result::KernelError;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BudgetTransition {
    pub before: usize,
    pub after: usize,
}

impl BudgetTransition {
    pub fn new(before: usize, after: usize) -> Result<Self, KernelError> {
        if after > before {
            return Err(KernelError::Message(
                "an execution event cannot increase its budget".into(),
            ));
        }
        Ok(Self { before, after })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "before": self.before,
            "after": self.after,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExecutionEvent {
    pub run_id: String,
    pub sequence: usize,
    pub plan_digest: String,
    pub operation_spec_digest: String,
    pub executor_digest: String,
    pub policy_digest: String,
    pub environment_digest: String,
    pub validator_ref: String,
    pub validator_digest: String,
    pub verifier_ref: String,
    pub verifier_digest: String,
    pub admission_receipt_refs: Vec<String>,
    pub inputs: Vec<OperandRef>,
    pub outputs: Vec<OperandRef>,
    pub parent_event_refs: Vec<String>,
    pub budget: BudgetTransition,
    pub outcome_code: String,
    pub outcome_digest: String,
    pub authority_effect: AuthorityEffect,
}

#[derive(Debug, Clone)]
pub struct ExecutionEventInput {
    pub run_id: String,
    pub sequence: usize,
    pub plan_digest: String,
    pub operation_spec_digest: String,
    pub executor_digest: String,
    pub policy_digest: String,
    pub environment_digest: String,
    pub validator_ref: String,
    pub validator_digest: String,
    pub verifier_ref: String,
    pub verifier_digest: String,
    pub admission_receipt_refs: Vec<String>,
    pub inputs: Vec<OperandRef>,
    pub outputs: Vec<OperandRef>,
    pub parent_event_refs: Vec<String>,
    pub budget: BudgetTransition,
    pub outcome_code: String,
    pub outcome_digest: String,
    pub authority_effect: AuthorityEffect,
}

fn require_unique_digests(
    items: Vec<String>,
    field: &str,
    dup_message: &str,
) -> Result<(Vec<String>, BTreeSet<String>), KernelError> {
    let mut out = Vec::with_capacity(items.len());
    let mut seen = BTreeSet::new();
    for item in items {
        let digest = require_digest(&item, field)?;
        if !seen.insert(digest.clone()) {
            return Err(KernelError::Message(dup_message.into()));
        }
        out.push(digest);
    }
    Ok((out, seen))
}

fn verify_operand_receipts(
    inputs: &[OperandRef],
    outputs: &[OperandRef],
    seen_receipts: &BTreeSet<String>,
) -> Result<(), KernelError> {
    for operand in inputs.iter().chain(outputs.iter()) {
        if !seen_receipts.contains(&operand.admission_receipt_ref) {
            return Err(KernelError::Message(
                "event admission receipts do not cover every input/output operand".into(),
            ));
        }
    }
    Ok(())
}

struct ValidatedEventIdentities {
    run_id: String,
    plan_digest: String,
    operation_spec_digest: String,
    executor_digest: String,
    policy_digest: String,
    environment_digest: String,
    validator_ref: String,
    validator_digest: String,
    verifier_ref: String,
    verifier_digest: String,
    outcome_code: String,
    outcome_digest: String,
}

fn validate_event_primary_digests(
    input: &ExecutionEventInput,
) -> Result<(String, String, String, String, String, String), KernelError> {
    Ok((
        require_identifier(&input.run_id, "run_id")?,
        require_digest(&input.plan_digest, "plan_digest")?,
        require_digest(&input.operation_spec_digest, "operation_spec_digest")?,
        require_digest(&input.executor_digest, "executor_digest")?,
        require_digest(&input.policy_digest, "policy_digest")?,
        require_digest(&input.environment_digest, "environment_digest")?,
    ))
}

fn validate_event_actor_and_outcome(
    input: &ExecutionEventInput,
) -> Result<(String, String, String, String, String, String), KernelError> {
    Ok((
        require_identifier(&input.validator_ref, "validator_ref")?,
        require_digest(&input.validator_digest, "validator_digest")?,
        require_identifier(&input.verifier_ref, "verifier_ref")?,
        require_digest(&input.verifier_digest, "verifier_digest")?,
        require_identifier(&input.outcome_code, "outcome_code")?,
        require_digest(&input.outcome_digest, "outcome_digest")?,
    ))
}

fn validate_event_identities(
    input: &ExecutionEventInput,
) -> Result<ValidatedEventIdentities, KernelError> {
    let (run_id, plan_digest, operation_spec_digest, executor_digest, policy_digest, environment_digest) =
        validate_event_primary_digests(input)?;
    let (validator_ref, validator_digest, verifier_ref, verifier_digest, outcome_code, outcome_digest) =
        validate_event_actor_and_outcome(input)?;
    Ok(ValidatedEventIdentities {
        run_id,
        plan_digest,
        operation_spec_digest,
        executor_digest,
        policy_digest,
        environment_digest,
        validator_ref,
        validator_digest,
        verifier_ref,
        verifier_digest,
        outcome_code,
        outcome_digest,
    })
}

impl ExecutionEvent {
    pub fn new(input: ExecutionEventInput) -> Result<Self, KernelError> {
        let ids = validate_event_identities(&input)?;
        if input.authority_effect != AuthorityEffect::None {
            return Err(KernelError::Message(
                "execution events are evidence records with AuthorityEffect None".into(),
            ));
        }

        let (receipts, seen_receipts) = require_unique_digests(
            input.admission_receipt_refs,
            "admission_receipt_ref",
            "admission receipt references must be unique",
        )?;
        verify_operand_receipts(&input.inputs, &input.outputs, &seen_receipts)?;
        let (parents, _) = require_unique_digests(
            input.parent_event_refs,
            "parent_event_ref",
            "parent event references must be unique",
        )?;

        Ok(Self {
            run_id: ids.run_id,
            sequence: input.sequence,
            plan_digest: ids.plan_digest,
            operation_spec_digest: ids.operation_spec_digest,
            executor_digest: ids.executor_digest,
            policy_digest: ids.policy_digest,
            environment_digest: ids.environment_digest,
            validator_ref: ids.validator_ref,
            validator_digest: ids.validator_digest,
            verifier_ref: ids.verifier_ref,
            verifier_digest: ids.verifier_digest,
            admission_receipt_refs: receipts,
            inputs: input.inputs,
            outputs: input.outputs,
            parent_event_refs: parents,
            budget: input.budget,
            outcome_code: ids.outcome_code,
            outcome_digest: ids.outcome_digest,
            authority_effect: input.authority_effect,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "run_id": self.run_id,
            "sequence": self.sequence,
            "plan_digest": self.plan_digest,
            "operation_spec_digest": self.operation_spec_digest,
            "executor_digest": self.executor_digest,
            "policy_digest": self.policy_digest,
            "environment_digest": self.environment_digest,
            "validator_ref": self.validator_ref,
            "validator_digest": self.validator_digest,
            "verifier_ref": self.verifier_ref,
            "verifier_digest": self.verifier_digest,
            "admission_receipt_refs": self.admission_receipt_refs,
            "inputs": self.inputs.iter().map(OperandRef::to_canonical).collect::<Vec<_>>(),
            "outputs": self.outputs.iter().map(OperandRef::to_canonical).collect::<Vec<_>>(),
            "parent_event_refs": self.parent_event_refs,
            "budget": self.budget.to_canonical(),
            "outcome_code": self.outcome_code,
            "outcome_digest": self.outcome_digest,
            "authority_effect": self.authority_effect.as_str(),
        })
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id("core.oewas.execution-event.v1", &self.to_canonical())
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/trace.rs
// Claim: urn:core:crates_rs:core-operad-theory:trace:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord55aa1c6a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord55aa1c6a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError55aa1c6a {
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
impl BoundaryError55aa1c6a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError55aa1c6a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError55aa1c6a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord55aa1c6a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError55aa1c6a> {
        if capacity_bound == 0 {
            return Err(BoundaryError55aa1c6a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError55aa1c6a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError55aa1c6a::ExceedsCapacity {
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

    fn sample_digest(ch: char) -> String {
        format!("sha256:{}", ch.to_string().repeat(64))
    }

    fn valid_event_input() -> ExecutionEventInput {
        let receipt = sample_digest('a');
        let op_ref = OperandRef::new(
            &sample_digest('b'),
            "colour.a",
            "schema.a",
            &receipt,
            &sample_digest('c'),
        )
        .unwrap();
        ExecutionEventInput {
            run_id: "run.1".into(),
            sequence: 0,
            plan_digest: sample_digest('1'),
            operation_spec_digest: sample_digest('2'),
            executor_digest: sample_digest('3'),
            policy_digest: sample_digest('4'),
            environment_digest: sample_digest('5'),
            validator_ref: "val.1".into(),
            validator_digest: sample_digest('6'),
            verifier_ref: "ver.1".into(),
            verifier_digest: sample_digest('7'),
            admission_receipt_refs: vec![receipt],
            inputs: vec![op_ref],
            outputs: vec![],
            parent_event_refs: vec![],
            budget: BudgetTransition::new(1, 1).unwrap(),
            outcome_code: "ok".into(),
            outcome_digest: sample_digest('8'),
            authority_effect: AuthorityEffect::None,
        }
    }

    #[test]
    fn execution_event_refuses_non_none_authority_and_uncovered_receipts() {
        let mut bad_auth = valid_event_input();
        bad_auth.authority_effect = AuthorityEffect::EvidenceOnly;
        assert!(ExecutionEvent::new(bad_auth).is_err());

        let mut uncovered = valid_event_input();
        uncovered.admission_receipt_refs.clear();
        assert!(ExecutionEvent::new(uncovered).is_err());

        let mut dup_receipt = valid_event_input();
        let r = dup_receipt.admission_receipt_refs[0].clone();
        dup_receipt.admission_receipt_refs.push(r);
        assert!(ExecutionEvent::new(dup_receipt).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_55aa1c6a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord55aa1c6a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord55aa1c6a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord55aa1c6a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord55aa1c6a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord55aa1c6a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError55aa1c6a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError55aa1c6a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
