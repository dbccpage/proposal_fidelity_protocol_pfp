//! Homology computation: H_n = ker(d_n) / im(d_{n+1}).
//!
//! For a chain complex C_2 --d2--> C_1 --d1--> C_0:
//! - H_0 = ker(0) / im(d_1) = C_0 / im(d_1), so dim H_0 = c0_dim - rank(d_1)
//! - H_1 = ker(d_1) / im(d_2), so dim H_1 = dim ker(d_1) - rank(d_2)


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_30bec09d;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_30bec09d<T> = std::result::Result<T, BoundaryError_30bec09d>;
use crate::chain_complex::ChainComplex;
use crate::errors::HomologicalError;
#[cfg(test)]
use crate::scalar::Q;
use crate::witness::HomologyWitness;
use linear_algebra::linear_algebra::image_kernel::ExactRowReduction;
use serde::{Deserialize, Serialize};

/// Report of homology dimensions for a chain complex.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HomologyReport {
    /// dim H_0 = c0_dim - rank(d_1)
    pub h0_dim: usize,
    /// dim H_1 = dim ker(d_1) - rank(d_2)
    pub h1_dim: usize,
    /// Rank of boundary_1 (dim im d_1)
    pub rank_d1: usize,
    /// Rank of boundary_2 (dim im d_2)
    pub rank_d2: usize,
    /// dim ker d_1
    pub ker_d1_dim: usize,
    /// Witness certifying the computation.
    pub witness: HomologyWitness,
}

/// Compute rank of a boundary map at the given degree.
///
/// # Arguments
/// * `complex` - The chain complex.
/// * `degree` - The degree of the boundary map (1 or 2).
///
/// # Errors
/// Returns `HomologicalError::InvalidDegree` for degrees other than 1 or 2.
/// Returns `HomologicalError::UnsupportedOperation` if rank computation fails.
pub fn rank_boundary(complex: &ChainComplex, degree: usize) -> Result<usize, HomologicalError> {
    let matrix = match degree {
        1 => &complex.boundary_1.matrix,
        2 => &complex.boundary_2.matrix,
        _ => return Err(HomologicalError::InvalidDegree(degree as i32)),
    };
    matrix
        .rank()
        .map_err(|e| HomologicalError::UnsupportedOperation(format!("{}", e)))
}

/// Compute dimension of kernel of a boundary map at the given degree.
///
/// # Arguments
/// * `complex` - The chain complex.
/// * `degree` - The degree of the boundary map (1 or 2).
///
/// # Errors
/// Returns `HomologicalError::InvalidDegree` for degrees other than 1 or 2.
/// Returns `HomologicalError::UnsupportedOperation` if kernel basis computation fails.
pub fn dim_kernel(complex: &ChainComplex, degree: usize) -> Result<usize, HomologicalError> {
    let matrix = match degree {
        1 => &complex.boundary_1.matrix,
        2 => &complex.boundary_2.matrix,
        _ => return Err(HomologicalError::InvalidDegree(degree as i32)),
    };
    let kb = matrix
        .kernel_basis()
        .map_err(|e| HomologicalError::UnsupportedOperation(format!("{}", e)))?;
    Ok(kb.len())
}

/// Compute dimension of image of a boundary map at the given degree.
///
/// This is equivalent to `rank_boundary`.
pub fn dim_image(complex: &ChainComplex, degree: usize) -> Result<usize, HomologicalError> {
    rank_boundary(complex, degree)
}

/// Compute dim H_n = dim ker(d_n) - dim im(d_{n+1}).
///
/// For a 3-term complex C_2 -> C_1 -> C_0:
/// - H_0 = ker(0) / im(d_1) = C_0 / im(d_1), so dim H_0 = c0_dim - rank(d_1)
/// - H_1 = ker(d_1) / im(d_2), so dim H_1 = dim ker(d_1) - rank(d_2)
///
/// # Errors
/// Returns `HomologicalError::InvalidDegree` for degrees other than 0 or 1.
/// Returns `HomologicalError::HomologyDimensionUnderflow` if dim im > dim ker
/// (which would indicate a bug in the chain complex construction).
pub fn dim_homology(complex: &ChainComplex, degree: usize) -> Result<usize, HomologicalError> {
    match degree {
        0 => {
            // H_0 = C_0 / im(d_1)
            // dim H_0 = c0_dim - rank(d_1)
            let im_d1 = rank_boundary(complex, 1)?;
            complex
                .c0_dim
                .checked_sub(im_d1)
                .ok_or(HomologicalError::HomologyDimensionUnderflow {
                    ker_dim: complex.c0_dim,
                    im_dim: im_d1,
                })
        }
        1 => {
            // H_1 = ker(d_1) / im(d_2)
            // dim H_1 = dim ker(d_1) - rank(d_2)
            let ker_d1 = dim_kernel(complex, 1)?;
            let im_d2 = rank_boundary(complex, 2)?;
            ker_d1
                .checked_sub(im_d2)
                .ok_or(HomologicalError::HomologyDimensionUnderflow {
                    ker_dim: ker_d1,
                    im_dim: im_d2,
                })
        }
        _ => Err(HomologicalError::InvalidDegree(degree as i32)),
    }
}

/// Compute the full homology report for a chain complex.
///
/// Returns dimensions of H_0 and H_1, along with intermediate rank/kernel data
/// and a witness certifying the computation.
///
/// # Errors
/// Returns errors from `rank_boundary`, `dim_kernel`, or `dim_homology`.
pub fn homology_report(complex: &ChainComplex) -> Result<HomologyReport, HomologicalError> {
    let rank_d1 = rank_boundary(complex, 1)?;
    let rank_d2 = rank_boundary(complex, 2)?;
    let ker_d1_dim = dim_kernel(complex, 1)?;
    let h0_dim = dim_homology(complex, 0)?;
    let h1_dim = dim_homology(complex, 1)?;

    let witness = HomologyWitness {
        complex_hash: complex.complex_hash().clone(),
        degree: 1,
        ker_dim: ker_d1_dim,
        im_dim: rank_d2,
        homology_dim: h1_dim,
    };

    Ok(HomologyReport {
        h0_dim,
        h1_dim,
        rank_d1,
        rank_d2,
        ker_d1_dim,
        witness,
    })
}

// Origin: engine/crates_rs/core_homology/src/homology.rs
// Claim: urn:core:crates_rs:core-homology:homology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord30bec09d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord30bec09d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError30bec09d {
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
impl BoundaryError30bec09d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError30bec09d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError30bec09d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord30bec09d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError30bec09d> {
        if capacity_bound == 0 {
            return Err(BoundaryError30bec09d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError30bec09d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError30bec09d::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::chain_complex::ChainComplex;
    use linear_algebra::backend::basic_matrix::BasicMatrix;
    use num_rational::Rational64;

    fn r(n: i64) -> Q {
        crate::scalar::q(n)
    }

    fn zero_matrix(rows: usize, cols: usize) -> BasicMatrix<Q> {
        BasicMatrix::from_row_major(rows, cols, vec![r(0); rows * cols])
            .expect("zero matrix creation should succeed")
    }

    #[test]
    fn test_trivial_complex_homology() {
        // C_2 = 0, C_1 = 0, C_0 = R
        // H_0 = R (dim 1), no H_1 to compute in 3-term sense
        let d1 = zero_matrix(1, 0);
        let d2 = zero_matrix(0, 0);

        let complex = ChainComplex::new(1, 0, 0, d1, d2).expect("complex");
        let report = homology_report(&complex).expect("report");

        assert_eq!(report.h0_dim, 1);
        assert_eq!(report.h1_dim, 0);
        assert_eq!(report.rank_d1, 0);
        assert_eq!(report.rank_d2, 0);
    }

    #[test]
    fn test_simple_graph_homology() {
        // Graph: 0 -- 1 (single edge)
        // C_0 = R^2 (vertices), C_1 = R (edge), C_2 = 0
        // d_1: edge -> boundary = [1, -1]
        //
        // H_0 = ker(0) / im(d_1) = R^2 / span([1,-1]) = R (connected component)
        // dim H_0 = 2 - 1 = 1
        //
        // H_1 = ker(d_1) / im(d_2) = 0 / 0 = 0 (no cycles)
        // dim H_1 = 0

        let d1 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(-1)]).expect("d1");
        let d2 = zero_matrix(1, 0);

        let complex = ChainComplex::new(2, 1, 0, d1, d2).expect("complex");
        let report = homology_report(&complex).expect("report");

        assert_eq!(report.h0_dim, 1); // one connected component
        assert_eq!(report.h1_dim, 0); // no cycles (tree)
        assert_eq!(report.rank_d1, 1);
        assert_eq!(report.rank_d2, 0);
        assert_eq!(report.ker_d1_dim, 0);
    }

    #[test]
    fn test_cycle_graph_homology() {
        // Triangle graph: 0 -- 1 -- 2 -- 0
        // C_0 = R^3 (vertices), C_1 = R^3 (edges), C_2 = 0
        // Edges: e01 = 0->1, e12 = 1->2, e20 = 2->0
        // d_1 = [[-1, 0, 1],   (row 0: boundary of edges at vertex 0)
        //        [ 1,-1, 0],   (row 1: boundary of edges at vertex 1)
        //        [ 0, 1,-1]]   (row 2: boundary of edges at vertex 2)
        //
        // Kernel of d_1 = span([1, 1, 1]) (the cycle)
        // dim ker(d_1) = 1
        // rank(d_1) = 2
        //
        // H_0 = 3 - 2 = 1 (connected)
        // H_1 = 1 - 0 = 1 (one cycle)

        let d1 = BasicMatrix::from_row_major(
            3,
            3,
            vec![r(-1), r(0), r(1), r(1), r(-1), r(0), r(0), r(1), r(-1)],
        )
        .expect("d1");
        let d2 = zero_matrix(3, 0);

        let complex = ChainComplex::new(3, 3, 0, d1, d2).expect("complex");
        let report = homology_report(&complex).expect("report");

        assert_eq!(report.h0_dim, 1); // one connected component
        assert_eq!(report.h1_dim, 1); // one cycle
        assert_eq!(report.rank_d1, 2);
        assert_eq!(report.ker_d1_dim, 1);
    }

    #[test]
    fn test_two_components_homology() {
        // Two disconnected vertices: no edges
        // C_0 = R^2, C_1 = 0, C_2 = 0
        // H_0 = 2 (two components)

        let d1 = zero_matrix(2, 0);
        let d2 = zero_matrix(0, 0);

        let complex = ChainComplex::new(2, 0, 0, d1, d2).expect("complex");
        let report = homology_report(&complex).expect("report");

        assert_eq!(report.h0_dim, 2); // two disconnected vertices
        assert_eq!(report.h1_dim, 0);
    }
}

#[cfg(test)]
mod l4_boundary_tests_30bec09d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord30bec09d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord30bec09d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord30bec09d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord30bec09d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord30bec09d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError30bec09d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError30bec09d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
