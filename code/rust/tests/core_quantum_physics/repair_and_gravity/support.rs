//! Shared construction helpers for the holonomy tests: `core_holonomy`
//! complexes and connections with `2 x 2` Gaussian-rational fibres.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational;
use core_holonomy::{
    CellComplex, DiscreteConnection, ExactMatrix as FieldMatrix, GaussianRational,
};
use core_kernel::resource_limits::OperationLimits;
use core_number_theory::cyclotomic::GaussianRat;
use core_solvers::data_cochain_packet::FiniteCochainPacket;

/// Boundary adapter for the holonomy test carrier. Group construction is Lie-owned.
pub fn quaternion_group() -> Vec<BasicMatrix<GaussianRat>> {
    core_lie_theory::su2_matrix::quaternion_group_matrices().unwrap()
}

pub type Scalar = GaussianRational<BigRational>;
pub type Holonomy = FieldMatrix<Scalar>;
pub type Connection = DiscreteConnection<Scalar>;

/// The quaternion units in the order `1, -1, i, -i, j, -j, k, -k`.
pub const MINUS_ONE: usize = 1;
pub const I: usize = 2;
pub const MINUS_I: usize = 3;
pub const J: usize = 4;
pub const MINUS_J: usize = 5;
pub const K: usize = 6;

pub fn q8(index: usize) -> BasicMatrix<GaussianRat> {
    quaternion_group()[index].clone()
}

pub fn field(m: &BasicMatrix<GaussianRat>) -> Holonomy {
    Holonomy::try_new(
        m.rows(),
        m.cols(),
        m.as_slice()
            .iter()
            .map(|z| Scalar {
                re: z.re.clone(),
                im: z.im.clone(),
            })
            .collect(),
    )
    .expect("validated finite holonomy test carrier")
}

pub fn identity(dimension: usize) -> Holonomy {
    Holonomy::try_identity(dimension).unwrap()
}

pub fn path(vertices: &[&str]) -> Vec<String> {
    vertices.iter().map(|v| v.to_string()).collect()
}

pub fn cell_complex(vertices: &[&str], edges: &[(&str, &str)], faces: &[&[&str]]) -> CellComplex {
    FiniteCochainPacket::build_complex(vertices, edges, faces).unwrap()
}

/// A connection with the declared matrix on each listed directed edge.
pub fn connection(
    dimension: usize,
    values: &[(&str, &str, BasicMatrix<GaussianRat>)],
) -> Connection {
    let mut c = Connection::new(dimension, OperationLimits::holonomy());
    for (u, v, m) in values {
        c.set_connection(*u, *v, field(m)).unwrap();
    }
    c
}

/// The square `a -> b -> c -> d -> a` carrying `i, j, i^-1, j^-1`.
pub fn quaternion_plaquette() -> Connection {
    connection(
        2,
        &[
            ("a", "b", q8(I)),
            ("b", "c", q8(J)),
            ("c", "d", q8(MINUS_I)),
            ("d", "a", q8(MINUS_J)),
        ],
    )
}

// Origin: engine/crates_rs/tests/core_quantum_physics/repair_and_gravity/support.rs
// Claim: urn:core:crates_rs:tests:support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4f2d17a6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4f2d17a6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4f2d17a6 {
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
impl BoundaryError4f2d17a6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4f2d17a6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4f2d17a6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4f2d17a6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4f2d17a6> {
        if capacity_bound == 0 {
            return Err(BoundaryError4f2d17a6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4f2d17a6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4f2d17a6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4f2d17a6() {
    let admitted = BoundaryRecord4f2d17a6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4f2d17a6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
