//! Nondegenerate Rayleigh-Schrodinger series in intermediate normalization,
//! checked independently against the characteristic polynomial and
//! Hellmann-Feynman identity. Rational degenerate first-order blocks are exposed.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_5dda1855<T> {
    fn checked_invariant_5dda1855(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_5dda1855<T> for Option<T> {
    #[inline]
    fn checked_invariant_5dda1855(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_5dda1855<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_5dda1855(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_hermitian::{self, gi};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution, matrix};
use num_traits::{Signed, Zero};
use core_number_theory::{
    cyclotomic::GaussianRat,
    power_series::{SeriesError, TruncatedSeries},
    rational::{rq, Rational},
};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact finite formal perturbation theory.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PerturbationError {
    #[error(transparent)]
    ExactAlgebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("Hamiltonian is malformed, non-Hermitian, or exceeds dimension eight")]
    Hamiltonian,
    #[error("level is outside the carrier")]
    Level,
    #[error("nondegenerate recursion requires an isolated unperturbed energy")]
    Degenerate,
    #[error("order exceeds 64")]
    Order,
    #[error("an energy coefficient was not real")]
    NonrealEnergy,
    #[error("matrix or spectrum operation refused: {0}")]
    Matrix(String),
    #[error("declared spectral resolution refused: {0:?}")]
    Spectrum(exact_hermitian::SpectrumError),
    #[error(transparent)]
    Series(#[from] SeriesError),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PerturbationSeries {
    pub energy: TruncatedSeries<Rational>,
    pub state: Vec<Vec<GaussianRat>>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PerturbationTheory {
    h0: Vec<Rational>,
    v: BasicMatrix<GaussianRat>,
}
impl PerturbationTheory {
    pub fn new(h0: Vec<Rational>, v: BasicMatrix<GaussianRat>) -> Result<Self, PerturbationError> {
        if h0.is_empty()
            || h0.len() > 8
            || exact_hermitian::square_dim(&v).map_err(|_| PerturbationError::Hamiltonian)?
                != h0.len()
            || !exact_hermitian::is_hermitian(&v)
        {
            return Err(PerturbationError::Hamiltonian);
        }
        Ok(Self { h0, v })
    }
    fn compute_next_state_vector(
        &self,
        level: usize,
        k: usize,
        rhs: &[GaussianRat],
        state: &[Vec<GaussianRat>],
        energy: &[Rational],
    ) -> Vec<GaussianRat> {
        let n = self.h0.len();
        let mut next = vec![gi(0, 0); n];
        for m in 0..n {
            if m == level {
                continue;
            }
            let mut value = rhs[m].clone();
            for j in 1..k {
                value = value - (&state[k - j][m] * &GaussianRat::from_rational(energy[j].clone()));
            }
            next[m] = value * GaussianRat::from_rational((&self.h0[level] - &self.h0[m]).recip());
        }
        next
    }

    pub fn series(
        &self,
        level: usize,
        order: usize,
    ) -> Result<PerturbationSeries, PerturbationError> {
        if level >= self.h0.len() {
            return Err(PerturbationError::Level);
        }
        if order > 64 {
            return Err(PerturbationError::Order);
        }
        if self
            .h0
            .iter()
            .enumerate()
            .any(|(i, e)| i != level && *e == self.h0[level])
        {
            return Err(PerturbationError::Degenerate);
        }
        let n = self.h0.len();
        let mut energy = vec![self.h0[level].clone()];
        let mut state = vec![vec![gi(0, 0); n]];
        state[0][level] = gi(1, 0);
        for k in 1..=order {
            let rhs = matrix::multiply_vector(&self.v, &state[k - 1])
                .map_err(|e| PerturbationError::Matrix(e.to_string()))?;
            if !rhs[level].is_real() {
                return Err(PerturbationError::NonrealEnergy);
            }
            energy.push(rhs[level].re.clone());
            let next = self.compute_next_state_vector(level, k, &rhs, &state, &energy);
            state.push(next);
        }
        Ok(PerturbationSeries {
            energy: TruncatedSeries::from_coefficients(energy, order)?,
            state,
        })
    }
    pub fn energy_coefficients(
        &self,
        level: usize,
        order: usize,
    ) -> Result<Vec<Rational>, PerturbationError> {
        Ok(self.series(level, order)?.energy.coefficients().to_vec())
    }

    fn build_lagrange_basis(
        node: usize,
        n: usize,
        order: usize,
    ) -> Result<TruncatedSeries<Rational>, PerturbationError> {
        let mut lagrange = TruncatedSeries::constant(rq(1, 1), order)?;
        for other in 0..=n {
            if other == node {
                continue;
            }
            let coeffs = if order == 0 {
                vec![-Rational::from_integer(other.into())]
            } else {
                vec![-Rational::from_integer(other.into()), rq(1, 1)]
            };
            let c = TruncatedSeries::from_coefficients(coeffs, order)?;
            let denominator =
                Rational::from_integer(node.into()) - Rational::from_integer(other.into());
            lagrange = lagrange.mul(&c)?.scale(&denominator.recip());
        }
        Ok(lagrange)
    }

    fn accumulate_node_polynomial(
        &self,
        node: usize,
        n: usize,
        order: usize,
        diagonal: &BasicMatrix<GaussianRat>,
        coefficient_series: &mut [TruncatedSeries<Rational>],
    ) -> Result<(), PerturbationError> {
        let scaled_v = matrix::scale(
            &self.v,
            &GaussianRat::from_rational(Rational::from_integer(node.into())),
        )?;
        let h = matrix::add(diagonal, &scaled_v)?;
        let polynomial =
            linear_algebra::exact_field::characteristic_polynomial::characteristic_polynomial(&h)
                .map_err(|e| PerturbationError::Matrix(e.to_string()))?;
        let lagrange = Self::build_lagrange_basis(node, n, order)?;
        for (j, c) in polynomial.iter().enumerate() {
            if !c.is_real() {
                return Err(PerturbationError::NonrealEnergy);
            }
            coefficient_series[j] = coefficient_series[j].add(&lagrange.scale(&c.re))?;
        }
        Ok(())
    }

    /// Independent determinant identity: interpolate det(E I-H(g)) in g from
    /// n+1 native characteristic-polynomial evaluations, then substitute E(g).
    pub fn characteristic_polynomial_residual(
        &self,
        energy: &TruncatedSeries<Rational>,
    ) -> Result<TruncatedSeries<Rational>, PerturbationError> {
        let n = self.h0.len();
        let order = energy.order();
        if order > 64 {
            return Err(PerturbationError::Order);
        }
        let mut coefficient_series = vec![TruncatedSeries::constant(rq(0, 1), order)?; n + 1];
        let diagonal = matrix::diagonal(
            &self
                .h0
                .iter()
                .cloned()
                .map(GaussianRat::from_rational)
                .collect::<Vec<_>>(),
        )?;
        for node in 0..=n {
            self.accumulate_node_polynomial(node, n, order, &diagonal, &mut coefficient_series)?;
        }
        let mut result = TruncatedSeries::constant(rq(0, 1), order)?;
        for c in coefficient_series.iter().rev() {
            result = result.mul(energy)?.add(c)?;
        }
        Ok(result)
    }

    fn compute_norm_and_expectation(
        &self,
        series: &PerturbationSeries,
        order: usize,
    ) -> Result<(Vec<Rational>, Vec<Rational>), PerturbationError> {
        let mut norm = vec![rq(0, 1); order + 1];
        let mut expectation = vec![rq(0, 1); order + 1];
        for k in 0..=order {
            for i in 0..=k {
                let inner = involution::inner_product(&series.state[i], &series.state[k - i])
                    .map_err(|e| PerturbationError::Matrix(e.to_string()))?;
                let vp = matrix::multiply_vector(&self.v, &series.state[k - i])
                    .map_err(|e| PerturbationError::Matrix(e.to_string()))?;
                let vinner = involution::inner_product(&series.state[i], &vp)
                    .map_err(|e| PerturbationError::Matrix(e.to_string()))?;
                norm[k] += &inner.re;
                expectation[k] += &vinner.re;
            }
        }
        Ok((norm, expectation))
    }

    pub fn hellmann_feynman_holds(
        &self,
        series: &PerturbationSeries,
    ) -> Result<bool, PerturbationError> {
        let order = series.energy.order();
        if order > 64 {
            return Err(PerturbationError::Order);
        }
        if series.state.len() != order + 1 || series.state.iter().any(|p| p.len() != self.h0.len())
        {
            return Err(PerturbationError::Hamiltonian);
        }
        let (norm, expectation) = self.compute_norm_and_expectation(series, order)?;
        let norm_series = TruncatedSeries::from_coefficients(norm, order)?;
        let exp_series = TruncatedSeries::from_coefficients(expectation, order)?;
        let prod = series.energy.derivative().mul(&norm_series)?;
        let residual = prod.sub(&exp_series)?;
        Ok(residual.coefficients()[..order].iter().all(Zero::is_zero))
    }
    pub fn degenerate_first_order(
        &self,
        level: usize,
        declared_spectrum: &[Rational],
    ) -> Result<exact_hermitian::SpectralResolution, PerturbationError> {
        if level >= self.h0.len() {
            return Err(PerturbationError::Level);
        }
        let indices: Vec<usize> = self
            .h0
            .iter()
            .enumerate()
            .filter_map(|(i, e)| (*e == self.h0[level]).then_some(i))
            .collect();
        let rows = indices
            .iter()
            .map(|&i| {
                indices
                    .iter()
                    .map(|&j| {
                        self.v
                            .get_ref(i, j)
                            .checked_invariant_5dda1855("validated Hamiltonian shape")
                            .clone()
                    })
                    .collect()
            })
            .collect();
        exact_hermitian::spectral_resolution(
            &matrix::from_rows(rows).map_err(|e| PerturbationError::Matrix(e.to_string()))?,
            declared_spectrum,
        )
        .map_err(PerturbationError::Spectrum)
    }
    /// Disjoint Gershgorin disks give a sufficient analytic branch radius.
    pub fn convergence_radius_lower_bound(
        &self,
        level: usize,
    ) -> Result<Option<Rational>, PerturbationError> {
        if level >= self.h0.len() {
            return Err(PerturbationError::Level);
        }
        let gap = self
            .h0
            .iter()
            .enumerate()
            .filter(|(i, _)| *i != level)
            .map(|(_, e)| (e - &self.h0[level]).abs())
            .min();
        let norm = (0..self.h0.len())
            .map(|i| {
                (0..self.h0.len())
                    .map(|j| {
                        self.v
                            .get_ref(i, j)
                            .checked_invariant_5dda1855("validated Hamiltonian shape")
                            .re
                            .abs()
                            + self
                                .v
                                .get_ref(i, j)
                                .checked_invariant_5dda1855("validated Hamiltonian shape")
                                .im
                                .abs()
                    })
                    .sum::<Rational>()
            })
            .max()
            .unwrap_or_default();
        if norm.is_zero() {
            return Ok(None);
        }
        Ok(gap.map(|g| g / (rq(2, 1) * norm)))
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/perturbation_theory.rs
// Claim: urn:core:crates_rs:core-quantum-physics:perturbation-theory:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn two_level_energy_series_is_the_signed_catalan_sequence() {
        let p = PerturbationTheory::new(
            vec![rq(0, 1), rq(1, 1)],
            matrix::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).unwrap(),
        )
        .unwrap();
        let s = p.series(0, 8).unwrap();
        assert_eq!(
            s.energy.coefficients(),
            &[
                rq(0, 1),
                rq(0, 1),
                rq(-1, 1),
                rq(0, 1),
                rq(1, 1),
                rq(0, 1),
                rq(-2, 1),
                rq(0, 1),
                rq(5, 1)
            ]
        );
        assert!(p
            .characteristic_polynomial_residual(&s.energy)
            .unwrap()
            .coefficients()
            .iter()
            .all(Zero::is_zero));
        assert!(p.hellmann_feynman_holds(&s).unwrap());
        assert_eq!(p.convergence_radius_lower_bound(0).unwrap(), Some(rq(1, 2)));
    }
    #[test]
    fn three_level_series_matches_the_independent_determinant_and_degenerate_block() {
        let v = matrix::from_rows(vec![
            vec![gi(0, 0), gi(1, 0), gi(2, 0)],
            vec![gi(1, 0), gi(0, 0), gi(1, 0)],
            vec![gi(2, 0), gi(1, 0), gi(0, 0)],
        ])
        .unwrap();
        let p = PerturbationTheory::new(vec![rq(0, 1), rq(1, 1), rq(3, 1)], v).unwrap();
        let s = p.series(0, 5).unwrap();
        assert_eq!(
            &s.energy.coefficients()[2..],
            &[rq(-7, 3), rq(4, 3), rq(70, 27), rq(-152, 27)]
        );
        assert!(p
            .characteristic_polynomial_residual(&s.energy)
            .unwrap()
            .coefficients()
            .iter()
            .all(Zero::is_zero));
        assert!(p.hellmann_feynman_holds(&s).unwrap());
        let p = PerturbationTheory::new(
            vec![rq(0, 1), rq(0, 1)],
            matrix::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).unwrap(),
        )
        .unwrap();
        assert_eq!(p.series(0, 2), Err(PerturbationError::Degenerate));
        assert_eq!(
            p.degenerate_first_order(0, &[rq(-1, 1), rq(1, 1)])
                .unwrap()
                .eigenvalues(),
            &[rq(-1, 1), rq(1, 1)]
        );
    }
}
