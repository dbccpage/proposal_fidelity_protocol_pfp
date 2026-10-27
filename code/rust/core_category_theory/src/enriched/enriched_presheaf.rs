//! enriched_presheaf shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort enriched presheaf shell F : C^op → V (V-enriched).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct EnrichedPresheaf {
    pub label: String,
    /// Domain enriched category shell label (C).
    pub domain_enriched: String,
    /// Base monoidal / closed V label (codomain of the presheaf).
    pub base_monoidal_v: String,
    /// Object-assignment ref (A ↦ FA ∈ Ob(V)).
    pub object_map_ref: String,
    /// Action / restriction family ref.
    pub action_ref: String,
    pub notes: Vec<String>,
}

impl EnrichedPresheaf {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            domain_enriched: String::new(),
            base_monoidal_v: String::new(),
            object_map_ref: String::new(),
            action_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn on(
        label: impl Into<String>,
        domain_enriched: impl Into<String>,
        base_monoidal_v: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            domain_enriched: domain_enriched.into(),
            base_monoidal_v: base_monoidal_v.into(),
            object_map_ref: String::new(),
            action_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.domain_enriched.is_empty() {
            return Err("empty domain_enriched".into());
        }
        if self.base_monoidal_v.is_empty() {
            return Err("empty base_monoidal_v".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/enriched/enriched_presheaf.rs
// Claim: urn:core:crates_rs:core-category-theory:enriched-presheaf:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord087bd3e0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord087bd3e0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError087bd3e0 {
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
impl BoundaryError087bd3e0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError087bd3e0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError087bd3e0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord087bd3e0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError087bd3e0> {
        if capacity_bound == 0 {
            return Err(BoundaryError087bd3e0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError087bd3e0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError087bd3e0::ExceedsCapacity {
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
        assert!(EnrichedPresheaf::on("P", "C", "V").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(EnrichedPresheaf::new("").validate_shell().is_err());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HomDimensionError { kind: &'static str, left: u128, right: u128 }
impl HomDimensionError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Positive hom-object dimensions of a finite enriched presheaf, with a checked total.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HomDimensionSum { objects: u64, total: u64 }
impl HomDimensionSum {
    pub fn try_from_dimensions(dimensions: &[u64]) -> Result<Self, HomDimensionError> {
        if dimensions.is_empty() {
            return Err(HomDimensionError::new("an enriched presheaf names at least one object", 0, 0));
        }
        let mut total = 0u64;
        for dimension in dimensions {
            if *dimension == 0 {
                return Err(HomDimensionError::new("a hom-object dimension is positive", 0, u128::from(*dimension)));
            }
            total = total.checked_add(*dimension).ok_or_else(|| HomDimensionError::new("hom-dimension sum overflow", u128::from(total), u128::from(*dimension)))?;
        }
        let objects = u64::try_from(dimensions.len()).map_err(|_| HomDimensionError::new("object count exceeds u64", dimensions.len() as u128, u128::from(u64::MAX)))?;
        Ok(Self { objects, total })
    }
    pub const fn total(&self) -> u64 { self.total }
    pub const fn objects(&self) -> u64 { self.objects }
}
#[cfg(test)]
mod hom_dimension_checks {
    use super::HomDimensionSum;
    #[test]
    fn dimensions_add() {
        let sum = HomDimensionSum::try_from_dimensions(&[2, 5, 1]);
        assert_eq!(sum.as_ref().map(HomDimensionSum::total), Ok(8));
        assert_eq!(sum.as_ref().map(HomDimensionSum::objects), Ok(3));
    }
    #[test]
    fn a_zero_dimension_is_refused() {
        assert_eq!(HomDimensionSum::try_from_dimensions(&[2, 0]).map(|_| ()).map_err(|e| e.kind()), Err("a hom-object dimension is positive"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_087bd3e0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord087bd3e0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord087bd3e0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord087bd3e0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord087bd3e0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord087bd3e0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError087bd3e0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError087bd3e0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
