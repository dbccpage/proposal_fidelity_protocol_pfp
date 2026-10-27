use crate::backend::basic_matrix::CheckedNumeric;
use thiserror::Error;

/// Errors for sparse COO operators.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum SparseOperatorError {
    #[error("entry index out of bounds: row={row}, col={col}, shape={rows}x{cols}")]
    EntryOutOfBounds {
        row: usize,
        col: usize,
        rows: usize,
        cols: usize,
    },

    #[error("input vector dimension mismatch: expected {expected}, actual {actual}")]
    VectorDimensionMismatch { expected: usize, actual: usize },

    #[error("scalar arithmetic overflow")]
    Overflow,
}

/// A sparse linear operator in coordinate-list format.
///
/// Convention:
/// - `rows` is the output dimension.
/// - `cols` is the input dimension.
/// - each entry `(r, c, value)` contributes `value * x[c]` to output `r`.
///
/// Duplicate `(row, col)` entries are allowed and are accumulated during
/// application, unless a `CompressWitness` is attached.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SparseOperator<T> {
    rows: usize,
    cols: usize,
    entries: Vec<(usize, usize, T)>,
    compress_witness: Option<CompressWitness>,
}

/// Local witness that the current COO entries are sorted and duplicate-free.
///
/// This witness is not cryptographic and is not independently value-bound.
/// Zero-valued entries may still be present.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompressWitness(());

impl<T> SparseOperator<T> {
    /// Constructs an empty sparse operator of shape `rows × cols`.
    pub fn new(rows: usize, cols: usize) -> Self {
        Self {
            rows,
            cols,
            entries: Vec::new(),
            compress_witness: Some(CompressWitness(())), // Empty is trivially compressed
        }
    }

    /// Constructs a sparse operator from entries, checking all indices.
    pub fn from_entries_checked(
        rows: usize,
        cols: usize,
        entries: Vec<(usize, usize, T)>,
    ) -> Result<Self, SparseOperatorError> {
        for (row, col, _) in &entries {
            if *row >= rows || *col >= cols {
                return Err(SparseOperatorError::EntryOutOfBounds {
                    row: *row,
                    col: *col,
                    rows,
                    cols,
                });
            }
        }

        Ok(Self {
            rows,
            cols,
            entries,
            compress_witness: None, // Unchecked arrays lose compression provenance
        })
    }

    /// Returns the operator shape.
    pub fn shape(&self) -> (usize, usize) {
        (self.rows, self.cols)
    }

    /// Returns the number of rows.
    pub fn rows(&self) -> usize {
        self.rows
    }

    /// Returns the number of columns.
    pub fn cols(&self) -> usize {
        self.cols
    }

    /// Returns COO entries.
    pub fn entries(&self) -> &[(usize, usize, T)] {
        &self.entries
    }

    /// Consumes the operator into raw COO parts, discarding compression witness metadata.
    pub fn into_entries(self) -> (usize, usize, Vec<(usize, usize, T)>) {
        (self.rows, self.cols, self.entries)
    }

    /// Adds one COO entry after checking bounds.
    pub fn add_entry(
        &mut self,
        row: usize,
        col: usize,
        value: T,
    ) -> Result<(), SparseOperatorError> {
        if row >= self.rows || col >= self.cols {
            return Err(SparseOperatorError::EntryOutOfBounds {
                row,
                col,
                rows: self.rows,
                cols: self.cols,
            });
        }

        self.entries.push((row, col, value));
        // Inserting invalidates compression provenance
        self.compress_witness = None;
        Ok(())
    }
}

impl<T> SparseOperator<T>
where
    T: CheckedNumeric,
{
    /// Applies the sparse operator to a vector.
    pub fn apply(&self, x: &[T]) -> Result<Vec<T>, SparseOperatorError> {
        if x.len() != self.cols {
            return Err(SparseOperatorError::VectorDimensionMismatch {
                expected: self.cols,
                actual: x.len(),
            });
        }

        let mut result = vec![T::zero(); self.rows];

        for (row, col, value) in &self.entries {
            // Safe bounds because entries are checked at construction/insertion.
            let product = value
                .checked_mul(&x[*col])
                .map_err(|_| SparseOperatorError::Overflow)?;
            result[*row] = result[*row]
                .checked_add(&product)
                .map_err(|_| SparseOperatorError::Overflow)?;
        }

        Ok(result)
    }

    /// Compresses the operator in-place, merging duplicate indices and sorting by (row, col).
    pub fn compress_checked(&mut self) -> Result<(), SparseOperatorError> {
        if self.compress_witness.is_some() {
            return Ok(());
        }

        self.entries.sort_by_key(|&(r, c, _)| (r, c));

        let mut compressed = Vec::with_capacity(self.entries.len());
        let mut current_opt: Option<(usize, usize, T)> = None;

        for (r, c, v) in self.entries.drain(..) {
            match current_opt.take() {
                Some((curr_r, curr_c, curr_v)) if curr_r == r && curr_c == c => {
                    let merged_v = curr_v
                        .checked_add(&v)
                        .map_err(|_| SparseOperatorError::Overflow)?;
                    current_opt = Some((curr_r, curr_c, merged_v));
                }
                Some(previous) => {
                    compressed.push(previous);
                    current_opt = Some((r, c, v));
                }
                None => {
                    current_opt = Some((r, c, v));
                }
            }
        }

        if let Some(last) = current_opt {
            compressed.push(last);
        }

        self.entries = compressed;
        self.compress_witness = Some(CompressWitness(()));
        Ok(())
    }

    pub fn compress_witness(&self) -> Option<&CompressWitness> {
        self.compress_witness.as_ref()
    }

    pub fn is_compressed(&self) -> bool {
        self.compress_witness.is_some()
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/sparse_operator.rs
// Claim: urn:core:crates_rs:core-linear-algebra:sparse-operator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::Zero;

    #[derive(Debug, Clone, PartialEq, Eq)]
    struct CheckedI64(i64);

    impl std::ops::Add for CheckedI64 {
        type Output = Self;
        fn add(self, rhs: Self) -> Self {
            CheckedI64(self.0.wrapping_add(rhs.0))
        }
    }
    impl std::ops::Sub for CheckedI64 {
        type Output = Self;
        fn sub(self, rhs: Self) -> Self {
            CheckedI64(self.0.wrapping_sub(rhs.0))
        }
    }
    impl std::ops::Mul for CheckedI64 {
        type Output = Self;
        fn mul(self, rhs: Self) -> Self {
            CheckedI64(self.0.wrapping_mul(rhs.0))
        }
    }

    #[derive(Debug, Error, Clone, PartialEq, Eq)]
    #[error("overflow")]
    struct OverflowError;

    impl Zero for CheckedI64 {
        fn zero() -> Self {
            CheckedI64(0)
        }
        fn is_zero(&self) -> bool {
            self.0 == 0
        }
    }

    impl CheckedNumeric for CheckedI64 {
        type Error = OverflowError;
        fn checked_add(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_add(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
        fn checked_sub(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_sub(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
        fn checked_mul(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_mul(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
    }

    #[test]
    fn applies_sparse_operator() -> Result<(), SparseOperatorError> {
        let mut op = SparseOperator::<CheckedI64>::new(2, 3);
        op.add_entry(0, 0, CheckedI64(2))?;
        op.add_entry(0, 2, CheckedI64(3))?;
        op.add_entry(1, 1, CheckedI64(5))?;

        let out = op.apply(&[CheckedI64(10), CheckedI64(20), CheckedI64(30)])?;

        assert_eq!(out, vec![CheckedI64(110), CheckedI64(100)]);
        Ok(())
    }

    #[test]
    fn rejects_bad_entry() {
        let mut op = SparseOperator::<CheckedI64>::new(2, 3);

        assert!(matches!(
            op.add_entry(2, 0, CheckedI64(1)),
            Err(SparseOperatorError::EntryOutOfBounds { .. })
        ));

        assert!(matches!(
            op.add_entry(0, 3, CheckedI64(1)),
            Err(SparseOperatorError::EntryOutOfBounds { .. })
        ));
    }

    #[test]
    fn rejects_vector_dimension_mismatch() {
        let op = SparseOperator::<CheckedI64>::new(2, 3);

        assert!(matches!(
            op.apply(&[CheckedI64(1), CheckedI64(2)]),
            Err(SparseOperatorError::VectorDimensionMismatch {
                expected: 3,
                actual: 2
            })
        ));
    }

    #[test]
    fn duplicate_entries_accumulate() -> Result<(), SparseOperatorError> {
        let mut op = SparseOperator::<CheckedI64>::new(1, 1);
        op.add_entry(0, 0, CheckedI64(2))?;
        op.add_entry(0, 0, CheckedI64(3))?;

        assert_eq!(op.apply(&[CheckedI64(10)])?, vec![CheckedI64(50)]);
        Ok(())
    }

    #[test]
    fn compress_merges_duplicates_and_grants_witness() -> Result<(), SparseOperatorError> {
        let mut op = SparseOperator::<CheckedI64>::new(2, 2);
        op.add_entry(1, 1, CheckedI64(5))?;
        op.add_entry(0, 0, CheckedI64(2))?;
        op.add_entry(0, 0, CheckedI64(3))?;

        assert!(!op.is_compressed());
        op.compress_checked()?;
        assert!(op.is_compressed());

        // Now sorted and merged: (0,0,5), (1,1,5)
        let entries = op.entries();
        assert_eq!(entries.len(), 2);
        assert_eq!(entries[0], (0, 0, CheckedI64(5)));
        assert_eq!(entries[1], (1, 1, CheckedI64(5)));

        Ok(())
    }

    #[test]
    fn overflow_returns_error() -> Result<(), SparseOperatorError> {
        let mut op = SparseOperator::<CheckedI64>::new(1, 1);
        op.add_entry(0, 0, CheckedI64(i64::MAX))?;

        let err = op.apply(&[CheckedI64(2)]);
        assert!(matches!(err, Err(SparseOperatorError::Overflow)));
        Ok(())
    }

    #[test]
    fn from_entries_checked_rejects_out_of_bounds() {
        let result = SparseOperator::<CheckedI64>::from_entries_checked(
            2,
            2,
            vec![(0, 0, CheckedI64(1)), (2, 0, CheckedI64(1))],
        );

        assert!(matches!(
            result,
            Err(SparseOperatorError::EntryOutOfBounds { row: 2, col: 0, .. })
        ));
    }

    #[test]
    fn compress_is_idempotent() -> Result<(), SparseOperatorError> {
        let mut op = SparseOperator::<CheckedI64>::new(1, 1);
        op.add_entry(0, 0, CheckedI64(1))?;
        op.add_entry(0, 0, CheckedI64(2))?;

        op.compress_checked()?;
        let once = op.entries().to_vec();

        op.compress_checked()?;
        let twice = op.entries().to_vec();

        assert_eq!(once, twice);
        Ok(())
    }

    #[test]
    fn add_entry_invalidates_compress_witness() -> Result<(), SparseOperatorError> {
        let mut op = SparseOperator::<CheckedI64>::new(1, 1);

        assert!(op.is_compressed());

        op.add_entry(0, 0, CheckedI64(1))?;

        assert!(!op.is_compressed());
        Ok(())
    }

    #[test]
    fn compression_preserves_application_semantics() -> Result<(), SparseOperatorError> {
        let mut op = SparseOperator::<CheckedI64>::new(2, 2);
        op.add_entry(0, 0, CheckedI64(2))?;
        op.add_entry(0, 0, CheckedI64(3))?;
        op.add_entry(1, 1, CheckedI64(4))?;

        let x = [CheckedI64(10), CheckedI64(20)];
        let before = op.apply(&x)?;

        op.compress_checked()?;

        let after = op.apply(&x)?;
        assert_eq!(before, after);
        Ok(())
    }
}
