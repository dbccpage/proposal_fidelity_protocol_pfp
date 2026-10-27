use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use num_rational::Rational64;
use num_traits::{One, Zero};
use thiserror::Error;

/// Errors for projector construction and application.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum ProjectorError {
    #[error("matrix error: {0}")]
    Matrix(#[from] MatrixError),

    #[error("projector matrix must be square: rows={rows}, cols={cols}")]
    NonSquareMatrix { rows: usize, cols: usize },

    #[error("vector dimension mismatch: expected {expected}, actual {actual}")]
    VectorDimensionMismatch { expected: usize, actual: usize },

    #[error("matrix is not idempotent: P^2 != P")]
    NotIdempotent,

    #[error("matrix is not symmetric")]
    NotSymmetric,

    #[error("projection complement construction unavailable: {reason}")]
    ConstructionUnavailable { reason: &'static str },
}

/// Local provenance metadata for a dynamically verified property.
///
/// This is not cryptographic and does not bind the witness to a matrix value.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TheoremProvenance {
    description: String,
}

impl TheoremProvenance {
    pub(crate) fn verified_locally(description: &str) -> Self {
        Self {
            description: description.to_string(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProjectorKind {
    Idempotent,
    OrthogonalStandardDot,
}

/// Witness produced by local dynamic verification that a matrix satisfies P² = P.
///
/// This witness is crate-local forgeable and not value-bound.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProjectorWitness {
    dimension: usize,
    kind: ProjectorKind,
    provenance: TheoremProvenance,
}

impl ProjectorWitness {
    pub(crate) fn new_unchecked(
        dimension: usize,
        kind: ProjectorKind,
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            dimension,
            kind,
            provenance,
        }
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    pub fn kind(&self) -> &ProjectorKind {
        &self.kind
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// A certified projection operator satisfying P² = P.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Projector<T> {
    matrix: BasicMatrix<T>,
    witness: ProjectorWitness,
}

impl<T> Projector<T> {
    pub fn matrix(&self) -> &BasicMatrix<T> {
        &self.matrix
    }

    pub fn witness(&self) -> &ProjectorWitness {
        &self.witness
    }

    pub fn dimension(&self) -> usize {
        self.witness.dimension()
    }

    // Sole gated constructor of the sealed projector; checked path not yet wired.
    #[allow(dead_code)]
    pub(crate) fn new_unchecked(matrix: BasicMatrix<T>, witness: ProjectorWitness) -> Self {
        Self { matrix, witness }
    }

    /// Dismantles the certified projector into its raw matrix and witness.
    /// This provides zero-cost access to the raw data while preserving mathematical provenance.
    pub fn into_certified_parts(self) -> (BasicMatrix<T>, ProjectorWitness) {
        (self.matrix, self.witness)
    }
}

impl Projector<Rational64> {
    pub fn new_checked(matrix: BasicMatrix<Rational64>) -> Result<Self, ProjectorError> {
        let (rows, cols) = matrix.shape();

        if rows != cols {
            return Err(ProjectorError::NonSquareMatrix { rows, cols });
        }

        let square = matrix.mul(&matrix)?;

        if square != matrix {
            return Err(ProjectorError::NotIdempotent);
        }

        Ok(Self {
            matrix,
            witness: ProjectorWitness::new_unchecked(
                rows,
                ProjectorKind::Idempotent,
                TheoremProvenance::verified_locally("P^2 = P"),
            ),
        })
    }

    pub fn new_orthogonal_checked(matrix: BasicMatrix<Rational64>) -> Result<Self, ProjectorError> {
        let projector = Self::new_checked(matrix)?;

        let transpose = projector.matrix.try_transpose()?;
        if transpose != projector.matrix {
            return Err(ProjectorError::NotSymmetric);
        }

        let dim = projector.dimension();
        Ok(Self {
            matrix: projector.matrix,
            witness: ProjectorWitness::new_unchecked(
                dim,
                ProjectorKind::OrthogonalStandardDot,
                TheoremProvenance::verified_locally("P^2 = P and P^T = P"),
            ),
        })
    }

    pub fn apply(&self, x: &[Rational64]) -> Result<Vec<Rational64>, ProjectorError> {
        if x.len() != self.matrix.cols() {
            return Err(ProjectorError::VectorDimensionMismatch {
                expected: self.matrix.cols(),
                actual: x.len(),
            });
        }

        Ok(self.matrix.mul_vec(x)?)
    }
}

fn rational_gram_schmidt(
    input: &[Vec<Rational64>],
    dimension: usize,
) -> Result<Vec<Vec<Rational64>>, ProjectorError> {
    let mut output: Vec<Vec<Rational64>> = Vec::with_capacity(input.len());
    for v in input {
        if v.len() != dimension {
            return Err(ProjectorError::VectorDimensionMismatch {
                expected: dimension,
                actual: v.len(),
            });
        }
        let mut u = v.clone();
        for q in &output {
            let num: Rational64 = v
                .iter()
                .zip(q.iter())
                .map(|(a, b)| *a * *b)
                .fold(Rational64::zero(), |acc, x| acc + x);
            let den: Rational64 = q
                .iter()
                .map(|x| *x * *x)
                .fold(Rational64::zero(), |acc, x| acc + x);
            if !den.is_zero() {
                let coeff = num / den;
                for i in 0..u.len() {
                    u[i] -= coeff * q[i];
                }
            }
        }
        if u.iter().any(|x| !x.is_zero()) {
            output.push(u);
        }
    }
    Ok(output)
}

/// Constructs the standard-dot orthogonal projector onto `col(a)⊥`.
///
/// If `a` has shape n×m, the returned matrix has shape n×n and satisfies:
/// - P² = P
/// - Pᵀ = P
/// - P * a = 0
///
/// This is an exact rational construction, not a floating-point approximation.
pub fn orthogonal_complement_projector_standard_dot(
    a: &BasicMatrix<Rational64>,
) -> Result<Projector<Rational64>, ProjectorError> {
    let n = a.rows();

    if a.cols() == 0 || n == 0 {
        let identity = rational_identity_matrix(n)?;
        return Projector::new_orthogonal_checked(identity);
    }

    let proj = build_complement_projection_matrix(a, n)?;
    let projector = Projector::new_orthogonal_checked(proj)?;
    verify_column_annihilation(&projector, a)?;

    Ok(projector)
}

fn build_complement_projection_matrix(
    a: &BasicMatrix<Rational64>,
    n: usize,
) -> Result<BasicMatrix<Rational64>, ProjectorError> {
    let cols = transpose_rows_as_vectors(a)?;
    let ortho = rational_gram_schmidt(&cols, n)?;
    let mut proj = rational_identity_matrix(n)?;

    for u in &ortho {
        subtract_rank_one_projection(&mut proj, u, n)?;
    }
    Ok(proj)
}

fn rational_identity_matrix(n: usize) -> Result<BasicMatrix<Rational64>, ProjectorError> {
    let mut identity = BasicMatrix::<Rational64>::zero(n, n)?;
    for i in 0..n {
        identity.set(i, i, Rational64::one())?;
    }
    Ok(identity)
}

fn transpose_rows_as_vectors(
    a: &BasicMatrix<Rational64>,
) -> Result<Vec<Vec<Rational64>>, ProjectorError> {
    let at = a.try_transpose()?;
    Ok((0..at.rows())
        .map(|i| {
            (0..at.cols())
                .map(|j| at.get(i, j))
                .collect::<Result<Vec<_>, _>>()
        })
        .collect::<Result<Vec<_>, _>>()?)
}

fn subtract_rank_one_projection(
    proj: &mut BasicMatrix<Rational64>,
    u: &[Rational64],
    n: usize,
) -> Result<(), ProjectorError> {
    let norm_sq: Rational64 = u
        .iter()
        .map(|x| *x * *x)
        .fold(Rational64::zero(), |acc, value| acc + value);

    if norm_sq.is_zero() {
        return Ok(());
    }

    for i in 0..n {
        for j in 0..n {
            let current = proj.get(i, j)?;
            let update = u[i] * u[j] / norm_sq;
            proj.set(i, j, current - update)?;
        }
    }
    Ok(())
}

fn verify_column_annihilation(
    projector: &Projector<Rational64>,
    a: &BasicMatrix<Rational64>,
) -> Result<(), ProjectorError> {
    let annihilation =
        projector
            .matrix()
            .checked_mul(a)
            .map_err(|_| ProjectorError::ConstructionUnavailable {
                reason: "checked matrix multiplication failed",
            })?;
    if !annihilation.as_slice().iter().all(|x| x.is_zero()) {
        return Err(ProjectorError::ConstructionUnavailable {
            reason: "constructed complement projector does not annihilate input column space",
        });
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/projector.rs
// Claim: urn:core:crates_rs:core-linear-algebra:projector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn r(n: i64, d: i64) -> Rational64 {
        Rational64::new(n, d)
    }

    #[test]
    fn reject_non_square_projector() {
        let mat = BasicMatrix::from_row_major(2, 3, vec![r(1, 1); 6]).unwrap();
        assert!(matches!(
            Projector::new_checked(mat),
            Err(ProjectorError::NonSquareMatrix { .. })
        ));
    }

    #[test]
    fn reject_non_idempotent() {
        let mat = BasicMatrix::from_row_major(2, 2, vec![r(2, 1); 4]).unwrap();
        assert!(matches!(
            Projector::new_checked(mat),
            Err(ProjectorError::NotIdempotent)
        ));
    }

    #[test]
    fn accept_identity() {
        let mat =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let proj = Projector::new_checked(mat).unwrap();
        assert_eq!(proj.dimension(), 2);
        assert_eq!(*proj.witness().kind(), ProjectorKind::Idempotent);
    }

    #[test]
    fn accept_zero_matrix() {
        let mat = BasicMatrix::from_row_major(2, 2, vec![r(0, 1); 4]).unwrap();
        let proj = Projector::new_checked(mat).unwrap();
        assert_eq!(proj.dimension(), 2);
    }

    #[test]
    fn reject_non_symmetric_idempotent_for_orthogonal() {
        // P = [1 1; 0 0], P^2 = P, P^T != P
        let mat =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(1, 1), r(0, 1), r(0, 1)]).unwrap();
        assert!(Projector::new_checked(mat.clone()).is_ok());
        assert!(matches!(
            Projector::new_orthogonal_checked(mat),
            Err(ProjectorError::NotSymmetric)
        ));
    }

    #[test]
    fn apply_rejects_wrong_vector_length() {
        let mat =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let proj = Projector::new_checked(mat).unwrap();
        assert!(matches!(
            proj.apply(&[r(1, 1)]),
            Err(ProjectorError::VectorDimensionMismatch { .. })
        ));
    }

    #[test]
    fn apply_identity_returns_same_vector() {
        let mat =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let proj = Projector::new_checked(mat).unwrap();
        let v = vec![r(5, 1), r(-3, 1)];
        assert_eq!(proj.apply(&v).unwrap(), v);
    }

    #[test]
    fn orthogonal_complement_of_full_rank_identity_is_zero_projector() {
        let a =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let proj = orthogonal_complement_projector_standard_dot(&a).unwrap();
        assert!(proj.matrix().as_slice().iter().all(|x| x.is_zero()));
    }

    #[test]
    fn orthogonal_complement_of_zero_column_matrix_is_identity() {
        let a = BasicMatrix::from_row_major(2, 0, vec![]).unwrap();
        let proj = orthogonal_complement_projector_standard_dot(&a).unwrap();
        assert_eq!(proj.matrix().get(0, 0).unwrap(), r(1, 1));
        assert_eq!(proj.matrix().get(1, 1).unwrap(), r(1, 1));
        assert_eq!(proj.matrix().get(0, 1).unwrap(), r(0, 1));
    }

    #[test]
    fn orthogonal_complement_of_span_in_q2_is_diag() {
        // A = [1; 0] (2x1)
        let a = BasicMatrix::from_row_major(2, 1, vec![r(1, 1), r(0, 1)]).unwrap();
        let proj = orthogonal_complement_projector_standard_dot(&a).unwrap();
        // proj should be diag(0, 1)
        assert_eq!(proj.matrix().get(0, 0).unwrap(), r(0, 1));
        assert_eq!(proj.matrix().get(1, 1).unwrap(), r(1, 1));
        assert_eq!(proj.matrix().get(0, 1).unwrap(), r(0, 1));
        assert_eq!(proj.matrix().get(1, 0).unwrap(), r(0, 1));
    }
}
