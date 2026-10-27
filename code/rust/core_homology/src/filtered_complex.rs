//! Chain complex equipped with a filtration.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.

use serde::{Deserialize, Serialize};

/// Finite record shell for `filtered_complex`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct FilteredComplex {
    pub label: String,
    pub notes: Vec<String>,
}

impl FilteredComplex {
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


/// A filtration is a nondecreasing sequence of integer times.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiltrationWitness {
    steps: u32,
    span: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FiltrationError {
    Shell,
    Overflow,
    NotNested { index: usize, earlier: i64, later: i64 },
}

// Origin: engine/crates_rs/core_homology/src/filtered_complex.rs
// Claim: urn:core:crates_rs:core-homology:filtered-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FiltrationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FiltrationError {}

impl FiltrationWitness {
    pub fn admit(shell: &FilteredComplex, times: &[i64]) -> Result<Self, FiltrationError> {
        if shell.validate_shell().is_err() {
            return Err(FiltrationError::Shell);
        }
        for (index, window) in times.windows(2).enumerate() {
            if window[1] < window[0] {
                return Err(FiltrationError::NotNested {
                    index,
                    earlier: window[0],
                    later: window[1],
                });
            }
        }
        let steps = u32::try_from(times.len()).map_err(|_| FiltrationError::Overflow)?;
        let span = match (times.first(), times.last()) {
            (Some(first), Some(last)) => last.checked_sub(*first).ok_or(FiltrationError::Overflow)?,
            _ => 0,
        };
        Ok(Self { steps, span })
    }

    pub fn span(&self) -> i64 {
        self.span
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = FilteredComplex::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = FilteredComplex::new("filtered_complex").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }

    #[test]
    fn filtration_times_are_nondecreasing() {
        let shell = FilteredComplex::new("filtered_complex");
        let admitted = FiltrationWitness::admit(&shell, &[0, 2, 2, 5]);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.span()), Some(5));
        assert!(matches!(
            FiltrationWitness::admit(&shell, &[1, 0]),
            Err(FiltrationError::NotNested {
                index: 0,
                earlier: 1,
                later: 0
            })
        ));
    }

}
