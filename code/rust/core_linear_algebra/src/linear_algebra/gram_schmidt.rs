//! Exact rational Gram-Schmidt orthogonalization.
//!
//! ## Module Invariant
//! This module performs exact Gram-Schmidt over `Ratio<BigInt>` using the
//! standard coordinate dot product.
//!
//! It constructs an orthogonal basis from a linearly independent list of
//! coordinate vectors.
//!
//! ## What Is Certified
//! - input vector dimensions match the declared basis;
//! - no zero pivots occur;
//! - output vectors are pairwise orthogonal exactly;
//! - output vectors are nonzero exactly;
//! - output vector count equals input vector count;
//! - arithmetic is exact over `Ratio<BigInt>`.
//!
//! ## What Is Not Claimed
//! - orthonormality;
//! - numerical floating-point stability;
//! - arbitrary inner-product Gram matrix support;
//! - complex/Hermitian Gram-Schmidt;
//! - QR factorization;
//! - rank-revealing pivoting.
//!
//! ## Boundary
//! This module uses the standard dot product in the declared coordinate basis.
//! A separate `gram_schmidt_gram.rs` module should handle arbitrary Gram
//! matrices once `InnerProductSpace` is L4+.

use num_bigint::BigInt;
use num_rational::Ratio;
use num_traits::Zero;
use thiserror::Error;

use crate::basis::{BasisDescriptor, BasisError};
use crate::proof::{TheoremProvenance, VectorFamilyHash};
use crate::vector::{CoordinateVector, VectorError};

pub type BigRational = Ratio<BigInt>;

/// Errors for exact rational Gram-Schmidt.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum GramSchmidtError {
    #[error("basis error: {0}")]
    Basis(#[from] BasisError),

    #[error("vector error: {0}")]
    Vector(#[from] VectorError),

    #[error("input vector family is empty")]
    EmptyInput,

    #[error("input vector {index} has dimension {actual}, expected {expected}")]
    DimensionMismatch {
        index: usize,
        expected: usize,
        actual: usize,
    },

    #[error("input vector {index} has basis mismatch")]
    BasisMismatch { index: usize },

    #[error("zero pivot at input vector {index}; vectors are linearly dependent")]
    ZeroPivot { index: usize },

    #[error("internal verification failed: output vector {index} is zero")]
    OutputZero { index: usize },

    #[error("internal verification failed: output vectors {left} and {right} are not orthogonal")]
    OrthogonalityFailure { left: usize, right: usize },

    #[error("internal verification failed: span preservation failed at index {index}")]
    SpanPreservationFailure { index: usize },
}

/// Witness that a family of vectors is pairwise orthogonal under the standard
/// coordinate dot product.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OrthogonalityWitness {
    input_family_hash: VectorFamilyHash,
    vector_count: usize,
    basis: BasisDescriptor,
    provenance: TheoremProvenance,
    _private: (),
}

impl OrthogonalityWitness {
    pub(crate) fn new_unchecked(
        input_family_hash: VectorFamilyHash,
        vector_count: usize,
        basis: BasisDescriptor,
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            input_family_hash,
            vector_count,
            basis,
            provenance,
            _private: (),
        }
    }

    pub fn input_family_hash(&self) -> &VectorFamilyHash {
        &self.input_family_hash
    }

    pub fn vector_count(&self) -> usize {
        self.vector_count
    }

    pub fn basis(&self) -> &BasisDescriptor {
        &self.basis
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// Witness that Gram-Schmidt preserved the span by triangular operations.
///
/// In exact classical Gram-Schmidt, each output vector has the form:
///
/// `u_i = v_i - sum_{j < i} c_{ij} u_j`.
///
/// Therefore the change from input family to output family is triangular with
/// diagonal entries equal to `1`, hence span-preserving.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpanPreservationWitness {
    input_family_hash: VectorFamilyHash,
    vector_count: usize,
    basis: BasisDescriptor,
    provenance: TheoremProvenance,
    _private: (),
}

impl SpanPreservationWitness {
    pub(crate) fn new_unchecked(
        input_family_hash: VectorFamilyHash,
        vector_count: usize,
        basis: BasisDescriptor,
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            input_family_hash,
            vector_count,
            basis,
            provenance,
            _private: (),
        }
    }

    pub fn input_family_hash(&self) -> &VectorFamilyHash {
        &self.input_family_hash
    }

    pub fn vector_count(&self) -> usize {
        self.vector_count
    }

    pub fn basis(&self) -> &BasisDescriptor {
        &self.basis
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// Exact orthogonalization certificate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GramSchmidtCertificate {
    input_family_hash: VectorFamilyHash,
    input_count: usize,
    output_count: usize,
    basis: BasisDescriptor,
    projection_coefficients: Vec<Vec<BigRational>>,
    orthogonality: OrthogonalityWitness,
    span_preservation: SpanPreservationWitness,
    provenance: TheoremProvenance,
}

impl GramSchmidtCertificate {
    pub fn input_family_hash(&self) -> &VectorFamilyHash {
        &self.input_family_hash
    }

    pub fn input_count(&self) -> usize {
        self.input_count
    }

    pub fn output_count(&self) -> usize {
        self.output_count
    }

    pub fn basis(&self) -> &BasisDescriptor {
        &self.basis
    }

    pub fn projection_coefficients(&self) -> &[Vec<BigRational>] {
        &self.projection_coefficients
    }

    pub fn orthogonality(&self) -> &OrthogonalityWitness {
        &self.orthogonality
    }

    pub fn span_preservation(&self) -> &SpanPreservationWitness {
        &self.span_preservation
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// Output of exact rational Gram-Schmidt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OrthogonalFamily {
    vectors: Vec<CoordinateVector<BigRational>>,
    certificate: GramSchmidtCertificate,
}

impl OrthogonalFamily {
    pub fn vectors(&self) -> &[CoordinateVector<BigRational>] {
        &self.vectors
    }

    pub fn certificate(&self) -> &GramSchmidtCertificate {
        &self.certificate
    }

    pub fn into_parts(self) -> (Vec<CoordinateVector<BigRational>>, GramSchmidtCertificate) {
        (self.vectors, self.certificate)
    }
}

fn dot(a: &[BigRational], b: &[BigRational]) -> BigRational {
    let mut acc = BigRational::zero();

    for (x, y) in a.iter().zip(b.iter()) {
        acc += x * y;
    }

    acc
}

fn scalar_mul(s: &BigRational, v: &[BigRational]) -> Vec<BigRational> {
    v.iter().map(|x| s * x).collect()
}

fn sub_vec(a: &[BigRational], b: &[BigRational]) -> Vec<BigRational> {
    a.iter().zip(b.iter()).map(|(x, y)| x - y).collect()
}

fn is_zero_vec(v: &[BigRational]) -> bool {
    v.iter().all(Zero::is_zero)
}

fn verify_input_family(
    vectors: &[CoordinateVector<BigRational>],
    basis: &BasisDescriptor,
) -> Result<(), GramSchmidtError> {
    if vectors.is_empty() {
        return Err(GramSchmidtError::EmptyInput);
    }

    for (index, v) in vectors.iter().enumerate() {
        if v.basis().id() != basis.id() {
            return Err(GramSchmidtError::BasisMismatch { index });
        }

        let actual = v.coordinates().len();
        let expected = basis.dimension();

        if actual != expected {
            return Err(GramSchmidtError::DimensionMismatch {
                index,
                expected,
                actual,
            });
        }
    }

    Ok(())
}

fn verify_output_family(vectors: &[CoordinateVector<BigRational>]) -> Result<(), GramSchmidtError> {
    for (i, v) in vectors.iter().enumerate() {
        if is_zero_vec(v.coordinates()) {
            return Err(GramSchmidtError::OutputZero { index: i });
        }
    }

    for i in 0..vectors.len() {
        for j in 0..i {
            let pairing = dot(vectors[i].coordinates(), vectors[j].coordinates());

            if !pairing.is_zero() {
                return Err(GramSchmidtError::OrthogonalityFailure { left: j, right: i });
            }
        }
    }

    Ok(())
}

fn verify_span_preservation(
    inputs: &[CoordinateVector<BigRational>],
    outputs: &[CoordinateVector<BigRational>],
    coeffs: &[Vec<BigRational>],
) -> Result<(), GramSchmidtError> {
    for i in 0..outputs.len() {
        let mut expected_u = inputs[i].coordinates().to_vec();
        for j in 0..i {
            let projection = scalar_mul(&coeffs[i][j], outputs[j].coordinates());
            expected_u = sub_vec(&expected_u, &projection);
        }
        if expected_u != outputs[i].coordinates() {
            return Err(GramSchmidtError::SpanPreservationFailure { index: i });
        }
    }
    Ok(())
}

/// Exact rational Gram-Schmidt under the standard coordinate dot product.
///
/// This returns an orthogonal family, not an orthonormal family.
pub fn gram_schmidt_exact_standard(
    input: Vec<CoordinateVector<BigRational>>,
    input_family_hash: VectorFamilyHash,
    basis: BasisDescriptor,
    provenance: TheoremProvenance,
) -> Result<OrthogonalFamily, GramSchmidtError> {
    verify_input_family(&input, &basis)?;

    let mut output: Vec<CoordinateVector<BigRational>> = Vec::with_capacity(input.len());
    let mut projection_coefficients = Vec::with_capacity(input.len());

    for (i, v) in input.iter().enumerate() {
        let mut u = v.coordinates().to_vec();
        let mut coeffs_i = Vec::with_capacity(output.len());

        for q in &output {
            let numerator = dot(v.coordinates(), q.coordinates());
            let denominator = dot(q.coordinates(), q.coordinates());

            if denominator.is_zero() {
                return Err(GramSchmidtError::ZeroPivot { index: i });
            }

            let coefficient = numerator / denominator;
            let projection = scalar_mul(&coefficient, q.coordinates());
            u = sub_vec(&u, &projection);
            coeffs_i.push(coefficient);
        }

        if is_zero_vec(&u) {
            return Err(GramSchmidtError::ZeroPivot { index: i });
        }

        output.push(CoordinateVector::new_unchecked(u, basis.clone()));
        projection_coefficients.push(coeffs_i);
    }

    verify_output_family(&output)?;
    verify_span_preservation(&input, &output, &projection_coefficients)?;

    let orthogonality = OrthogonalityWitness::new_unchecked(
        input_family_hash.clone(),
        output.len(),
        basis.clone(),
        provenance.clone(),
    );

    let span_preservation = SpanPreservationWitness::new_unchecked(
        input_family_hash.clone(),
        output.len(),
        basis.clone(),
        provenance.clone(),
    );

    let certificate = GramSchmidtCertificate {
        input_family_hash,
        input_count: input.len(),
        output_count: output.len(),
        basis,
        projection_coefficients,
        orthogonality,
        span_preservation,
        provenance,
    };

    Ok(OrthogonalFamily {
        vectors: output,
        certificate,
    })
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/gram_schmidt.rs
// Claim: urn:core:crates_rs:core-linear-algebra:gram-schmidt:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::basis::{BasisDescriptor, BasisId};
    use crate::proof::{ReplayHash, TheoremProvenance};

    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(BigInt::from(n), BigInt::from(d))
    }

    fn provenance() -> TheoremProvenance {
        TheoremProvenance::DerivedFromFiniteVerification {
            theorem_id: crate::proof::TheoremId::new("test").unwrap(),
            replay: ReplayHash::from_bytes([0; 32]),
        }
    }

    fn family_hash() -> VectorFamilyHash {
        VectorFamilyHash::from_bytes([0; 32])
    }

    fn basis(dim: usize) -> Result<BasisDescriptor, BasisError> {
        Ok(BasisDescriptor::new(
            BasisId::new("standard".to_string())?,
            dim,
        ))
    }

    fn vec2(x: i64, y: i64, basis: BasisDescriptor) -> CoordinateVector<BigRational> {
        CoordinateVector::new_unchecked(vec![q(x, 1), q(y, 1)], basis)
    }

    #[test]
    fn accepts_independent_vectors() -> Result<(), GramSchmidtError> {
        let b = basis(2)?;

        let input = vec![vec2(1, 1, b.clone()), vec2(1, 0, b.clone())];

        let family = gram_schmidt_exact_standard(input, family_hash(), b, provenance())?;

        assert_eq!(family.vectors().len(), 2);

        let u0 = family.vectors()[0].coordinates();
        let u1 = family.vectors()[1].coordinates();

        assert!(dot(u0, u1).is_zero());

        Ok(())
    }

    #[test]
    fn rejects_dependent_vectors() -> Result<(), GramSchmidtError> {
        let b = basis(2)?;

        let input = vec![vec2(1, 1, b.clone()), vec2(2, 2, b.clone())];

        let result = gram_schmidt_exact_standard(input, family_hash(), b, provenance());

        assert!(matches!(
            result,
            Err(GramSchmidtError::ZeroPivot { index: 1 })
        ));
        Ok(())
    }

    #[test]
    fn rejects_empty_input() -> Result<(), GramSchmidtError> {
        let b = basis(2)?;

        let result = gram_schmidt_exact_standard(Vec::new(), family_hash(), b, provenance());

        assert!(matches!(result, Err(GramSchmidtError::EmptyInput)));
        Ok(())
    }

    #[test]
    fn rejects_dimension_mismatch() -> Result<(), GramSchmidtError> {
        let b2 = basis(2)?;
        let b3 = basis(3)?;

        let input = vec![CoordinateVector::new_unchecked(
            vec![q(1, 1), q(2, 1), q(3, 1)],
            b3,
        )];

        let result = gram_schmidt_exact_standard(input, family_hash(), b2, provenance());

        assert!(matches!(
            result,
            Err(GramSchmidtError::BasisMismatch { .. })
                | Err(GramSchmidtError::DimensionMismatch { .. })
        ));
        Ok(())
    }

    #[test]
    fn certificate_records_counts_and_coefficients() -> Result<(), GramSchmidtError> {
        let b = basis(2)?;

        let input = vec![vec2(1, 0, b.clone()), vec2(1, 1, b.clone())];

        let family = gram_schmidt_exact_standard(input, family_hash(), b, provenance())?;

        assert_eq!(family.certificate().input_count(), 2);
        assert_eq!(family.certificate().output_count(), 2);
        assert_eq!(family.certificate().orthogonality().vector_count(), 2);

        let coeffs = family.certificate().projection_coefficients();
        assert_eq!(coeffs.len(), 2);
        assert_eq!(coeffs[0].len(), 0);
        assert_eq!(coeffs[1].len(), 1);
        assert_eq!(coeffs[1][0], q(1, 1));

        Ok(())
    }

    #[test]
    fn verify_span_preservation_succeeds() -> Result<(), GramSchmidtError> {
        let b = basis(2)?;

        let input = vec![vec2(2, 1, b.clone()), vec2(1, 2, b.clone())];

        let family = gram_schmidt_exact_standard(input.clone(), family_hash(), b, provenance())?;
        let output = family.vectors();
        let coeffs = family.certificate().projection_coefficients();

        // The exact Gram-Schmidt loop natively runs verify_span_preservation,
        // so if it succeeded, it is already verified. But we can test it directly:
        assert!(verify_span_preservation(&input, output, coeffs).is_ok());

        Ok(())
    }

    #[test]
    fn rejects_basis_mismatch_specifically() -> Result<(), GramSchmidtError> {
        let b1 = basis(2)?;
        let b2 = BasisDescriptor::new(BasisId::new("different".to_string())?, 2);

        let input = vec![
            vec2(1, 0, b2), // dimension matches, basis ID does not
        ];

        let result = gram_schmidt_exact_standard(input, family_hash(), b1, provenance());

        assert!(matches!(
            result,
            Err(GramSchmidtError::BasisMismatch { index: 0 })
        ));
        Ok(())
    }

    #[test]
    fn verify_output_family_fails_on_zero_vector() -> Result<(), GramSchmidtError> {
        let b = basis(2)?;
        let output = vec![
            vec2(1, 0, b.clone()),
            vec2(0, 0, b.clone()), // corrupted zero vector
        ];

        let result = verify_output_family(&output);
        assert!(matches!(
            result,
            Err(GramSchmidtError::OutputZero { index: 1 })
        ));
        Ok(())
    }

    #[test]
    fn verify_output_family_fails_on_non_orthogonal() -> Result<(), GramSchmidtError> {
        let b = basis(2)?;
        let output = vec![
            vec2(1, 0, b.clone()),
            vec2(1, 1, b.clone()), // corrupted, not orthogonal
        ];

        let result = verify_output_family(&output);
        assert!(matches!(
            result,
            Err(GramSchmidtError::OrthogonalityFailure { left: 0, right: 1 })
        ));
        Ok(())
    }

    #[test]
    fn verify_span_preservation_fails_on_corruption() -> Result<(), GramSchmidtError> {
        let b = basis(2)?;

        let input = vec![vec2(2, 1, b.clone()), vec2(1, 2, b.clone())];

        let family =
            gram_schmidt_exact_standard(input.clone(), family_hash(), b.clone(), provenance())?;
        let mut output = family.vectors().to_vec();
        let coeffs = family.certificate().projection_coefficients();

        // Corrupt the output to break span preservation
        output[1] = vec2(99, 99, b);

        let result = verify_span_preservation(&input, &output, coeffs);
        assert!(matches!(
            result,
            Err(GramSchmidtError::SpanPreservationFailure { index: 1 })
        ));

        Ok(())
    }
}
