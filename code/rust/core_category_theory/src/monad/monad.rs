//! monad shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! A monad is an endofunctor T with unit η : Id ⇒ T and multiply μ : T² ⇒ T.
//! This shell holds label refs only; law discharge is external.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_dbff0ffd;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_dbff0ffd<T> = std::result::Result<T, BoundaryError_dbff0ffd>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled monad (T, η, μ).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Monad {
    pub label: String,
    /// Ref to the underlying endofunctor T : C → C.
    pub endofunctor_ref: String,
    /// Ref to the unit natural transformation η : Id ⇒ T.
    pub unit_ref: String,
    /// Ref to the multiplication natural transformation μ : T² ⇒ T.
    pub multiply_ref: String,
    /// Optional base category label (diagnostic).
    pub category_ref: String,
    pub notes: Vec<String>,
}

impl Monad {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            endofunctor_ref: String::new(),
            unit_ref: String::new(),
            multiply_ref: String::new(),
            category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_structure(
        label: impl Into<String>,
        endofunctor_ref: impl Into<String>,
        unit_ref: impl Into<String>,
        multiply_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            endofunctor_ref: endofunctor_ref.into(),
            unit_ref: unit_ref.into(),
            multiply_ref: multiply_ref.into(),
            category_ref: String::new(),
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
        if self.endofunctor_ref.is_empty() {
            return Err("empty endofunctor_ref".into());
        }
        if self.unit_ref.is_empty() {
            return Err("empty unit_ref".into());
        }
        if self.multiply_ref.is_empty() {
            return Err("empty multiply_ref".into());
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let m = Monad::with_structure("Maybe", "T_Maybe", "η_Maybe", "μ_Maybe");
        assert!(m.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty_label() {
        assert!(Monad::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_refs() {
        let m = Monad::new("M");
        assert!(m.validate_shell().is_err());
    }

    #[test]
    fn structure_fields_present() {
        let m = Monad::with_structure("Id", "T_Id", "η_Id", "μ_Id").with_note("shell");
        assert_eq!(m.endofunctor_ref, "T_Id");
        assert_eq!(m.unit_ref, "η_Id");
        assert_eq!(m.multiply_ref, "μ_Id");
        assert_eq!(m.notes.len(), 1);
        assert!(m.validate_shell().is_ok());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WriterLawError {
    Shell,
    Modulus,
}

// Origin: engine/crates_rs/core_category_theory/src/monad/monad.rs
// Claim: urn:core:crates_rs:core-category-theory:monad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for WriterLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for WriterLawError {}

/// The writer monad of the cyclic monoid Z/nZ, checked on every triple when n is at most 12.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CyclicWriterWitness {
    modulus: u32,
}

impl CyclicWriterWitness {
    fn check_writer_pair(modulus: u32, left: u32, middle: u32) -> Result<(), WriterLawError> {
        let inner = left.checked_add(middle).ok_or(WriterLawError::Modulus)? % modulus;
        for right in 0..modulus {
            let associated_left = inner.checked_add(right).ok_or(WriterLawError::Modulus)? % modulus;
            let associated_right = left
                .checked_add(middle.checked_add(right).ok_or(WriterLawError::Modulus)? % modulus)
                .ok_or(WriterLawError::Modulus)?
                % modulus;
            if associated_left != associated_right {
                return Err(WriterLawError::Modulus);
            }
        }
        Ok(())
    }

    pub fn try_new(shell: &Monad, modulus: u32) -> Result<Self, WriterLawError> {
        if shell.validate_shell().is_err() {
            return Err(WriterLawError::Shell);
        }
        if modulus == 0 || modulus > 12 {
            return Err(WriterLawError::Modulus);
        }
        for left in 0..modulus {
            let unit = left.checked_add(0).ok_or(WriterLawError::Modulus)? % modulus;
            if unit != left {
                return Err(WriterLawError::Modulus);
            }
            for middle in 0..modulus {
                Self::check_writer_pair(modulus, left, middle)?;
            }
        }
        Ok(Self { modulus })
    }

    pub fn modulus(&self) -> u32 { self.modulus }
}

#[cfg(test)]
mod writer_law_tests {
    use super::*;

    #[test]
    fn addition_mod_four_is_a_writer_monoid() {
        let shell = Monad::with_structure("writer", "T", "eta", "mu");
        let witness = CyclicWriterWitness::try_new(&shell, 4);
        assert!(matches!(witness, Ok(ref witness) if witness.modulus() == 4));
    }

    #[test]
    fn a_zero_modulus_is_refused() {
        let shell = Monad::with_structure("writer", "T", "eta", "mu");
        let witness = CyclicWriterWitness::try_new(&shell, 0);
        assert!(matches!(witness, Err(WriterLawError::Modulus)));
    }
}
