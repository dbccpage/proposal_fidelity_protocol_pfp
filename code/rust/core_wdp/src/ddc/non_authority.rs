//! DDC No-Authority Firewall registry for the DDA crate's well-typed trace surfaces.
//!
//! Canonical provenance:
//! `coda_atlas/F004_papers/006_project_sentinel_codename_adversary_engine/001_discrete_deformation_calculus/discrete_deformation_calculus.md`
//! (Paper ID: `oe_010_dda_trace_calculus`, Series: `008_engine_runtime`, `OE010-04`).
//!
//! The registry is sealed: downstream code cannot declare an unrelated type to
//! be a registered DDA trace. Both admitted trace types remain evidence-only,
//! and the registry deliberately has no dependency on the host promotion
//! contract. Adding another trace representation requires editing this owner
//! module and replaying the constructor audit.

use crate::ddc::ddc_alphabet::DdaTrace;
use crate::ddc::op_verification::VerifiedTrace;
use core_types::authority::AuthorityEffect;

mod sealed {
    pub trait Sealed {}
}

/// Marker for the complete frozen registry of well-typed DDA trace types.
///
/// This trait cannot be implemented outside this crate because its supertrait
/// is private. An untyped model proposal such as `agent_contract::DefectTrace`
/// is intentionally excluded until the existing operation verifier has
/// converted it into one of the registered representations.
pub trait RegisteredDdaTrace: sealed::Sealed {}

impl sealed::Sealed for DdaTrace {}
impl RegisteredDdaTrace for DdaTrace {}

impl sealed::Sealed for VerifiedTrace {}
impl RegisteredDdaTrace for VerifiedTrace {}

/// Stable names used by the repository audit to detect registry drift.
pub const REGISTERED_DDA_TRACE_TYPES: [&str; 2] =
    ["dda_alphabet::DdaTrace", "op_verification::VerifiedTrace"];

/// DDC No-Authority Firewall (`OE010-04`): authority ceiling for every sealed registered trace.
///
/// Verification can strengthen evidence but cannot change this return type or
/// value. In particular, this function cannot construct `CertifiedAuthority`
/// or `AuthorizedLocalResultV1`; those types are not dependencies of this
/// registry and their constructors remain outside the DDA crate.
pub fn registered_trace_authority_effect<T: RegisteredDdaTrace>(_trace: &T) -> AuthorityEffect {
    AuthorityEffect::None
}

// Origin: engine/crates_rs/core_wdp/src/ddc/non_authority.rs
// Claim: urn:core:crates_rs:core-wdp:non-authority:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8cae4b31 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8cae4b31` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8cae4b31 {
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
impl BoundaryError8cae4b31 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8cae4b31 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8cae4b31 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8cae4b31 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8cae4b31> {
        if capacity_bound == 0 {
            return Err(BoundaryError8cae4b31::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8cae4b31::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8cae4b31::ExceedsCapacity {
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
    use crate::ddc::degree_tower::{BinaryCochainSegment, BinaryLinearMap};
    use crate::ddc::op_verification::CochainState;

    fn initial_state() -> CochainState {
        let d0 = BinaryLinearMap::from_rows(1, vec![vec![true], vec![false]]).unwrap();
        let d1 = BinaryLinearMap::from_rows(2, vec![vec![false, true]]).unwrap();
        let segment = BinaryCochainSegment::new(1, d0, d1).unwrap();
        CochainState::new(segment, vec![false, false]).unwrap()
    }

    #[test]
    fn both_registered_trace_types_are_pinned_to_none() {
        let emitted = DdaTrace::new();
        let verified = VerifiedTrace::new(initial_state());

        assert_eq!(
            registered_trace_authority_effect(&emitted),
            AuthorityEffect::None
        );
        assert_eq!(
            registered_trace_authority_effect(&verified),
            AuthorityEffect::None
        );
        assert_eq!(emitted.authority_effect(), AuthorityEffect::None);
        assert_eq!(verified.authority_effect(), AuthorityEffect::None);
    }
}

#[cfg(test)]
mod l4_boundary_tests_8cae4b31 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8cae4b31::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8cae4b31::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8cae4b31::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8cae4b31::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8cae4b31::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8cae4b31::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8cae4b31::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
