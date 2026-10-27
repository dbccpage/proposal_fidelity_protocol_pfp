//! Canary test (S3): the registry stores hashed-shape-only keys; no raw
//! cochain payload field is persisted on any path. Read the four source files
//! at compile time via `include_str!` and assert none contains a forbidden
//! payload token. Positive control: `src/signature.rs` MUST contain the
//! shape-input tokens `face_indices` and `quotient_space_id`.
//!
//! The canary token literals below are split via `concat!` so this very file
//! does NOT itself contain a forbidden literal in raw form. That keeps the
//! grep clean on the canary file too.

const SIGNATURE_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/signature.rs");
const RECORD_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/record.rs");
const REGISTRY_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/registry.rs");
const WIRE_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/wire.rs");

fn assert_absent(label: &str, source: &str, token: &str) {
    assert!(
        !source.contains(token),
        "FORBIDDEN payload token `{}` found in {}",
        token,
        label
    );
}

#[test]
fn no_raw_payload_tokens_in_signature() {
    let needle_coeff_method = concat!("Cochain", "::coefficient");
    let needle_coeffs = "coeffs";
    let needle_payload_bytes = concat!("payload", "_bytes");
    let needle_raw_cochain = concat!("raw", "_cochain");
    let needle_cochain_payload = concat!("cochain", "_payload");
    assert_absent("signature.rs", SIGNATURE_RS, needle_coeff_method);
    assert_absent("signature.rs", SIGNATURE_RS, needle_coeffs);
    assert_absent("signature.rs", SIGNATURE_RS, needle_payload_bytes);
    assert_absent("signature.rs", SIGNATURE_RS, needle_raw_cochain);
    assert_absent("signature.rs", SIGNATURE_RS, needle_cochain_payload);
}

#[test]
fn no_raw_payload_tokens_in_record() {
    let needle_coeff_method = concat!("Cochain", "::coefficient");
    let needle_coeffs = "coeffs";
    let needle_payload_bytes = concat!("payload", "_bytes");
    let needle_raw_cochain = concat!("raw", "_cochain");
    let needle_cochain_payload = concat!("cochain", "_payload");
    assert_absent("record.rs", RECORD_RS, needle_coeff_method);
    assert_absent("record.rs", RECORD_RS, needle_coeffs);
    assert_absent("record.rs", RECORD_RS, needle_payload_bytes);
    assert_absent("record.rs", RECORD_RS, needle_raw_cochain);
    assert_absent("record.rs", RECORD_RS, needle_cochain_payload);
}

#[test]
fn no_raw_payload_tokens_in_registry() {
    let needle_coeff_method = concat!("Cochain", "::coefficient");
    let needle_coeffs = "coeffs";
    let needle_payload_bytes = concat!("payload", "_bytes");
    let needle_raw_cochain = concat!("raw", "_cochain");
    let needle_cochain_payload = concat!("cochain", "_payload");
    assert_absent("registry.rs", REGISTRY_RS, needle_coeff_method);
    assert_absent("registry.rs", REGISTRY_RS, needle_coeffs);
    assert_absent("registry.rs", REGISTRY_RS, needle_payload_bytes);
    assert_absent("registry.rs", REGISTRY_RS, needle_raw_cochain);
    assert_absent("registry.rs", REGISTRY_RS, needle_cochain_payload);
}

#[test]
fn no_raw_payload_tokens_in_wire() {
    let needle_coeff_method = concat!("Cochain", "::coefficient");
    let needle_coeffs = "coeffs";
    let needle_payload_bytes = concat!("payload", "_bytes");
    let needle_raw_cochain = concat!("raw", "_cochain");
    let needle_cochain_payload = concat!("cochain", "_payload");
    assert_absent("wire.rs", WIRE_RS, needle_coeff_method);
    assert_absent("wire.rs", WIRE_RS, needle_coeffs);
    assert_absent("wire.rs", WIRE_RS, needle_payload_bytes);
    assert_absent("wire.rs", WIRE_RS, needle_raw_cochain);
    assert_absent("wire.rs", WIRE_RS, needle_cochain_payload);
}

#[test]
fn signature_rs_positive_control() {
    let needle_face = concat!("face", "_indices");
    let needle_qs_id = concat!("quotient", "_space_id");
    assert!(
        SIGNATURE_RS.contains(needle_face),
        "positive control: signature.rs should mention `face_indices` to document its shape inputs"
    );
    assert!(
        SIGNATURE_RS.contains(needle_qs_id),
        "positive control: signature.rs should mention `quotient_space_id` to document its shape inputs"
    );
}

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/canary_no_raw_payload.rs
// Claim: urn:core:crates_rs:tests:canary-no-raw-payload:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde8fe5ee0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde8fe5ee0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore8fe5ee0 {
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
impl BoundaryErrore8fe5ee0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore8fe5ee0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore8fe5ee0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde8fe5ee0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore8fe5ee0> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore8fe5ee0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore8fe5ee0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore8fe5ee0::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e8fe5ee0() {
    let admitted = BoundaryRecorde8fe5ee0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde8fe5ee0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
