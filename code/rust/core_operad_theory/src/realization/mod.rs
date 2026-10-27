//! Realization Tier for Operad Theory.
//!
//! AuthorityEffect: None.

pub mod algebra_over_operad;
pub mod module_over_operad;
pub mod associativity_witness;

pub use algebra_over_operad::{EvaluationOutcome, EvaluationReceipt, OperadAlgebra, PolicyDecisionRef};
pub use module_over_operad::{AlgebraModule, OperadicModule};
pub use associativity_witness::{ComputationStatus, EvidenceKind, LawResult, StructuralAssociativityWitness};

use crate::foundation::{OperadColour, OperadSignature, Operation, OperationId, PlanarColoredOperad};

/// Outer slot of `(f ∘_i g) ∘_{i+j} h`, the index `StructuralAssociativityWitness` writes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SequentialSlotWitness {
    outer_slot: u64,
    insertion_i: u64,
    insertion_j: u64,
    composed_arity: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SequentialSlotError {
    Overflow,
    Colour,
    OperationId,
    Insert,
    Arity { arity: u64 },
    Unsatisfied,
    IndexText,
    RefusalDrift,
    OutOfArity { i: u64, j: u64, f_arity: u64, g_arity: u64 },
    OuterOutOfArity { outer: u64, composed: u64 },
}

// Origin: engine/crates_rs/core_operad_theory/src/realization/mod.rs
// Claim: urn:core:crates_rs:core-operad-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SequentialSlotError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SequentialSlotError {}

impl SequentialSlotWitness {
    /// Refuse a slot outside arity. The outer slot of a lawful insertion is `i + j`, and it must
    /// lie in the arity of `f ∘_i g`, which is `arity(f) + arity(g) - 1`.
    pub fn certify_indices(
        i: u64,
        j: u64,
        f_arity: u64,
        g_arity: u64,
    ) -> Result<Self, SequentialSlotError> {
        if i >= f_arity || j >= g_arity {
            return Err(SequentialSlotError::OutOfArity { i, j, f_arity, g_arity });
        }
        let outer_slot = i.checked_add(j).ok_or(SequentialSlotError::Overflow)?;
        let composed_arity = f_arity
            .checked_add(g_arity)
            .ok_or(SequentialSlotError::Overflow)?
            .checked_sub(1)
            .ok_or(SequentialSlotError::Overflow)?;
        if outer_slot >= composed_arity {
            return Err(SequentialSlotError::OuterOutOfArity {
                outer: outer_slot,
                composed: composed_arity,
            });
        }
        Ok(Self {
            outer_slot,
            insertion_i: i,
            insertion_j: j,
            composed_arity,
        })
    }

    fn check_sequential_witness(
        operad: &PlanarColoredOperad,
        operation: &Operation,
        slots: &Self,
        arity: u64,
    ) -> Result<(), SequentialSlotError> {
        let i = usize::try_from(slots.insertion_i).map_err(|_| SequentialSlotError::Overflow)?;
        let j = usize::try_from(slots.insertion_j).map_err(|_| SequentialSlotError::Overflow)?;
        let produced = StructuralAssociativityWitness::verify_sequential(
            operad, operation, operation, operation, i, j,
        );
        if produced.law_id != "sequential_associativity"
            || produced.index_convention != "zero_based"
            || !produced.is_satisfied()
        {
            return Err(SequentialSlotError::Unsatisfied);
        }
        let outer_mark = format!("o_{}", slots.outer_slot);
        let inner_mark = format!("o_{}", slots.insertion_j);
        if !produced.left_expression.contains(&outer_mark)
            || !produced.right_expression.contains(&inner_mark)
        {
            return Err(SequentialSlotError::IndexText);
        }
        Self::check_refused_witness(operad, operation, arity)
    }

    fn check_refused_witness(
        operad: &PlanarColoredOperad,
        operation: &Operation,
        arity: u64,
    ) -> Result<(), SequentialSlotError> {
        let refused = StructuralAssociativityWitness::verify_sequential(
            operad,
            operation,
            operation,
            operation,
            operation.arity(),
            0,
        );
        if refused.computation_status != ComputationStatus::Refused
            || refused.law_result != LawResult::NotApplicable
            || Self::certify_indices(arity, 0, arity, arity).is_ok()
        {
            return Err(SequentialSlotError::RefusalDrift);
        }
        Ok(())
    }

    /// Binary generator on one colour: slots `i = 1`, `j = 1`, outer slot `2`, and index `2` is refused.
    pub fn certify() -> Result<Self, SequentialSlotError> {
        let mut operad = PlanarColoredOperad::new("AssocOperad", false);
        let colour = operad.add_colour(OperadColour::new("C").map_err(|_| SequentialSlotError::Colour)?);
        let operation = Operation::new_generator(
            OperationId::new("f").map_err(|_| SequentialSlotError::OperationId)?,
            OperadSignature::new(vec![colour.clone(), colour.clone()], colour),
            "f",
        );
        operad.add_operation(operation.clone()).map_err(|_| SequentialSlotError::Insert)?;
        let arity = u64::try_from(operation.arity()).map_err(|_| SequentialSlotError::Overflow)?;
        if arity != 2 {
            return Err(SequentialSlotError::Arity { arity });
        }
        let slots = Self::certify_indices(1, 1, arity, arity)?;
        Self::check_sequential_witness(&operad, &operation, &slots, arity)?;
        Ok(slots)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod sequential_slot_tests {
    use super::*;

    #[test]
    fn outer_slot_is_i_plus_j() {
        assert!(matches!(
            SequentialSlotWitness::certify(),
            Ok(witness)
                if witness.insertion_i == 1
                    && witness.insertion_j == 1
                    && witness.insertion_i.checked_add(witness.insertion_j) == Some(witness.outer_slot)
                    && witness.outer_slot == 2
                    && witness.composed_arity == 3
        ));
        assert!(matches!(
            SequentialSlotWitness::certify_indices(2, 0, 2, 2),
            Err(SequentialSlotError::OutOfArity { i: 2, j: 0, f_arity: 2, g_arity: 2 })
        ));
    }
}
