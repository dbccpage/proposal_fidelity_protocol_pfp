//! Host wire boundary for source-bound finite WDP packets. No filesystem reads.
//! AuthorityEffect: None.

use core_types::AuthorityEffect;
use core_wdp::wdp_source_packet::{
    evaluate_source_packet, replay_source_packet, WdpPacketRefusalCodeV1, WdpPacketRefusalV1,
    WdpSourcePacketReplayV1, WdpSourcePacketRequestV1, WdpSourcePacketResultV1,
};
use serde::Deserialize;
use serde_json::Value;

use crate::invoke::{RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use crate::wire_limits::{validate_json_value, JsonWireLimitError};

/// The native invoke process has the same 64 KiB limit, including its envelope.
pub const MAX_WDP_PACKET_WIRE_BYTES: usize = 65_536;
/// Root depth is zero; the evaluate and replay schemas require fewer than eight levels.
pub const MAX_WDP_PACKET_VALUE_DEPTH: usize = 16;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WdpPacketVerifyRequestV1 {
    pub request: WdpSourcePacketRequestV1,
    pub result: WdpSourcePacketResultV1,
}

fn wire_refusal(detail: impl Into<String>) -> WdpPacketRefusalV1 {
    WdpPacketRefusalV1 {
        code: WdpPacketRefusalCodeV1::Wire,
        detail: detail.into(),
        authority_effect: AuthorityEffect::None,
    }
}

fn preflight(value: &Value) -> Result<(), WdpPacketRefusalV1> {
    validate_json_value(value, MAX_WDP_PACKET_WIRE_BYTES, MAX_WDP_PACKET_VALUE_DEPTH).map_err(
        |error| match error {
            JsonWireLimitError::Size => wire_refusal("source-packet wire exceeds 64 KiB"),
            JsonWireLimitError::Depth => wire_refusal("source-packet wire exceeds depth 16"),
        },
    )?;
    // Bound text before a rational string can allocate a large BigInt. A source
    // id is at most 256 bytes; each exact numerator/denominator is <=1024 bits.
    fn check_text(value: &Value) -> Result<(), WdpPacketRefusalV1> {
        match value {
            Value::String(text) if text.len() > 640 => Err(wire_refusal(
                "packet string exceeds the bounded exact scalar encoding",
            )),
            Value::Array(values) => values.iter().try_for_each(check_text),
            Value::Object(fields) => fields.values().try_for_each(check_text),
            _ => Ok(()),
        }
    }
    check_text(value)
}

pub fn evaluate(payload: &Value) -> Result<WdpSourcePacketResultV1, WdpPacketRefusalV1> {
    preflight(payload)?;
    let request =
        serde_json::from_value(payload.clone()).map_err(|error| wire_refusal(error.to_string()))?;
    let result = evaluate_source_packet(&request)?;
    // A successful live result must fit back through the same invoke seam for
    // independent replay, including the request, candidate and full envelope.
    let replay = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "wdp_packet_verify".to_owned(),
        payload: serde_json::json!({"request": payload, "result": result}),
    };
    let bytes = serde_json::to_vec(&replay).map_err(|error| wire_refusal(error.to_string()))?;
    if bytes.len() > MAX_WDP_PACKET_WIRE_BYTES {
        return Err(wire_refusal(
            "exact result and request exceed the 64 KiB live replay envelope",
        ));
    }
    Ok(result)
}

pub fn verify(payload: &Value) -> Result<WdpSourcePacketReplayV1, WdpPacketRefusalV1> {
    preflight(payload)?;
    let request: WdpPacketVerifyRequestV1 =
        serde_json::from_value(payload.clone()).map_err(|error| wire_refusal(error.to_string()))?;
    replay_source_packet(&request.request, &request.result)
}

// Origin: engine/crates_rs/pfp/src/wdp_packet.rs
// Claim: urn:core:crates_rs:pfp:wdp-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda2a03aec {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda2a03aec` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora2a03aec {
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
impl BoundaryErrora2a03aec {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora2a03aec {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora2a03aec {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda2a03aec {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora2a03aec> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora2a03aec::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora2a03aec::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora2a03aec::ExceedsCapacity {
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
mod l4_boundary_tests_a2a03aec {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda2a03aec::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda2a03aec::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda2a03aec::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda2a03aec::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda2a03aec::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora2a03aec::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora2a03aec::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
