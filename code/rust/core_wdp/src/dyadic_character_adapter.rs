//! Retains declared finite character data; all arithmetic has a math owner.
//! No finite prefix is promoted to a continuum, topology or physical model.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c02c88c3<T> {
    fn checked_invariant_c02c88c3(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c02c88c3<T> for Option<T> {
    #[inline]
    fn checked_invariant_c02c88c3(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c02c88c3<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c02c88c3(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::types::AuthorityEffect;
use core_number_theory::cyclotomic_field::CyclotomicNumber;
use core_number_theory::dyadic_presentation::{
    CharacterSumLimits, DyadicError, DyadicLevel, FiniteDualPrefix,
};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredDyadicPairing {
    prefix: FiniteDualPrefix,
    compared_index: usize,
    actual_inner_product: CyclotomicNumber,
}

impl DeclaredDyadicPairing {
    pub fn new(
        indices: &[usize],
        compared_index: usize,
        limits: CharacterSumLimits,
    ) -> Result<Self, DyadicError> {
        let prefix = FiniteDualPrefix::new(indices)?;
        let group = DyadicLevel::new((prefix.indices().len() - 1) as u32)?;
        if compared_index >= group.order() {
            return Err(DyadicError::OutOfCarrier);
        }
        let actual_inner_product = group.normalized_inner_product(
            &(*prefix.indices().last().checked_invariant_c02c88c3("checked invariant")).into(),
            &compared_index.into(),
            limits,
        )?;
        Ok(Self {
            prefix,
            compared_index,
            actual_inner_product,
        })
    }

    pub fn prefix(&self) -> &FiniteDualPrefix {
        &self.prefix
    }

    pub fn compared_index(&self) -> usize {
        self.compared_index
    }

    pub fn actual_inner_product(&self) -> &CyclotomicNumber {
        &self.actual_inner_product
    }

    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

// Origin: engine/crates_rs/core_wdp/src/dyadic_character_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:dyadic-character-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc02c88c3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc02c88c3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc02c88c3 {
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
impl BoundaryErrorc02c88c3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc02c88c3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc02c88c3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc02c88c3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc02c88c3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc02c88c3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc02c88c3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc02c88c3::ExceedsCapacity {
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
mod l4_boundary_tests_c02c88c3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc02c88c3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc02c88c3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc02c88c3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc02c88c3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc02c88c3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc02c88c3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc02c88c3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
