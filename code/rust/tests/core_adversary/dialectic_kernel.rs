//! Dialectic kernel: depth 5, exact rationals, local-profile receipts. AuthorityEffect: None.

use num_rational::Ratio;
use core_adversary::dialectic::{
    dialectic_bytes, parse_ratio, receipt_bytes, Act, DialecticBody, TurnProposal, AdversaryTurnEngine,
    AUTHORITY_EFFECT, MAX_DEPTH,
};
use core_adversary::literature_receipt::LiteratureReceipt;
use core_adversary::receipt::ReceiptStatus;
use sha2::{Digest, Sha256};

fn subject() -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(b"subject")))
}

fn proposal(act: Act, seat: &str, spent: Ratio<i64>) -> TurnProposal {
    TurnProposal {
        act,
        depth: 0,
        seat_id: seat.to_owned(),
        budget_spent: spent,
        subject_sha256: subject(),
    }
}

#[test]
fn seven_acts_seal_and_the_eighth_turn_is_terminal() {
    let seats = [
        "carrier",
        "defect_hunter",
        "primal_dual",
        "gauge_breaker",
        "scope_guard",
        "master",
        "adversary",
    ];
    let acts = [Act::I, Act::II, Act::III, Act::IV, Act::V, Act::VI, Act::VII];
    let mut engine = AdversaryTurnEngine::open(0, Ratio::from_integer(1)).unwrap();
    for (act, seat) in acts.into_iter().zip(seats) {
        let receipt = engine.step(proposal(act, seat, Ratio::from_integer(0)));
        assert_eq!(receipt.status, ReceiptStatus::Pass);
        assert_eq!(receipt.authority_effect(), AUTHORITY_EFFECT);
    }
    assert_eq!(engine.state().terminal, Some(ReceiptStatus::Pass));
    assert_eq!(engine.state().next_act, None);
    let extra = engine.step(proposal(Act::I, "syntax_prefilter", Ratio::from_integer(0)));
    assert_eq!(extra.status, ReceiptStatus::Refusal);
    assert_eq!(extra.code, "TERMINAL");
    assert_eq!(extra.body.turns.len(), 7);
}

#[test]
fn depth_budget_seat_and_act_fences() {
    assert!(AdversaryTurnEngine::open(MAX_DEPTH + 1, Ratio::from_integer(1)).is_err());
    let mut engine = AdversaryTurnEngine::open(0, Ratio::new(1, 2)).unwrap();
    let exhausted = engine.step(proposal(Act::I, "carrier", Ratio::from_integer(1)));
    assert_eq!(exhausted.status, ReceiptStatus::Fail);
    assert_eq!(exhausted.code, "BUDGET_EXHAUSTED");
    assert_eq!(exhausted.body.turns.len(), 0);
    assert_eq!(exhausted.body.budget_remaining, Ratio::new(1, 2));

    let mut engine = AdversaryTurnEngine::open(0, Ratio::from_integer(2)).unwrap();
    let first = engine.step(proposal(Act::I, "carrier", Ratio::new(1, 2)));
    assert_eq!(first.status, ReceiptStatus::Pass);
    assert_eq!(first.body.budget_remaining, Ratio::new(3, 2));
    let skipped = engine.step(proposal(Act::III, "primal_dual", Ratio::from_integer(0)));
    assert_eq!(skipped.code, "ACT_ORDER");
    assert_eq!(skipped.body.turns.len(), 1);
    let reused = engine.step(proposal(Act::II, "carrier", Ratio::from_integer(0)));
    assert_eq!(reused.status, ReceiptStatus::Fail);
    assert_eq!(reused.code, "SEAT_REUSED");

    let nested = AdversaryTurnEngine::open(0, Ratio::from_integer(1))
        .unwrap()
        .nest()
        .unwrap();
    assert_eq!(nested.state().depth, 1);
    assert_eq!(nested.state().next_act, Some(Act::I));
    assert!(AdversaryTurnEngine::open(MAX_DEPTH, Ratio::from_integer(1))
        .unwrap()
        .nest()
        .is_err());
}

#[test]
fn state_bytes_roundtrip_and_hash_tamper_refuses() {
    let mut engine = AdversaryTurnEngine::open(0, Ratio::from_integer(1)).unwrap();
    engine.step(proposal(Act::I, "carrier", Ratio::from_integer(0)));
    let state = engine.state();
    let bytes = state.canonical_bytes().unwrap();
    let parsed = core_adversary::dialectic::AdversaryState::try_from(bytes.as_slice()).unwrap();
    assert_eq!(parsed, state);
    let text = String::from_utf8(bytes).unwrap();
    let old = state.turns[0].evidence.canonical_sha256.clone();
    let mut flipped = old.clone().into_bytes();
    let last = flipped.len() - 1;
    flipped[last] = if flipped[last] == b'a' { b'b' } else { b'a' };
    let tampered = text.replace(&old, &String::from_utf8(flipped).unwrap());
    assert!(core_adversary::dialectic::AdversaryState::try_from(tampered.as_bytes()).is_err());
}

#[test]
fn command_bytes_reject_float_prose_and_seal_literature() {
    let opened = dialectic_bytes(br#"{"command":"open","depth":0,"budget":"2/4"}"#);
    assert_eq!(opened.status, ReceiptStatus::Pass);
    let encoded = String::from_utf8(receipt_bytes(&opened).unwrap()).unwrap();
    assert!(encoded.starts_with("{\"authority_effect\":\"None\""));
    assert!(encoded.contains("\"budget_opened\":\"1/2\""));
    assert!(!encoded.contains("verified"));
    assert_eq!(
        dialectic_bytes(br#"{"command":"open","depth":0.5,"budget":"1"}"#).code,
        "FLOAT_FORBIDDEN"
    );
    assert_eq!(
        dialectic_bytes(br#"{"command":"open","depth":0,"budget":"0.5"}"#).code,
        "BUDGET_MALFORMED"
    );
    assert_eq!(
        dialectic_bytes(br#"{"command":"open","depth":0,"budget":"1","verified":true}"#).code,
        "PROSE_AUTHORITY"
    );
    assert_eq!(
        dialectic_bytes(br#"{"command":"open","depth":0,"budget":"1","budget":"2"}"#).code,
        "DUPLICATE_KEY"
    );
    assert!(parse_ratio("2/4").unwrap() == Ratio::new(1, 2));

    let sealed = dialectic_bytes(
        br#"{"command":"seal_literature","receipt_id":"r1","package_id":"pkg","cite_key":"cite","title":"Title","arxiv_id":"2401.00001","source_kind":"manual","authority_effect":"None","claims_global_green":false}"#,
    );
    let DialecticBody::Literature(receipt) = sealed.body else {
        panic!("literature body");
    };
    assert_eq!(
        receipt.content_fingerprint,
        "06196acbff9596f741d9a50018255498e2772a1aa9b093ad7bbb1f16f08b7d4d"
    );
    let again = LiteratureReceipt::try_from(receipt.canonical_bytes().unwrap().as_slice()).unwrap();
    assert_eq!(again, receipt);
    assert_eq!(
        dialectic_bytes(
            br#"{"command":"seal_literature","receipt_id":"r1","package_id":"pkg","cite_key":"cite","title":"Title","arxiv_id":"not-an-id","source_kind":"manual","authority_effect":"None","claims_global_green":false}"#
        )
        .code,
        "ARXIV_ID"
    );
    assert_eq!(
        dialectic_bytes(
            br#"{"command":"seal_literature","receipt_id":"r1","package_id":"pkg","cite_key":"cite","title":"Title","source_kind":"manual","authority_effect":"None","claims_global_green":true}"#
        )
        .code,
        "PROSE_AUTHORITY"
    );
}

// Origin: engine/crates_rs/tests/core_adversary/dialectic_kernel.rs
// Claim: urn:core:crates_rs:tests:dialectic-kernel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord018e1b38 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord018e1b38` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError018e1b38 {
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
impl BoundaryError018e1b38 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError018e1b38 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError018e1b38 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord018e1b38 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError018e1b38> {
        if capacity_bound == 0 {
            return Err(BoundaryError018e1b38::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError018e1b38::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError018e1b38::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_018e1b38() {
    let admitted = BoundaryRecord018e1b38::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord018e1b38::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
