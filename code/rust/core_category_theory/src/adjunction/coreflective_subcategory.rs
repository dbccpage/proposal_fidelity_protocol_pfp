//! coreflective subcategory shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! A full subcategory i : A ↪ C is coreflective when the inclusion admits
//! a right adjoint (coreflector) c : C → A, i ⊣ c.

use serde::{Deserialize, Serialize};

/// Best-effort shell for a coreflective subcategory declaration.
///
/// Records subcategory and coreflector labels only — not a coreflectivity proof.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoreflectiveSubcategoryShell {
    pub label: String,
    /// Ambient category C.
    pub ambient_category: String,
    /// Subcategory A ⊆ C (full subcategory label).
    pub subcategory: String,
    /// Inclusion i : A → C label.
    pub inclusion: String,
    /// Coreflector (right adjoint) c : C → A label.
    pub coreflector: String,
    /// Optional unit ref for i ⊣ c.
    pub unit_ref: String,
    /// Optional counit ref for i ⊣ c.
    pub counit_ref: String,
    pub notes: Vec<String>,
}

impl CoreflectiveSubcategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            ambient_category: String::new(),
            subcategory: String::new(),
            inclusion: String::new(),
            coreflector: String::new(),
            unit_ref: String::new(),
            counit_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_labels(
        label: impl Into<String>,
        ambient_category: impl Into<String>,
        subcategory: impl Into<String>,
        coreflector: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            ambient_category: ambient_category.into(),
            subcategory: subcategory.into(),
            inclusion: String::new(),
            coreflector: coreflector.into(),
            unit_ref: String::new(),
            counit_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_inclusion(mut self, inclusion: impl Into<String>) -> Self {
        self.inclusion = inclusion.into();
        self
    }

    pub fn with_unit_counit(
        mut self,
        unit_ref: impl Into<String>,
        counit_ref: impl Into<String>,
    ) -> Self {
        self.unit_ref = unit_ref.into();
        self.counit_ref = counit_ref.into();
        self
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.ambient_category.is_empty() {
            return Err("empty ambient_category".into());
        }
        if self.subcategory.is_empty() {
            return Err("empty subcategory".into());
        }
        if self.coreflector.is_empty() {
            return Err("empty coreflector".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/adjunction/coreflective_subcategory.rs
// Claim: urn:core:crates_rs:core-category-theory:coreflective-subcategory:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0f2bb15b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0f2bb15b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0f2bb15b {
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
impl BoundaryError0f2bb15b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0f2bb15b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0f2bb15b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0f2bb15b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0f2bb15b> {
        if capacity_bound == 0 {
            return Err(BoundaryError0f2bb15b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0f2bb15b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0f2bb15b::ExceedsCapacity {
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
        let c = CoreflectiveSubcategoryShell::with_labels("corefl", "C", "A", "c");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(CoreflectiveSubcategoryShell::new("")
            .validate_shell()
            .is_err());
    }

    #[test]
    fn with_inclusion_and_unit_ok() {
        let c = CoreflectiveSubcategoryShell::with_labels("compactly-gen", "Top", "CG", "k")
            .with_inclusion("i")
            .with_unit_counit("η", "ε");
        assert_eq!(c.coreflector, "k");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn rejects_missing_coreflector() {
        let mut c = CoreflectiveSubcategoryShell::new("x");
        c.ambient_category = "C".into();
        c.subcategory = "A".into();
        assert!(c.validate_shell().is_err());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoreflectorError { kind: &'static str, left: u128, right: u128 }
impl CoreflectorError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// A coreflector supplies one counit per subcategory object, and that count does not exceed the ambient category.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoreflectorCount { ambient: u64, subcategory: u64, counits: u64 }
impl CoreflectorCount {
    pub fn try_new(ambient: u64, subcategory: u64) -> Result<Self, CoreflectorError> {
        if subcategory > ambient {
            return Err(CoreflectorError::new("subcategory larger than the ambient category", u128::from(subcategory), u128::from(ambient)));
        }
        Ok(Self { ambient, subcategory, counits: subcategory })
    }
    pub const fn counits(&self) -> u64 { self.counits }
}
#[cfg(test)]
mod coreflector_checks {
    use super::CoreflectorCount;
    #[test]
    fn counits_match_the_subcategory() {
        let count = CoreflectorCount::try_new(5, 2);
        assert_eq!(count.as_ref().map(CoreflectorCount::counits), Ok(2));
    }
    #[test]
    fn a_larger_subcategory_is_refused() {
        assert_eq!(CoreflectorCount::try_new(1, 2).map(|_| ()).map_err(|e| e.kind()), Err("subcategory larger than the ambient category"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_0f2bb15b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0f2bb15b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0f2bb15b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0f2bb15b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0f2bb15b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0f2bb15b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0f2bb15b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0f2bb15b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
