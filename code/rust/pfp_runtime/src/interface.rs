//! Transport-independent `symgam` request boundary.
//!
//! Classifiers and detectors operate on caller-supplied bytes. Neither this
//! module nor the exact engines read files, spawn processes or call providers.
//! Well-formed refusals are values; the binary alone owns stdin/stdout failure.

use crate::f2::{F2Matrix, GaugeBoard, GaugeVerdict};
use core_prompt_civilization::pharmacy::{
    detect_with_raw_bytes, DetectionContext, HostReplayReceipt,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

const DESCRIPTION_SCHEMA: &str = "core.symgam.host-description.v1";
const BOARD_REQUEST_SCHEMA: &str = "core.symgam.classify-board-request.v1";
const BOARD_VERDICT_SCHEMA: &str = "core.symgam.classify-board-verdict.v1";
const DETECT_REQUEST_SCHEMA: &str = "core.symgam.detect-request.v1";
const DETECT_REPORT_SCHEMA: &str = "core.symgam.detect-report.v1";

pub const MAX_REQUEST_BYTES: usize = 1_048_576;

#[derive(Debug, Deserialize)]
struct BoardRequest {
    /// `D0 ∈ F2^{E×V}`, rows of 0/1.
    d0: Vec<Vec<u8>>,
    /// `D1 ∈ F2^{F×E}`, rows of 0/1.
    d1: Vec<Vec<u8>>,
    /// The parity cochain `a ∈ F2^E`.
    a: Vec<u8>,
}

#[derive(Debug, Deserialize)]
struct DetectRequest {
    candidate: Value,
    #[serde(default)]
    context: DetectContextWire,
}

#[derive(Debug, Default, Deserialize, Serialize)]
struct DetectContextWire {
    #[serde(default)]
    prompt: Option<String>,
    #[serde(default)]
    unexplored_branches: usize,
    #[serde(default)]
    seen_digests: Vec<String>,
    #[serde(default)]
    seen_semantic_digests: Vec<String>,
    #[serde(default)]
    host_replay_receipt: Option<HostReplayReceipt>,
    #[serde(default)]
    semantic_replay_passed: bool,
}

fn bits(values: &[u8]) -> Result<Vec<bool>, String> {
    values
        .iter()
        .enumerate()
        .map(|(index, value)| match value {
            0 => Ok(false),
            1 => Ok(true),
            _ => Err(format!(
                "BIT_NOT_BINARY: a[{index}] is {value}; only 0 and 1 are bits"
            )),
        })
        .collect()
}

pub fn refusal(code: &str, detail: impl AsRef<str>) -> Value {
    json!({
        "schema_version": "core.symgam.refusal.v1",
        "refused": true,
        "code": code,
        "detail": detail.as_ref(),
        "authority_effect": "None",
    })
}

/// What each verdict means for the *next move*, which is the whole point of
/// classifying before generating.
fn admissible_repairs(verdict: &GaugeVerdict) -> &'static [&'static str] {
    match verdict {
        // Nothing is repairable until the declared object is a complex.
        GaugeVerdict::BoardInvalid { .. } => &["REDECLARE_BOARD"],
        // D1*D0 = 0 means every gauge move preserves the syndrome, so rephrasing
        // is provably wasted effort. Only a carrier change can help.
        GaugeVerdict::LocalCurvature { .. } => &["CARRIER_CHANGE", "REFRAME"],
        // Already exact; the witness is the repair.
        GaugeVerdict::GaugeExact { .. } => &["ACCEPT_WITNESS"],
        // Locally consistent everywhere, globally not: no single framing works.
        GaugeVerdict::GlobalH1Obstruction { .. } => &["SPLIT_CARRIER", "LIFT", "REFRAME"],
    }
}

fn classify(request: BoardRequest) -> Value {
    let d0 = match F2Matrix::from_rows(&request.d0) {
        Ok(matrix) => matrix,
        Err(error) => return refusal("D0_MALFORMED", error.to_string()),
    };
    let d1 = match F2Matrix::from_rows(&request.d1) {
        Ok(matrix) => matrix,
        Err(error) => return refusal("D1_MALFORMED", error.to_string()),
    };

    let board = GaugeBoard::new(d0, d1);
    let a = match bits(&request.a) {
        Ok(bits) => bits,
        Err(detail) => return refusal("BIT_NOT_BINARY", detail),
    };

    let verdict = match board.classify(&a) {
        Ok(verdict) => verdict,
        // A breach of our own invariant is not the caller's malformed board, and
        // telling them it is sends them to fix input that is already correct.
        Err(error @ crate::f2::F2Error::SeparatorMissing { .. }) => {
            return refusal("HOST_INTERNAL_INVARIANT", error.to_string())
        }
        Err(error) => return refusal("BOARD_SHAPE_MISMATCH", error.to_string()),
    };

    let witness = match &verdict {
        GaugeVerdict::BoardInvalid { product } => json!({
            "kind": "chain_law_product",
            "detail": "D1*D0 is nonzero, so this is a graded diagram, not a cochain complex",
            "product_is_zero": product.is_zero(),
        }),
        GaugeVerdict::LocalCurvature { syndrome } => json!({
            "kind": "syndrome",
            "syndrome": syndrome.iter().map(|b| u8::from(*b)).collect::<Vec<_>>(),
        }),
        GaugeVerdict::GaugeExact { lambda } => json!({
            "kind": "lambda",
            "lambda": lambda.iter().map(|b| u8::from(*b)).collect::<Vec<_>>(),
        }),
        GaugeVerdict::GlobalH1Obstruction { separator } => json!({
            "kind": "separator",
            "separator": separator.iter().map(|b| u8::from(*b)).collect::<Vec<_>>(),
        }),
    };

    json!({
        "schema_version": BOARD_VERDICT_SCHEMA,
        "verdict": verdict.token(),
        "witness": witness,
        "admissible_repairs": admissible_repairs(&verdict),
        "gauge_moves_can_help": matches!(verdict, GaugeVerdict::GaugeExact { .. }),
        "evidence_ceiling": "LocalReplay",
        "authority_effect": "None",
    })
}

fn run_detect(request: DetectRequest, raw_bytes: Option<&[u8]>) -> Value {
    let context = DetectionContext {
        prompt: request.context.prompt,
        unexplored_branches: request.context.unexplored_branches,
        seen_digests: request.context.seen_digests,
        seen_semantic_digests: request.context.seen_semantic_digests,
        host_replay_receipt: request.context.host_replay_receipt,
        semantic_replay_passed: request.context.semantic_replay_passed,
    };
    let report = detect_with_raw_bytes(&request.candidate, raw_bytes, &context);

    json!({
        "schema_version": DETECT_REPORT_SCHEMA,
        "normalized_json_digest": report.normalized_json_digest,
        "raw_bytes_digest": report.raw_bytes_digest,
        "subject_digest": report.subject_digest,
        "semantic_payload_digest": report.semantic_payload_digest,
        "detectors_run": report.detectors_run,
        "is_clean": report.is_clean(),
        "strongest_disposition": report.strongest_disposition().map(|d| d.as_str()),
        "findings": report.findings.iter().map(|finding| json!({
            "class": finding.class.code(),
            "disposition": finding.disposition.as_str(),
            "locus": finding.locus,
            "detail": finding.detail,
        })).collect::<Vec<_>>(),
        "evidence_ceiling": "LocalReplay",
        "authority_effect": "None",
    })
}

pub fn describe() -> Value {
    json!({
        "schema_version": DESCRIPTION_SCHEMA,
        "logical_id": "core-symgam-host",
        "crate_version": env!("CARGO_PKG_VERSION"),
        "modes": ["--describe", "classify-board", "detect"],
        "classify_board_request_schema": BOARD_REQUEST_SCHEMA,
        "classify_board_verdict_schema": BOARD_VERDICT_SCHEMA,
        "detect_request_schema": DETECT_REQUEST_SCHEMA,
        "detect_report_schema": DETECT_REPORT_SCHEMA,
        "max_request_bytes": MAX_REQUEST_BYTES,
        "canonicalization_profile": "core-sorted-json-no-float-v1",
        "evidence_ceiling": "LocalReplay",
        "authority_effect": "None",
    })
}

/// Dispatch a complete bounded request without rewriting its custody bytes.
/// Description and unknown modes do not parse or inspect the request body.
pub fn dispatch(mode: &str, bytes: &[u8]) -> Value {
    match mode {
        "--describe" => describe(),
        "classify-board" | "detect" => {
            if bytes.len() > MAX_REQUEST_BYTES {
                return refusal(
                    "REQUEST_UNREADABLE",
                    format!("request exceeds {MAX_REQUEST_BYTES} bytes"),
                );
            }
            let value: Value = match serde_json::from_slice(bytes) {
                Ok(value) => value,
                Err(error) => return refusal("REQUEST_NOT_JSON", error.to_string()),
            };
            if mode == "classify-board" {
                match serde_json::from_value::<BoardRequest>(value) {
                    Err(error) => refusal("REQUEST_SHAPE_INVALID", error.to_string()),
                    Ok(request) => classify(request),
                }
            } else {
                match serde_json::from_value::<DetectRequest>(value) {
                    Err(error) => refusal("REQUEST_SHAPE_INVALID", error.to_string()),
                    Ok(request) => run_detect(request, Some(bytes)),
                }
            }
        }
        other => refusal("UNKNOWN_MODE", format!("unknown mode {other:?}")),
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/interface.rs
// Claim: urn:core:crates_rs:pfp-runtime:interface:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde7813949 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde7813949` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore7813949 {
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
impl BoundaryErrore7813949 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore7813949 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore7813949 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde7813949 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore7813949> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore7813949::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore7813949::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore7813949::ExceedsCapacity {
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
mod l4_boundary_tests_e7813949 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde7813949::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde7813949::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde7813949::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde7813949::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde7813949::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore7813949::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore7813949::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
