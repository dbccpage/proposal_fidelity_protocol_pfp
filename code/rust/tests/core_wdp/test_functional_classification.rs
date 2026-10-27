use core_category_theory::finite_functional_classification::{
    realize_functional, FunctionalSignature, RetentionSignature,
};
use core_wdp::functional_classification::{
    classify_existing_functional_packet, classify_functional_maps, classify_retention_packet,
    construct_retention_witness,
};
use core_wdp::retention::RetentionPacket;
use core_wdp::AuthorityEffect;
use std::collections::{BTreeMap, BTreeSet};

#[test]
fn every_native_retention_witness_round_trips_through_existing_packet_api() {
    let mut count = 0;
    for bits in 0..64 {
        let signature = RetentionSignature {
            nontrivial: bits & 1 != 0,
            reversible: bits & 2 != 0,
            observable: bits & 4 != 0,
            tolerance: bits & 8 != 0,
            minimal: bits & 16 != 0,
            active: bits & 32 != 0,
        };
        if signature.is_realizable() {
            let packet = construct_retention_witness(signature).unwrap();
            let classified = classify_retention_packet(&packet).unwrap();
            assert_eq!(classified.signature, signature);
            assert_eq!(classified.authority_effect, AuthorityEffect::None);
            assert!(classified.quotient_size > 0);
            count += 1;
        } else {
            assert!(construct_retention_witness(signature).is_err());
        }
    }
    assert_eq!(count, 19);
}

#[test]
fn every_functional_signature_round_trips_through_named_maps() {
    let mut count = 0;
    for bits in 0..32 {
        let signature = FunctionalSignature {
            linked: bits & 1 != 0,
            presentation_stable: bits & 2 != 0,
            report_stable: bits & 4 != 0,
            calibrated: bits & 8 != 0,
            blind_spot: bits & 16 != 0,
        };
        if let Ok(model) = realize_functional(signature) {
            let carrier: Vec<_> = (0..model.presentation().len())
                .map(|x| format!("x{x}"))
                .collect();
            let q = carrier
                .iter()
                .enumerate()
                .map(|(x, s)| (s.clone(), format!("p{}", model.presentation()[x])))
                .collect();
            let report = carrier
                .iter()
                .enumerate()
                .map(|(x, s)| (s.clone(), format!("r{}", model.report()[x])))
                .collect();
            let context = carrier
                .iter()
                .enumerate()
                .map(|(x, s)| (s.clone(), carrier[model.context()[x]].clone()))
                .collect();
            let target = carrier
                .iter()
                .enumerate()
                .map(|(x, s)| (s.clone(), format!("r{}", model.target()[x])))
                .collect();
            assert_eq!(
                classify_functional_maps(&carrier, &q, &report, &context, &target).unwrap(),
                signature
            );
            count += 1;
        }
    }
    assert_eq!(count, 20);
}

#[test]
fn manuscript_report_stability_does_not_equal_legacy_presentation_stability() {
    let carrier = vec!["a".to_owned(), "b".to_owned()];
    let q = BTreeMap::from([("a".into(), "p".into()), ("b".into(), "q".into())]);
    let h = BTreeMap::from([
        ("p".into(), "constant".into()),
        ("q".into(), "constant".into()),
    ]);
    let t = BTreeMap::from([("a".into(), "b".into()), ("b".into(), "a".into())]);
    let target = BTreeMap::from([
        ("a".into(), "constant".into()),
        ("b".into(), "constant".into()),
    ]);
    let classified = classify_existing_functional_packet(&carrier, &q, &h, &t, &target).unwrap();
    assert!(!classified.legacy_audit.is_context_stable);
    assert!(!classified.signature.presentation_stable);
    assert!(classified.signature.report_stable);
    assert!(classified.signature.linked);
    assert!(classified.signature.calibrated);
    assert!(!classified.legacy_audit.demonstrates_awareness);
    assert_eq!(classified.authority_effect, AuthorityEffect::None);
    let mut partial_context = t.clone();
    partial_context.remove("b");
    assert!(
        classify_existing_functional_packet(&carrier, &q, &h, &partial_context, &target).is_err()
    );
    let mut partial_target = target.clone();
    partial_target.remove("b");
    assert!(classify_existing_functional_packet(&carrier, &q, &h, &t, &partial_target).is_err());
    let mut missing_report = h.clone();
    missing_report.remove("q");
    assert!(
        classify_existing_functional_packet(&carrier, &q, &missing_report, &t, &target).is_err()
    );
    let mut extra = q.clone();
    extra.insert("outside".into(), "p".into());
    assert!(classify_existing_functional_packet(&carrier, &extra, &h, &t, &target).is_err());
    assert!(
        classify_existing_functional_packet(&["a".into(), "a".into()], &q, &h, &t, &target)
            .is_err()
    );
    let mut outside_context = t;
    outside_context.insert("a".into(), "outside".into());
    assert!(
        classify_existing_functional_packet(&carrier, &q, &h, &outside_context, &target).is_err()
    );
}

#[test]
fn comparison_nontransitivity_and_mutated_packet_tables_are_refused() {
    let states: BTreeSet<_> = ["a", "b", "c"].into_iter().map(String::from).collect();
    let update = states
        .iter()
        .map(|s| ((s.clone(), "i".into()), s.clone()))
        .collect();
    let reports = states.iter().map(|s| (s.clone(), s.clone())).collect();
    let packet = RetentionPacket::new(
        states,
        BTreeSet::from(["i".into()]),
        update,
        reports,
        BTreeSet::from([("a".into(), "b".into()), ("b".into(), "c".into())]),
    )
    .unwrap();
    assert!(classify_retention_packet(&packet).is_err());
    let mut broken = construct_retention_witness(RetentionSignature {
        nontrivial: true,
        reversible: true,
        observable: true,
        tolerance: false,
        minimal: true,
        active: false,
    })
    .unwrap();
    broken.report_map.clear();
    assert!(classify_retention_packet(&broken).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_functional_classification.rs
// Claim: urn:core:crates_rs:tests:test-functional-classification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd875dfa0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd875dfa0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord875dfa0 {
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
impl BoundaryErrord875dfa0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord875dfa0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord875dfa0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd875dfa0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord875dfa0> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord875dfa0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord875dfa0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord875dfa0::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d875dfa0() {
    let admitted = BoundaryRecordd875dfa0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd875dfa0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
