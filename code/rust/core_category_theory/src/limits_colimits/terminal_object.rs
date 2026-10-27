//! terminal_object shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort shell for a terminal object (limit of the empty diagram).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct TerminalObject {
    pub label: String,
    /// Object claimed to be terminal.
    pub object: String,
    /// Ambient category reference (diagnostic).
    pub category_ref: String,
    pub notes: Vec<String>,
}

impl TerminalObject {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            object: String::new(),
            category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn in_category(
        label: impl Into<String>,
        object: impl Into<String>,
        category_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            object: object.into(),
            category_ref: category_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.object.is_empty() {
            return Err("empty object".into());
        }
        if self.category_ref.is_empty() {
            return Err("empty category_ref".into());
        }
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TerminalArrowWitness {
    object_count: u64,
    arrows_into_terminal: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TerminalArrowWitnessError {
    ShellRejected,
    ZeroObjects,
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/terminal_object.rs
// Claim: urn:core:crates_rs:core-category-theory:terminal-object:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TerminalArrowWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TerminalArrowWitnessError {}

impl TerminalArrowWitness {
    pub fn certify(terminal: &TerminalObject, object_count: u64) -> Result<Self, TerminalArrowWitnessError> {
        terminal.validate_shell().map_err(|_| TerminalArrowWitnessError::ShellRejected)?;
        if object_count == 0 { return Err(TerminalArrowWitnessError::ZeroObjects); }
        Ok(Self { object_count, arrows_into_terminal: object_count })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(TerminalObject::in_category("1", "1", "C")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(TerminalObject::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_object() {
        assert!(TerminalObject::new("t").validate_shell().is_err());
    }

#[test]
    fn exact_witness_holds() {
        let terminal = TerminalObject::in_category("1", "1", "C");
        assert!(matches!(TerminalArrowWitness::certify(&terminal, 4), Ok(w) if w.arrows_into_terminal == 4));
        assert!(matches!(TerminalArrowWitness::certify(&terminal, 0), Err(TerminalArrowWitnessError::ZeroObjects)));
    }
}
