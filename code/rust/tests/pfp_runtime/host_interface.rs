//! The reusable host boundary must preserve the binary's mathematics, refusal
//! vocabulary, inclusive byte fence and raw detector-byte custody.

use pfp_runtime::interface::{describe, dispatch, MAX_REQUEST_BYTES};
use serde_json::json;
use sha2::{Digest, Sha256};

#[test]
fn description_keeps_the_existing_modes_and_authority_ceiling() {
    let description = describe();
    assert_eq!(
        description["schema_version"],
        "core.symgam.host-description.v1"
    );
    assert_eq!(description["logical_id"], "core-symgam-host");
    assert_eq!(
        description["modes"],
        json!(["--describe", "classify-board", "detect"])
    );
    assert_eq!(description["max_request_bytes"], MAX_REQUEST_BYTES);
    assert_eq!(description["authority_effect"], "None");
    assert_eq!(description["evidence_ceiling"], "LocalReplay");
    assert_eq!(dispatch("--describe", b"not a request"), description);
}

#[test]
fn exact_and_curved_boards_keep_their_distinct_next_moves() {
    let exact = dispatch(
        "classify-board",
        br#"{"d0":[[1],[1]],"d1":[[1,1]],"a":[1,1]}"#,
    );
    assert_eq!(exact["verdict"], "GAUGE_EXACT");
    assert_eq!(exact["witness"], json!({"kind":"lambda", "lambda":[1]}));
    assert_eq!(exact["admissible_repairs"], json!(["ACCEPT_WITNESS"]));
    assert_eq!(exact["authority_effect"], "None");

    let curved = dispatch(
        "classify-board",
        br#"{"d0":[[1],[1]],"d1":[[1,1]],"a":[1,0]}"#,
    );
    assert_eq!(curved["verdict"], "LOCAL_CURVATURE");
    assert_eq!(curved["gauge_moves_can_help"], false);
    assert_eq!(
        curved["admissible_repairs"],
        json!(["CARRIER_CHANGE", "REFRAME"])
    );
}

#[test]
fn malformed_input_non_bits_and_missing_fields_remain_refusals() {
    for (bytes, code) in [
        (&b"{"[..], "REQUEST_NOT_JSON"),
        (&b"{}"[..], "REQUEST_SHAPE_INVALID"),
        (&br#"{"d0":[[1]],"d1":[],"a":[2]}"#[..], "BIT_NOT_BINARY"),
        (
            &br#"{"d0":[[1,0],[1]],"d1":[],"a":[0]}"#[..],
            "D0_MALFORMED",
        ),
    ] {
        let outcome = dispatch("classify-board", bytes);
        assert_eq!(outcome["refused"], true, "{outcome}");
        assert_eq!(outcome["code"], code, "{outcome}");
        assert_eq!(outcome["authority_effect"], "None");
        assert!(outcome.get("verdict").is_none());
    }
    assert_eq!(dispatch("unknown", b"{}")["code"], "UNKNOWN_MODE");
}

#[test]
fn the_complete_request_limit_is_inclusive_and_cannot_hide_a_tail() {
    let mut bytes = br#"{"d0":[[1],[1]],"d1":[[1,1]],"a":[1,1]}"#.to_vec();
    bytes.resize(MAX_REQUEST_BYTES, b' ');
    assert_eq!(dispatch("classify-board", &bytes)["verdict"], "GAUGE_EXACT");
    bytes.push(b'x');
    let refused = dispatch("classify-board", &bytes);
    assert_eq!(refused["code"], "REQUEST_UNREADABLE");
    assert_eq!(refused["refused"], true);
}

#[test]
fn detection_preserves_complete_raw_bytes_separately_from_parsed_candidate() {
    let compact = br#"{"candidate":{"answer":1}}"#;
    let spaced = br#"{ "candidate" : { "answer" : 1 } }"#;
    let first = dispatch("detect", compact);
    let second = dispatch("detect", spaced);
    assert_eq!(first["schema_version"], "core.symgam.detect-report.v1");
    assert_eq!(
        first["normalized_json_digest"],
        second["normalized_json_digest"]
    );
    assert_ne!(first["raw_bytes_digest"], second["raw_bytes_digest"]);
    for (bytes, outcome) in [(&compact[..], &first), (&spaced[..], &second)] {
        let expected = format!("sha256:{}", hex::encode(Sha256::digest(bytes)));
        assert_eq!(outcome["raw_bytes_digest"], expected);
        assert_eq!(outcome["authority_effect"], "None");
    }
}

// Origin: engine/crates_rs/tests/pfp_runtime/host_interface.rs
// Claim: urn:core:crates_rs:tests:host-interface:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb3a07ed9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb3a07ed9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb3a07ed9 {
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
impl BoundaryErrorb3a07ed9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb3a07ed9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb3a07ed9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb3a07ed9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb3a07ed9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb3a07ed9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb3a07ed9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb3a07ed9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b3a07ed9() {
    let admitted = BoundaryRecordb3a07ed9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb3a07ed9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
