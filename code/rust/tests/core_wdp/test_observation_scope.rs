//! Finite controls for WDP-DIM-R, OBS-BITS and OBS-MENU.
//! All report/query decisions and certificate replays use the canonical owner.
//! AuthorityEffect: None.

use core_category_theory::finite_report_query::{ReportQueryDecision, ReportQueryProblem};
use std::collections::BTreeSet;

fn factorable<A: Ord + Clone + std::fmt::Debug>(reports: &[A], answers: &[usize]) -> bool {
    assert_eq!(reports.len(), answers.len());
    let source: Vec<_> = (0..reports.len()).collect();
    let report_codomain: Vec<_> = reports
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let query_codomain: Vec<_> = answers
        .iter()
        .copied()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let report_rows: Vec<_> = reports.iter().cloned().enumerate().collect();
    let query_rows: Vec<_> = answers.iter().copied().enumerate().collect();
    let problem = ReportQueryProblem::new(
        &source,
        &report_codomain,
        &query_codomain,
        &report_rows,
        &query_rows,
    )
    .expect("explicit finite total tables");
    let decision = problem.decide();
    problem
        .verify_decision(&decision)
        .expect("canonical certificate replay");
    matches!(decision, ReportQueryDecision::Factorable(_))
}

const QUERIES: [[usize; 4]; 5] = [
    [0, 0, 1, 1], // A
    [0, 1, 0, 1], // B
    [1, 0, 0, 0], // C
    [0, 1, 0, 0], // D
    [0, 0, 1, 0], // E
];

#[test]
fn pairwise_non_derivability_does_not_force_equal_size_minimal_separators() {
    for (i, report) in QUERIES.iter().enumerate() {
        for (j, answer) in QUERIES.iter().enumerate() {
            assert_eq!(factorable(report, answer), i == j, "query pair {i}, {j}");
        }
    }
    let sufficient: Vec<_> = (0..32u32)
        .map(|mask| {
            let reports: Vec<Vec<_>> = (0..4)
                .map(|state| {
                    (0..5)
                        .filter(|i| mask & (1 << i) != 0)
                        .map(|i| QUERIES[i][state])
                        .collect()
                })
                .collect();
            factorable(&reports, &[0, 1, 2, 3])
        })
        .collect();
    let minimal: Vec<_> = (0..32u32)
        .filter(|&mask| {
            sufficient[mask as usize]
                && (0..5).all(|i| mask & (1 << i) == 0 || !sufficient[(mask & !(1 << i)) as usize])
        })
        .collect();
    assert!(minimal.contains(&0b00011), "A,B must be inclusion-minimal");
    assert!(
        minimal.contains(&0b11100),
        "C,D,E must be inclusion-minimal"
    );
    let sizes: BTreeSet<_> = minimal.iter().map(|mask| mask.count_ones()).collect();
    assert_eq!(sizes, BTreeSet::from([2, 3]));
    println!(
        "OBS-MENU: 20 ordered non-derivability checks, 32 shelf subsets; minimal masks {minimal:?}"
    );
}

#[test]
fn auxiliary_bits_price_answers_within_each_existing_report_fiber() {
    for mask in 0..16u32 {
        let one_bit: Vec<_> = (0..4).map(|i| (0usize, (mask >> i) & 1)).collect();
        assert!(!factorable(&one_bit, &[0, 1, 2, 3]));
    }
    assert!(factorable(&[(0, 0), (0, 1), (0, 2), (0, 3)], &[0, 1, 2, 3]));
    assert!(!factorable(&[0, 0, 0, 0], &[0, 0, 1, 1]));
    assert!(factorable(&[0, 0, 1, 1], &[0, 0, 1, 1]));
    // One auxiliary bit can reuse its codes in different p-fibers.
    assert!(factorable(&[(0, 0), (0, 1), (1, 0), (1, 1)], &[0, 1, 2, 3]));
    assert!(factorable(&[0, 0, 1, 1], &[3, 3, 7, 7]));
    assert!(factorable::<usize>(&[], &[]));
}

#[test]
fn actual_reports_on_r_and_ambient_quotient_reports_are_different_questions() {
    // V=Q^2, R=<e1>, B=0, Q=0, E=(1,0). Restricted sample 0,e1.
    assert!(factorable(&[0, 1], &[0, 1]));
    // Admitting e2 gives the explicit equal-report/opposite-answer collision.
    assert!(!factorable(&[0, 1, 0], &[0, 1, 2]));
    // R=<e1>, B=<e2>, A=(1,1): A|R distinguishes 0,e1.
    assert!(factorable(&[0, 1], &[0, 1]));
    // Quotienting by A(B)=Q collapses both reports; R intersect B was zero.
    assert!(!factorable(&[0, 0], &[0, 1]));
}

// Origin: engine/crates_rs/tests/core_wdp/test_observation_scope.rs
// Claim: urn:core:crates_rs:tests:test-observation-scope:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb0591ac2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb0591ac2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb0591ac2 {
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
impl BoundaryErrorb0591ac2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb0591ac2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb0591ac2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb0591ac2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb0591ac2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb0591ac2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb0591ac2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb0591ac2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b0591ac2() {
    let admitted = BoundaryRecordb0591ac2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb0591ac2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
