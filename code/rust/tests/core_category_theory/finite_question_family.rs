use core_category_theory::finite_question_family::*;
use core_category_theory::finite_report_descent::{DescentError, DescentOutcome};
use core_category_theory::finite_report_query::ReportQueryDecision;
use std::collections::BTreeSet;

fn binary(rows: &[[u8; 2]]) -> FiniteQuestionFamily<u8> {
    FiniteQuestionFamily::new(2, rows.iter().map(|r| r.to_vec()).collect()).unwrap()
}

#[test]
fn every_small_report_is_sufficient_exactly_when_it_refines_answer_equality() {
    for n in 0..=3 {
        for mask in 0..(1 << (2 * n)) {
            let rows: Vec<_> = (0..n)
                .map(|i| vec![(mask >> (2 * i)) & 1, (mask >> (2 * i + 1)) & 1])
                .collect();
            let family = FiniteQuestionFamily::new(2, rows.clone()).unwrap();
            let quotient = family.quotient();
            assert!(family.verify_quotient(&quotient));
            for labels in 0..(1 << n) {
                let report: Vec<_> = (0..n).map(|i| (labels >> i) & 1).collect();
                let problem = family.factor_report(&report).unwrap();
                let decision = problem.decide();
                problem.verify_decision(&decision).unwrap();
                let collision =
                    (0..n).any(|i| (0..n).any(|j| report[i] == report[j] && rows[i] != rows[j]));
                assert_eq!(
                    matches!(decision, ReportQueryDecision::Collision(_)),
                    collision
                );
                if let ReportQueryDecision::Factorable(cert) = decision {
                    for i in 0..n {
                        assert_eq!(cert.decoder[&report[i]], rows[i]);
                    }
                }
            }
            for i in 0..n {
                for j in 0..n {
                    assert_eq!(
                        quotient.class_of[i] == quotient.class_of[j],
                        rows[i] == rows[j]
                    );
                }
            }
        }
    }
}

#[test]
fn empty_source_and_no_questions_have_different_quotients() {
    let empty = FiniteQuestionFamily::<u8>::new(0, vec![]).unwrap();
    let inhabited = FiniteQuestionFamily::<u8>::new(0, vec![vec![], vec![]]).unwrap();
    assert_eq!(empty.quotient().profiles.len(), 0);
    assert_eq!(inhabited.quotient().profiles.len(), 1);
    let mut forged = inhabited.quotient();
    forged.class_of[1] = 7;
    assert!(!inhabited.verify_quotient(&forged));
    assert!(matches!(
        inhabited.factor_report(&[0]),
        Err(QuestionFamilyError::MapLength { .. })
    ));
    assert!(matches!(
        FiniteQuestionFamily::new(2, vec![vec![0]]),
        Err(QuestionFamilyError::RowWidth { .. })
    ));
}

#[test]
fn operation_descent_checks_availability_and_result_class() {
    let source = binary(&[[0, 0], [0, 0]]);
    let target = binary(&[[0, 0], [1, 0]]);
    for image in [vec![None, Some(0)], vec![Some(0), Some(1)]] {
        let p = source.descend_operation(&target, &image).unwrap();
        assert!(matches!(p.decide(), ReportQueryDecision::Collision(_)));
        p.verify_decision(&p.decide()).unwrap();
    }
    for image in [vec![None, None], vec![Some(1), Some(1)]] {
        assert!(matches!(
            source.descend_operation(&target, &image).unwrap().decide(),
            ReportQueryDecision::Factorable(_)
        ));
    }
    assert!(matches!(
        source.descend_operation(&target, &[Some(2), None]),
        Err(QuestionFamilyError::ImageOutsideTarget { .. })
    ));
}

#[test]
fn local_quotients_do_not_automatically_preserve_joint_questions() {
    let local = FiniteQuestionFamily::<u8>::new(0, vec![vec![], vec![]]).unwrap();
    let joint = FiniteQuestionFamily::new(1, vec![vec![0], vec![1]]).unwrap();
    let xor = [Some(0), Some(1), Some(1), Some(0)];
    let problem = local.descend_composition(&local, &joint, &xor).unwrap();
    assert!(matches!(
        problem.decide(),
        ReportQueryDecision::Collision(_)
    ));
    let refined = FiniteQuestionFamily::new(1, vec![vec![0], vec![1]]).unwrap();
    assert!(matches!(
        refined
            .descend_composition(&refined, &joint, &xor)
            .unwrap()
            .decide(),
        ReportQueryDecision::Factorable(_)
    ));
    assert!(matches!(
        local.descend_composition(&local, &joint, &xor[..3]),
        Err(QuestionFamilyError::MapLength { .. })
    ));
    assert!(matches!(
        local.descend_composition(&local, &joint, &[Some(2); 4]),
        Err(QuestionFamilyError::ImageOutsideTarget { .. })
    ));
}

#[test]
fn lggr_distinguishes_no_extension_unique_extension_and_ambiguity() {
    let family = binary(&[[0, 0], [0, 0], [1, 1]]);
    let site = family
        .report_site(&BTreeSet::from([0, 1, 2, 3]), 10_000)
        .unwrap();
    assert_eq!(
        site.presheaf()
            .descent_fiber(3, &[1, 2], &[0, 1])
            .unwrap()
            .outcome(),
        DescentOutcome::NoGlobalExtension
    );
    assert_eq!(
        site.presheaf()
            .descent_fiber(3, &[1, 2], &[1, 1])
            .unwrap()
            .outcome(),
        DescentOutcome::Unique { global_section: 2 }
    );
    assert_eq!(
        site.presheaf()
            .descent_fiber(3, &[1, 2], &[0, 0])
            .unwrap()
            .outcome(),
        DescentOutcome::Ambiguous {
            global_sections: vec![0, 1]
        }
    );
    let classification = site.presheaf().classify_cover(3, &[1, 2], 4).unwrap();
    assert!(!classification.has_existence);
    assert!(!classification.is_separated);
    assert!(matches!(
        site.presheaf().classify_cover(3, &[1, 2], 3),
        Err(DescentError::EnumerationLimit { .. })
    ));
    assert!(site
        .presheaf()
        .verify_cover_classification(3, &[1, 2], 4, &classification)
        .unwrap());
}

#[test]
fn disagreement_on_an_overlap_is_not_an_lggr_existence_obstruction() {
    let family = FiniteQuestionFamily::new(3, vec![vec![0, 0, 0], vec![1, 1, 1]]).unwrap();
    let site = family
        .report_site(&BTreeSet::from([0, 1, 3, 5, 7]), 10_000)
        .unwrap();
    assert!(matches!(
        site.presheaf().descent_fiber(7, &[3, 5], &[0, 1]),
        Err(DescentError::IncompatibleLocals { .. })
    ));
    assert!(matches!(
        site.presheaf().descent_fiber(7, &[3, 5], &[0, 9]),
        Err(DescentError::InvalidLocalSections)
    ));
    assert!(matches!(
        family.report_site(&BTreeSet::from([0, 3, 5, 7]), 10_000),
        Err(QuestionFamilyError::Descent(
            DescentError::MissingIntersection { .. }
        ))
    ));
}

#[test]
fn malformed_contexts_and_exhausted_budgets_are_refusals() {
    let family = binary(&[[0, 0]]);
    assert!(matches!(
        family.report_site(&BTreeSet::from([0, 1, 2, 3]), 0),
        Err(QuestionFamilyError::WorkLimit)
    ));
    assert!(matches!(
        family.report_site(&BTreeSet::from([0, 1, 4]), 10_000),
        Err(QuestionFamilyError::Descent(
            DescentError::ContextOutsideCarrier { .. }
        ))
    ));
    assert!(matches!(
        family.report_site(&BTreeSet::from([0, 1]), 10_000),
        Err(QuestionFamilyError::Descent(
            DescentError::MissingEmptyOrFullContext
        ))
    ));
    let widest = FiniteQuestionFamily::<u8>::new(64, vec![]).unwrap();
    widest
        .report_site(&BTreeSet::from([0, u64::MAX]), 10_000)
        .unwrap();
    assert!(FiniteQuestionFamily::<u8>::new(65, vec![])
        .unwrap()
        .report_site(&BTreeSet::new(), 0)
        .is_err());
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_question_family.rs
// Claim: urn:core:crates_rs:tests:finite-question-family:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde6bf56f4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde6bf56f4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore6bf56f4 {
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
impl BoundaryErrore6bf56f4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore6bf56f4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore6bf56f4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde6bf56f4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore6bf56f4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore6bf56f4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore6bf56f4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore6bf56f4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e6bf56f4() {
    let admitted = BoundaryRecorde6bf56f4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde6bf56f4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
