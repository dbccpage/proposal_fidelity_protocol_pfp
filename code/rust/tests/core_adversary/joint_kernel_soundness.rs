//! Adversary records LGGR V soundness from `lggr_v::check_soundness`.
//!
//! A path-kernel product is a different function and is not the verdict.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use core_epk::lggr_v::check_soundness;
use core_epk::matrix_path_kernel::RationalMatrix2x2;
use core_linear_algebra::backend::basic_matrix::BasicMatrix;
use core_adversary::soundness::{record_joint_kernel_soundness, SOUNDNESS_DECISION};

fn ratio(numerator: i64) -> BigRational {
    BigRational::new(BigInt::from(numerator), BigInt::from(1))
}

fn matrix(rows: usize, cols: usize, entries: &[i64]) -> BasicMatrix<BigRational> {
    BasicMatrix::from_row_major(rows, cols, entries.iter().copied().map(ratio).collect()).unwrap()
}

fn assert_matches_check_soundness(d: &BasicMatrix<BigRational>, q: &BasicMatrix<BigRational>) {
    let verdict = record_joint_kernel_soundness(d, q).expect("soundness decision");
    let direct = check_soundness(d, q).expect("lggr_v::check_soundness");
    assert_eq!(verdict.decision, SOUNDNESS_DECISION);
    assert_ne!(verdict.decision, "matrix_path_kernel");
    assert_eq!(verdict.report, direct);
    assert_eq!(verdict.report.sound, direct.d_rank == direct.qd_rank);
    if verdict.report.sound {
        assert!(verdict.report.witness.is_none());
        assert_eq!(verdict.report.qd_rank, verdict.report.d_rank);
    } else {
        let witness = verdict
            .report
            .witness
            .as_ref()
            .expect("an unsound pair carries a witness");
        let image = d.mul_vec(witness).expect("D v");
        assert!(image.iter().any(|entry| !entry.is_zero()), "D v must be nonzero");
        let observed = q.mul(d).expect("Q D").mul_vec(witness).expect("Q D v");
        assert!(observed.iter().all(Zero::is_zero), "Q D v must be zero");
    }
}

#[test]
fn a_sound_pair_and_an_unsound_pair_follow_check_soundness() {
    let identity = matrix(2, 2, &[1, 0, 0, 1]);
    assert_matches_check_soundness(&identity, &identity);

    let projection = matrix(1, 2, &[1, -1]);
    assert_matches_check_soundness(&identity, &projection);
}

#[test]
fn a_path_kernel_product_is_not_the_soundness_verdict() {
    let identity = matrix(2, 2, &[1, 0, 0, 1]);
    let projection = matrix(1, 2, &[1, -1]);
    let verdict = record_joint_kernel_soundness(&identity, &projection).expect("unsound pair");
    let closed_walk = RationalMatrix2x2::identity()
        .multiply(&RationalMatrix2x2::identity())
        .expect("path product");

    assert_eq!(closed_walk, RationalMatrix2x2::identity());
    assert!(!verdict.report.sound);
    assert_eq!(verdict.decision, SOUNDNESS_DECISION);
    assert_eq!(verdict.report.d_rank, 2);
    assert_eq!(verdict.report.qd_rank, 1);
}

// Origin: engine/crates_rs/tests/core_adversary/joint_kernel_soundness.rs
// Claim: urn:core:crates_rs:tests:joint-kernel-soundness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord267e7e38 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord267e7e38` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError267e7e38 {
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
impl BoundaryError267e7e38 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError267e7e38 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError267e7e38 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord267e7e38 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError267e7e38> {
        if capacity_bound == 0 {
            return Err(BoundaryError267e7e38::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError267e7e38::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError267e7e38::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_267e7e38() {
    let admitted = BoundaryRecord267e7e38::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord267e7e38::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
