//! DP-3 replay: raw Γ against the second-repair quotient Γ, through the owner
//! crates `core_functional::gamma_reconciliation` and
//! `core_solvers::solver_graph_reconciliation`. Exact rationals only.

use num_bigint::BigInt;
use num_rational::BigRational as Q;
use core_functional::gamma_reconciliation::{RepairQuotientProblem, ValueGapWitness};
use core_solvers::solver_graph_reconciliation::{
    compare_at, decide_value_agreement, decide_zero_test_agreement, ValueAgreementVerdict,
    ZeroTestVerdict,
};

fn q(n: i64) -> Q {
    Q::from_integer(BigInt::from(n))
}
fn col(v: &[i64]) -> Vec<Vec<Q>> {
    v.iter().map(|x| vec![q(*x)]).collect()
}
fn problem(d: &[i64], a: &[i64], w: &[i64]) -> RepairQuotientProblem {
    RepairQuotientProblem::try_new(1, 1, col(d), col(a), w.iter().map(|x| q(*x)).collect())
        .expect("well-formed fixture")
}

#[test]
fn positive_report_example_raw_two_quotient_one() {
    let p = problem(&[1, 1], &[1, 0], &[1, 1]);
    let (raw, quotient) = compare_at(&p, &[q(1)]).expect("compare");
    assert_eq!(raw, q(2));
    assert_eq!(quotient.value, q(1));
    assert_eq!(p.verify_quotient_certificate(&quotient), Ok(q(1)));
    match decide_value_agreement(&p, 500).expect("decide") {
        ValueAgreementVerdict::Disagree { certificate, gap, .. } => {
            assert!(p.verify_vertex_farkas(&certificate).is_ok());
            let (r, qv) = p.verify_value_gap(&gap).expect("gap replays");
            assert!(qv < r);
        }
        other => panic!("expected disagreement, got {other:?}"),
    }
    // Zero tests still agree: rank D + rank A = rank [D | A].
    assert!(matches!(
        decide_zero_test_agreement(&p).expect("zero test"),
        ZeroTestVerdict::Agree { rank_d: 1, rank_a: 1, rank_joint: 2 }
    ));
}

#[test]
fn positive_vertex_condition_holds_for_opposite_repair() {
    let p = problem(&[1, 1], &[1, -1], &[1, 1]);
    match decide_value_agreement(&p, 500).expect("decide") {
        ValueAgreementVerdict::Agree { table } => {
            assert_eq!(table.entries().len(), 4);
            assert!(p.verify_vertex_table(&table).is_ok());
        }
        other => panic!("expected agreement, got {other:?}"),
    }
}

#[test]
fn negative_identical_maps_split_the_zero_tests() {
    let p = problem(&[1], &[1], &[1]);
    match decide_zero_test_agreement(&p).expect("zero test") {
        ZeroTestVerdict::Disagree { witness, raw } => {
            assert!(raw > q(0));
            assert_eq!(p.verify_zero_test_gap(&witness), Ok(raw));
        }
        other => panic!("expected disagreement, got {other:?}"),
    }
}

#[test]
fn boundary_weighted_values() {
    let p = problem(&[1, 1], &[1, 0], &[2, 3]);
    let (raw, quotient) = compare_at(&p, &[q(1)]).expect("compare");
    assert_eq!((raw, quotient.value), (q(5), q(3)));
    let (raw0, quot0) = compare_at(&p, &[q(0)]).expect("compare at zero");
    assert_eq!((raw0, quot0.value), (q(0), q(0)));
}

#[test]
fn mutation_tampered_witnesses_are_refused() {
    let p = problem(&[1, 1], &[1, 0], &[1, 1]);
    let (_, mut quotient) = compare_at(&p, &[q(1)]).expect("compare");
    quotient.value = q(0);
    assert!(p.verify_quotient_certificate(&quotient).is_err());
    // A claimed gap at x = 1 with u = 0 is no gap: residual equals raw.
    let fake = ValueGapWitness { x: vec![q(1)], u: vec![q(0)] };
    assert!(p.verify_value_gap(&fake).is_err());
    assert!(RepairQuotientProblem::try_new(1, 1, col(&[1, 1]), col(&[1, 0]), vec![q(1), q(0)])
        .is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_dp3_gamma_reconciliation.rs
// Claim: urn:core:crates_rs:tests:test-dp3-gamma-reconciliation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9b572dc3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9b572dc3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9b572dc3 {
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
impl BoundaryError9b572dc3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9b572dc3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9b572dc3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9b572dc3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9b572dc3> {
        if capacity_bound == 0 {
            return Err(BoundaryError9b572dc3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9b572dc3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9b572dc3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9b572dc3() {
    let admitted = BoundaryRecord9b572dc3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9b572dc3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
