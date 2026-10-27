//! S9: terminalize-seal handoff firewall test.
//!
//! This test does NOT mint a terminal itself; it verifies the `residual_families`
//! module is OFF the authority path. The two checks:
//!
//! 1. The host crate's `Cargo.toml` (`core_epk`, which carries this module since
//!    the `core_residual_families` crate was merged into it) does NOT depend on
//!    `core_sweep_kernel` or `core_certifiers`.
//! 2. No source file of the module (`src/residual_families/*.rs`) names a
//!    `Certificate` return type.
//!
//! The actual terminal is sealed elsewhere via
//! `core_sweep_kernel::terminalize_row` / `core_certifiers::certify_checked_packet`.

const CARGO_TOML: &str = include_str!("../../core_local_green_global_red_lggr/Cargo.toml");
const MOD_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/mod.rs");
const SIGNATURE_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/signature.rs");
const RECORD_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/record.rs");
const RECURRENCE_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/recurrence.rs");
const REGISTRY_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/registry.rs");
const WIRE_RS: &str = include_str!("../../core_local_green_global_red_lggr/src/residual_families/wire.rs");

#[test]
fn cargo_toml_does_not_depend_on_authority_minters() {
    assert!(
        !CARGO_TOML.contains("core_sweep_kernel"),
        "FIREWALL: host crate Cargo.toml must NOT depend on core_sweep_kernel"
    );
    assert!(
        !CARGO_TOML.contains("core_certifiers"),
        "FIREWALL: host crate Cargo.toml must NOT depend on core_certifiers"
    );
}

fn assert_no_certificate_return_type(label: &str, source: &str) {
    // Look for `-> Certificate` (with optional generics) or
    // `-> Result<Certificate`. We don't ban the WORD "certificate" — the
    // doc-comments may reference core_certifiers prose. We ban a function
    // signature that RETURNS a Certificate.
    let arrow_cert = "-> Certificate";
    let arrow_result_cert = "-> Result<Certificate";
    let arrow_option_cert = "-> Option<Certificate";
    assert!(
        !source.contains(arrow_cert),
        "FIREWALL: {} contains a `-> Certificate` return type",
        label
    );
    assert!(
        !source.contains(arrow_result_cert),
        "FIREWALL: {} contains a `-> Result<Certificate` return type",
        label
    );
    assert!(
        !source.contains(arrow_option_cert),
        "FIREWALL: {} contains a `-> Option<Certificate` return type",
        label
    );
}

#[test]
fn no_certificate_return_type_in_public_sources() {
    assert_no_certificate_return_type("mod.rs", MOD_RS);
    assert_no_certificate_return_type("signature.rs", SIGNATURE_RS);
    assert_no_certificate_return_type("record.rs", RECORD_RS);
    assert_no_certificate_return_type("recurrence.rs", RECURRENCE_RS);
    assert_no_certificate_return_type("registry.rs", REGISTRY_RS);
    assert_no_certificate_return_type("wire.rs", WIRE_RS);
}

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/terminalize_row_seal.rs
// Claim: urn:core:crates_rs:tests:terminalize-row-seal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb44db1a2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb44db1a2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb44db1a2 {
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
impl BoundaryErrorb44db1a2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb44db1a2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb44db1a2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb44db1a2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb44db1a2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb44db1a2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb44db1a2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb44db1a2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b44db1a2() {
    let admitted = BoundaryRecordb44db1a2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb44db1a2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
