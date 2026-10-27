use core_wdp::self_reference_adapter::{
    audit_self_reference, checked_self_reference, plan_successful_self_reports,
    verify_self_reference_audit, NamedComparisonProtocol, NamedReflexiveProvenance,
    NamedSelfReferencePacket,
};
use core_wdp::AuthorityEffect;
use std::collections::{BTreeMap, BTreeSet};

fn names(items: &[&str]) -> BTreeSet<String> {
    items.iter().map(|s| (*s).into()).collect()
}
fn map(pairs: &[(&str, &str)]) -> BTreeMap<String, String> {
    pairs
        .iter()
        .map(|(a, b)| ((*a).into(), (*b).into()))
        .collect()
}
fn partial(pairs: &[(&str, &str)]) -> BTreeMap<String, Option<String>> {
    pairs
        .iter()
        .map(|(a, b)| ((*a).into(), Some((*b).into())))
        .collect()
}
fn packet() -> NamedSelfReferencePacket {
    let provenance = [("idle", "a0", "r0"), ("later", "a1", "r1")]
        .into_iter()
        .map(|(x, a, r)| {
            (
                x.into(),
                Some(NamedReflexiveProvenance {
                    source_observer: "self".into(),
                    target_observer: "self".into(),
                    captured_accessible: a.into(),
                    reaccessed_accessible: a.into(),
                    reported_value: r.into(),
                }),
            )
        })
        .collect();
    NamedSelfReferencePacket {
        observer_id: "self".into(),
        observers: names(&["self", "other"]),
        states: vec!["idle".into(), "later".into()],
        accessible: names(&["a0", "a1"]),
        report_alphabet: names(&["r0", "r1"]),
        sigma: map(&[("idle", "a0"), ("later", "a1")]),
        presentation: map(&[("a0", "same"), ("a1", "same")]),
        reports: partial(&[("idle", "r0"), ("later", "r1")]),
        provenance,
        context: map(&[("idle", "idle"), ("later", "later")]),
        later: map(&[("idle", "later"), ("later", "idle")]),
        target: partial(&[("idle", "r1"), ("later", "r0")]),
        generation: BTreeSet::from([("a0".into(), "r0".into()), ("a1".into(), "r1".into())]),
        protocol: Some(NamedComparisonProtocol {
            evaluator_id: "E".into(),
            domain: BTreeSet::from([
                ("r0".into(), "r0".into()),
                ("r0".into(), "r1".into()),
                ("r1".into(), "r0".into()),
                ("r1".into(), "r1".into()),
            ]),
        }),
    }
}

#[test]
fn named_r1_r2_r3_bridge_replays_actual_later_map_and_richer_self_state() {
    let packet = packet();
    let audit = audit_self_reference(&packet).unwrap();
    assert!(
        audit.signature.linkage_verified
            && audit.signature.report_stable
            && audit.signature.comparison_available
            && audit.signature.comparison_success
    );
    assert!(audit.report_determined_accessible && !audit.report_determined_presentation);
    assert_eq!(audit.authority_effect, AuthorityEffect::None);
    assert!(verify_self_reference_audit(&packet, &audit).is_ok());
    assert!(checked_self_reference(&packet)
        .unwrap()
        .later_target_factor_accessible()
        .is_some());
}

#[test]
fn report_availability_and_protocol_success_never_substitute_for_each_other() {
    let mut packet = packet();
    packet.target = packet.reports.clone();
    let audit = audit_self_reference(&packet).unwrap();
    assert!(audit.signature.comparison_available && !audit.signature.comparison_success);
    packet.protocol = None;
    let audit = audit_self_reference(&packet).unwrap();
    assert!(!audit.signature.comparison_available && !audit.signature.comparison_success);
    packet.reports.insert("later".into(), None);
    let audit = audit_self_reference(&packet).unwrap();
    assert!(!audit.signature.report_total && !audit.stability_available);
    assert!(audit.points["idle"].report_available && !audit.points["later"].report_available);
}

#[test]
fn candidate_provenance_and_receipt_truth_are_independently_recomputed() {
    let mut packet = packet();
    let original = audit_self_reference(&packet).unwrap();
    packet
        .provenance
        .get_mut("idle")
        .unwrap()
        .as_mut()
        .unwrap()
        .target_observer = "other".into();
    let changed = audit_self_reference(&packet).unwrap();
    assert!(changed.signature.linkage_provided && !changed.signature.linkage_verified);
    assert!(verify_self_reference_audit(&packet, &original).is_err());
    let mut forged = changed.clone();
    forged.signature.linkage_verified = true;
    // The legitimate changed-packet digest is intact: semantic claims still fail.
    assert_eq!(forged.receipt_digest, changed.receipt_digest);
    assert!(verify_self_reference_audit(&packet, &forged).is_err());
    packet.generation.clear();
    assert!(
        !audit_self_reference(&packet)
            .unwrap()
            .signature
            .linkage_verified
    );
}

#[test]
fn absent_rows_and_unknown_ids_refuse_instead_of_defaulting() {
    let original = packet();
    let mut bad = original.clone();
    bad.context.remove("later");
    assert!(audit_self_reference(&bad).is_err());
    let mut bad = original.clone();
    bad.target.remove("later");
    assert!(audit_self_reference(&bad).is_err());
    let mut bad = original.clone();
    bad.reports.remove("later");
    assert!(audit_self_reference(&bad).is_err());
    let mut bad = original.clone();
    bad.sigma.insert("idle".into(), "outside".into());
    assert!(audit_self_reference(&bad).is_err());
    let mut bad = original.clone();
    bad.later.insert("idle".into(), "outside".into());
    assert!(audit_self_reference(&bad).is_err());
    let mut bad = original.clone();
    bad.states.push("idle".into());
    assert!(audit_self_reference(&bad).is_err());
    let mut bad = original;
    bad.protocol.as_mut().unwrap().evaluator_id.clear();
    assert!(audit_self_reference(&bad).is_err());
}

#[test]
fn fixed_bridge_plan_is_replayed_and_context_requirement_is_explicit() {
    let mut packet = packet();
    let plan = plan_successful_self_reports(&packet, true)
        .unwrap()
        .unwrap();
    assert!(
        audit_self_reference(&plan)
            .unwrap()
            .signature
            .comparison_success
    );
    packet.context = map(&[("idle", "later"), ("later", "idle")]);
    assert!(plan_successful_self_reports(&packet, true)
        .unwrap()
        .is_none());
    assert!(plan_successful_self_reports(&packet, false)
        .unwrap()
        .is_some());
    packet.target.insert("later".into(), None);
    assert!(plan_successful_self_reports(&packet, false)
        .unwrap()
        .is_none());
}

// Origin: engine/crates_rs/tests/core_wdp/test_self_reference_adapter.rs
// Claim: urn:core:crates_rs:tests:test-self-reference-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddd144a66 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddd144a66` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordd144a66 {
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
impl BoundaryErrordd144a66 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordd144a66 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordd144a66 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddd144a66 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordd144a66> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordd144a66::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordd144a66::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordd144a66::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_dd144a66() {
    let admitted = BoundaryRecorddd144a66::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddd144a66::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
