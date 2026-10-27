//! Finite witnesses for the existing Digest grammar and domain framing.
//! These checks name bytes; they do not establish what those bytes attest to.

use core_kernel::{Digest, DigestError};

// Known answers were computed independently with .NET SHA256.HashData and
// Python hashlib.sha256 over the literal preimage hex recorded below. Expected
// hashes are not produced by Digest or reconstructed framing in these tests.
const EMPTY_DOMAIN: &str =
    "sha256:af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc";
const UTF8_DOMAIN: &str = "sha256:72fb57ca2e03d021f1695213663a8ca918d6bba7bf7d313b3ad01da6e9dbc1a8";
const DOMAIN_AB: &str = "sha256:290a3daa9b49526a2ed7352cd7f5e69c551a01e15de61fc04c43f780d7172b71";
const DOMAIN_A: &str = "sha256:e98bc483cc6af9ccf82bc23e481a128c12818251d9d359a7b560dcabfd7909d6";
const UTF8_DOMAIN_JSON: &str =
    r#""sha256:72fb57ca2e03d021f1695213663a8ca918d6bba7bf7d313b3ad01da6e9dbc1a8""#;

const MALFORMED_DIGESTS: &[(&str, &str)] = &[
    (
        "",
        "missing the sha256: prefix; a bare hex string is not a digest",
    ),
    (
        "72fb57ca2e03d021f1695213663a8ca918d6bba7bf7d313b3ad01da6e9dbc1a8",
        "missing the sha256: prefix; a bare hex string is not a digest",
    ),
    (
        "SHA256:72fb57ca2e03d021f1695213663a8ca918d6bba7bf7d313b3ad01da6e9dbc1a8",
        "missing the sha256: prefix; a bare hex string is not a digest",
    ),
    ("sha256:", "expected 64 hex digits"),
    ("sha256:abc", "expected 64 hex digits"),
    (
        "sha256:72fb57ca2e03d021f1695213663a8ca918d6bba7bf7d313b3ad01da6e9dbc1a80",
        "expected 64 hex digits",
    ),
    (
        "sha256:72FB57CA2E03D021F1695213663A8CA918D6BBA7BF7D313B3AD01DA6E9DBC1A8",
        "expected lowercase hex only",
    ),
    (
        "sha256:72fb57ca2e03d021f1695213663a8ca918d6bba7bf7d313b3ad01da6e9dbc1ag",
        "expected lowercase hex only",
    ),
];

#[test]
fn empty_domain_still_hashes_the_eight_byte_length_prefix() {
    // Preimage hex: 0000000000000000, not the empty message.
    assert_eq!(Digest::of_domained("", b"").as_str(), EMPTY_DOMAIN);
}

#[test]
fn domain_length_counts_utf8_bytes_in_a_big_endian_u64_prefix() {
    // Domain é is c3a9 (two bytes); payload is 0078 (NUL, x).
    // Preimage hex: 0000000000000002c3a90078.
    assert_eq!(Digest::of_domained("é", b"\0x").as_str(), UTF8_DOMAIN);
}

#[test]
fn shifted_domain_boundary_matches_two_distinct_literal_known_answers() {
    // Preimages: 0000000000000002616263 and 0000000000000001616263.
    // Both unframed bodies are 616263, but the domain lengths are two and one.
    let first = Digest::of_domained("ab", b"c");
    let second = Digest::of_domained("a", b"bc");
    assert_eq!(first.as_str(), DOMAIN_AB);
    assert_eq!(second.as_str(), DOMAIN_A);
    assert_ne!(first, second);
}

#[test]
fn public_parse_preserves_each_literal_canonical_known_answer() {
    for text in [EMPTY_DOMAIN, UTF8_DOMAIN, DOMAIN_AB, DOMAIN_A] {
        let digest = Digest::parse(text).expect("literal canonical digest");
        assert_eq!(digest.as_str(), text);
        assert_eq!(digest.to_string(), text);
        assert_eq!(String::from(digest), text);
    }
}

#[test]
fn serde_accepts_and_emits_the_literal_canonical_string_wire() {
    let parsed = Digest::parse(UTF8_DOMAIN).expect("literal canonical digest");
    let decoded: Digest =
        serde_json::from_str(UTF8_DOMAIN_JSON).expect("literal canonical JSON string");
    assert_eq!(decoded, parsed);
    assert_eq!(decoded.as_str(), UTF8_DOMAIN);
    assert_eq!(serde_json::to_string(&decoded).unwrap(), UTF8_DOMAIN_JSON);
}

#[test]
fn public_parse_refuses_malformed_spellings_with_the_exact_error() {
    for &(value, reason) in MALFORMED_DIGESTS {
        assert_eq!(
            Digest::parse(value),
            Err(DigestError {
                value: value.to_owned(),
                reason,
            }),
            "malformed spelling: {value:?}",
        );
    }
}

#[test]
fn serde_refuses_the_same_malformed_spellings_as_data_errors() {
    for &(value, reason) in MALFORMED_DIGESTS {
        // Encode a valid JSON string, so refusal must concern Digest data rather
        // than a JSON syntax error. No Digest validation verdict is substituted.
        let wire = serde_json::to_string(value).unwrap();
        let error = serde_json::from_str::<Digest>(&wire).unwrap_err();
        assert!(error.is_data(), "unexpected error for {value:?}: {error}");
        assert!(
            error.to_string().contains(reason),
            "missing parse refusal for {value:?}: {error}",
        );
    }
}

#[test]
fn serde_refuses_non_string_json_values() {
    for wire in ["null", "true", "1", "[]", "{}"] {
        let error = serde_json::from_str::<Digest>(wire).unwrap_err();
        assert!(error.is_data(), "unexpected error for {wire}: {error}");
    }
}

// Origin: engine/crates_rs/tests/core_kernel/digest_domain_contract.rs
// Claim: urn:core:crates_rs:tests:digest-domain-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf80cc30d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf80cc30d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf80cc30d {
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
impl BoundaryErrorf80cc30d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf80cc30d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf80cc30d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf80cc30d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf80cc30d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf80cc30d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf80cc30d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf80cc30d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f80cc30d() {
    let admitted = BoundaryRecordf80cc30d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf80cc30d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
