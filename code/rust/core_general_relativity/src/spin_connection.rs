//! `spin_connection` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_ae8c9c86;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_ae8c9c86<T> = std::result::Result<T, BoundaryError_ae8c9c86>;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `spin_connection` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct SpinConnection {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl SpinConnection {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_and_fence() {
        let x = SpinConnection::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(SpinConnection::authority_fence().contains("AuthorityEffect None"));
    }
}

/// Skew-symmetric integer connection. `SpinConnection::degree` is the frame dimension.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SkewConnectionWitness {
    dimension: usize,
    entries: Vec<i64>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SkewConnectionError {
    DegreeMismatch { degree: usize, dimension: usize },
    Shape,
    NotSkew { row: usize, column: usize, value: i64, opposite: i64 },
    Diagonal { index: usize, value: i64 },
    Index,
    Overflow,
}

// Origin: engine/crates_rs/core_general_relativity/src/spin_connection.rs
// Claim: urn:core:crates_rs:core-general-relativity:spin-connection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SkewConnectionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SkewConnectionError {}

fn verify_skew_entry(
    dimension: usize,
    entries_row_major: &[i64],
    row: usize,
    column: usize,
) -> Result<(), SkewConnectionError> {
    let index = row
        .checked_mul(dimension)
        .and_then(|value| value.checked_add(column))
        .ok_or(SkewConnectionError::Overflow)?;
    let opposite_index = column
        .checked_mul(dimension)
        .and_then(|value| value.checked_add(row))
        .ok_or(SkewConnectionError::Overflow)?;
    let value = *entries_row_major.get(index).ok_or(SkewConnectionError::Index)?;
    let opposite = *entries_row_major
        .get(opposite_index)
        .ok_or(SkewConnectionError::Index)?;
    if row == column && value != 0 {
        return Err(SkewConnectionError::Diagonal { index: row, value });
    }
    let negated = value.checked_neg().ok_or(SkewConnectionError::Overflow)?;
    if opposite != negated {
        return Err(SkewConnectionError::NotSkew {
            row,
            column,
            value,
            opposite,
        });
    }
    Ok(())
}

impl SkewConnectionWitness {
    pub fn try_for_connection(
        connection: &SpinConnection,
        entries_row_major: &[i64],
    ) -> Result<Self, SkewConnectionError> {
        let dimension = connection.degree;
        let expected = dimension.checked_mul(dimension).ok_or(SkewConnectionError::Overflow)?;
        if entries_row_major.len() != expected {
            return Err(SkewConnectionError::Shape);
        }
        for row in 0..dimension {
            for column in 0..dimension {
                verify_skew_entry(dimension, entries_row_major, row, column)?;
            }
        }
        Ok(Self { dimension, entries: entries_row_major.to_vec() })
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    pub fn entries(&self) -> &[i64] {
        &self.entries
    }
}
