//! limit shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_ea89ab35;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_ea89ab35<T> = std::result::Result<T, BoundaryError_ea89ab35>;
use serde::{Deserialize, Serialize};

use super::cone::Cone;

/// Best-effort shell for a limit of a diagram (diagram_ref + limiting cone).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Limit {
    pub label: String,
    /// Opaque reference to the diagram being limited.
    pub diagram_ref: String,
    pub cone: Cone,
    pub notes: Vec<String>,
}

impl Limit {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            diagram_ref: String::new(),
            cone: Cone::default(),
            notes: Vec::new(),
        }
    }

    pub fn of_diagram(
        label: impl Into<String>,
        diagram_ref: impl Into<String>,
        cone: Cone,
    ) -> Self {
        Self {
            label: label.into(),
            diagram_ref: diagram_ref.into(),
            cone,
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.diagram_ref.is_empty() {
            return Err("empty diagram_ref".into());
        }
        self.cone
            .validate_shell()
            .map_err(|e| format!("cone: {e}"))?;
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::limits_colimits::cone::Cone;

    #[test]
    fn validate_ok() {
        let cone = Cone::with_apex("lim_cone", "L");
        let lim = Limit::of_diagram("lim", "D", cone);
        assert!(lim.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty_diagram() {
        let cone = Cone::with_apex("lim_cone", "L");
        let lim = Limit::of_diagram("lim", "", cone);
        assert!(lim.validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_empty_label() {
        assert!(Limit::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_bad_cone() {
        let lim = Limit::of_diagram("lim", "D", Cone::new("c"));
        assert!(lim.validate_shell().is_err());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteProductCardinality { left: u64, right: u64, product: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProductCardError { Overflow, Identity }

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/limit.rs
// Claim: urn:core:crates_rs:core-category-theory:limit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ProductCardError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ProductCardError {}

impl FiniteProductCardinality {
    /// `|A x B| = |A| * |B|`.
    pub fn try_new(left: u64, right: u64) -> Result<Self, ProductCardError> {
        let product = left.checked_mul(right).ok_or(ProductCardError::Overflow)?;
        if right != 0 && product / right != left {
            return Err(ProductCardError::Identity);
        }
        Ok(Self { left, right, product })
    }

    pub fn product(&self) -> u64 { self.product }
}

#[cfg(test)]
mod product_card_checks {
    use super::*;

    #[test]
    fn three_by_four_is_twelve() {
        let card = FiniteProductCardinality::try_new(3, 4);
        assert!(matches!(card, Ok(c) if c.product() == 12));
    }

    #[test]
    fn overflow_is_refused() {
        assert!(matches!(FiniteProductCardinality::try_new(u64::MAX, 2), Err(ProductCardError::Overflow)));
    }
}
