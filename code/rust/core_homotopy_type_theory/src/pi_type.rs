//! Dependent function type former `Π(x:A). B(x)`.
//!
//! Structural record only: base and family are opaque string refs.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Dependent product (function) type `Π(x : base). family(x)`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PiType {
    pub base_type_ref: String,
    pub family_ref: String,
}

impl PiType {
    /// Validate that base and family references are non-empty.
    pub fn validate(&self) -> Result<(), PiTypeError> {
        if self.base_type_ref.is_empty() {
            return Err(PiTypeError::EmptyBaseTypeRef);
        }
        if self.family_ref.is_empty() {
            return Err(PiTypeError::EmptyFamilyRef);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum PiTypeError {
    #[error("pi type base_type_ref must be non-empty")]
    EmptyBaseTypeRef,
    #[error("pi type family_ref must be non-empty")]
    EmptyFamilyRef,
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/pi_type.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:pi-type:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let pi = PiType {
            base_type_ref: "A".to_string(),
            family_ref: "B".to_string(),
        };
        assert!(pi.validate().is_ok());
    }

    #[test]
    fn validate_rejects_empty_base() {
        let pi = PiType {
            base_type_ref: String::new(),
            family_ref: "B".to_string(),
        };
        assert_eq!(pi.validate(), Err(PiTypeError::EmptyBaseTypeRef));
    }

    #[test]
    fn validate_rejects_empty_family() {
        let pi = PiType {
            base_type_ref: "A".to_string(),
            family_ref: String::new(),
        };
        assert_eq!(pi.validate(), Err(PiTypeError::EmptyFamilyRef));
    }
}

/// Cardinality of a finite dependent product. The empty product is 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PiCardinalityWitness {
    fiber_count: usize,
    cardinality: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PiCardinalityError {
    InvalidPi,
    Overflow,
}

impl PiCardinalityWitness {
    pub fn try_from_fibers(
        pi: &PiType,
        fibers: &[u64],
    ) -> Result<Self, PiCardinalityError> {
        pi.validate().map_err(|_| PiCardinalityError::InvalidPi)?;
        if fibers.is_empty() {
            return Ok(Self {
                fiber_count: 0,
                cardinality: 1,
            });
        }
        let mut cardinality = 1u64;
        for fiber in fibers {
            cardinality = cardinality
                .checked_mul(*fiber)
                .ok_or(PiCardinalityError::Overflow)?;
        }
        Ok(Self {
            fiber_count: fibers.len(),
            cardinality,
        })
    }

    pub fn cardinality(&self) -> u64 {
        self.cardinality
    }
}
