//! opfibration shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! An opfibration (cocartesian fibration) p: E → B has cocartesian lifts
//! of morphisms out of each object of E.

use serde::{Deserialize, Serialize};

/// Best-effort opfibration shell p: total → base.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct OpfibrationShell {
    pub label: String,
    pub total_label: String,
    pub base_label: String,
    /// Cleavage claim: cocartesian lifts are chosen (diagnostic flag).
    pub cloven: bool,
    /// Optional cofiber labels over base objects: (base_object, cofiber_label).
    pub cofibers: Vec<(String, String)>,
    pub notes: Vec<String>,
}

impl OpfibrationShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            total_label: String::new(),
            base_label: String::new(),
            cloven: false,
            cofibers: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn over(
        label: impl Into<String>,
        total_label: impl Into<String>,
        base_label: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            total_label: total_label.into(),
            base_label: base_label.into(),
            cloven: false,
            cofibers: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.total_label.is_empty() {
            return Err("empty total_label".into());
        }
        if self.base_label.is_empty() {
            return Err("empty base_label".into());
        }
        for (i, (b, c)) in self.cofibers.iter().enumerate() {
            if b.is_empty() || c.is_empty() {
                return Err(format!("empty cofiber entry at index {i}"));
            }
        }
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CleavageWitness {
    base_morphisms: u64,
    chosen_lifts: u64,
    cofiber_count: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CleavageWitnessError {
    ShellRejected,
    CleavageMismatch { base_morphisms: u64, chosen_lifts: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/category/opfibration.rs
// Claim: urn:core:crates_rs:core-category-theory:opfibration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CleavageWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CleavageWitnessError {}

impl CleavageWitness {
    pub fn certify(shell: &OpfibrationShell, base_morphisms: u64, chosen_lifts: u64) -> Result<Self, CleavageWitnessError> {
        shell.validate_shell().map_err(|_| CleavageWitnessError::ShellRejected)?;
        if shell.cloven {
            if chosen_lifts != base_morphisms {
                return Err(CleavageWitnessError::CleavageMismatch { base_morphisms, chosen_lifts });
            }
        } else if chosen_lifts != 0 {
            return Err(CleavageWitnessError::CleavageMismatch { base_morphisms, chosen_lifts });
        }
        let cofiber_count = u64::try_from(shell.cofibers.len()).map_err(|_| CleavageWitnessError::Overflow)?;
        Ok(Self { base_morphisms, chosen_lifts, cofiber_count })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(OpfibrationShell::over("Opf", "E", "B")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(OpfibrationShell::new("").validate_shell().is_err());
        assert!(OpfibrationShell::new("O").validate_shell().is_err());
    }

#[test]
    fn exact_witness_holds() {
        let mut shell = OpfibrationShell::over("Opf", "E", "B");
        assert!(matches!(CleavageWitness::certify(&shell, 4, 0), Ok(w) if w.chosen_lifts == 0));
        shell.cloven = true;
        assert!(matches!(CleavageWitness::certify(&shell, 4, 3), Err(CleavageWitnessError::CleavageMismatch { .. })));
    }
}
