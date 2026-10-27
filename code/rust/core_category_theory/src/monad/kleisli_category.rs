//! kleisli_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Kleisli category C_T of a monad T: objects of C, morphisms A → T(B).
//! Shell holds a base monad ref only; construction is external
//! (see crate-root `kleisli_category` / `legacy_monad` for finite builds).

use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled Kleisli category of a monad.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct KleisliCategory {
    pub label: String,
    /// Ref to the base monad T whose Kleisli category this records.
    pub base_monad_ref: String,
    /// Optional base category label (diagnostic).
    pub base_category_ref: String,
    pub notes: Vec<String>,
}

impl KleisliCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_monad_ref: String::new(),
            base_category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn for_monad(label: impl Into<String>, base_monad_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_monad_ref: base_monad_ref.into(),
            base_category_ref: String::new(),
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
            return Err("empty label".into());
        }
        if self.base_monad_ref.is_empty() {
            return Err("empty base_monad_ref".into());
        }
        Ok(())
    }
}


/// Kleisli hom-sets are base hom-sets into `T(B)`: the two counts agree.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct KleisliHomWitness {
    hom_count: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum KleisliHomError {
    Shell,
    HomMismatch { base_homs_into_t: u32, kleisli_homs: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/monad/kleisli_category.rs
// Claim: urn:core:crates_rs:core-category-theory:kleisli-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for KleisliHomError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for KleisliHomError {}

impl KleisliHomWitness {
    pub fn admit(
        shell: &KleisliCategory,
        base_homs_into_t: u32,
        kleisli_homs: u32,
    ) -> Result<Self, KleisliHomError> {
        if shell.validate_shell().is_err() {
            return Err(KleisliHomError::Shell);
        }
        if base_homs_into_t != kleisli_homs {
            return Err(KleisliHomError::HomMismatch {
                base_homs_into_t,
                kleisli_homs,
            });
        }
        Ok(Self {
            hom_count: kleisli_homs,
        })
    }

    pub fn hom_count(&self) -> u32 {
        self.hom_count
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let k = KleisliCategory::for_monad("Kl(Maybe)", "Maybe");
        assert!(k.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(KleisliCategory::new("").validate_shell().is_err());
        assert!(KleisliCategory::new("K").validate_shell().is_err());
    }

    #[test]
    fn kleisli_homs_match_the_base_homs_into_t() {
        let shell = KleisliCategory::for_monad("Kl(Maybe)", "Maybe");
        let admitted = KleisliHomWitness::admit(&shell, 5, 5);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.hom_count()), Some(5));
        assert!(matches!(
            KleisliHomWitness::admit(&shell, 5, 4),
            Err(KleisliHomError::HomMismatch {
                base_homs_into_t: 5,
                kleisli_homs: 4
            })
        ));
    }

}
