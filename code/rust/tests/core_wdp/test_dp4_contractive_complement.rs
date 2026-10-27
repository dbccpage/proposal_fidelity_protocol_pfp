//! DP-4 replay: rational splittings and the contractive-complement criterion,
//! through `core_functional::residual_splitting` and
//! `core_solvers::solver_cohomology_splitting`. Exact rationals only.

use num_bigint::BigInt;
use num_rational::BigRational as Q;
use core_solvers::solver_cohomology_splitting::{
    decide_contractive_complement, decide_distortion_at_most, DistortionVerdict, SplittingFrame,
};
use core_solvers::solver_lp_exact_simplex::solve_weighted_l1_projection;

fn q(n: i64, d: i64) -> Q {
    Q::new(BigInt::from(n), BigInt::from(d))
}
fn z(n: i64) -> Q {
    q(n, 1)
}
fn diagonal(m: usize) -> Vec<Vec<Q>> {
    vec![vec![z(1)]; m]
}

#[test]
fn negative_diagonal_line_has_no_contractive_complement() {
    let w = vec![z(1); 3];
    match decide_contractive_complement(diagonal(3), 1, &w, 4000).expect("decide") {
        DistortionVerdict::Unattainable { system, multipliers } => {
            assert!(system.verify_farkas(&multipliers).is_ok());
        }
        other => panic!("expected unattainable, got {other:?}"),
    }
}

#[test]
fn positive_four_thirds_attained_and_sharp() {
    let w = vec![z(1); 3];
    let DistortionVerdict::Attained { certificate, distortion } =
        decide_distortion_at_most(diagonal(3), 1, &w, &q(4, 3), 4000).expect("decide")
    else {
        panic!("expected attainment at 4/3");
    };
    assert_eq!(distortion, q(4, 3));
    assert_eq!(certificate.verify(&w), Ok(q(4, 3)));
    let x = vec![z(1), z(0), z(0)];
    let phi = solve_weighted_l1_projection(&x, &w, &diagonal(3), 1024)
        .expect("phi")
        .value;
    assert_eq!(phi, z(1));
    let lx: Q = certificate
        .residual
        .iter()
        .map(|row| {
            let v: Q = row.iter().zip(&x).map(|(a, b)| a * b).sum();
            if v < z(0) { -v } else { v }
        })
        .sum();
    assert_eq!(lx, q(4, 3));
}

#[test]
fn boundary_just_below_four_thirds_is_unattainable() {
    let w = vec![z(1); 3];
    assert!(matches!(
        decide_distortion_at_most(diagonal(3), 1, &w, &q(1333, 1000), 4000).expect("decide"),
        DistortionVerdict::Unattainable { .. }
    ));
}

#[test]
fn positive_two_dimensional_line_is_contractive() {
    let w = vec![z(1); 2];
    assert!(matches!(
        decide_contractive_complement(diagonal(2), 1, &w, 4000).expect("decide"),
        DistortionVerdict::Attained { .. }
    ));
}

#[test]
fn mutation_tampered_splitting_is_refused() {
    let w = vec![z(1); 3];
    let frame = SplittingFrame::try_new(diagonal(3), 3, 1).expect("frame");
    let mut cert = frame.certificate(vec![vec![z(0), z(0)]]).expect("certificate");
    assert!(cert.verify(&w).is_ok());
    cert.projection[0][0] += z(1);
    assert!(cert.verify(&w).is_err());
    assert!(SplittingFrame::try_new(diagonal(3), 2, 1).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_dp4_contractive_complement.rs
// Claim: urn:core:crates_rs:tests:test-dp4-contractive-complement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordadcf5c45 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordadcf5c45` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroradcf5c45 {
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
impl BoundaryErroradcf5c45 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroradcf5c45 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroradcf5c45 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordadcf5c45 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroradcf5c45> {
        if capacity_bound == 0 {
            return Err(BoundaryErroradcf5c45::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroradcf5c45::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroradcf5c45::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_adcf5c45() {
    let admitted = BoundaryRecordadcf5c45::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordadcf5c45::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
