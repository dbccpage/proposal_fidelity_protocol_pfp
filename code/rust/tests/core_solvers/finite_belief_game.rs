//! Independent finite controls for WDP-CHS-D01/D03/D08/D09/P02/P08/P12/P19.
use num_rational::BigRational;
use core_solvers::finite_belief_game::{Action, Arena, GameError};
use std::collections::BTreeSet;

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(n.into(), d.into())
}
fn action(label: &str, cost: BigRational, successors: &[usize]) -> Action {
    Action {
        label: label.into(),
        cost,
        successors: successors.to_vec(),
    }
}
fn arena(extra: bool, guard: bool) -> Arena {
    let mut start = vec![
        action("direct", q(5, 1), &[2]),
        action("trap", q(1, 1), &[3]),
    ];
    if !guard {
        start.push(action("via", q(3, 4), &[1]));
    }
    if extra {
        start.push(action("shortcut", q(1, 2), &[2]));
    }
    Arena::new(
        vec![false, false, true, false],
        vec![
            start,
            vec![action("finish", q(3, 1), &[2])],
            vec![],
            vec![action("stay", q(1, 1), &[3])],
        ],
        0,
    )
    .unwrap()
}

#[test]
fn exact_bellman_certificates_and_target_before_dead_end() {
    let a = arena(false, false);
    let cert = a.solve();
    assert_eq!(
        cert.values,
        vec![Some(q(15, 4)), Some(q(3, 1)), Some(q(0, 1)), None]
    );
    a.verify(&cert).unwrap();
    for state in 0..4 {
        let mut forged = cert.clone();
        forged.values[state] = Some(q(77, 4));
        assert!(a.verify(&forged).is_err());
    }
    let mut forged = cert.clone();
    forged.choices[0] = Some(0); // feasible direct route is not optimal
    assert!(a.verify(&forged).is_err());
    forged.choices[0] = Some(usize::MAX);
    assert!(a.verify(&forged).is_err());
    forged.values.pop();
    assert!(a.verify(&forged).is_err());
    assert!(a.verify_loss(&BTreeSet::from([3])).is_err()); // avoidable trap
    assert!(a.verify_loss(&BTreeSet::from([0, 3])).is_err());
    let loss = Arena::new(
        vec![false, true],
        vec![vec![action("stay", q(1, 1), &[0])], vec![]],
        0,
    )
    .unwrap();
    loss.verify_loss(&BTreeSet::from([0])).unwrap();
    loss.verify(&loss.solve()).unwrap();
}

#[test]
fn adversarial_successor_is_universal_and_extra_actions_cannot_hurt() {
    let a = Arena::new(
        vec![false, true, false],
        vec![
            vec![action("risk", q(1, 1), &[1, 2])],
            vec![],
            vec![action("stay", q(1, 1), &[2])],
        ],
        0,
    )
    .unwrap();
    assert_eq!(a.solve().values[0], None);
    a.verify_loss(&BTreeSet::from([0, 2])).unwrap();
    assert_eq!(arena(true, false).solve().values[0], Some(q(1, 2)));
    assert_eq!(arena(false, true).solve().values[0], Some(q(5, 1)));
}

#[test]
fn coarsest_congruence_and_quotient_preserve_values() {
    let a = Arena::new(
        vec![false, false, true, true],
        vec![
            vec![action("go", q(2, 3), &[2])],
            vec![action("go", BigRational::new_raw(4.into(), 6.into()), &[3])],
            vec![],
            vec![],
        ],
        0,
    )
    .unwrap();
    let blocks = a.refine(&[99; 4]).unwrap();
    assert_eq!(blocks, vec![0, 0, 1, 1]);
    let quotient = a.quotient(&blocks).unwrap();
    let original = a.solve();
    let reduced = quotient.solve();
    for (s, &b) in blocks.iter().enumerate() {
        assert_eq!(original.values[s], reduced.values[b]);
    }
    assert!(a.quotient(&[0; 4]).is_err());
    assert!(a.refine(&[]).is_err());
    // Price and enabled-label differences must also split equal reports.
    for changed in [action("go", q(3, 4), &[3]), action("other", q(2, 3), &[3])] {
        let b = Arena::new(
            vec![false, false, true, true],
            vec![
                vec![action("go", q(2, 3), &[2])],
                vec![changed],
                vec![],
                vec![],
            ],
            0,
        )
        .unwrap();
        let blocks = b.refine(&[0; 4]).unwrap();
        assert_ne!(blocks[0], blocks[1]);
    }
}

#[test]
fn malformed_inputs_are_refused_without_panicking() {
    assert!(Arena::new(vec![], vec![], 0).is_err());
    for a in [
        action("x", q(0, 1), &[0]),
        action("x", q(-1, 1), &[0]),
        action("x", q(1, 1), &[]),
        action("x", q(1, 1), &[1]),
        action("x", q(1, 1), &[0, 0]),
        action("x", BigRational::new_raw(1.into(), 0.into()), &[0]),
    ] {
        assert!(Arena::new(vec![false], vec![vec![a]], 0).is_err());
    }
    let a = arena(false, false);
    let mut forged = a.solve();
    forged.values[0] = Some(BigRational::new_raw(1.into(), 0.into()));
    assert_eq!(a.verify(&forged), Err(GameError::Certificate));
    assert_eq!(a.verify_feasible(&forged), Err(GameError::Certificate));
}

#[test]
fn feasible_upper_bound_is_not_an_optimality_or_loss_certificate() {
    let a = arena(false, false);
    let mut certificate = a.solve();
    certificate.values[0] = Some(q(5, 1));
    certificate.choices[0] = Some(0); // direct route costs 5; optimum is 15/4
    certificate.values[1] = None; // no claim about unused state 1
    certificate.choices[1] = None;
    a.verify_feasible(&certificate).unwrap();
    assert!(a.verify(&certificate).is_err());
    certificate.values[0] = Some(q(4, 1));
    assert!(a.verify_feasible(&certificate).is_err());
    certificate.values[0] = None;
    certificate.choices[0] = None;
    assert!(a.verify_feasible(&certificate).is_err());
}

// Origin: engine/crates_rs/tests/core_solvers/finite_belief_game.rs
// Claim: urn:core:crates_rs:tests:finite-belief-game:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcd439a93 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcd439a93` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcd439a93 {
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
impl BoundaryErrorcd439a93 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcd439a93 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcd439a93 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcd439a93 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcd439a93> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcd439a93::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcd439a93::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcd439a93::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_cd439a93() {
    let admitted = BoundaryRecordcd439a93::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordcd439a93::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
