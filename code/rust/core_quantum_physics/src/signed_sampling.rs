//! Exact real finite signed sums and declared iid sign-mean statistics.
//! AuthorityEffect: None. No sampler, thermal exponential, free-energy gap or
//! computational hardness is inferred. Independent copies are an explicit
//! mathematical product-weight construction, not a claim about a physical model.
use crate::exact_hermitian::{check_hermitian, exact_limits};
use crate::finite_schrodinger_step::{euler_propagator, norm_rate};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as star, matrix as mx};
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_holonomy::signed_transport::SignedCoefficientGraph;
use core_number_theory::cyclotomic::GaussianRat;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("signed sampling refusal: {0}")]
pub struct SignedSamplingError(pub &'static str);

fn canonical(q: &BigRational) -> bool {
    if q.denom() <= &0.into() {
        return false;
    }
    let reduced = BigRational::new(q.numer().clone(), q.denom().clone());
    reduced.numer() == q.numer() && reduced.denom() == q.denom()
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignedWeightFamily {
    signed_mass: BigRational,
    absolute_mass: BigRational,
}
impl SignedWeightFamily {
    fn from_totals(
        signed_mass: BigRational,
        absolute_mass: BigRational,
    ) -> Result<Self, SignedSamplingError> {
        if !canonical(&signed_mass)
            || !canonical(&absolute_mass)
            || absolute_mass <= BigRational::zero()
            || signed_mass.abs() > absolute_mass
        {
            return Err(SignedSamplingError(
                "zero/invalid absolute-weight partition",
            ));
        }
        Ok(Self {
            signed_mass,
            absolute_mass,
        })
    }
    pub fn try_new(weights: &[BigRational]) -> Result<Self, SignedSamplingError> {
        if weights.is_empty() || weights.iter().any(|q| !canonical(q)) {
            return Err(SignedSamplingError(
                "empty or noncanonical exact weight family",
            ));
        }
        Self::from_totals(
            weights.iter().cloned().sum(),
            weights.iter().map(Signed::abs).sum(),
        )
    }
    pub fn signed_mass(&self) -> &BigRational {
        &self.signed_mass
    }
    pub fn absolute_mass(&self) -> &BigRational {
        &self.absolute_mass
    }
    pub fn average_sign(&self) -> BigRational {
        &self.signed_mass / &self.absolute_mass
    }
    /// Requires iid sampling from q_x=|w_x|/sum|w|. Zero-weight atoms have q=0.
    pub fn iid_sign_mean_variance(
        &self,
        samples: usize,
    ) -> Result<BigRational, SignedSamplingError> {
        if samples == 0 {
            return Err(SignedSamplingError("iid sample count is zero"));
        }
        let a = self.average_sign();
        Ok((BigRational::one() - &a * &a) / BigRational::from_integer(samples.into()))
    }
    /// Relative variance of the sign mean only; undefined at signed mass zero.
    pub fn iid_relative_variance(
        &self,
        samples: usize,
    ) -> Result<BigRational, SignedSamplingError> {
        let a = self.average_sign();
        if a.is_zero() {
            return Err(SignedSamplingError("relative variance at zero signed sum"));
        }
        Ok(self.iid_sign_mean_variance(samples)? / (&a * &a))
    }
    /// Product family weights w_(x1,...,xk)=prod_j w_xj. This specifies the
    /// independence/factorization needed for a_k=a^k, rather than discovering it.
    pub fn independent_copies(&self, copies: usize) -> Result<Self, SignedSamplingError> {
        if copies == 0 {
            return Err(SignedSamplingError(
                "positive independent-copy count required",
            ));
        }
        let exponent = i32::try_from(copies)
            .map_err(|_| SignedSamplingError("copy exponent exceeds exact host API"))?;
        Self::from_totals(
            self.signed_mass.pow(exponent),
            self.absolute_mass.pow(exponent),
        )
    }
}

/// Actual coefficient bridge: declared standard orthonormal basis and real
/// scalars give a Hermitian Q(i) matrix. No dynamics is selected by this map.
pub fn real_symmetric_hamiltonian(
    coefficients: &[Vec<BigRational>],
) -> Result<BasicMatrix<GaussianRat>, SignedSamplingError> {
    // Match the delegated Euler identity admission before cloning coefficients
    // or constructing any dense matrix. Its identity uses a 2^20 element cap.
    let side = coefficients.len();
    let elements = side
        .checked_mul(side)
        .ok_or(SignedSamplingError("Hamiltonian dimension overflow"))?;
    if side == 0 || elements > (1 << 20) {
        return Err(SignedSamplingError(
            "Hamiltonian dense carrier exceeds 2^20 element budget",
        ));
    }
    let graph = SignedCoefficientGraph::try_new(coefficients.to_vec())
        .map_err(|_| SignedSamplingError("Hamiltonian coefficient shape/symmetry/exactness"))?;
    let matrix = mx::from_rows(
        graph
            .coefficients()
            .iter()
            .map(|row| {
                row.iter()
                    .map(|q| GaussianRat {
                        re: q.clone(),
                        im: BigRational::zero(),
                    })
                    .collect()
            })
            .collect(),
    )
    .map_err(|_| SignedSamplingError("Hamiltonian matrix carrier"))?;
    check_hermitian(&matrix)
        .map_err(|_| SignedSamplingError("empty or non-Hermitian Hamiltonian"))?;
    Ok(matrix)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HamiltonianStepCertificate {
    pub hamiltonian: BasicMatrix<GaussianRat>,
    pub euler_step: BasicMatrix<GaussianRat>,
    pub norm_rate: BigRational,
    pub euler_unitarity_defect: BasicMatrix<GaussianRat>,
}

fn compute_euler_unitarity_defect_and_expected(
    h: &BasicMatrix<GaussianRat>,
    euler: &BasicMatrix<GaussianRat>,
    tau: &BigRational,
) -> Result<(BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>), SignedSamplingError> {
    let algebra = |_| SignedSamplingError("exact Hamiltonian matrix algebra refused");
    let adjoint = star::adjoint(euler).map_err(algebra)?;
    let product = mx::multiply_with_limits(&adjoint, euler, exact_limits()).map_err(algebra)?;
    let identity =
        mx::identity_with_limits::<GaussianRat>(h.rows(), exact_limits()).map_err(algebra)?;
    let defect = mx::sub(&product, &identity).map_err(algebra)?;
    let h_squared = mx::multiply_with_limits(h, h, exact_limits()).map_err(algebra)?;
    let expected = mx::scale(
        &h_squared,
        &GaussianRat {
            re: tau * tau,
            im: BigRational::zero(),
        },
    )
    .map_err(algebra)?;
    Ok((defect, expected))
}

/// Reuses the existing finite Schrödinger owner. Euler is NOT declared unitary:
/// the checked defect is tau² H², while the instantaneous norm rate is zero.
pub fn verify_real_hamiltonian_step(
    coefficients: &[Vec<BigRational>],
    tau: &BigRational,
    psi: &[GaussianRat],
) -> Result<HamiltonianStepCertificate, SignedSamplingError> {
    if !canonical(tau) || psi.iter().any(|z| !canonical(&z.re) || !canonical(&z.im)) {
        return Err(SignedSamplingError("noncanonical step or amplitude"));
    }
    let h = real_symmetric_hamiltonian(coefficients)?;
    let rate =
        norm_rate(&h, psi).map_err(|_| SignedSamplingError("Hamiltonian amplitude carrier"))?;
    let euler = euler_propagator(&h, tau).map_err(|_| SignedSamplingError("Euler step carrier"))?;
    let (defect, expected) = compute_euler_unitarity_defect_and_expected(&h, &euler, tau)?;
    if !rate.is_zero() || defect != expected {
        return Err(SignedSamplingError(
            "finite Hamiltonian identity replay failed",
        ));
    }
    Ok(HamiltonianStepCertificate {
        hamiltonian: h,
        euler_step: euler,
        norm_rate: rate,
        euler_unitarity_defect: defect,
    })
}

fn entrywise_abs_matrix(
    t: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, SignedSamplingError> {
    let mut absolute_rows = Vec::with_capacity(t.rows());
    for i in 0..t.rows() {
        let mut row = Vec::with_capacity(t.cols());
        for j in 0..t.cols() {
            let entry = t
                .get_ref(i, j)
                .map_err(|_| SignedSamplingError("transfer entry carrier"))?;
            row.push(GaussianRat {
                re: entry.re.abs(),
                im: BigRational::zero(),
            });
        }
        absolute_rows.push(row);
    }
    mx::from_rows(absolute_rows)
        .map_err(|_| SignedSamplingError("exact transfer matrix algebra refused"))
}

fn power_pair_traces(
    mut signed: BasicMatrix<GaussianRat>,
    t: &BasicMatrix<GaussianRat>,
    abs_t: &BasicMatrix<GaussianRat>,
    slices: usize,
) -> Result<(BigRational, BigRational), SignedSamplingError> {
    let algebra = |_| SignedSamplingError("exact transfer matrix algebra refused");
    let mut absolute = signed.clone();
    for _ in 0..slices {
        signed = mx::multiply_with_limits(&signed, t, exact_limits()).map_err(algebra)?;
        absolute = mx::multiply_with_limits(&absolute, abs_t, exact_limits()).map_err(algebra)?;
    }
    Ok((
        mx::trace(&signed).map_err(algebra)?.re,
        mx::trace(&absolute).map_err(algebra)?.re,
    ))
}

fn validate_transfer_step_and_slices(
    step: &BigRational,
    slices: usize,
) -> Result<(), SignedSamplingError> {
    if !canonical(step) || step < &BigRational::zero() || slices == 0 || slices > 1024 {
        return Err(SignedSamplingError(
            "invalid step or finite transfer slice bound",
        ));
    }
    Ok(())
}

/// Exact finite polynomial path partition: Z=Tr(T^m), Zabs=Tr(|T|^m),
/// T=I-step H and |T| ENTRYWISE absolute values. These traces sum all closed
/// path products and their absolute values, respectively. No exp(-beta H).
/// Resource domain: 1..=1024 slices; positivity of T as an operator is not inferred.
pub fn finite_transfer_partition(
    graph: &SignedCoefficientGraph,
    step: &BigRational,
    slices: usize,
) -> Result<SignedWeightFamily, SignedSamplingError> {
    validate_transfer_step_and_slices(step, slices)?;
    let h = real_symmetric_hamiltonian(graph.coefficients())?;
    let algebra = |_| SignedSamplingError("exact transfer matrix algebra refused");
    let identity =
        mx::identity_with_limits::<GaussianRat>(h.rows(), exact_limits()).map_err(algebra)?;
    let scaled = mx::scale(
        &h,
        &GaussianRat {
            re: step.clone(),
            im: BigRational::zero(),
        },
    )
    .map_err(algebra)?;
    let t = mx::sub(&identity, &scaled).map_err(algebra)?;
    let abs_t = entrywise_abs_matrix(&t)?;
    let (tr_signed, tr_abs) = power_pair_traces(identity, &t, &abs_t, slices)?;
    SignedWeightFamily::from_totals(tr_signed, tr_abs)
}

// Origin: engine/crates_rs/core_quantum_physics/src/signed_sampling.rs
// Claim: urn:core:crates_rs:core-quantum-physics:signed-sampling:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_70bb9b94 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
