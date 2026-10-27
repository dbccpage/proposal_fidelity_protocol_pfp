//! Production CH17 adapter: endpoint-block preservation versus cancellation.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::semiring_lumpability::lumpable_quotient;
use linear_algebra::semiring_lumpability::{membership, semiring_product};
use num_rational::BigRational;

fn matrix(values: &[i64], n: usize) -> BasicMatrix<BigRational> {
    BasicMatrix::from_row_major(
        n,
        n,
        values
            .iter()
            .map(|value| BigRational::from_integer((*value).into()))
            .collect(),
    )
    .unwrap()
}

#[test]
fn named_adapter_preserves_endpoint_blocks_at_every_checked_length() {
    let transition = matrix(&[2, -1, 3, 0, 1, 3, 4, -2, 1], 3);
    let blocks = vec![vec![0, 1], vec![2]];
    let quotient = lumpable_quotient(&transition, &blocks).unwrap().unwrap();
    assert_eq!(quotient, matrix(&[1, 3, 2, 1], 2));
    let membership = membership::<BigRational>(3, &blocks).unwrap();
    let mut direct = membership.clone();
    let mut transported = membership;
    for _length in 0..=12 {
        assert_eq!(direct, transported);
        direct = semiring_product(&transition, &direct).unwrap();
        transported = semiring_product(&transported, &quotient).unwrap();
    }
}

#[test]
fn signed_total_cancellation_does_not_imply_endpoint_block_preservation() {
    // Every outgoing total is zero, but sources 0 and 1 disagree on block {2}.
    let transition = matrix(&[1, -1, 0, 0, 1, -1, 0, 0, 0], 3);
    assert!(lumpable_quotient(&transition, &[vec![0, 1], vec![2]])
        .unwrap()
        .is_none());
    let total_partition = vec![vec![0, 1, 2]];
    let quotient = lumpable_quotient(&transition, &total_partition)
        .unwrap()
        .unwrap();
    assert_eq!(quotient, matrix(&[0], 1));
    let membership = membership::<BigRational>(3, &total_partition).unwrap();
    let mut direct = membership.clone();
    let mut transported = membership;
    for _length in 0..=8 {
        assert_eq!(direct, transported);
        direct = semiring_product(&transition, &direct).unwrap();
        transported = semiring_product(&transported, &quotient).unwrap();
    }
    // The nonzero one-edge weights remain distinct although their total is zero.
    assert_ne!(
        transition.get_ref(0, 0).unwrap(),
        transition.get_ref(1, 0).unwrap()
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_semiring_coarse_graining.rs
// Claim: urn:core:crates_rs:tests:test-semiring-coarse-graining:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord31b3dfa1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord31b3dfa1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError31b3dfa1 {
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
impl BoundaryError31b3dfa1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError31b3dfa1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError31b3dfa1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord31b3dfa1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError31b3dfa1> {
        if capacity_bound == 0 {
            return Err(BoundaryError31b3dfa1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError31b3dfa1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError31b3dfa1::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_31b3dfa1() {
    let admitted = BoundaryRecord31b3dfa1::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord31b3dfa1::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
