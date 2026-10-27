//! vertical_composition shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Vertical composition of natural transformations (β ∘ α) — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_9380f2ba;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_9380f2ba<T> = std::result::Result<T, BoundaryError_9380f2ba>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a vertical composition claim on nat-trans refs.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerticalComposition {
    pub label: String,
    /// Outer (later) natural transformation.
    pub outer_nat_trans_ref: String,
    /// Inner (earlier) natural transformation.
    pub inner_nat_trans_ref: String,
    /// Optional result nat-trans label.
    pub result_ref: String,
    pub notes: Vec<String>,
}

impl VerticalComposition {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            outer_nat_trans_ref: String::new(),
            inner_nat_trans_ref: String::new(),
            result_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of(
        label: impl Into<String>,
        outer_nat_trans_ref: impl Into<String>,
        inner_nat_trans_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            outer_nat_trans_ref: outer_nat_trans_ref.into(),
            inner_nat_trans_ref: inner_nat_trans_ref.into(),
            result_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.outer_nat_trans_ref.is_empty() {
            return Err("empty outer_nat_trans_ref".into());
        }
        if self.inner_nat_trans_ref.is_empty() {
            return Err("empty inner_nat_trans_ref".into());
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
        assert!(VerticalComposition::of("vcomp", "beta", "alpha")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(VerticalComposition::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_refs() {
        assert!(VerticalComposition::new("v").validate_shell().is_err());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum VerticalLawError {
    Shell,
    Shape,
    NotBijective,
    Associativity { point: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/functor/vertical_composition.rs
// Claim: urn:core:crates_rs:core-category-theory:vertical-composition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for VerticalLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for VerticalLawError {}

/// Associativity of composition for three bijections on a finite ordinal.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerticalAssocWitness {
    objects: usize,
}

fn compose_bijections(outer: &[u32], inner: &[u32]) -> Result<Vec<u32>, VerticalLawError> {
    if outer.len() != inner.len() || outer.is_empty() {
        return Err(VerticalLawError::Shape);
    }
    let mut image = Vec::with_capacity(inner.len());
    for (point, &inner_image) in inner.iter().enumerate() {
        let index = usize::try_from(inner_image).map_err(|_| VerticalLawError::Shape)?;
        let value = *outer.get(index).ok_or(VerticalLawError::Shape)?;
        if usize::try_from(value).map_err(|_| VerticalLawError::Shape)? >= outer.len() {
            return Err(VerticalLawError::Shape);
        }
        let _ = point;
        image.push(value);
    }
    Ok(image)
}

fn require_bijection(arrows: &[u32]) -> Result<(), VerticalLawError> {
    let mut seen = vec![false; arrows.len()];
    for &image in arrows {
        let index = usize::try_from(image).map_err(|_| VerticalLawError::NotBijective)?;
        let slot = seen.get_mut(index).ok_or(VerticalLawError::NotBijective)?;
        if *slot {
            return Err(VerticalLawError::NotBijective);
        }
        *slot = true;
    }
    Ok(())
}

impl VerticalAssocWitness {
    fn check_associative(left: &[u32], right: &[u32]) -> Result<(), VerticalLawError> {
        for (point, (lhs, rhs)) in left.iter().zip(right.iter()).enumerate() {
            if lhs != rhs {
                return Err(VerticalLawError::Associativity { point });
            }
        }
        Ok(())
    }

    pub fn try_new(shell: &VerticalComposition, first: &[u32], second: &[u32], third: &[u32]) -> Result<Self, VerticalLawError> {
        if shell.validate_shell().is_err() {
            return Err(VerticalLawError::Shell);
        }
        require_bijection(first)?;
        require_bijection(second)?;
        require_bijection(third)?;
        let left_inner = compose_bijections(second, first)?;
        let left = compose_bijections(third, &left_inner)?;
        let right_inner = compose_bijections(third, second)?;
        let right = compose_bijections(&right_inner, first)?;
        Self::check_associative(&left, &right)?;
        Ok(Self { objects: first.len() })
    }

    pub fn objects(&self) -> usize { self.objects }
}

#[cfg(test)]
mod vertical_law_tests {
    use super::*;

    #[test]
    fn three_bijections_associate() {
        let shell = VerticalComposition::of("vcomp", "beta", "alpha");
        let witness = VerticalAssocWitness::try_new(&shell, &[1, 2, 0], &[0, 2, 1], &[2, 0, 1]);
        assert!(matches!(witness, Ok(ref witness) if witness.objects() == 3));
    }

    #[test]
    fn a_collapsed_arrow_is_not_a_bijection() {
        let shell = VerticalComposition::of("vcomp", "beta", "alpha");
        let witness = VerticalAssocWitness::try_new(&shell, &[0, 0, 1], &[0, 1, 2], &[0, 1, 2]);
        assert!(matches!(witness, Err(VerticalLawError::NotBijective)));
    }
}
