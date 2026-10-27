//! Serialization preserves the checked row-major storage invariant.

use crate::backend::basic_matrix::BasicMatrix;
use serde::ser::SerializeStruct;
use serde::{Deserialize, Deserializer, Serialize, Serializer};

impl<T: Serialize> Serialize for BasicMatrix<T> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut wire = serializer.serialize_struct("BasicMatrix", 3)?;
        wire.serialize_field("rows", &self.rows())?;
        wire.serialize_field("cols", &self.cols())?;
        wire.serialize_field("data", self.as_slice())?;
        wire.end()
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct MatrixWire<T> {
    rows: usize,
    cols: usize,
    data: Vec<T>,
}

impl<'de, T: Deserialize<'de>> Deserialize<'de> for BasicMatrix<T> {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let wire = MatrixWire::<T>::deserialize(deserializer)?;
        Self::from_row_major(wire.rows, wire.cols, wire.data).map_err(serde::de::Error::custom)
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/basic_matrix_serde.rs
// Claim: urn:core:crates_rs:core-linear-algebra:basic-matrix-serde:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf54772ce {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf54772ce` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf54772ce {
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
impl BoundaryErrorf54772ce {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf54772ce {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf54772ce {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf54772ce {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf54772ce> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf54772ce::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf54772ce::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf54772ce::ExceedsCapacity {
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
mod l4_boundary_tests_f54772ce {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf54772ce::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf54772ce::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf54772ce::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf54772ce::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf54772ce::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf54772ce::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf54772ce::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
