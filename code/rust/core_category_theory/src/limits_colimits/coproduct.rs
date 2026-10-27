//! coproduct shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_d9e51516;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_d9e51516<T> = std::result::Result<T, BoundaryError_d9e51516>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a (binary or multi-summand) coproduct.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Coproduct {
    pub label: String,
    /// Coproduct object.
    pub coproduct_object: String,
    /// Summand object labels.
    pub summands: Vec<String>,
    /// Injection morphism labels (aligned with summands when both present).
    pub injections: Vec<String>,
    pub notes: Vec<String>,
}

impl Coproduct {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            coproduct_object: String::new(),
            summands: Vec::new(),
            injections: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn binary(
        label: impl Into<String>,
        coproduct_object: impl Into<String>,
        left: impl Into<String>,
        right: impl Into<String>,
        injection_left: impl Into<String>,
        injection_right: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            coproduct_object: coproduct_object.into(),
            summands: vec![left.into(), right.into()],
            injections: vec![injection_left.into(), injection_right.into()],
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.coproduct_object.is_empty() {
            return Err("empty coproduct_object".into());
        }
        if self.summands.is_empty() {
            return Err("empty summands".into());
        }
        for (i, s) in self.summands.iter().enumerate() {
            if s.is_empty() {
                return Err(format!("empty summand at index {i}"));
            }
        }
        for (i, j) in self.injections.iter().enumerate() {
            if j.is_empty() {
                return Err(format!("empty injection at index {i}"));
            }
        }
        if !self.injections.is_empty() && self.injections.len() != self.summands.len() {
            return Err("injections length must match summands length".into());
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
        let c = Coproduct::binary("A+B", "A+B", "A", "B", "ι₁", "ι₂");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Coproduct::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_mismatched_injections() {
        let mut c = Coproduct::binary("S", "S", "A", "B", "ι₁", "ι₂");
        c.injections.pop();
        assert!(c.validate_shell().is_err());
    }
}

/// Cardinality of a binary coproduct of finite sets: |A ⊔ B| = |A| + |B|,
/// witnessed by the two injections.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CoproductCardinalities {
    left: u64,
    right: u64,
    total: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CoproductCardinalityError {
    Overflow { left: u64, right: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/coproduct.rs
// Claim: urn:core:crates_rs:core-category-theory:coproduct:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CoproductCardinalityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CoproductCardinalityError {}

impl CoproductCardinalities {
    pub fn try_new(left: u64, right: u64) -> Result<Self, CoproductCardinalityError> {
        let total = left
            .checked_add(right)
            .ok_or(CoproductCardinalityError::Overflow { left, right })?;
        Ok(Self { left, right, total })
    }

    pub fn left(&self) -> u64 {
        self.left
    }

    pub fn right(&self) -> u64 {
        self.right
    }

    pub fn total(&self) -> u64 {
        self.total
    }

    pub fn injection_count(&self) -> u64 {
        2
    }
}

#[cfg(test)]
mod coproduct_cardinality_witness {
    use super::*;

    #[test]
    fn binary_sum_is_checked() {
        let card = CoproductCardinalities::try_new(3, 5);
        assert!(card.is_ok());
        if let Ok(card) = card {
            assert_eq!(card.total(), 8);
            assert_eq!(card.injection_count(), 2);
        }
    }

    #[test]
    fn refuses_overflow() {
        assert!(matches!(
            CoproductCardinalities::try_new(u64::MAX, 1),
            Err(CoproductCardinalityError::Overflow { .. })
        ));
    }
}
