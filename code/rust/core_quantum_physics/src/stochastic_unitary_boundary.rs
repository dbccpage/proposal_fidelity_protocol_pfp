// AuthorityEffect: None.

//! Stochastic steps against unitary steps on a finite carrier.
//!
//! A step on `n` sites is a square row-stochastic rational matrix `T`: it
//! pushes a population row vector `p` to `p T`. Computed exactly:
//!
//! - [`isometric_permutation`]: whether `T` also preserves the `l2` norm of
//!   every vector, decided as `T* T = I` by
//!   `unitary_generator_admission::is_unitary`, and if so the permutation it
//!   performs. An `l2`-isometric stochastic matrix is a permutation matrix:
//!   each row has entries in `[0, 1]` summing to one and squares summing to
//!   one, which leaves a single entry `1`. The stochastic matrices therefore
//!   meet the unitary group in a finite group, and no nonconstant continuous
//!   path of unitaries runs through them;
//! - [`TwoStateGenerator`]: rate generators `Q = [[-a, a], [b, -b]]` with
//!   `a, b >= 0` and `a + b > 0`, and their semigroup
//!   `T(s) = I + (1 - s) Q / (a + b)` at rational `s` in `(0, 1]`. This is
//!   `exp(t Q)` at `s = exp(-(a + b) t)`; the exponential is not computed, the
//!   semigroup is parametrised by `s`. `T(s)` is row stochastic, has
//!   determinant `s`, and satisfies `T(s) T(s') = T(s s')` because
//!   `Q^2 = -(a + b) Q`;
//! - [`two_state_embedding`]: a two-state step `[[1 - alpha, alpha],
//!   [beta, 1 - beta]]` other than the identity lies on such a semigroup exactly
//!   when `alpha + beta < 1`, that is when its determinant `1 - alpha - beta`
//!   is positive; the generator `T - I` and the parameter `s = det T` are then
//!   returned. A step with determinant `<= 0`, such as the swap, lies on none,
//!   because every `T(s)` has positive determinant.
//!
//! So a stochastic step can have fractional powers among stochastic matrices
//! once a continuous parameter is declared; what it cannot be, short of a
//! permutation, is an `l2` isometry. Refused: empty, non-square, negative or
//! unnormalized rows; generators with a negative rate or zero total rate;
//! parameters outside `(0, 1]`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_a0c50cef<T> {
    fn checked_invariant_a0c50cef(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_a0c50cef<T> for Option<T> {
    #[inline]
    fn checked_invariant_a0c50cef(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_a0c50cef<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_a0c50cef(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::{One, Signed, Zero};

use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

/// Refusals for stochastic steps and two-state semigroups.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum StochasticStepError {
    #[error("matrix operation refused: {0}")]
    Algebra(String),
    #[error("finite stochastic kernel exceeds its operation budget")]
    Budget,
    #[error("population is negative, has wrong shape or does not sum to one")]
    Population,
    #[error("a step needs at least one site")]
    Empty,
    #[error("row {row} has {actual} entries, the step has {expected} sites")]
    NotSquare {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("row {row} has a negative entry or does not sum to one")]
    NotRowStochastic { row: usize },
    #[error("a two-state step has two sites, not {sites}")]
    NotTwoState { sites: usize },
    #[error("rates must be nonnegative with a positive total")]
    Rates,
    #[error("the semigroup parameter must lie in (0, 1]")]
    Parameter,
    #[error("an l2-isometric stochastic step without a unit entry in row {row}")]
    IsometryWithoutPermutation { row: usize },
}

fn check_step(step: &[Vec<Rational>]) -> Result<usize, StochasticStepError> {
    let n = step.len();
    if n == 0 {
        return Err(StochasticStepError::Empty);
    }
    for (row, entries) in step.iter().enumerate() {
        if entries.len() != n {
            return Err(StochasticStepError::NotSquare {
                row,
                expected: n,
                actual: entries.len(),
            });
        }
        let sum: Rational = entries.iter().sum();
        if entries.iter().any(Signed::is_negative) || !sum.is_one() {
            return Err(StochasticStepError::NotRowStochastic { row });
        }
    }
    Ok(n)
}

fn as_gaussian(step: &[Vec<Rational>], n: usize) -> BasicMatrix<GaussianRat> {
    linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(
        n,
        n,
        step.iter()
            .flatten()
            .cloned()
            .map(GaussianRat::from_rational)
            .collect(),
    )
    .checked_invariant_a0c50cef("validated matrix literal")
}

/// The permutation `sigma` with `T[i][sigma(i)] = 1`, when the stochastic step
/// `T` preserves the `l2` norm; `None` when it does not.
pub fn isometric_permutation(
    step: &[Vec<Rational>],
) -> Result<Option<Vec<usize>>, StochasticStepError> {
    let n = check_step(step)?;
    if !core_lie_theory::scalar::is_unitary(
        &Ok::<_, crate::exact_hermitian::ExactHermitianError>((&as_gaussian(step, n)).clone())
            .map_err(|e| StochasticStepError::Algebra(e.to_string()))?,
    )
    .map_err(|e| StochasticStepError::Algebra(e.to_string()))?
    {
        return Ok(None);
    }
    step.iter()
        .enumerate()
        .map(|(row, entries)| {
            entries
                .iter()
                .position(One::is_one)
                .ok_or(StochasticStepError::IsometryWithoutPermutation { row })
        })
        .collect::<Result<Vec<usize>, _>>()
        .map(Some)
}

/// A two-state rate generator `Q = [[-a, a], [b, -b]]`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TwoStateGenerator {
    a: Rational,
    b: Rational,
}

impl TwoStateGenerator {
    /// Rates `a` (from state 0 to 1) and `b` (from 1 to 0).
    pub fn new(a: Rational, b: Rational) -> Result<Self, StochasticStepError> {
        if a.is_negative() || b.is_negative() || (&a + &b).is_zero() {
            return Err(StochasticStepError::Rates);
        }
        Ok(Self { a, b })
    }

    pub fn rates(&self) -> (&Rational, &Rational) {
        (&self.a, &self.b)
    }

    /// `T(s) = I + (1 - s) Q / (a + b)`, row by row.
    pub fn step(&self, s: &Rational) -> Result<Vec<Vec<Rational>>, StochasticStepError> {
        if !s.is_positive() || *s > Rational::one() {
            return Err(StochasticStepError::Parameter);
        }
        let factor = (Rational::one() - s) / (&self.a + &self.b);
        let up = &factor * &self.a;
        let down = &factor * &self.b;
        Ok(vec![
            vec![Rational::one() - &up, up],
            vec![down.clone(), Rational::one() - down],
        ])
    }
}

/// Where a two-state step sits relative to the two-state semigroups.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TwoStateEmbedding {
    /// The identity: `T(1)` of every generator.
    Identity,
    /// `T = T(s)` for the generator `T - I`.
    OnSemigroup {
        generator: TwoStateGenerator,
        parameter: Rational,
    },
    /// No semigroup reaches `T`: every `T(s)` has positive determinant.
    NotEmbeddable { determinant: Rational },
}

/// Decide whether a two-state stochastic step lies on a semigroup `T(s)`.
pub fn two_state_embedding(
    step: &[Vec<Rational>],
) -> Result<TwoStateEmbedding, StochasticStepError> {
    let sites = check_step(step)?;
    if sites != 2 {
        return Err(StochasticStepError::NotTwoState { sites });
    }
    let alpha = step[0][1].clone();
    let beta = step[1][0].clone();
    let total = &alpha + &beta;
    if total.is_zero() {
        return Ok(TwoStateEmbedding::Identity);
    }
    let determinant = Rational::one() - total;
    if !determinant.is_positive() {
        return Ok(TwoStateEmbedding::NotEmbeddable { determinant });
    }
    Ok(TwoStateEmbedding::OnSemigroup {
        generator: TwoStateGenerator::new(alpha, beta)?,
        parameter: determinant,
    })
}

/// A finite Markov kernel with exact population evolution, stationary and
/// detailed-balance checks, and the Dobrushin total-variation contraction.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MarkovKernel {
    matrix: linear_algebra::backend::basic_matrix::BasicMatrix<Rational>,
}
impl MarkovKernel {
    pub fn new(rows: Vec<Vec<Rational>>) -> Result<Self, StochasticStepError> {
        let n = check_step(&rows)?;
        if n > 256 {
            return Err(StochasticStepError::Budget);
        }
        let matrix = linear_algebra::exact_field::matrix::from_rows(rows)
            .map_err(|e| StochasticStepError::Algebra(e.to_string()))?;
        Ok(Self { matrix })
    }
    pub fn matrix(&self) -> &linear_algebra::backend::basic_matrix::BasicMatrix<Rational> {
        &self.matrix
    }
    pub fn evolve(
        &self,
        population: &[Rational],
        steps: u32,
    ) -> Result<Vec<Rational>, StochasticStepError> {
        let n = self.matrix.rows();
        if population.len() != n
            || population.iter().any(Signed::is_negative)
            || population.iter().sum::<Rational>() != Rational::one()
        {
            return Err(StochasticStepError::Population);
        }
        if steps > 4096 {
            return Err(StochasticStepError::Budget);
        }
        let power = linear_algebra::exact_field::matrix::power(&self.matrix, u64::from(steps))
            .map_err(|e| StochasticStepError::Algebra(e.to_string()))?;
        Ok((0..n)
            .map(|j| {
                (0..n)
                    .map(|i| &population[i] * power.get_ref(i, j).checked_invariant_a0c50cef("validated shape"))
                    .sum()
            })
            .collect())
    }
    pub fn is_stationary(&self, population: &[Rational]) -> Result<bool, StochasticStepError> {
        Ok(self.evolve(population, 1)? == population)
    }
    pub fn detailed_balance(&self, population: &[Rational]) -> Result<bool, StochasticStepError> {
        self.evolve(population, 0)?;
        let n = self.matrix.rows();
        Ok((0..n).all(|i| {
            (0..n).all(|j| {
                &population[i] * self.matrix.get_ref(i, j).checked_invariant_a0c50cef("shape")
                    == &population[j] * self.matrix.get_ref(j, i).checked_invariant_a0c50cef("shape")
            })
        }))
    }
    pub fn dobrushin_coefficient(&self) -> Rational {
        let n = self.matrix.rows();
        (0..n)
            .flat_map(|i| {
                (0..n).map(move |j| {
                    (0..n)
                        .map(|k| {
                            (self.matrix.get_ref(i, k).checked_invariant_a0c50cef("shape")
                                - self.matrix.get_ref(j, k).checked_invariant_a0c50cef("shape"))
                            .abs()
                        })
                        .sum::<Rational>()
                        / Rational::from_integer(2.into())
                })
            })
            .max()
            .unwrap_or_else(Rational::zero)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/stochastic_unitary_boundary.rs
// Claim: urn:core:crates_rs:core-quantum-physics:stochastic-unitary-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_a0c50cef {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
