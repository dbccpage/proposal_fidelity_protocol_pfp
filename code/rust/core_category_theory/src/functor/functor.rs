//! functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Covariant functor F : C → D as a labeled finite record (shape only).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_8466adc1;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_8466adc1<T> = std::result::Result<T, BoundaryError_8466adc1>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled functor between labeled categories.
///
/// `object_map` / `morphism_map` are diagnostic pair lists, not law certificates.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Functor {
    pub label: String,
    pub source_category: String,
    pub target_category: String,
    /// Object map as (source_object, target_object) pairs.
    pub object_map: Vec<(String, String)>,
    /// Morphism map as (source_morphism, target_morphism) pairs.
    pub morphism_map: Vec<(String, String)>,
    pub notes: Vec<String>,
}

impl Functor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            source_category: String::new(),
            target_category: String::new(),
            object_map: Vec::new(),
            morphism_map: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        source_category: impl Into<String>,
        target_category: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            source_category: source_category.into(),
            target_category: target_category.into(),
            object_map: Vec::new(),
            morphism_map: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_object_map(mut self, object_map: Vec<(String, String)>) -> Self {
        self.object_map = object_map;
        self
    }

    pub fn with_morphism_map(mut self, morphism_map: Vec<(String, String)>) -> Self {
        self.morphism_map = morphism_map;
        self
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
        for (i, (a, b)) in self.object_map.iter().enumerate() {
            if a.is_empty() || b.is_empty() {
                return Err(format!("empty object_map tag at index {i}"));
            }
        }
        for (i, (a, b)) in self.morphism_map.iter().enumerate() {
            if a.is_empty() || b.is_empty() {
                return Err(format!("empty morphism_map tag at index {i}"));
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
        assert!(Functor::between("F", "C", "D").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Functor::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_source() {
        let f = Functor::new("F");
        assert!(f.validate_shell().is_err());
    }

    #[test]
    fn with_maps_ok() {
        let f = Functor::between("F", "C", "D")
            .with_object_map(vec![("a".into(), "Fa".into())])
            .with_morphism_map(vec![("f".into(), "Ff".into())]);
        assert_eq!(f.object_map.len(), 1);
        assert_eq!(f.morphism_map.len(), 1);
        assert!(f.validate_shell().is_ok());
    }

    #[test]
    fn rejects_empty_map_tag() {
        let f = Functor::between("F", "C", "D").with_object_map(vec![("a".into(), "".into())]);
        assert!(f.validate_shell().is_err());
    }
}

/// Identity-on-objects census: a functor that is the identity on a finite
/// carrier sends each object to itself, so the identity-morphism count equals
/// the object count.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FunctorIdentityCount {
    objects: u64,
    identity_morphisms: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum FunctorIdentityError {
    EmptyCarrier,
    IdentityCount { objects: u64, identity_morphisms: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/functor/functor.rs
// Claim: urn:core:crates_rs:core-category-theory:functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FunctorIdentityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FunctorIdentityError {}

impl FunctorIdentityCount {
    pub fn try_new(objects: u64, identity_morphisms: u64) -> Result<Self, FunctorIdentityError> {
        if objects == 0 {
            return Err(FunctorIdentityError::EmptyCarrier);
        }
        if objects != identity_morphisms {
            return Err(FunctorIdentityError::IdentityCount {
                objects,
                identity_morphisms,
            });
        }
        Ok(Self {
            objects,
            identity_morphisms,
        })
    }

    pub fn objects(&self) -> u64 {
        self.objects
    }

    pub fn identity_morphisms(&self) -> u64 {
        self.identity_morphisms
    }
}

#[cfg(test)]
mod functor_identity_witness {
    use super::*;

    #[test]
    fn identity_count_matches_objects() {
        let census = FunctorIdentityCount::try_new(4, 4);
        assert!(census.is_ok());
        if let Ok(census) = census {
            assert_eq!(census.objects(), 4);
            assert_eq!(census.identity_morphisms(), 4);
        }
    }

    #[test]
    fn identity_count_refuses_mismatch() {
        assert!(matches!(
            FunctorIdentityCount::try_new(4, 3),
            Err(FunctorIdentityError::IdentityCount {
                objects: 4,
                identity_morphisms: 3
            })
        ));
        assert!(matches!(
            FunctorIdentityCount::try_new(0, 0),
            Err(FunctorIdentityError::EmptyCarrier)
        ));
    }
}
