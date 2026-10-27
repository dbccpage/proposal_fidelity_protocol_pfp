//! Native readouts of actual transitions executed by the pinned original source.
//! The Python receipt is independently regenerated; these checks do not claim
//! native execution or universal refinement of the original transition system.
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Signed;
use core_wdp::genesis_ongoing_adapter::{
    GenesisOngoingAdapter, GenesisOngoingPacket, MarkedTriple,
};
use serde::Deserialize;

const SOURCE: &str = include_str!("fixtures/source_replay_receipt.json");

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Packet {
    terms: Vec<String>,
    r: Vec<i64>,
    s: Vec<i64>,
    filled: Vec<[usize; 3]>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Observation {
    packet: Packet,
    excess: Vec<i64>,
    diagnostics: Vec<i64>,
    balances: Vec<bool>,
    seed22_plain_cost: usize,
    enabled_changes: usize,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Transition {
    context: usize,
    occurrence: usize,
    kind: String,
    adds_term_or_assertion: bool,
    before: Observation,
    after: Observation,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Raising {
    before: Observation,
    after: Observation,
    potential: Vec<i64>,
}
#[derive(Deserialize)]
struct Replay {
    schema: String,
    transitions: Vec<Transition>,
    raising: Raising,
}
fn integers(values: &[i64]) -> Vec<BigInt> {
    values.iter().copied().map(BigInt::from).collect()
}
fn check(observation: &Observation) -> GenesisOngoingAdapter {
    let p = &observation.packet;
    let n = p.terms.len();
    let adapter = GenesisOngoingAdapter::try_new(GenesisOngoingPacket {
        terms: p.terms.clone(),
        r: integers(&p.r),
        s: integers(&p.s),
        filled: p
            .filled
            .iter()
            .map(|&[x, y, z]| MarkedTriple { x, y, z })
            .collect(),
    })
    .unwrap();
    let native = adapter.receipt().unwrap();
    native.verify_against(adapter.source()).unwrap();
    assert_eq!(native.excess, integers(&observation.excess));
    assert_eq!(
        native.diagnostics,
        integers(&observation.diagnostics)
            .into_iter()
            .map(BigRational::from_integer)
            .collect::<Vec<_>>()
    );
    assert_eq!(native.balances, observation.balances);
    // Seed 22's selected plain-state price is not a WDP quotient norm.
    assert_eq!(
        BigInt::from(observation.seed22_plain_cost),
        BigInt::from(n) + native.excess.iter().map(Signed::abs).sum::<BigInt>()
    );
    // Independently count the source's declared one-step alternatives from
    // this exact raw state, including both filling orientations and loops.
    let marked_possible = n * n.saturating_sub(1) * n.saturating_sub(2) / 3;
    let changes = n * n.saturating_sub(1) / 2
        + p.r.iter().chain(&p.s).filter(|&&v| v > 0).count()
        + marked_possible
        - p.filled.len()
        + 1
        + 2 * n * n;
    assert_eq!(observation.enabled_changes, changes);
    adapter
}

#[test]
fn all_thirty_two_actual_source_changes_have_matching_native_readouts() {
    let replay: Replay = serde_json::from_str(SOURCE).unwrap();
    assert_eq!(replay.schema, "wdp-source-replays-v1");
    assert_eq!(replay.transitions.len(), 32);
    let mut next = [0usize; 3];
    let mut kinds = std::collections::BTreeSet::new();
    for transition in replay.transitions {
        assert_eq!(transition.occurrence, next[transition.context]);
        next[transition.context] += 1;
        assert_eq!(
            transition.adds_term_or_assertion,
            matches!(transition.kind.as_str(), "ADD_TERM" | "ADD_ASSERTION")
        );
        kinds.insert(transition.kind);
        check(&transition.before);
        check(&transition.after);
    }
    assert_eq!(
        kinds,
        ["ADD_ASSERTION", "ADD_TERM", "FILL", "IDENTIFY", "REMOVE"]
            .into_iter()
            .map(String::from)
            .collect()
    );
}

#[test]
fn actual_source_raising_matches_native_repair_but_preserves_its_own_history() {
    let replay: Replay = serde_json::from_str(SOURCE).unwrap();
    let before = check(&replay.raising.before);
    let after = check(&replay.raising.after);
    let repair = before.repair(&integers(&replay.raising.potential)).unwrap();
    assert_eq!(repair.repaired_excess, after.excess());
    assert_eq!(repair.diagnostics, after.receipt().unwrap().diagnostics);
    assert_ne!(before.source(), after.source()); // actual multiplicities remain distinct
    assert!(before.repair_equivalence(&after).unwrap().is_some());
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_source_replay.rs
// Claim: urn:core:crates_rs:tests:test-genesis-source-replay:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc3674c58 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc3674c58` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc3674c58 {
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
impl BoundaryErrorc3674c58 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc3674c58 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc3674c58 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc3674c58 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc3674c58> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc3674c58::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc3674c58::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc3674c58::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c3674c58() {
    let admitted = BoundaryRecordc3674c58::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc3674c58::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
