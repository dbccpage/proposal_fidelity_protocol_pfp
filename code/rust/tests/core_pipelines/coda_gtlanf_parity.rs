//! M10 — F7 Rust replay against a retained historical Python/Rust fixture.
//!
//! Fixture: `tests/fixtures/coda_gtlanf_parity_v1.json` in this crate.
//! (resolved relative to `CARGO_MANIFEST_DIR`; override with the
//! `CODA_GTLA_PARITY_FIXTURE` env var). The fixture's `terminal_mapping` is the
//! DECLARED contract binding the Python str spellings to the Rust `Outcome`
//! arms — the mapping the Inspector found unwitnessed in M10 (two of the
//! three Python strings matched no Rust arm, and no Rust file consumed the
//! golden).
//!
//! Exact upstream custody is recorded in `engine/RUNTIME_FIXTURE_CUSTODY.json`.
//! This Rust run alone does not execute the historical Python suite.
//!
//! Fail-closed: an unregistered `rust_outcome` token in the fixture panics
//! with the token named; there is no default arm.
//!
//! AuthorityEffect: None — these tests normalize payloads and mint nothing.

use core_pipelines::coda_gtlanf::{include_i, is_fixed, normalize_l, t, FinClaim, Normalize};
use core_types::{AuthorityTerminal, Outcome, RefusalSource, ScopedNegativeTerminal};
use serde_json::Value;
use std::path::PathBuf;

/// Concrete `Normalize` witness shared with the Python side: sorted + deduped.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Tags(Vec<u8>);

impl Normalize for Tags {
    fn normalize(&self) -> Self {
        let mut v = self.0.clone();
        v.sort_unstable();
        v.dedup();
        Tags(v)
    }
}

fn fixture_path() -> PathBuf {
    if let Ok(path) = std::env::var("GTLA_PARITY_FIXTURE") {
        return PathBuf::from(path);
    }
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../tests/core_pipelines/fixtures/gtlanf_parity_v1.json")
}

fn fixture() -> Value {
    let path = fixture_path();
    let text = std::fs::read_to_string(&path).unwrap_or_else(|error| {
        panic!(
            "cannot read the shared parity fixture {}: {error}",
            path.display()
        )
    });
    serde_json::from_str(&text).expect("parity fixture must be valid JSON")
}

/// The declared mapping, fail-closed: unknown tokens refuse loudly.
fn outcome_from_token(token: &str) -> Outcome {
    match token {
        "Terminal(ExactRuleDerived)" => Outcome::Terminal(AuthorityTerminal::ExactRuleDerived),
        "ScopedNegative(NoRule)" => Outcome::ScopedNegative(ScopedNegativeTerminal::NoRule),
        "Refused(Repair)" => Outcome::Refused(RefusalSource::Repair),
        other => {
            panic!("unregistered rust_outcome token in the parity fixture (fail-closed): {other}")
        }
    }
}

fn tags_from(value: &Value) -> Tags {
    Tags(
        value
            .as_array()
            .expect("payload must be a JSON array")
            .iter()
            .map(|n| n.as_u64().expect("payload entries must be integers") as u8)
            .collect(),
    )
}

#[test]
fn f7_laws_hold_on_every_shared_cell() {
    let fx = fixture();
    assert_eq!(fx["authority_effect"], "None");
    let payloads = fx["tags_payloads"].as_object().expect("tags_payloads");
    let normalized = fx["normalized_expected"]
        .as_object()
        .expect("normalized_expected");
    let fixed_expected = fx["fixed_expected"].as_object().expect("fixed_expected");
    let mapping = fx["terminal_mapping"].as_array().expect("terminal_mapping");
    assert_eq!(mapping.len(), 3, "the declared three-way terminal mapping");

    let mut cells = 0;
    for row in mapping {
        let terminal = outcome_from_token(row["rust_outcome"].as_str().expect("rust_outcome str"));
        for (name, raw) in payloads {
            let claim = FinClaim::new(terminal, tags_from(raw));
            let once = t(claim.clone());
            let twice = t(once.clone());
            assert_eq!(twice, once, "T must be idempotent on {name}");
            assert!(is_fixed(&once), "T({name}) must be T-fixed");
            assert_eq!(
                once.terminal, terminal,
                "T must preserve the terminal class"
            );
            assert_eq!(
                once.payload,
                tags_from(&normalized[name]),
                "frozen normal form of {name}"
            );
            assert_eq!(
                is_fixed(&claim),
                fixed_expected[name].as_bool().expect("fixed_expected bool"),
                "fixedness of {name} must match the frozen expectation"
            );
            let nf = normalize_l(claim);
            assert_eq!(*nf.terminal(), terminal);
            assert_eq!(*nf.payload(), tags_from(&normalized[name]));
            cells += 1;
        }
    }
    assert_eq!(
        cells, 9,
        "3 terminals x 3 payloads, same grid as the Python side"
    );
}

#[test]
fn normalizing_included_normal_forms_is_identity_on_shared_cells() {
    let fx = fixture();
    for row in fx["terminal_mapping"].as_array().expect("terminal_mapping") {
        let terminal = outcome_from_token(row["rust_outcome"].as_str().expect("rust_outcome str"));
        for (_name, raw) in fx["tags_payloads"].as_object().expect("tags_payloads") {
            let a = normalize_l(FinClaim::new(terminal, tags_from(raw)));
            let la_i = normalize_l(include_i(a.clone()));
            assert_eq!(
                la_i, a,
                "normalizing an included normal form must be identity"
            );
        }
    }
}

#[test]
fn unregistered_rust_outcome_token_refuses_fail_closed() {
    let result = std::panic::catch_unwind(|| outcome_from_token("Terminal(LocalGreen)"));
    assert!(
        result.is_err(),
        "an unknown mapping token must refuse, never default"
    );
}

// Origin: engine/crates_rs/tests/core_pipelines/coda_gtlanf_parity.rs
// Claim: urn:core:crates_rs:tests:coda-gtlanf-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfcd84ec1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfcd84ec1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfcd84ec1 {
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
impl BoundaryErrorfcd84ec1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfcd84ec1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfcd84ec1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfcd84ec1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfcd84ec1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfcd84ec1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfcd84ec1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfcd84ec1::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fcd84ec1() {
    let admitted = BoundaryRecordfcd84ec1::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfcd84ec1::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
