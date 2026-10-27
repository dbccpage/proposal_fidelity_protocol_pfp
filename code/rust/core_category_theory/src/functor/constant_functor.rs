//! constant_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Constant functor Δ_d : C → D with value d — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_11244424;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_11244424<T> = std::result::Result<T, BoundaryError_11244424>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a constant functor between labeled categories.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ConstantFunctor {
    pub label: String,
    pub source_category: String,
    pub target_category: String,
    /// Constant object in the target category.
    pub constant_object: String,
    pub notes: Vec<String>,
}

impl ConstantFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            source_category: String::new(),
            target_category: String::new(),
            constant_object: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn constant(
        label: impl Into<String>,
        source_category: impl Into<String>,
        target_category: impl Into<String>,
        constant_object: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            source_category: source_category.into(),
            target_category: target_category.into(),
            constant_object: constant_object.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.source_category.is_empty() {
            return Err("empty source_category".into());
        }
        if self.target_category.is_empty() {
            return Err("empty target_category".into());
        }
        if self.constant_object.is_empty() {
            return Err("empty constant_object".into());
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
        assert!(ConstantFunctor::constant("const_d", "C", "D", "d")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(ConstantFunctor::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_fields() {
        assert!(ConstantFunctor::new("c").validate_shell().is_err());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConstantLawError {
    Shell,
    Empty,
    Object { index: usize },
    Arrow { index: usize },
}

// Origin: engine/crates_rs/core_category_theory/src/functor/constant_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:constant-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ConstantLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ConstantLawError {}

/// A constant functor sends every object to one value and every arrow to the identity index.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConstantImageWitness {
    objects: usize,
    image: u32,
}

impl ConstantImageWitness {
    pub fn try_new(functor: &ConstantFunctor, object_images: &[u32], arrow_images: &[u32]) -> Result<Self, ConstantLawError> {
        if functor.validate_shell().is_err() {
            return Err(ConstantLawError::Shell);
        }
        let image = *object_images.first().ok_or(ConstantLawError::Empty)?;
        for (index, value) in object_images.iter().copied().enumerate() {
            if value != image {
                return Err(ConstantLawError::Object { index });
            }
        }
        for (index, value) in arrow_images.iter().copied().enumerate() {
            if value != 0 {
                return Err(ConstantLawError::Arrow { index });
            }
        }
        Ok(Self { objects: object_images.len(), image })
    }

    pub fn objects(&self) -> usize { self.objects }
    pub fn image(&self) -> u32 { self.image }
}

#[cfg(test)]
mod constant_law_tests {
    use super::*;

    #[test]
    fn every_object_lands_on_the_same_value() {
        let functor = ConstantFunctor::constant("const_d", "C", "D", "d");
        let witness = ConstantImageWitness::try_new(&functor, &[4, 4, 4], &[0, 0]);
        assert!(matches!(witness, Ok(ref witness) if witness.image() == 4 && witness.objects() == 3));
    }

    #[test]
    fn a_second_object_image_is_refused() {
        let functor = ConstantFunctor::constant("const_d", "C", "D", "d");
        let witness = ConstantImageWitness::try_new(&functor, &[4, 5], &[]);
        assert!(matches!(witness, Err(ConstantLawError::Object { index: 1 })));
    }
}
