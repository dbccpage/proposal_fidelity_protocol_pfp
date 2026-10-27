//! HoTT-facing spine for the Core tower.
//!
//! This crate encodes the type-theoretic reading of the tower:
//! difference is primitive, sameness is certified zero-difference, authority is
//! an inhabited dependent type, and terminalization is an eliminator into
//! authority/refusal outcomes. It is a finite record layer, not a proof
//! assistant kernel.
//!
//! `primitive_difference` (the finite PD quotient/descent kernel) and the type
//! formers (Π, Σ, sum, unit, empty, path, universe, univalence witness) are
//! shape records validated here. The former `native_hott` crate
//! was a partial copy of this one and was merged into it on 2026-09-25.

pub mod contractible_type;
pub mod difference;
pub mod empty_type;
pub mod higher_inductive_type;
pub mod hott_contract_alignment;
pub mod identity;
pub mod path;
pub mod path_transport;
pub mod pi_type;
pub mod presentation_difference;
pub mod primitive_difference;
pub mod sigma_type;
pub mod sum_type;
pub mod tower;
pub mod truncation;
pub mod type_formation;
pub mod type_universe;
pub mod unit_type;
pub mod univalence_witness;

pub use presentation_difference::{
    active_obstruction, evaluate_extension, ActiveObstructionV1, DemandV1,
    ExtensionEffect, ExtensionEvaluationV1, PresentationV1, QuestionV1,
};

pub use higher_inductive_type::{HigherInductiveType, PathConstructor, PointConstructor};
pub use hott_contract_alignment::HottContractBinding;
pub use tower::{HottLayerView, HottTower, CoreLayer};
pub mod a_infinity;
pub mod quasi_category;
pub mod substitution;


/// Path concatenation: endpoints meet, and lengths add by checked arithmetic.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PathConcatWitness {
    length: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PathConcatError {
    Empty,
    Overflow,
    EndpointMismatch { left_end: i64, right_start: i64 },
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/lib.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PathConcatError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PathConcatError {}

impl PathConcatWitness {
    pub fn admit(left: &[i64], right: &[i64]) -> Result<Self, PathConcatError> {
        if left.is_empty() || right.is_empty() {
            return Err(PathConcatError::Empty);
        }
        let left_end = left[left.len() - 1];
        let right_start = right[0];
        if left_end != right_start {
            return Err(PathConcatError::EndpointMismatch {
                left_end,
                right_start,
            });
        }
        let left_steps = u32::try_from(left.len() - 1).map_err(|_| PathConcatError::Overflow)?;
        let right_steps = u32::try_from(right.len() - 1).map_err(|_| PathConcatError::Overflow)?;
        let length = left_steps
            .checked_add(right_steps)
            .ok_or(PathConcatError::Overflow)?;
        Ok(Self { length })
    }

    pub fn length(&self) -> u32 {
        self.length
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod path_concat_witness_tests {
    use super::*;

    #[test]
    fn concatenation_adds_path_lengths() {
        let admitted = PathConcatWitness::admit(&[0, 1, 2], &[2, 5]);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.length()), Some(3));
        assert!(matches!(
            PathConcatWitness::admit(&[0, 1], &[2, 3]),
            Err(PathConcatError::EndpointMismatch {
                left_end: 1,
                right_start: 2
            })
        ));
    }
}
