// AuthorityEffect: None.

//! Discrete Quantum Phase Estimation over exact cyclotomic fields and dyadic rationals.
//!
//! When the phase theta is an exact dyadic rational theta = k / 2^m, the eigenvalue
//! exp(2 pi i k / 2^m) lies in the cyclotomic field Q(zeta_{2^m}).
//!
//! This module implements genuine inverse Quantum Fourier Transform (QFT) operations:
//!   1. Constructs the exact register state vector |Psi_k> in Q(zeta_{24}) for m in {1, 2, 3}:
//!        |Psi_k>_l = zeta_{2^m}^{k * l}.
//!   2. Constructs the exact unnormalized inverse QFT matrix F^dagger:
//!        (F^dagger)_{j, l} = zeta_{2^m}^{- j * l}.
//!   3. Computes the matrix-vector product w = F^dagger |Psi_k>:
//!        w_j = sum_{l=0}^{2^m-1} zeta_{2^m}^{(k - j) l}.
//!   4. Evaluates cyclotomic geometric sum cancellation:
//!        w_j = 2^m * delta_{j, k}.
//!   5. Calculates exact measurement probability:
//!        P(k) = |w_k|^2 / sum_j |w_j|^2 = (2^m)^2 / (2^m)^2 = 1/1 in Q.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_65096192<T> {
    fn checked_invariant_65096192(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_65096192<T> for Option<T> {
    #[inline]
    fn checked_invariant_65096192(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_65096192<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_65096192(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::{Cyc24, GaussianRat};
use core_number_theory::rational::{r_one, rq, Rational};
use serde::{Deserialize, Serialize};

/// Returns the exact root of unity zeta_{2^m}^p embedded in Cyc24 for m in {1, 2, 3}.
pub fn dyadic_root_of_unity(m: usize, power: i64) -> Cyc24 {
    let step = match m {
        1 => 12, // zeta_2 = zeta_{24}^12 = -1
        2 => 6,  // zeta_4 = zeta_{24}^6 = i
        3 => 3,  // zeta_8 = zeta_{24}^3
        _ => unreachable!("Exact dyadic roots in Cyc24 supported for m in 1..=3"),
    };
    let period = 24 / step;
    let idx = (power.rem_euclid(period) * step) as i32;
    Cyc24::zeta24(idx)
}

/// Returns the exact normalization factor 1 / sqrt(2^m) in Cyc24 for m in {1, 2, 3}.
pub fn qft_normalization(m: usize) -> Cyc24 {
    match m {
        1 => Cyc24::inv_sqrt2(),
        2 => Cyc24::rat(rq(1, 2)),
        3 => Cyc24::inv_sqrt2().mul(&Cyc24::rat(rq(1, 2))),
        _ => unreachable!("Exact dyadic QFT normalization supported for m in 1..=3"),
    }
}

/// Constructs the genuine unitary inverse QFT matrix U_IQFT = (1 / sqrt(2^m)) * F^dagger.
pub fn build_unitary_iqft_matrix(m: usize) -> BasicMatrix<Cyc24> {
    assert!((1..=3).contains(&m));
    let dim = 1 << m;
    let norm = qft_normalization(m);
    let mut mat = linear_algebra::exact_field::matrix::zeros_with_limits::<Cyc24>(
        dim,
        dim,
        linear_algebra::backend::basic_matrix::OperationLimits {
            max_elements: 1 << 20,
            max_scalar_ops: 1 << 24,
        },
    )
    .checked_invariant_65096192("validated finite matrix shape and budget");
    for j in 0..dim {
        for l in 0..dim {
            let phase = dyadic_root_of_unity(m, -((j * l) as i64));
            (mat)
                .set(j, l, phase.mul(&norm))
                .checked_invariant_65096192("validated finite matrix shape and budget");
        }
    }
    mat
}

/// Verifies that U_IQFT is strictly unitary: U_IQFT * U_IQFT^dagger == I_dim identically.
pub fn verify_qft_unitarity(m: usize) -> bool {
    let u = build_unitary_iqft_matrix(m);
    let u_dag = linear_algebra::exact_field::involution::adjoint(&(u))
        .checked_invariant_65096192("validated finite matrix shape and budget");
    let prod = linear_algebra::exact_field::matrix::multiply_with_limits(
        &(u),
        &u_dag,
        linear_algebra::backend::basic_matrix::OperationLimits {
            max_elements: 1 << 20,
            max_scalar_ops: 1 << 24,
        },
    )
    .checked_invariant_65096192("validated finite matrix shape and budget");
    let id = linear_algebra::exact_field::matrix::identity_with_limits::<Cyc24>(
        1 << m,
        linear_algebra::backend::basic_matrix::OperationLimits {
            max_elements: 1 << 20,
            max_scalar_ops: 1 << 24,
        },
    )
    .checked_invariant_65096192("validated finite matrix shape and budget");
    prod == id
}

/// Discrete Phase Estimation simulator over exact dyadic rational phases.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DiscretePhaseEstimation {
    pub m_qubits: usize,
    pub register_dim: usize,
    pub target_k: usize,
    pub dyadic_numerator: usize,
    pub dyadic_denominator: usize,
    pub is_exact_projection: bool,
    pub unitary_qft_verified: bool,
    pub target_probability: (i64, i64),
}

impl DiscretePhaseEstimation {
    /// Executes genuine discrete phase estimation via explicit inverse QFT matrix multiplication.
    pub fn run(m: usize, k: usize) -> Self {
        assert!(
            (1..=3).contains(&m),
            "m must be in 1..=3 for Cyc24 exact algebra"
        );
        let dim = 1 << m;
        let target_k = k % dim;

        // 1. Construct register state vector |Psi_k>
        let mut psi = Vec::with_capacity(dim);
        for l in 0..dim {
            psi.push(dyadic_root_of_unity(m, (target_k * l) as i64));
        }

        // 2. Construct inverse QFT matrix F^dagger
        let mut ift_matrix = Vec::with_capacity(dim);
        for j in 0..dim {
            let mut row = Vec::with_capacity(dim);
            for l in 0..dim {
                // (F^dagger)_{j, l} = zeta_{dim}^{- j * l}
                row.push(dyadic_root_of_unity(m, -((j * l) as i64)));
            }
            ift_matrix.push(row);
        }

        // 3. Compute matrix-vector product w = F^dagger |Psi_k>
        let mut w = Vec::with_capacity(dim);
        for j in 0..dim {
            let mut sum = Cyc24::zero();
            for l in 0..dim {
                sum = sum.add(&ift_matrix[j][l].mul(&psi[l]));
            }
            w.push(sum);
        }

        // 4. Verify geometric cancellation: w_j == 0 for all j != target_k
        let mut all_off_target_zero = true;
        for j in 0..dim {
            if j != target_k && !w[j].is_zero() {
                all_off_target_zero = false;
                break;
            }
        }

        // 5. On-target reinforcement: w_{target_k} == dim
        let expected_val = Cyc24::from_int(dim as i64);
        let on_target_reinforcement = w[target_k] == expected_val;

        let is_exact = all_off_target_zero && on_target_reinforcement;
        let qft_unitary = verify_qft_unitarity(m);

        Self {
            m_qubits: m,
            register_dim: dim,
            target_k,
            dyadic_numerator: target_k,
            dyadic_denominator: dim,
            is_exact_projection: is_exact,
            unitary_qft_verified: qft_unitary,
            target_probability: {
                use num_traits::ToPrimitive;
                let norm = w[target_k]
                    .mul(&w[target_k].conj())
                    .as_rational()
                    .checked_invariant_65096192("dyadic output norm lies in Q");
                let total: Rational = w
                    .iter()
                    .map(|a| {
                        a.mul(&a.conj())
                            .as_rational()
                            .checked_invariant_65096192("dyadic output norms lie in Q")
                    })
                    .sum();
                let p = norm / total;
                (
                    p.numer().to_i64().checked_invariant_65096192("bounded dyadic numerator"),
                    p.denom().to_i64().checked_invariant_65096192("bounded dyadic denominator"),
                )
            },
        }
    }

    /// Returns the exact rational probability of the outcome.
    pub fn rational_probability(&self) -> Rational {
        rq(self.target_probability.0, self.target_probability.1)
    }

    /// Verifies that all 2^m dyadic phases project deterministically with probability 1.
    pub fn verify_all_dyadic_phases(m: usize) -> bool {
        let dim = 1 << m;
        for k in 0..dim {
            let res = Self::run(m, k);
            if !res.is_exact_projection
                || !res.unitary_qft_verified
                || res.target_probability != (1, 1)
                || res.rational_probability() != r_one()
            {
                return false;
            }
        }
        true
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PhaseEstimationError {
    #[error("the register, phase denominator, or combined conductor exceeds the finite budget")]
    Budget,
    #[error(transparent)]
    Field(#[from] core_number_theory::cyclotomic_field::CyclotomicError),
    #[error(transparent)]
    Matrix(#[from] crate::exact_hermitian::ExactHermitianError),
    #[error("the declared matrix is not unitary or the vector is not a normalized eigenvector with the declared phase")]
    Eigenpair,
}

/// Exact QPE for any rational phase whose combined conductor fits the sovereign
/// cyclotomic-field budget. The unnormalised Fourier sum is divided by N^2 at
/// readout, so no unrepresented square root or float is introduced.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalPhaseEstimation {
    pub register_dim: usize,
    pub phase: Rational,
    pub conductor: usize,
    pub amplitudes: Vec<core_number_theory::cyclotomic_field::CyclotomicNumber>,
    pub probabilities: Vec<core_number_theory::cyclotomic_field::CyclotomicNumber>,
    pub fourier_unitary: bool,
}

impl RationalPhaseEstimation {
    fn compute_amplitudes_and_probabilities(
        n: usize,
        conductor: usize,
        phase_step: usize,
        fourier_step: usize,
    ) -> Result<
        (
            Vec<core_number_theory::cyclotomic_field::CyclotomicNumber>,
            Vec<core_number_theory::cyclotomic_field::CyclotomicNumber>,
        ),
        PhaseEstimationError,
    > {
        use num_bigint::BigInt;
        use core_number_theory::cyclotomic_field::CyclotomicNumber;
        let mut amplitudes = Vec::with_capacity(n);
        let mut probabilities = Vec::with_capacity(n);
        let divisor = Rational::new(BigInt::from(1), BigInt::from(n) * BigInt::from(n));
        for j in 0..n {
            let mut sum = CyclotomicNumber::zero(conductor)?;
            for l in 0..n {
                let exponent = ((phase_step as i64) - (j * fourier_step) as i64) * (l as i64);
                let term = CyclotomicNumber::zeta(conductor, exponent)?;
                sum = sum.add(&term)?;
            }
            let prob = sum.mul(&sum.conjugate())?.scale(&divisor);
            probabilities.push(prob);
            amplitudes.push(sum);
        }
        Ok((amplitudes, probabilities))
    }

    fn check_fourier_unitarity(
        n: usize,
        conductor: usize,
        fourier_step: usize,
    ) -> Result<bool, PhaseEstimationError> {
        use num_bigint::BigInt;
        use core_number_theory::cyclotomic_field::CyclotomicNumber;
        let mut fourier_unitary = true;
        for difference in 0..n {
            let mut gram_entry = CyclotomicNumber::zero(conductor)?;
            for l in 0..n {
                let term =
                    CyclotomicNumber::zeta(conductor, (difference * l * fourier_step) as i64)?;
                gram_entry = gram_entry.add(&term)?;
            }
            let target_rat = if difference == 0 {
                Rational::from_integer(BigInt::from(n))
            } else {
                core_number_theory::rational::r_zero()
            };
            let expected = CyclotomicNumber::from_rational(conductor, target_rat)?;
            fourier_unitary &= gram_entry == expected;
        }
        Ok(fourier_unitary)
    }

    pub fn run(m: usize, phase: Rational) -> Result<Self, PhaseEstimationError> {
        use num_bigint::BigInt;
        use num_integer::Integer;
        use num_traits::ToPrimitive;
        if m > 7 {
            return Err(PhaseEstimationError::Budget);
        }
        let n = 1usize << m;
        let q = phase
            .denom()
            .to_usize()
            .ok_or(PhaseEstimationError::Budget)?;
        let numerator = phase
            .numer()
            .mod_floor(phase.denom())
            .to_usize()
            .ok_or(PhaseEstimationError::Budget)?;
        let conductor = n
            .checked_mul(q / n.gcd(&q))
            .filter(|&c| c <= core_number_theory::polynomial::MAX_CONDUCTOR)
            .ok_or(PhaseEstimationError::Budget)?;
        let phase_step = numerator * (conductor / q);
        let fourier_step = conductor / n;
        let (amplitudes, probabilities) = Self::compute_amplitudes_and_probabilities(
            n,
            conductor,
            phase_step,
            fourier_step,
        )?;
        // F*F=N I: each off-diagonal Gram entry is a Fourier character sum.
        let fourier_unitary = Self::check_fourier_unitarity(n, conductor, fourier_step)?;
        Ok(Self {
            register_dim: n,
            phase: Rational::new(BigInt::from(numerator), BigInt::from(q)),
            conductor,
            amplitudes,
            probabilities,
            fourier_unitary,
        })
    }

    fn verify_unitary_and_normalized(
        u: &BasicMatrix<GaussianRat>,
        psi: &[core_number_theory::cyclotomic::GaussianRat],
    ) -> Result<(), PhaseEstimationError> {
        let d = crate::exact_hermitian::square_dim(u)?;
        let adj_u = linear_algebra::exact_field::involution::adjoint(u)
            .checked_invariant_65096192("validated finite matrix shape and budget");
        let prod = linear_algebra::exact_field::matrix::multiply_with_limits(
            &adj_u,
            u,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_65096192("validated finite matrix shape and budget");
        let id_d = linear_algebra::exact_field::matrix::identity::<GaussianRat>(d)
            .map_err(crate::exact_hermitian::ExactHermitianError::from)?;
        let norm_psi = linear_algebra::exact_field::involution::inner_product(psi, psi)
            .map_err(crate::exact_hermitian::ExactHermitianError::from)?;
        if prod != id_d || norm_psi != core_number_theory::cyclotomic::GaussianRat::one() {
            return Err(PhaseEstimationError::Eigenpair);
        }
        Ok(())
    }

    fn embed_gaussian_in_cyclotomic(
        conductor: usize,
        i_unit: &core_number_theory::cyclotomic_field::CyclotomicNumber,
        z: &GaussianRat,
    ) -> Result<core_number_theory::cyclotomic_field::CyclotomicNumber, PhaseEstimationError> {
        use core_number_theory::cyclotomic_field::CyclotomicNumber;
        let re_part = CyclotomicNumber::from_rational(conductor, z.re.clone())?;
        Ok(re_part.add(&i_unit.scale(&z.im))?)
    }

    fn phase_cyclotomic_eigenvalue(
        phase: &Rational,
    ) -> Result<
        (
            usize,
            core_number_theory::cyclotomic_field::CyclotomicNumber,
            core_number_theory::cyclotomic_field::CyclotomicNumber,
        ),
        PhaseEstimationError,
    > {
        use num_integer::Integer;
        use num_traits::ToPrimitive;
        use core_number_theory::cyclotomic_field::CyclotomicNumber;
        let q = phase
            .denom()
            .to_usize()
            .ok_or(PhaseEstimationError::Budget)?;
        let conductor = q
            .checked_mul(4 / q.gcd(&4))
            .ok_or(PhaseEstimationError::Budget)?;
        let p = phase
            .numer()
            .mod_floor(phase.denom())
            .to_i64()
            .ok_or(PhaseEstimationError::Budget)?;
        let eigenvalue = CyclotomicNumber::zeta(conductor, p * (conductor / q) as i64)?;
        let i = CyclotomicNumber::zeta(conductor, (conductor / 4) as i64)?;
        Ok((conductor, eigenvalue, i))
    }

    /// Admit the phase only after checking U*U=I and U psi=zeta_q^p psi.
    pub fn from_eigenpair(
        m: usize,
        phase: Rational,
        u: &BasicMatrix<GaussianRat>,
        psi: &[core_number_theory::cyclotomic::GaussianRat],
    ) -> Result<Self, PhaseEstimationError> {
        Self::verify_unitary_and_normalized(u, psi)?;
        let evolved = linear_algebra::exact_field::matrix::multiply_vector(u, psi)
            .map_err(crate::exact_hermitian::ExactHermitianError::from)?;
        let (conductor, eigenvalue, i) = Self::phase_cyclotomic_eigenvalue(&phase)?;
        for (a, b) in evolved.iter().zip(psi) {
            let ea = Self::embed_gaussian_in_cyclotomic(conductor, &i, a)?;
            let eb = Self::embed_gaussian_in_cyclotomic(conductor, &i, b)?;
            if ea != eigenvalue.mul(&eb)? {
                return Err(PhaseEstimationError::Eigenpair);
            }
        }
        Self::run(m, phase)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/phase_estimation.rs
// Claim: urn:core:crates_rs:core-quantum-physics:phase-estimation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dyadic_roots_match_wide_reference_at_integer_boundaries() {
        let powers = [
            i64::MIN,
            i64::MIN + 1,
            i64::MIN + 7,
            i64::MIN / 12 - 1,
            i64::MIN / 12,
            i64::MIN / 6 - 1,
            i64::MIN / 6,
            i64::MIN / 3 - 1,
            i64::MIN / 3,
            -25,
            -24,
            -9,
            -8,
            -1,
            0,
            1,
            7,
            8,
            24,
            25,
            i64::MAX / 12,
            i64::MAX / 12 + 1,
            i64::MAX / 6,
            i64::MAX / 6 + 1,
            i64::MAX / 3,
            i64::MAX / 3 + 1,
            i64::MAX - 7,
            i64::MAX - 1,
            i64::MAX,
        ];
        for m in 1..=3 {
            let step = 24_i128 / (1_i128 << m);
            for power in powers {
                let expected_index = (i128::from(power) * step).rem_euclid(24) as i32;
                assert_eq!(
                    dyadic_root_of_unity(m, power),
                    Cyc24::zeta24(expected_index),
                    "m={m}, power={power}"
                );
            }
        }
    }

    #[test]
    fn dyadic_roots_are_periodic_across_signed_exponents() {
        for m in 1..=3 {
            let period = 1_i64 << m;
            for power in [i64::MIN, i64::MIN + 1, -25, -1, 0, 1, 25, i64::MAX] {
                let root = dyadic_root_of_unity(m, power);
                if let Some(next) = power.checked_add(period) {
                    assert_eq!(root, dyadic_root_of_unity(m, next), "m={m}, power={power}");
                }
                if let Some(previous) = power.checked_sub(period) {
                    assert_eq!(
                        root,
                        dyadic_root_of_unity(m, previous),
                        "m={m}, power={power}"
                    );
                }
            }
            for power in -64..=64 {
                let expected_index =
                    (i128::from(power) * 24 / i128::from(period)).rem_euclid(24) as i32;
                assert_eq!(
                    dyadic_root_of_unity(m, power),
                    Cyc24::zeta24(expected_index)
                );
            }
        }
    }

    #[test]
    fn test_phase_estimation_m1_all_phases() {
        assert!(DiscretePhaseEstimation::verify_all_dyadic_phases(1));
    }

    #[test]
    fn test_phase_estimation_m2_all_phases() {
        assert!(DiscretePhaseEstimation::verify_all_dyadic_phases(2));
    }

    #[test]
    fn test_phase_estimation_m3_all_phases() {
        assert!(DiscretePhaseEstimation::verify_all_dyadic_phases(3));
    }

    #[test]
    fn test_unitary_qft_matrices() {
        assert!(verify_qft_unitarity(1));
        assert!(verify_qft_unitarity(2));
        assert!(verify_qft_unitarity(3));
    }
}
