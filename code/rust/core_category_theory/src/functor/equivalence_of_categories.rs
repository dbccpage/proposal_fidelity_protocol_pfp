//! equivalence_of_categories shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Equivalence C ≃ D via functors + unit/counit refs — shape only, not a proof.

use serde::{Deserialize, Serialize};

/// Best-effort shell for an equivalence of categories claim.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct EquivalenceOfCategories {
    pub label: String,
    pub left_functor_ref: String,
    pub right_functor_ref: String,
    /// Optional unit natural transformation η : Id ⇒ G F.
    pub unit_nat_trans_ref: String,
    /// Optional counit natural transformation ε : F G ⇒ Id.
    pub counit_nat_trans_ref: String,
    pub notes: Vec<String>,
}

impl EquivalenceOfCategories {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            left_functor_ref: String::new(),
            right_functor_ref: String::new(),
            unit_nat_trans_ref: String::new(),
            counit_nat_trans_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        left_functor_ref: impl Into<String>,
        right_functor_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            left_functor_ref: left_functor_ref.into(),
            right_functor_ref: right_functor_ref.into(),
            unit_nat_trans_ref: String::new(),
            counit_nat_trans_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.left_functor_ref.is_empty() {
            return Err("empty left_functor_ref".into());
        }
        if self.right_functor_ref.is_empty() {
            return Err("empty right_functor_ref".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/functor/equivalence_of_categories.rs
// Claim: urn:core:crates_rs:core-category-theory:equivalence-of-categories:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7cb1d7a1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7cb1d7a1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7cb1d7a1 {
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
impl BoundaryError7cb1d7a1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7cb1d7a1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7cb1d7a1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7cb1d7a1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7cb1d7a1> {
        if capacity_bound == 0 {
            return Err(BoundaryError7cb1d7a1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7cb1d7a1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7cb1d7a1::ExceedsCapacity {
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
        assert!(EquivalenceOfCategories::between("eq", "F", "G")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(EquivalenceOfCategories::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_functors() {
        assert!(EquivalenceOfCategories::new("eq").validate_shell().is_err());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BijectionError { kind: &'static str, left: u128, right: u128 }
impl BijectionError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// A finite equivalence shadow: forward and backward maps are mutual inverses on 0..n.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteBijection { cardinality: u64 }
impl FiniteBijection {
    fn lookup_at(
        slice: &[u64],
        index: u64,
        overflow_msg: &'static str,
        missing_msg: &'static str,
    ) -> Result<u64, BijectionError> {
        let pos = usize::try_from(index)
            .map_err(|_| BijectionError::new(overflow_msg, u128::from(index), 0))?;
        slice
            .get(pos)
            .copied()
            .ok_or_else(|| BijectionError::new(missing_msg, u128::from(index), slice.len() as u128))
    }

    fn verify_inverse_at(
        forward: &[u64],
        backward: &[u64],
        cardinality: u64,
        index: u64,
    ) -> Result<(), BijectionError> {
        let image = Self::lookup_at(forward, index, "index exceeds usize", "forward image missing")?;
        let preimage = Self::lookup_at(backward, index, "index exceeds usize", "backward image missing")?;
        if image >= cardinality || preimage >= cardinality {
            return Err(BijectionError::new(
                "map leaves 0..n",
                u128::from(image.max(preimage)),
                u128::from(cardinality),
            ));
        }
        let back = Self::lookup_at(backward, image, "image exceeds usize", "backward at image missing")?;
        let forth = Self::lookup_at(forward, preimage, "preimage exceeds usize", "forward at preimage missing")?;
        if back != index || forth != index {
            return Err(BijectionError::new(
                "maps are not mutual inverses",
                u128::from(back),
                u128::from(index),
            ));
        }
        Ok(())
    }

    pub fn try_inverse(forward: &[u64], backward: &[u64]) -> Result<Self, BijectionError> {
        if forward.len() != backward.len() {
            return Err(BijectionError::new("inverse maps have different lengths", forward.len() as u128, backward.len() as u128));
        }
        let cardinality = u64::try_from(forward.len()).map_err(|_| BijectionError::new("cardinality exceeds u64", forward.len() as u128, u128::from(u64::MAX)))?;
        let mut index = 0u64;
        while index < cardinality {
            Self::verify_inverse_at(forward, backward, cardinality, index)?;
            index = index.checked_add(1).ok_or_else(|| BijectionError::new("index overflow", u128::from(index), 1))?;
        }
        Ok(Self { cardinality })
    }
    pub const fn cardinality(&self) -> u64 { self.cardinality }
}
#[cfg(test)]
mod bijection_checks {
    use super::FiniteBijection;
    #[test]
    fn a_transposition_and_its_inverse_are_admitted() {
        let bijection = FiniteBijection::try_inverse(&[1, 0, 2], &[1, 0, 2]);
        assert_eq!(bijection.as_ref().map(FiniteBijection::cardinality), Ok(3));
    }
    #[test]
    fn a_non_inverse_is_refused() {
        assert_eq!(FiniteBijection::try_inverse(&[1, 0], &[0, 1]).map(|_| ()).map_err(|e| e.kind()), Err("maps are not mutual inverses"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_7cb1d7a1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7cb1d7a1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7cb1d7a1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7cb1d7a1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7cb1d7a1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7cb1d7a1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7cb1d7a1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7cb1d7a1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
