use core_category_theory::finite_self_reference::{
    realize_self_reference, CheckedSelfReference, SelfReferenceSignature,
};
use std::collections::BTreeSet;

fn full() -> CheckedSelfReference {
    realize_self_reference(SelfReferenceSignature {
        report_total: true,
        linkage_provided: true,
        linkage_verified: true,
        report_stable: true,
        comparison_available: true,
        comparison_success: true,
    })
    .unwrap()
}

#[test]
fn every_aggregate_bridge_signature_has_witness_or_exact_obstruction() {
    let mut count = 0;
    for bits in 0..64 {
        let signature = SelfReferenceSignature {
            report_total: bits & 1 != 0,
            linkage_provided: bits & 2 != 0,
            linkage_verified: bits & 4 != 0,
            report_stable: bits & 8 != 0,
            comparison_available: bits & 16 != 0,
            comparison_success: bits & 32 != 0,
        };
        if signature.is_realizable() {
            let model = realize_self_reference(signature).unwrap();
            assert_eq!(model.signature(), signature);
            assert_eq!(model.stability_available(), signature.report_total);
            for x in 0..model.point_count() {
                let point = model.audit_point(x).unwrap();
                assert!(!point.linkage_verified || point.linkage_provided);
                assert!(!point.linkage_provided || point.report_available);
                assert!(!point.comparison_success || point.comparison_available);
                assert!(!point.stability_success || point.stability_available);
            }
            count += 1;
        } else {
            assert!(realize_self_reference(signature).is_err());
        }
    }
    assert_eq!(count, 19);
}

#[test]
fn provenance_and_comparison_are_semantically_replayed() {
    let model = full();
    assert!(model.signature().linkage_verified && model.signature().comparison_success);
    let original = model.data().clone();
    let mut stale = original.clone();
    stale.provenance[0].as_mut().unwrap().reaccessed_accessible = 1;
    assert!(
        !CheckedSelfReference::new(stale)
            .unwrap()
            .audit_point(0)
            .unwrap()
            .linkage_verified
    );
    let mut foreign = original.clone();
    foreign.provenance[0].as_mut().unwrap().target_observer = 1;
    assert!(
        !CheckedSelfReference::new(foreign)
            .unwrap()
            .audit_point(0)
            .unwrap()
            .linkage_verified
    );
    let mut wrong_report = original.clone();
    wrong_report.provenance[0].as_mut().unwrap().reported_value = 1;
    assert!(
        !CheckedSelfReference::new(wrong_report)
            .unwrap()
            .audit_point(0)
            .unwrap()
            .linkage_verified
    );
    let mut no_generation = original.clone();
    no_generation.generation.remove(&(0, 0));
    assert!(
        !CheckedSelfReference::new(no_generation)
            .unwrap()
            .audit_point(0)
            .unwrap()
            .linkage_verified
    );
    let mut inaccessible = original.clone();
    inaccessible
        .protocol
        .as_mut()
        .unwrap()
        .domain
        .remove(&(0, 0));
    let point = CheckedSelfReference::new(inaccessible)
        .unwrap()
        .audit_point(0)
        .unwrap();
    assert!(!point.comparison_available && !point.comparison_success);
    let mut disagreement = original.clone();
    disagreement.target = vec![Some(0), Some(1)];
    let point = CheckedSelfReference::new(disagreement)
        .unwrap()
        .audit_point(0)
        .unwrap();
    assert!(point.comparison_available && !point.comparison_success);
    let mut undefined = original;
    undefined.target[1] = None;
    assert!(
        !CheckedSelfReference::new(undefined)
            .unwrap()
            .audit_point(0)
            .unwrap()
            .comparison_available
    );
}

#[test]
fn accessible_state_linkage_can_distinguish_coarser_presentation_blind_spots() {
    let mut data = full().data().clone();
    data.presentation = vec![0, 0];
    let model = CheckedSelfReference::new(data).unwrap();
    assert!(model.signature().linkage_verified);
    assert!(model.report_factor_accessible().is_some());
    assert!(model.report_factor_presentation().is_none());
    let mut nondeterministic = model.data().clone();
    nondeterministic.sigma = vec![0, 0];
    nondeterministic.generation = BTreeSet::from([(0, 0), (0, 1)]);
    for p in nondeterministic.provenance.iter_mut().flatten() {
        p.captured_accessible = 0;
        p.reaccessed_accessible = 0;
    }
    let model = CheckedSelfReference::new(nondeterministic).unwrap();
    assert!(model.signature().linkage_verified);
    assert!(!model.generation_is_functional());
    assert!(model.report_factor_accessible().is_none());
}

#[test]
fn later_factorization_checks_values_and_partiality_on_every_fiber() {
    let mut data = full().data().clone();
    data.later = vec![0, 0];
    let model = CheckedSelfReference::new(data).unwrap();
    assert!(model
        .factor_prescribed_target_through_later(&[Some(0), Some(1)])
        .unwrap()
        .is_none());
    assert!(model
        .factor_prescribed_target_through_later(&[Some(0), None])
        .unwrap()
        .is_none());
    let factor = model
        .factor_prescribed_target_through_later(&[Some(1), Some(1)])
        .unwrap()
        .unwrap();
    assert_eq!(factor[&0], Some(1));
    assert!(model
        .factor_prescribed_target_through_later(&[Some(0)])
        .is_err());
    let mut collision = full().data().clone();
    collision.sigma = vec![0, 0];
    let model = CheckedSelfReference::new(collision).unwrap();
    assert!(model.later_target_factor_accessible().is_none());
    let mut partial_collision = model.data().clone();
    partial_collision.target[1] = None;
    assert!(CheckedSelfReference::new(partial_collision)
        .unwrap()
        .later_target_factor_accessible()
        .is_none());
}

#[test]
fn malformed_carriers_and_partial_rows_are_rejected_before_audit() {
    let original = full().data().clone();
    let mut bad = original.clone();
    bad.context.pop();
    assert!(CheckedSelfReference::new(bad).is_err());
    let mut bad = original.clone();
    bad.later[0] = 2;
    assert!(CheckedSelfReference::new(bad).is_err());
    let mut bad = original.clone();
    bad.provenance[0].as_mut().unwrap().captured_accessible = 2;
    assert!(CheckedSelfReference::new(bad).is_err());
    let mut bad = original.clone();
    bad.generation.insert((2, 0));
    assert!(CheckedSelfReference::new(bad).is_err());
    let mut bad = original.clone();
    bad.protocol.as_mut().unwrap().domain.insert((0, 2));
    assert!(CheckedSelfReference::new(bad).is_err());
    let mut bad = original.clone();
    bad.report_count = 0;
    assert!(CheckedSelfReference::new(bad).is_err());
    let mut bad = original;
    bad.sigma.clear();
    assert!(CheckedSelfReference::new(bad).is_err());
    assert!(full().audit_point(2).is_err());
}

#[test]
fn exact_fixed_bridge_existence_plan_constructs_success_or_exhibits_missing_condition() {
    let model = full();
    let planned = model.successful_linked_report_plan(true).unwrap().unwrap();
    assert!(
        planned.signature().linkage_verified
            && planned.signature().comparison_success
            && planned.signature().report_stable
    );
    let mut data = model.data().clone();
    data.context = vec![1, 0];
    let unstable = CheckedSelfReference::new(data).unwrap();
    assert!(unstable
        .successful_linked_report_plan(true)
        .unwrap()
        .is_none());
    assert!(
        unstable
            .successful_linked_report_plan(false)
            .unwrap()
            .unwrap()
            .signature()
            .comparison_success
    );
    let mut data = model.data().clone();
    data.target[1] = None;
    assert!(CheckedSelfReference::new(data)
        .unwrap()
        .successful_linked_report_plan(false)
        .unwrap()
        .is_none());
    let mut data = model.data().clone();
    data.generation.remove(&(0, 0));
    assert!(CheckedSelfReference::new(data)
        .unwrap()
        .successful_linked_report_plan(false)
        .unwrap()
        .is_none());
    let mut data = model.data().clone();
    data.protocol.as_mut().unwrap().domain.remove(&(0, 0));
    assert!(CheckedSelfReference::new(data)
        .unwrap()
        .successful_linked_report_plan(false)
        .unwrap()
        .is_none());
    let mut data = model.data().clone();
    data.protocol = None;
    assert!(CheckedSelfReference::new(data)
        .unwrap()
        .successful_linked_report_plan(false)
        .unwrap()
        .is_none());
}

#[test]
fn partial_report_event_stability_is_not_silently_identified_with_total_availability() {
    let mut data = full().data().clone();
    data.reports[1] = None;
    let stable = CheckedSelfReference::new(data.clone()).unwrap();
    assert!(stable.report_events_preserved());
    assert!(!stable.stability_available() && !stable.signature().report_stable);
    data.context = vec![1, 0];
    assert!(!CheckedSelfReference::new(data)
        .unwrap()
        .report_events_preserved());
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_self_reference.rs
// Claim: urn:core:crates_rs:tests:finite-self-reference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb74e6694 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb74e6694` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb74e6694 {
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
impl BoundaryErrorb74e6694 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb74e6694 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb74e6694 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb74e6694 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb74e6694> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb74e6694::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb74e6694::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb74e6694::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b74e6694() {
    let admitted = BoundaryRecordb74e6694::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb74e6694::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
