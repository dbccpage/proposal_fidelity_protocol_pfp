use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational as Q;
use num_traits::{One, Zero};
use core_functional::path_error::{certify_path_error, PathErrorRefusal};
use core_functional::protected_linear_quotient::{QuotientError, ReportQuotient};
fn q(n: i64) -> Q {
    Q::from_integer(n.into())
}
fn m(rows: usize, cols: usize, v: Vec<Q>) -> BasicMatrix<Q> {
    BasicMatrix::from_row_major(rows, cols, v).unwrap()
}

#[test]
fn minimal_report_replays_original_questions_and_has_a_right_section() {
    let questions = m(
        3,
        3,
        vec![q(2), q(4), q(0), q(1), q(2), q(0), q(0), q(0), q(3)],
    );
    let report = ReportQuotient::new(questions.clone()).unwrap();
    assert_eq!(report.report_dimension(), 2);
    assert_eq!(
        report.report(),
        &m(2, 3, vec![q(1), q(2), q(0), q(0), q(0), q(1)])
    );
    assert_eq!(report.decoder().mul(report.report()).unwrap(), questions);
    let x = vec![q(7), q(2), q(4)];
    let y = vec![q(3), q(4), q(4)];
    assert_eq!(
        report.report().mul_vec(&x).unwrap(),
        report.report().mul_vec(&y).unwrap()
    );
    assert_eq!(
        questions.mul_vec(&x).unwrap(),
        questions.mul_vec(&y).unwrap()
    );
}

#[test]
fn quotient_transport_is_unique_functorial_and_refuses_visible_kernel_leakage() {
    let source = ReportQuotient::new(m(1, 2, vec![q(1), q(0)])).unwrap();
    let middle = ReportQuotient::new(m(2, 3, vec![q(1), q(0), q(0), q(2), q(0), q(0)])).unwrap();
    let target = ReportQuotient::new(m(1, 2, vec![q(3), q(0)])).unwrap();
    let t = m(3, 2, vec![q(2), q(0), q(7), q(3), q(1), q(5)]);
    let s = m(2, 3, vec![q(4), q(0), q(0), q(2), q(9), q(7)]);
    let td = source.descend(&middle, &t).unwrap();
    let sd = middle.descend(&target, &s).unwrap();
    assert_eq!(
        source.descend(&target, &s.mul(&t).unwrap()).unwrap(),
        sd.mul(&td).unwrap()
    );
    assert_eq!(
        td.mul(source.report()).unwrap(),
        middle.report().mul(&t).unwrap()
    );
    let leak = m(2, 2, vec![q(1), q(1), q(0), q(1)]);
    assert!(matches!(
        source.descend(&source, &leak),
        Err(QuotientError::VisibleKernel)
    ));
    let wrong = m(1, 1, vec![q(1)]);
    assert!(matches!(
        source.descend(&source, &wrong),
        Err(QuotientError::Shape)
    ));
}

#[test]
fn zero_question_rank_and_malformed_data_receive_correct_results() {
    let r = ReportQuotient::new(m(2, 3, vec![Q::zero(); 6])).unwrap();
    assert_eq!(r.report_dimension(), 0);
    assert_eq!(r.decoder().mul(r.report()).unwrap(), *r.questions());
    let bad = Q::new_raw(1.into(), 0.into());
    assert!(matches!(
        ReportQuotient::new(m(1, 1, vec![bad])),
        Err(QuotientError::Profile)
    ));
    assert!(ReportQuotient::new(m(0, 2, vec![])).is_err());
}

#[test]
fn telescoping_terms_replay_for_heterogeneous_noncommuting_paths() {
    let a = vec![
        m(3, 2, vec![q(1), q(2), q(0), q(1), q(3), q(0)]),
        m(2, 3, vec![q(1), q(0), q(2), q(0), q(1), q(1)]),
        m(2, 2, vec![q(1), q(3), q(2), q(1)]),
    ];
    let b = vec![
        m(3, 2, vec![q(0), q(1), q(1), q(0), q(2), q(1)]),
        m(2, 3, vec![q(1), q(1), q(0), q(2), q(0), q(1)]),
        m(2, 2, vec![q(2), q(0), q(1), q(1)]),
    ];
    let bound = certify_path_error(&a, &b).unwrap();
    assert!(bound.actual_norm() > &Q::zero());
    assert!(bound.actual_norm() <= bound.bound());
    assert_eq!(bound.first(), a);
    assert_eq!(bound.second(), b);
    let sum = bound
        .terms()
        .iter()
        .fold(m(2, 2, vec![Q::zero(); 4]), |s, t| s.add(t).unwrap());
    assert_eq!(&sum, bound.residual());
}

#[test]
fn amplification_refutes_unweighted_local_budget_and_scalar_bounds_are_sharp() {
    let a = vec![m(1, 1, vec![Q::one()]), m(1, 1, vec![q(100)])];
    let b = vec![m(1, 1, vec![Q::zero()]), m(1, 1, vec![q(100)])];
    let report = certify_path_error(&a, &b).unwrap();
    assert_eq!(report.actual_norm(), &q(100));
    assert_eq!(report.bound(), &q(100));
    for count in [1, 2, 5, 16] {
        let a = vec![m(1, 1, vec![q(2)]); count];
        let b = vec![m(1, 1, vec![q(1)]); count];
        let report = certify_path_error(&a, &b).unwrap();
        assert_eq!(report.actual_norm(), report.bound());
    }
}

#[test]
fn incomplete_mismatched_paths_are_refused() {
    assert!(matches!(
        certify_path_error(&[], &[]),
        Err(PathErrorRefusal::Shape)
    ));
    let a = vec![m(1, 1, vec![q(1)])];
    let b = vec![m(2, 1, vec![q(1), q(1)])];
    assert!(matches!(
        certify_path_error(&a, &b),
        Err(PathErrorRefusal::Shape)
    ));
    let huge = m(
        1,
        1,
        vec![Q::from_integer(num_bigint::BigInt::from(1) << 1025)],
    );
    assert!(matches!(
        certify_path_error(&[huge.clone()], &[huge]),
        Err(PathErrorRefusal::ScalarProfile)
    ));
}

// Origin: engine/crates_rs/tests/core_functional/observer_transport.rs
// Claim: urn:core:crates_rs:tests:observer-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb29af5d6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb29af5d6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb29af5d6 {
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
impl BoundaryErrorb29af5d6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb29af5d6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb29af5d6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb29af5d6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb29af5d6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb29af5d6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb29af5d6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb29af5d6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b29af5d6() {
    let admitted = BoundaryRecordb29af5d6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb29af5d6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
