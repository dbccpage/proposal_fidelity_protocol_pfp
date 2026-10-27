//! Exact finite decoherence functional.
//!
//! Grounded in core_functional and chain_histories.

pub use core_functional::decoherence::{DecoherenceError, DecoherenceFunctional};
pub use crate::chain_histories::{chain_histories, ChainHistory};

/// Shape of a decoherence matrix on a family of equal chain histories.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct HistoryFamilyShape {
    history_count: usize,
    label_length: usize,
    dimension: usize,
    matrix_entries: usize,
}

/// Refusal of a chain-history family before a decoherence matrix is formed.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HistoryFamilyError {
    Empty,
    NotSquare { index: usize, rows: usize, cols: usize },
    DimensionMismatch { index: usize, dimension: usize, expected: usize },
    EmptyLabels { index: usize },
    LabelLengthMismatch { index: usize, length: usize, expected: usize },
    EntryOverflow,
    Budget(DecoherenceError),
}

// Origin: engine/crates_rs/core_quantum_physics/src/decoherence_functional.rs
// Claim: urn:core:crates_rs:core-quantum-physics:decoherence-functional:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HistoryFamilyError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HistoryFamilyError {}

impl HistoryFamilyShape {
    /// Admit a nonempty family of square class operators with one common label length.
    pub fn certify(histories: &[ChainHistory]) -> Result<Self, HistoryFamilyError> {
        let Some(first) = histories.first() else {
            return Err(HistoryFamilyError::Empty);
        };
        let dimension = first.class_operator.rows();
        let cols = first.class_operator.cols();
        if dimension != cols {
            return Err(HistoryFamilyError::NotSquare {
                index: 0,
                rows: dimension,
                cols,
            });
        }
        let label_length = first.labels.len();
        if label_length == 0 {
            return Err(HistoryFamilyError::EmptyLabels { index: 0 });
        }
        for (index, history) in histories.iter().enumerate().skip(1) {
            let rows = history.class_operator.rows();
            let history_cols = history.class_operator.cols();
            if rows != history_cols {
                return Err(HistoryFamilyError::NotSquare {
                    index,
                    rows,
                    cols: history_cols,
                });
            }
            if rows != dimension {
                return Err(HistoryFamilyError::DimensionMismatch {
                    index,
                    dimension: rows,
                    expected: dimension,
                });
            }
            if history.labels.is_empty() {
                return Err(HistoryFamilyError::EmptyLabels { index });
            }
            if history.labels.len() != label_length {
                return Err(HistoryFamilyError::LabelLengthMismatch {
                    index,
                    length: history.labels.len(),
                    expected: label_length,
                });
            }
        }
        let history_count = histories.len();
        let matrix_entries = history_count
            .checked_mul(history_count)
            .ok_or(HistoryFamilyError::EntryOverflow)?;
        crate::chain_histories::preflight_history_budget(history_count, label_length, dimension)
            .map_err(HistoryFamilyError::Budget)?;
        Ok(Self {
            history_count,
            label_length,
            dimension,
            matrix_entries,
        })
    }

    /// Number of histories, which is the side of the decoherence matrix.
    pub fn history_count(self) -> usize {
        self.history_count
    }

    /// Shared positive label length.
    pub fn label_length(self) -> usize {
        self.label_length
    }

    /// Common square dimension of the class operators.
    pub fn dimension(self) -> usize {
        self.dimension
    }

    /// Entry count `n * n` of the decoherence matrix.
    pub fn matrix_entries(self) -> usize {
        self.matrix_entries
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod history_family_shape_checks {
    use super::{ChainHistory, DecoherenceError, HistoryFamilyError, HistoryFamilyShape};
    use linear_algebra::backend::basic_matrix::BasicMatrix;
    use core_number_theory::cyclotomic::GaussianRat;

    #[test]
    fn one_square_history_has_one_decoherence_entry() {
        let shape = BasicMatrix::try_from_fn(1, 1, |_row, _col| GaussianRat::one()).map(|class_operator| {
            HistoryFamilyShape::certify(&[ChainHistory {
                labels: vec![0],
                class_operator,
            }])
        });
        assert!(matches!(
            shape,
            Ok(Ok(family)) if family.matrix_entries() == 1 && family.dimension() == 1 && family.label_length() == 1
        ));
    }

    #[test]
    fn an_empty_family_is_refused() {
        assert!(matches!(
            HistoryFamilyShape::certify(&[]),
            Err(HistoryFamilyError::Empty)
        ));
    }

    #[test]
    fn histories_must_share_a_label_length() {
        let shape = BasicMatrix::try_from_fn(1, 1, |_row, _col| GaussianRat::one()).map(|class_operator| {
            let second = class_operator.clone();
            HistoryFamilyShape::certify(&[
                ChainHistory {
                    labels: vec![0],
                    class_operator,
                },
                ChainHistory {
                    labels: vec![0, 1],
                    class_operator: second,
                },
            ])
        });
        assert!(matches!(
            shape,
            Ok(Err(HistoryFamilyError::LabelLengthMismatch {
                index: 1,
                length: 2,
                expected: 1
            }))
        ));
    }

    #[test]
    fn a_zero_dimension_fails_the_history_budget() {
        let shape = BasicMatrix::try_from_fn(0, 0, |_row, _col| GaussianRat::zero()).map(|class_operator| {
            HistoryFamilyShape::certify(&[ChainHistory {
                labels: vec![0],
                class_operator,
            }])
        });
        assert!(matches!(
            shape,
            Ok(Err(HistoryFamilyError::Budget(DecoherenceError::Empty)))
        ));
    }
}
