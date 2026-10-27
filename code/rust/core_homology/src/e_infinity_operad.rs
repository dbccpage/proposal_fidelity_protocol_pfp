//! E∞ operad shell.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.

use serde::{Deserialize, Serialize};

/// Finite record shell for `e_infinity_operad`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct EInfinityOperad {
    pub label: String,
    pub notes: Vec<String>,
}

impl EInfinityOperad {
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
pub struct SymmetricGroupOrderWitness {
    arity: u64,
    symmetry_order: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SymmetricGroupOrderWitnessError {
    ShellRejected,
    ArityOutOfRange { arity: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/e_infinity_operad.rs
// Claim: urn:core:crates_rs:core-homology:e-infinity-operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SymmetricGroupOrderWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SymmetricGroupOrderWitnessError {}

impl SymmetricGroupOrderWitness {
    pub fn certify(shell: &EInfinityOperad, arity: u64) -> Result<Self, SymmetricGroupOrderWitnessError> {
        shell.validate_shell().map_err(|_| SymmetricGroupOrderWitnessError::ShellRejected)?;
        if arity == 0 || arity > 20 { return Err(SymmetricGroupOrderWitnessError::ArityOutOfRange { arity }); }
        let mut symmetry_order = 1u64;
        let mut k = 1u64;
        while k <= arity {
            symmetry_order = symmetry_order.checked_mul(k).ok_or(SymmetricGroupOrderWitnessError::Overflow)?;
            k = k.checked_add(1).ok_or(SymmetricGroupOrderWitnessError::Overflow)?;
        }
        Ok(Self { arity, symmetry_order })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = EInfinityOperad::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = EInfinityOperad::new("e_infinity_operad").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }

#[test]
    fn exact_witness_holds() {
        let shell = EInfinityOperad::new("e-inf");
        assert!(matches!(SymmetricGroupOrderWitness::certify(&shell, 4), Ok(w) if w.symmetry_order == 24));
        assert!(matches!(SymmetricGroupOrderWitness::certify(&shell, 0), Err(SymmetricGroupOrderWitnessError::ArityOutOfRange { .. })));
    }
}
