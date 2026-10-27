//! Clearing lemma speed-up for PH reduction.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_cda6c614;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_cda6c614<T> = std::result::Result<T, BoundaryError_cda6c614>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `clearing_optimization`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct ClearingOptimization {
    pub label: String,
    pub notes: Vec<String>,
}

impl ClearingOptimization {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = ClearingOptimization::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = ClearingOptimization::new("clearing_optimization").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_homology/src/clearing_optimization.rs
// Claim: urn:core:homology:clearing:unit-pivot:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClearedColumn {
    pivot_row: usize,
    pivot: i64,
    height: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ClearedColumnError {
    ShellRefused { reason: String },
    EmptyColumn,
    LengthMismatch { pivot: usize, other: usize, claimed: usize },
    PivotRowOutOfRange { pivot_row: usize, height: usize },
    PivotNotUnit { pivot: i64 },
    Overflow { index: usize },
    UpdateMismatch { index: usize, computed: i64, claimed: i64 },
    PivotNotCleared { value: i64 },
}

// Origin: engine/crates_rs/core_homology/src/clearing_optimization.rs
// Claim: urn:core:crates_rs:core-homology:clearing-optimization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ClearedColumnError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ClearedColumnError {}

impl ClearedColumn {
    pub fn try_on(
        shell: &ClearingOptimization,
        pivot_column: &[i64],
        other: &[i64],
        claimed: &[i64],
        pivot_row: usize,
    ) -> Result<Self, ClearedColumnError> {
        shell
            .validate_shell()
            .map_err(|reason| ClearedColumnError::ShellRefused { reason })?;
        let (pivot, factor) = Self::validate_pivot(pivot_column, other, claimed, pivot_row)?;
        Self::verify_cleared_entries(pivot_column, other, claimed, factor, pivot_row)?;
        Ok(Self {
            pivot_row,
            pivot,
            height: pivot_column.len(),
        })
    }

    fn validate_pivot(
        pivot_column: &[i64],
        other: &[i64],
        claimed: &[i64],
        pivot_row: usize,
    ) -> Result<(i64, i64), ClearedColumnError> {
        if pivot_column.is_empty() {
            return Err(ClearedColumnError::EmptyColumn);
        }
        if other.len() != pivot_column.len() || claimed.len() != pivot_column.len() {
            return Err(ClearedColumnError::LengthMismatch {
                pivot: pivot_column.len(),
                other: other.len(),
                claimed: claimed.len(),
            });
        }
        let pivot = *pivot_column
            .get(pivot_row)
            .ok_or(ClearedColumnError::PivotRowOutOfRange {
                pivot_row,
                height: pivot_column.len(),
            })?;
        if pivot != 1 && pivot != -1 {
            return Err(ClearedColumnError::PivotNotUnit { pivot });
        }
        let factor = other
            .get(pivot_row)
            .and_then(|&entry| entry.checked_mul(pivot))
            .ok_or(ClearedColumnError::Overflow { index: pivot_row })?;
        Ok((pivot, factor))
    }

    fn verify_cleared_entries(
        pivot_column: &[i64],
        other: &[i64],
        claimed: &[i64],
        factor: i64,
        pivot_row: usize,
    ) -> Result<(), ClearedColumnError> {
        for index in 0..pivot_column.len() {
            let computed = pivot_column
                .get(index)
                .and_then(|&pe| factor.checked_mul(pe))
                .and_then(|scaled| other.get(index).and_then(|&oe| oe.checked_sub(scaled)))
                .ok_or(ClearedColumnError::Overflow { index })?;
            let claimed_entry = *claimed.get(index).ok_or(ClearedColumnError::Overflow { index })?;
            if computed != claimed_entry {
                return Err(ClearedColumnError::UpdateMismatch {
                    index,
                    computed,
                    claimed: claimed_entry,
                });
            }
        }
        let cleared_pivot = *claimed.get(pivot_row).ok_or(ClearedColumnError::Overflow { index: pivot_row })?;
        if cleared_pivot != 0 {
            return Err(ClearedColumnError::PivotNotCleared { value: cleared_pivot });
        }
        Ok(())
    }

    pub fn height(&self) -> usize {
        self.height
    }

    pub fn pivot(&self) -> i64 {
        self.pivot
    }
}

#[cfg(test)]
mod cleared_column_tests {
    use super::*;

    #[test]
    fn unit_pivot_clears_the_other_column() {
        let shell = ClearingOptimization::new("clearing");
        let witness = ClearedColumn::try_on(&shell, &[1, 2], &[3, 4], &[0, -2], 0);
        assert!(matches!(witness, Ok(ref w) if w.height() == 2 && w.pivot() == 1));
    }

    #[test]
    fn refuses_a_non_unit_pivot() {
        let shell = ClearingOptimization::new("clearing");
        let wrong = ClearedColumn::try_on(&shell, &[2, 0], &[1, 0], &[0, 0], 0);
        assert!(matches!(wrong, Err(ClearedColumnError::PivotNotUnit { pivot: 2 })));
    }
}
