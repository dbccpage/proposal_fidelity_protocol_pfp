//! monoidal_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_317d84d5;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_317d84d5<T> = std::result::Result<T, BoundaryError_317d84d5>;
use serde::{Deserialize, Serialize};

/// Best-effort monoidal functor shell F : C → D with strength data refs.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MonoidalFunctor {
    pub label: String,
    /// Domain monoidal category shell label.
    pub domain_monoidal: String,
    /// Codomain monoidal category shell label.
    pub codomain_monoidal: String,
    /// Underlying ordinary functor ref.
    pub functor_ref: String,
    /// Tensorator / strength μ : F(A) ⊗ F(B) → F(A ⊗ B) ref.
    pub tensorator_ref: String,
    /// Unit comparison ε : I_D → F(I_C) ref.
    pub unit_comparison_ref: String,
    /// True if strong monoidal is claimed (diagnostic only).
    pub strong_claimed: bool,
    pub notes: Vec<String>,
}

impl MonoidalFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            domain_monoidal: String::new(),
            codomain_monoidal: String::new(),
            functor_ref: String::new(),
            tensorator_ref: String::new(),
            unit_comparison_ref: String::new(),
            strong_claimed: false,
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        domain_monoidal: impl Into<String>,
        codomain_monoidal: impl Into<String>,
        functor_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            domain_monoidal: domain_monoidal.into(),
            codomain_monoidal: codomain_monoidal.into(),
            functor_ref: functor_ref.into(),
            tensorator_ref: String::new(),
            unit_comparison_ref: String::new(),
            strong_claimed: false,
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.domain_monoidal.is_empty() {
            return Err("empty domain_monoidal".into());
        }
        if self.codomain_monoidal.is_empty() {
            return Err("empty codomain_monoidal".into());
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
        assert!(MonoidalFunctor::between("F", "C", "D", "F0")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(MonoidalFunctor::new("").validate_shell().is_err());
    }
}

/// Strict monoidal image of a pair of finite dimensions: the tensor of
/// dimensions multiplies, and overflow is a typed refusal.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StrictTensorDimension {
    left: u64,
    right: u64,
    image: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum StrictTensorError {
    Overflow { left: u64, right: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/monoidal/monoidal_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:monoidal-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for StrictTensorError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for StrictTensorError {}

impl StrictTensorDimension {
    pub fn try_new(left: u64, right: u64) -> Result<Self, StrictTensorError> {
        let image = left
            .checked_mul(right)
            .ok_or(StrictTensorError::Overflow { left, right })?;
        Ok(Self { left, right, image })
    }

    pub fn image(&self) -> u64 {
        self.image
    }
}

#[cfg(test)]
mod strict_tensor_witness {
    use super::*;

    #[test]
    fn image_dimension_is_product() {
        let dim = StrictTensorDimension::try_new(4, 3);
        assert!(dim.is_ok());
        if let Ok(dim) = dim {
            assert_eq!(dim.image(), 12);
        }
    }

    #[test]
    fn refuses_overflow() {
        assert!(matches!(
            StrictTensorDimension::try_new(u64::MAX, 3),
            Err(StrictTensorError::Overflow { .. })
        ));
    }
}
