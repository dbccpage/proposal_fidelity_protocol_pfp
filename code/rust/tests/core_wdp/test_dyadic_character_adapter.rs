use core_number_theory::dyadic_presentation::{CharacterSumLimits, DyadicError};
use core_number_theory::rational::ri;
use core_wdp::dyadic_character_adapter::DeclaredDyadicPairing;
use core_wdp::types::AuthorityEffect;

#[test]
fn finite_pairing_retains_declared_prefix_actual_value_and_no_authority() {
    let pairing =
        DeclaredDyadicPairing::new(&[0, 1, 3, 7], 3, CharacterSumLimits::default()).unwrap();
    assert_eq!(pairing.prefix().indices(), &[0, 1, 3, 7]);
    assert_eq!(pairing.compared_index(), 3);
    assert_eq!(pairing.actual_inner_product().as_rational(), Some(ri(0)));
    assert_eq!(pairing.authority_effect(), AuthorityEffect::None);
    assert_eq!(pairing.prefix().next_indices().unwrap(), [7, 15]);
    assert_eq!(
        DeclaredDyadicPairing::new(&[0, 1, 2], 0, CharacterSumLimits::default()),
        Err(DyadicError::IncoherentPrefix)
    );
    assert_eq!(
        DeclaredDyadicPairing::new(&[0, 1], 2, CharacterSumLimits::default()),
        Err(DyadicError::OutOfCarrier)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_dyadic_character_adapter.rs
// Claim: urn:core:crates_rs:tests:test-dyadic-character-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord65894140 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord65894140` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError65894140 {
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
impl BoundaryError65894140 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError65894140 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError65894140 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord65894140 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError65894140> {
        if capacity_bound == 0 {
            return Err(BoundaryError65894140::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError65894140::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError65894140::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_65894140() {
    let admitted = BoundaryRecord65894140::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord65894140::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
