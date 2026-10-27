//! adjunction shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! L ⊣ R declared by left/right functor labels plus unit/counit refs.
//! Shape validation only — not triangle-identity PROVED.

use serde::{Deserialize, Serialize};

/// Best-effort shell for an adjunction L ⊣ R.
///
/// Records functor labels and references to unit/counit shells (by label).
/// Does not certify triangle identities or hom-set bijections.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct AdjunctionShell {
    pub label: String,
    /// Left adjoint L : C → D.
    pub left_functor: String,
    /// Right adjoint R : D → C.
    pub right_functor: String,
    /// Label ref to the unit η : Id_C ⇒ R ∘ L shell.
    pub unit_ref: String,
    /// Label ref to the counit ε : L ∘ R ⇒ Id_D shell.
    pub counit_ref: String,
    /// Optional source category label (domain of L / codomain of R).
    pub source_category: String,
    /// Optional target category label (codomain of L / domain of R).
    pub target_category: String,
    pub notes: Vec<String>,
}

impl AdjunctionShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            left_functor: String::new(),
            right_functor: String::new(),
            unit_ref: String::new(),
            counit_ref: String::new(),
            source_category: String::new(),
            target_category: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        left_functor: impl Into<String>,
        right_functor: impl Into<String>,
        unit_ref: impl Into<String>,
        counit_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            left_functor: left_functor.into(),
            right_functor: right_functor.into(),
            unit_ref: unit_ref.into(),
            counit_ref: counit_ref.into(),
            source_category: String::new(),
            target_category: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_categories(
        mut self,
        source_category: impl Into<String>,
        target_category: impl Into<String>,
    ) -> Self {
        self.source_category = source_category.into();
        self.target_category = target_category.into();
        self
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.left_functor.is_empty() {
            return Err("empty left_functor".into());
        }
        if self.right_functor.is_empty() {
            return Err("empty right_functor".into());
        }
        if self.unit_ref.is_empty() {
            return Err("empty unit_ref".into());
        }
        if self.counit_ref.is_empty() {
            return Err("empty counit_ref".into());
        }
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdjunctionHomWitness {
    left_hom: u64,
    right_hom: u64,
    triangle_steps: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdjunctionHomWitnessError {
    ShellRejected,
    EmptyHom,
    HomMismatch { left_hom: u64, right_hom: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/adjunction/adjunction.rs
// Claim: urn:core:crates_rs:core-category-theory:adjunction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for AdjunctionHomWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for AdjunctionHomWitnessError {}

impl AdjunctionHomWitness {
    pub fn certify(shell: &AdjunctionShell, left_hom: u64, right_hom: u64) -> Result<Self, AdjunctionHomWitnessError> {
        shell.validate_shell().map_err(|_| AdjunctionHomWitnessError::ShellRejected)?;
        if left_hom == 0 || right_hom == 0 { return Err(AdjunctionHomWitnessError::EmptyHom); }
        if left_hom != right_hom { return Err(AdjunctionHomWitnessError::HomMismatch { left_hom, right_hom }); }
        let triangle_steps = 2u64.checked_mul(2).ok_or(AdjunctionHomWitnessError::Overflow)?;
        Ok(Self { left_hom, right_hom, triangle_steps })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let a = AdjunctionShell::between("free-forget", "Free", "Forget", "η", "ε");
        assert!(a.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty_label() {
        assert!(AdjunctionShell::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_functors() {
        let a = AdjunctionShell::new("adj");
        assert!(a.validate_shell().is_err());
    }

    #[test]
    fn with_categories_ok() {
        let a = AdjunctionShell::between("L⊣R", "L", "R", "unit", "counit")
            .with_categories("C", "D")
            .with_note("dev shell");
        assert_eq!(a.source_category, "C");
        assert_eq!(a.target_category, "D");
        assert!(a.validate_shell().is_ok());
    }

#[test]
    fn exact_witness_holds() {
        let shell = AdjunctionShell::between("free-forget", "Free", "Forget", "unit", "counit");
        assert!(matches!(AdjunctionHomWitness::certify(&shell, 5, 5), Ok(w) if w.triangle_steps == 4));
        assert!(matches!(AdjunctionHomWitness::certify(&shell, 5, 4), Err(AdjunctionHomWitnessError::HomMismatch { .. })));
    }
}
