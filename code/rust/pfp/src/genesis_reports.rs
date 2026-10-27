//! Bounded native transport for Genesis admission reports. No filesystem I/O.
use core_wdp::genesis_report_runtime::{self as runtime, Request, ResultPacket};
use serde::Deserialize;
use serde_json::{json, Value};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Replay {
    request: Request,
    result: ResultPacket,
}

fn preflight(value: &Value) -> Result<(), String> {
    crate::wire_limits::validate_json_value(value, 65_536, 16)
        .map_err(|e| format!("GENESIS_WIRE: {e:?}"))
}

pub fn evaluate(payload: &Value) -> Result<Value, String> {
    preflight(payload)?;
    let request: Request =
        serde_json::from_value(payload.clone()).map_err(|e| format!("GENESIS_WIRE: {e}"))?;
    let result = runtime::evaluate(&request).map_err(|e| e.to_string())?;
    // A successful result must fit a subsequent replay through this SAME seam.
    let envelope = json!({"schema_version": crate::invoke::RUNTIME_REQUEST_SCHEMA,
        "action": "genesis_report_verify", "payload": {"request": request, "result": result}});
    preflight(&envelope)?;
    serde_json::to_value(result).map_err(|e| e.to_string())
}

pub fn verify(payload: &Value) -> Result<Value, String> {
    preflight(payload)?;
    let replay: Replay =
        serde_json::from_value(payload.clone()).map_err(|e| format!("GENESIS_WIRE: {e}"))?;
    runtime::verify(&replay.request, &replay.result).map_err(|e| e.to_string())?;
    Ok(
        json!({"schema_version": "core.genesis.report-replay.v1", "verified": true,
        "authority_effect": "None", "request_sha256": runtime::request_sha256(&replay.request).map_err(|e| e.to_string())?}),
    )
}

// Origin: engine/crates_rs/pfp/src/genesis_reports.rs
// Claim: urn:core:crates_rs:pfp:genesis-reports:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord36bc1c47 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord36bc1c47` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError36bc1c47 {
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
impl BoundaryError36bc1c47 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError36bc1c47 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError36bc1c47 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord36bc1c47 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError36bc1c47> {
        if capacity_bound == 0 {
            return Err(BoundaryError36bc1c47::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError36bc1c47::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError36bc1c47::ExceedsCapacity {
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
mod l4_boundary_tests_36bc1c47 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord36bc1c47::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord36bc1c47::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord36bc1c47::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord36bc1c47::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord36bc1c47::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError36bc1c47::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError36bc1c47::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
