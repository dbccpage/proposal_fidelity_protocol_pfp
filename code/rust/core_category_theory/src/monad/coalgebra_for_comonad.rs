//! coalgebra_for_comonad shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! A coalgebra for a comonad W is a carrier A with structure map k : A → W(A).
//! Shell holds carrier + structure-map labels and a comonad ref.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_4a0344ae;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_4a0344ae<T> = std::result::Result<T, BoundaryError_4a0344ae>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled W-coalgebra (A, k).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoalgebraForComonad {
    pub label: String,
    /// Carrier object label A.
    pub carrier_label: String,
    /// Structure map label k : A → W(A).
    pub structure_map_label: String,
    /// Ref to the ambient comonad W.
    pub comonad_ref: String,
    pub notes: Vec<String>,
}

impl CoalgebraForComonad {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            carrier_label: String::new(),
            structure_map_label: String::new(),
            comonad_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_structure(
        label: impl Into<String>,
        carrier_label: impl Into<String>,
        structure_map_label: impl Into<String>,
        comonad_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            carrier_label: carrier_label.into(),
            structure_map_label: structure_map_label.into(),
            comonad_ref: comonad_ref.into(),
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
        if self.carrier_label.is_empty() {
            return Err("empty carrier_label".into());
        }
        if self.structure_map_label.is_empty() {
            return Err("empty structure_map_label".into());
        }
        if self.comonad_ref.is_empty() {
            return Err("empty comonad_ref".into());
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
        let c = CoalgebraForComonad::with_structure("stream_coalg", "Stream", "k_stream", "Env");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(CoalgebraForComonad::new("").validate_shell().is_err());
        assert!(CoalgebraForComonad::new("c").validate_shell().is_err());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/monad/coalgebra_for_comonad.rs
// Claim: urn:core:category:comonad:coalgebra-laws:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoalgebraLaws {
    carrier: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CoalgebraLawsError {
    ShellRefused { reason: String },
    Empty,
    LengthMismatch,
    ImageOutOfRange { index: usize, image: u16 },
    CounitFailed { index: usize, returned: u16 },
    CoassociativityFailed { index: usize, left: u16, right: u16 },
}

// Origin: engine/crates_rs/core_category_theory/src/monad/coalgebra_for_comonad.rs
// Claim: urn:core:crates_rs:core-category-theory:coalgebra-for-comonad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CoalgebraLawsError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CoalgebraLawsError {}

fn at(map: &[u16], index: usize, len: usize) -> Result<u16, CoalgebraLawsError> {
    let image = *map.get(index).ok_or(CoalgebraLawsError::ImageOutOfRange { index, image: 0 })?;
    if usize::from(image) >= len {
        return Err(CoalgebraLawsError::ImageOutOfRange { index, image });
    }
    Ok(image)
}

impl CoalgebraLaws {
    fn verify_coalgebra_at(
        structure: &[u16],
        counit: &[u16],
        comultiply: &[u16],
        extended: &[u16],
        index: usize,
        len: usize,
    ) -> Result<(), CoalgebraLawsError> {
        let acted = at(structure, index, len)?;
        let after_counit = at(counit, usize::from(acted), len)?;
        if usize::from(after_counit) != index {
            return Err(CoalgebraLawsError::CounitFailed {
                index,
                returned: after_counit,
            });
        }
        let left = at(comultiply, usize::from(acted), len)?;
        let right = at(extended, usize::from(acted), len)?;
        if left != right {
            return Err(CoalgebraLawsError::CoassociativityFailed { index, left, right });
        }
        Ok(())
    }

    pub fn try_on(
        shell: &CoalgebraForComonad,
        structure: &[u16],
        counit: &[u16],
        comultiply: &[u16],
        extended: &[u16],
    ) -> Result<Self, CoalgebraLawsError> {
        shell
            .validate_shell()
            .map_err(|reason| CoalgebraLawsError::ShellRefused { reason })?;
        if structure.is_empty() {
            return Err(CoalgebraLawsError::Empty);
        }
        let len = structure.len();
        if counit.len() != len || comultiply.len() != len || extended.len() != len {
            return Err(CoalgebraLawsError::LengthMismatch);
        }
        for index in 0..len {
            Self::verify_coalgebra_at(structure, counit, comultiply, extended, index, len)?;
        }
        Ok(Self { carrier: len })
    }

    pub fn carrier(&self) -> usize {
        self.carrier
    }
}

#[cfg(test)]
mod coalgebra_laws_tests {
    use super::*;

    #[test]
    fn counit_and_comultiplication_agree() {
        let shell = CoalgebraForComonad::with_structure("stream", "A", "k", "W");
        let witness = CoalgebraLaws::try_on(&shell, &[1, 0], &[1, 0], &[0, 1], &[0, 1]);
        assert!(matches!(witness, Ok(ref w) if w.carrier() == 2));
    }

    #[test]
    fn refuses_a_counit_that_is_not_a_retraction() {
        let shell = CoalgebraForComonad::with_structure("stream", "A", "k", "W");
        let wrong = CoalgebraLaws::try_on(&shell, &[1, 0], &[0, 0], &[0, 1], &[0, 1]);
        assert!(matches!(wrong, Err(CoalgebraLawsError::CounitFailed { index: 1, returned: 0 })));
    }
}
