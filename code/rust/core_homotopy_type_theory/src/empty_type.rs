//! Empty type former `0` / `⊥`.
//!
//! Structural record only: a named empty type id.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Empty type `0` (no constructors).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EmptyType {
    pub id: String,
}

impl EmptyType {
    /// Validate that id is non-empty.
    pub fn validate(&self) -> Result<(), EmptyTypeError> {
        if self.id.is_empty() {
            return Err(EmptyTypeError::EmptyId);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum EmptyTypeError {
    #[error("empty type id must be non-empty")]
    EmptyId,
    #[error(
        "empty cardinal law failed: claimed sum {claimed_sum}, claimed product {claimed_product}, cardinality {cardinality_a}"
    )]
    CardinalLaw {
        claimed_sum: u64,
        claimed_product: u64,
        cardinality_a: u64,
    },
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let empty = EmptyType {
            id: "Empty".to_string(),
        };
        assert!(empty.validate().is_ok());
    }

    #[test]
    fn validate_rejects_empty_id() {
        let empty = EmptyType { id: String::new() };
        assert_eq!(empty.validate(), Err(EmptyTypeError::EmptyId));
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_homotopy_type_theory/src/empty_type.rs
// Claim: urn:core:hott:empty:cardinal-laws:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EmptyCardinal {
    cardinality_a: u64,
    sum_with_a: u64,
    product_with_a: u64,
}

impl EmptyType {
    pub fn try_cardinal(
        &self,
        cardinality_a: u64,
        claimed_sum: u64,
        claimed_product: u64,
    ) -> Result<EmptyCardinal, EmptyTypeError> {
        self.validate()?;
        if claimed_sum != cardinality_a || claimed_product != 0 {
            return Err(EmptyTypeError::CardinalLaw {
                claimed_sum,
                claimed_product,
                cardinality_a,
            });
        }
        Ok(EmptyCardinal {
            cardinality_a,
            sum_with_a: claimed_sum,
            product_with_a: claimed_product,
        })
    }
}

impl EmptyCardinal {
    pub fn sum_with_a(&self) -> u64 {
        self.sum_with_a
    }

    pub fn product_with_a(&self) -> u64 {
        self.product_with_a
    }
}

#[cfg(test)]
mod empty_cardinal_tests {
    use super::*;

    #[test]
    fn empty_sum_is_the_other_cardinal_and_the_product_is_zero() {
        let empty = EmptyType { id: "0".to_string() };
        let witness = empty.try_cardinal(7, 7, 0);
        assert!(matches!(
            witness,
            Ok(ref law) if law.sum_with_a() == 7 && law.product_with_a() == 0
        ));
    }

    #[test]
    fn refuses_a_nonzero_product() {
        let empty = EmptyType { id: "0".to_string() };
        let wrong = empty.try_cardinal(7, 7, 1);
        assert!(matches!(
            wrong,
            Err(EmptyTypeError::CardinalLaw { claimed_sum: 7, claimed_product: 1, cardinality_a: 7 })
        ));
    }
}
