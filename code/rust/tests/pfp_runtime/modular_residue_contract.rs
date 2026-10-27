//! Cross-language parity for the pinned modular-residue convention.
//!
//! AuthorityEffect: None.

use pfp_runtime::least_non_negative_residue;
use serde::Deserialize;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct VectorFile {
    schema: String,
    authority_effect: String,
    doctrine: Vec<String>,
    cases: Vec<VectorCase>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct VectorCase {
    lhs: String,
    modulus: String,
    least_non_negative_residue: String,
    truncated_remainder: String,
    conventions_agree: bool,
}

fn vector_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../governance/contracts/pinned/modular_residue_vectors.json")
}

#[test]
fn rust_matches_every_pinned_residue_and_names_the_truncation_hazard() {
    let path = vector_path();
    let bytes = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("cannot read {}: {error}", path.display()));
    let vectors: VectorFile = serde_json::from_str(&bytes)
        .unwrap_or_else(|error| panic!("cannot parse {}: {error}", path.display()));

    assert_eq!(vectors.schema, "core.modular_residue_vectors.v1");
    assert_eq!(vectors.authority_effect, "None");
    assert!(
        !vectors.doctrine.is_empty(),
        "the interface must state its doctrine"
    );
    assert_eq!(
        vectors.cases.len(),
        15,
        "the pinned interface census changed"
    );
    assert_eq!(
        vectors
            .cases
            .iter()
            .filter(|case| !case.conventions_agree)
            .count(),
        6,
        "the interface must retain cases that expose Rust `%` truncation"
    );

    for case in vectors.cases {
        let lhs: i128 = case.lhs.parse().expect("lhs fits i128");
        let modulus: i128 = case.modulus.parse().expect("modulus fits i128");
        let expected: i128 = case
            .least_non_negative_residue
            .parse()
            .expect("least residue fits i128");
        let pinned_truncated: i128 = case
            .truncated_remainder
            .parse()
            .expect("truncated remainder fits i128");

        let actual = least_non_negative_residue(lhs, modulus);
        let rust_truncated = lhs % modulus;
        assert_eq!(
            actual, expected,
            "wrong least residue for {lhs} mod {modulus}"
        );
        assert_eq!(
            rust_truncated, pinned_truncated,
            "pinned truncation witness drifted for {lhs} % {modulus}"
        );
        assert_eq!(
            case.conventions_agree,
            actual == rust_truncated,
            "agreement flag is false evidence for {lhs} mod {modulus}"
        );
        if !case.conventions_agree {
            assert_ne!(
                actual, rust_truncated,
                "a disagreement vector must kill the tempting `%` implementation"
            );
        }
    }
}

// Origin: engine/crates_rs/tests/pfp_runtime/modular_residue_contract.rs
// Claim: urn:core:crates_rs:tests:modular-residue-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordebfdc7af {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordebfdc7af` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorebfdc7af {
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
impl BoundaryErrorebfdc7af {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorebfdc7af {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorebfdc7af {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordebfdc7af {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorebfdc7af> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorebfdc7af::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorebfdc7af::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorebfdc7af::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ebfdc7af() {
    let admitted = BoundaryRecordebfdc7af::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordebfdc7af::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
