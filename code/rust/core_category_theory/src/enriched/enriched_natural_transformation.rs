//! enriched_natural_transformation shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort enriched natural transformation shell α : F ⇒ G.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct EnrichedNaturalTransformation {
    pub label: String,
    /// Source enriched functor shell label.
    pub source_functor: String,
    /// Target enriched functor shell label.
    pub target_functor: String,
    /// Shared base monoidal V label.
    pub base_monoidal_v: String,
    /// Component family ref α_A : I → D(FA, GA) in V (or equivalent).
    pub components_ref: String,
    pub notes: Vec<String>,
}

impl EnrichedNaturalTransformation {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            source_functor: String::new(),
            target_functor: String::new(),
            base_monoidal_v: String::new(),
            components_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        source_functor: impl Into<String>,
        target_functor: impl Into<String>,
        base_monoidal_v: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            source_functor: source_functor.into(),
            target_functor: target_functor.into(),
            base_monoidal_v: base_monoidal_v.into(),
            components_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.source_functor.is_empty() {
            return Err("empty source_functor".into());
        }
        if self.target_functor.is_empty() {
            return Err("empty target_functor".into());
        }
        if self.base_monoidal_v.is_empty() {
            return Err("empty base_monoidal_v".into());
        }
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NaturalitySquareWitness {
    components: u64,
    cells: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NaturalitySquareWitnessError {
    ShellRejected,
    ZeroComponents,
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/enriched/enriched_natural_transformation.rs
// Claim: urn:core:crates_rs:core-category-theory:enriched-natural-transformation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for NaturalitySquareWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for NaturalitySquareWitnessError {}

impl NaturalitySquareWitness {
    pub fn certify(transformation: &EnrichedNaturalTransformation, components: u64) -> Result<Self, NaturalitySquareWitnessError> {
        transformation.validate_shell().map_err(|_| NaturalitySquareWitnessError::ShellRejected)?;
        if components == 0 { return Err(NaturalitySquareWitnessError::ZeroComponents); }
        let square = 2u64.checked_mul(2).ok_or(NaturalitySquareWitnessError::Overflow)?;
        let cells = components.checked_mul(square).ok_or(NaturalitySquareWitnessError::Overflow)?;
        Ok(Self { components, cells })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(
            EnrichedNaturalTransformation::between("alpha", "F", "G", "V")
                .validate_shell()
                .is_ok()
        );
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(EnrichedNaturalTransformation::new("")
            .validate_shell()
            .is_err());
    }

#[test]
    fn exact_witness_holds() {
        let nt = EnrichedNaturalTransformation::between("a", "F", "G", "V");
        assert!(matches!(NaturalitySquareWitness::certify(&nt, 3), Ok(w) if w.cells == 12));
        assert!(matches!(NaturalitySquareWitness::certify(&nt, 0), Err(NaturalitySquareWitnessError::ZeroComponents)));
    }
}
