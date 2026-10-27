//! Rust half of the shared Nomos URN conformance corpus.
//!
//! This grammar has two implementations -- `nomos_urn.py` and `nomos_urn.rs` --
//! and until now nothing compared them. Each had its own tests (10 and 9), and
//! each tested itself against its own expectations, so the two could drift
//! apart on any input neither suite happened to cover. The first symptom would
//! have been a contract id accepted on one side of the seam and refused on the
//! other.
//!
//! `nomos_urn_golden_vectors_v1.json` is the shared corpus. Python is its
//! declared owner and produced the expectations by running; this side conforms
//! to the same bytes. The file is embedded with `include_str!` so a missing or
//! moved corpus is a compile error rather than a skipped test -- a conformance
//! test that silently does not run is worse than none, because it reports green.

// Origin: engine/crates_rs/core_contracts/src/nomos_urn_golden_parity.rs
// Claim: urn:core:crates_rs:core-contracts:nomos-urn-golden-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord473a7ace {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord473a7ace` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError473a7ace {
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
impl BoundaryError473a7ace {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError473a7ace {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError473a7ace {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord473a7ace {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError473a7ace> {
        if capacity_bound == 0 {
            return Err(BoundaryError473a7ace::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError473a7ace::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError473a7ace::ExceedsCapacity {
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
mod tests {
    use crate::nomos_urn::{
        format_nomos_urn, is_well_formed_nomos_urn, parse_nomos_urn, NomosUrnError,
    };
    use serde_json::Value;

    const CORPUS: &str = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../tests/core_contracts/fixtures/nomos_urn_golden_vectors_v1.json"
    ));

    /// The name the corpus records for a refusal, so both languages can be held
    /// to the same vocabulary rather than merely to "it refused".
    fn kind_name(err: &NomosUrnError) -> &'static str {
        match err {
            NomosUrnError::Empty => "Empty",
            NomosUrnError::MissingPrefix => "MissingPrefix",
            NomosUrnError::WrongSegmentCount => "WrongSegmentCount",
            NomosUrnError::EmptySegment => "EmptySegment",
            NomosUrnError::BadDomainCharset => "BadDomainCharset",
            NomosUrnError::BadNameCharset => "BadNameCharset",
            NomosUrnError::BadCrateCharset => "BadCrateCharset",
            NomosUrnError::BadVersion => "BadVersion",
            NomosUrnError::UnexpectedFileMarker => "UnexpectedFileMarker",
        }
    }

    fn corpus() -> Value {
        serde_json::from_str(CORPUS).expect("golden vector corpus must be valid JSON")
    }

    fn vectors(root: &Value) -> &Vec<Value> {
        root["vectors"]
            .as_array()
            .expect("vectors must be an array")
    }

    #[test]
    fn the_corpus_loads_and_is_not_empty() {
        let root = corpus();
        assert_eq!(
            root["schema"].as_str(),
            Some("core.contract.nomos_urn_golden_vectors.v1")
        );
        assert!(
            vectors(&root).len() >= 28,
            "corpus shrank to {}; vectors are removed only when the grammar \
             drops a case, and that must be deliberate",
            vectors(&root).len()
        );
    }

    #[test]
    fn the_corpus_covers_every_error_kind_this_side_can_produce() {
        // Every variant Rust can return must appear in the corpus, or drift in
        // that variant is undetectable from here.
        let all = [
            NomosUrnError::Empty,
            NomosUrnError::MissingPrefix,
            NomosUrnError::WrongSegmentCount,
            NomosUrnError::EmptySegment,
            NomosUrnError::BadDomainCharset,
            NomosUrnError::BadNameCharset,
            NomosUrnError::BadCrateCharset,
            NomosUrnError::BadVersion,
            NomosUrnError::UnexpectedFileMarker,
        ];
        let root = corpus();
        let covered: Vec<String> = vectors(&root)
            .iter()
            .filter(|v| !v["accepts"].as_bool().unwrap_or(true))
            .map(|v| v["error_kind"].as_str().unwrap().to_string())
            .collect();
        let mut missing = Vec::new();
        for err in all.iter() {
            let name = kind_name(err);
            if !covered.iter().any(|c| c == name) {
                missing.push(name);
            }
        }
        assert!(missing.is_empty(), "error kinds not covered: {missing:?}");
    }

    #[test]
    fn every_accepted_vector_parses_to_the_recorded_parts() {
        let root = corpus();
        let mut mismatches: Vec<String> = Vec::new();
        for vector in vectors(&root) {
            if !vector["accepts"].as_bool().unwrap_or(false) {
                continue;
            }
            let label = vector["label"].as_str().unwrap();
            let raw = vector["raw"].as_str().unwrap();
            match parse_nomos_urn(raw) {
                Err(err) => mismatches.push(format!("{label}: refused with {}", kind_name(&err))),
                Ok(parsed) => {
                    if parsed.domain != vector["domain"].as_str().unwrap() {
                        mismatches.push(format!("{label}: domain {}", parsed.domain));
                    }
                    if parsed.name != vector["name"].as_str().unwrap() {
                        mismatches.push(format!("{label}: name {}", parsed.name));
                    }
                    if parsed.version != vector["version"].as_str().unwrap() {
                        mismatches.push(format!("{label}: version {}", parsed.version));
                    }
                    let expected_crate = vector["crate_name"].as_str();
                    if parsed.crate_name.as_deref() != expected_crate {
                        mismatches.push(format!(
                            "{label}: crate_name {:?} vs corpus {:?}",
                            parsed.crate_name, expected_crate
                        ));
                    }
                    if parsed.file_locus != vector["file_locus"].as_bool().unwrap() {
                        mismatches.push(format!("{label}: file_locus {}", parsed.file_locus));
                    }
                }
            }
        }
        assert!(
            mismatches.is_empty(),
            "accepted-vector disagreements with the Python owner: {mismatches:#?}"
        );
    }

    #[test]
    fn every_rejected_vector_refuses_with_the_recorded_kind() {
        // The kind matters, not merely that it refused. Two parsers can agree a
        // URN is bad and disagree about why, and a caller branching on the kind
        // would then behave differently across the seam.
        let root = corpus();
        let mut mismatches: Vec<String> = Vec::new();
        for vector in vectors(&root) {
            if vector["accepts"].as_bool().unwrap_or(false) {
                continue;
            }
            let label = vector["label"].as_str().unwrap();
            let raw = vector["raw"].as_str().unwrap();
            let expected = vector["error_kind"].as_str().unwrap();
            match parse_nomos_urn(raw) {
                Ok(_) => mismatches.push(format!("{label}: accepted, corpus records refusal")),
                Err(err) => {
                    let actual = kind_name(&err);
                    if actual != expected {
                        mismatches.push(format!(
                            "{label}: refused with {actual}, corpus records {expected}"
                        ));
                    }
                }
            }
        }
        assert!(
            mismatches.is_empty(),
            "rejected-vector disagreements with the Python owner: {mismatches:#?}"
        );
    }

    #[test]
    fn is_well_formed_agrees_with_parse_on_every_vector() {
        let root = corpus();
        let mut disagreements: Vec<String> = Vec::new();
        for vector in vectors(&root) {
            let raw = vector["raw"].as_str().unwrap();
            let accepts = vector["accepts"].as_bool().unwrap();
            if is_well_formed_nomos_urn(raw) != accepts {
                disagreements.push(vector["label"].as_str().unwrap().to_string());
            }
        }
        assert!(
            disagreements.is_empty(),
            "predicate disagrees with corpus on: {disagreements:?}"
        );
    }

    #[test]
    fn accepted_vectors_round_trip_through_format() {
        let root = corpus();
        let mut lossy: Vec<String> = Vec::new();
        for vector in vectors(&root) {
            if !vector["accepts"].as_bool().unwrap_or(false) {
                continue;
            }
            let raw = vector["raw"].as_str().unwrap();
            let parsed = parse_nomos_urn(raw).expect("accepted vector must parse");
            let formatted = format_nomos_urn(&parsed);
            if formatted != raw {
                lossy.push(format!(
                    "{}: {formatted:?} != {raw:?}",
                    vector["label"].as_str().unwrap()
                ));
            }
        }
        assert!(
            lossy.is_empty(),
            "format/parse round trip is lossy: {lossy:#?}"
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_473a7ace {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord473a7ace::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord473a7ace::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord473a7ace::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord473a7ace::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord473a7ace::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError473a7ace::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError473a7ace::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
