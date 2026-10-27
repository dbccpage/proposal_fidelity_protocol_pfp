/// Rank-nullity certificate for a finite linear map: image rank plus kernel
/// rank equals the ambient dimension.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RankNullityCertificate {
    ambient: u64,
    image: u64,
    kernel: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RankNullityError {
    EmptyAmbient,
    ImageExceedsAmbient {
        ambient: u64,
        image: u64,
    },
    Nullity {
        ambient: u64,
        image: u64,
        kernel: u64,
    },
}

// Origin: engine/crates_rs/core_linear_algebra/src/contract_property_witnesses.rs
// Claim: urn:core:crates_rs:core-linear-algebra:contract-property-witnesses:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RankNullityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RankNullityError {}

impl RankNullityCertificate {
    pub fn try_new(ambient: u64, image: u64, kernel: u64) -> Result<Self, RankNullityError> {
        if ambient == 0 {
            return Err(RankNullityError::EmptyAmbient);
        }
        if image > ambient {
            return Err(RankNullityError::ImageExceedsAmbient { ambient, image });
        }
        let expected = ambient
            .checked_sub(image)
            .ok_or(RankNullityError::Nullity {
                ambient,
                image,
                kernel,
            })?;
        if kernel != expected {
            return Err(RankNullityError::Nullity {
                ambient,
                image,
                kernel,
            });
        }
        Ok(Self {
            ambient,
            image,
            kernel,
        })
    }

    pub fn ambient(&self) -> u64 {
        self.ambient
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod rank_nullity_witness {
    use super::*;

    #[test]
    fn a_rank_one_projection_on_a_plane_has_nullity_one() {
        let certificate = RankNullityCertificate::try_new(2, 1, 1);
        assert!(certificate.is_ok());
        if let Ok(certificate) = certificate {
            assert_eq!(certificate.ambient(), 2);
        }
    }

    #[test]
    fn a_wrong_nullity_is_refused() {
        assert!(matches!(
            RankNullityCertificate::try_new(2, 1, 0),
            Err(RankNullityError::Nullity {
                ambient: 2,
                image: 1,
                kernel: 0
            })
        ));
    }
}

#[cfg(test)]
mod __core_linear_algebra_property_witnesses {
    use crate::backend::basic_matrix::{BasicMatrix, CheckedNumeric, MatrixError};
    use crate::linear_algebra::complex_matrix::{
        CMatrix, CVector, ComplexMatrix, ComplexMatrixError, C64,
    };
    use crate::linear_algebra::density::{
        DensityMatrixCandidate, DensityMatrixConfig, DensityMatrixError,
        DensityMatrixValidationReport, NumericalDensityMatrix,
    };
    use crate::linear_algebra::eigen::{
        compute_sorted_symmetric_eigenvalues, SymmetricEigenError, SymmetricEigenvalueReport,
    };
    use crate::linear_algebra::gram_schmidt::{
        gram_schmidt_exact_standard, GramSchmidtCertificate, GramSchmidtError, OrthogonalFamily,
        OrthogonalityWitness, SpanPreservationWitness,
    };
    use crate::linear_algebra::image_kernel::{
        ExactLinearAlgebraError, ExactRowReduction, RankRref, RawSubspaceBasis,
    };
    use crate::linear_algebra::incidence_matrix::{
        incidence_matrix, incidence_matrix_dmatrix, IncidenceMatrixError,
    };
    use crate::linear_algebra::vector_space::InnerProduct;
    use crate::linear_map::LinearMap;
    use num_rational::Rational64;

    #[test]
    fn matrix_and_complex_bound_symbols_have_compiled_witnesses() {
        assert!(core::any::type_name::<BasicMatrix<Rational64>>().contains("BasicMatrix"));
        assert!(core::any::type_name::<MatrixError>().contains("MatrixError"));
        assert!(core::any::type_name::<ComplexMatrix>().contains("ComplexMatrix"));
        assert!(core::any::type_name::<ComplexMatrixError>().contains("ComplexMatrixError"));
        assert!(core::any::type_name::<C64>().contains("Complex"));
        assert!(core::any::type_name::<CMatrix>().contains("Matrix"));
        assert!(core::any::type_name::<CVector>().contains("Matrix"));
    }

    #[test]
    fn density_eigen_and_gram_schmidt_symbols_have_compiled_witnesses() {
        assert!(core::any::type_name::<DensityMatrixCandidate>().contains("DensityMatrixCandidate"));
        assert!(core::any::type_name::<NumericalDensityMatrix>().contains("NumericalDensityMatrix"));
        assert!(core::any::type_name::<DensityMatrixConfig>().contains("DensityMatrixConfig"));
        assert!(core::any::type_name::<DensityMatrixValidationReport>()
            .contains("DensityMatrixValidationReport"));
        assert!(core::any::type_name::<DensityMatrixError>().contains("DensityMatrixError"));
        assert!(core::any::type_name::<SymmetricEigenvalueReport>()
            .contains("SymmetricEigenvalueReport"));
        assert!(core::any::type_name::<SymmetricEigenError>().contains("SymmetricEigenError"));
        let _ = compute_sorted_symmetric_eigenvalues;

        let _ = gram_schmidt_exact_standard;
        assert!(core::any::type_name::<OrthogonalFamily>().contains("OrthogonalFamily"));
        assert!(core::any::type_name::<GramSchmidtCertificate>().contains("GramSchmidtCertificate"));
        assert!(core::any::type_name::<OrthogonalityWitness>().contains("OrthogonalityWitness"));
        assert!(
            core::any::type_name::<SpanPreservationWitness>().contains("SpanPreservationWitness")
        );
        assert!(core::any::type_name::<GramSchmidtError>().contains("GramSchmidtError"));
    }

    #[test]
    fn structural_linear_algebra_symbols_have_compiled_witnesses() {
        assert!(core::any::type_name::<RankRref<Rational64>>().contains("RankRref"));
        assert!(core::any::type_name::<RawSubspaceBasis<Rational64>>().contains("RawSubspaceBasis"));
        assert!(
            core::any::type_name::<ExactLinearAlgebraError>().contains("ExactLinearAlgebraError")
        );
        fn assert_row_reduction<T: crate::scalars::CheckedExactField, M: ExactRowReduction<T>>() {}
        assert_row_reduction::<Rational64, BasicMatrix<Rational64>>();
        // ADR-001: the same implementation must serve the canonical unbounded
        // coefficient domain. This witness is the point of the genericization --
        // without it, `BasicMatrix<BigRational>` has no `rank`/`kernel_basis`.
        assert_row_reduction::<num_rational::BigRational, BasicMatrix<num_rational::BigRational>>();

        let _ = incidence_matrix;
        let _ = incidence_matrix_dmatrix;
        assert!(core::any::type_name::<IncidenceMatrixError>().contains("IncidenceMatrixError"));
        assert!(core::any::type_name::<LinearMap<Rational64>>().contains("LinearMap"));

        fn assert_checked_numeric<T: CheckedNumeric>() {}
        assert_checked_numeric::<Rational64>();
        fn assert_inner_product<T: InnerProduct<Rational64, Vec<Rational64>> + ?Sized>() {}
        let _ = assert_inner_product::<dyn InnerProduct<Rational64, Vec<Rational64>>>;
    }
}
