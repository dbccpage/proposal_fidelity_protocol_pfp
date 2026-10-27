//! Exact finite Frobenius algebras with both Frobenius identities replayed.
//! Specialness, commutativity and dagger compatibility are computed separately.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_adace75c<T> {
    fn checked_invariant_adace75c(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_adace75c<T> for Option<T> {
    #[inline]
    fn checked_invariant_adace75c(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_adace75c<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_adace75c(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::{
    dagger_category::{DaggerCategory, DaggerError},
    exact_hermitian::gi,
};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::elimination;
use linear_algebra::exact_field::{involution, matrix};
use core_number_theory::cyclotomic::GaussianRat;
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact finite Frobenius equations.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FrobeniusError {
    #[error(transparent)]
    ExactAlgebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error(transparent)]
    Dagger(#[from] DaggerError),
    #[error("Frobenius maps have incompatible dimensions, or dimension exceeds 16")]
    Shape,
    #[error("the trace form is degenerate")]
    DegenerateForm,
    #[error("Frobenius law fails: {0:?}")]
    Law(FrobeniusDefect),
    #[error("matrix operation refused: {0}")]
    Matrix(String),
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FrobeniusDefect {
    Associativity,
    Coassociativity,
    LeftUnit,
    RightUnit,
    LeftCounit,
    RightCounit,
    LeftFrobenius,
    RightFrobenius,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FrobeniusAlgebra {
    dimension: usize,
    mu: BasicMatrix<GaussianRat>,
    eta: BasicMatrix<GaussianRat>,
    delta: BasicMatrix<GaussianRat>,
    eps: BasicMatrix<GaussianRat>,
}
impl FrobeniusAlgebra {
    pub fn try_new(
        mu: BasicMatrix<GaussianRat>,
        eta: BasicMatrix<GaussianRat>,
        delta: BasicMatrix<GaussianRat>,
        eps: BasicMatrix<GaussianRat>,
    ) -> Result<Self, FrobeniusError> {
        let d = mu.rows();
        if !(1..=16).contains(&d)
            || mu.cols() != d * d
            || (eta.rows(), eta.cols()) != (d, 1)
            || (delta.rows(), delta.cols()) != (d * d, d)
            || (eps.rows(), eps.cols()) != (1, d)
        {
            return Err(FrobeniusError::Shape);
        }
        let algebra = Self {
            dimension: d,
            mu,
            eta,
            delta,
            eps,
        };
        if let Some(defect) = algebra.first_defect()? {
            return Err(FrobeniusError::Law(defect));
        }
        Ok(algebra)
    }
    pub fn dimension(&self) -> usize {
        self.dimension
    }
    pub fn multiplication(&self) -> &BasicMatrix<GaussianRat> {
        &self.mu
    }
    pub fn unit(&self) -> &BasicMatrix<GaussianRat> {
        &self.eta
    }
    pub fn comultiplication(&self) -> &BasicMatrix<GaussianRat> {
        &self.delta
    }
    pub fn counit(&self) -> &BasicMatrix<GaussianRat> {
        &self.eps
    }
    fn tensor_mul(
        left_op: &BasicMatrix<GaussianRat>,
        t_left: &BasicMatrix<GaussianRat>,
        t_right: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, FrobeniusError> {
        let t = DaggerCategory::tensor(t_left, t_right)?;
        Ok(matrix::multiply(left_op, &t)?)
    }

    fn mul_tensor(
        t_left: &BasicMatrix<GaussianRat>,
        t_right: &BasicMatrix<GaussianRat>,
        right_op: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, FrobeniusError> {
        let t = DaggerCategory::tensor(t_left, t_right)?;
        Ok(matrix::multiply(&t, right_op)?)
    }

    fn check_associative_laws(
        &self,
        id: &BasicMatrix<GaussianRat>,
    ) -> Result<Option<FrobeniusDefect>, FrobeniusError> {
        if Self::tensor_mul(&self.mu, &self.mu, id)? != Self::tensor_mul(&self.mu, id, &self.mu)? {
            return Ok(Some(FrobeniusDefect::Associativity));
        }
        if Self::mul_tensor(&self.delta, id, &self.delta)?
            != Self::mul_tensor(id, &self.delta, &self.delta)?
        {
            return Ok(Some(FrobeniusDefect::Coassociativity));
        }
        Ok(None)
    }

    fn check_unit_laws(
        &self,
        id: &BasicMatrix<GaussianRat>,
    ) -> Result<Option<FrobeniusDefect>, FrobeniusError> {
        if Self::tensor_mul(&self.mu, &self.eta, id)? != *id {
            return Ok(Some(FrobeniusDefect::LeftUnit));
        }
        if Self::tensor_mul(&self.mu, id, &self.eta)? != *id {
            return Ok(Some(FrobeniusDefect::RightUnit));
        }
        if Self::mul_tensor(&self.eps, id, &self.delta)? != *id {
            return Ok(Some(FrobeniusDefect::LeftCounit));
        }
        if Self::mul_tensor(id, &self.eps, &self.delta)? != *id {
            return Ok(Some(FrobeniusDefect::RightCounit));
        }
        Ok(None)
    }

    fn check_frobenius_laws(
        &self,
        id: &BasicMatrix<GaussianRat>,
    ) -> Result<Option<FrobeniusDefect>, FrobeniusError> {
        let tensor = DaggerCategory::tensor;
        let composite = matrix::multiply(&self.delta, &self.mu)?;
        if matrix::multiply(&tensor(&self.mu, id)?, &tensor(id, &self.delta)?)? != composite {
            return Ok(Some(FrobeniusDefect::LeftFrobenius));
        }
        if matrix::multiply(&tensor(id, &self.mu)?, &tensor(&self.delta, id)?)? != composite {
            return Ok(Some(FrobeniusDefect::RightFrobenius));
        }
        Ok(None)
    }

    pub fn first_defect(&self) -> Result<Option<FrobeniusDefect>, FrobeniusError> {
        let id = matrix::identity(self.dimension)?;
        if let Some(defect) = self.check_associative_laws(&id)? {
            return Ok(Some(defect));
        }
        if let Some(defect) = self.check_unit_laws(&id)? {
            return Ok(Some(defect));
        }
        self.check_frobenius_laws(&id)
    }
    pub fn special_scalar(&self) -> Option<GaussianRat> {
        let composite = matrix::multiply(&self.mu, &self.delta).ok()?;
        let scalar = composite.get_ref(0, 0).ok()?.clone();
        (composite == matrix::scale(&matrix::identity(self.dimension).ok()?, &scalar).ok()?)
            .then_some(scalar)
    }
    pub fn is_dagger(&self) -> bool {
        involution::adjoint(&self.mu) == Ok(self.delta.clone())
            && involution::adjoint(&self.eta) == Ok(self.eps.clone())
    }
    pub fn is_commutative(&self) -> bool {
        (0..self.dimension).all(|i| {
            (0..self.dimension).all(|j| {
                (0..self.dimension).all(|k| {
                    self.mu
                        .get_ref(k, i * self.dimension + j)
                        .checked_invariant_adace75c("validated multiplication shape")
                        == self
                            .mu
                            .get_ref(k, j * self.dimension + i)
                            .checked_invariant_adace75c("validated multiplication shape")
                })
            })
        })
    }
    pub fn copy(d: usize) -> Result<Self, FrobeniusError> {
        if !(1..=16).contains(&d) {
            return Err(FrobeniusError::Shape);
        }
        let mut mu =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(d, d * d, |_, _| {
                gi(0, 0)
            })?;
        let mut eta =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(d, 1, |_, _| gi(1, 0))?;
        for i in 0..d {
            mu.set(i, i * d + i, gi(1, 0))?;
            eta.set(i, 0, gi(1, 0))?;
        }
        Self::try_new(
            mu.clone(),
            eta.clone(),
            involution::adjoint(&mu)?,
            involution::adjoint(&eta)?,
        )
    }
    fn populate_matrix_algebra(
        n: usize,
        d: usize,
        mu: &mut BasicMatrix<GaussianRat>,
        eta: &mut BasicMatrix<GaussianRat>,
    ) -> Result<(), FrobeniusError> {
        for i in 0..n {
            eta.set(i * n + i, 0, gi(1, 0))?;
            for j in 0..n {
                for k in 0..n {
                    mu.set(i * n + k, (i * n + j) * d + j * n + k, gi(1, 0))?;
                }
            }
        }
        Ok(())
    }
    pub fn matrix_algebra(n: usize) -> Result<Self, FrobeniusError> {
        if n == 0 || n > 4 {
            return Err(FrobeniusError::Shape);
        }
        let d = n * n;
        let mut mu =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(d, d * d, |_, _| {
                gi(0, 0)
            })?;
        let mut eta =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(d, 1, |_, _| gi(0, 0))?;
        Self::populate_matrix_algebra(n, d, &mut mu, &mut eta)?;
        Self::try_new(
            mu.clone(),
            eta.clone(),
            involution::adjoint(&mu)?,
            involution::adjoint(&eta)?,
        )
    }
    pub fn group_algebra_cyclic(n: usize) -> Result<Self, FrobeniusError> {
        if !(1..=16).contains(&n) {
            return Err(FrobeniusError::Shape);
        }
        let mut mu =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(n, n * n, |_, _| {
                gi(0, 0)
            })?;
        let mut eta =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(n, 1, |_, _| gi(0, 0))?;
        eta.set(0, 0, gi(1, 0))?;
        for i in 0..n {
            for j in 0..n {
                mu.set((i + j) % n, i * n + j, gi(1, 0))?;
            }
        }
        Self::try_new(
            mu.clone(),
            eta.clone(),
            involution::adjoint(&mu)?,
            involution::adjoint(&eta)?,
        )
    }
    fn compute_coproduct_entry(
        d: usize,
        i: usize,
        k: usize,
        a: usize,
        inverse: &BasicMatrix<GaussianRat>,
        mu: &BasicMatrix<GaussianRat>,
    ) -> Result<GaussianRat, FrobeniusError> {
        let mut entry = gi(0, 0);
        for j in 0..d {
            let inv_ij = inverse
                .get_ref(i, j)
                .map_err(|e| FrobeniusError::Matrix(e.to_string()))?;
            entry = entry + inv_ij * mu.get_ref(k, j * d + a)?;
        }
        Ok(entry)
    }
    fn build_trace_form_coproduct(
        d: usize,
        inverse: &BasicMatrix<GaussianRat>,
        mu: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, FrobeniusError> {
        let mut delta =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(d * d, d, |_, _| {
                gi(0, 0)
            })?;
        for i in 0..d {
            for k in 0..d {
                for a in 0..d {
                    let entry = Self::compute_coproduct_entry(d, i, k, a, inverse, mu)?;
                    delta.set(i * d + k, a, entry)?;
                }
            }
        }
        Ok(delta)
    }
    /// Build the dual-basis coproduct from the exact inverse of eps(mu(-,-)).
    pub fn from_trace_form(
        mu: BasicMatrix<GaussianRat>,
        eta: BasicMatrix<GaussianRat>,
        eps: BasicMatrix<GaussianRat>,
    ) -> Result<Self, FrobeniusError> {
        let d = mu.rows();
        let bad_shape = mu.cols() != d * d
            || (eta.rows(), eta.cols()) != (d, 1)
            || (eps.rows(), eps.cols()) != (1, d);
        if !(1..=16).contains(&d) || bad_shape {
            return Err(FrobeniusError::Shape);
        }
        let pairing = matrix::multiply(&eps, &mu)?;
        let gram = linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(
            d,
            d,
            pairing.as_slice().to_vec(),
        )?;
        let inverse = elimination::inverse(&gram).map_err(|_| FrobeniusError::DegenerateForm)?;
        let delta = Self::build_trace_form_coproduct(d, &inverse, &mu)?;
        Self::try_new(mu, eta, delta, eps)
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/frobenius_algebra.rs
// Claim: urn:core:crates_rs:core-quantum-physics:frobenius-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn copy_structure_is_special_commutative_dagger_frobenius() {
        for d in [2, 3] {
            let a = FrobeniusAlgebra::copy(d).unwrap();
            assert_eq!(a.first_defect().unwrap(), None);
            assert!(a.is_dagger());
            assert!(a.is_commutative());
            assert_eq!(a.special_scalar(), Some(gi(1, 0)));
        }
    }
    #[test]
    fn matrix_and_cyclic_group_algebras_have_computed_special_scalars() {
        let matrix = FrobeniusAlgebra::matrix_algebra(2).unwrap();
        assert!(!matrix.is_commutative());
        assert_eq!(matrix.special_scalar(), Some(gi(2, 0)));
        let reconstructed = FrobeniusAlgebra::from_trace_form(
            matrix.mu.clone(),
            matrix.eta.clone(),
            matrix.eps.clone(),
        )
        .unwrap();
        assert_eq!(reconstructed, matrix);
        let group = FrobeniusAlgebra::group_algebra_cyclic(3).unwrap();
        assert!(group.is_commutative());
        assert_eq!(group.special_scalar(), Some(gi(3, 0)));
        assert!(matches!(
            FrobeniusAlgebra::from_trace_form(
                group.mu,
                group.eta,
                linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(1, 3, |_, _| gi(
                    0, 0
                ))
                .unwrap()
            ),
            Err(FrobeniusError::DegenerateForm)
        ));
    }
}
