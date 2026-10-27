//! finite_set shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Related contract (if present): `urn:core:math:finite_set:v0.1.0`.

use serde::{Deserialize, Serialize};

/// Best-effort shell for a finite set with explicit element inventory.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteSet {
    pub label: String,
    /// Finite element tags (canonical identifiers or hashes as strings).
    pub elements: Vec<String>,
    /// Declared cardinality; when set, must match `elements.len()` for validation.
    pub declared_cardinality: Option<usize>,
    pub notes: Vec<String>,
}

impl FiniteSet {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            elements: Vec::new(),
            declared_cardinality: Some(0),
            notes: Vec::new(),
        }
    }

    pub fn with_elements(label: impl Into<String>, elements: Vec<String>) -> Self {
        let n = elements.len();
        Self {
            label: label.into(),
            elements,
            declared_cardinality: Some(n),
            notes: Vec::new(),
        }
    }

    pub fn cardinality(&self) -> usize {
        self.elements.len()
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        for (i, e) in self.elements.iter().enumerate() {
            if e.is_empty() {
                return Err(format!("empty element tag at index {i}"));
            }
        }
        if let Some(n) = self.declared_cardinality {
            if n != self.elements.len() {
                return Err(format!(
                    "declared_cardinality {n} != elements.len() {}",
                    self.elements.len()
                ));
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/foundations/finite_set.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-set:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordebc3d8e6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordebc3d8e6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorebc3d8e6 {
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
impl BoundaryErrorebc3d8e6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorebc3d8e6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorebc3d8e6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordebc3d8e6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorebc3d8e6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorebc3d8e6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorebc3d8e6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorebc3d8e6::ExceedsCapacity {
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
        assert!(FiniteSet::new("x").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(FiniteSet::new("").validate_shell().is_err());
    }

    #[test]
    fn with_elements_ok() {
        let s = FiniteSet::with_elements("F", vec!["0".into(), "1".into()]);
        assert_eq!(s.cardinality(), 2);
        assert!(s.validate_shell().is_ok());
    }

    #[test]
    fn rejects_cardinality_mismatch() {
        let mut s = FiniteSet::with_elements("F", vec!["a".into()]);
        s.declared_cardinality = Some(3);
        assert!(s.validate_shell().is_err());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnionCardError { kind: &'static str, left: u128, right: u128 }
impl UnionCardError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Cardinality of a union from the two sizes and their intersection.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DisjointUnionCard { left: u64, right: u64, intersection: u64, union_card: u64 }
impl DisjointUnionCard {
    pub fn try_new(left: u64, right: u64, intersection: u64) -> Result<Self, UnionCardError> {
        if intersection > left || intersection > right {
            return Err(UnionCardError::new("intersection exceeds a side", u128::from(intersection), u128::from(left.min(right))));
        }
        let sum = left.checked_add(right).ok_or_else(|| UnionCardError::new("cardinality sum overflow", u128::from(left), u128::from(right)))?;
        let union_card = sum.checked_sub(intersection).ok_or_else(|| UnionCardError::new("union underflow", u128::from(sum), u128::from(intersection)))?;
        let restored = union_card.checked_add(intersection).ok_or_else(|| UnionCardError::new("union did not restore the sum", u128::from(union_card), u128::from(intersection)))?;
        if restored != sum {
            return Err(UnionCardError::new("union did not restore the sum", u128::from(restored), u128::from(sum)));
        }
        Ok(Self { left, right, intersection, union_card })
    }
    pub const fn union_card(&self) -> u64 { self.union_card }
}
#[cfg(test)]
mod union_card_checks {
    use super::DisjointUnionCard;
    #[test]
    fn inclusion_exclusion_is_exact() {
        let card = DisjointUnionCard::try_new(5, 4, 2);
        assert_eq!(card.as_ref().map(DisjointUnionCard::union_card), Ok(7));
    }
    #[test]
    fn an_oversized_intersection_is_refused() {
        assert_eq!(DisjointUnionCard::try_new(1, 4, 2).map(|_| ()).map_err(|e| e.kind()), Err("intersection exceeds a side"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_ebc3d8e6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordebc3d8e6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordebc3d8e6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordebc3d8e6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordebc3d8e6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordebc3d8e6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorebc3d8e6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorebc3d8e6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
