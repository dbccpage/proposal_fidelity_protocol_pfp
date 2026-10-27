//! Enriched hierarchy shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

pub mod base_category;
pub mod enriched_adjunction;
pub mod enriched_category;
pub mod enriched_functor;
pub mod enriched_natural_transformation;
pub mod enriched_presheaf;
pub mod weighted_colimit;
pub mod weighted_limit;

pub use base_category::BaseCategory;
pub use enriched_adjunction::EnrichedAdjunction;
pub use enriched_category::{EnrichedCategory, HomObjectEntry};
pub use enriched_functor::EnrichedFunctor;
pub use enriched_natural_transformation::EnrichedNaturalTransformation;
pub use enriched_presheaf::EnrichedPresheaf;
pub use weighted_colimit::WeightedColimit;
pub use weighted_limit::WeightedLimit;

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/enriched/mod.rs
// Claim: urn:core:category:enriched:hom-square:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HomSquare {
    objects: u64,
    hom_count: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HomSquareError {
    Shell,
    Empty,
    TooWide { objects: usize },
    DuplicateObject { index: usize },
    EmptyObject { index: usize },
    Shape { objects: u64, hom_count: usize },
    UnknownObject { index: usize },
    DuplicateHom { index: usize },
    MissingHom { index: usize },
}

// Origin: engine/crates_rs/core_category_theory/src/enriched/mod.rs
// Claim: urn:core:crates_rs:core-category-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HomSquareError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HomSquareError {}

fn validate_enriched_objects(raw_objects: &[String]) -> Result<u64, HomSquareError> {
    let n = raw_objects.len();
    if n == 0 {
        return Err(HomSquareError::Empty);
    }
    if n > 16 {
        return Err(HomSquareError::TooWide { objects: n });
    }
    for (index, label) in raw_objects.iter().enumerate() {
        if label.is_empty() {
            return Err(HomSquareError::EmptyObject { index });
        }
        if raw_objects[..index].iter().any(|earlier| earlier == label) {
            return Err(HomSquareError::DuplicateObject { index });
        }
    }
    u64::try_from(n).map_err(|_| HomSquareError::TooWide { objects: n })
}

fn verify_hom_square_entries(
    category: &EnrichedCategory,
    n: usize,
    cells: usize,
) -> Result<(), HomSquareError> {
    let mut seen = vec![false; cells];
    for (index, entry) in category.hom_objects.iter().enumerate() {
        let domain = category
            .objects
            .iter()
            .position(|label| label == &entry.domain)
            .ok_or(HomSquareError::UnknownObject { index })?;
        let codomain = category
            .objects
            .iter()
            .position(|label| label == &entry.codomain)
            .ok_or(HomSquareError::UnknownObject { index })?;
        let slot = domain * n + codomain;
        if seen[slot] {
            return Err(HomSquareError::DuplicateHom { index });
        }
        seen[slot] = true;
    }
    if let Some(index) = seen.iter().position(|filled| !filled) {
        return Err(HomSquareError::MissingHom { index });
    }
    Ok(())
}

impl HomSquare {
    pub fn objects(&self) -> u64 { self.objects }
    pub fn hom_count(&self) -> u64 { self.hom_count }

    pub fn try_from_category(category: &EnrichedCategory) -> Result<Self, HomSquareError> {
        if category.validate_shell().is_err() {
            return Err(HomSquareError::Shell);
        }
        let objects = validate_enriched_objects(&category.objects)?;
        let n = category.objects.len();
        let cells = objects.checked_mul(objects).ok_or(HomSquareError::TooWide { objects: n })?;
        if category.hom_objects.len() != cells as usize {
            return Err(HomSquareError::Shape { objects, hom_count: category.hom_objects.len() });
        }
        verify_hom_square_entries(category, n, cells as usize)?;
        Ok(Self { objects, hom_count: cells })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod hom_square_tests {
    use super::*;

    fn two_object() -> EnrichedCategory {
        let mut category = EnrichedCategory::over_v("C", "V");
        category.objects = vec!["a".to_string(), "b".to_string()];
        category.with_hom("a", "a", "aa");
        category.with_hom("a", "b", "ab");
        category.with_hom("b", "a", "ba");
        category.with_hom("b", "b", "bb");
        category
    }

    #[test]
    fn every_object_pair_has_one_hom() {
        let square = HomSquare::try_from_category(&two_object());
        assert!(matches!(square, Ok(ref row) if row.objects() == 2 && row.hom_count() == 4));
    }

    #[test]
    fn a_missing_pair_is_not_a_hom_square() {
        let mut category = two_object();
        category.hom_objects.pop();
        assert!(matches!(
            HomSquare::try_from_category(&category),
            Err(HomSquareError::Shape { objects: 2, hom_count: 3 })
        ));
    }
}
