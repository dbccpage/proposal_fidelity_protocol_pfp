//! yoneda shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Yoneda embedding / lemma carrier — shape only (label + category_ref).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_9fc91fb9;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_9fc91fb9<T> = std::result::Result<T, BoundaryError_9fc91fb9>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a Yoneda construction on a category reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Yoneda {
    pub label: String,
    pub category_ref: String,
    pub notes: Vec<String>,
}

impl Yoneda {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn on_category(label: impl Into<String>, category_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.category_ref.is_empty() {
            return Err("empty category_ref".into());
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(Yoneda::on_category("y", "C").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Yoneda::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_ref() {
        assert!(Yoneda::new("y").validate_shell().is_err());
    }
}

/// Exact row-sums of a finite hom-table for a Yoneda embedding.
/// Each object carries at least the identity, so the diagonal entry is at least 1.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct YonedaRowSumWitness {
    object_count: usize,
    row_sums: Vec<u64>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum YonedaCountError {
    EmptyLabel,
    EmptyRows,
    RowWidthMismatch { row: usize, width: usize, expected: usize },
    MissingIdentity { object: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/functor/yoneda.rs
// Claim: urn:core:crates_rs:core-category-theory:yoneda:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for YonedaCountError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for YonedaCountError {}

impl YonedaRowSumWitness {
    pub fn try_from_hom_table(
        label: &str,
        hom_counts: &[Vec<u64>],
    ) -> Result<Self, YonedaCountError> {
        if label.is_empty() {
            return Err(YonedaCountError::EmptyLabel);
        }
        if hom_counts.is_empty() {
            return Err(YonedaCountError::EmptyRows);
        }
        let object_count = hom_counts.len();
        let mut row_sums = Vec::with_capacity(object_count);
        for (index, row) in hom_counts.iter().enumerate() {
            if row.len() != object_count {
                return Err(YonedaCountError::RowWidthMismatch {
                    row: index,
                    width: row.len(),
                    expected: object_count,
                });
            }
            let diagonal = row.get(index).copied().ok_or(YonedaCountError::RowWidthMismatch {
                row: index,
                width: row.len(),
                expected: object_count,
            })?;
            if diagonal < 1 {
                return Err(YonedaCountError::MissingIdentity { object: index });
            }
            let mut sum = 0u64;
            for count in row {
                sum = sum.checked_add(*count).ok_or(YonedaCountError::Overflow)?;
            }
            row_sums.push(sum);
        }
        Ok(Self {
            object_count,
            row_sums,
        })
    }

    pub fn object_count(&self) -> usize {
        self.object_count
    }

    pub fn row_sum(&self, object: usize) -> Option<u64> {
        self.row_sums.get(object).copied()
    }
}
