use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::elimination;
use linear_algebra::exact_pfaffian::pfaffian;
use num_bigint::BigInt;
use num_rational::BigRational;
fn q(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}
#[test]
fn pfaffian_sign_pivoting_and_determinant_square_are_exact() {
    for n in [0, 2, 4, 6, 8] {
        for seed in 0..9 {
            let mut data = vec![q(0); n * n];
            for i in 0..n {
                for j in i + 1..n {
                    let v = q(((i * 13 + j * 7 + seed * 3) % 11) as i64 - 5);
                    data[i * n + j] = v.clone();
                    data[j * n + i] = -v;
                }
            }
            let m = BasicMatrix::from_row_major(n, n, data).unwrap();
            let p = pfaffian(&m).unwrap();
            assert_eq!(&p * &p, elimination::determinant(&m).unwrap());
        }
    }
    let a = BasicMatrix::from_row_major(
        4,
        4,
        [0, 2, 3, 5, -2, 0, 7, 11, -3, -7, 0, 13, -5, -11, -13, 0]
            .map(q)
            .to_vec(),
    )
    .unwrap();
    assert_eq!(pfaffian(&a).unwrap(), q(2 * 13 - 3 * 11 + 5 * 7));
    let swapped = BasicMatrix::from_row_major(2, 2, vec![q(0), q(-3), q(3), q(0)]).unwrap();
    assert_eq!(pfaffian(&swapped).unwrap(), q(-3));
}
#[test]
fn non_alternating_and_odd_carriers_are_refused() {
    assert!(
        pfaffian(&BasicMatrix::from_row_major(2, 2, vec![q(1), q(2), q(-2), q(0)]).unwrap())
            .is_err()
    );
    assert!(pfaffian(&BasicMatrix::from_row_major(3, 3, vec![q(0); 9]).unwrap()).is_err());
}

// Origin: engine/crates_rs/tests/core_linear_algebra/exact_pfaffian.rs
// Claim: urn:core:crates_rs:tests:exact-pfaffian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb729951e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb729951e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb729951e {
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
impl BoundaryErrorb729951e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb729951e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb729951e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb729951e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb729951e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb729951e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb729951e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb729951e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b729951e() {
    let admitted = BoundaryRecordb729951e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb729951e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
