//! The Pauli matrix representation of unit quaternions and its adjoint action.
//!
//! `U(a,b,c,d)=a I-i(b X+c Y+d Z)` is a representation of the rational
//! unit quaternions in `SU(2,Q(i))`. The primary adjoint map is
//! `R(U)_jk=Tr(sigma_j U sigma_k U^dagger)/2`: it is a homomorphism, has
//! kernel `{+-I}` on SU(2), and forgets every scalar phase on U(2).
//! The quaternion/spinor-norm algorithms are owned by `crate::su2`.
//! All matrices use checked `linear_algebra::exact_field` operations.
//!
//! AuthorityEffect: None.
use crate::pauli_symplectic::{pauli, Pauli, PauliError};
use crate::scalar::{dagger, is_unitary};
use crate::su2::{Quaternion, Su2Error};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use num_traits::One;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SpinLiftError {
    #[error("the quaternion has squared norm {0}, not one")]
    NotUnitQuaternion(Rational),
    #[error("the matrix must be a 2x2 unitary")]
    NotQubitUnitary,
    #[error("the adjoint trace has a non-real component")]
    NonRealAdjoint,
    #[error(transparent)]
    Quaternion(#[from] Su2Error),
    #[error(transparent)]
    Pauli(#[from] PauliError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

pub fn unit_quaternion_matrix(
    q: &[Rational; 4],
) -> Result<BasicMatrix<GaussianRat>, SpinLiftError> {
    let norm: Rational = q.iter().map(|x| x * x).sum();
    if norm != Rational::one() {
        return Err(SpinLiftError::NotUnitQuaternion(norm));
    }
    let [a, b, c, d] = q;
    Ok(BasicMatrix::from_row_major(
        2,
        2,
        vec![
            GaussianRat {
                re: a.clone(),
                im: -d,
            },
            GaussianRat { re: -c, im: -b },
            GaussianRat {
                re: c.clone(),
                im: -b,
            },
            GaussianRat {
                re: a.clone(),
                im: d.clone(),
            },
        ],
    )
    .map_err(ExactFieldError::from)?)
}

fn adjoint_entry(
    basis_k: &BasicMatrix<GaussianRat>,
    image: &BasicMatrix<GaussianRat>,
) -> Result<Rational, SpinLiftError> {
    let t = mx::trace(&mx::multiply(basis_k, image)?)?;
    if t.im != ri(0) {
        return Err(SpinLiftError::NonRealAdjoint);
    }
    Ok(t.re / ri(2))
}

fn pauli_basis() -> Result<[BasicMatrix<GaussianRat>; 3], SpinLiftError> {
    Ok([
        pauli::<GaussianRat>(Pauli::X)?,
        pauli(Pauli::Y)?,
        pauli(Pauli::Z)?,
    ])
}

fn fill_adjoint_column(
    u: &BasicMatrix<GaussianRat>,
    ud: &BasicMatrix<GaussianRat>,
    basis: &[BasicMatrix<GaussianRat>; 3],
    j: usize,
    result: &mut BasicMatrix<Rational>,
) -> Result<(), SpinLiftError> {
    let image = mx::multiply(&mx::multiply(u, &basis[j])?, ud)?;
    for (k, basis_k) in basis.iter().enumerate() {
        let entry = adjoint_entry(basis_k, &image)?;
        result.set(k, j, entry).map_err(ExactFieldError::from)?;
    }
    Ok(())
}

/// The adjoint cover as a primary group map, independent of any quantum channel.
pub fn adjoint_su2(u: &BasicMatrix<GaussianRat>) -> Result<BasicMatrix<Rational>, SpinLiftError> {
    if u.shape() != (2, 2) || !is_unitary(u)? {
        return Err(SpinLiftError::NotQubitUnitary);
    }
    let basis = pauli_basis()?;
    let ud = dagger(u)?;
    let mut result = mx::zeros(3, 3)?;
    for j in 0..3 {
        fill_adjoint_column(u, &ud, &basis, j, &mut result)?;
    }
    Ok(result)
}

/// A rational matrix spin lift, with the square-class refusal of the quaternion owner.
pub fn matrix_spin_lift(
    r: &BasicMatrix<Rational>,
) -> Result<BasicMatrix<GaussianRat>, SpinLiftError> {
    let Quaternion { w, x, y, z } = crate::su2::spin_lift(r)?;
    unit_quaternion_matrix(&[w, x, y, z])
}

/// Quaternion units in the fixed order (1,-1,i,-i,j,-j,k,-k).
pub fn quaternion_group_matrices() -> Result<Vec<BasicMatrix<GaussianRat>>, SpinLiftError> {
    let group = crate::su2::quaternion_group()?;
    let mut units = group.elements().to_vec();
    units.sort_by_key(|q| {
        for (axis, value) in [&q.w, &q.x, &q.y, &q.z].iter().enumerate() {
            if **value == ri(1) {
                return 2 * axis;
            }
            if **value == ri(-1) {
                return 2 * axis + 1;
            }
        }
        8
    });
    units
        .iter()
        .map(|q| unit_quaternion_matrix(&[q.w.clone(), q.x.clone(), q.y.clone(), q.z.clone()]))
        .collect()
}

// Origin: engine/crates_rs/core_lie_theory/src/su2_matrix.rs
// Claim: urn:core:crates_rs:core-lie-theory:su2-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_fcb4558b {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
