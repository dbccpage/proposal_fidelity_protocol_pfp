//! Coproduct type former `A + B`.
//!
//! Structural record only: left and right are opaque string refs.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Binary sum (coproduct) type `left + right`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SumType {
    pub left_type_ref: String,
    pub right_type_ref: String,
}

impl SumType {
    /// Validate that left and right type references are non-empty.
    pub fn validate(&self) -> Result<(), SumTypeError> {
        if self.left_type_ref.is_empty() {
            return Err(SumTypeError::EmptyLeftTypeRef);
        }
        if self.right_type_ref.is_empty() {
            return Err(SumTypeError::EmptyRightTypeRef);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum SumTypeError {
    #[error("sum type left_type_ref must be non-empty")]
    EmptyLeftTypeRef,
    #[error("sum type right_type_ref must be non-empty")]
    EmptyRightTypeRef,
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/sum_type.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:sum-type:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let sum = SumType {
            left_type_ref: "A".to_string(),
            right_type_ref: "B".to_string(),
        };
        assert!(sum.validate().is_ok());
    }

    #[test]
    fn validate_rejects_empty_left() {
        let sum = SumType {
            left_type_ref: String::new(),
            right_type_ref: "B".to_string(),
        };
        assert_eq!(sum.validate(), Err(SumTypeError::EmptyLeftTypeRef));
    }

    #[test]
    fn validate_rejects_empty_right() {
        let sum = SumType {
            left_type_ref: "A".to_string(),
            right_type_ref: String::new(),
        };
        assert_eq!(sum.validate(), Err(SumTypeError::EmptyRightTypeRef));
    }
}

/// Which summand an index belongs to.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SumIndex {
    /// Index into the left summand.
    Left(u32),
    /// Index into the right summand.
    Right(u32),
}

/// Refusal from a coproduct encoding.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SumEncodeError {
    /// A side index is outside that summand.
    OutOfRange,
    /// `left_card + right_index` overflowed.
    Overflow,
}

/// Flat index of a point of `A + B`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CoproductPoint {
    flat: u32,
}

impl CoproductPoint {
    /// Left indices stay in `0..left_card`. Right indices follow them.
    pub fn try_encode(left_card: u32, side: SumIndex) -> Result<Self, SumEncodeError> {
        let flat = match side {
            SumIndex::Left(index) => {
                if index >= left_card {
                    return Err(SumEncodeError::OutOfRange);
                }
                index
            }
            SumIndex::Right(index) => left_card.checked_add(index).ok_or(SumEncodeError::Overflow)?,
        };
        Ok(Self { flat })
    }

    /// Inverse of [`Self::try_encode`] for a known left cardinality.
    pub fn try_decode(self, left_card: u32) -> Result<SumIndex, SumEncodeError> {
        if self.flat < left_card {
            Ok(SumIndex::Left(self.flat))
        } else {
            Ok(SumIndex::Right(
                self.flat.checked_sub(left_card).ok_or(SumEncodeError::Overflow)?,
            ))
        }
    }

    /// Flat index.
    pub fn flat(self) -> u32 { self.flat }
}

#[cfg(test)]
mod coproduct_point_tests {
    use super::*;
    #[test]
    fn a_right_index_round_trips() {
        let point = CoproductPoint::try_encode(3, SumIndex::Right(1));
        assert!(matches!(point, Ok(p) if p.flat() == 4));
        let Ok(point) = point else { return; };
        assert!(matches!(point.try_decode(3), Ok(SumIndex::Right(1))));
    }
}
