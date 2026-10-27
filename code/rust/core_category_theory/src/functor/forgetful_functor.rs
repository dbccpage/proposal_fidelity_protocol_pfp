//! forgetful_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Forgetful (underlying) functor U : C → D — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_92b88efc;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_92b88efc<T> = std::result::Result<T, BoundaryError_92b88efc>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a forgetful functor between labeled categories.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ForgetfulFunctor {
    pub label: String,
    pub source_category: String,
    pub target_category: String,
    pub notes: Vec<String>,
}

impl ForgetfulFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            source_category: String::new(),
            target_category: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        source_category: impl Into<String>,
        target_category: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            source_category: source_category.into(),
            target_category: target_category.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.source_category.is_empty() {
            return Err("empty source_category".into());
        }
        if self.target_category.is_empty() {
            return Err("empty target_category".into());
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
        assert!(ForgetfulFunctor::between("U", "Grp", "Set")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(ForgetfulFunctor::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_categories() {
        assert!(ForgetfulFunctor::new("U").validate_shell().is_err());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LagrangeIndex { group_order: u64, subgroup_order: u64, index: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LagrangeError { Empty, Overflow, Quotient }

// Origin: engine/crates_rs/core_category_theory/src/functor/forgetful_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:forgetful-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for LagrangeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for LagrangeError {}

impl LagrangeIndex {
    /// `|G| = [G:H] * |H|`.
    pub fn try_new(subgroup_order: u64, index: u64) -> Result<Self, LagrangeError> {
        if subgroup_order == 0 || index == 0 {
            return Err(LagrangeError::Empty);
        }
        let group_order = subgroup_order.checked_mul(index).ok_or(LagrangeError::Overflow)?;
        if group_order / index != subgroup_order {
            return Err(LagrangeError::Quotient);
        }
        Ok(Self { group_order, subgroup_order, index })
    }

    pub fn group_order(&self) -> u64 { self.group_order }
}

#[cfg(test)]
mod lagrange_checks {
    use super::*;

    #[test]
    fn index_two_doubles_the_subgroup() {
        let index = LagrangeIndex::try_new(3, 2);
        assert!(matches!(index, Ok(i) if i.group_order() == 6));
    }

    #[test]
    fn a_zero_subgroup_is_refused() {
        assert!(matches!(LagrangeIndex::try_new(0, 2), Err(LagrangeError::Empty)));
    }
}
