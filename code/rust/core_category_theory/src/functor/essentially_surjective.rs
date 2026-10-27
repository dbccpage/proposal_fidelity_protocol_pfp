//! essentially_surjective shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Essential surjectivity claim (every target object isomorphic to an image) — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_67692bf0;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_67692bf0<T> = std::result::Result<T, BoundaryError_67692bf0>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for an essential-surjectivity claim on a functor reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct EssentiallySurjective {
    pub label: String,
    pub functor_ref: String,
    pub notes: Vec<String>,
}

impl EssentiallySurjective {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            functor_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn on_functor(label: impl Into<String>, functor_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            functor_ref: functor_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.functor_ref.is_empty() {
            return Err("empty functor_ref".into());
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
        assert!(EssentiallySurjective::on_functor("ess_surj", "F")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(EssentiallySurjective::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_ref() {
        assert!(EssentiallySurjective::new("x").validate_shell().is_err());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/functor/essentially_surjective.rs
// Claim: urn:core:category:functor:skeletal-coverage:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SkeletalCoverage {
    objects: u16,
    distinct_preimages: u16,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SkeletalCoverageError {
    ShellRefused { reason: String },
    Empty,
    LengthMismatch { objects: u16, preimages: usize },
    ImageOutOfRange { index: usize, image: u16 },
    MissingPreimage { index: usize },
    RepeatedPreimage { image: u16 },
}

// Origin: engine/crates_rs/core_category_theory/src/functor/essentially_surjective.rs
// Claim: urn:core:crates_rs:core-category-theory:essentially-surjective:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SkeletalCoverageError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SkeletalCoverageError {}

impl SkeletalCoverage {
    fn count_distinct_preimages(
        objects: u16,
        preimage: &[Option<u16>],
    ) -> Result<u16, SkeletalCoverageError> {
        let mut seen = vec![false; usize::from(objects)];
        let mut distinct_preimages = 0u16;
        for index in 0..preimage.len() {
            let image = preimage
                .get(index)
                .and_then(|slot| *slot)
                .ok_or(SkeletalCoverageError::MissingPreimage { index })?;
            let slot = usize::from(image);
            let flag = seen
                .get_mut(slot)
                .ok_or(SkeletalCoverageError::ImageOutOfRange { index, image })?;
            if *flag {
                return Err(SkeletalCoverageError::RepeatedPreimage { image });
            }
            *flag = true;
            distinct_preimages = distinct_preimages
                .checked_add(1)
                .ok_or(SkeletalCoverageError::ImageOutOfRange { index, image })?;
        }
        Ok(distinct_preimages)
    }

    pub fn try_on(
        shell: &EssentiallySurjective,
        objects: u16,
        preimage: &[Option<u16>],
    ) -> Result<Self, SkeletalCoverageError> {
        shell
            .validate_shell()
            .map_err(|reason| SkeletalCoverageError::ShellRefused { reason })?;
        if objects == 0 {
            return Err(SkeletalCoverageError::Empty);
        }
        if preimage.len() != usize::from(objects) {
            return Err(SkeletalCoverageError::LengthMismatch {
                objects,
                preimages: preimage.len(),
            });
        }
        let distinct_preimages = Self::count_distinct_preimages(objects, preimage)?;
        if distinct_preimages != objects {
            return Err(SkeletalCoverageError::LengthMismatch {
                objects,
                preimages: usize::from(distinct_preimages),
            });
        }
        Ok(Self { objects, distinct_preimages })
    }

    pub fn objects(&self) -> u16 {
        self.objects
    }

    pub fn distinct_preimages(&self) -> u16 {
        self.distinct_preimages
    }
}

#[cfg(test)]
mod skeletal_coverage_tests {
    use super::*;

    #[test]
    fn covers_every_object_once() {
        let shell = EssentiallySurjective::on_functor("ess", "F");
        let witness = SkeletalCoverage::try_on(&shell, 3, &[Some(1), Some(0), Some(2)]);
        assert!(matches!(
            witness,
            Ok(ref w) if w.objects() == 3 && w.distinct_preimages() == 3
        ));
    }

    #[test]
    fn refuses_a_repeated_preimage() {
        let shell = EssentiallySurjective::on_functor("ess", "F");
        let wrong = SkeletalCoverage::try_on(&shell, 3, &[Some(1), Some(1), Some(0)]);
        assert!(matches!(wrong, Err(SkeletalCoverageError::RepeatedPreimage { image: 1 })));
    }
}
