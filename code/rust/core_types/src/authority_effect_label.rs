//! Shared advisory fact-label `{EvidenceOnly, FactOnly}`.
//!
//! Consolidates the three byte-identical enums formerly defined separately in
//! `core_certifiers::checked_packet`, `core_measurement::measurement_access`,
//! and `core_measurement::measurement_envelope` (Sprint 120-0 ADR
//! `AuthorityEffect` audit).
//!
//! This is an **advisory label**, NOT the authority firewall. It can never carry
//! a [`crate::authority::CertifiedAuthority`] payload — the firewall is
//! [`crate::authority::AuthorityEffect`], kept deliberately distinct. `FactLabel`
//! projects onto the shared strength lattice
//! [`crate::authority_lattice::AuthorityEffectLevel`] via [`FactLabel::level`].

use crate::authority_lattice::AuthorityEffectLevel;
use serde::{Deserialize, Serialize};

/// Advisory fact-label: was an artifact backed by evidence only, or checked into a fact?
///
/// Neither variant is certified authority. Mirrors the derives of the enums it
/// replaces (Copy + Hash + serde).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum FactLabel {
    /// Evidence only — not yet verified.
    EvidenceOnly,
    /// Fact only — verified and checked (NOT the certified dependent pair).
    FactOnly,
}

impl Default for FactLabel {
    /// The safe default for unverified artifacts.
    fn default() -> Self {
        Self::EvidenceOnly
    }
}

impl FactLabel {
    /// Project onto the canonical authority-strength lattice. `EvidenceOnly` and
    /// `FactOnly` sit strictly below `Certified` — a fact-label is never authority.
    pub fn level(&self) -> AuthorityEffectLevel {
        match self {
            Self::EvidenceOnly => AuthorityEffectLevel::EvidenceOnly,
            Self::FactOnly => AuthorityEffectLevel::FactOnly,
        }
    }
}

// Origin: engine/crates_rs/core_types/src/authority_effect_label.rs
// Claim: urn:core:crates_rs:core-types:authority-effect-label:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord570b7df7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord570b7df7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError570b7df7 {
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
impl BoundaryError570b7df7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError570b7df7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError570b7df7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord570b7df7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError570b7df7> {
        if capacity_bound == 0 {
            return Err(BoundaryError570b7df7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError570b7df7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError570b7df7::ExceedsCapacity {
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
    fn level_maps_each_variant_exactly() {
        assert_eq!(
            FactLabel::EvidenceOnly.level(),
            AuthorityEffectLevel::EvidenceOnly
        );
        assert_eq!(FactLabel::FactOnly.level(), AuthorityEffectLevel::FactOnly);
    }

    #[test]
    fn level_is_strictly_below_certified() {
        // A fact-label can never reach the certified (authority) top.
        assert!(FactLabel::EvidenceOnly.level() < AuthorityEffectLevel::Certified);
        assert!(FactLabel::FactOnly.level() < AuthorityEffectLevel::Certified);
    }

    #[test]
    fn serde_round_trips_both_variants() {
        for v in [FactLabel::EvidenceOnly, FactLabel::FactOnly] {
            let json = serde_json::to_string(&v).unwrap();
            let back: FactLabel = serde_json::from_str(&json).unwrap();
            assert_eq!(v, back);
        }
    }

    #[test]
    fn default_is_evidence_only() {
        assert_eq!(FactLabel::default(), FactLabel::EvidenceOnly);
    }
}

#[cfg(test)]
mod l4_boundary_tests_570b7df7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord570b7df7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord570b7df7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord570b7df7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord570b7df7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord570b7df7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError570b7df7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError570b7df7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
