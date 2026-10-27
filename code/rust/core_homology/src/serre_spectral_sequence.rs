//! Serre spectral sequence instance shell.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_c7080d04;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_c7080d04<T> = std::result::Result<T, BoundaryError_c7080d04>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `serre_spectral_sequence`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct SerreSpectralSequence {
    pub label: String,
    pub notes: Vec<String>,
}

impl SerreSpectralSequence {
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
        let s = SerreSpectralSequence::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = SerreSpectralSequence::new("serre_spectral_sequence").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_homology/src/serre_spectral_sequence.rs
// Claim: urn:core:homology:serre:bidegree:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SerreBidegree {
    page: i64,
    source_p: i64,
    source_q: i64,
    target_p: i64,
    target_q: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SerreBidegreeError {
    ShellRefused { reason: String },
    PageNotPositive { page: i64 },
    Overflow,
    TargetMismatch { coordinate: &'static str, computed: i64, claimed: i64 },
}

// Origin: engine/crates_rs/core_homology/src/serre_spectral_sequence.rs
// Claim: urn:core:crates_rs:core-homology:serre-spectral-sequence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SerreBidegreeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SerreBidegreeError {}

impl SerreBidegree {
    pub fn try_on(
        shell: &SerreSpectralSequence,
        page: i64,
        source_p: i64,
        source_q: i64,
        claimed_p: i64,
        claimed_q: i64,
    ) -> Result<Self, SerreBidegreeError> {
        shell
            .validate_shell()
            .map_err(|reason| SerreBidegreeError::ShellRefused { reason })?;
        if page < 1 {
            return Err(SerreBidegreeError::PageNotPositive { page });
        }
        let target_p = source_p.checked_add(page).ok_or(SerreBidegreeError::Overflow)?;
        let target_q = source_q
            .checked_sub(page)
            .ok_or(SerreBidegreeError::Overflow)?
            .checked_add(1)
            .ok_or(SerreBidegreeError::Overflow)?;
        if target_p != claimed_p {
            return Err(SerreBidegreeError::TargetMismatch {
                coordinate: "p",
                computed: target_p,
                claimed: claimed_p,
            });
        }
        if target_q != claimed_q {
            return Err(SerreBidegreeError::TargetMismatch {
                coordinate: "q",
                computed: target_q,
                claimed: claimed_q,
            });
        }
        Ok(Self {
            page,
            source_p,
            source_q,
            target_p,
            target_q,
        })
    }

    pub fn target_p(&self) -> i64 {
        self.target_p
    }

    pub fn target_q(&self) -> i64 {
        self.target_q
    }
}

#[cfg(test)]
mod serre_bidegree_tests {
    use super::*;

    #[test]
    fn page_two_shifts_bidegree() {
        let shell = SerreSpectralSequence::new("serre");
        let witness = SerreBidegree::try_on(&shell, 2, 1, 4, 3, 3);
        assert!(matches!(witness, Ok(ref w) if w.target_p() == 3 && w.target_q() == 3));
    }

    #[test]
    fn refuses_a_wrong_target() {
        let shell = SerreSpectralSequence::new("serre");
        let wrong = SerreBidegree::try_on(&shell, 2, 1, 4, 3, 4);
        assert!(matches!(
            wrong,
            Err(SerreBidegreeError::TargetMismatch { coordinate: "q", computed: 3, claimed: 4 })
        ));
    }
}
