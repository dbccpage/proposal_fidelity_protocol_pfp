//! Exact tests for the dynamics movement of the finite quantum mechanics
//! programme: weighted transport and graded path-sums, time-sliced action
//! shadows, finite-step Schrödinger transport, unitary steps and the admission
//! of their generators. One submodule per retired source paper; the
//! paper-to-module map lives in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

mod feynman_finite_shadow_histories;
mod finite_path_sum_graded_transport;
mod hamiltonian_generator_admission;
mod schrodinger_finite_shadow;
mod unitary_finite_shadow;
mod weighted_transport_calculus;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as iv, matrix as mx};
use linear_algebra::semiring_matrix::{self as sm, boolean_square_roots, Boolean};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::finite_schrodinger_step::euler_propagator;

/// Counts stated by `unitary_finite_shadow`: Boolean square roots of the identity,
/// none for the swap, and the Gaussian half-steps whose number is the Euler norm factor.
#[derive(Debug, Clone, PartialEq, Eq)]
struct DynamicsCensus {
    dimension: u64,
    boolean_identity_roots: u64,
    boolean_swap_roots: u64,
    gaussian_half_steps: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum DynamicsCensusError {
    Boolean,
    Field,
    Schrodinger,
    Overflow,
    Dimension,
    BooleanIdentityRoots,
    BooleanSwapRoots,
    HalfStep,
    NotUnitary,
    DuplicateHalfStep,
    NormDrift,
    EulerScale,
}

// Origin: engine/crates_rs/tests/core_quantum_physics/dynamics/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DynamicsCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DynamicsCensusError {}

impl DynamicsCensus {
    fn check_identity_roots(
        dimension: u64,
        identity: &BasicMatrix<Boolean>,
        swap_b: &BasicMatrix<Boolean>,
        identity_roots: &[BasicMatrix<Boolean>],
    ) -> Result<u64, DynamicsCensusError> {
        let count =
            u64::try_from(identity_roots.len()).map_err(|_| DynamicsCensusError::Overflow)?;
        let valid = count == dimension
            && identity_roots.contains(swap_b)
            && identity_roots.contains(identity);
        if !valid {
            return Err(DynamicsCensusError::BooleanIdentityRoots);
        }
        Ok(count)
    }

    fn certify_boolean_roots(
        dimension: u64,
        rows: usize,
    ) -> Result<(u64, u64), DynamicsCensusError> {
        let identity = boolean(sm::identity::<Boolean>(rows))?;
        let swap_b = boolean(sm::from_rows(vec![
            vec![Boolean(false), Boolean(true)],
            vec![Boolean(true), Boolean(false)],
        ]))?;
        let identity_roots = boolean(boolean_square_roots(&identity))?;
        let boolean_identity_roots =
            Self::check_identity_roots(dimension, &identity, &swap_b, &identity_roots)?;
        let swap_roots = boolean(boolean_square_roots(&swap_b))?;
        let boolean_swap_roots =
            u64::try_from(swap_roots.len()).map_err(|_| DynamicsCensusError::Overflow)?;
        if boolean_swap_roots != 0 {
            return Err(DynamicsCensusError::BooleanSwapRoots);
        }
        Ok((boolean_identity_roots, boolean_swap_roots))
    }

    fn verify_single_half_step(
        index: usize,
        root: &BasicMatrix<GaussianRat>,
        swap_g: &BasicMatrix<GaussianRat>,
        half_steps: &[BasicMatrix<GaussianRat>],
    ) -> Result<(), DynamicsCensusError> {
        if field(mx::multiply(root, root))? != *swap_g {
            return Err(DynamicsCensusError::HalfStep);
        }
        if !field(iv::is_unitary(root))? {
            return Err(DynamicsCensusError::NotUnitary);
        }
        if half_steps.iter().skip(index + 1).any(|other| other == root) {
            return Err(DynamicsCensusError::DuplicateHalfStep);
        }
        Ok(())
    }

    fn certify_gaussian_half_steps(
        swap_g: &BasicMatrix<GaussianRat>,
        expected: u64,
    ) -> Result<u64, DynamicsCensusError> {
        let mut half_steps = Vec::new();
        for mu in [gi(0, 1), gi(0, -1)] {
            for sign in [1i64, -1] {
                let rooted = field(swap_root(&mu))?;
                half_steps.push(field(mx::scale(&rooted, &gi(sign, 0)))?);
            }
        }
        for (index, root) in half_steps.iter().enumerate() {
            Self::verify_single_half_step(index, root, swap_g, &half_steps)?;
        }
        let count = u64::try_from(half_steps.len()).map_err(|_| DynamicsCensusError::Overflow)?;
        if count != expected {
            return Err(DynamicsCensusError::HalfStep);
        }
        Ok(count)
    }

    fn certify_euler_scale(
        psi: &[GaussianRat],
        gaussian_half_steps: u64,
    ) -> Result<(), DynamicsCensusError> {
        let generator = field(mx::from_rows(vec![
            vec![gi(1, 0), gi(1, 1)],
            vec![gi(1, -1), gi(-1, 0)],
        ]))?;
        let euler =
            euler_propagator(&generator, &ri(1)).map_err(|_| DynamicsCensusError::Schrodinger)?;
        let blown = field(mx::multiply_vector(&euler, psi))?;
        let factor =
            i64::try_from(gaussian_half_steps).map_err(|_| DynamicsCensusError::Overflow)?;
        if norm_sq(&blown) != ri(factor) * norm_sq(psi) {
            return Err(DynamicsCensusError::EulerScale);
        }
        Ok(())
    }

    fn certify() -> Result<Self, DynamicsCensusError> {
        let swap_g = field(mx::from_rows(vec![
            vec![gi(0, 0), gi(1, 0)],
            vec![gi(1, 0), gi(0, 0)],
        ]))?;
        if swap_g.rows() != swap_g.cols() {
            return Err(DynamicsCensusError::Dimension);
        }
        let dimension = u64::try_from(swap_g.rows()).map_err(|_| DynamicsCensusError::Overflow)?;
        let (boolean_identity_roots, boolean_swap_roots) =
            Self::certify_boolean_roots(dimension, swap_g.rows())?;
        let psi = vec![gi(1, 0), gi(0, 0)];
        let image = field(mx::multiply_vector(&swap_g, &psi))?;
        if norm_sq(&image) != norm_sq(&psi) {
            return Err(DynamicsCensusError::NormDrift);
        }
        let expected = boolean_identity_roots
            .checked_mul(dimension)
            .ok_or(DynamicsCensusError::Overflow)?;
        let gaussian_half_steps = Self::certify_gaussian_half_steps(&swap_g, expected)?;
        Self::certify_euler_scale(&psi, gaussian_half_steps)?;
        Ok(Self {
            dimension,
            boolean_identity_roots,
            boolean_swap_roots,
            gaussian_half_steps,
        })
    }
}

fn field<T>(
    value: Result<T, linear_algebra::exact_field::ExactFieldError>,
) -> Result<T, DynamicsCensusError> {
    value.map_err(|_| DynamicsCensusError::Field)
}

fn boolean<T>(
    value: Result<T, linear_algebra::backend::basic_matrix::MatrixError>,
) -> Result<T, DynamicsCensusError> {
    value.map_err(|_| DynamicsCensusError::Boolean)
}

fn swap_root(
    mu: &GaussianRat,
) -> Result<BasicMatrix<GaussianRat>, linear_algebra::exact_field::ExactFieldError> {
    let half = gq(1, 2, 0, 1);
    let p = gi(1, 0).add(mu).mul(&half);
    let q = gi(1, 0).sub(mu).mul(&half);
    mx::from_rows(vec![vec![p.clone(), q.clone()], vec![q, p]])
}

fn norm_sq(psi: &[GaussianRat]) -> Rational {
    psi.iter().map(GaussianRat::norm_sq).sum()
}

#[test]
fn unitary_shadow_half_steps_match_the_euler_factor() {
    assert!(matches!(
        DynamicsCensus::certify(),
        Ok(witness)
            if witness.boolean_swap_roots == 0
                && witness.boolean_identity_roots == witness.dimension
                && witness.boolean_identity_roots.checked_mul(witness.dimension)
                    == Some(witness.gaussian_half_steps)
                && witness.dimension == 2
                && witness.gaussian_half_steps == 4
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
