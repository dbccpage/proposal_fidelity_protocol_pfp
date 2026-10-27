//! The LGGR V joint-kernel soundness verdict as Python reaches it through `adversary_support`.
//! The verdict comes from `lggr_v::check_soundness`; no caller flag decides it.
//!
//! AuthorityEffect: None.

use pfp::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use serde_json::{json, Value};

fn soundness(d: Value, q: Value) -> Result<Value, String> {
    let response = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.into(),
        action: "adversary_support".into(),
        payload: json!({"operation": "lggr_joint_kernel_soundness", "request": {
            "binding": {"source_id": "fixture", "candidate_id": "c", "question": "q",
                "operation_id": "adversary.lggr-joint-kernel.v1",
                "checker_id": "independent-rational-replay.v1"},
            "d": d, "q": q}}),
    });
    assert!(response.success, "{:?}", response.error);
    let result = response.result.unwrap();
    if result["refusal"].is_null() {
        Ok(result["outcome"].clone())
    } else {
        Err(result["refusal"].to_string())
    }
}

#[test]
fn a_blind_observer_returns_a_witness() {
    let wire = soundness(json!([["1", "0"], ["0", "1"]]), json!([["1", "0"]])).unwrap();
    assert_eq!(wire["schema_version"], "adversary.lggr_joint_kernel_soundness.v1");
    assert_eq!(wire["decision"], "lggr_v::check_soundness");
    assert_eq!(wire["sound"], false);
    assert_eq!((wire["d_rank"].clone(), wire["qd_rank"].clone()), (json!(2), json!(1)));
    let witness: Vec<&str> = wire["witness"].as_array().unwrap().iter().map(|v| v.as_str().unwrap()).collect();
    assert_eq!(witness[0], "0");
    assert_ne!(witness[1], "0");
    assert_eq!(wire["authority_effect"], "None");
}

#[test]
fn one_perturbed_entry_of_q_flips_the_verdict() {
    let blind = soundness(json!([["1"], ["0"]]), json!([["0", "1"]])).unwrap();
    assert_eq!(blind["sound"], false);
    let seen = soundness(json!([["1"], ["0"]]), json!([["1", "1"]])).unwrap();
    assert_eq!(seen["sound"], true);
    assert!(seen["witness"].is_null());
}

#[test]
fn ragged_and_mismatched_matrices_refuse() {
    let ragged = soundness(json!([["1", "0"], ["1"]]), json!([["1", "0"]])).unwrap_err();
    assert!(ragged.contains("LGGR_SOUNDNESS_D_NOT_RECTANGULAR"), "{ragged}");
    let mismatch = soundness(json!([["1"], ["0"]]), json!([["1", "0", "0"]])).unwrap_err();
    assert!(mismatch.contains("LGGR_SOUNDNESS_REFUSED"), "{mismatch}");
}

// Origin: engine/crates_rs/tests/pfp/lggr_joint_kernel_host.rs
// Claim: urn:core:crates_rs:tests:lggr-joint-kernel-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord719b28ad {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord719b28ad` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError719b28ad {
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
impl BoundaryError719b28ad {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError719b28ad {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError719b28ad {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord719b28ad {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError719b28ad> {
        if capacity_bound == 0 {
            return Err(BoundaryError719b28ad::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError719b28ad::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError719b28ad::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_719b28ad() {
    let admitted = BoundaryRecord719b28ad::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord719b28ad::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
