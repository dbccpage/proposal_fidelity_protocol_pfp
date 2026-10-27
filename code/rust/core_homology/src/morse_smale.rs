//! Combinatorial Morse–Smale complex shell.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.

use serde::{Deserialize, Serialize};

/// Finite record shell for `morse_smale`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct MorseSmale {
    pub label: String,
    pub notes: Vec<String>,
}

impl MorseSmale {
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

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MorseCancellationWitness {
    index0: u64,
    index1: u64,
    pairings: u64,
    unpaired0: u64,
    unpaired1: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MorseCancellationWitnessError {
    ShellRejected,
    PairingExceedsCritical { pairings: u64, index0: u64, index1: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/morse_smale.rs
// Claim: urn:core:crates_rs:core-homology:morse-smale:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MorseCancellationWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MorseCancellationWitnessError {}

impl MorseCancellationWitness {
    pub fn certify(shell: &MorseSmale, index0: u64, index1: u64, pairings: u64) -> Result<Self, MorseCancellationWitnessError> {
        shell.validate_shell().map_err(|_| MorseCancellationWitnessError::ShellRejected)?;
        if pairings > index0 || pairings > index1 {
            return Err(MorseCancellationWitnessError::PairingExceedsCritical { pairings, index0, index1 });
        }
        let unpaired0 = index0.checked_sub(pairings).ok_or(MorseCancellationWitnessError::Overflow)?;
        let unpaired1 = index1.checked_sub(pairings).ok_or(MorseCancellationWitnessError::Overflow)?;
        let cancelled = pairings.checked_mul(2).ok_or(MorseCancellationWitnessError::Overflow)?;
        let total = index0.checked_add(index1).ok_or(MorseCancellationWitnessError::Overflow)?;
        if cancelled > total { return Err(MorseCancellationWitnessError::PairingExceedsCritical { pairings, index0, index1 }); }
        Ok(Self { index0, index1, pairings, unpaired0, unpaired1 })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = MorseSmale::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = MorseSmale::new("morse_smale").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }

#[test]
    fn exact_witness_holds() {
        let shell = MorseSmale::new("ms");
        assert!(matches!(MorseCancellationWitness::certify(&shell, 3, 2, 2), Ok(w) if w.unpaired0 == 1 && w.unpaired1 == 0));
        assert!(matches!(MorseCancellationWitness::certify(&shell, 1, 2, 2), Err(MorseCancellationWitnessError::PairingExceedsCritical { .. })));
    }
}
