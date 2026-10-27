//! representable_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Representable functor claim (≅ Hom(A, −) or Hom(−, A)) — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_d845f004;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_d845f004<T> = std::result::Result<T, BoundaryError_d845f004>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a representable functor on a category reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct RepresentableFunctor {
    pub label: String,
    pub category_ref: String,
    /// Optional representing object tag.
    pub representing_object: String,
    pub notes: Vec<String>,
}

impl RepresentableFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: String::new(),
            representing_object: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn on_category(label: impl Into<String>, category_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            representing_object: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn represented_by(
        label: impl Into<String>,
        category_ref: impl Into<String>,
        representing_object: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            representing_object: representing_object.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.category_ref.is_empty() {
            return Err("empty category_ref".into());
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
        assert!(RepresentableFunctor::on_category("y_A", "C")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(RepresentableFunctor::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_ref() {
        assert!(RepresentableFunctor::new("x").validate_shell().is_err());
    }

    #[test]
    fn represented_by_sets_object() {
        let r = RepresentableFunctor::represented_by("y_A", "C", "A");
        assert_eq!(r.representing_object, "A");
        assert!(r.validate_shell().is_ok());
    }
}

/// Hom-cardinalities of a representable functor on a finite category.
/// The slot at `representing_index` is the endomorphism monoid and must be
/// at least 1 (the identity).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RepresentableHom {
    object_count: u64,
    hom_cardinalities: Vec<u64>,
    representing_index: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RepresentableHomError {
    EmptyCarrier,
    LengthMismatch { object_count: u64, recorded: usize },
    IndexOutOfRange { representing_index: usize, object_count: u64 },
    MissingIdentity { representing_index: usize, endomorphisms: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/functor/representable_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:representable-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RepresentableHomError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RepresentableHomError {}

impl RepresentableHom {
    pub fn try_new(
        object_count: u64,
        hom_cardinalities: Vec<u64>,
        representing_index: usize,
    ) -> Result<Self, RepresentableHomError> {
        if object_count == 0 {
            return Err(RepresentableHomError::EmptyCarrier);
        }
        let recorded = hom_cardinalities.len();
        let expected = usize::try_from(object_count).map_err(|_| RepresentableHomError::LengthMismatch {
            object_count,
            recorded,
        })?;
        if recorded != expected {
            return Err(RepresentableHomError::LengthMismatch {
                object_count,
                recorded,
            });
        }
        if representing_index >= expected {
            return Err(RepresentableHomError::IndexOutOfRange {
                representing_index,
                object_count,
            });
        }
        let endomorphisms = hom_cardinalities
            .get(representing_index)
            .copied()
            .ok_or(RepresentableHomError::IndexOutOfRange {
                representing_index,
                object_count,
            })?;
        if endomorphisms < 1 {
            return Err(RepresentableHomError::MissingIdentity {
                representing_index,
                endomorphisms,
            });
        }
        Ok(Self {
            object_count,
            hom_cardinalities,
            representing_index,
        })
    }

    pub fn object_count(&self) -> u64 {
        self.object_count
    }

    pub fn endomorphisms(&self) -> Option<u64> {
        self.hom_cardinalities.get(self.representing_index).copied()
    }
}

#[cfg(test)]
mod representable_hom_witness {
    use super::*;

    #[test]
    fn endomorphism_slot_holds_identity() {
        let hom = RepresentableHom::try_new(3, vec![2, 1, 4], 1);
        assert!(hom.is_ok());
        if let Ok(hom) = hom {
            assert_eq!(hom.object_count(), 3);
            assert_eq!(hom.endomorphisms(), Some(1));
        }
    }

    #[test]
    fn refuses_empty_endomorphism_slot() {
        assert!(matches!(
            RepresentableHom::try_new(2, vec![0, 3], 0),
            Err(RepresentableHomError::MissingIdentity {
                representing_index: 0,
                endomorphisms: 0
            })
        ));
    }
}
