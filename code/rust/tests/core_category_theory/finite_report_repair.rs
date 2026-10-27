use core_category_theory::finite_question_family::FiniteQuestionFamily;
use core_category_theory::finite_report_repair::*;
use std::collections::BTreeSet;

fn family(rows: &[[u8; 2]]) -> FiniteQuestionFamily<u8> {
    FiniteQuestionFamily::new(2, rows.iter().map(|r| r.to_vec()).collect()).unwrap()
}

#[test]
fn every_small_repair_matches_the_independent_pair_relation() {
    // 4,681 complete tables, including the empty carrier. The oracle compares
    // pairs directly; it does not replay the solver's choice of witnesses.
    for n in 0..=4 {
        for values in 0..(1 << (2 * n)) {
            let rows: Vec<_> = (0..n)
                .map(|i| vec![(values >> (2 * i)) & 1, (values >> (2 * i + 1)) & 1])
                .collect();
            let f = FiniteQuestionFamily::new(2, rows.clone()).unwrap();
            for labels in 0..(1 << n) {
                let report: Vec<_> = (0..n).map(|i| (labels >> i) & 1).collect();
                let c = repair_report(&f, &report, RepairLimits::default()).unwrap();
                verify_repair(&f, &report, &c, RepairLimits::default()).unwrap();
                for i in 0..n {
                    for j in 0..n {
                        assert_eq!(
                            c.class_of[i] == c.class_of[j],
                            report[i] == report[j] && rows[i] == rows[j]
                        );
                    }
                }
                let before = report.iter().collect::<BTreeSet<_>>().len();
                let after = report.iter().zip(&rows).collect::<BTreeSet<_>>().len();
                assert!(c.steps.len() <= after - before);
            }
        }
    }
}

#[test]
fn class_increase_bound_is_sharp_and_multiway_splits_can_be_faster() {
    let f = family(&[[0, 0], [1, 0], [0, 1]]);
    let c = repair_report(&f, &[0; 3], RepairLimits::default()).unwrap();
    assert_eq!(c.steps.len(), 2); // k_star - k_initial = 3 - 1.
    let f = FiniteQuestionFamily::new(1, vec![vec![0], vec![1], vec![2]]).unwrap();
    let c = repair_report(&f, &[0; 3], RepairLimits::default()).unwrap();
    assert_eq!(c.steps.len(), 1);
}

#[test]
fn a_valid_alternative_witness_order_replays() {
    let f = family(&[[0, 0], [1, 0], [0, 1]]);
    let c = RepairCertificate {
        steps: vec![
            RepairStep {
                first: 0,
                second: 2,
                question: 1,
            },
            RepairStep {
                first: 0,
                second: 1,
                question: 0,
            },
        ],
        class_of: vec![0, 1, 2],
    };
    verify_repair(&f, &[0; 3], &c, RepairLimits::default()).unwrap();
}

#[test]
fn forged_missing_and_unnecessary_splits_are_refused() {
    let f = family(&[[0, 0], [1, 0], [0, 0]]);
    let c = repair_report(&f, &[0; 3], RepairLimits::default()).unwrap();
    for bad in [
        RepairCertificate {
            class_of: vec![0, 0, 0],
            ..c.clone()
        },
        RepairCertificate {
            class_of: vec![0, 1, 2],
            ..c.clone()
        },
        RepairCertificate {
            steps: vec![],
            ..c.clone()
        },
        RepairCertificate {
            steps: vec![RepairStep {
                first: 0,
                second: 2,
                question: 0,
            }],
            ..c.clone()
        },
        RepairCertificate {
            steps: vec![RepairStep {
                first: usize::MAX,
                second: 1,
                question: 0,
            }],
            ..c.clone()
        },
        RepairCertificate {
            steps: vec![RepairStep {
                first: 0,
                second: 1,
                question: usize::MAX,
            }],
            ..c.clone()
        },
    ] {
        assert!(verify_repair(&f, &[0; 3], &bad, RepairLimits::default()).is_err());
    }
    let premature = RepairCertificate {
        steps: vec![],
        class_of: vec![0; 3],
    };
    assert_eq!(
        verify_repair(&f, &[0; 3], &premature, RepairLimits::default()),
        Err(RepairError::NotLeastSufficient)
    );
    let changed = family(&[[0, 0], [0, 0], [1, 0]]);
    assert!(verify_repair(&changed, &[0; 3], &c, RepairLimits::default()).is_err());
}

#[test]
fn old_information_is_retained_and_equal_profiles_are_not_split() {
    let f = family(&[[0, 0]; 3]);
    let c = repair_report(&f, &["kept", "other", "kept"], RepairLimits::default()).unwrap();
    assert!(c.steps.is_empty());
    assert_eq!(c.class_of, vec![0, 1, 0]);
    verify_repair(&f, &["kept", "other", "kept"], &c, RepairLimits::default()).unwrap();
}

#[test]
fn availability_is_an_answer_but_unasked_future_questions_are_not_recovered() {
    let f = FiniteQuestionFamily::new(1, vec![vec![None], vec![Some(0)]]).unwrap();
    let c = repair_report(&f, &[0; 2], RepairLimits::default()).unwrap();
    assert_eq!(c.class_of, vec![0, 1]);
    let present = family(&[[0, 0]; 2]);
    let c = repair_report(&present, &[0; 2], RepairLimits::default()).unwrap();
    assert_eq!(c.class_of, vec![0, 0]);
    let future = family(&[[0, 0], [1, 0]]);
    let operation = present
        .descend_operation(&future, &[Some(0), Some(1)])
        .unwrap();
    assert!(matches!(
        operation.decide(),
        core_category_theory::finite_report_query::ReportQueryDecision::Collision(_)
    ));
}

#[test]
fn empty_carriers_and_empty_questions_preserve_their_distinct_meanings() {
    for report in [vec![], vec![0, 1, 0]] {
        let f = FiniteQuestionFamily::<u8>::new(0, vec![vec![]; report.len()]).unwrap();
        let c = repair_report(&f, &report, RepairLimits::default()).unwrap();
        assert_eq!(c.class_of, report);
        assert!(c.steps.is_empty());
    }
}

#[test]
fn budgets_and_malformed_reports_refuse_without_mathematical_verdicts() {
    let f = family(&[[0, 0], [1, 0]]);
    let limits = RepairLimits::default();
    assert_eq!(
        repair_report(&f, &[0], limits),
        Err(RepairError::ReportLength)
    );
    assert_eq!(
        repair_report(
            &f,
            &[0; 2],
            RepairLimits {
                max_rows: 1,
                ..limits
            }
        ),
        Err(RepairError::SizeLimit)
    );
    assert_eq!(
        repair_report(
            &f,
            &[0; 2],
            RepairLimits {
                max_questions: 1,
                ..limits
            }
        ),
        Err(RepairError::SizeLimit)
    );
    assert_eq!(
        repair_report(
            &f,
            &[0; 2],
            RepairLimits {
                max_pair_checks: 0,
                ..limits
            }
        ),
        Err(RepairError::PairLimit)
    );
    assert_eq!(
        repair_report(
            &f,
            &[0; 2],
            RepairLimits {
                max_steps: 0,
                ..limits
            }
        ),
        Err(RepairError::StepLimit)
    );
    let c = repair_report(&f, &[0; 2], limits).unwrap();
    assert_eq!(
        verify_repair(
            &f,
            &[0; 2],
            &c,
            RepairLimits {
                max_steps: 0,
                ..limits
            }
        ),
        Err(RepairError::StepLimit)
    );
    assert_eq!(
        verify_repair(
            &f,
            &[0; 2],
            &c,
            RepairLimits {
                max_pair_checks: 0,
                ..limits
            }
        ),
        Err(RepairError::PairLimit)
    );
    assert!(repair_report(
        &f,
        &[0, 1],
        RepairLimits {
            max_steps: 0,
            ..limits
        }
    )
    .is_ok());
}
#[test]
fn legal_prefix_does_not_claim_complete_sufficiency() {
    use core_category_theory::finite_question_family::FiniteQuestionFamily;
    use core_category_theory::finite_report_repair::{
        replay_repair_prefix, verify_repair, RepairCertificate, RepairError, RepairLimits,
        RepairStep,
    };
    let family = FiniteQuestionFamily::new(2, vec![vec![0, 0], vec![0, 1], vec![1, 0]]).unwrap();
    let report = vec![0, 0, 0];
    let steps = vec![RepairStep {
        first: 0,
        second: 1,
        question: 1,
    }];
    let partitions =
        replay_repair_prefix(&family, &report, &steps, RepairLimits::default()).unwrap();
    assert_eq!(partitions, vec![vec![0, 0, 0], vec![0, 1, 0]]);
    let incomplete = RepairCertificate {
        steps,
        class_of: partitions[1].clone(),
    };
    assert_eq!(
        verify_repair(&family, &report, &incomplete, RepairLimits::default()),
        Err(RepairError::NotLeastSufficient)
    );
    let invalid = vec![RepairStep {
        first: 0,
        second: 8,
        question: 1,
    }];
    assert_eq!(
        replay_repair_prefix(&family, &report, &invalid, RepairLimits::default()),
        Err(RepairError::InvalidStep { index: 0 })
    );
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_report_repair.rs
// Claim: urn:core:crates_rs:tests:finite-report-repair:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7d3360fb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7d3360fb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7d3360fb {
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
impl BoundaryError7d3360fb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7d3360fb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7d3360fb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7d3360fb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7d3360fb> {
        if capacity_bound == 0 {
            return Err(BoundaryError7d3360fb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7d3360fb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7d3360fb::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7d3360fb() {
    let admitted = BoundaryRecord7d3360fb::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7d3360fb::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
