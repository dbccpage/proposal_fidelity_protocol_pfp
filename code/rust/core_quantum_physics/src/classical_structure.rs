//! Orthonormal pointer bases as special commutative dagger-Frobenius algebras.
//! Copyability is computed from the coalgebra, including its counit.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::{
    exact_hermitian::gi,
    frobenius_algebra::{FrobeniusAlgebra, FrobeniusError},
};
use linear_algebra::exact_field::{involution, matrix};
use core_number_theory::{cyclotomic::GaussianRat, rational::Rational};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact orthonormal classical structures.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ClassicalError {
    #[error(transparent)]
    ExactAlgebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("family is not a complete orthonormal basis over Q(i)")]
    NotOrthonormal,
    #[error(transparent)]
    Frobenius(#[from] FrobeniusError),
    #[error("vector does not belong to the declared carrier")]
    Shape,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClassicalStructure {
    basis: Vec<Vec<GaussianRat>>,
    algebra: FrobeniusAlgebra,
}
impl ClassicalStructure {
    pub fn from_basis(basis: Vec<Vec<GaussianRat>>) -> Result<Self, ClassicalError> {
        Self::validate_orthonormal_basis(&basis)?;
        let (delta, eps) = Self::build_comultiplication_and_counit(&basis)?;
        let algebra = FrobeniusAlgebra::try_new(
            involution::adjoint(&delta)?,
            involution::adjoint(&eps)?,
            delta,
            eps,
        )?;
        if [
            algebra.special_scalar() != Some(gi(1, 0)),
            !algebra.is_commutative(),
            !algebra.is_dagger(),
        ]
        .into_iter()
        .any(|b| b)
        {
            return Err(ClassicalError::NotOrthonormal);
        }
        Ok(Self { basis, algebra })
    }

    fn validate_orthonormal_basis(basis: &[Vec<GaussianRat>]) -> Result<(), ClassicalError> {
        let d = basis.len();
        if !(1..=16).contains(&d) || basis.iter().any(|v| v.len() != d) {
            return Err(ClassicalError::NotOrthonormal);
        }
        for i in 0..d {
            for j in 0..d {
                let prod = involution::inner_product(&basis[i], &basis[j])
                    .map_err(|_| ClassicalError::NotOrthonormal)?;
                if prod != gi(i64::from(i == j), 0) {
                    return Err(ClassicalError::NotOrthonormal);
                }
            }
        }
        Ok(())
    }

    fn build_comultiplication_and_counit(
        basis: &[Vec<GaussianRat>],
    ) -> Result<
        (
            linear_algebra::backend::basic_matrix::BasicMatrix<GaussianRat>,
            linear_algebra::backend::basic_matrix::BasicMatrix<GaussianRat>,
        ),
        ClassicalError,
    > {
        let d = basis.len();
        let mut delta =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(d * d, d, |_, _| {
                gi(0, 0)
            })?;
        let mut eps =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(1, d, |_, _| gi(0, 0))?;
        for b in basis {
            Self::accumulate_basis_vector(&mut delta, &mut eps, b, d)?;
        }
        Ok((delta, eps))
    }

    fn accumulate_basis_vector(
        delta: &mut linear_algebra::backend::basic_matrix::BasicMatrix<GaussianRat>,
        eps: &mut linear_algebra::backend::basic_matrix::BasicMatrix<GaussianRat>,
        b: &[GaussianRat],
        d: usize,
    ) -> Result<(), ClassicalError> {
        for k in 0..d {
            eps.set(0, k, eps.get_ref(0, k)? + &b[k].conj())?;
            for i in 0..d {
                for j in 0..d {
                    let entry = delta.get_ref(i * d + j, k)? + &(&b[i] * &b[j] * b[k].conj());
                    delta.set(i * d + j, k, entry)?;
                }
            }
        }
        Ok(())
    }
    pub fn standard(d: usize) -> Result<Self, ClassicalError> {
        if !(1..=16).contains(&d) {
            return Err(ClassicalError::Shape);
        }
        Self::from_basis(
            (0..d)
                .map(|i| (0..d).map(|j| gi(i64::from(i == j), 0)).collect())
                .collect(),
        )
    }
    pub fn basis(&self) -> &[Vec<GaussianRat>] {
        &self.basis
    }
    pub fn algebra(&self) -> &FrobeniusAlgebra {
        &self.algebra
    }
    /// Normalized copyable points are precisely the basis vectors. Zero obeys
    /// Delta(0)=0 tensor 0 but fails eps(0)=1, hence is not a coalgebra point.
    pub fn is_copyable_point(&self, vector: &[GaussianRat]) -> Result<bool, ClassicalError> {
        if vector.len() != self.basis.len() {
            return Err(ClassicalError::Shape);
        }
        let copied = matrix::multiply_vector(self.algebra.comultiplication(), vector)
            .map_err(|_| ClassicalError::Shape)?;
        let product: Vec<GaussianRat> = vector
            .iter()
            .flat_map(|a| vector.iter().map(move |b| a * b))
            .collect();
        let counit = matrix::multiply_vector(self.algebra.counit(), vector)
            .map_err(|_| ClassicalError::Shape)?;
        Ok(copied == product && counit == vec![gi(1, 0)])
    }
    pub fn complementary(&self, other: &Self) -> Result<bool, ClassicalError> {
        let d = self.basis.len();
        if other.basis.len() != d {
            return Err(ClassicalError::Shape);
        }
        let target = Rational::new(1.into(), d.into());
        for a in &self.basis {
            for b in &other.basis {
                let overlap = involution::inner_product(a, b).map_err(|_| ClassicalError::Shape)?;
                if &overlap.re * &overlap.re + &overlap.im * &overlap.im != target {
                    return Ok(false);
                }
            }
        }
        Ok(true)
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/classical_structure.rs
// Claim: urn:core:crates_rs:core-quantum-physics:classical-structure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::exact_hermitian::gq;
    use num_traits::Zero;
    #[test]
    fn rational_rotated_basis_is_a_classical_structure_with_only_basis_points_copyable() {
        let basis = vec![
            vec![gq(3, 5, 0, 1), gq(4, 5, 0, 1)],
            vec![gq(-4, 5, 0, 1), gq(3, 5, 0, 1)],
        ];
        let c = ClassicalStructure::from_basis(basis).unwrap();
        assert!(c.algebra().first_defect().unwrap().is_none());
        for b in c.basis() {
            assert!(c.is_copyable_point(b).unwrap());
        }
        assert!(!c.is_copyable_point(&[gi(0, 0), gi(0, 0)]).unwrap());
        assert!(!c.is_copyable_point(&[gi(1, 0), gi(0, 0)]).unwrap());
        assert!(ClassicalStructure::from_basis(vec![vec![gi(1, 0), gi(0, 0)]; 2]).is_err());
    }
    #[test]
    fn complex_rational_unbiased_basis_is_complementary() {
        let z = ClassicalStructure::standard(2).unwrap();
        let a = gq(1, 2, 1, 2);
        let b = gq(1, 2, -1, 2);
        let x =
            ClassicalStructure::from_basis(vec![vec![a.clone(), b.clone()], vec![a, -b]]).unwrap();
        assert!(z.complementary(&x).unwrap());
        assert!(!z.complementary(&z).unwrap());
        assert!(!x.basis().iter().flatten().all(|v| v.im.is_zero()));
    }
}
