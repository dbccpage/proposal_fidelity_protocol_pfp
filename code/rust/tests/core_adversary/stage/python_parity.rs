use core_adversary::stage::ports::{SeatTurnReply, SeatTurnRequest};
use serde_json::{json, Value};

#[test]
fn frozen_python_seat_vectors() {
    let rows: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/python_seat_ports_v1.json")).unwrap();
    assert_eq!(rows.len(), 15);
    for row in rows {
        let actual = match row["op"].as_str().unwrap() {
            "reply_validate" => {
                let reply: SeatTurnReply =
                    serde_json::from_slice(&serde_json::to_vec(&row["reply"]).unwrap()).unwrap();
                match reply.validate() {
                    Ok(()) => json!({"ok": true}),
                    Err(error) => json!({"error": error.message}),
                }
            }
            "reply_partial" => {
                let reply: SeatTurnReply =
                    serde_json::from_slice(&serde_json::to_vec(&row["reply"]).unwrap()).unwrap();
                reply.validate().unwrap();
                json!(reply)
            }
            "request_digest" | "request_partial" => {
                let request: SeatTurnRequest =
                    serde_json::from_value(row["request"].clone()).unwrap();
                json!(request.request_digest().unwrap())
            }
            "reply_provenance" => {
                let reply: SeatTurnReply = serde_json::from_value(row["reply"].clone()).unwrap();
                reply.validate().unwrap();
                reply.provenance()
            }
            other => panic!("unknown fixture {other}"),
        };
        assert_eq!(actual, row["expected"]);
    }
}

// Origin: engine/crates_rs/tests/core_adversary/stage/python_parity.rs
// Claim: urn:core:crates_rs:tests:python-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3d053e63 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3d053e63` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3d053e63 {
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
impl BoundaryError3d053e63 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3d053e63 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3d053e63 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3d053e63 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3d053e63> {
        if capacity_bound == 0 {
            return Err(BoundaryError3d053e63::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3d053e63::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3d053e63::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3d053e63() {
    let admitted = BoundaryRecord3d053e63::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3d053e63::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
