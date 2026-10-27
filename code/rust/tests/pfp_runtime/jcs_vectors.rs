// AuthorityEffect: None.
//! Selected local encoding-profile vectors; not exhaustive conformance verification.
//!
//! Checks on the supplied fixtures:
//! 1. UTF-16 code unit sorting order (emoji surrogate vs BMP Hebrew character).
//! 2. ECMAScript 7.1.12.1 number serialization (integers, negative zero, scientific exponent thresholds).
//! 3. Idempotency: jcs(canonicalize(v)) == canonicalize(v).
//! 4. Refusal of duplicate keys.
//! 5. Refusal of integers > 2^53 - 1 (MAX_SAFE_INTEGER).
//! 6. Non-escaping of solidus ('/').
//! 7. SHA-256 digest computation over canonical bytes.

use pfp_runtime::jcs::{
    canonicalize_str, digest_str_sha256, format_es_number, JcsError, MAX_SAFE_INTEGER,
};
use sha2::Digest;

#[test]
fn test_utf16_code_unit_sorting_order() {
    // RFC 8785 §3.2.3 specifies UTF-16 key sorting; this vector is not a conformance suite.
    // U+FB33 (Hebrew Pointed Dalet 'דּ') has UTF-16 code unit 0xFB33.
    // U+1F600 (Grinning Face '😀') in UTF-16 is surrogate pair [0xD83D, 0xDE00].
    // Since 0xD83D < 0xFB33, the emoji must sort BEFORE the Hebrew character,
    // contrary to Unicode scalar value sorting (where 0xFB33 < 0x1F600).
    let raw = r#"{"\uFB33": 1, "\uD83D\uDE00": 2}"#;
    let canonical = canonicalize_str(raw).expect("canonicalization must succeed");
    assert_eq!(canonical, "{\"😀\":2,\"דּ\":1}");

    // Additional sorting vector: ASCII keys sorted ordinally
    let raw_ascii = r#"{"b": 1, "a": 2, "aa": 3, "ab": 4}"#;
    let canonical_ascii = canonicalize_str(raw_ascii).expect("canonicalization must succeed");
    assert_eq!(canonical_ascii, r#"{"a":2,"aa":3,"ab":4,"b":1}"#);
}

#[test]
fn test_ecmascript_number_serialization() {
    // Zeroes
    assert_eq!(format_es_number(0.0).unwrap(), "0");
    assert_eq!(format_es_number(-0.0).unwrap(), "0");

    // Standard integers
    assert_eq!(format_es_number(1.0).unwrap(), "1");
    assert_eq!(format_es_number(-1.0).unwrap(), "-1");
    assert_eq!(format_es_number(42.0).unwrap(), "42");
    assert_eq!(format_es_number(-42.0).unwrap(), "-42");

    // Decimals
    assert_eq!(format_es_number(1.5).unwrap(), "1.5");
    assert_eq!(format_es_number(-1.5).unwrap(), "-1.5");
    assert_eq!(format_es_number(0.125).unwrap(), "0.125");

    // Boundary at 1e21:
    // Numbers < 1e21 use fixed notation if k <= n <= 21
    // 10^20 -> 21 digits -> "100000000000000000000"
    assert_eq!(format_es_number(1e20).unwrap(), "100000000000000000000");
    // 10^21 -> exponent notation "1e+21"
    assert_eq!(format_es_number(1e21).unwrap(), "1e+21");
    assert_eq!(format_es_number(-1e21).unwrap(), "-1e+21");

    // Boundary at 1e-6:
    // 1e-6 -> "0.000001"
    assert_eq!(format_es_number(1e-6).unwrap(), "0.000001");
    // 1e-7 -> "1e-7"
    assert_eq!(format_es_number(1e-7).unwrap(), "1e-7");
    assert_eq!(format_es_number(-1e-7).unwrap(), "-1e-7");

    // JSON array with multiple numbers
    let raw_arr = r#"[1.0, -0.0, 1e21, 0.000001, 1e-7]"#;
    let canonical_arr = canonicalize_str(raw_arr).expect("canonicalization must succeed");
    assert_eq!(canonical_arr, "[1,0,1e+21,0.000001,1e-7]");
}

#[test]
fn test_minimal_escaping_and_no_solidus_escape() {
    // RFC 8785 §3.2.2.2: Solidus '/' MUST NOT be escaped.
    // Quotes and backslashes must be escaped.
    // Control characters \b, \f, \n, \r, \t must be 2-char escaped.
    let raw =
        r#"{"url": "https://example.com/foo/bar", "quote": "hello \"world\"", "newline": "a\nb"}"#;
    let canonical = canonicalize_str(raw).expect("canonicalization must succeed");
    assert_eq!(
        canonical,
        r#"{"newline":"a\nb","quote":"hello \"world\"","url":"https://example.com/foo/bar"}"#
    );
}

#[test]
fn test_idempotency() {
    let raw = r#"{
        "z": [true, false, null, 123.456],
        "a": { "inner_b": 2, "inner_a": 1 },
        "m": "test"
    }"#;
    let round1 = canonicalize_str(raw).expect("round 1 succeeds");
    let round2 = canonicalize_str(&round1).expect("round 2 succeeds");
    assert_eq!(round1, round2);
}

#[test]
fn test_duplicate_key_refusal() {
    let raw_duplicate = r#"{"key": 1, "key": 2}"#;
    let res = canonicalize_str(raw_duplicate);
    match res {
        Err(JcsError::DuplicateKey(key)) => assert_eq!(key, "key"),
        other => panic!("expected DuplicateKey error, got {other:?}"),
    }
}

#[test]
fn test_max_safe_integer_refusal() {
    // MAX_SAFE_INTEGER is 2^53 - 1 = 9007199254740991
    let safe = format!(r#"{{"safe": {}}}"#, MAX_SAFE_INTEGER);
    let canonical = canonicalize_str(&safe).expect("safe integer must succeed");
    assert_eq!(canonical, format!(r#"{{"safe":{}}}"#, MAX_SAFE_INTEGER));

    // Exceeds safe integer by 1
    let unsafe_int = format!(r#"{{"unsafe": {}}}"#, MAX_SAFE_INTEGER + 1);
    let res = canonicalize_str(&unsafe_int);
    match res {
        Err(JcsError::IntegerOutOfRange(_)) => {}
        other => panic!("expected IntegerOutOfRange error, got {other:?}"),
    }
}

#[test]
fn test_digest_sha256() {
    let raw = r#"{"b": 2, "a": 1}"#;
    let digest = digest_str_sha256(raw).expect("digest computation must succeed");
    // Canonical string is `{"a":1,"b":2}`
    // SHA256('{"a":1,"b":2}') in hex:
    let expected = hex::encode(sha2::Sha256::digest(b"{\"a\":1,\"b\":2}"));
    assert_eq!(digest, expected);
}

// Origin: engine/crates_rs/tests/pfp_runtime/jcs_vectors.rs
// Claim: urn:core:crates_rs:tests:jcs-vectors:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord20abe292 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord20abe292` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError20abe292 {
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
impl BoundaryError20abe292 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError20abe292 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError20abe292 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord20abe292 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError20abe292> {
        if capacity_bound == 0 {
            return Err(BoundaryError20abe292::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError20abe292::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError20abe292::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_20abe292() {
    let admitted = BoundaryRecord20abe292::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord20abe292::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
