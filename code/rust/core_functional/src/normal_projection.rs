//! Exact finite linear projection diagnostics; no interpretation of text.
//! Projectors remain pure linear maps. Norms and residual measurement live here.
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational;
use num_traits::Zero;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum NormalProjectionError {
    #[error("PROJECTION_SHAPE_MISMATCH")]
    Shape,
    #[error("PROJECTOR_NOT_IDEMPOTENT")]
    NotIdempotent,
    #[error("PROJECTION_MATRIX_REFUSED: {0}")]
    Matrix(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NormalProjectionMeasurement {
    pub retained_rate: Vec<BigRational>,
    pub normal_residual: Vec<BigRational>,
    pub normal_l1: BigRational,
    pub retained_observation: BigRational,
}

fn validate_projection_shapes(
    projector: &[Vec<BigRational>],
    rate: &[BigRational],
    observer: &[BigRational],
) -> Result<usize, NormalProjectionError> {
    let dim = rate.len();
    let valid_dims = dim > 0
        && projector.len() == dim
        && observer.len() == dim
        && projector.iter().all(|row| row.len() == dim);
    let any_zero_denom = projector
        .iter()
        .flatten()
        .chain(rate)
        .chain(observer)
        .any(|q| q.denom().is_zero());
    if !valid_dims || any_zero_denom {
        return Err(NormalProjectionError::Shape);
    }
    Ok(dim)
}

/// Measure n=(I-P)L and h=O(PL) only after exact P²=P admission.
pub fn measure_normal_projection(
    projector: &[Vec<BigRational>],
    rate: &[BigRational],
    observer: &[BigRational],
) -> Result<NormalProjectionMeasurement, NormalProjectionError> {
    let dim = validate_projection_shapes(projector, rate, observer)?;
    let matrix = |message: linear_algebra::backend::basic_matrix::MatrixError| {
        NormalProjectionError::Matrix(message.to_string())
    };
    let p = BasicMatrix::from_row_major(dim, dim, projector.iter().flatten().cloned().collect())
        .map_err(matrix)?;
    if p.mul(&p).map_err(matrix)? != p {
        return Err(NormalProjectionError::NotIdempotent);
    }
    let retained_rate = p.mul_vec(rate).map_err(matrix)?;
    let normal_residual: Vec<_> = rate
        .iter()
        .zip(&retained_rate)
        .map(|(l, pl)| l - pl)
        .collect();
    use num_traits::Signed;
    let normal_l1: BigRational = normal_residual.iter().map(|entry| entry.abs()).sum();
    let observation = BasicMatrix::from_row_major(1, dim, observer.to_vec()).map_err(matrix)?;
    let retained_observation = observation.mul_vec(&retained_rate).map_err(matrix)?[0].clone();
    Ok(NormalProjectionMeasurement {
        retained_rate,
        normal_residual,
        normal_l1,
        retained_observation,
    })
}

// Origin: engine/crates_rs/core_functional/src/normal_projection.rs
// Claim: urn:core:crates_rs:core-functional:normal-projection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }

    #[test]
    fn separates_retained_cochain_and_discarded_rate_exactly() {
        let half = BigRational::new(1.into(), 2.into());
        let result = measure_normal_projection(
            &[vec![q(1), q(0)], vec![q(0), q(0)]],
            &[q(3), half.clone()],
            &[q(1), q(7)],
        )
        .unwrap();
        assert_eq!(result.retained_observation, q(3));
        assert_eq!(result.normal_residual, vec![q(0), half.clone()]);
        assert_eq!(result.normal_l1, half);
    }

    #[test]
    fn rejects_a_false_projector_and_wrong_shapes() {
        assert_eq!(
            measure_normal_projection(&[vec![q(2)]], &[q(1)], &[q(1)]),
            Err(NormalProjectionError::NotIdempotent)
        );
        assert_eq!(
            measure_normal_projection(&[], &[q(1)], &[q(1)]),
            Err(NormalProjectionError::Shape)
        );
    }
}
