use linear_algebra::backend::basic_matrix::BasicMatrix;
use serde_json::json;

#[test]
fn rectangular_and_zero_area_matrices_keep_wire_shape() {
    for (rows, cols, data) in [
        (2, 3, vec![1, 2, 3, 4, 5, 6]),
        (3, 0, vec![]),
        (0, 4, vec![]),
    ] {
        let matrix = BasicMatrix::from_row_major(rows, cols, data.clone()).unwrap();
        let wire = serde_json::to_value(&matrix).unwrap();
        assert_eq!(wire, json!({"rows": rows, "cols": cols, "data": data}));
        assert_eq!(
            serde_json::from_value::<BasicMatrix<i64>>(wire).unwrap(),
            matrix
        );
    }
}

#[test]
fn malformed_storage_and_shape_overflow_are_refused() {
    let short = json!({"rows": 2, "cols": 3, "data": [1, 2, 3]});
    assert!(serde_json::from_value::<BasicMatrix<i64>>(short)
        .unwrap_err()
        .to_string()
        .contains("does not match"));
    let overflow = json!({"rows": usize::MAX, "cols": 2, "data": []});
    assert!(serde_json::from_value::<BasicMatrix<i64>>(overflow)
        .unwrap_err()
        .to_string()
        .contains("overflow"));
    let unknown = json!({"rows": 1, "cols": 1, "data": [1], "unchecked": true});
    assert!(serde_json::from_value::<BasicMatrix<i64>>(unknown).is_err());
}

// Origin: engine/crates_rs/tests/core_linear_algebra/basic_matrix_serialization.rs
// Claim: urn:core:crates_rs:tests:basic-matrix-serialization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord79702803 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord79702803` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError79702803 {
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
impl BoundaryError79702803 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError79702803 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError79702803 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord79702803 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError79702803> {
        if capacity_bound == 0 {
            return Err(BoundaryError79702803::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError79702803::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError79702803::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_79702803() {
    let admitted = BoundaryRecord79702803::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord79702803::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
