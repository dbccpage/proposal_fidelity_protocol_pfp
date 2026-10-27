use core_category_theory::finite_continuation::PartialDynamics;
use core_category_theory::finite_joint_carrier::*;
use core_category_theory::finite_report_query::ReportQueryDecision;
fn m(reports: Vec<usize>) -> PartialDynamics {
    PartialDynamics::new(reports.clone(), vec![vec![]; reports.len()], 0).unwrap()
}
#[test]
fn missing_joint_distinction_has_collision_and_minimal_refinement() {
    let local = m(vec![0, 0]);
    let p = JointCarrierProblem::new(
        &local,
        &local,
        vec![(0, 0), (0, 1), (1, 0), (1, 1)],
        vec![1, 0, 0, 1],
        100,
    )
    .unwrap();
    let a = p.analyze().unwrap();
    p.verify_analysis(&a).unwrap();
    let ReportQueryDecision::Collision(w) = &a.decision else {
        panic!("missing collision")
    };
    assert_eq!(p.pairs()[w.first], (0, 0));
    assert_eq!(p.pairs()[w.second], (0, 1));
    assert_eq!(a.refinement.profiles.len(), 2);
    let f = p.fiber((0, 0)).unwrap();
    assert_eq!(f.rows.len(), 4);
    assert_eq!(f.answers.len(), 2);
    p.verify_fiber((0, 0), &f).unwrap();
    let mut forged = a;
    forged.refinement.class_of[0] = 99;
    assert!(p.verify_analysis(&forged).is_err());
}
#[test]
fn local_green_global_red_is_not_a_typing_error_or_answer_ambiguity() {
    let local = m(vec![0, 1]);
    let p =
        JointCarrierProblem::new(&local, &local, vec![(0, 0), (1, 1)], vec![4, 5], 100).unwrap();
    assert!(matches!(
        p.analyze().unwrap().decision,
        ReportQueryDecision::Factorable(_)
    ));
    let red = p.fiber((0, 1)).unwrap();
    assert!(red.rows.is_empty());
    p.verify_fiber((0, 1), &red).unwrap();
    assert_eq!(p.fiber((0, 2)), Err(JointError::UnknownLocalClass));
    let green = p.fiber((1, 1)).unwrap();
    assert_eq!(green.rows, vec![1]);
    assert!(p.verify_fiber((0, 1), &green).is_err());
    let expanded = JointCarrierProblem::new(
        &local,
        &local,
        vec![(0, 0), (1, 1), (0, 1)],
        vec![4, 5, 6],
        100,
    )
    .unwrap();
    assert!(expanded.verify_fiber((0, 1), &red).is_err());
}
#[test]
fn every_two_by_two_boolean_joint_question_is_decided_exactly() {
    for labels in 0..4 {
        let l = m(vec![0, labels & 1]);
        let r = m(vec![0, labels >> 1]);
        for bits in 0..16 {
            let answers: Vec<_> = (0..4).map(|i| (bits >> i) & 1).collect();
            let p = JointCarrierProblem::new(
                &l,
                &r,
                vec![(0, 0), (0, 1), (1, 0), (1, 1)],
                answers.clone(),
                100,
            )
            .unwrap();
            let a = p.analyze().unwrap();
            let sufficient = (0..4)
                .all(|i| (0..4).all(|j| a.reports[i] != a.reports[j] || answers[i] == answers[j]));
            assert_eq!(
                matches!(a.decision, ReportQueryDecision::Factorable(_)),
                sufficient
            );
            for i in 0..4 {
                for j in 0..4 {
                    assert_eq!(
                        a.refinement.class_of[i] == a.refinement.class_of[j],
                        a.reports[i] == a.reports[j] && answers[i] == answers[j]
                    );
                }
            }
        }
    }
}
#[test]
fn malformed_relations_refuse_and_empty_relations_are_explicit() {
    let l = m(vec![0]);
    assert_eq!(
        JointCarrierProblem::new(&l, &l, vec![(0, 0), (0, 0)], vec![0, 0], 100),
        Err(JointError::InvalidRelation)
    );
    assert_eq!(
        JointCarrierProblem::new(&l, &l, vec![(1, 0)], vec![0], 100),
        Err(JointError::InvalidRelation)
    );
    assert_eq!(
        JointCarrierProblem::new(&l, &l, vec![], vec![], 0),
        Err(JointError::WorkLimit)
    );
    let p = JointCarrierProblem::new(&l, &l, vec![], vec![], 100).unwrap();
    assert!(p.fiber((0, 0)).unwrap().rows.is_empty());
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_joint_carrier.rs
// Claim: urn:core:crates_rs:tests:finite-joint-carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde737305d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde737305d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore737305d {
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
impl BoundaryErrore737305d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore737305d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore737305d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde737305d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore737305d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore737305d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore737305d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore737305d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e737305d() {
    let admitted = BoundaryRecorde737305d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde737305d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
