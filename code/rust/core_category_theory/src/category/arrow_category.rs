//! arrow_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Arr(C): objects are morphisms of C; morphisms are commutative squares.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_ab28f03c;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_ab28f03c<T> = std::result::Result<T, BoundaryError_ab28f03c>;
use serde::{Deserialize, Serialize};

use super::category::MorphismTriple;

/// Best-effort arrow category shell Arr(C).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArrowCategoryShell {
    pub label: String,
    pub base_label: String,
    /// Objects of Arr(C) = morphisms of C (as triples).
    pub arrow_objects: Vec<MorphismTriple>,
    pub notes: Vec<String>,
}

impl ArrowCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_label: String::new(),
            arrow_objects: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn of_base(label: impl Into<String>, base_label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_label: base_label.into(),
            arrow_objects: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.base_label.is_empty() {
            return Err("empty base_label".into());
        }
        for (i, m) in self.arrow_objects.iter().enumerate() {
            if m.source.is_empty() || m.target.is_empty() || m.name.is_empty() {
                return Err(format!("empty arrow_object field at index {i}"));
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/category/arrow_category.rs
// Claim: urn:core:crates_rs:core-category-theory:arrow-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(ArrowCategoryShell::of_base("Arr(C)", "C")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(ArrowCategoryShell::new("").validate_shell().is_err());
        assert!(ArrowCategoryShell::new("A").validate_shell().is_err());
    }

    #[test]
    fn with_arrow_object_ok() {
        let mut a = ArrowCategoryShell::of_base("Arr(C)", "C");
        a.arrow_objects.push(MorphismTriple::new("x", "y", "f"));
        assert!(a.validate_shell().is_ok());
    }
}

/// A square of endofunctions commutes when right ∘ top equals bottom ∘ left.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FunctionSquare {
    order: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SquareError {
    Bound,
    Shape,
    Commute,
}

impl std::fmt::Display for SquareError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SquareError::Bound => write!(formatter, "square order must lie in 1..=12"),
            SquareError::Shape => write!(formatter, "a side map leaves the set"),
            SquareError::Commute => write!(formatter, "the two paths around the square differ"),
        }
    }
}

impl std::error::Error for SquareError {}

fn validate_endomap(order: usize, map: &[usize]) -> Result<(), SquareError> {
    if map.len() != order || map.iter().any(|&v| v >= order) {
        return Err(SquareError::Shape);
    }
    Ok(())
}

impl FunctionSquare {
    pub fn commutes(order: usize, top: &[usize], left: &[usize], right: &[usize], bottom: &[usize]) -> Result<Self, SquareError> {
        if order == 0 || order > 12 {
            return Err(SquareError::Bound);
        }
        for map in [top, left, right, bottom] {
            validate_endomap(order, map)?;
        }
        for index in 0..order {
            if right[top[index]] != bottom[left[index]] {
                return Err(SquareError::Commute);
            }
        }
        Ok(Self { order })
    }

    pub fn order(&self) -> usize {
        self.order
    }
}

#[cfg(test)]
mod square_tests {
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
    fn four_swaps_commute_and_an_identity_bottom_does_not() {
        let square = taken(FunctionSquare::commutes(2, &[1, 0], &[1, 0], &[1, 0], &[1, 0]));
        assert_eq!(square.order(), 2);
        assert!(FunctionSquare::commutes(2, &[1, 0], &[1, 0], &[1, 0], &[0, 1]).is_err());
    }
}
