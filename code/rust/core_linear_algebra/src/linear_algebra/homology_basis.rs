use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use crate::linear_algebra::image_kernel::{ExactLinearAlgebraError, ExactRowReduction};
use crate::proof::TheoremProvenance;
use num_rational::Rational64;
use num_traits::Zero;
use thiserror::Error;

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum HomologyBasisError {
    #[error("Boundary matrices dimensions are incompatible for composition: left cols {left_cols}, right rows {right_rows}")]
    DimensionMismatch { left_cols: usize, right_rows: usize },

    #[error("Sequence is not a chain complex: d_k * d_{{k+1}} != 0")]
    BoundaryNotSquaredZero,

    #[error("Reduction error: {0}")]
    Reduction(#[from] ExactLinearAlgebraError),

    #[error("Matrix error: {0}")]
    Matrix(#[from] MatrixError),

    #[error("{label} vector has wrong dimension: expected {expected}, actual {actual}")]
    VectorDimensionMismatch {
        label: &'static str,
        expected: usize,
        actual: usize,
    },

    #[error(
        "boundary rank exceeds cycle rank: boundary_rank={boundary_rank}, cycle_rank={cycle_rank}"
    )]
    BoundaryRankExceedsCycleRank {
        boundary_rank: usize,
        cycle_rank: usize,
    },

    #[error("homology rank formula violated: cycle_rank={cycle_rank}, boundary_rank={boundary_rank}, homology_rank={homology_rank}")]
    RankFormulaViolation {
        cycle_rank: usize,
        boundary_rank: usize,
        homology_rank: usize,
    },

    #[error("homology representative is not a cycle")]
    RepresentativeNotCycle,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HomologyBasisWitness {
    degree: usize,
    boundary_k_shape: (usize, usize),
    boundary_k_plus_1_shape: (usize, usize),
    cycle_rank: usize,
    boundary_rank: usize,
    homology_rank: usize,
    provenance: TheoremProvenance,
}

impl HomologyBasisWitness {
    pub fn degree(&self) -> usize {
        self.degree
    }
    pub fn boundary_k_shape(&self) -> (usize, usize) {
        self.boundary_k_shape
    }
    pub fn boundary_k_plus_1_shape(&self) -> (usize, usize) {
        self.boundary_k_plus_1_shape
    }
    pub fn cycle_rank(&self) -> usize {
        self.cycle_rank
    }
    pub fn boundary_rank(&self) -> usize {
        self.boundary_rank
    }
    pub fn homology_rank(&self) -> usize {
        self.homology_rank
    }
    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct HomologyBasis {
    ambient_dimension: usize,
    cycle_rank: usize,
    boundary_rank: usize,
    homology_rank: usize,
    representatives: Vec<Vec<Rational64>>,
    boundary_basis: Vec<Vec<Rational64>>,
    witness: HomologyBasisWitness,
}

impl HomologyBasis {
    pub fn ambient_dimension(&self) -> usize {
        self.ambient_dimension
    }
    pub fn cycle_rank(&self) -> usize {
        self.cycle_rank
    }
    pub fn boundary_rank(&self) -> usize {
        self.boundary_rank
    }
    pub fn homology_rank(&self) -> usize {
        self.homology_rank
    }
    pub fn representatives(&self) -> &[Vec<Rational64>] {
        &self.representatives
    }
    pub fn boundary_basis(&self) -> &[Vec<Rational64>] {
        &self.boundary_basis
    }
    pub fn witness(&self) -> &HomologyBasisWitness {
        &self.witness
    }
    pub fn provenance(&self) -> &TheoremProvenance {
        &self.witness.provenance
    }
}

fn check_vector_dimensions(
    label: &'static str,
    vectors: &[Vec<Rational64>],
    expected: usize,
) -> Result<(), HomologyBasisError> {
    for vector in vectors {
        if vector.len() != expected {
            return Err(HomologyBasisError::VectorDimensionMismatch {
                label,
                expected,
                actual: vector.len(),
            });
        }
    }

    Ok(())
}

pub fn homology_basis(
    degree: usize,
    boundary_k: &BasicMatrix<Rational64>,
    boundary_k_plus_1: &BasicMatrix<Rational64>,
    provenance: TheoremProvenance,
) -> Result<HomologyBasis, HomologyBasisError> {
    verify_chain_complex_step(boundary_k, boundary_k_plus_1)?;

    let cycles = boundary_k.kernel_basis()?;
    let boundaries = boundary_k_plus_1.image_basis()?;

    let cycle_vecs = cycles.vectors();
    let boundary_vecs = boundaries.vectors();
    let ambient_dimension = boundary_k.cols();

    check_vector_dimensions("cycle basis", cycle_vecs, ambient_dimension)?;
    check_vector_dimensions("boundary basis", boundary_vecs, ambient_dimension)?;

    let cycle_rank = cycle_vecs.len();
    let boundary_rank = boundary_vecs.len();
    if boundary_rank > cycle_rank {
        return Err(HomologyBasisError::BoundaryRankExceedsCycleRank {
            boundary_rank,
            cycle_rank,
        });
    }

    let homology_generators =
        select_homology_representatives(cycle_vecs, boundary_vecs, ambient_dimension, cycle_rank)?;
    verify_representatives_are_cycles(boundary_k, &homology_generators, ambient_dimension)?;

    let homology_rank = homology_generators.len();
    let witness = HomologyBasisWitness {
        degree,
        boundary_k_shape: (boundary_k.rows(), boundary_k.cols()),
        boundary_k_plus_1_shape: (boundary_k_plus_1.rows(), boundary_k_plus_1.cols()),
        cycle_rank,
        boundary_rank,
        homology_rank,
        provenance,
    };

    Ok(HomologyBasis {
        ambient_dimension,
        cycle_rank,
        boundary_rank,
        homology_rank,
        representatives: homology_generators,
        boundary_basis: boundary_vecs.to_vec(),
        witness,
    })
}

fn verify_chain_complex_step(
    boundary_k: &BasicMatrix<Rational64>,
    boundary_k_plus_1: &BasicMatrix<Rational64>,
) -> Result<(), HomologyBasisError> {
    if boundary_k.cols() != boundary_k_plus_1.rows() {
        return Err(HomologyBasisError::DimensionMismatch {
            left_cols: boundary_k.cols(),
            right_rows: boundary_k_plus_1.rows(),
        });
    }
    let composition = boundary_k.checked_mul(boundary_k_plus_1).map_err(|_| {
        HomologyBasisError::Matrix(MatrixError::InvalidOperation("checked_mul failed".into()))
    })?;
    if !composition.as_slice().iter().all(|x| x.is_zero()) {
        return Err(HomologyBasisError::BoundaryNotSquaredZero);
    }
    Ok(())
}

fn select_homology_representatives(
    cycle_vecs: &[Vec<Rational64>],
    boundary_vecs: &[Vec<Rational64>],
    ambient_dimension: usize,
    cycle_rank: usize,
) -> Result<Vec<Vec<Rational64>>, HomologyBasisError> {
    let boundary_rank = boundary_vecs.len();
    let mut current_basis = boundary_vecs.to_vec();
    let mut current_rank = boundary_rank;
    let mut homology_generators = Vec::new();

    for z in cycle_vecs {
        let mut test_basis = current_basis.clone();
        test_basis.push(z.clone());

        let test_matrix = BasicMatrix::from_row_major(
            test_basis.len(),
            ambient_dimension,
            test_basis.into_iter().flatten().collect(),
        )?;

        let rank = test_matrix.rank()?;
        if rank > current_rank {
            homology_generators.push(z.clone());
            current_basis.push(z.clone());
            current_rank = rank;
        }
    }

    let homology_rank = homology_generators.len();
    if homology_rank != cycle_rank - boundary_rank {
        return Err(HomologyBasisError::RankFormulaViolation {
            cycle_rank,
            boundary_rank,
            homology_rank,
        });
    }
    Ok(homology_generators)
}

fn verify_representatives_are_cycles(
    boundary_k: &BasicMatrix<Rational64>,
    homology_generators: &[Vec<Rational64>],
    ambient_dimension: usize,
) -> Result<(), HomologyBasisError> {
    for h in homology_generators {
        let h_mat = BasicMatrix::from_row_major(ambient_dimension, 1, h.clone())?;
        let res = boundary_k.checked_mul(&h_mat).map_err(|_| {
            HomologyBasisError::Matrix(MatrixError::InvalidOperation("checked_mul failed".into()))
        })?;
        if !res.as_slice().iter().all(|x| x.is_zero()) {
            return Err(HomologyBasisError::RepresentativeNotCycle);
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/homology_basis.rs
// Claim: urn:core:crates_rs:core-linear-algebra:homology-basis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_rational::Rational64;

    fn r(n: i64, d: i64) -> Rational64 {
        Rational64::new(n, d)
    }

    fn dummy_prov() -> TheoremProvenance {
        TheoremProvenance::DerivedFromFiniteVerification {
            theorem_id: crate::proof::TheoremId::new("test").unwrap(),
            replay: crate::proof::ReplayHash::from_bytes([0; 32]),
        }
    }

    #[test]
    fn test_homology_basis_trivial_triangle() {
        // C_1 -> C_0
        // d_1: 3x3 matrix
        let d_1_data = vec![
            r(-1, 1),
            r(0, 1),
            r(-1, 1),
            r(1, 1),
            r(-1, 1),
            r(0, 1),
            r(0, 1),
            r(1, 1),
            r(1, 1),
        ];
        let d_1 = BasicMatrix::from_row_major(3, 3, d_1_data).unwrap();

        // C_2 -> C_1
        // d_2: 3x1 matrix
        let d_2_data = vec![r(1, 1), r(1, 1), r(-1, 1)];
        let d_2 = BasicMatrix::from_row_major(3, 1, d_2_data).unwrap();

        let basis = homology_basis(1, &d_1, &d_2, dummy_prov()).unwrap();

        assert_eq!(basis.ambient_dimension(), 3);
        assert_eq!(basis.cycle_rank(), 1);
        assert_eq!(basis.boundary_rank(), 1);
        assert_eq!(basis.homology_rank(), 0); // Exact sequence at C_1
    }

    #[test]
    fn test_homology_basis_empty_boundary() {
        // C_1 -> C_0 (same d_1)
        let d_1_data = vec![
            r(-1, 1),
            r(0, 1),
            r(-1, 1),
            r(1, 1),
            r(-1, 1),
            r(0, 1),
            r(0, 1),
            r(1, 1),
            r(1, 1),
        ];
        let d_1 = BasicMatrix::from_row_major(3, 3, d_1_data).unwrap();

        // But no 2-cells. d_2 is a 3x0 matrix.
        let d_2 = BasicMatrix::from_row_major(3, 0, vec![]).unwrap();

        let basis = homology_basis(1, &d_1, &d_2, dummy_prov()).unwrap();

        assert_eq!(basis.ambient_dimension(), 3);
        assert_eq!(basis.cycle_rank(), 1);
        assert_eq!(basis.boundary_rank(), 0);
        assert_eq!(basis.homology_rank(), 1); // 1-dimensional hole
        assert_eq!(basis.representatives().len(), 1);
    }

    #[test]
    fn test_dimension_mismatch_rejected() {
        let d_1 = BasicMatrix::from_row_major(3, 3, vec![r(0, 1); 9]).unwrap();
        let d_2 = BasicMatrix::from_row_major(2, 1, vec![r(0, 1); 2]).unwrap();

        let result = homology_basis(1, &d_1, &d_2, dummy_prov());
        assert!(matches!(
            result,
            Err(HomologyBasisError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn test_boundary_not_squared_zero_rejected() {
        let d_1 =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let d_2 =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();

        let result = homology_basis(1, &d_1, &d_2, dummy_prov());
        assert!(matches!(
            result,
            Err(HomologyBasisError::BoundaryNotSquaredZero)
        ));
    }
}
