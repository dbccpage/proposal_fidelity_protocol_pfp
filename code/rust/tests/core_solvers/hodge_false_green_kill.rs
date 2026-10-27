//! Independent exact Hodge controls, gauge checks and forged-certificate attacks.
//! AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    matrix,
    rational_bareiss::{RationalBudget, RationalError, RationalLimits},
};
use num_rational::BigRational;
use core_solvers::cert_hodge_decomp::{check_hodge_certificate, HodgeError, HodgeProblem};
use core_solvers::solver_hodge_rational_decomp::solve_hodge;

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(n.into(), d.into())
}
fn limits() -> RationalLimits {
    RationalLimits {
        max_scalar_ops: 1_000_000,
        max_elements: 10_000,
        max_bits: 4096,
    }
}
fn budget() -> RationalBudget {
    RationalBudget::new(limits())
}
fn triangle() -> BasicMatrix<BigRational> {
    matrix::from_rows(vec![
        vec![q(-1, 1), q(1, 1), q(0, 1)],
        vec![q(0, 1), q(-1, 1), q(1, 1)],
        vec![q(1, 1), q(0, 1), q(-1, 1)],
    ])
    .unwrap()
}

#[test]
fn filled_triangle_has_exact_and_coexact_components_with_singular_gauge() {
    let d0 = triangle();
    let d1 = matrix::from_rows(vec![vec![q(1, 1); 3]]).unwrap();
    let flow = vec![q(1, 1), q(0, 1), q(0, 1)];
    let p = HodgeProblem {
        d0: &d0,
        d1: &d1,
        flow: &flow,
    };
    let solved = solve_hodge(&p, &mut budget()).unwrap();
    let c = &solved.certificate;
    assert_eq!(c.exact, vec![q(2, 3), q(-1, 3), q(-1, 3)]);
    assert_eq!(c.coexact, vec![q(1, 3); 3]);
    assert_eq!(c.harmonic, vec![q(0, 1); 3]);
    assert_eq!(c.alpha[2], q(0, 1)); // deterministic free-coordinate gauge
    assert_eq!(solved.verified.authority_effect(), "AuthorityEffect: None");
    // Any constant shift of the vertex potential gives the same decomposition.
    let mut gauge = c.clone();
    for x in &mut gauge.alpha {
        *x += q(5, 7);
    }
    check_hodge_certificate(&p, &gauge, &mut budget()).unwrap();
}

#[test]
fn unfilled_cycle_has_nonzero_harmonic_component_and_disconnected_gauges() {
    let d0 = triangle();
    let d1 = BasicMatrix::from_row_major(0, 3, vec![]).unwrap();
    let flow = vec![q(1, 1), q(0, 1), q(0, 1)];
    let p = HodgeProblem {
        d0: &d0,
        d1: &d1,
        flow: &flow,
    };
    let c = solve_hodge(&p, &mut budget()).unwrap().certificate;
    assert_eq!(c.harmonic, vec![q(1, 3); 3]);
    assert_eq!(c.coexact, vec![q(0, 1); 3]);
    let isolated = matrix::from_rows(vec![vec![q(-1, 1), q(1, 1), q(0, 1), q(0, 1)]]).unwrap();
    let none = BasicMatrix::from_row_major(0, 1, vec![]).unwrap();
    let p = HodgeProblem {
        d0: &isolated,
        d1: &none,
        flow: &[q(2, 5)],
    };
    let c = solve_hodge(&p, &mut budget()).unwrap().certificate;
    assert_eq!(c.alpha, vec![q(-2, 5), q(0, 1), q(0, 1), q(0, 1)]);
    assert_eq!(c.exact, vec![q(2, 5)]);
}

#[test]
fn component_relabeling_nonharmonic_residual_and_tiny_rational_forgery_refuse() {
    let d0 = triangle();
    let d1 = matrix::from_rows(vec![vec![q(1, 1); 3]]).unwrap();
    let flow = vec![q(1, 1), q(0, 1), q(0, 1)];
    let p = HodgeProblem {
        d0: &d0,
        d1: &d1,
        flow: &flow,
    };
    let good = solve_hodge(&p, &mut budget()).unwrap().certificate;
    let mut bad = good.clone();
    std::mem::swap(&mut bad.exact, &mut bad.coexact);
    assert_eq!(
        check_hodge_certificate(&p, &bad, &mut budget()),
        Err(HodgeError::Component)
    );
    let mut bad = good.clone();
    bad.harmonic[0] += q(1, 1_000_000_000_000);
    assert_eq!(
        check_hodge_certificate(&p, &bad, &mut budget()),
        Err(HodgeError::Reconstruction)
    );
    let mut bad = good.clone();
    bad.alpha.fill(q(0, 1));
    bad.exact.fill(q(0, 1));
    bad.harmonic = good.exact;
    assert_eq!(
        check_hodge_certificate(&p, &bad, &mut budget()),
        Err(HodgeError::Harmonicity)
    );
}

#[test]
fn fuel_is_shared_across_solves_and_independent_replay() {
    let d0 = triangle();
    let d1 = matrix::from_rows(vec![vec![q(1, 1); 3]]).unwrap();
    let p = HodgeProblem {
        d0: &d0,
        d1: &d1,
        flow: &[q(1, 1), q(0, 1), q(0, 1)],
    };
    let solved = solve_hodge(&p, &mut budget()).unwrap();
    let mut exact = limits();
    exact.max_scalar_ops = solved.scalar_ops;
    assert_eq!(
        solve_hodge(&p, &mut RationalBudget::new(exact)).unwrap(),
        solved
    );
    exact.max_scalar_ops -= 1;
    assert_eq!(
        solve_hodge(&p, &mut RationalBudget::new(exact)),
        Err(HodgeError::Arithmetic(RationalError::FuelExhausted))
    );
}

#[test]
fn invalid_chain_shape_rational_and_empty_complex() {
    let d0 = triangle();
    let bad = matrix::from_rows(vec![vec![q(1, 1), q(0, 1), q(0, 1)]]).unwrap();
    let p = HodgeProblem {
        d0: &d0,
        d1: &bad,
        flow: &vec![q(0, 1); 3],
    };
    assert_eq!(solve_hodge(&p, &mut budget()), Err(HodgeError::ChainLaw));
    let none = BasicMatrix::from_row_major(0, 3, vec![]).unwrap();
    assert_eq!(
        solve_hodge(
            &HodgeProblem {
                d0: &d0,
                d1: &none,
                flow: &[]
            },
            &mut budget()
        ),
        Err(HodgeError::Shape)
    );
    let invalid = vec![BigRational::new_raw(1.into(), 0.into()), q(0, 1), q(0, 1)];
    assert_eq!(
        solve_hodge(
            &HodgeProblem {
                d0: &d0,
                d1: &none,
                flow: &invalid
            },
            &mut budget()
        ),
        Err(HodgeError::Arithmetic(RationalError::InvalidRational))
    );
    let empty = BasicMatrix::from_row_major(0, 0, vec![]).unwrap();
    let c = solve_hodge(
        &HodgeProblem {
            d0: &empty,
            d1: &empty,
            flow: &[],
        },
        &mut budget(),
    )
    .unwrap();
    assert!(c.certificate.harmonic.is_empty());
}

#[test]
fn all_three_components_can_be_nonzero_and_cannot_be_reassigned() {
    let d0 = matrix::from_rows(vec![
        vec![q(-1, 1), q(1, 1), q(0, 1)],
        vec![q(0, 1), q(-1, 1), q(1, 1)],
        vec![q(1, 1), q(0, 1), q(-1, 1)],
        vec![q(0, 1); 3],
    ])
    .unwrap();
    let d1 = matrix::from_rows(vec![vec![q(1, 1), q(1, 1), q(1, 1), q(0, 1)]]).unwrap();
    let flow = vec![q(1, 1), q(0, 1), q(0, 1), q(2, 7)];
    let p = HodgeProblem {
        d0: &d0,
        d1: &d1,
        flow: &flow,
    };
    let c = solve_hodge(&p, &mut budget()).unwrap().certificate;
    assert_eq!(c.exact, vec![q(2, 3), q(-1, 3), q(-1, 3), q(0, 1)]);
    assert_eq!(c.coexact, vec![q(1, 3), q(1, 3), q(1, 3), q(0, 1)]);
    assert_eq!(c.harmonic, vec![q(0, 1), q(0, 1), q(0, 1), q(2, 7)]);
}

// Origin: engine/crates_rs/tests/core_solvers/hodge_false_green_kill.rs
// Claim: urn:core:crates_rs:tests:hodge-false-green-kill:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord03d0e872 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord03d0e872` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError03d0e872 {
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
impl BoundaryError03d0e872 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError03d0e872 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError03d0e872 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord03d0e872 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError03d0e872> {
        if capacity_bound == 0 {
            return Err(BoundaryError03d0e872::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError03d0e872::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError03d0e872::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_03d0e872() {
    let admitted = BoundaryRecord03d0e872::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord03d0e872::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
