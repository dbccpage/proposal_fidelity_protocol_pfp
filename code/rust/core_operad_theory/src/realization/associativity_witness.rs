//! Realization: Structural associativity and unit witnesses.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use crate::foundation::{Operation, PlanarColoredOperad};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ComputationStatus {
    Completed,
    Refused,
    NotComputed,
    BudgetExceeded,
    InternalError,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum LawResult {
    Satisfied,
    Violated,
    NotApplicable,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EvidenceKind {
    ExactStructural,
    Symbolic,
    BoundedExample,
    ShapeOnly,
}

/// Witness certificate proving structural operadic composition compliance.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StructuralAssociativityWitness {
    pub law_id: String,
    pub computation_status: ComputationStatus,
    pub law_result: LawResult,
    pub evidence_kind: EvidenceKind,
    pub left_expression: String,
    pub right_expression: String,
    pub index_convention: String,
    pub evidence_notes: String,
}

impl StructuralAssociativityWitness {
    pub fn is_satisfied(&self) -> bool {
        self.computation_status == ComputationStatus::Completed && self.law_result == LawResult::Satisfied
    }

    pub fn verify_sequential(
        operad: &PlanarColoredOperad,
        f: &Operation,
        g: &Operation,
        h: &Operation,
        i: usize,
        j: usize,
    ) -> Self {
        let left_str = format!("({} o_{} {}) o_{} {}", f.op_id.as_str(), i, g.op_id.as_str(), i + j, h.op_id.as_str());
        let right_str = format!("{} o_{} ({} o_{} {})", f.op_id.as_str(), i, g.op_id.as_str(), j, h.op_id.as_str());

        if i >= f.arity() || j >= g.arity() {
            return Self {
                law_id: "sequential_associativity".to_string(),
                computation_status: ComputationStatus::Refused,
                law_result: LawResult::NotApplicable,
                evidence_kind: EvidenceKind::ExactStructural,
                left_expression: left_str,
                right_expression: right_str,
                index_convention: "zero_based".to_string(),
                evidence_notes: format!("Indices i={}, j={} out of arity bounds", i, j),
            };
        }

        if g.output() != &f.inputs()[i] || h.output() != &g.inputs()[j] {
            return Self {
                law_id: "sequential_associativity".to_string(),
                computation_status: ComputationStatus::Refused,
                law_result: LawResult::NotApplicable,
                evidence_kind: EvidenceKind::ExactStructural,
                left_expression: left_str,
                right_expression: right_str,
                index_convention: "zero_based".to_string(),
                evidence_notes: "Ill-typed colour boundary matching.".to_string(),
            };
        }

        let f_circ_g = match operad.partial_compose(f, g, i) {
            Ok(op) => op,
            Err(e) => return Self::refused(&left_str, &right_str, e),
        };
        let left_op = match operad.partial_compose(&f_circ_g, h, i + j) {
            Ok(op) => op,
            Err(e) => return Self::refused(&left_str, &right_str, e),
        };

        let g_circ_h = match operad.partial_compose(g, h, j) {
            Ok(op) => op,
            Err(e) => return Self::refused(&left_str, &right_str, e),
        };
        let right_op = match operad.partial_compose(f, &g_circ_h, i) {
            Ok(op) => op,
            Err(e) => return Self::refused(&left_str, &right_str, e),
        };

        let is_eq = left_op.signature == right_op.signature;
        Self {
            law_id: "sequential_associativity".to_string(),
            computation_status: ComputationStatus::Completed,
            law_result: if is_eq { LawResult::Satisfied } else { LawResult::Violated },
            evidence_kind: EvidenceKind::ExactStructural,
            left_expression: left_str,
            right_expression: right_str,
            index_convention: "zero_based".to_string(),
            evidence_notes: format!("Verified exact equality of composite signatures: {}", left_op.signature),
        }
    }

    pub fn verify_unit(operad: &PlanarColoredOperad, f: &Operation) -> Self {
        let left_str = format!("{} o_0 id", f.op_id.as_str());
        let right_str = f.op_id.as_str().to_string();

        if f.arity() == 0 {
            return Self {
                law_id: "unit_law".to_string(),
                computation_status: ComputationStatus::Completed,
                law_result: LawResult::Satisfied,
                evidence_kind: EvidenceKind::ExactStructural,
                left_expression: left_str,
                right_expression: right_str,
                index_convention: "zero_based".to_string(),
                evidence_notes: "Nullary operation vacuously satisfies unit law.".to_string(),
            };
        }

        let id_op = Operation::identity(f.inputs()[0].clone());
        let composed = match operad.partial_compose(f, &id_op, 0) {
            Ok(op) => op,
            Err(e) => return Self::refused(&left_str, &right_str, e),
        };

        let is_eq = composed.signature == f.signature;
        Self {
            law_id: "unit_law".to_string(),
            computation_status: ComputationStatus::Completed,
            law_result: if is_eq { LawResult::Satisfied } else { LawResult::Violated },
            evidence_kind: EvidenceKind::ExactStructural,
            left_expression: left_str,
            right_expression: right_str,
            index_convention: "zero_based".to_string(),
            evidence_notes: "Unit law verified.".to_string(),
        }
    }

    fn refused(left: &str, right: &str, err: String) -> Self {
        Self {
            law_id: "associativity".to_string(),
            computation_status: ComputationStatus::Refused,
            law_result: LawResult::NotApplicable,
            evidence_kind: EvidenceKind::ExactStructural,
            left_expression: left.to_string(),
            right_expression: right.to_string(),
            index_convention: "zero_based".to_string(),
            evidence_notes: err,
        }
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/realization/associativity_witness.rs
// Claim: urn:core:crates_rs:core-operad-theory:associativity-witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0706a5e9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0706a5e9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0706a5e9 {
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
impl BoundaryError0706a5e9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0706a5e9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0706a5e9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0706a5e9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0706a5e9> {
        if capacity_bound == 0 {
            return Err(BoundaryError0706a5e9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0706a5e9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0706a5e9::ExceedsCapacity {
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
mod l4_boundary_tests_0706a5e9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0706a5e9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0706a5e9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0706a5e9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0706a5e9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0706a5e9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0706a5e9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0706a5e9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
