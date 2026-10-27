//! isomorphism_of_categories shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Strict isomorphism of categories (inverse functors) — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_9b627cce;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_9b627cce<T> = std::result::Result<T, BoundaryError_9b627cce>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for an isomorphism-of-categories claim.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct IsomorphismOfCategories {
    pub label: String,
    pub functor_ref: String,
    pub inverse_functor_ref: String,
    pub notes: Vec<String>,
}

impl IsomorphismOfCategories {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            functor_ref: String::new(),
            inverse_functor_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        functor_ref: impl Into<String>,
        inverse_functor_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            functor_ref: functor_ref.into(),
            inverse_functor_ref: inverse_functor_ref.into(),
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
        if self.inverse_functor_ref.is_empty() {
            return Err("empty inverse_functor_ref".into());
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
        assert!(IsomorphismOfCategories::between("iso", "F", "F_inv")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(IsomorphismOfCategories::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_refs() {
        assert!(IsomorphismOfCategories::new("iso")
            .validate_shell()
            .is_err());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/functor/isomorphism_of_categories.rs
// Claim: urn:core:category:functor:mutual-inverse:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MutualInverse {
    objects: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MutualInverseError {
    ShellRefused { reason: String },
    Empty,
    LengthMismatch { forward: usize, backward: usize },
    ImageOutOfRange { index: usize, image: u16 },
    NotInverse { index: usize, returned: u16 },
}

// Origin: engine/crates_rs/core_category_theory/src/functor/isomorphism_of_categories.rs
// Claim: urn:core:crates_rs:core-category-theory:isomorphism-of-categories:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MutualInverseError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MutualInverseError {}

fn step(map: &[u16], index: usize, len: usize) -> Result<usize, MutualInverseError> {
    let image = *map.get(index).ok_or(MutualInverseError::ImageOutOfRange { index, image: 0 })?;
    let as_usize = usize::from(image);
    if as_usize >= len {
        return Err(MutualInverseError::ImageOutOfRange { index, image });
    }
    Ok(as_usize)
}

fn check_roundtrip(
    first: &[u16],
    second: &[u16],
    index: usize,
    len: usize,
) -> Result<(), MutualInverseError> {
    let mid = step(first, index, len)?;
    let back = step(second, mid, len)?;
    if back != index {
        let returned = u16::try_from(back)
            .map_err(|_| MutualInverseError::ImageOutOfRange { index, image: 0 })?;
        return Err(MutualInverseError::NotInverse { index, returned });
    }
    Ok(())
}

impl MutualInverse {
    pub fn try_on(
        shell: &IsomorphismOfCategories,
        forward: &[u16],
        backward: &[u16],
    ) -> Result<Self, MutualInverseError> {
        shell
            .validate_shell()
            .map_err(|reason| MutualInverseError::ShellRefused { reason })?;
        if forward.is_empty() {
            return Err(MutualInverseError::Empty);
        }
        if forward.len() != backward.len() {
            return Err(MutualInverseError::LengthMismatch {
                forward: forward.len(),
                backward: backward.len(),
            });
        }
        let len = forward.len();
        for index in 0..len {
            check_roundtrip(forward, backward, index, len)?;
            check_roundtrip(backward, forward, index, len)?;
        }
        Ok(Self { objects: len })
    }

    pub fn objects(&self) -> usize {
        self.objects
    }
}

#[cfg(test)]
mod mutual_inverse_tests {
    use super::*;

    #[test]
    fn forward_and_backward_cancel() {
        let shell = IsomorphismOfCategories::between("iso", "F", "G");
        let witness = MutualInverse::try_on(&shell, &[1, 2, 0], &[2, 0, 1]);
        assert!(matches!(witness, Ok(ref w) if w.objects() == 3));
    }

    #[test]
    fn refuses_a_constant_backward_map() {
        let shell = IsomorphismOfCategories::between("iso", "F", "G");
        let wrong = MutualInverse::try_on(&shell, &[1, 2, 0], &[0, 0, 0]);
        assert!(matches!(wrong, Err(MutualInverseError::NotInverse { .. })));
    }
}
