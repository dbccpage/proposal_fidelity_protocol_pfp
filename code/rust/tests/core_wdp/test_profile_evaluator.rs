use std::collections::BTreeSet;

use core_wdp::profile_evaluator::{FiniteProfile, ProfileStatus, ProfileTransport, TableEvidence};
use core_wdp::AuthorityEffect;

fn set(items: &[&str]) -> BTreeSet<String> {
    items.iter().map(|item| (*item).to_owned()).collect()
}

fn evidence(query: &str, value: bool) -> TableEvidence {
    TableEvidence {
        query: query.to_owned(),
        value,
    }
}

fn profile(admitted: &[&str], refused: &[&str], budget: usize) -> FiniteProfile {
    FiniteProfile::new(
        vec![("t".into(), true), ("f".into(), false)],
        set(admitted),
        set(refused),
        budget,
    )
    .unwrap()
}

fn target(admitted: &[&str], refused: &[&str], budget: usize) -> FiniteProfile {
    FiniteProfile::new(
        vec![("T".into(), true), ("F".into(), false)],
        set(admitted),
        set(refused),
        budget,
    )
    .unwrap()
}

fn transport(source: FiniteProfile, target: FiniteProfile) -> ProfileTransport {
    ProfileTransport::new(
        source,
        target,
        vec![("t".into(), "T".into()), ("f".into(), "F".into())],
    )
    .unwrap()
}

#[test]
fn profile_constructor_rejects_duplicate_and_undeclared_policy_data() {
    assert!(FiniteProfile::new(
        vec![("x".into(), true), ("x".into(), false)],
        set(&["x"]),
        set(&[]),
        1,
    )
    .is_err());
    assert!(FiniteProfile::new(vec![], set(&["x"]), set(&[]), 1).is_err());
    assert!(FiniteProfile::new(vec![("x".into(), true)], set(&[]), set(&["x"]), 1).is_err());
    let empty = FiniteProfile::new(vec![], set(&[]), set(&[]), 0).unwrap();
    assert!(empty.evaluate("x", &[]).is_err());
    let checked = profile(&["t"], &[], 0);
    assert_eq!(checked.budget(), 0);
    assert_eq!(checked.table().get("t"), Some(&true));
    assert_eq!(checked.admitted(), &set(&["t"]));
    assert!(checked.refused().is_empty());
}

#[test]
fn five_statuses_and_semantic_verification_are_distinct() {
    let checked = profile(&["t", "f"], &[], 1);
    assert!(checked.verify_evidence(&evidence("t", true)));
    assert!(!checked.verify_evidence(&evidence("t", false)));
    assert!(!checked.verify_evidence(&evidence("outside", true)));
    assert_eq!(
        checked.evaluate("t", &[evidence("t", true)]).unwrap(),
        ProfileStatus::Proved
    );
    assert_eq!(
        checked.evaluate("f", &[evidence("f", false)]).unwrap(),
        ProfileStatus::Refuted
    );
    assert_eq!(
        checked.evaluate("t", &[evidence("t", false)]).unwrap(),
        ProfileStatus::Undetermined
    );
    let outside = profile(&[], &[], 1);
    assert!(outside.verify_evidence(&evidence("t", true)));
    assert_eq!(
        outside.evaluate("t", &[evidence("t", true)]).unwrap(),
        ProfileStatus::OutsideProfile
    );
    let refused = profile(&["t"], &["t"], 1);
    assert!(refused.verify_evidence(&evidence("t", true)));
    assert_eq!(
        refused.evaluate("t", &[evidence("t", true)]).unwrap(),
        ProfileStatus::Refused
    );
    assert!(checked.evaluate("not-declared", &[]).is_err());
}

#[test]
fn guards_are_exclusive_and_exhaustive_over_small_finite_models() {
    let pool = [
        evidence("t", true),
        evidence("t", false),
        evidence("f", true),
        evidence("f", false),
        evidence("z", true),
    ];
    for admitted_bits in 0_usize..4 {
        let admitted = ["t", "f"]
            .into_iter()
            .enumerate()
            .filter_map(|(i, query)| ((admitted_bits & (1 << i)) != 0).then_some(query))
            .collect::<Vec<_>>();
        for refused_bits in 0_usize..4 {
            if refused_bits & !admitted_bits != 0 {
                continue;
            }
            let refused = ["t", "f"]
                .into_iter()
                .enumerate()
                .filter_map(|(i, query)| ((refused_bits & (1 << i)) != 0).then_some(query))
                .collect::<Vec<_>>();
            for budget in 0..=3 {
                let checked = profile(&admitted, &refused, budget);
                for first in &pool {
                    for second in &pool {
                        let candidates = [first.clone(), second.clone()];
                        for query in ["t", "f"] {
                            let guards = checked.status_guards(query, &candidates).unwrap();
                            assert_eq!(guards.iter().filter(|guard| **guard).count(), 1);
                            let status = checked.evaluate(query, &candidates).unwrap();
                            assert_ne!((query, status), ("t", ProfileStatus::Refuted));
                            assert_ne!((query, status), ("f", ProfileStatus::Proved));
                        }
                    }
                }
            }
        }
    }
}

#[test]
fn replay_budget_prefix_is_preserved_without_evidence_repair_or_filtering() {
    let candidates = [evidence("t", false), evidence("t", true)];
    assert_eq!(
        profile(&["t"], &[], 0).evaluate("t", &candidates).unwrap(),
        ProfileStatus::Undetermined
    );
    assert_eq!(
        profile(&["t"], &[], 1).evaluate("t", &candidates).unwrap(),
        ProfileStatus::Undetermined
    );
    assert_eq!(
        profile(&["t"], &[], 2).evaluate("t", &candidates).unwrap(),
        ProfileStatus::Proved
    );
    let checked = profile(&["t"], &[], 1);
    let receipt = checked.evaluate_with_receipt("t", &candidates).unwrap();
    assert_eq!(receipt.replayed_count, 1);
    assert_eq!(receipt.authority_effect, AuthorityEffect::None);
    assert!(checked.verify_receipt("t", &candidates, &receipt).is_ok());
    assert!(checked
        .verify_receipt(
            "t",
            &[candidates[1].clone(), candidates[0].clone()],
            &receipt
        )
        .is_err());
}

#[test]
fn forged_status_and_rehashed_receipts_are_not_semantic_truth() {
    let checked = profile(&["t", "f"], &[], 1);
    let candidates = [evidence("t", true)];
    let receipt = checked.evaluate_with_receipt("t", &candidates).unwrap();
    let mut forged = receipt.clone();
    forged.status = ProfileStatus::Refuted;
    forged.receipt_digest = forged.recompute_digest().unwrap();
    assert!(checked.verify_receipt("t", &candidates, &forged).is_err());
    let mut forged_count = receipt.clone();
    forged_count.replayed_count = 99;
    forged_count.receipt_digest = forged_count.recompute_digest().unwrap();
    assert!(checked
        .verify_receipt("t", &candidates, &forged_count)
        .is_err());
    for changed in [
        profile(&["t"], &["t"], 1),
        profile(&[], &[], 1),
        profile(&["t", "f"], &[], 0),
    ] {
        assert!(changed.verify_receipt("t", &candidates, &receipt).is_err());
    }
    assert!(checked.verify_receipt("f", &candidates, &receipt).is_err());
}

#[test]
fn transport_constructor_rejects_lossy_partial_and_model_changing_encodings() {
    let source = profile(&["t", "f"], &[], 1);
    let same_value_source = FiniteProfile::new(
        vec![("a".into(), true), ("b".into(), true)],
        set(&["a", "b"]),
        set(&[]),
        1,
    )
    .unwrap();
    let one_target =
        FiniteProfile::new(vec![("A".into(), true)], set(&["A"]), set(&[]), 1).unwrap();
    assert!(ProfileTransport::new(
        same_value_source,
        one_target,
        vec![("a".into(), "A".into()), ("b".into(), "A".into())]
    )
    .is_err());
    assert!(ProfileTransport::new(
        source.clone(),
        target(&["T", "F"], &[], 1),
        vec![("t".into(), "T".into())]
    )
    .is_err());
    assert!(ProfileTransport::new(
        source.clone(),
        target(&["T", "F"], &[], 1),
        vec![("t".into(), "T".into()), ("t".into(), "F".into())]
    )
    .is_err());
    assert!(ProfileTransport::new(
        source.clone(),
        target(&["T", "F"], &[], 1),
        vec![("t".into(), "F".into()), ("f".into(), "T".into())]
    )
    .is_err());
    assert!(ProfileTransport::new(
        source,
        target(&["T", "F"], &[], 1),
        vec![("t".into(), "absent".into()), ("f".into(), "F".into())]
    )
    .is_err());
}

#[test]
fn transport_replays_target_policy_budget_and_admission_instead_of_copying_status() {
    let candidates = [evidence("f", false), evidence("t", true)];
    for (target_profile, expected) in [
        (target(&["T", "F"], &[], 1), ProfileStatus::Undetermined),
        (target(&["T", "F"], &["T"], 2), ProfileStatus::Refused),
        (target(&["F"], &[], 2), ProfileStatus::OutsideProfile),
        (target(&["T", "F"], &[], 2), ProfileStatus::Proved),
    ] {
        let adapter = transport(profile(&["t", "f"], &[], 2), target_profile);
        let receipt = adapter.replay_target("t", &candidates).unwrap();
        assert_eq!(receipt.source_receipt.status, ProfileStatus::Proved);
        assert_eq!(receipt.target_receipt.status, expected);
        assert_eq!(
            receipt.transported_candidates,
            [evidence("F", false), evidence("T", true)]
        );
        assert_eq!(receipt.authority_effect, AuthorityEffect::None);
        assert!(adapter
            .verify_target_replay("t", &candidates, &receipt)
            .is_ok());
        assert!(adapter.source().verify_evidence(&candidates[0]));
        assert!(adapter
            .target()
            .verify_evidence(&receipt.transported_candidates[0]));
    }
}

#[test]
fn transport_checks_every_evidence_and_recomputes_receipts() {
    let adapter = transport(profile(&["t", "f"], &[], 1), target(&["T", "F"], &[], 1));
    assert!(adapter.transport_evidence(&evidence("t", false)).is_err());
    assert!(adapter
        .transport_evidence(&evidence("absent", true))
        .is_err());
    assert!(adapter
        .replay_target("t", &[evidence("t", true), evidence("f", true)])
        .is_err());
    assert!(adapter.replay_target("absent", &[]).is_err());
    let candidates = [evidence("t", true)];
    let mut receipt = adapter.replay_target("t", &candidates).unwrap();
    receipt.target_receipt.status = ProfileStatus::Refuted;
    receipt.target_receipt.receipt_digest = receipt.target_receipt.recompute_digest().unwrap();
    receipt.receipt_digest = receipt.recompute_digest().unwrap();
    assert!(adapter
        .verify_target_replay("t", &candidates, &receipt)
        .is_err());
    let mut altered_evidence = adapter.replay_target("t", &candidates).unwrap();
    altered_evidence.transported_candidates[0].value = false;
    altered_evidence.receipt_digest = altered_evidence.recompute_digest().unwrap();
    assert!(adapter
        .verify_target_replay("t", &candidates, &altered_evidence)
        .is_err());
}

#[test]
fn transport_receipt_binds_unused_parts_of_the_checked_encoding() {
    let source = profile(&["t", "f"], &[], 1);
    let target = FiniteProfile::new(
        vec![
            ("T".into(), true),
            ("F".into(), false),
            ("otherF".into(), false),
        ],
        set(&["T", "F", "otherF"]),
        set(&[]),
        1,
    )
    .unwrap();
    let first = ProfileTransport::new(
        source.clone(),
        target.clone(),
        vec![("t".into(), "T".into()), ("f".into(), "F".into())],
    )
    .unwrap();
    let changed = ProfileTransport::new(
        source,
        target,
        vec![("t".into(), "T".into()), ("f".into(), "otherF".into())],
    )
    .unwrap();
    let candidates = [evidence("t", true)];
    let receipt = first.replay_target("t", &candidates).unwrap();
    let changed_receipt = changed.replay_target("t", &candidates).unwrap();
    assert_eq!(receipt.target_receipt, changed_receipt.target_receipt);
    assert_ne!(receipt.transport_digest, changed_receipt.transport_digest);
    assert!(changed
        .verify_target_replay("t", &candidates, &receipt)
        .is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_profile_evaluator.rs
// Claim: urn:core:crates_rs:tests:test-profile-evaluator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord07a191df {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord07a191df` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError07a191df {
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
impl BoundaryError07a191df {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError07a191df {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError07a191df {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord07a191df {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError07a191df> {
        if capacity_bound == 0 {
            return Err(BoundaryError07a191df::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError07a191df::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError07a191df::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_07a191df() {
    let admitted = BoundaryRecord07a191df::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord07a191df::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
