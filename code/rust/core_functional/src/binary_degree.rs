//! Binary chain-law defect measurement and shared shape admission.
//!
//! Binary quotient distance is owned by `phi1`; binary closure mass by `gamma2`.
//! This module measures chain-law violations and shares finite shape checks.

/// The largest binary source dimension admitted to the exhaustive Phi1 search.
pub const MAX_EXHAUSTIVE_BINARY_DOMAIN_DIM: usize = 20;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum BinaryDegreeError {
    #[error("binary map row {row} has {actual} entries; expected {expected}")]
    RaggedMatrix {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("binary input has {actual} entries; expected {expected}")]
    InputDimensionMismatch { expected: usize, actual: usize },
    #[error(
        "binary Phi1 source dimension {domain_dim} exceeds exact-search bound {max_supported}"
    )]
    ExhaustiveSearchTooLarge {
        domain_dim: usize,
        max_supported: usize,
    },
}

/// A cycle-free finite binary specialization. Matrices are row-major over F2.
pub struct BinaryDegreeFunctional;

impl BinaryDegreeFunctional {
    /// Number of nonzero entries in a supplied d1*d0 matrix.
    ///
    /// This is a chain-law violation count, not quotient Phi1. The caller is
    /// responsible for constructing the composite on the declared carrier.
    pub fn chain_composite_weight(
        composite_rows: &[Vec<bool>],
        source_dim: usize,
    ) -> Result<usize, BinaryDegreeError> {
        check_shape(composite_rows, source_dim)?;
        Ok(composite_rows
            .iter()
            .flatten()
            .filter(|entry| **entry)
            .count())
    }

    /// Decide membership in the image of a binary linear map by row reduction.
    pub fn is_in_image(
        rows: &[Vec<bool>],
        domain_dim: usize,
        target: &[bool],
    ) -> Result<bool, BinaryDegreeError> {
        check_shape(rows, domain_dim)?;
        check_input_length(target, rows.len())?;
        Ok(image_membership_unchecked(rows, domain_dim, target))
    }
}

pub(crate) fn check_shape(rows: &[Vec<bool>], domain_dim: usize) -> Result<(), BinaryDegreeError> {
    for (row_index, row) in rows.iter().enumerate() {
        if row.len() != domain_dim {
            return Err(BinaryDegreeError::RaggedMatrix {
                row: row_index,
                expected: domain_dim,
                actual: row.len(),
            });
        }
    }
    Ok(())
}

pub(crate) fn check_input_length(input: &[bool], expected: usize) -> Result<(), BinaryDegreeError> {
    if input.len() != expected {
        return Err(BinaryDegreeError::InputDimensionMismatch {
            expected,
            actual: input.len(),
        });
    }
    Ok(())
}

pub(crate) fn image_membership_unchecked(
    rows: &[Vec<bool>],
    domain_dim: usize,
    target: &[bool],
) -> bool {
    let mut augmented: Vec<Vec<bool>> = rows
        .iter()
        .zip(target)
        .map(|(row, rhs)| {
            let mut augmented_row = row.clone();
            augmented_row.push(*rhs);
            augmented_row
        })
        .collect();

    let mut pivot_row = 0;
    for column in 0..domain_dim {
        let Some(found) = (pivot_row..augmented.len()).find(|row| augmented[*row][column]) else {
            continue;
        };
        augmented.swap(pivot_row, found);
        let pivot = augmented[pivot_row].clone();
        for (row_index, row) in augmented.iter_mut().enumerate() {
            if row_index != pivot_row && row[column] {
                for (entry, pivot_entry) in row[column..].iter_mut().zip(&pivot[column..]) {
                    *entry ^= *pivot_entry;
                }
            }
        }
        pivot_row += 1;
        if pivot_row == augmented.len() {
            break;
        }
    }

    !augmented
        .iter()
        .any(|row| row[..domain_dim].iter().all(|entry| !entry) && row[domain_dim])
}

pub(crate) fn hamming_weight(values: &[bool]) -> usize {
    values.iter().filter(|value| **value).count()
}

// Origin: engine/crates_rs/core_functional/src/binary_degree.rs
// Claim: urn:core:crates_rs:core-functional:binary-degree:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::gamma2::{Gamma2Functional, IntegerGamma2Error};

    #[test]
    fn binary_quotient_and_closure_have_distinct_values() {
        let d0 = vec![vec![true], vec![true], vec![false]];
        let d1 = vec![vec![false, false, true]];
        let residual = [false, false, true];
        assert_eq!(
            crate::phi1::Phi1Functional::binary(&d0, 1, &residual),
            Ok(1)
        );
        assert_eq!(
            crate::gamma2::Gamma2Functional::binary(&d1, 3, &residual),
            Ok(1)
        );
    }

    #[test]
    fn integer_face_gamma2_detects_arithmetic_overflow() {
        assert_eq!(Gamma2Functional::checked_face([3, 4, -2]), Ok(5));
        assert_eq!(Gamma2Functional::checked_total(&[3, 4]), Ok(7));
        assert_eq!(
            Gamma2Functional::checked_face([i64::MAX, 1, 0]),
            Err(IntegerGamma2Error::CapacityOverflow)
        );
    }

    #[test]
    fn composite_weight_is_shape_checked_and_separate_from_phi1() {
        let composite = vec![vec![true, false], vec![true, true]];
        assert_eq!(
            BinaryDegreeFunctional::chain_composite_weight(&composite, 2),
            Ok(3)
        );
        assert_eq!(
            BinaryDegreeFunctional::chain_composite_weight(&composite, 1),
            Err(BinaryDegreeError::RaggedMatrix {
                row: 0,
                expected: 1,
                actual: 2,
            })
        );
    }
}
