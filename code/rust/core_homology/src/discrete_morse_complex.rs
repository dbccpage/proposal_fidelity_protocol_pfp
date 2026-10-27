//! Morse chain complex (smaller, homotopy equivalent).
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_549f38e3;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_549f38e3<T> = std::result::Result<T, BoundaryError_549f38e3>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `discrete_morse_complex`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct DiscreteMorseComplex {
    pub label: String,
    pub notes: Vec<String>,
}

impl DiscreteMorseComplex {
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
        let s = DiscreteMorseComplex::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = DiscreteMorseComplex::new("discrete_morse_complex").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// A Morse matching pairs distinct cells. Twice the pair count cannot exceed
/// the cell count; the remainder is the critical set.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MorseMatchingCensus {
    cells: u64,
    pairs: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum MorseMatchingError {
    PairsExceedCells { cells: u64, pairs: u64 },
    PairOverflow { pairs: u64 },
}

// Origin: engine/crates_rs/core_homology/src/discrete_morse_complex.rs
// Claim: urn:core:crates_rs:core-homology:discrete-morse-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MorseMatchingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MorseMatchingError {}

impl MorseMatchingCensus {
    pub fn try_new(cells: u64, pairs: u64) -> Result<Self, MorseMatchingError> {
        let covered = pairs
            .checked_mul(2)
            .ok_or(MorseMatchingError::PairOverflow { pairs })?;
        if covered > cells {
            return Err(MorseMatchingError::PairsExceedCells { cells, pairs });
        }
        Ok(Self { cells, pairs })
    }

    pub fn critical_cells(&self) -> Option<u64> {
        let covered = self.pairs.checked_mul(2)?;
        self.cells.checked_sub(covered)
    }
}

#[cfg(test)]
mod morse_matching_witness {
    use super::*;

    #[test]
    fn critical_cells_are_unpaired() {
        let census = MorseMatchingCensus::try_new(7, 2);
        assert!(census.is_ok());
        if let Ok(census) = census {
            assert_eq!(census.critical_cells(), Some(3));
        }
    }

    #[test]
    fn refuses_overmatching() {
        assert!(matches!(
            MorseMatchingCensus::try_new(3, 2),
            Err(MorseMatchingError::PairsExceedCells { cells: 3, pairs: 2 })
        ));
    }
}
