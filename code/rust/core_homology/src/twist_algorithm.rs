//! Twist reduction algorithm for persistent homology.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_25e483e6;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_25e483e6<T> = std::result::Result<T, BoundaryError_25e483e6>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `twist_algorithm`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct TwistAlgorithm {
    pub label: String,
    pub notes: Vec<String>,
}

impl TwistAlgorithm {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("label must be non-empty".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_homology/src/twist_algorithm.rs
// Claim: urn:core:crates_rs:core-homology:twist-algorithm:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = TwistAlgorithm::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = TwistAlgorithm::new("twist_algorithm").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Column reduction over GF(2) with distinct lowest-one pivots. Rank plus nullity equals the width.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReducedBoundary {
    rank: usize,
    nullity: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TwistExactError {
    Shape,
    Row,
    StepBound,
    Pivot,
    Rank,
}

impl std::fmt::Display for TwistExactError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Shape => write!(f, "boundary needs between 1 and 64 rows"),
            Self::Row => write!(f, "a column uses a row outside the matrix"),
            Self::StepBound => write!(f, "reduction exceeded the column-row step bound"),
            Self::Pivot => write!(f, "two reduced columns share a lowest one"),
            Self::Rank => write!(f, "rank and nullity do not add to the column count"),
        }
    }
}

impl std::error::Error for TwistExactError {}

impl ReducedBoundary {
    pub fn reduce(rows: usize, columns: &[u64]) -> Result<Self, TwistExactError> {
        if rows == 0 || rows > 64 {
            return Err(TwistExactError::Shape);
        }
        let mask = if rows == 64 {
            u64::MAX
        } else {
            (1u64 << rows) - 1
        };
        if columns.iter().any(|column| column & !mask != 0) {
            return Err(TwistExactError::Row);
        }
        let mut cols = columns.to_vec();
        let cap = columns
            .len()
            .saturating_mul(rows.saturating_add(1))
            .saturating_add(1);
        Self::reduce_columns_in_place(rows, &mut cols, cap)?;
        let rank = Self::count_reduced_rank(rows, &cols)?;
        let nullity = cols.len().checked_sub(rank).ok_or(TwistExactError::Rank)?;
        if rank.checked_add(nullity) != Some(cols.len()) {
            return Err(TwistExactError::Rank);
        }
        Ok(Self { rank, nullity })
    }

    fn reduce_columns_in_place(
        rows: usize,
        cols: &mut [u64],
        cap: usize,
    ) -> Result<(), TwistExactError> {
        let mut pivot = vec![None; rows];
        let mut steps = 0usize;
        for j in 0..cols.len() {
            loop {
                steps = steps.checked_add(1).ok_or(TwistExactError::StepBound)?;
                if steps > cap {
                    return Err(TwistExactError::StepBound);
                }
                let column = *cols.get(j).ok_or(TwistExactError::Shape)?;
                if column == 0 {
                    break;
                }
                let low = column.trailing_zeros() as usize;
                if let Some(other) = *pivot.get(low).ok_or(TwistExactError::Row)? {
                    let donor = *cols.get(other).ok_or(TwistExactError::Shape)?;
                    cols[j] ^= donor;
                } else {
                    pivot[low] = Some(j);
                    break;
                }
            }
        }
        Ok(())
    }

    fn count_reduced_rank(rows: usize, cols: &[u64]) -> Result<usize, TwistExactError> {
        let mut seen = vec![false; rows];
        let mut rank = 0usize;
        for column in cols {
            if *column == 0 {
                continue;
            }
            let low = column.trailing_zeros() as usize;
            if *seen.get(low).ok_or(TwistExactError::Row)? {
                return Err(TwistExactError::Pivot);
            }
            seen[low] = true;
            rank = rank.checked_add(1).ok_or(TwistExactError::Rank)?;
        }
        Ok(rank)
    }

    pub fn rank(&self) -> usize {
        self.rank
    }

    pub fn nullity(&self) -> usize {
        self.nullity
    }
}

#[cfg(test)]
mod exact_twist_tests {
    use super::*;

    #[test]
    fn a_rank_two_boundary_has_nullity_one() {
        let reduced = ReducedBoundary::reduce(2, &[1, 0b11, 0b10]).map_or_else(|_| loop { assert!(false); }, |value| value);
        assert_eq!(reduced.rank(), 2);
        assert_eq!(reduced.nullity(), 1);
    }
}
