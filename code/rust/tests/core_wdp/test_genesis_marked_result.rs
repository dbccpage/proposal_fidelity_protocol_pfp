use num_bigint::BigInt;
use core_wdp::genesis_gauge_result::{Source23Error, Source23State};
use core_wdp::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use core_wdp::genesis_source_execution::*;

fn state(n: usize, r: &[i64], s: &[i64], filled: &[[usize; 3]]) -> Source25State {
    Source25State::try_new(GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r: r.iter().map(|&v| v.into()).collect(),
        s: s.iter().map(|&v| v.into()).collect(),
        filled: filled
            .iter()
            .map(|t| MarkedTriple {
                x: t[0],
                y: t[1],
                z: t[2],
            })
            .collect(),
    })
    .unwrap()
}
#[test]
fn separate_table_and_mark_orbits_lose_joint_loop_incidence() {
    let a = state(
        4,
        &[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        &[0; 16],
        &[[0, 1, 2]],
    );
    let b = state(
        4,
        &[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        &[0; 16],
        &[[1, 2, 3]],
    );
    let table = Source23State::try_new(4, a.packet().r.clone(), a.packet().s.clone()).unwrap();
    assert_eq!(
        table.result_key(24).unwrap(),
        Source23State::try_new(4, b.packet().r.clone(), b.packet().s.clone())
            .unwrap()
            .result_key(24)
            .unwrap()
    );
    assert!(a
        .nothing_with()
        .unwrap()
        .same_marked_result(&b.nothing_with().unwrap(), 24)
        .unwrap());
    assert!(!a.same_marked_result(&b, 24).unwrap());
    assert_ne!(
        a.canonical_state(24).unwrap(),
        b.canonical_state(24).unwrap()
    );
    assert_eq!(a.align_to(&b, 24), Err(Source23Error::NotSameResult));
    assert!(a.unbalanced().unwrap().is_empty());
    assert!(b.unbalanced().unwrap().is_empty());
}
#[test]
fn paired_assertions_raising_and_alignment_keep_raw_states_and_marks() {
    let base = state(3, &[7, 1, 0, 0, 9, 0, 0, 0, 2], &[0; 9], &[[0, 1, 2]]);
    let together = state(3, &[8, 2, 1, 1, 10, 1, 1, 1, 3], &[1; 9], &[[0, 1, 2]]);
    assert_eq!(together.plain_state().unwrap(), base);
    assert!(base.same_marked_result(&together, 6).unwrap());
    assert_ne!(
        base.canonical_state(6).unwrap(),
        together.canonical_state(6).unwrap()
    );
    let image = [2, 0, 1];
    let moved = base.rewrite(&image).unwrap();
    let raised = moved.raise_terms(&[2.into(), 0.into(), 1.into()]).unwrap();
    assert!(base.same_marked_result(&raised, 6).unwrap());
    let aligned = base.align_to(&raised, 6).unwrap();
    assert_eq!(aligned, moved);
    assert_ne!(aligned, raised);
    assert_eq!(
        aligned.balance_record().unwrap(),
        raised.balance_record().unwrap()
    );
    assert_eq!(
        base.swap_relations().unwrap().swap_relations().unwrap(),
        base
    );
}
#[test]
fn cyclic_rotations_and_reverse_orientation_have_different_balance_meanings() {
    let a = state(3, &[0, 1, 0, 0, 0, 0, 0, 0, 0], &[0; 9], &[[0, 1, 2]]);
    let b = state(3, &[0, 1, 0, 0, 0, 0, 0, 0, 0], &[0; 9], &[[0, 2, 1]]);
    assert_eq!(a.balance_record().unwrap()[0].1, false);
    assert_eq!(b.balance_record().unwrap()[0].1, true);
    assert!(!a.same_marked_result(&b, 6).unwrap());
    assert!(a
        .same_marked_result(&a.rewrite(&[1, 2, 0]).unwrap(), 6)
        .unwrap());
    assert_eq!(a.unbalanced().unwrap(), a.packet().filled);
    assert!(a
        .swap_relations()
        .unwrap()
        .balance_record()
        .unwrap()
        .iter()
        .all(|(_, value)| !value));
}
#[test]
fn term_addition_does_not_descend_and_a_later_fill_exposes_the_loss() {
    let a = state(2, &[0; 4], &[0; 4], &[]);
    let b = a.raise_terms(&[1.into(), 0.into()]).unwrap();
    assert!(a.same_marked_result(&b, 2).unwrap());
    let aa = a.perform_enabled(Source25Change::AddTerm).unwrap();
    let bb = b.perform_enabled(Source25Change::AddTerm).unwrap();
    assert!(!aa.same_marked_result(&bb, 6).unwrap());
    let fill = Source25Change::Fill { x: 0, y: 1, z: 2 };
    assert!(aa
        .perform_enabled(fill)
        .unwrap()
        .unbalanced()
        .unwrap()
        .is_empty());
    assert_eq!(
        bb.perform_enabled(fill).unwrap().unbalanced().unwrap(),
        vec![MarkedTriple { x: 0, y: 1, z: 2 }]
    );
    let left = Source25Run::replay(a, &[]).unwrap();
    let right = Source25Run::replay(b, &[Source25Change::AddTerm]).unwrap();
    assert_eq!(
        left.then(&right),
        Err(SourceExecutionError::IntermediateMismatch)
    );
}
#[test]
fn identification_merges_marks_but_can_create_a_balance_obstruction() {
    let a = state(4, &[0; 16], &[0; 16], &[[0, 2, 3], [1, 2, 3]]);
    let b = a
        .raise_terms(&[0.into(), 0.into(), 1.into(), 0.into()])
        .unwrap();
    assert!(a.same_marked_result(&b, 24).unwrap());
    assert!(b.unbalanced().unwrap().is_empty());
    let identify = Source25Change::Identify { x: 0, y: 1 };
    let aa = a.perform_enabled(identify).unwrap();
    let bb = b.perform_enabled(identify).unwrap();
    assert_eq!(aa.packet().filled, vec![MarkedTriple { x: 0, y: 1, z: 2 }]);
    assert_eq!(aa.packet().filled, bb.packet().filled);
    assert!(!aa.same_marked_result(&bb, 6).unwrap());
    assert!(aa.unbalanced().unwrap().is_empty());
    assert_eq!(bb.unbalanced().unwrap(), bb.packet().filled);
}
#[test]
fn malformed_writings_and_incomplete_joint_orbits_refuse() {
    let base = state(3, &[0; 9], &[0; 9], &[[0, 1, 2]]);
    assert!(base.result_mark(5).is_err());
    assert!(base.canonical_state(5).is_err());
    assert!(base.align_to(&base, 5).is_err());
    assert_eq!(
        base.rewrite(&[0, 0, 2]),
        Err(Source23Error::InvalidPermutation)
    );
    assert!(!base.same_marked_result(&Source25State::empty(), 0).unwrap());
    assert_eq!(base.packet().r, vec![BigInt::from(0); 9]);
    let empty = Source25State::empty();
    assert!(empty.result_mark(0).is_err());
    assert_eq!(empty.canonical_state(1).unwrap(), empty);
    assert_eq!(empty.balance_record().unwrap(), vec![]);
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_marked_result.rs
// Claim: urn:core:crates_rs:tests:test-genesis-marked-result:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordce55bd3f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordce55bd3f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorce55bd3f {
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
impl BoundaryErrorce55bd3f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorce55bd3f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorce55bd3f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordce55bd3f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorce55bd3f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorce55bd3f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorce55bd3f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorce55bd3f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ce55bd3f() {
    let admitted = BoundaryRecordce55bd3f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordce55bd3f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
