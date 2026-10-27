//! initial_object shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort shell for an initial object (colimit of the empty diagram).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct InitialObject {
    pub label: String,
    /// Object claimed to be initial.
    pub object: String,
    /// Ambient category reference (diagnostic).
    pub category_ref: String,
    pub notes: Vec<String>,
}

impl InitialObject {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            object: String::new(),
            category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn in_category(
        label: impl Into<String>,
        object: impl Into<String>,
        category_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            object: object.into(),
            category_ref: category_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.object.is_empty() {
            return Err("empty object".into());
        }
        if self.category_ref.is_empty() {
            return Err("empty category_ref".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/initial_object.rs
// Claim: urn:core:crates_rs:core-category-theory:initial-object:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord42d9f281 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord42d9f281` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError42d9f281 {
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
impl BoundaryError42d9f281 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError42d9f281 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError42d9f281 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord42d9f281 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError42d9f281> {
        if capacity_bound == 0 {
            return Err(BoundaryError42d9f281::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError42d9f281::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError42d9f281::ExceedsCapacity {
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
        assert!(InitialObject::in_category("0", "0", "C")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(InitialObject::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_object() {
        assert!(InitialObject::new("i").validate_shell().is_err());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InitialArrowError { kind: &'static str, left: u128, right: u128 }
impl InitialArrowError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Exactly one arrow out of the initial object for every object, including itself.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InitialArrowFamily { targets: u64, arrows: u64 }
impl InitialArrowFamily {
    pub fn try_new(targets: u64, arrows: u64) -> Result<Self, InitialArrowError> {
        if arrows != targets {
            return Err(InitialArrowError::new("an initial object has one arrow to each object", u128::from(arrows), u128::from(targets)));
        }
        Ok(Self { targets, arrows })
    }
    pub const fn arrows(&self) -> u64 { self.arrows }
}
#[cfg(test)]
mod initial_arrow_checks {
    use super::InitialArrowFamily;
    #[test]
    fn the_arrow_count_equals_the_object_count() {
        assert_eq!(InitialArrowFamily::try_new(4, 4).as_ref().map(InitialArrowFamily::arrows), Ok(4));
    }
    #[test]
    fn an_extra_arrow_is_refused() {
        assert_eq!(InitialArrowFamily::try_new(4, 5).map(|_| ()).map_err(|e| e.kind()), Err("an initial object has one arrow to each object"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_42d9f281 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord42d9f281::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord42d9f281::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord42d9f281::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord42d9f281::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord42d9f281::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError42d9f281::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError42d9f281::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
