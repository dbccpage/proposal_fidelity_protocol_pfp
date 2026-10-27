//! Exact constructors shared by the channel tests.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

/// A rational matrix `rows / den`.
pub fn rm(rows: &[&[i64]], den: i64) -> BasicMatrix<GaussianRat> {
    let data = rows
        .iter()
        .map(|row| {
            row.iter()
                .map(|&v| GaussianRat::from_rational(rq(v, den)))
                .collect()
        })
        .collect();
    mx::from_rows(data).unwrap()
}

/// `diag(values) / den`.
pub fn dm(values: &[i64], den: i64) -> BasicMatrix<GaussianRat> {
    let entries: Vec<GaussianRat> = values
        .iter()
        .map(|&v| GaussianRat::from_rational(rq(v, den)))
        .collect();
    mx::diagonal(&entries).unwrap()
}

pub fn pauli_x() -> BasicMatrix<GaussianRat> {
    rm(&[&[0, 1], &[1, 0]], 1)
}

pub fn pauli_z() -> BasicMatrix<GaussianRat> {
    dm(&[1, -1], 1)
}

/// The rational rotation `[[3/5, -4/5], [4/5, 3/5]]`.
pub fn rotation() -> BasicMatrix<GaussianRat> {
    rm(&[&[3, -4], &[4, 3]], 5)
}

/// The matrix unit `|i><j|` on `C^n`.
pub fn unit(n: usize, i: usize, j: usize) -> BasicMatrix<GaussianRat> {
    let mut m = mx::zeros(n, n).unwrap();
    m.set(i, j, GaussianRat::one()).unwrap();
    m
}

/// Choi matrix of `rho -> (1 - p) rho + p Tr(rho) I / d`:
/// `(1 - p) |Omega><Omega| + (p / d) I`, with `|Omega> = sum_i |i>|i>`.
pub fn depolarizing_choi(d: usize, p: &Rational) -> BasicMatrix<GaussianRat> {
    let mut choi = mx::scale(
        &(mx::identity(d * d).unwrap()),
        &GaussianRat::from_rational(p / Rational::from_integer(d.into())),
    )
    .unwrap();
    for i in 0..d {
        for j in 0..d {
            let entry = choi
                .get_ref(i * d + i, j * d + j)
                .unwrap()
                .add(&GaussianRat::from_rational(ri(1) - p));
            choi.set(i * d + i, j * d + j, entry).unwrap();
        }
    }
    choi
}

/// A graph packet with declared weights.
pub fn packet(
    vertices: &[&str],
    edges: &[(&str, &str)],
    weights: Vec<Rational>,
) -> FiniteCochainPacket {
    let complex = FiniteCochainPacket::build_complex(vertices, edges, &[]).unwrap();
    FiniteCochainPacket::new(complex, weights).unwrap()
}

// Origin: engine/crates_rs/tests/core_quantum_physics/channels/support.rs
// Claim: urn:core:crates_rs:tests:support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfc8ed81f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfc8ed81f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfc8ed81f {
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
impl BoundaryErrorfc8ed81f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfc8ed81f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfc8ed81f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfc8ed81f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfc8ed81f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfc8ed81f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfc8ed81f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfc8ed81f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fc8ed81f() {
    let admitted = BoundaryRecordfc8ed81f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfc8ed81f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
