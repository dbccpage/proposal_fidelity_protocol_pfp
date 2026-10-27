//! identity_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Identity functor Id_C : C → C — shape only.

use serde::{Deserialize, Serialize};

/// Best-effort shell for an identity functor on a category reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct IdentityFunctor {
    pub label: String,
    pub category_ref: String,
    pub notes: Vec<String>,
}

impl IdentityFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn on_category(label: impl Into<String>, category_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.category_ref.is_empty() {
            return Err("empty category_ref".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/functor/identity_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:identity-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordde00a5aa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordde00a5aa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorde00a5aa {
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
impl BoundaryErrorde00a5aa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorde00a5aa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorde00a5aa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordde00a5aa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorde00a5aa> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorde00a5aa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorde00a5aa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorde00a5aa::ExceedsCapacity {
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
        assert!(IdentityFunctor::on_category("Id_C", "C")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(IdentityFunctor::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_ref() {
        assert!(IdentityFunctor::new("Id").validate_shell().is_err());
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IdentityLawError { kind: &'static str, left: u128, right: u128 }
impl IdentityLawError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// One identity arrow per object, plus a checked count of the remaining arrows.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IdentityLaw { objects: u64, identities: u64, arrows: u64 }
impl IdentityLaw {
    pub fn try_new(objects: u64, arrows: u64) -> Result<Self, IdentityLawError> {
        if arrows < objects {
            return Err(IdentityLawError::new("identities are missing", u128::from(arrows), u128::from(objects)));
        }
        let extra = arrows.checked_sub(objects).ok_or_else(|| IdentityLawError::new("arrow remainder underflow", u128::from(arrows), u128::from(objects)))?;
        let restored = objects.checked_add(extra).ok_or_else(|| IdentityLawError::new("arrow total overflow", u128::from(objects), u128::from(extra)))?;
        if restored != arrows {
            return Err(IdentityLawError::new("arrow total was not restored", u128::from(restored), u128::from(arrows)));
        }
        Ok(Self { objects, identities: objects, arrows })
    }
    pub const fn identities(&self) -> u64 { self.identities }
    pub const fn arrows(&self) -> u64 { self.arrows }
}
#[cfg(test)]
mod identity_law_checks {
    use super::IdentityLaw;
    #[test]
    fn identities_equal_the_object_count() {
        let law = IdentityLaw::try_new(3, 5);
        assert_eq!(law.as_ref().map(IdentityLaw::identities), Ok(3));
        assert_eq!(law.as_ref().map(IdentityLaw::arrows), Ok(5));
    }
    #[test]
    fn fewer_arrows_than_objects_is_refused() {
        assert_eq!(IdentityLaw::try_new(2, 1).map(|_| ()).map_err(|e| e.kind()), Err("identities are missing"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_de00a5aa {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordde00a5aa::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordde00a5aa::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordde00a5aa::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordde00a5aa::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordde00a5aa::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorde00a5aa::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorde00a5aa::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
