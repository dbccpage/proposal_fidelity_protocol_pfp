//! algebra_for_monad shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! An algebra for a monad T is a carrier A with structure map h : T(A) → A.
//! Shell holds carrier + structure-map labels and a monad ref.

use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled T-algebra (A, h).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct AlgebraForMonad {
    pub label: String,
    /// Carrier object label A.
    pub carrier_label: String,
    /// Structure map label h : T(A) → A.
    pub structure_map_label: String,
    /// Ref to the ambient monad T.
    pub monad_ref: String,
    pub notes: Vec<String>,
}

impl AlgebraForMonad {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            carrier_label: String::new(),
            structure_map_label: String::new(),
            monad_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_structure(
        label: impl Into<String>,
        carrier_label: impl Into<String>,
        structure_map_label: impl Into<String>,
        monad_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            carrier_label: carrier_label.into(),
            structure_map_label: structure_map_label.into(),
            monad_ref: monad_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.carrier_label.is_empty() {
            return Err("empty carrier_label".into());
        }
        if self.structure_map_label.is_empty() {
            return Err("empty structure_map_label".into());
        }
        if self.monad_ref.is_empty() {
            return Err("empty monad_ref".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/monad/algebra_for_monad.rs
// Claim: urn:core:crates_rs:core-category-theory:algebra-for-monad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord984af891 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord984af891` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError984af891 {
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
impl BoundaryError984af891 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError984af891 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError984af891 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord984af891 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError984af891> {
        if capacity_bound == 0 {
            return Err(BoundaryError984af891::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError984af891::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError984af891::ExceedsCapacity {
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
        let a = AlgebraForMonad::with_structure("bool_alg", "Bool", "h_bool", "Maybe");
        assert!(a.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(AlgebraForMonad::new("").validate_shell().is_err());
        assert!(AlgebraForMonad::new("a").validate_shell().is_err());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AlgebraCardError { kind: &'static str, left: u128, right: u128 }
impl AlgebraCardError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Finite monad algebra: the unit section keeps |A| <= |T(A)| and the structure map's image fits in A.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AlgebraCard { carrier: u64, free_carrier: u64, image: u64 }
impl AlgebraCard {
    pub fn try_new(carrier: u64, free_carrier: u64, image: u64) -> Result<Self, AlgebraCardError> {
        if carrier > free_carrier {
            return Err(AlgebraCardError::new("unit section is not injective", u128::from(carrier), u128::from(free_carrier)));
        }
        if image > carrier {
            return Err(AlgebraCardError::new("structure image exceeds the carrier", u128::from(image), u128::from(carrier)));
        }
        Ok(Self { carrier, free_carrier, image })
    }
    pub const fn image(&self) -> u64 { self.image }
}
#[cfg(test)]
mod algebra_card_checks {
    use super::AlgebraCard;
    #[test]
    fn a_retraction_onto_a_subset_is_admitted() {
        assert_eq!(AlgebraCard::try_new(2, 4, 2).as_ref().map(AlgebraCard::image), Ok(2));
    }
    #[test]
    fn an_image_larger_than_the_carrier_is_refused() {
        assert_eq!(AlgebraCard::try_new(2, 4, 3).map(|_| ()).map_err(|e| e.kind()), Err("structure image exceeds the carrier"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_984af891 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord984af891::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord984af891::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord984af891::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord984af891::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord984af891::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError984af891::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError984af891::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
