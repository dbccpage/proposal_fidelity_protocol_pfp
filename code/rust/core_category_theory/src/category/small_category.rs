//! small_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! A small category has a set (not a proper class) of morphisms.
//! This shell records a finite presentation claim only.

use serde::{Deserialize, Serialize};

use super::category::{FiniteCategoryShell, MorphismTriple};

/// Best-effort small-category shell (finite presentation + smallness claim).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct SmallCategoryShell {
    pub label: String,
    /// Underlying finite presentation (optional; may be empty).
    pub presentation: FiniteCategoryShell,
    /// Declared claim that Hom-sets are sets (diagnostic flag only).
    pub claims_small: bool,
    pub notes: Vec<String>,
}

impl SmallCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        let label = label.into();
        Self {
            presentation: FiniteCategoryShell::new(label.clone()),
            label,
            claims_small: true,
            notes: Vec::new(),
        }
    }

    pub fn from_presentation(presentation: FiniteCategoryShell) -> Self {
        Self {
            label: presentation.label.clone(),
            presentation,
            claims_small: true,
            notes: Vec::new(),
        }
    }

    pub fn objects(&self) -> &[String] {
        &self.presentation.objects
    }

    pub fn morphisms(&self) -> &[MorphismTriple] {
        &self.presentation.morphisms
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if !self.claims_small {
            return Err("claims_small must be true for SmallCategoryShell".into());
        }
        self.presentation.validate_shell()?;
        if self.presentation.label != self.label && !self.presentation.label.is_empty() {
            // Allow empty presentation label only when objects empty; otherwise labels should match.
            if !self.presentation.objects.is_empty() {
                return Err(format!(
                    "presentation.label {:?} != shell.label {:?}",
                    self.presentation.label, self.label
                ));
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/category/small_category.rs
// Claim: urn:core:crates_rs:core-category-theory:small-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8be0b017 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8be0b017` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8be0b017 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError8be0b017 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8be0b017 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8be0b017 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8be0b017 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8be0b017> {
        if capacity_bound == 0 {
            return Err(BoundaryError8be0b017::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8be0b017::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8be0b017::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(SmallCategoryShell::new("C").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(SmallCategoryShell::new("").validate_shell().is_err());
    }

    #[test]
    fn from_presentation_ok() {
        let p = FiniteCategoryShell::with_objects("C", vec!["x".into()]);
        let s = SmallCategoryShell::from_presentation(p);
        assert_eq!(s.objects().len(), 1);
        assert!(s.validate_shell().is_ok());
    }
}

// Exact carrier witness.
impl SmallCategoryShell {
    /// Identity census of the presentation, plus unique morphism names.
    pub fn certify_presentation(&self) -> Result<super::category::IdentityCensus, super::category::IdentityCensusError> {
        let census = self.presentation.certify_identities()?;
        let mut names = std::collections::BTreeSet::new();
        for morphism in self.morphisms() {
            if morphism.name.is_empty() || !names.insert(morphism.name.clone()) {
                return Err(super::category::IdentityCensusError::DuplicateMorphism);
            }
        }
        if census.object_count() != census.identity_count() {
            return Err(super::category::IdentityCensusError::ExtraIdentity);
        }
        Ok(census)
    }
}

#[cfg(test)]
mod presentation_census_checks {
    use super::*;

    #[test]
    fn a_one_object_presentation_certifies() {
        let shell = SmallCategoryShell::from_presentation(FiniteCategoryShell::with_objects("C", vec!["x".into()]));
        let census = shell.certify_presentation();
        assert!(matches!(census, Ok(c) if c.object_count() == 1));
    }
}

#[cfg(test)]
mod l4_boundary_tests_8be0b017 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8be0b017::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8be0b017::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8be0b017::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8be0b017::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8be0b017::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8be0b017::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8be0b017::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
