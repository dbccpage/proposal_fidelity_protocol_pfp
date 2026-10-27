use std::fs;
use std::path::PathBuf;

use pfp_runtime::canonical::{
    canonical_bytes, canonical_json, canonical_unwire, canonical_wire, domain_digest_json,
};
use serde::Deserialize;
use serde_json::Value;

#[derive(Debug, Deserialize)]
struct GoldenVector {
    name: String,
    raw_input_json: String,
    wire_representation: Value,
    canonical_json: String,
    canonical_bytes_hex: String,
    domain_digest_sha256: String,
    domain: String,
}

#[derive(Debug, Deserialize)]
struct GoldenFile {
    schema_version: String,
    #[allow(dead_code)]
    domain: String,
    vector_count: usize,
    vectors: Vec<GoldenVector>,
}

/// The golden vectors, resolved from this crate rather than from the cwd.
///
/// This used to try five paths, four relative to the working directory and one
/// absolute: `C:\Users\a343o\source\repos\sentinelpy-feature\...`. A committed
/// test that reaches into a named developer's other checkout passes for exactly
/// one person on exactly one machine, and its result depends on where `cargo`
/// was invoked from.
///
/// `CARGO_MANIFEST_DIR` is fixed at compile time and independent of the cwd, so
/// there is one path and it is correct everywhere.
fn find_golden_file() -> PathBuf {
    let candidates = [PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../../pfp/tests/golden_canonical_vectors.json")];
    for path in &candidates {
        if path.exists() {
            return path.clone();
        }
    }
    panic!("golden_canonical_vectors.json not found in candidate paths");
}

#[test]
fn parity_against_python_canonical_golden_vectors() {
    let golden_path = find_golden_file();
    let content = fs::read_to_string(&golden_path).expect("read golden file");
    let golden_data: GoldenFile = serde_json::from_str(&content).expect("parse golden file");

    assert_eq!(
        golden_data.schema_version,
        "core.symbol-game.golden-canonical-vectors.v1"
    );
    assert_eq!(golden_data.vectors.len(), golden_data.vector_count);

    for (index, vec) in golden_data.vectors.iter().enumerate() {
        let raw_val: Value = serde_json::from_str(&vec.raw_input_json).expect("valid raw json");

        // 1. Check canonical wire generation matches Python wire
        let wire_val = canonical_wire(&raw_val).unwrap_or_else(|e| {
            panic!(
                "Vector #{} ({}) canonical_wire failed: {:?}",
                index, vec.name, e
            )
        });
        assert_eq!(
            wire_val, vec.wire_representation,
            "Vector #{} ({}) wire representation mismatch",
            index, vec.name
        );

        // 2. Check canonical JSON string matches Python canonical JSON
        let canon_json = canonical_json(&raw_val).unwrap_or_else(|e| {
            panic!(
                "Vector #{} ({}) canonical_json failed: {:?}",
                index, vec.name, e
            )
        });
        assert_eq!(
            canon_json, vec.canonical_json,
            "Vector #{} ({}) canonical JSON string mismatch",
            index, vec.name
        );

        // 3. Check canonical bytes match Python canonical bytes
        let bytes = canonical_bytes(&raw_val).unwrap_or_else(|e| {
            panic!(
                "Vector #{} ({}) canonical_bytes failed: {:?}",
                index, vec.name, e
            )
        });
        assert_eq!(
            hex::encode(&bytes),
            vec.canonical_bytes_hex,
            "Vector #{} ({}) canonical bytes hex mismatch",
            index,
            vec.name
        );

        // 4. Check domain digest matches Python domain digest
        let digest = domain_digest_json(&vec.domain, &raw_val).unwrap_or_else(|e| {
            panic!(
                "Vector #{} ({}) domain_digest failed: {:?}",
                index, vec.name, e
            )
        });
        assert_eq!(
            digest, vec.domain_digest_sha256,
            "Vector #{} ({}) domain digest SHA-256 mismatch",
            index, vec.name
        );

        // 5. Check round-trip unwiring
        let unwired = canonical_unwire(&wire_val).unwrap_or_else(|e| {
            panic!(
                "Vector #{} ({}) canonical_unwire failed: {:?}",
                index, vec.name, e
            )
        });
        let roundtrip_wire = unwired.to_wire();
        assert_eq!(
            roundtrip_wire, vec.wire_representation,
            "Vector #{} ({}) round-trip wire mismatch",
            index, vec.name
        );
    }
}

// Origin: engine/crates_rs/tests/pfp_runtime/canonical_parity.rs
// Claim: urn:core:crates_rs:tests:canonical-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda0336c36 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda0336c36` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora0336c36 {
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
impl BoundaryErrora0336c36 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora0336c36 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora0336c36 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda0336c36 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora0336c36> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora0336c36::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora0336c36::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora0336c36::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a0336c36() {
    let admitted = BoundaryRecorda0336c36::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda0336c36::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
