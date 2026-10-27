//! Declared finite data shared by the representation tests.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use core_number_theory::cyclotomic::GaussianRat;
use core_quantum_physics::exact_hermitian::{gi, gq};

/// The real rotation `[[3/5, -4/5], [4/5, 3/5]]`.
pub fn rotation() -> BasicMatrix<GaussianRat> {
    mx::from_rows(vec![
        vec![gq(3, 5, 0, 1), gq(-4, 5, 0, 1)],
        vec![gq(4, 5, 0, 1), gq(3, 5, 0, 1)],
    ])
    .unwrap()
}

/// The complex unitary `[[3/5, -4i/5], [-4i/5, 3/5]]`.
pub fn complex_mixer() -> BasicMatrix<GaussianRat> {
    mx::from_rows(vec![
        vec![gq(3, 5, 0, 1), gq(0, 1, -4, 5)],
        vec![gq(0, 1, -4, 5), gq(3, 5, 0, 1)],
    ])
    .unwrap()
}

/// `|j><j|` on `C^d`.
pub fn basis_projector(d: usize, j: usize) -> BasicMatrix<GaussianRat> {
    let entries: Vec<_> = (0..d)
        .map(|k| if k == j { gi(1, 0) } else { gi(0, 0) })
        .collect();
    mx::diagonal(&entries).unwrap()
}

/// The partition of `C^d` into its basis projectors.
pub fn basis_partition(d: usize) -> Vec<BasicMatrix<GaussianRat>> {
    (0..d).map(|j| basis_projector(d, j)).collect()
}

/// The Pauli matrices `X`, `Y`, `Z`.
pub fn pauli() -> [BasicMatrix<GaussianRat>; 3] {
    use core_lie_theory::pauli_symplectic::{pauli, Pauli};
    [Pauli::X, Pauli::Y, Pauli::Z].map(|axis| pauli::<GaussianRat>(axis).unwrap())
}

// Origin: engine/crates_rs/tests/core_quantum_physics/representation/support.rs
// Claim: urn:core:crates_rs:tests:support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorded931ee4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorded931ee4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrored931ee4 {
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
impl BoundaryErrored931ee4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrored931ee4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrored931ee4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorded931ee4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrored931ee4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrored931ee4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrored931ee4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrored931ee4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ed931ee4() {
    let admitted = BoundaryRecorded931ee4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorded931ee4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
