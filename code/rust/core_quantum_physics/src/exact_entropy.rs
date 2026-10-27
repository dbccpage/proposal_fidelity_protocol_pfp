//! Exact entropy of a declared rational quantum spectrum with multiplicities.
//! Factorization, logarithm forms and real enclosures use their sovereign owners.
//! The transcendence classification records the cited theorem hypothesis; this
//! module does not mechanize Baker's theorem or mint certified authority.
use num_bigint::BigInt;
use num_traits::{One, Signed, ToPrimitive, Zero};
use core_finite_probability::log_form::{LogForm, LogFormError};
use core_kernel::interval::Interval;
use core_number_theory::integer_factorization::{
    factor_positive_rational, FactorizationBudget, FactorizationError,
};
use core_number_theory::rational::Rational;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SpectrumError {
    #[error("the spectrum is empty")]
    Empty,
    #[error("eigenvalue {index} is outside [0,1]")]
    Eigenvalue { index: usize },
    #[error("eigenvalue {index} has a nonpositive rational denominator")]
    InvalidDenominator { index: usize },
    #[error("multiplicity {index} is zero")]
    ZeroMultiplicity { index: usize },
    #[error("spectrum trace is {trace}, expected one")]
    Trace { trace: Rational },
    #[error("spectrum dimension overflow")]
    DimensionOverflow,
    #[error("power trace needs order >= 2")]
    Order,
    #[error("order {requested} exceeds declared maximum {maximum}")]
    OrderBudget { requested: usize, maximum: usize },
    #[error("a prime basis key has {bits} bits, exceeding the u64 log-form representation")]
    PrimeBasis { bits: u64 },
    #[error(transparent)]
    Factorization(#[from] FactorizationError),
    #[error(transparent)]
    Log(#[from] LogFormError),
    #[error("normalized rational spectrum and its zero-entropy characterization disagree")]
    InconsistentReduction,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalSpectrum {
    entries: Vec<(Rational, usize)>,
    dimension: usize,
}
impl RationalSpectrum {
    pub fn try_new(entries: Vec<(Rational, usize)>) -> Result<Self, SpectrumError> {
        if entries.is_empty() {
            return Err(SpectrumError::Empty);
        }
        let mut dimension = 0usize;
        let mut trace = Rational::zero();
        for (index, (q, m)) in entries.iter().enumerate() {
            if !q.denom().is_positive() {
                return Err(SpectrumError::InvalidDenominator { index });
            }
            if q < &Rational::zero() || q > &Rational::one() {
                return Err(SpectrumError::Eigenvalue { index });
            }
            if *m == 0 {
                return Err(SpectrumError::ZeroMultiplicity { index });
            }
            dimension = dimension
                .checked_add(*m)
                .ok_or(SpectrumError::DimensionOverflow)?;
            trace += q * Rational::from_integer(BigInt::from(*m));
        }
        if !trace.is_one() {
            return Err(SpectrumError::Trace { trace });
        }
        Ok(Self { entries, dimension })
    }
    pub fn entries(&self) -> &[(Rational, usize)] {
        &self.entries
    }
    pub fn dimension(&self) -> usize {
        self.dimension
    }
    pub fn is_pure(&self) -> bool {
        self.entries.iter().any(|(q, m)| q.is_one() && *m == 1)
    }
    /// Renyi power trace Tr rho^alpha, with an explicit order budget.
    pub fn power_trace(&self, order: usize, max_order: usize) -> Result<Rational, SpectrumError> {
        if order < 2 {
            return Err(SpectrumError::Order);
        }
        if order > max_order {
            return Err(SpectrumError::OrderBudget {
                requested: order,
                maximum: max_order,
            });
        }
        let mut total = Rational::zero();
        for (q, m) in &self.entries {
            let mut exponent = order;
            let mut square = q.clone();
            let mut power = Rational::one();
            while exponent > 0 {
                if exponent & 1 == 1 {
                    power *= &square;
                }
                exponent >>= 1;
                if exponent > 0 {
                    square = &square * &square;
                }
            }
            total += Rational::from_integer(BigInt::from(*m)) * power;
        }
        Ok(total)
    }
    /// Exact prime log reduction; factorization budget applies to each eigenvalue.
    pub fn log_reduction(
        &self,
        budget: FactorizationBudget,
    ) -> Result<LogReduction, SpectrumError> {
        let mut factored = Vec::new();
        let mut primes = BTreeSet::new();
        for (q, _) in &self.entries {
            let mut row = BTreeMap::new();
            if !q.is_zero() {
                for (prime, exponent) in factor_positive_rational(q, budget)? {
                    let key = prime
                        .to_u64()
                        .ok_or(SpectrumError::PrimeBasis { bits: prime.bits() })?;
                    primes.insert(key);
                    row.insert(key, exponent);
                }
            }
            factored.push(row);
        }
        let primes = primes.into_iter().collect::<Vec<_>>();
        let exponents = factored
            .iter()
            .map(|row| {
                primes
                    .iter()
                    .map(|p| row.get(p).copied().unwrap_or(0))
                    .collect::<Vec<_>>()
            })
            .collect::<Vec<_>>();
        let gamma = (0..primes.len())
            .map(|column| {
                self.entries
                    .iter()
                    .enumerate()
                    .map(|(row, (q, m))| {
                        -q * Rational::from_integer(BigInt::from(*m))
                            * Rational::from_integer(BigInt::from(exponents[row][column]))
                    })
                    .sum::<Rational>()
            })
            .collect::<Vec<_>>();
        let mut form = LogForm::zero();
        for (prime, coefficient) in primes.iter().zip(&gamma) {
            form = form.add(&LogForm::ln_of_prime(*prime)?.scale(coefficient));
        }
        if form.is_zero() != self.is_pure() {
            return Err(SpectrumError::InconsistentReduction);
        }
        Ok(LogReduction {
            primes,
            exponents,
            gamma,
            form,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LogReduction {
    pub primes: Vec<u64>,
    pub exponents: Vec<Vec<i64>>,
    pub gamma: Vec<Rational>,
    form: LogForm,
}
impl LogReduction {
    pub fn form(&self) -> &LogForm {
        &self.form
    }
    pub fn enclosure(&self, bits: u32) -> Result<Interval, SpectrumError> {
        Ok(self.form.enclosure(bits)?)
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CitedAnchor {
    LindemannWeierstrass,
    Baker1975,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EntropyClass {
    ExactZero,
    TranscendentalByCited {
        anchor: CitedAnchor,
        reduction: LogReduction,
    },
}
impl EntropyClass {
    pub fn classify(
        spectrum: &RationalSpectrum,
        budget: FactorizationBudget,
    ) -> Result<Self, SpectrumError> {
        let reduction = spectrum.log_reduction(budget)?;
        if reduction.form.is_zero() {
            Ok(Self::ExactZero)
        } else {
            let anchor = if reduction.gamma.iter().filter(|q| !q.is_zero()).count() == 1 {
                CitedAnchor::LindemannWeierstrass
            } else {
                CitedAnchor::Baker1975
            };
            Ok(Self::TranscendentalByCited { anchor, reduction })
        }
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/exact_entropy.rs
// Claim: urn:core:crates_rs:core-quantum-physics:exact-entropy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::{ri, rq};
    fn budget() -> FactorizationBudget {
        FactorizationBudget {
            max_operations: 1000000,
        }
    }
    #[test]
    fn multiplicities_log_reductions_and_purity_are_bound_to_the_spectrum() {
        let spectrum =
            RationalSpectrum::try_new(vec![(rq(3, 4), 1), (rq(1, 4), 1), (ri(0), 2)]).unwrap();
        let reduced = spectrum.log_reduction(budget()).unwrap();
        assert_eq!(reduced.primes, vec![2, 3]);
        assert_eq!(reduced.gamma, vec![ri(2), rq(-3, 4)]);
        assert_eq!(spectrum.power_trace(2, 32).unwrap(), rq(5, 8));
        let simplex = core_finite_probability::simplex::ProbabilitySimplex::try_new(vec![
            rq(3, 4),
            rq(1, 4),
            ri(0),
            ri(0),
        ])
        .unwrap();
        assert_eq!(
            *reduced.form(),
            core_finite_probability::log_form::shannon_entropy_form(&simplex).unwrap()
        );
        let uniform = RationalSpectrum::try_new(vec![(rq(1, 3), 3)]).unwrap();
        assert_eq!(uniform.dimension(), 3);
        assert_eq!(uniform.log_reduction(budget()).unwrap().gamma, vec![ri(1)]);
        assert!(matches!(
            EntropyClass::classify(&uniform, budget()).unwrap(),
            EntropyClass::TranscendentalByCited {
                anchor: CitedAnchor::LindemannWeierstrass,
                ..
            }
        ));
        let pure = RationalSpectrum::try_new(vec![(ri(1), 1), (ri(0), 4)]).unwrap();
        assert_eq!(
            EntropyClass::classify(&pure, budget()).unwrap(),
            EntropyClass::ExactZero
        );
        assert_eq!(pure.power_trace(2, 32).unwrap(), ri(1));
    }
    #[test]
    fn malformed_spectra_and_budget_exhaustion_are_refusals() {
        assert!(matches!(
            RationalSpectrum::try_new(vec![]),
            Err(SpectrumError::Empty)
        ));
        assert!(matches!(
            RationalSpectrum::try_new(vec![(ri(1), 0)]),
            Err(SpectrumError::ZeroMultiplicity { .. })
        ));
        assert!(matches!(
            RationalSpectrum::try_new(vec![(rq(1, 3), 2)]),
            Err(SpectrumError::Trace { .. })
        ));
        assert!(matches!(
            RationalSpectrum::try_new(vec![(ri(-1), 1), (ri(2), 1)]),
            Err(SpectrumError::Eigenvalue { .. })
        ));
        let mixed = RationalSpectrum::try_new(vec![(rq(1, 3), 3)]).unwrap();
        assert!(mixed
            .log_reduction(FactorizationBudget { max_operations: 0 })
            .is_err());
        assert!(mixed.power_trace(1, 32).is_err());
        assert!(mixed.power_trace(33, 32).is_err());
    }
    #[test]
    fn raw_nonpositive_denominators_are_refused_before_spectrum_arithmetic() {
        for (numerator, denominator) in [(0, 0), (1, 0), (-1, 0), (0, -1), (-1, -1)] {
            let raw = Rational::new_raw(numerator.into(), denominator.into());
            assert_eq!(
                RationalSpectrum::try_new(vec![(ri(1), 1), (raw, 1)]),
                Err(SpectrumError::InvalidDenominator { index: 1 })
            );
        }
        let canonical = Rational::new((-1).into(), (-1).into());
        assert!(RationalSpectrum::try_new(vec![(canonical, 1)])
            .unwrap()
            .is_pure());
    }
    #[test]
    fn entropy_enclosures_have_declared_width_and_intersect_density_enclosures() {
        let spectrum = RationalSpectrum::try_new(vec![(rq(3, 4), 1), (rq(1, 4), 1)]).unwrap();
        let enclosure = spectrum
            .log_reduction(budget())
            .unwrap()
            .enclosure(64)
            .unwrap();
        assert!(enclosure.diam() <= Rational::new(1.into(), BigInt::from(1) << 64));
        let rho = crate::density_matrix::ExactDensityMatrix::try_new(
            linear_algebra::exact_field::matrix::from_rows(vec![
                vec![
                    crate::exact_hermitian::gq(3, 4, 0, 1),
                    crate::exact_hermitian::gi(0, 0),
                ],
                vec![
                    crate::exact_hermitian::gi(0, 0),
                    crate::exact_hermitian::gq(1, 4, 0, 1),
                ],
            ])
            .unwrap(),
        )
        .unwrap();
        let other = crate::entropy::Entropy::von_neumann_enclosure(&rho, 32).unwrap();
        assert!(enclosure.lo() <= other.hi() && other.lo() <= enclosure.hi());
    }
}
