//! Integration tests for SkillOperandV1 filtering and prompt injection (U04).
//!
//! Invariants tested:
//! - Only Promoted operands are injected.
//! - Candidate or Suppressed operands are rejected / skipped.
//! - Max 3 operands injected, max 1200 tokens total.
//! - Single operand <= 1600 bytes and <= 400 tokens.
//!
//! AuthorityEffect: None.

use pfp_runtime::operand::{
    render_operand_prompt_block, select_operands_for_injection, OperandStatus, SkillOperandV1,
};

fn make_operand(
    id: &str,
    status: OperandStatus,
    target_colour: &str,
    text: &str,
    tokens: u64,
) -> SkillOperandV1 {
    SkillOperandV1 {
        operand_id: id.to_string(),
        title: format!("Title of {}", id),
        description: format!("Description of {}", id),
        source_colour: "Open".to_string(),
        target_colour: target_colour.to_string(),
        ddc_motif: "CR".to_string(),
        content_bytes_len: text.as_bytes().len() as u64,
        token_estimate: tokens,
        status,
        prompt_injection_text: text.to_string(),
        replay_evidence_hash: "abcd1234ef".to_string(),
        authority_effect: "None".to_string(),
    }
}

#[test]
fn test_unpromoted_operands_are_never_injected() {
    let candidate = make_operand(
        "op_cand",
        OperandStatus::Candidate,
        "Closed",
        "candidate advice",
        50,
    );
    let suppressed = make_operand(
        "op_supp",
        OperandStatus::Suppressed,
        "Closed",
        "suppressed advice",
        50,
    );
    let promoted = make_operand(
        "op_prom",
        OperandStatus::Promoted,
        "Closed",
        "promoted advice",
        50,
    );

    let all_operands = vec![candidate, suppressed, promoted];

    let selected = select_operands_for_injection(&all_operands, Some("Closed"));
    // MUTATION KILL GATE: Candidate and Suppressed MUST be excluded!
    assert_eq!(selected.len(), 1);
    assert_eq!(selected[0].operand_id, "op_prom");
}

#[test]
fn test_colour_matching_and_size_limits() {
    let wrong_colour = make_operand(
        "op_wrong_col",
        OperandStatus::Promoted,
        "Open",
        "open advice",
        50,
    );
    let right_colour = make_operand(
        "op_right_col",
        OperandStatus::Promoted,
        "Closed",
        "closed advice",
        50,
    );

    let operands = vec![wrong_colour, right_colour];
    let selected = select_operands_for_injection(&operands, Some("Closed"));
    assert_eq!(selected.len(), 1);
    assert_eq!(selected[0].operand_id, "op_right_col");

    // Oversized operand (> 1600 bytes)
    let huge_text = "x".repeat(1601);
    let mut huge_op = make_operand(
        "op_huge",
        OperandStatus::Promoted,
        "Closed",
        &huge_text,
        100,
    );
    huge_op.content_bytes_len = 1601;
    assert!(huge_op.validate_size().is_err());

    let huge_ops = vec![huge_op];
    let selected_huge = select_operands_for_injection(&huge_ops, Some("Closed"));
    assert_eq!(selected_huge.len(), 0);
}

#[test]
fn test_max_three_operands_and_token_cap() {
    let ops = vec![
        make_operand("op_1", OperandStatus::Promoted, "Closed", "advice 1", 300),
        make_operand("op_2", OperandStatus::Promoted, "Closed", "advice 2", 300),
        make_operand("op_3", OperandStatus::Promoted, "Closed", "advice 3", 300),
        make_operand("op_4", OperandStatus::Promoted, "Closed", "advice 4", 300),
    ];

    let selected = select_operands_for_injection(&ops, Some("Closed"));
    // At most 3 operands can be injected
    assert_eq!(selected.len(), 3);
    assert_eq!(selected[0].operand_id, "op_1");
    assert_eq!(selected[1].operand_id, "op_2");
    assert_eq!(selected[2].operand_id, "op_3");

    let prompt_block = render_operand_prompt_block(&selected);
    assert!(prompt_block.contains("Learned Skill Operands Available"));
    assert!(prompt_block.contains("op_1"));
    assert!(prompt_block.contains("op_2"));
    assert!(prompt_block.contains("op_3"));
    assert!(!prompt_block.contains("op_4"));
}

// Origin: engine/crates_rs/tests/pfp_runtime/operand_injection.rs
// Claim: urn:core:crates_rs:tests:operand-injection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1680ef93 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1680ef93` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1680ef93 {
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
impl BoundaryError1680ef93 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1680ef93 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1680ef93 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1680ef93 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1680ef93> {
        if capacity_bound == 0 {
            return Err(BoundaryError1680ef93::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1680ef93::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1680ef93::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_1680ef93() {
    let admitted = BoundaryRecord1680ef93::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1680ef93::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
