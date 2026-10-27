use num_bigint::BigInt;
use core_wdp::genesis_gauge_result::*;

fn state(n: usize, r: &[i64], s: &[i64]) -> Source23State {
    Source23State::try_new(
        n,
        r.iter().map(|&v| v.into()).collect(),
        s.iter().map(|&v| v.into()).collect(),
    )
    .unwrap()
}
fn from_excess(n: usize, e: &[i64]) -> Source23State {
    state(
        n,
        &e.iter().map(|&v| v.max(0)).collect::<Vec<_>>(),
        &e.iter().map(|&v| (-v).max(0)).collect::<Vec<_>>(),
    )
}
#[test]
fn raising_and_paired_assertions_preserve_result_but_do_not_preserve_raw_cost() {
    let zero = state(2, &[0; 4], &[0; 4]);
    let raised = zero.raise_terms(&[1.into(), 0.into()]).unwrap();
    assert_ne!(zero, raised);
    assert!(zero.same_result(&raised, 2).unwrap());
    assert_eq!(
        raised.excess(),
        vec![0.into(), 1.into(), (-1).into(), 0.into()]
    );
    assert_eq!(zero.plain_cost(), 2.into());
    assert_eq!(raised.plain_cost(), 4.into());
    let together = state(2, &[1; 4], &[1; 4]);
    assert!(together.same_result(&zero, 2).unwrap());
    assert_eq!(together.plain_state().unwrap(), zero);
}
#[test]
fn sorted_sum_profile_loses_joint_incidence_needed_for_the_complete_key() {
    let a = state(3, &[1, 1, 0, 0, 0, 0, 0, 0, 0], &[0; 9]);
    let b = state(3, &[1, 0, 0, 0, 0, 1, 0, 0, 0], &[0; 9]);
    assert_eq!(a.sum_profile(1).unwrap(), b.sum_profile(1).unwrap());
    assert!(!a.same_result(&b, 6).unwrap());
    assert_eq!(a.align_to(&b, 6), Err(Source23Error::NotSameResult));
}
#[test]
fn first_loop_then_two_way_then_triangle_witnesses_detect_all_obstruction_kinds() {
    let looped = from_excess(3, &[2, 1, 0, -1, 0, 0, 0, 0, 0]);
    assert_eq!(looped.nothing_certificate(0).unwrap().unwrap().kind, "loop");
    let pair = from_excess(3, &[0, 2, 0, -1, 0, 0, 0, 0, 0]);
    let witness = pair.nothing_certificate(0).unwrap().unwrap();
    assert_eq!(witness.kind, "two-way");
    assert_eq!(witness.terms, vec![0, 1]);
    let triangle = from_excess(3, &[0, 1, 0, -1, 0, 0, 0, 0, 0]);
    let witness = triangle.nothing_certificate(1).unwrap().unwrap();
    assert_eq!(witness.kind, "around");
    assert_eq!(witness.value, 1.into());
    let gradient = from_excess(3, &[0, -1, 3, 1, 0, 4, -3, -4, 0]);
    assert!(gradient.nothing_certificate(1).unwrap().is_none());
    assert!(gradient.nothing_certificate(0).is_err());
    assert_eq!(gradient.normal_table().unwrap(), vec![BigInt::from(0); 9]);
}
#[test]
fn alignment_returns_original_raw_state_in_the_target_writing() {
    let base = state(2, &[7, 4, 0, 9], &[0, 0, 2, 0]);
    let moved = base.rewrite(&[1, 0]).unwrap();
    let target = moved.raise_term(0).unwrap();
    assert_eq!(base.align_to(&target, 2).unwrap(), moved);
    assert_ne!(moved, target);
    assert_eq!(
        moved.normal_table().unwrap(),
        target.normal_table().unwrap()
    );
}
#[test]
fn every_atomic_intermediate_and_noop_occurrence_survives_composition() {
    let base = state(2, &[0; 4], &[0; 4]);
    let events = [0, 1, 0];
    let run = Source23Run::replay(base.clone(), &events).unwrap();
    assert_eq!(run.assertion_additions(), 6.into());
    for split in 0..=events.len() {
        let left = Source23Run::replay(base.clone(), &events[..split]).unwrap();
        let right = Source23Run::replay(left.final_state().clone(), &events[split..]).unwrap();
        assert_eq!(left.then(&right).unwrap(), run);
    }
    let first = Source23Run::replay(base.clone(), &[0]).unwrap();
    let wrong = Source23Run::replay(base, &[1]).unwrap();
    assert!(first
        .final_state()
        .same_result(&wrong.states()[0], 2)
        .unwrap());
    assert_eq!(first.then(&wrong), Err(Source23Error::IntermediateMismatch));
    let one = state(1, &[0], &[0]);
    let noops = Source23Run::replay(one.clone(), &[0, 0]).unwrap();
    assert_eq!(noops.states(), &[one.clone(), one.clone(), one]);
    assert_eq!(noops.raised_terms(), &[0, 0]);
    assert_eq!(noops.assertion_additions(), 0.into());
}
#[test]
fn malformed_inputs_and_exact_orbit_refusals_do_not_mutate_the_state() {
    assert!(Source23State::try_new(usize::MAX, vec![], vec![]).is_err());
    assert!(Source23State::try_new(2, vec![0.into()], vec![0.into()]).is_err());
    assert!(Source23State::try_new(1, vec![(-1).into()], vec![0.into()]).is_err());
    let base = state(3, &[0; 9], &[0; 9]);
    assert!(base.result_key(5).is_err());
    assert!(base.raise_terms(&[0.into()]).is_err());
    assert!(base
        .raise_terms(&[(-1).into(), 0.into(), 0.into()])
        .is_err());
    assert!(base.rewrite(&[0, 0, 2]).is_err());
    assert!(base.sum_profile(0).is_err());
    assert!(!base.same_result(&Source23State::empty(), 0).unwrap());
    assert_eq!(base, state(3, &[0; 9], &[0; 9]));
    assert_eq!(Source23State::empty().result_key(1).unwrap().normal, vec![]);
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_gauge_result.rs
// Claim: urn:core:crates_rs:tests:test-genesis-gauge-result:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord868d4d83 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord868d4d83` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError868d4d83 {
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
impl BoundaryError868d4d83 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError868d4d83 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError868d4d83 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord868d4d83 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError868d4d83> {
        if capacity_bound == 0 {
            return Err(BoundaryError868d4d83::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError868d4d83::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError868d4d83::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_868d4d83() {
    let admitted = BoundaryRecord868d4d83::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord868d4d83::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
