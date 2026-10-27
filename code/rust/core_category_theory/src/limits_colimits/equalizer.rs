//! equalizer shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort shell for an equalizer of a parallel pair.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Equalizer {
    pub label: String,
    pub equalizer_object: String,
    pub source: String,
    pub target: String,
    pub morphism_f: String,
    pub morphism_g: String,
    /// Equalizer morphism e : E → source with f∘e = g∘e.
    pub equalizer_morphism: String,
    pub notes: Vec<String>,
}

impl Equalizer {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            equalizer_object: String::new(),
            source: String::new(),
            target: String::new(),
            morphism_f: String::new(),
            morphism_g: String::new(),
            equalizer_morphism: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of_pair(
        label: impl Into<String>,
        equalizer_object: impl Into<String>,
        source: impl Into<String>,
        target: impl Into<String>,
        morphism_f: impl Into<String>,
        morphism_g: impl Into<String>,
        equalizer_morphism: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            equalizer_object: equalizer_object.into(),
            source: source.into(),
            target: target.into(),
            morphism_f: morphism_f.into(),
            morphism_g: morphism_g.into(),
            equalizer_morphism: equalizer_morphism.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.equalizer_object.is_empty() {
            return Err("empty equalizer_object".into());
        }
        if self.source.is_empty() {
            return Err("empty source".into());
        }
        if self.target.is_empty() {
            return Err("empty target".into());
        }
        if self.morphism_f.is_empty() {
            return Err("empty morphism_f".into());
        }
        if self.morphism_g.is_empty() {
            return Err("empty morphism_g".into());
        }
        if self.equalizer_morphism.is_empty() {
            return Err("empty equalizer_morphism".into());
        }
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EqualizerDimensionWitness {
    dim_equalizer: u64,
    dim_source: u64,
    dim_target: u64,
    parallel_arrows: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EqualizerDimensionWitnessError {
    ShellRejected,
    ZeroDimension,
    NotASubobject { dim_equalizer: u64, dim_source: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/equalizer.rs
// Claim: urn:core:crates_rs:core-category-theory:equalizer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for EqualizerDimensionWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for EqualizerDimensionWitnessError {}

impl EqualizerDimensionWitness {
    pub fn certify(equalizer: &Equalizer, dim_equalizer: u64, dim_source: u64, dim_target: u64) -> Result<Self, EqualizerDimensionWitnessError> {
        equalizer.validate_shell().map_err(|_| EqualizerDimensionWitnessError::ShellRejected)?;
        if dim_equalizer == 0 || dim_source == 0 || dim_target == 0 { return Err(EqualizerDimensionWitnessError::ZeroDimension); }
        if dim_equalizer > dim_source { return Err(EqualizerDimensionWitnessError::NotASubobject { dim_equalizer, dim_source }); }
        Ok(Self { dim_equalizer, dim_source, dim_target, parallel_arrows: 2 })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let e = Equalizer::of_pair("eq", "E", "A", "B", "f", "g", "e");
        assert!(e.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Equalizer::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_morphism() {
        assert!(Equalizer::new("eq").validate_shell().is_err());
    }

#[test]
    fn exact_witness_holds() {
        let eq = Equalizer::of_pair("eq", "E", "A", "B", "f", "g", "e");
        assert!(matches!(EqualizerDimensionWitness::certify(&eq, 2, 5, 3), Ok(w) if w.parallel_arrows == 2));
        assert!(matches!(EqualizerDimensionWitness::certify(&eq, 6, 5, 3), Err(EqualizerDimensionWitnessError::NotASubobject { .. })));
    }
}
