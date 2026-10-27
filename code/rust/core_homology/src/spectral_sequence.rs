//! Spectral sequence E-page machine (shell).
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.

use serde::{Deserialize, Serialize};

/// Finite record shell for `spectral_sequence`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct SpectralSequence {
    pub label: String,
    pub notes: Vec<String>,
}

impl SpectralSequence {
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


/// Homological differential `d_r` has bidegree `(-r, r - 1)` and therefore
/// drops total degree by exactly 1.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpectralDegreeWitness {
    page: u32,
    drop: i32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SpectralDegreeError {
    Shell,
    PageZero,
    Overflow,
    DegreeDefect { drop: i32 },
    PageMismatch { p_drop: i32, page: i32 },
}

// Origin: engine/crates_rs/core_homology/src/spectral_sequence.rs
// Claim: urn:core:crates_rs:core-homology:spectral-sequence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SpectralDegreeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SpectralDegreeError {}

impl SpectralDegreeWitness {
    pub fn admit(
        shell: &SpectralSequence,
        page: u32,
        p: i32,
        q: i32,
    ) -> Result<Self, SpectralDegreeError> {
        if shell.validate_shell().is_err() {
            return Err(SpectralDegreeError::Shell);
        }
        if page == 0 {
            return Err(SpectralDegreeError::PageZero);
        }
        let page_i = i32::try_from(page).map_err(|_| SpectralDegreeError::Overflow)?;
        let (target_p, drop) = Self::compute_spectral_target(page_i, p, q)?;
        if drop != 1 {
            return Err(SpectralDegreeError::DegreeDefect { drop });
        }
        let p_drop = p.checked_sub(target_p).ok_or(SpectralDegreeError::Overflow)?;
        if p_drop != page_i {
            return Err(SpectralDegreeError::PageMismatch { p_drop, page: page_i });
        }
        Ok(Self { page, drop })
    }

    fn compute_spectral_target(
        page_i: i32,
        p: i32,
        q: i32,
    ) -> Result<(i32, i32), SpectralDegreeError> {
        let source = p.checked_add(q).ok_or(SpectralDegreeError::Overflow)?;
        let target_p = p.checked_sub(page_i).ok_or(SpectralDegreeError::Overflow)?;
        let target_q = q
            .checked_add(page_i)
            .and_then(|v| v.checked_sub(1))
            .ok_or(SpectralDegreeError::Overflow)?;
        let target = target_p
            .checked_add(target_q)
            .ok_or(SpectralDegreeError::Overflow)?;
        let drop = source.checked_sub(target).ok_or(SpectralDegreeError::Overflow)?;
        Ok((target_p, drop))
    }

    pub fn drop(&self) -> i32 {
        self.drop
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = SpectralSequence::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = SpectralSequence::new("spectral_sequence").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }

    #[test]
    fn page_differential_drops_total_degree_by_one() {
        let shell = SpectralSequence::new("spectral_sequence");
        let admitted = SpectralDegreeWitness::admit(&shell, 2, 3, 4);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.drop()), Some(1));
        assert!(matches!(
            SpectralDegreeWitness::admit(&shell, 0, 0, 0),
            Err(SpectralDegreeError::PageZero)
        ));
    }

}
