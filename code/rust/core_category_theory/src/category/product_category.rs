//! product_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! C × D: objects are pairs (c, d); morphisms are pairs of morphisms.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_eafa75d5;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_eafa75d5<T> = std::result::Result<T, BoundaryError_eafa75d5>;
use serde::{Deserialize, Serialize};

/// Best-effort product category shell C × D.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProductCategoryShell {
    pub label: String,
    pub left_factor_label: String,
    pub right_factor_label: String,
    /// Optional object-pair tags as "c|d" (diagnostic inventory).
    pub object_pairs: Vec<String>,
    pub notes: Vec<String>,
}

impl ProductCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            left_factor_label: String::new(),
            right_factor_label: String::new(),
            object_pairs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn of(
        label: impl Into<String>,
        left_factor_label: impl Into<String>,
        right_factor_label: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            left_factor_label: left_factor_label.into(),
            right_factor_label: right_factor_label.into(),
            object_pairs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.left_factor_label.is_empty() {
            return Err("empty left_factor_label".into());
        }
        if self.right_factor_label.is_empty() {
            return Err("empty right_factor_label".into());
        }
        for (i, p) in self.object_pairs.iter().enumerate() {
            if p.is_empty() {
                return Err(format!("empty object_pair tag at index {i}"));
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
        assert!(ProductCategoryShell::of("C×D", "C", "D")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(ProductCategoryShell::new("").validate_shell().is_err());
        assert!(ProductCategoryShell::new("P").validate_shell().is_err());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/category/product_category.rs
// Claim: urn:core:category:product:cardinality:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProductCardinality {
    left: u64,
    right: u64,
    objects: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProductCardinalityError {
    ShellRefused { reason: String },
    Overflow,
    CountMismatch { product: u64, stored: u64 },
    PairTag { index: usize },
}

// Origin: engine/crates_rs/core_category_theory/src/category/product_category.rs
// Claim: urn:core:crates_rs:core-category-theory:product-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ProductCardinalityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ProductCardinalityError {}

fn validate_pair_tag(index: usize, tag: &str) -> Result<(), ProductCardinalityError> {
    let mut sides = tag.split('|');
    let first = sides.next().ok_or(ProductCardinalityError::PairTag { index })?;
    let second = sides.next().ok_or(ProductCardinalityError::PairTag { index })?;
    if first.is_empty() || second.is_empty() || sides.next().is_some() {
        return Err(ProductCardinalityError::PairTag { index });
    }
    Ok(())
}

impl ProductCardinality {
    pub fn try_on(shell: &ProductCategoryShell, left: u64, right: u64) -> Result<Self, ProductCardinalityError> {
        shell
            .validate_shell()
            .map_err(|reason| ProductCardinalityError::ShellRefused { reason })?;
        let product = left.checked_mul(right).ok_or(ProductCardinalityError::Overflow)?;
        let stored = u64::try_from(shell.object_pairs.len()).map_err(|_| ProductCardinalityError::Overflow)?;
        if product != stored {
            return Err(ProductCardinalityError::CountMismatch { product, stored });
        }
        for (index, tag) in shell.object_pairs.iter().enumerate() {
            validate_pair_tag(index, tag)?;
        }
        Ok(Self { left, right, objects: product })
    }

    pub fn objects(&self) -> u64 {
        self.objects
    }
}

#[cfg(test)]
mod product_cardinality_tests {
    use super::*;

    #[test]
    fn counts_the_cartesian_product() {
        let mut shell = ProductCategoryShell::of("CxD", "C", "D");
        shell.object_pairs = vec!["a|x".into(), "a|y".into(), "b|x".into(), "b|y".into()];
        let witness = ProductCardinality::try_on(&shell, 2, 2);
        assert!(matches!(witness, Ok(ref w) if w.objects() == 4));
    }

    #[test]
    fn refuses_a_short_inventory() {
        let shell = ProductCategoryShell::of("CxD", "C", "D");
        let wrong = ProductCardinality::try_on(&shell, 2, 3);
        assert!(matches!(
            wrong,
            Err(ProductCardinalityError::CountMismatch { product: 6, stored: 0 })
        ));
    }
}
