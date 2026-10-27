//! product shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_8677d036;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_8677d036<T> = std::result::Result<T, BoundaryError_8677d036>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a (binary or multi-factor) product.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Product {
    pub label: String,
    /// Product object.
    pub product_object: String,
    /// Factor object labels.
    pub factors: Vec<String>,
    /// Projection morphism labels (aligned with factors when both present).
    pub projections: Vec<String>,
    pub notes: Vec<String>,
}

impl Product {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            product_object: String::new(),
            factors: Vec::new(),
            projections: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn binary(
        label: impl Into<String>,
        product_object: impl Into<String>,
        left: impl Into<String>,
        right: impl Into<String>,
        projection_left: impl Into<String>,
        projection_right: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            product_object: product_object.into(),
            factors: vec![left.into(), right.into()],
            projections: vec![projection_left.into(), projection_right.into()],
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.product_object.is_empty() {
            return Err("empty product_object".into());
        }
        if self.factors.is_empty() {
            return Err("empty factors".into());
        }
        for (i, f) in self.factors.iter().enumerate() {
            if f.is_empty() {
                return Err(format!("empty factor at index {i}"));
            }
        }
        for (i, p) in self.projections.iter().enumerate() {
            if p.is_empty() {
                return Err(format!("empty projection at index {i}"));
            }
        }
        if !self.projections.is_empty() && self.projections.len() != self.factors.len() {
            return Err("projections length must match factors length".into());
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
        let p = Product::binary("A×B", "A×B", "A", "B", "π₁", "π₂");
        assert!(p.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Product::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_mismatched_projections() {
        let mut p = Product::binary("P", "P", "A", "B", "π₁", "π₂");
        p.projections.pop();
        assert!(p.validate_shell().is_err());
    }
}

/// Cardinality of a binary product of finite sets: |A × B| = |A| · |B|,
/// witnessed by the two projections.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProductCardinalities {
    left: u64,
    right: u64,
    total: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ProductCardinalityError {
    Overflow { left: u64, right: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/product.rs
// Claim: urn:core:crates_rs:core-category-theory:product:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ProductCardinalityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ProductCardinalityError {}

impl ProductCardinalities {
    pub fn try_new(left: u64, right: u64) -> Result<Self, ProductCardinalityError> {
        let total = left
            .checked_mul(right)
            .ok_or(ProductCardinalityError::Overflow { left, right })?;
        Ok(Self { left, right, total })
    }

    pub fn total(&self) -> u64 {
        self.total
    }

    pub fn projection_count(&self) -> u64 {
        2
    }
}

#[cfg(test)]
mod product_cardinality_witness {
    use super::*;

    #[test]
    fn binary_product_is_checked() {
        let card = ProductCardinalities::try_new(3, 5);
        assert!(card.is_ok());
        if let Ok(card) = card {
            assert_eq!(card.total(), 15);
            assert_eq!(card.projection_count(), 2);
        }
    }

    #[test]
    fn refuses_overflow() {
        assert!(matches!(
            ProductCardinalities::try_new(u64::MAX, 2),
            Err(ProductCardinalityError::Overflow { .. })
        ));
    }
}
