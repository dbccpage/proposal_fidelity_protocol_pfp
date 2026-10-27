//! Quantum entropy measures (von Neumann entropy, relative entropy, purity) for `core_quantum_physics`.
//!
//! The [`DensityMatrix`] of this module stores only the computational-basis populations
//! of a state, so [`Entropy::von_neumann`], [`Entropy::relative_entropy`] and
//! [`Entropy::purity`] are the Shannon entropy, relative entropy and collision probability
//! of that population vector. They equal the quantum quantities only for states diagonal
//! in the computational basis; a state with coherences has smaller von Neumann entropy.
//!
//! [`Entropy::von_neumann_exact`] is the genuine `S(rho) = -Tr(rho ln rho)` of an
//! [`ExactDensityMatrix`] (full operator over `Q(i)`) whenever its spectrum is rational:
//! the exact spectrum comes from `core_number_theory` root isolation, and the entropy is
//! the exact rational combination of logarithms of primes from
//! `core_finite_probability::log_form`. An irrational spectrum is refused.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::density_matrix::{DensityMatrix, ExactDensityMatrix};
use core_finite_probability::log_form::{shannon_entropy_form, LogForm};
use core_finite_probability::simplex::ProbabilitySimplex;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite entropy face.";

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum EntropyError {
    #[error(transparent)]
    Density(#[from] crate::density_matrix::DensityError),
    #[error("empty distribution")]
    EmptyDistribution,
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("non-finite entry encountered")]
    NonFiniteEntry,
    #[error("negative probability at index {index}: {value}")]
    NegativeProbability { index: usize, value: f64 },
    #[error("infinite divergence")]
    InfiniteDivergence,
    #[error(
        "the spectrum is not rational, so the entropy is not a rational combination of logarithms"
    )]
    IrrationalSpectrum,
    #[error("exact density matrix refused: {0}")]
    ExactDensity(String),
    #[error("entropy form refused: {0}")]
    Form(String),
}

/// Finite carrier for `entropy`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Entropy {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl Entropy {
    /// Rational enclosure of entropy for any exact Hermitian state, including
    /// irrational spectra. Eigenvalues are isolated by the shared exact spectrum
    /// and -x log x is enclosed using certified elementary logarithms.
    pub fn von_neumann_enclosure(
        rho: &ExactDensityMatrix,
        bits: u32,
    ) -> Result<core_kernel::interval::Interval, EntropyError> {
        use core_kernel::interval::Interval;
        use core_number_theory::polynomial::Polynomial;
        use core_number_theory::rational::{ri, Rational};
        if bits > core_finite_probability::log_form::MAX_ENCLOSURE_BITS {
            return Err(EntropyError::Form("precision budget exceeded".into()));
        }
        let coeff = rho
            .as_operator()
            .characteristic_polynomial()
            .map_err(|e| EntropyError::ExactDensity(e.to_string()))?;
        let polynomial = Polynomial::from_coefficients(coeff.into_iter().map(|z| z.re).collect());
        let spectrum = rho
            .spectrum()
            .map_err(|e| EntropyError::ExactDensity(e.to_string()))?;
        let tolerance = Rational::new(1.into(), num_bigint::BigInt::from(1) << bits);
        let mut total = Interval::point(ri(0));
        for root in spectrum.roots() {
            if let Some(term) =
                Self::enclose_root_entropy_term(&polynomial, root, &tolerance, bits)?
            {
                total = total.add(&term);
            }
        }
        Ok(total)
    }

    fn enclose_root_entropy_term(
        polynomial: &core_number_theory::polynomial::Polynomial<
            core_number_theory::rational::Rational,
        >,
        root: &core_number_theory::polynomial::RealRoot,
        tolerance: &core_number_theory::rational::Rational,
        bits: u32,
    ) -> Result<Option<core_kernel::interval::Interval>, EntropyError> {
        use core_kernel::interval::Interval;
        use core_number_theory::polynomial::refine_root;
        use core_number_theory::rational::Rational;
        let refined = refine_root(polynomial, root, tolerance)
            .map_err(|e| EntropyError::Form(e.to_string()))?;
        let Some((range, multiplicity)) = Self::isolate_positive_root_range(polynomial, refined)?
        else {
            return Ok(None);
        };
        let lo = core_kernel::elementary::ln_enclosure(range.lo(), bits)
            .map_err(|e| EntropyError::Form(e.to_string()))?;
        let hi = core_kernel::elementary::ln_enclosure(range.hi(), bits)
            .map_err(|e| EntropyError::Form(e.to_string()))?;
        let logarithm = Interval::new(lo.lo().clone(), hi.hi().clone());
        let term = range
            .mul(&logarithm)
            .mul_scalar(&(-Rational::from_integer(multiplicity.into())));
        Ok(Some(term))
    }

    fn isolate_positive_root_range(
        polynomial: &core_number_theory::polynomial::Polynomial<
            core_number_theory::rational::Rational,
        >,
        mut root: core_number_theory::polynomial::RealRoot,
    ) -> Result<Option<(core_kernel::interval::Interval, usize)>, EntropyError> {
        use num_traits::{Signed, Zero};
        use core_kernel::interval::Interval;
        use core_number_theory::polynomial::{refine_root, RootLocation};
        use core_number_theory::rational::ri;
        loop {
            match &root.location {
                RootLocation::Exact(q) if q.is_zero() => return Ok(None),
                RootLocation::Exact(q) => {
                    return Ok(Some((Interval::point(q.clone()), root.multiplicity)))
                }
                RootLocation::Isolated(i) if i.lo().is_positive() => {
                    return Ok(Some((i.clone(), root.multiplicity)))
                }
                RootLocation::Isolated(i) => {
                    let width = i.diam() / ri(2);
                    root = refine_root(polynomial, &root, &width)
                        .map_err(|e| EntropyError::Form(e.to_string()))?;
                }
            }
        }
    }

    /// Renyi-2 entropy -log Tr rho^2, as an exact logarithm form.
    pub fn renyi_two_exact(rho: &ExactDensityMatrix) -> Result<LogForm, EntropyError> {
        Ok(LogForm::ln_of_positive_rational(
            &rho.purity(),
            core_finite_probability::log_form::DEFAULT_FACTOR_BOUND,
        )
        .map_err(|e| EntropyError::Form(e.to_string()))?
        .neg())
    }

    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// von Neumann entropy S(ρ) = -∑ pᵢ ln pᵢ in nats (0 ln 0 := 0).
    pub fn von_neumann(rho: &DensityMatrix) -> f64 {
        rho.von_neumann_entropy()
    }

    /// The exact von Neumann entropy `-Tr(rho ln rho)` of a density operator with a rational
    /// spectrum, as `sum_q gamma_q ln q` over primes `q` (`gamma_q = -sum_i lambda_i v_q(lambda_i)`
    /// with `v_q` the `q`-adic valuation). Zero exactly for pure states. A spectrum with an
    /// irrational eigenvalue is refused with [`EntropyError::IrrationalSpectrum`].
    pub fn von_neumann_exact(rho: &ExactDensityMatrix) -> Result<LogForm, EntropyError> {
        let spectrum = rho
            .spectrum()
            .map_err(|e| EntropyError::ExactDensity(e.to_string()))?;
        let eigenvalues = spectrum
            .rational_eigenvalues()
            .ok_or(EntropyError::IrrationalSpectrum)?;
        let mut probabilities = Vec::with_capacity(rho.dim());
        for (value, multiplicity) in eigenvalues {
            for _ in 0..multiplicity {
                probabilities.push(value.clone());
            }
        }
        let simplex = ProbabilitySimplex::try_new(probabilities)
            .map_err(|e| EntropyError::Form(e.to_string()))?;
        shannon_entropy_form(&simplex).map_err(|e| EntropyError::Form(e.to_string()))
    }

    /// von Neumann entropy in bits (divided by ln 2).
    pub fn von_neumann_bits(rho: &DensityMatrix) -> f64 {
        rho.von_neumann_entropy() / std::f64::consts::LN_2
    }

    /// Purity γ = Tr(ρ²) = ∑ pᵢ².
    pub fn purity(rho: &DensityMatrix) -> f64 {
        rho.purity()
    }

    /// Quantum relative entropy S(ρ ‖ σ) = ∑ pᵢ (ln pᵢ - ln qᵢ).
    /// Returns InfiniteDivergence if supp(ρ) ⊄ supp(σ).
    pub fn relative_entropy(
        rho: &DensityMatrix,
        sigma: &DensityMatrix,
    ) -> Result<f64, EntropyError> {
        if rho.dim != sigma.dim {
            return Err(EntropyError::DimensionMismatch {
                expected: rho.dim,
                actual: sigma.dim,
            });
        }
        rho.validate(crate::density_matrix::DEFAULT_TOL)?;
        sigma.validate(crate::density_matrix::DEFAULT_TOL)?;
        let mut d_rel = 0.0;
        for i in 0..rho.dim {
            let p = rho.probs[i];
            let q = sigma.probs[i];
            if p > 0.0 {
                if q <= 0.0 {
                    return Err(EntropyError::InfiniteDivergence);
                }
                d_rel += p * (p.ln() - q.ln());
            }
        }
        Ok(d_rel)
    }

    /// Classical Shannon entropy of a probability distribution.
    pub fn shannon(probabilities: &[f64]) -> Result<f64, EntropyError> {
        if probabilities.is_empty() {
            return Err(EntropyError::EmptyDistribution);
        }
        let mut sum = 0.0;
        let mut s = 0.0;
        for (i, &p) in probabilities.iter().enumerate() {
            if !p.is_finite() {
                return Err(EntropyError::NonFiniteEntry);
            }
            if p < 0.0 {
                return Err(EntropyError::NegativeProbability { index: i, value: p });
            }
            sum += p;
            if p > 0.0 {
                s -= p * p.ln();
            }
        }
        if (sum - 1.0).abs() > 1e-6 && sum > 0.0 {
            // Renormalize
            let inv = 1.0 / sum;
            s = 0.0;
            for &p in probabilities {
                if p > 0.0 {
                    let q = p * inv;
                    s -= q * q.ln();
                }
            }
        }
        Ok(s)
    }

    /// Degree / dimension proxy.
    pub fn degree(&self) -> usize {
        self.degree
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/entropy.rs
// Claim: urn:core:crates_rs:core-quantum-physics:entropy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hilbert_space::HilbertSpace;

    #[test]
    fn new_and_fence() {
        let x = Entropy::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(Entropy::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn von_neumann_entropy_values() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let pure = DensityMatrix::pure_computational(&h2, 0, "0").unwrap();
        assert!(Entropy::von_neumann(&pure) < 1e-12);
        assert!((Entropy::purity(&pure) - 1.0).abs() < 1e-12);

        let mixed = DensityMatrix::maximally_mixed(&h2, "mix");
        assert!((Entropy::von_neumann(&mixed) - (2.0_f64).ln()).abs() < 1e-12);
        assert!((Entropy::von_neumann_bits(&mixed) - 1.0).abs() < 1e-12);
        assert!((Entropy::purity(&mixed) - 0.5).abs() < 1e-12);
    }

    #[test]
    fn relative_entropy_properties() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let rho = DensityMatrix::try_from_probs(&h2, vec![0.7, 0.3], "rho", 1e-6).unwrap();
        let sigma = DensityMatrix::try_from_probs(&h2, vec![0.5, 0.5], "sigma", 1e-6).unwrap();

        // S(rho || rho) = 0
        assert!(Entropy::relative_entropy(&rho, &rho).unwrap() < 1e-12);

        // S(rho || sigma) >= 0 (Klein's inequality)
        let d_rel = Entropy::relative_entropy(&rho, &sigma).unwrap();
        assert!(d_rel > 0.0);
    }
}

#[cfg(test)]
mod exact_entropy_tests {
    use super::*;
    use crate::quantum_state::RayVector;
    use num_traits::{ToPrimitive, Zero};
    use core_number_theory::rational::{rq, Rational};

    fn ket(entries: &[(i64, i64)]) -> ExactDensityMatrix {
        ExactDensityMatrix::pure(&RayVector::from_ints(entries).unwrap()).unwrap()
    }

    fn basis(n: usize, k: usize) -> ExactDensityMatrix {
        ExactDensityMatrix::pure(&RayVector::basis(n, k).unwrap()).unwrap()
    }

    #[test]
    fn a_pure_state_has_zero_entropy_and_the_maximally_mixed_state_has_ln_d() {
        assert!(Entropy::von_neumann_exact(&ket(&[(1, 0), (1, 0)]))
            .unwrap()
            .is_zero());
        let mixed =
            Entropy::von_neumann_exact(&ExactDensityMatrix::maximally_mixed(4).unwrap()).unwrap();
        // ln 4 = 2 ln 2, and nothing else
        assert_eq!(mixed.coefficient(2), rq(2, 1));
        assert_eq!(mixed.terms().len(), 1);
    }

    #[test]
    fn a_diagonal_mixture_has_the_shannon_entropy_of_its_weights() {
        let (a, b, c) = (basis(3, 0), basis(3, 1), basis(3, 2));
        let rho =
            ExactDensityMatrix::mixture(&[(rq(1, 2), &a), (rq(1, 4), &b), (rq(1, 4), &c)]).unwrap();
        // -(1/2) ln(1/2) - 2 (1/4) ln(1/4) = (3/2) ln 2
        let s = Entropy::von_neumann_exact(&rho).unwrap();
        assert_eq!(s.coefficient(2), rq(3, 2));
        assert_eq!(s.terms().len(), 1);
        // weights 1/3 and 2/3: ln 3 - (2/3) ln 2 = 0.63651416829...
        let (a2, b2) = (basis(2, 0), basis(2, 1));
        let rho2 = ExactDensityMatrix::mixture(&[(rq(1, 3), &a2), (rq(2, 3), &b2)]).unwrap();
        let s2 = Entropy::von_neumann_exact(&rho2).unwrap();
        assert_eq!(s2.coefficient(3), rq(1, 1));
        assert_eq!(s2.coefficient(2), rq(-2, 3));
        let value = s2.coefficient(3).to_f64().unwrap() * 3f64.ln()
            + s2.coefficient(2).to_f64().unwrap() * 2f64.ln();
        let direct = -(1.0 / 3.0) * (1.0f64 / 3.0).ln() - (2.0 / 3.0) * (2.0f64 / 3.0).ln();
        assert!((value - direct).abs() < 1e-12);
    }

    /// Coherences lower the entropy: an equal mixture of two Bell states is diagonal-free
    /// in the computational basis (all four populations 1/4, Shannon entropy ln 4) but has
    /// rank 2 with spectrum (1/2, 1/2, 0, 0), von Neumann entropy ln 2.
    #[test]
    fn coherences_make_the_von_neumann_entropy_smaller_than_the_population_entropy() {
        let phi_plus = ket(&[(1, 0), (0, 0), (0, 0), (1, 0)]);
        let psi_plus = ket(&[(0, 0), (1, 0), (1, 0), (0, 0)]);
        let rho =
            ExactDensityMatrix::mixture(&[(rq(1, 2), &phi_plus), (rq(1, 2), &psi_plus)]).unwrap();
        let s = Entropy::von_neumann_exact(&rho).unwrap();
        assert_eq!(s.coefficient(2), rq(1, 1));
        assert_eq!(s.terms().len(), 1);
        // the population shadow loses the coherences and reports ln 4
        let (shadow, coherence_weight) = rho.population_shadow("shadow").unwrap();
        assert!(coherence_weight > Rational::zero());
        let population_entropy = Entropy::von_neumann(&shadow);
        assert!((population_entropy - 4f64.ln()).abs() < 1e-12);
        assert!(population_entropy > 2f64.ln() + 0.5);
    }

    #[test]
    fn an_irrational_spectrum_is_refused() {
        // (2/3)|0><0| + (1/3)|+><+| has eigenvalues (1 +- sqrt(5)/3) / 2
        let zero = basis(2, 0);
        let plus = ket(&[(1, 0), (1, 0)]);
        let rho = ExactDensityMatrix::mixture(&[(rq(2, 3), &zero), (rq(1, 3), &plus)]).unwrap();
        assert_eq!(
            Entropy::von_neumann_exact(&rho),
            Err(EntropyError::IrrationalSpectrum)
        );
    }
}
