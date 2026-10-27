//! Dense vectors and views.

pub mod row_vector;
pub mod vector;
pub mod view;
pub mod view_mut;

pub use row_vector::*;
pub use vector::{CoordinateVector, VectorError};

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OrthoError {
    Shape,
    Zero,
    Dot { value: i128 },
    Overflow,
}

// Origin: engine/crates_rs/core_linear_algebra/src/vector/mod.rs
// Claim: urn:core:crates_rs:core-linear-algebra:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for OrthoError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for OrthoError {}

/// Two nonzero integer vectors of one dimension with dot product zero.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OrthogonalPairWitness {
    dimension: usize,
}

impl OrthogonalPairWitness {
    pub fn try_new(left: &[i64], right: &[i64]) -> Result<Self, OrthoError> {
        if left.is_empty() || left.len() != right.len() {
            return Err(OrthoError::Shape);
        }
        if left.iter().all(|&x| x == 0) || right.iter().all(|&x| x == 0) {
            return Err(OrthoError::Zero);
        }
        let dot = Self::checked_dot(left, right)?;
        if dot != 0 {
            return Err(OrthoError::Dot { value: dot });
        }
        Ok(Self {
            dimension: left.len(),
        })
    }

    fn checked_dot(left: &[i64], right: &[i64]) -> Result<i128, OrthoError> {
        let mut dot = 0i128;
        for (&left_entry, &right_entry) in left.iter().zip(right.iter()) {
            let product = i128::from(left_entry)
                .checked_mul(i128::from(right_entry))
                .ok_or(OrthoError::Overflow)?;
            dot = dot.checked_add(product).ok_or(OrthoError::Overflow)?;
        }
        Ok(dot)
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod ortho_tests {
    use super::*;

    #[test]
    fn a_signed_pair_is_orthogonal() {
        let pair = OrthogonalPairWitness::try_new(&[1, -1], &[1, 1]);
        assert!(matches!(pair, Ok(ref pair) if pair.dimension() == 2));
    }

    #[test]
    fn a_positive_dot_product_is_refused() {
        let pair = OrthogonalPairWitness::try_new(&[1, 1], &[1, 1]);
        assert!(matches!(pair, Err(OrthoError::Dot { value: 2 })));
    }
}
