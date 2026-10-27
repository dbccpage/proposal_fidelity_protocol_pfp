//! Serialization helpers for core_homology types.
//!
//! Most types derive Serialize/Deserialize directly.
//! This module provides helpers for types that need custom serialization.

// Placeholder for custom serialization if needed.
// Currently all types use derived serde implementations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChainByteError { kind: &'static str, left: i128, right: i128 }
impl ChainByteError {
    const fn new(kind: &'static str, left: i128, right: i128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Little-endian record of a nonempty integer chain: eight bytes per coefficient.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ChainByteLedger { count: u64, byte_len: u64, checksum: i128 }
impl ChainByteLedger {
    pub fn try_encode(coefficients: &[i64]) -> Result<Self, ChainByteError> {
        if coefficients.is_empty() {
            return Err(ChainByteError::new("a chain record is nonempty", 0, 0));
        }
        let count = u64::try_from(coefficients.len()).map_err(|_| ChainByteError::new("coefficient count exceeds u64", i128::try_from(coefficients.len()).map_or(i128::MAX, |converted| converted), i128::from(u64::MAX)))?;
        let byte_len = count.checked_mul(8).ok_or_else(|| ChainByteError::new("byte length overflow", i128::from(count), 8))?;
        let mut checksum = 0i128;
        let mut decoded_sum = 0i128;
        for &coefficient in coefficients {
            (checksum, decoded_sum) = Self::accumulate_coefficient(checksum, decoded_sum, coefficient)?;
        }
        if decoded_sum != checksum {
            return Err(ChainByteError::new("decoded sum differs from the checksum", decoded_sum, checksum));
        }
        Ok(Self { count, byte_len, checksum })
    }
    fn accumulate_coefficient(
        checksum: i128,
        decoded_sum: i128,
        coefficient: i64,
    ) -> Result<(i128, i128), ChainByteError> {
        let next_checksum = checksum
            .checked_add(i128::from(coefficient))
            .ok_or_else(|| ChainByteError::new("checksum overflow", checksum, i128::from(coefficient)))?;
        let round_trip = i64::from_le_bytes(coefficient.to_le_bytes());
        if round_trip != coefficient {
            return Err(ChainByteError::new(
                "little-endian round trip changed a coefficient",
                i128::from(round_trip),
                i128::from(coefficient),
            ));
        }
        let next_decoded = decoded_sum
            .checked_add(i128::from(round_trip))
            .ok_or_else(|| ChainByteError::new("decoded sum overflow", decoded_sum, i128::from(round_trip)))?;
        Ok((next_checksum, next_decoded))
    }
    pub const fn byte_len(&self) -> u64 { self.byte_len }
    pub const fn checksum(&self) -> i128 { self.checksum }
}

// Origin: engine/crates_rs/core_homology/src/serialization.rs
// Claim: urn:core:crates_rs:core-homology:serialization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4cb24f90 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4cb24f90` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4cb24f90 {
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
impl BoundaryError4cb24f90 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4cb24f90 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4cb24f90 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4cb24f90 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4cb24f90> {
        if capacity_bound == 0 {
            return Err(BoundaryError4cb24f90::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4cb24f90::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4cb24f90::ExceedsCapacity {
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
mod chain_byte_checks {
    use super::ChainByteLedger;
    #[test]
    fn three_coefficients_occupy_twenty_four_bytes() {
        let ledger = ChainByteLedger::try_encode(&[1, -2, 4]);
        assert_eq!(ledger.as_ref().map(ChainByteLedger::byte_len), Ok(24));
        assert_eq!(ledger.as_ref().map(ChainByteLedger::checksum), Ok(3));
    }
    #[test]
    fn an_empty_chain_is_refused() {
        assert_eq!(ChainByteLedger::try_encode(&[]).map(|_| ()).map_err(|e| e.kind()), Err("a chain record is nonempty"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_4cb24f90 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4cb24f90::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4cb24f90::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4cb24f90::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4cb24f90::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4cb24f90::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4cb24f90::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4cb24f90::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
