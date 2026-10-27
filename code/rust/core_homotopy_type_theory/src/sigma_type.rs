//! Dependent pair type former `Σ(x:A). B(x)`.
//!
//! Structural record only: base and family are opaque string refs.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Dependent sum (pair) type `Σ(x : base). family(x)`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SigmaType {
    pub base_type_ref: String,
    pub family_ref: String,
}

impl SigmaType {
    /// Validate that base and family references are non-empty.
    pub fn validate(&self) -> Result<(), SigmaTypeError> {
        if self.base_type_ref.is_empty() {
            return Err(SigmaTypeError::EmptyBaseTypeRef);
        }
        if self.family_ref.is_empty() {
            return Err(SigmaTypeError::EmptyFamilyRef);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum SigmaTypeError {
    #[error("sigma type base_type_ref must be non-empty")]
    EmptyBaseTypeRef,
    #[error("sigma type family_ref must be non-empty")]
    EmptyFamilyRef,
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/sigma_type.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:sigma-type:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let sigma = SigmaType {
            base_type_ref: "A".to_string(),
            family_ref: "B".to_string(),
        };
        assert!(sigma.validate().is_ok());
    }

    #[test]
    fn validate_rejects_empty_base() {
        let sigma = SigmaType {
            base_type_ref: String::new(),
            family_ref: "B".to_string(),
        };
        assert_eq!(sigma.validate(), Err(SigmaTypeError::EmptyBaseTypeRef));
    }

    #[test]
    fn validate_rejects_empty_family() {
        let sigma = SigmaType {
            base_type_ref: "A".to_string(),
            family_ref: String::new(),
        };
        assert_eq!(sigma.validate(), Err(SigmaTypeError::EmptyFamilyRef));
    }
}

/// Cardinality of a finite dependent sum is the sum of the fiber sizes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteSigma {
    base: usize,
    cardinality: u128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SigmaCardError {
    Bound,
    Overflow,
}

impl std::fmt::Display for SigmaCardError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SigmaCardError::Bound => write!(formatter, "the base must have at most 32 points"),
            SigmaCardError::Overflow => write!(formatter, "the fiber sum overflowed"),
        }
    }
}

impl std::error::Error for SigmaCardError {}

impl FiniteSigma {
    pub fn cardinality(fibers: &[u32]) -> Result<Self, SigmaCardError> {
        if fibers.len() > 32 {
            return Err(SigmaCardError::Bound);
        }
        let mut cardinality: u128 = 0;
        for &fiber in fibers {
            cardinality = cardinality.checked_add(u128::from(fiber)).ok_or(SigmaCardError::Overflow)?;
        }
        Ok(Self {
            base: fibers.len(),
            cardinality,
        })
    }

    pub fn cardinality_value(&self) -> u128 {
        self.cardinality
    }
}

#[cfg(test)]
mod sigma_card_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn fibers_one_two_and_zero_sum_to_three() {
        let sigma = taken(FiniteSigma::cardinality(&[1, 2, 0]));
        assert_eq!(sigma.cardinality_value(), 3);
        assert!(FiniteSigma::cardinality(&[1u32; 33]).is_err());
    }
}
