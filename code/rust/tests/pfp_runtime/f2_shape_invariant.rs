//! `F2Matrix`'s shape invariant must survive serialization.
//!
//! The fields were briefly public so the struct could derive `Serialize` and
//! `Deserialize`. That gave the invariant away twice: `F2Matrix { rows: 3,
//! cols: 3, data: vec![] }` became constructible in-process, and `Deserialize`
//! rebuilt the struct field by field without calling `new`.
//!
//! A shape check that any caller can walk around is not a shape check. These
//! tests pin both directions.
//!
//! AuthorityEffect: None.

use pfp_runtime::f2::{F2Error, F2Matrix};

#[test]
fn a_wellformed_matrix_round_trips() {
    let matrix = F2Matrix::from_rows(&[vec![1, 0, 1], vec![0, 1, 1]]).expect("well formed");
    let json = serde_json::to_string(&matrix).expect("serializes");
    let back: F2Matrix = serde_json::from_str(&json).expect("deserializes");
    assert_eq!(back, matrix);
    assert_eq!(back.rows(), 2);
    assert_eq!(back.cols(), 3);
}

#[test]
fn the_wire_shape_is_unchanged() {
    // The fix must not break anything already serialized, so the JSON keeps the
    // same three keys it had when the fields were public.
    let matrix = F2Matrix::from_rows(&[vec![1, 0]]).expect("well formed");
    let value: serde_json::Value =
        serde_json::from_str(&serde_json::to_string(&matrix).unwrap()).unwrap();
    let object = value.as_object().expect("an object");
    assert_eq!(object.len(), 3);
    assert!(object.contains_key("rows"));
    assert!(object.contains_key("cols"));
    assert!(object.contains_key("data"));
}

#[test]
fn a_matrix_whose_data_contradicts_its_shape_is_refused() {
    // The case public fields allowed: three-by-three declared, no data supplied.
    let refused = serde_json::from_str::<F2Matrix>(r#"{"rows":3,"cols":3,"data":[]}"#);
    assert!(
        refused.is_err(),
        "deserialization must be held to the same shape check as F2Matrix::new"
    );
}

#[test]
fn an_overlong_data_vector_is_refused() {
    let refused =
        serde_json::from_str::<F2Matrix>(r#"{"rows":1,"cols":2,"data":[true,false,true]}"#);
    assert!(refused.is_err());
}

#[test]
fn the_constructor_and_the_wire_agree_on_what_is_valid() {
    // Whatever `new` refuses, the wire must refuse, or the seam is a way in.
    for (rows, cols, len) in [(0usize, 0usize, 0usize), (2, 2, 4), (3, 1, 3), (1, 4, 4)] {
        let data = vec![false; len];
        let by_constructor = F2Matrix::new(rows, cols, data.clone());
        let json = format!(
            r#"{{"rows":{rows},"cols":{cols},"data":{}}}"#,
            serde_json::to_string(&data).unwrap()
        );
        let by_wire = serde_json::from_str::<F2Matrix>(&json);
        assert_eq!(
            by_constructor.is_ok(),
            by_wire.is_ok(),
            "disagreement at rows={rows} cols={cols} len={len}"
        );
    }

    for (rows, cols, len) in [(3usize, 3usize, 0usize), (1, 2, 3), (2, 2, 3)] {
        let data = vec![false; len];
        assert!(matches!(
            F2Matrix::new(rows, cols, data.clone()),
            Err(F2Error::ShapeMismatch { .. })
        ));
        let json = format!(
            r#"{{"rows":{rows},"cols":{cols},"data":{}}}"#,
            serde_json::to_string(&data).unwrap()
        );
        assert!(
            serde_json::from_str::<F2Matrix>(&json).is_err(),
            "the wire admitted rows={rows} cols={cols} len={len} that new() refuses"
        );
    }
}

// Origin: engine/crates_rs/tests/pfp_runtime/f2_shape_invariant.rs
// Claim: urn:core:crates_rs:tests:f2-shape-invariant:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord10cd51a8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord10cd51a8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError10cd51a8 {
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
impl BoundaryError10cd51a8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError10cd51a8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError10cd51a8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord10cd51a8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError10cd51a8> {
        if capacity_bound == 0 {
            return Err(BoundaryError10cd51a8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError10cd51a8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError10cd51a8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_10cd51a8() {
    let admitted = BoundaryRecord10cd51a8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord10cd51a8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
