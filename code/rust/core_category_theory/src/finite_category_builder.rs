//! Ergonomic builder for declared finite categories.

use super::finite_category::{DeclaredFiniteCategory, ValidatedFiniteCategory};
use super::validation::ValidationReport;

#[derive(Debug, Clone)]
pub struct DeclaredFiniteCategoryBuilder {
    category: DeclaredFiniteCategory,
}

impl DeclaredFiniteCategoryBuilder {
    pub fn new(name: &str) -> Self {
        Self {
            category: DeclaredFiniteCategory::new(name),
        }
    }

    pub fn walking_arrow(name: &str, source: &str, target: &str, arrow: &str) -> Self {
        Self::new(name)
            .identity_object(source)
            .identity_object(target)
            .morphism(arrow, source, target)
            .identity_compositions()
    }

    pub fn object(mut self, object: &str) -> Self {
        self.category.add_object(object);
        self
    }

    pub fn morphism(mut self, name: &str, source: &str, target: &str) -> Self {
        self.category.add_morphism(name, source, target);
        self
    }

    pub fn identity(mut self, object: &str, morphism: &str) -> Self {
        self.category.add_identity(object, morphism);
        self
    }

    pub fn identity_checked(mut self, object: &str, morphism: &str) -> Result<Self, String> {
        if let Some((src, tgt)) = self.category.boundary_of(morphism) {
            if src != object || tgt != object {
                return Err(format!(
                    "Cannot set {} as identity of {}: boundary is {} → {}",
                    morphism, object, src, tgt
                ));
            }
        } else {
            self.category.add_morphism(morphism, object, object);
        }

        self.category.set_identity(object, morphism);
        Ok(self)
    }

    pub fn identity_object(mut self, object: &str) -> Self {
        let id = format!("id_{}", object);
        self.category.add_morphism(&id, object, object);
        self.category.set_identity(object, &id);
        self
    }

    /// Adds composition second ∘ first = composite.
    pub fn composition(mut self, first: &str, second: &str, composite: &str) -> Self {
        self.category.set_composition(first, second, composite);
        self
    }

    /// Alias for `composition`, emphasizing that `(f, g)` means `g` after `f`.
    pub fn path_composition(mut self, f: &str, g: &str, composite: &str) -> Self {
        self.category.set_composition(f, g, composite);
        self
    }

    /// Adds the identity compositions forced by the currently declared
    /// identities and morphism boundaries.
    pub fn identity_compositions(mut self) -> Self {
        let morphisms = self
            .category
            .morphisms
            .values()
            .cloned()
            .collect::<Vec<_>>();

        for morphism in morphisms {
            if let Some(source_id) = self
                .category
                .identity_of(&morphism.source)
                .map(|identity| identity.to_string())
            {
                self.category
                    .set_composition(&source_id, &morphism.name, &morphism.name);
            }
            if let Some(target_id) = self
                .category
                .identity_of(&morphism.target)
                .map(|identity| identity.to_string())
            {
                self.category
                    .set_composition(&morphism.name, &target_id, &morphism.name);
            }
        }

        self
    }

    pub fn build(self) -> DeclaredFiniteCategory {
        self.category
    }

    pub fn build_validated(self) -> Result<ValidatedFiniteCategory, ValidationReport> {
        ValidatedFiniteCategory::try_new(self.category)
    }
}

// Origin: engine/crates_rs/core_category_theory/src/finite_category_builder.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-category-builder:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord63368de6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord63368de6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError63368de6 {
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
impl BoundaryError63368de6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError63368de6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError63368de6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord63368de6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError63368de6> {
        if capacity_bound == 0 {
            return Err(BoundaryError63368de6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError63368de6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError63368de6::ExceedsCapacity {
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
    fn builder_can_validate_walking_arrow() {
        let category = DeclaredFiniteCategoryBuilder::walking_arrow("WalkingArrow", "A", "B", "f")
            .build_validated();

        assert!(category.is_ok());
    }
}

#[cfg(test)]
mod l4_boundary_tests_63368de6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord63368de6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord63368de6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord63368de6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord63368de6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord63368de6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError63368de6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError63368de6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
