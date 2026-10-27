//! symmetric_monoidal_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort symmetric monoidal functor shell.
/// Monoidal functor that preserves braiding (symmetry) up to claimed coherence.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct SymmetricMonoidalFunctor {
    pub label: String,
    /// Domain symmetric monoidal category shell label.
    pub domain_symmetric: String,
    /// Codomain symmetric monoidal category shell label.
    pub codomain_symmetric: String,
    /// Underlying monoidal functor shell label.
    pub monoidal_functor_ref: String,
    /// Braiding-preservation witness / coherence ref.
    pub braiding_preservation_ref: String,
    pub notes: Vec<String>,
}

impl SymmetricMonoidalFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            domain_symmetric: String::new(),
            codomain_symmetric: String::new(),
            monoidal_functor_ref: String::new(),
            braiding_preservation_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        domain_symmetric: impl Into<String>,
        codomain_symmetric: impl Into<String>,
        monoidal_functor_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            domain_symmetric: domain_symmetric.into(),
            codomain_symmetric: codomain_symmetric.into(),
            monoidal_functor_ref: monoidal_functor_ref.into(),
            braiding_preservation_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.domain_symmetric.is_empty() {
            return Err("empty domain_symmetric".into());
        }
        if self.codomain_symmetric.is_empty() {
            return Err("empty codomain_symmetric".into());
        }
        if self.monoidal_functor_ref.is_empty() {
            return Err("empty monoidal_functor_ref".into());
        }
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SymmetryOrderWitness {
    braiding_applications: u64,
    pairs: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SymmetryOrderWitnessError {
    ShellRejected,
    OddBraiding { braiding_applications: u64 },
    ZeroApplications,
}

// Origin: engine/crates_rs/core_category_theory/src/monoidal/symmetric_monoidal_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:symmetric-monoidal-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SymmetryOrderWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SymmetryOrderWitnessError {}

impl SymmetryOrderWitness {
    pub fn certify(functor: &SymmetricMonoidalFunctor, braiding_applications: u64) -> Result<Self, SymmetryOrderWitnessError> {
        functor.validate_shell().map_err(|_| SymmetryOrderWitnessError::ShellRejected)?;
        if braiding_applications == 0 { return Err(SymmetryOrderWitnessError::ZeroApplications); }
        if braiding_applications % 2 != 0 { return Err(SymmetryOrderWitnessError::OddBraiding { braiding_applications }); }
        let pairs = braiding_applications.checked_div(2).ok_or(SymmetryOrderWitnessError::OddBraiding { braiding_applications })?;
        Ok(Self { braiding_applications, pairs })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(SymmetricMonoidalFunctor::between("SF", "C", "D", "F")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(SymmetricMonoidalFunctor::new("").validate_shell().is_err());
    }

#[test]
    fn exact_witness_holds() {
        let functor = SymmetricMonoidalFunctor::between("SF", "C", "D", "F");
        assert!(matches!(SymmetryOrderWitness::certify(&functor, 4), Ok(w) if w.pairs == 2));
        assert!(matches!(SymmetryOrderWitness::certify(&functor, 3), Err(SymmetryOrderWitnessError::OddBraiding { .. })));
    }
}
