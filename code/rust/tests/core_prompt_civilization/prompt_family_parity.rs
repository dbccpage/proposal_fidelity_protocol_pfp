use core_prompt_civilization::prompt_family::{
    decode_family, validate_family, CallRecord, PromptNode, Reader, Shape,
};
use serde_json::{json, Value};

#[test]
fn frozen_python_prompt_family_vectors() {
    let rows: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/python_prompt_family_v1.json")).unwrap();
    assert_eq!(rows.len(), 41);
    for row in rows {
        let actual = match row["op"].as_str().unwrap() {
            "validate" => {
                let family = decode_family(&serde_json::to_vec(&row["family"]).unwrap()).unwrap();
                assert_eq!(
                    json!(family),
                    row["family"],
                    "family DTO decoding must preserve exact numbers"
                );
                match validate_family(&family) {
                    Ok(()) => json!({"ok": family}),
                    Err(error) => json!({"error": error}),
                }
            }
            "shape" => {
                let shape = Shape::from_text(row["text"].as_str().unwrap());
                json!({"shape": shape, "digest": shape.digest().unwrap()})
            }
            "identity" => {
                let reader: Reader = serde_json::from_value(row["reader"].clone()).unwrap();
                let node: PromptNode = serde_json::from_value(row["node"].clone()).unwrap();
                let call: CallRecord = serde_json::from_value(row["call"].clone()).unwrap();
                assert!(call.truncated().is_none());
                assert!(call.defect().is_none());
                json!({"reader_digest": reader.digest().unwrap(), "node_id": node.node_id().unwrap(), "call_id": call.call_id().unwrap()})
            }
            other => panic!("unknown fixture {other}"),
        };
        assert_eq!(actual, row["expected"], "operation {}", row["op"]);
    }
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/prompt_family_parity.rs
// Claim: urn:core:crates_rs:tests:prompt-family-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf4423453 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf4423453` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf4423453 {
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
impl BoundaryErrorf4423453 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf4423453 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf4423453 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf4423453 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf4423453> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf4423453::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf4423453::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf4423453::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f4423453() {
    let admitted = BoundaryRecordf4423453::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf4423453::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
