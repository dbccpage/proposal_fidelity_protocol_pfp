// AuthorityEffect: None.

//! Metric compatibility of finite quantum transports. A transport T preserves
//! a declared Gram matrix G exactly when T† G T = G. Isometries of a fixed
//! pairing compose, so a product of admitted steps has the same property.
//! Generic partial-map orbit classification lives in
//! `core_holonomy::functional_graph` and has no physics facade here.

use linear_algebra::{
    backend::basic_matrix::BasicMatrix,
    exact_field::{
        involution::{adjoint, is_hermitian, Involution},
        matrix::multiply,
        ExactFieldError,
    },
};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum IsometryError {
    #[error("Gram matrix and transport must be square matrices of one size")]
    Shape,
    #[error("the declared Gram matrix must be Hermitian")]
    NonHermitianGram,
    #[error("the transport exceeds dimension 128")]
    Budget,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

/// Check T† G T=G by exact multiplication over an involutive number field.
pub fn is_isometry<T: Involution>(
    gram: &BasicMatrix<T>,
    transport: &BasicMatrix<T>,
) -> Result<bool, IsometryError> {
    if gram.rows() != gram.cols() || transport.shape() != gram.shape() {
        return Err(IsometryError::Shape);
    }
    if gram.rows() > 128 {
        return Err(IsometryError::Budget);
    }
    if !is_hermitian(gram)? {
        return Err(IsometryError::NonHermitianGram);
    }
    Ok(multiply(&multiply(&adjoint(transport)?, gram)?, transport)? == *gram)
}
// Origin: engine/crates_rs/core_quantum_physics/src/transport_isometry_orbits.rs
// Claim: urn:core:crates_rs:core-quantum-physics:transport-isometry-orbits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use linear_algebra::exact_field::matrix::{from_rows, identity};
    use core_number_theory::cyclotomic::GaussianRat;
    use core_number_theory::rational::{rq, Rational};
    #[test]
    fn complex_and_real_transports_preserve_exactly_the_declared_pairing() {
        let rotation =
            from_rows(vec![vec![rq(3, 5), rq(-4, 5)], vec![rq(4, 5), rq(3, 5)]]).unwrap();
        assert!(is_isometry(&identity::<Rational>(2).unwrap(), &rotation).unwrap());
        assert!(!is_isometry(
            &from_rows(vec![vec![rq(2, 1), rq(0, 1)], vec![rq(0, 1), rq(1, 1)]]).unwrap(),
            &rotation
        )
        .unwrap());
        let u = from_rows(vec![
            vec![GaussianRat::i(), GaussianRat::zero()],
            vec![GaussianRat::zero(), GaussianRat::one()],
        ])
        .unwrap();
        assert!(is_isometry(&identity::<GaussianRat>(2).unwrap(), &u).unwrap());
        assert!(matches!(
            is_isometry(
                &identity::<Rational>(2).unwrap(),
                &identity::<Rational>(1).unwrap()
            ),
            Err(IsometryError::Shape)
        ));
        assert!(matches!(
            is_isometry(
                &from_rows(vec![vec![rq(1, 1), rq(1, 1)], vec![rq(0, 1), rq(1, 1)]]).unwrap(),
                &identity::<Rational>(2).unwrap()
            ),
            Err(IsometryError::NonHermitianGram)
        ));
    }
}
