//! functor_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Functor category [C, D] (objects = functors, morphisms = nat-trans) — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_4ecc0ffe;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_4ecc0ffe<T> = std::result::Result<T, BoundaryError_4ecc0ffe>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled functor category [source, target].
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FunctorCategory {
    pub label: String,
    pub source_category: String,
    pub target_category: String,
    pub notes: Vec<String>,
}

impl FunctorCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            source_category: String::new(),
            target_category: String::new(),
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
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(FunctorCategory::between("[C,D]", "C", "D")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(FunctorCategory::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_categories() {
        assert!(FunctorCategory::new("x").validate_shell().is_err());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NaturalityError {
    Shell,
    Shape,
    Range { index: usize },
    Naturality { point: usize },
}

// Origin: engine/crates_rs/core_category_theory/src/functor/functor_category.rs
// Claim: urn:core:crates_rs:core-category-theory:functor-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for NaturalityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for NaturalityError {}

/// Naturality of one component family against a parallel pair of total functions.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NaturalitySquareWitness {
    objects: usize,
}

impl NaturalitySquareWitness {
    fn in_bounds(val: u32, objects: usize) -> bool {
        usize::try_from(val).map_or(false, |v| v < objects)
    }

    fn check_ranges(
        source_arrow: &[u32],
        target_arrow: &[u32],
        component: &[u32],
        objects: usize,
    ) -> Result<(), NaturalityError> {
        for (index, ((&source, &target), &alpha)) in source_arrow
            .iter()
            .zip(target_arrow.iter())
            .zip(component.iter())
            .enumerate()
        {
            if !Self::in_bounds(source, objects)
                || !Self::in_bounds(target, objects)
                || !Self::in_bounds(alpha, objects)
            {
                return Err(NaturalityError::Range { index });
            }
        }
        Ok(())
    }

    fn step_arrow(arrow: &[u32], index: usize) -> Result<usize, NaturalityError> {
        let val = *arrow.get(index).ok_or(NaturalityError::Shape)?;
        usize::try_from(val).map_err(|_| NaturalityError::Shape)
    }

    fn check_naturality_point(
        source_arrow: &[u32],
        target_arrow: &[u32],
        component: &[u32],
        point: usize,
    ) -> Result<(), NaturalityError> {
        let image = Self::step_arrow(source_arrow, point)?;
        let left = *component.get(image).ok_or(NaturalityError::Shape)?;
        let via = Self::step_arrow(component, point)?;
        let right = *target_arrow.get(via).ok_or(NaturalityError::Shape)?;
        if left != right {
            return Err(NaturalityError::Naturality { point });
        }
        Ok(())
    }

    pub fn try_new(
        category: &FunctorCategory,
        source_arrow: &[u32],
        target_arrow: &[u32],
        component: &[u32],
    ) -> Result<Self, NaturalityError> {
        if category.validate_shell().is_err() {
            return Err(NaturalityError::Shell);
        }
        let objects = source_arrow.len();
        if objects == 0 || target_arrow.len() != objects || component.len() != objects {
            return Err(NaturalityError::Shape);
        }
        Self::check_ranges(source_arrow, target_arrow, component, objects)?;
        for point in 0..objects {
            Self::check_naturality_point(source_arrow, target_arrow, component, point)?;
        }
        Ok(Self { objects })
    }

    pub fn objects(&self) -> usize { self.objects }
}

#[cfg(test)]
mod naturality_tests {
    use super::*;

    #[test]
    fn identity_components_commute() {
        let category = FunctorCategory::between("fun", "C", "D");
        let witness = NaturalitySquareWitness::try_new(&category, &[0, 1], &[0, 1], &[0, 1]);
        assert!(matches!(witness, Ok(ref witness) if witness.objects() == 2));
    }

    #[test]
    fn a_twisted_source_arrow_breaks_naturality() {
        let category = FunctorCategory::between("fun", "C", "D");
        let witness = NaturalitySquareWitness::try_new(&category, &[1, 0], &[0, 1], &[0, 1]);
        assert!(matches!(witness, Err(NaturalityError::Naturality { point: 0 })));
    }
}
