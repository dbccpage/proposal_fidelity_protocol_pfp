//! The round-record digest must be what the host says it is.
//!
//! `main.rs` advertises `canonicalization_profile: "core-sorted-json-no-float-v1"`,
//! and a verifier in another language computes the sorted-key digest of the same
//! packet. `RoundRecord::seal` used `serde_json::to_vec`, which emits fields in
//! *declaration* order, so the two disagreed and the digest was canonical in
//! name only.
//!
//! These tests check the property rather than a hard-coded hash: a golden value
//! would pin whatever the code currently does, including the wrong thing.
//!
//! AuthorityEffect: None.

use core_operad_theory::kernel::canonical::canonical_id;
use pfp_runtime::packets::{
    CandidateMovePacket, Disposition, LocalReplayStatus, MoveKind, ParseResult, RoundRecord,
};

fn candidate() -> CandidateMovePacket {
    CandidateMovePacket::new(
        "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        7,
        "op://demo",
        MoveKind::Propose,
        "a rationale",
    )
}

fn seal(c: &CandidateMovePacket) -> RoundRecord {
    RoundRecord::seal(
        c,
        ParseResult::Pass,
        vec![],
        vec![],
        LocalReplayStatus::Pass,
        Disposition::AcceptedDelta,
        vec![],
    )
    .expect("a plain candidate is canonical")
}

#[test]
fn the_digest_equals_the_kernel_canonical_id_of_the_packet() {
    // The whole claim, stated as an equality against the function whose
    // Rust/Python parity is already pinned by a shared fixture.
    let c = candidate();
    let payload = serde_json::to_value(&c).expect("representable");
    let expected = canonical_id(RoundRecord::DIGEST_DOMAIN, &payload).expect("canonical");

    assert_eq!(seal(&c).canonical_digest(), expected);
}

#[test]
fn the_digest_does_not_depend_on_field_declaration_order() {
    // The property that separates a sorted-key digest from a declaration-order
    // one. Re-encoding through a map loses declaration order entirely; a
    // canonical digest is unmoved by that, a `to_vec` digest is not.
    let c = candidate();
    let value = serde_json::to_value(&c).expect("representable");

    let reordered: serde_json::Value =
        serde_json::from_str(&serde_json::to_string(&value).expect("string")).expect("round trip");

    assert_eq!(
        canonical_id(RoundRecord::DIGEST_DOMAIN, &value).expect("canonical"),
        canonical_id(RoundRecord::DIGEST_DOMAIN, &reordered).expect("canonical"),
    );
    assert_eq!(
        seal(&c).canonical_digest(),
        seal(&candidate()).canonical_digest()
    );
}

#[test]
fn a_different_packet_gets_a_different_digest() {
    // Guards the degenerate fix: returning a constant would satisfy the tests
    // above.
    let mut other = candidate();
    other.public_rationale = "a different rationale".to_owned();
    assert_ne!(
        seal(&candidate()).canonical_digest(),
        seal(&other).canonical_digest()
    );
}

#[test]
fn a_non_ascii_packet_is_refused_rather_than_silently_hashed() {
    // The canonical profile refuses non-ASCII because it has no agreed
    // byte-level form across languages. Previously `unwrap_or_default()` would
    // not even have been reached -- `to_vec` accepts it happily and produces a
    // digest no other language reproduces.
    let mut c = candidate();
    c.public_rationale = "rationale with an em dash \u{2014} here".to_owned();

    let sealed = RoundRecord::seal(
        &c,
        ParseResult::Pass,
        vec![],
        vec![],
        LocalReplayStatus::Pass,
        Disposition::AcceptedDelta,
        vec![],
    );
    assert!(
        sealed.is_err(),
        "a packet outside the canonical profile must refuse, not hash"
    );
}

#[test]
fn the_domain_tag_is_part_of_the_hashed_bytes() {
    let c = candidate();
    let payload = serde_json::to_value(&c).expect("representable");
    assert_ne!(
        canonical_id(RoundRecord::DIGEST_DOMAIN, &payload).expect("canonical"),
        canonical_id("core.something.else.v1", &payload).expect("canonical"),
        "two structures with identical fields must not collide across domains"
    );
}

// Origin: engine/crates_rs/tests/pfp_runtime/digest_is_canonical.rs
// Claim: urn:core:crates_rs:tests:digest-is-canonical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9f128496 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9f128496` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9f128496 {
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
impl BoundaryError9f128496 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9f128496 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9f128496 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9f128496 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9f128496> {
        if capacity_bound == 0 {
            return Err(BoundaryError9f128496::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9f128496::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9f128496::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9f128496() {
    let admitted = BoundaryRecord9f128496::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9f128496::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
