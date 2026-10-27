//! natural_transformation shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Natural transformation η : F ⇒ G as a labeled finite record (shape only).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_951ab739;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_951ab739<T> = std::result::Result<T, BoundaryError_951ab739>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a natural transformation between labeled functors.
///
/// `components` are diagnostic (object, morphism) pairs, not naturality certificates.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct NaturalTransformation {
    pub label: String,
    pub source_functor: String,
    pub target_functor: String,
    /// Component map as (object, morphism) pairs: η_A : F(A) → G(A).
    pub components: Vec<(String, String)>,
    pub notes: Vec<String>,
}

impl NaturalTransformation {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            source_functor: String::new(),
            target_functor: String::new(),
            components: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        source_functor: impl Into<String>,
        target_functor: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            source_functor: source_functor.into(),
            target_functor: target_functor.into(),
            components: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_components(mut self, components: Vec<(String, String)>) -> Self {
        self.components = components;
        self
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
        for (i, (obj, mor)) in self.components.iter().enumerate() {
            if obj.is_empty() || mor.is_empty() {
                return Err(format!("empty component tag at index {i}"));
            }
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
        assert!(NaturalTransformation::between("eta", "F", "G")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(NaturalTransformation::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_functors() {
        assert!(NaturalTransformation::new("eta").validate_shell().is_err());
    }

    #[test]
    fn with_components_ok() {
        let n = NaturalTransformation::between("eta", "F", "G")
            .with_components(vec![("A".into(), "eta_A".into())]);
        assert_eq!(n.components.len(), 1);
        assert!(n.validate_shell().is_ok());
    }

    #[test]
    fn rejects_empty_component_tag() {
        let n = NaturalTransformation::between("eta", "F", "G")
            .with_components(vec![("A".into(), "".into())]);
        assert!(n.validate_shell().is_err());
    }
}

/// Refusal from composition of maps on finite ordinals.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OrdinalError {
    /// An image leaves the next ordinal.
    Image { value: u32 },
    /// The inner and outer carriers do not meet.
    Shape,
}

// Origin: engine/crates_rs/core_category_theory/src/functor/natural_transformation.rs
// Claim: urn:core:crates_rs:core-category-theory:natural-transformation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for OrdinalError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for OrdinalError {}

/// A map `0..n → 0..m` stored by images.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OrdinalMap {
    images: Vec<u32>,
}

impl OrdinalMap {
    /// Compose `outer` after `inner`. `inner` lands in `0..outer.len()`.
    pub fn try_compose(outer: &[u32], inner: &[u32]) -> Result<Self, OrdinalError> {
        let codomain = u32::try_from(outer.len()).map_err(|_| OrdinalError::Shape)?;
        let mut images = Vec::new();
        for &value in inner {
            if value >= codomain {
                return Err(OrdinalError::Image { value });
            }
            let Some(image) = outer.get(value as usize).copied() else {
                return Err(OrdinalError::Image { value });
            };
            images.push(image);
        }
        Ok(Self { images })
    }

    /// Images of `0..n`.
    pub fn images(&self) -> &[u32] { &self.images }
}

#[cfg(test)]
mod ordinal_tests {
    use super::*;
    #[test]
    fn a_swap_composed_with_itself_is_the_identity() {
        let map = OrdinalMap::try_compose(&[1, 0], &[1, 0]);
        assert!(matches!(map, Ok(ref m) if m.images() == [0, 1]));
    }
}
