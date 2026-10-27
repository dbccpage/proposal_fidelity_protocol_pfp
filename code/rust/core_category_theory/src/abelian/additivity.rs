//! additivity shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Additive-category shape flags (zero object, biproducts). Not a proof of
//! enrichment over Ab or of biproduct existence.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_45c85021;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_45c85021<T> = std::result::Result<T, BoundaryError_45c85021>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for an additive-category claim.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Additivity {
    pub label: String,
    /// Claim that finite biproducts exist (shape flag only).
    pub has_biproducts: bool,
    /// Claim that a zero object exists (shape flag only).
    pub zero_object: bool,
    pub notes: Vec<String>,
}

impl Additivity {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            has_biproducts: false,
            zero_object: false,
            notes: Vec::new(),
        }
    }

    pub fn with_flags(label: impl Into<String>, has_biproducts: bool, zero_object: bool) -> Self {
        Self {
            label: label.into(),
            has_biproducts,
            zero_object,
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
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/abelian/additivity.rs
// Claim: urn:core:crates_rs:core-category-theory:additivity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(Additivity::new("Ab").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Additivity::new("").validate_shell().is_err());
    }

    #[test]
    fn with_flags_sets_bools() {
        let a = Additivity::with_flags("Add", true, true);
        assert!(a.has_biproducts && a.zero_object);
        assert!(a.validate_shell().is_ok());
    }
}

/// Finite biproduct of free abelian groups: dimension adds, and the four projection-inclusion identities hold.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IntegerBiproduct {
    left: usize,
    right: usize,
    dimension: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BiproductError {
    Bound,
    Shape,
    Identity,
}

impl std::fmt::Display for BiproductError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            BiproductError::Bound => write!(formatter, "each summand rank must lie in 1..=8"),
            BiproductError::Shape => write!(formatter, "inclusion or projection table has the wrong length"),
            BiproductError::Identity => write!(formatter, "a biproduct identity p_i i_j = delta_ij failed"),
        }
    }
}

impl std::error::Error for BiproductError {}

fn validate_biproduct_bounds(left: usize, right: usize) -> Result<usize, BiproductError> {
    if left == 0 || right == 0 || left > 8 || right > 8 {
        return Err(BiproductError::Bound);
    }
    left.checked_add(right).ok_or(BiproductError::Bound)
}

fn build_biproduct_projections(
    left: usize,
    dimension: usize,
) -> (Vec<Option<usize>>, Vec<Option<usize>>) {
    let mut project_left = Vec::with_capacity(dimension);
    let mut project_right = Vec::with_capacity(dimension);
    for index in 0..dimension {
        if index < left {
            project_left.push(Some(index));
            project_right.push(None);
        } else {
            project_left.push(None);
            project_right.push(Some(index - left));
        }
    }
    (project_left, project_right)
}

fn verify_inclusion_projections(
    inclusions: &[usize],
    primary: &[Option<usize>],
    secondary: &[Option<usize>],
) -> Result<(), BiproductError> {
    for (index, &image) in inclusions.iter().enumerate() {
        let hit_p = *primary.get(image).ok_or(BiproductError::Identity)?;
        let hit_s = *secondary.get(image).ok_or(BiproductError::Identity)?;
        if hit_p != Some(index) || hit_s.is_some() {
            return Err(BiproductError::Identity);
        }
    }
    Ok(())
}

impl IntegerBiproduct {
    pub fn certify(left: usize, right: usize) -> Result<Self, BiproductError> {
        let dimension = validate_biproduct_bounds(left, right)?;
        let include_left: Vec<usize> = (0..left).collect();
        let include_right: Vec<usize> = (0..right).map(|i| left + i).collect();
        let (project_left, project_right) = build_biproduct_projections(left, dimension);
        let checked = Self::identities(left, right, &include_left, &include_right, &project_left, &project_right)?;
        Ok(Self {
            left,
            right,
            dimension: checked,
        })
    }

    pub fn identities(
        left: usize,
        right: usize,
        include_left: &[usize],
        include_right: &[usize],
        project_left: &[Option<usize>],
        project_right: &[Option<usize>],
    ) -> Result<usize, BiproductError> {
        let dimension = validate_biproduct_bounds(left, right)?;
        if include_left.len() != left || include_right.len() != right {
            return Err(BiproductError::Shape);
        }
        if project_left.len() != dimension || project_right.len() != dimension {
            return Err(BiproductError::Shape);
        }
        verify_inclusion_projections(include_left, project_left, project_right)?;
        verify_inclusion_projections(include_right, project_right, project_left)?;
        Ok(dimension)
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }
}

#[cfg(test)]
mod biproduct_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn ranks_two_and_three_add_and_a_swapped_inclusion_fails() {
        let sum = taken(IntegerBiproduct::certify(2, 3));
        assert_eq!(sum.dimension(), 5);
        let broken = IntegerBiproduct::identities(1, 1, &[1], &[0], &[Some(0), None], &[None, Some(0)]);
        assert!(broken.is_err());
    }
}
