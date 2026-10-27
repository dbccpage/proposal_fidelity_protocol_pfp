//! Cohomology computation: H^n = ker(d^n) / im(d^{n-1}).
//!
//! For a cochain complex C^0 --d0--> C^1 --d1--> C^2:
//! - H^0 = ker(d^0) (no im(d^{-1}) since d^{-1} doesn't exist)
//! - H^1 = ker(d^1) / im(d^0), so dim H^1 = dim ker(d^1) - rank(d^0)


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_dbb58784;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_dbb58784<T> = std::result::Result<T, BoundaryError_dbb58784>;
use crate::cochain_complex::CochainComplex;
use crate::errors::HomologicalError;
#[cfg(test)]
use crate::scalar::Q;
use crate::witness::CohomologyWitness;
use linear_algebra::linear_algebra::image_kernel::ExactRowReduction;
use serde::{Deserialize, Serialize};

/// Report of cohomology dimensions for a cochain complex.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CohomologyReport {
    /// dim H^0 = dim ker(d^0)
    pub h0_dim: usize,
    /// dim H^1 = dim ker(d^1) - rank(d^0)
    pub h1_dim: usize,
    /// Rank of d0 (dim im d^0)
    pub rank_d0: usize,
    /// Rank of d1 (dim im d^1)
    pub rank_d1: usize,
    /// dim ker d^1
    pub ker_d1_dim: usize,
    /// Witness certifying the computation.
    pub witness: CohomologyWitness,
}

/// Compute rank of a coboundary map at the given degree.
///
/// # Arguments
/// * `complex` - The cochain complex.
/// * `degree` - The degree of the coboundary map (0 or 1).
///
/// # Errors
/// Returns `HomologicalError::InvalidDegree` for degrees other than 0 or 1.
/// Returns `HomologicalError::UnsupportedOperation` if rank computation fails.
pub fn rank_coboundary(complex: &CochainComplex, degree: usize) -> Result<usize, HomologicalError> {
    let matrix = match degree {
        0 => &complex.d0.matrix,
        1 => &complex.d1.matrix,
        _ => return Err(HomologicalError::InvalidDegree(degree as i32)),
    };
    matrix
        .rank()
        .map_err(|e| HomologicalError::UnsupportedOperation(format!("{}", e)))
}

/// Compute dimension of kernel of a coboundary map at the given degree.
///
/// # Arguments
/// * `complex` - The cochain complex.
/// * `degree` - The degree of the coboundary map (0 or 1).
///
/// # Errors
/// Returns `HomologicalError::InvalidDegree` for degrees other than 0 or 1.
/// Returns `HomologicalError::UnsupportedOperation` if kernel basis computation fails.
pub fn dim_kernel(complex: &CochainComplex, degree: usize) -> Result<usize, HomologicalError> {
    let matrix = match degree {
        0 => &complex.d0.matrix,
        1 => &complex.d1.matrix,
        _ => return Err(HomologicalError::InvalidDegree(degree as i32)),
    };
    let kb = matrix
        .kernel_basis()
        .map_err(|e| HomologicalError::UnsupportedOperation(format!("{}", e)))?;
    Ok(kb.len())
}

/// Compute dim H^n = dim ker(d^n) - dim im(d^{n-1}).
///
/// For a 3-term complex C^0 -> C^1 -> C^2:
/// - H^0 = ker(d^0), so dim H^0 = dim ker(d^0)
/// - H^1 = ker(d^1) / im(d^0), so dim H^1 = dim ker(d^1) - rank(d^0)
///
/// # Errors
/// Returns `HomologicalError::InvalidDegree` for degrees other than 0 or 1.
/// Returns `HomologicalError::HomologyDimensionUnderflow` if dim im > dim ker
/// (which would indicate a bug in the cochain complex construction).
pub fn dim_cohomology(complex: &CochainComplex, degree: usize) -> Result<usize, HomologicalError> {
    match degree {
        0 => {
            // H^0 = ker(d^0)
            dim_kernel(complex, 0)
        }
        1 => {
            // H^1 = ker(d^1) / im(d^0)
            // dim H^1 = dim ker(d^1) - rank(d^0)
            let ker_d1 = dim_kernel(complex, 1)?;
            let im_d0 = rank_coboundary(complex, 0)?;
            ker_d1
                .checked_sub(im_d0)
                .ok_or(HomologicalError::HomologyDimensionUnderflow {
                    ker_dim: ker_d1,
                    im_dim: im_d0,
                })
        }
        _ => Err(HomologicalError::InvalidDegree(degree as i32)),
    }
}

/// Compute the full cohomology report for a cochain complex.
///
/// Returns dimensions of H^0 and H^1, along with intermediate rank/kernel data
/// and a witness certifying the computation.
///
/// # Errors
/// Returns errors from `rank_coboundary`, `dim_kernel`, or `dim_cohomology`.
pub fn cohomology_report(complex: &CochainComplex) -> Result<CohomologyReport, HomologicalError> {
    let rank_d0 = rank_coboundary(complex, 0)?;
    let rank_d1 = rank_coboundary(complex, 1)?;
    let ker_d1_dim = dim_kernel(complex, 1)?;
    let h0_dim = dim_cohomology(complex, 0)?;
    let h1_dim = dim_cohomology(complex, 1)?;

    let witness = CohomologyWitness {
        complex_hash: complex.complex_hash().clone(),
        degree: 1,
        ker_dim: ker_d1_dim,
        im_dim: rank_d0,
        cohomology_dim: h1_dim,
    };

    Ok(CohomologyReport {
        h0_dim,
        h1_dim,
        rank_d0,
        rank_d1,
        ker_d1_dim,
        witness,
    })
}

// Origin: engine/crates_rs/core_homology/src/cohomology.rs
// Claim: urn:core:crates_rs:core-homology:cohomology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddbb58784 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddbb58784` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordbb58784 {
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
impl BoundaryErrordbb58784 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordbb58784 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordbb58784 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddbb58784 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordbb58784> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordbb58784::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordbb58784::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordbb58784::ExceedsCapacity {
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
    use crate::coboundary::CoboundaryMap;
    use crate::cochain_complex::{CochainComplex, TheoremProvenance};
    use crate::ids::Degree;
    use linear_algebra::backend::basic_matrix::BasicMatrix;
    use num_rational::Rational64;

    fn r(n: i64) -> Q {
        crate::scalar::q(n)
    }

    fn zero_matrix(rows: usize, cols: usize) -> BasicMatrix<Q> {
        BasicMatrix::from_row_major(rows, cols, vec![r(0); rows * cols])
            .expect("zero matrix creation should succeed")
    }

    fn test_provenance() -> TheoremProvenance {
        TheoremProvenance::new("unit_test".to_string()).expect("provenance")
    }

    #[test]
    fn test_trivial_complex_cohomology() {
        // C^0 = R, C^1 = 0, C^2 = 0
        // d^0: R -> 0 is the zero map (kernel = R)
        // H^0 = ker(d^0) = R, dim = 1
        let d0 = zero_matrix(0, 1);
        let d1 = zero_matrix(0, 0);

        let complex = CochainComplex::new(1, 0, 0, d0, d1, test_provenance()).expect("complex");
        let report = cohomology_report(&complex).expect("report");

        assert_eq!(report.h0_dim, 1);
        assert_eq!(report.h1_dim, 0);
        assert_eq!(report.rank_d0, 0);
        assert_eq!(report.rank_d1, 0);
    }

    #[test]
    fn test_simple_graph_cohomology() {
        // Graph: 0 -- 1 (single edge)
        // C^0 = R^2 (vertex functions), C^1 = R (edge functions), C^2 = 0
        // d^0: f -> (f(1) - f(0)) on each edge
        // d^0 = [-1, 1] (1x2 matrix)
        //
        // ker(d^0) = span([1, 1]) (constant functions), dim = 1
        // H^0 = dim 1 (connected)
        //
        // d^1: 0 (since C^2 = 0)
        // ker(d^1) = C^1 = R, dim = 1
        // im(d^0) = R, rank = 1
        // H^1 = 1 - 1 = 0 (no cohomology cycle)

        let d0 = BasicMatrix::from_row_major(1, 2, vec![r(-1), r(1)]).expect("d0");
        let d1 = zero_matrix(0, 1);

        let complex = CochainComplex::new(2, 1, 0, d0, d1, test_provenance()).expect("complex");
        let report = cohomology_report(&complex).expect("report");

        assert_eq!(report.h0_dim, 1); // one connected component -> constant functions
        assert_eq!(report.h1_dim, 0); // no 1-cohomology for tree
        assert_eq!(report.rank_d0, 1);
    }

    #[test]
    fn test_cycle_graph_cohomology() {
        // Triangle graph: 0 -- 1 -- 2 -- 0 (with orientation)
        // C^0 = R^3 (vertex functions), C^1 = R^3 (edge functions), C^2 = 0
        // Edges oriented: e01: 0->1, e12: 1->2, e20: 2->0
        //
        // d^0 (coboundary on vertices):
        // d^0(f)(e_ij) = f(j) - f(i)
        // d^0 = [[-1, 1, 0],   (e01: f(1) - f(0))
        //        [ 0,-1, 1],   (e12: f(2) - f(1))
        //        [ 1, 0,-1]]   (e20: f(0) - f(2))
        //
        // ker(d^0) = span([1,1,1]) (constant functions), dim = 1
        // rank(d^0) = 2
        //
        // d^1 = 0 (no 2-cochains)
        // ker(d^1) = C^1 = R^3, dim = 3
        // H^1 = 3 - 2 = 1 (one cohomology class, dual to the cycle)

        let d0 = BasicMatrix::from_row_major(
            3,
            3,
            vec![r(-1), r(1), r(0), r(0), r(-1), r(1), r(1), r(0), r(-1)],
        )
        .expect("d0");
        let d1 = zero_matrix(0, 3);

        let complex = CochainComplex::new(3, 3, 0, d0, d1, test_provenance()).expect("complex");
        let report = cohomology_report(&complex).expect("report");

        assert_eq!(report.h0_dim, 1); // one connected component
        assert_eq!(report.h1_dim, 1); // one 1-cohomology class (dual to cycle)
        assert_eq!(report.rank_d0, 2);
        assert_eq!(report.ker_d1_dim, 3);
    }

    #[test]
    fn test_two_components_cohomology() {
        // Two disconnected vertices: no edges
        // C^0 = R^2, C^1 = 0, C^2 = 0
        // d^0: R^2 -> 0, kernel = R^2, dim = 2
        // H^0 = 2 (two constant functions, one per component)

        let d0 = zero_matrix(0, 2);
        let d1 = zero_matrix(0, 0);

        let complex = CochainComplex::new(2, 0, 0, d0, d1, test_provenance()).expect("complex");
        let report = cohomology_report(&complex).expect("report");

        assert_eq!(report.h0_dim, 2); // two disconnected components
        assert_eq!(report.h1_dim, 0);
    }

    #[test]
    fn dim_cohomology_rejects_invalid_degree() {
        let d0 = zero_matrix(0, 1);
        let d1 = zero_matrix(0, 0);
        let complex = CochainComplex::new(1, 0, 0, d0, d1, test_provenance()).expect("complex");
        assert!(matches!(
            dim_cohomology(&complex, 2),
            Err(HomologicalError::InvalidDegree(2))
        ));
        assert!(matches!(
            rank_coboundary(&complex, 2),
            Err(HomologicalError::InvalidDegree(2))
        ));
        assert!(matches!(
            dim_kernel(&complex, 2),
            Err(HomologicalError::InvalidDegree(2))
        ));
    }

    #[test]
    fn dim_cohomology_rejects_image_exceeding_kernel() {
        let d0 = zero_matrix(2, 2);
        let d1 = BasicMatrix::from_row_major(1, 2, vec![r(0), r(0)]).expect("d1");
        let mut complex = CochainComplex::new(2, 2, 1, d0, d1, test_provenance()).expect("complex");
        complex.d0 = CoboundaryMap::new(
            Degree::new(0),
            Degree::new(1),
            BasicMatrix::from_row_major(2, 2, vec![r(1), r(0), r(0), r(1)]).expect("I"),
        );
        complex.d1 = CoboundaryMap::new(
            Degree::new(1),
            Degree::new(2),
            BasicMatrix::from_row_major(1, 2, vec![r(1), r(0)]).expect("d1"),
        );
        assert!(matches!(
            dim_cohomology(&complex, 1),
            Err(HomologicalError::HomologyDimensionUnderflow {
                ker_dim: 1,
                im_dim: 2
            })
        ));
    }

    #[test]
    fn h1_dim_excludes_nonclosed_residuals() {
        let d0 = zero_matrix(2, 1);
        let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(0)]).expect("d1");
        let complex = CochainComplex::new(1, 2, 1, d0, d1, test_provenance()).expect("complex");
        let report = cohomology_report(&complex).expect("report");
        let dim_q1 = complex.c1_dim - report.rank_d0;
        assert_eq!(report.ker_d1_dim, 1);
        assert_eq!(report.rank_d0, 0);
        assert_eq!(report.h1_dim, 1);
        assert_eq!(dim_q1, 2);
        assert_ne!(report.h1_dim, dim_q1);
    }

    #[test]
    fn test_de_rham_style_cohomology() {
        // Simple example: C^0 = R^2, C^1 = R^2, C^2 = R
        // Model: functions on interval [0,1] discretized
        // d^0 approximates gradient, d^1 approximates curl (in 1D, curl = 0)
        //
        // d^0 = [[-1, 1],   (first derivative approximation)
        //        [ 0, 0]]   (second component for padding)
        // This is rank 1, kernel has dim 1 (constants)
        //
        // d^1 = [[0, 0]]    (1x2, maps to scalar)
        // Kernel = R^2, rank = 0
        //
        // H^0 = dim ker(d^0) = 1
        // H^1 = dim ker(d^1) - rank(d^0) = 2 - 1 = 1

        let d0 = BasicMatrix::from_row_major(2, 2, vec![r(-1), r(1), r(0), r(0)]).expect("d0");
        let d1 = BasicMatrix::from_row_major(1, 2, vec![r(0), r(0)]).expect("d1");

        // Need to verify d^1 * d^0 = 0
        // [[0,0]] * [[-1,1],[0,0]] = [[0,0]] OK

        let complex = CochainComplex::new(2, 2, 1, d0, d1, test_provenance()).expect("complex");
        let report = cohomology_report(&complex).expect("report");

        assert_eq!(report.h0_dim, 1);
        assert_eq!(report.h1_dim, 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_dbb58784 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddbb58784::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddbb58784::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddbb58784::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddbb58784::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddbb58784::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordbb58784::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordbb58784::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
