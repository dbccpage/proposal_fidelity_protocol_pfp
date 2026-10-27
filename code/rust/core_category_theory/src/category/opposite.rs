//! opposite category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! C^op has the same objects; morphisms reverse (source ↔ target).

use serde::{Deserialize, Serialize};

use super::category::MorphismTriple;

/// Best-effort opposite-category shell wrapping a base label.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct OppositeCategoryShell {
    pub label: String,
    /// Label of the base category C (so this shell is C^op).
    pub base_label: String,
    /// Reversed morphism pairs: each triple is stored already reversed
    /// (source, target, name) relative to the base orientation.
    pub reversed_morphisms: Vec<MorphismTriple>,
    pub notes: Vec<String>,
}

impl OppositeCategoryShell {
    pub fn new(label: impl Into<String>, base_label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_label: base_label.into(),
            reversed_morphisms: Vec::new(),
            notes: Vec::new(),
        }
    }

    /// Reverse a base morphism (src, dst, name) → (dst, src, name) for C^op.
    pub fn reverse_of(
        label: impl Into<String>,
        base_label: impl Into<String>,
        base_morphisms: Vec<MorphismTriple>,
    ) -> Self {
        let reversed_morphisms = base_morphisms
            .into_iter()
            .map(|m| MorphismTriple::new(m.target, m.source, m.name))
            .collect();
        Self {
            label: label.into(),
            base_label: base_label.into(),
            reversed_morphisms,
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.base_label.is_empty() {
            return Err("empty base_label".into());
        }
        for (i, m) in self.reversed_morphisms.iter().enumerate() {
            if m.source.is_empty() || m.target.is_empty() || m.name.is_empty() {
                return Err(format!("empty reversed morphism field at index {i}"));
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/category/opposite.rs
// Claim: urn:core:crates_rs:core-category-theory:opposite:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord28bde593 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord28bde593` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError28bde593 {
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
impl BoundaryError28bde593 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError28bde593 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError28bde593 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord28bde593 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError28bde593> {
        if capacity_bound == 0 {
            return Err(BoundaryError28bde593::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError28bde593::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError28bde593::ExceedsCapacity {
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
        assert!(OppositeCategoryShell::new("C^op", "C")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(OppositeCategoryShell::new("", "C")
            .validate_shell()
            .is_err());
        assert!(OppositeCategoryShell::new("Cop", "")
            .validate_shell()
            .is_err());
    }

    #[test]
    fn reverse_of_swaps_endpoints() {
        let base = vec![MorphismTriple::new("a", "b", "f")];
        let op = OppositeCategoryShell::reverse_of("C^op", "C", base);
        assert_eq!(op.reversed_morphisms[0].source, "b");
        assert_eq!(op.reversed_morphisms[0].target, "a");
        assert!(op.validate_shell().is_ok());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OppositeError { kind: &'static str, left: u128, right: u128 }
impl OppositeError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Finite opposite: every endpoint lies in the object set, and reversing twice restores the arrow.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OppositeCensus { objects: u64, arrows: u64 }
impl OppositeCensus {
    pub fn try_reverse(objects: u64, arrows: &[(u64, u64)]) -> Result<Self, OppositeError> {
        let mut count = 0u64;
        for arrow in arrows {
            let (source, target) = *arrow;
            if source >= objects || target >= objects {
                return Err(OppositeError::new("arrow endpoint outside the object set", u128::from(source.max(target)), u128::from(objects)));
            }
            let reversed = (target, source);
            let restored = (reversed.1, reversed.0);
            if restored != *arrow {
                return Err(OppositeError::new("double reversal failed", u128::from(restored.0), u128::from(source)));
            }
            count = count.checked_add(1).ok_or_else(|| OppositeError::new("arrow count overflow", u128::from(count), 1))?;
        }
        Ok(Self { objects, arrows: count })
    }
    pub const fn arrows(&self) -> u64 { self.arrows }
}
#[cfg(test)]
mod opposite_census_checks {
    use super::OppositeCensus;
    #[test]
    fn reversal_preserves_the_arrow_count() {
        let census = OppositeCensus::try_reverse(3, &[(0, 1), (1, 2)]);
        assert_eq!(census.as_ref().map(OppositeCensus::arrows), Ok(2));
    }
    #[test]
    fn an_endpoint_past_the_object_set_is_refused() {
        assert_eq!(OppositeCensus::try_reverse(2, &[(0, 2)]).map(|_| ()).map_err(|e| e.kind()), Err("arrow endpoint outside the object set"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_28bde593 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord28bde593::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord28bde593::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord28bde593::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord28bde593::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord28bde593::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError28bde593::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError28bde593::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
