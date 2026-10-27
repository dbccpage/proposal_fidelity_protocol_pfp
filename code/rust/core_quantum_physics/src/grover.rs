// AuthorityEffect: None.

//! Exact algebraic Grover search via Householder reflections and Chebyshev recurrence.
//!
//! Provides:
//!   - Exact rational Householder reflection operators:
//!       R_w = I - 2 |w><w| (oracle reflection)
//!       R_s = 2 |s><s| - I (diffusion reflection)
//!   - Exact matrix-vector evolution: G |s> = R_s R_w |s> = |w> in 1 step for N=4.
//!   - Exact Chebyshev scalar recurrence with period 6 in Q.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_95b9ff5e<T> {
    fn checked_invariant_95b9ff5e(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_95b9ff5e<T> for Option<T> {
    #[inline]
    fn checked_invariant_95b9ff5e(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_95b9ff5e<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_95b9ff5e(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_bigint::BigInt;
use core_number_theory::rational::{r_one, r_zero, ri, rq, Rational};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

/// Exact Grover recurrence state at step k for N=4.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GroverRecurrenceN4 {
    pub amplitudes: Vec<Rational>,
    pub probabilities: Vec<Rational>,
    pub period: usize,
    pub exact_one_step_success: bool,
}

impl GroverRecurrenceN4 {
    /// Compute exact Chebyshev orbit for N=4 up to `steps`.
    /// Recurrence: x_{k+1} = 2*(1 - 2/N)*x_k - x_{k-1} = x_k - x_{k-1}.
    pub fn compute(steps: usize) -> Self {
        let mut amps = Vec::with_capacity(steps + 1);
        let mut probs = Vec::with_capacity(steps + 1);

        // x_0 = 1/2
        amps.push(rq(1, 2));
        probs.push(rq(1, 4));

        if steps >= 1 {
            // x_1 = 1
            amps.push(rq(1, 1));
            probs.push(rq(1, 1));
        }

        for k in 1..steps {
            // x_{k+1} = x_k - x_{k-1}
            let next_amp = &amps[k] - &amps[k - 1];
            let next_prob = &next_amp * &next_amp;
            amps.push(next_amp);
            probs.push(next_prob);
        }

        let is_one_step = if steps >= 1 {
            probs[1] == rq(1, 1)
        } else {
            false
        };

        Self {
            amplitudes: amps,
            probabilities: probs,
            period: 6,
            exact_one_step_success: is_one_step,
        }
    }
}

/// Exact Householder reflection matrix operator simulation on Q^4.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ExactGroverHouseholderN4 {
    pub oracle_reflection: BasicMatrix<Rational>,
    pub diffusion_reflection: BasicMatrix<Rational>,
    pub grover_step_matrix: BasicMatrix<Rational>,
    pub initial_state: Vec<Rational>,
    pub step1_state: Vec<Rational>,
    pub step1_target_probability: Rational,
    pub exact_one_step_success: bool,
}

impl ExactGroverHouseholderN4 {
    /// Constructs and executes the exact Householder reflection Grover search for N=4 and target w.
    pub fn run(target: usize) -> Self {
        assert!(target < 4, "target must be in 0..4");
        let model = GroverInstance::new(4, BTreeSet::from([target])).checked_invariant_95b9ff5e("fixed declaration");
        let iterate = model.iterate().checked_invariant_95b9ff5e("fixed dimension");
        let r_w = iterate.oracle;
        let r_s = iterate.diffusion;
        let g_op = iterate.step;
        let psi_0 = vec![rq(1, 2); 4];
        let psi_1 = mx::multiply_vector(&g_op, &psi_0).checked_invariant_95b9ff5e("fixed dimension");

        // Target probability |psi_1[target]|^2
        let prob_target = &psi_1[target] * &psi_1[target];
        let is_one_step = prob_target == r_one();

        Self {
            oracle_reflection: r_w,
            diffusion_reflection: r_s,
            grover_step_matrix: g_op,
            initial_state: psi_0,
            step1_state: psi_1,
            step1_target_probability: prob_target,
            exact_one_step_success: is_one_step,
        }
    }
}

use core_number_theory::cyclotomic::Cyc8;

/// Exact Grover search over quadratic extension field Q(sqrt(2)) for N=2.
/// Demonstrates genuine algebraic quadratic extension arithmetic without floating point.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ExactGroverQExtensionN2 {
    pub initial_state: [Cyc8; 2],
    pub oracle_reflection: BasicMatrix<Cyc8>,
    pub diffusion_reflection: BasicMatrix<Cyc8>,
    pub grover_step_matrix: BasicMatrix<Cyc8>,
    pub step1_state: [Cyc8; 2],
    pub target_probability_all_steps: Rational,
    pub chebyshev_recurrence_satisfied: bool,
    pub exact_period: usize,
}

impl ExactGroverQExtensionN2 {
    pub fn run(target: usize) -> Self {
        assert!(target < 2, "target must be in 0..2");
        let psi_0 = [Cyc8::inv_sqrt2(), Cyc8::inv_sqrt2()];
        let r_w = mx::from_fn(2, 2, |r, c| {
            if r != c {
                Cyc8::zero()
            } else if r == target {
                Cyc8::one().neg()
            } else {
                Cyc8::one()
            }
        })
        .checked_invariant_95b9ff5e("fixed dimension");
        let r_s = BasicMatrix::from_row_major(
            2,
            2,
            vec![Cyc8::zero(), Cyc8::one(), Cyc8::one(), Cyc8::zero()],
        )
        .checked_invariant_95b9ff5e("fixed shape");
        let g_op = mx::multiply(&r_s, &r_w).checked_invariant_95b9ff5e("fixed dimension");
        let psi_1: [Cyc8; 2] = mx::multiply_vector(&g_op, &psi_0)
            .checked_invariant_95b9ff5e("fixed dimension")
            .try_into()
            .checked_invariant_95b9ff5e("two entries");

        // Target probability: |psi_1[target]|^2 in Q
        let target_norm_sq = psi_1[target].mul(&psi_1[target].conj());
        let target_prob = target_norm_sq
            .as_rational()
            .checked_invariant_95b9ff5e("the computed N=2 norm is rational");

        // Chebyshev recurrence test: x_{k+1} = 2*cos(pi/2)*x_k - x_{k-1} = -x_{k-1}
        // with x_0 = 1/sqrt(2), x_1 = 1/sqrt(2), x_2 = -1/sqrt(2), x_3 = -1/sqrt(2), x_4 = 1/sqrt(2)
        let mut orbit = vec![psi_0.clone(), psi_1.clone()];
        for k in 1..4 {
            let next: [Cyc8; 2] = mx::multiply_vector(&g_op, &orbit[k])
                .checked_invariant_95b9ff5e("fixed dimension")
                .try_into()
                .checked_invariant_95b9ff5e("two entries");
            orbit.push(next);
        }
        let recurrence_ok = (1..4).all(|k| orbit[k + 1][target] == orbit[k - 1][target].neg());

        Self {
            initial_state: psi_0,
            oracle_reflection: r_w,
            diffusion_reflection: r_s,
            grover_step_matrix: g_op,
            step1_state: psi_1,
            target_probability_all_steps: target_prob,
            chebyshev_recurrence_satisfied: recurrence_ok,
            exact_period: 4,
        }
    }
}

/// Refusals of the finite rational Grover model.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GroverError {
    #[error("the carrier and marked set must be nonempty")]
    Empty,
    #[error("marked label {label} is outside {size} labels")]
    Label { label: usize, size: usize },
    #[error("the declared operation exceeds the finite budget")]
    Budget,
    #[error(transparent)]
    Matrix(#[from] linear_algebra::exact_field::ExactFieldError),
}

/// Rational Grover iteration on a declared marked subset. Amplitudes use the
/// unnormalised uniform vector; their squared norm is exactly `n`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GroverInstance {
    n: usize,
    marked: BTreeSet<usize>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GroverIterate {
    pub oracle: BasicMatrix<Rational>,
    pub diffusion: BasicMatrix<Rational>,
    pub step: BasicMatrix<Rational>,
}

impl GroverInstance {
    /// Exact oracle, Householder diffusion and their product on the declared
    /// rational carrier. Normalized amplitudes may require a square root of n;
    /// the iterate itself always lies in Q.
    pub fn iterate(&self) -> Result<GroverIterate, GroverError> {
        if self.n > 256 {
            return Err(GroverError::Budget);
        }
        let oracle = mx::from_fn(self.n, self.n, |r, c| {
            if r != c {
                r_zero()
            } else if self.marked.contains(&r) {
                ri(-1)
            } else {
                r_one()
            }
        })?;
        let two_over_n = Rational::new(BigInt::from(2), BigInt::from(self.n));
        let diffusion = mx::from_fn(self.n, self.n, |r, c| {
            &two_over_n - if r == c { r_one() } else { r_zero() }
        })?;
        let step = mx::multiply(&diffusion, &oracle)?;
        Ok(GroverIterate {
            oracle,
            diffusion,
            step,
        })
    }
    pub fn new(n: usize, marked: BTreeSet<usize>) -> Result<Self, GroverError> {
        if n == 0 || marked.is_empty() {
            return Err(GroverError::Empty);
        }
        if n > 4096 {
            return Err(GroverError::Budget);
        }
        if let Some(&label) = marked.iter().find(|&&label| label >= n) {
            return Err(GroverError::Label { label, size: n });
        }
        Ok(Self { n, marked })
    }

    pub fn size(&self) -> usize {
        self.n
    }
    pub fn marked(&self) -> &BTreeSet<usize> {
        &self.marked
    }

    /// `G = ((2/n) J - I) (I - 2 P_marked)`, over `Q`.
    pub fn step_matrix(
        &self,
    ) -> Result<linear_algebra::backend::basic_matrix::BasicMatrix<Rational>, GroverError> {
        if self.n > 256 {
            return Err(GroverError::Budget);
        }
        let twice_over_n = Rational::new(BigInt::from(2), BigInt::from(self.n));
        let data = (0..self.n)
            .flat_map(|i| {
                let twice_over_n = twice_over_n.clone();
                (0..self.n).map(move |j| {
                    let d = &twice_over_n - if i == j { r_one() } else { r_zero() };
                    if self.marked.contains(&j) {
                        -d
                    } else {
                        d
                    }
                })
            })
            .collect();
        linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(self.n, self.n, data)
            .map_err(|_| GroverError::Budget)
    }

    /// Apply the two Householder reflections without building a dense matrix.
    pub fn amplitudes(&self, steps: usize) -> Result<Vec<Rational>, GroverError> {
        if steps > 4096 || self.n.checked_mul(steps).unwrap_or(usize::MAX) > 1 << 20 {
            return Err(GroverError::Budget);
        }
        let mut state = vec![r_one(); self.n];
        let twice_over_n = Rational::new(BigInt::from(2), BigInt::from(self.n));
        for _ in 0..steps {
            for &j in &self.marked {
                state[j] = -&state[j];
            }
            let sum: Rational = state.iter().cloned().sum();
            let twice_mean = &twice_over_n * sum;
            for x in &mut state {
                *x = &twice_mean - &*x;
            }
        }
        Ok(state)
    }

    /// `(1 - T_(2k+1)(1-2M/n))/2`, computed by the Chebyshev recurrence.
    pub fn success_probability(&self, k: usize) -> Result<Rational, GroverError> {
        if k > 4096 {
            return Err(GroverError::Budget);
        }
        let c = r_one() - Rational::new(BigInt::from(2 * self.marked.len()), BigInt::from(self.n));
        let (mut a, mut b) = (r_one(), c.clone());
        for _ in 1..2 * k + 1 {
            let next = ri(2) * &c * &b - &a;
            a = b;
            b = next;
        }
        Ok((r_one() - b) * rq(1, 2))
    }

    /// First local maximum in the declared search budget. A flat orbit returns
    /// zero; exhaustion is a typed refusal, not a claimed optimum.
    pub fn optimal_iterations(&self, budget: usize) -> Result<usize, GroverError> {
        if budget > 4096 {
            return Err(GroverError::Budget);
        }
        let mut p = self.success_probability(0)?;
        for k in 0..budget {
            let next = self.success_probability(k + 1)?;
            if next <= p {
                return Ok(k);
            }
            p = next;
        }
        Err(GroverError::Budget)
    }

    /// Exact one-step success (including the already fully marked carrier).
    pub fn exact_one_step(&self) -> bool {
        self.n == self.marked.len() || self.n == 4 * self.marked.len()
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/grover.rs
// Claim: urn:core:crates_rs:core-quantum-physics:grover:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_grover_n4_exact_chebyshev_period6() {
        let g = GroverRecurrenceN4::compute(12);
        assert!(g.exact_one_step_success);
        assert_eq!(g.probabilities[1], r_one());
        assert_eq!(g.probabilities[0], rq(1, 4));
        assert_eq!(g.probabilities[2], rq(1, 4));
        assert_eq!(g.probabilities[3], rq(1, 4));
        assert_eq!(g.probabilities[4], r_one());
        assert_eq!(g.probabilities[5], rq(1, 4));
        assert_eq!(g.probabilities[6], rq(1, 4));

        // Test period 6 equality: x_k == x_{k+6}
        for k in 0..=6 {
            assert_eq!(g.amplitudes[k], g.amplitudes[k + 6]);
        }
    }

    #[test]
    fn test_grover_n4_exact_householder_reflections() {
        for target in 0..4 {
            let sim = ExactGroverHouseholderN4::run(target);
            assert!(sim.exact_one_step_success);
            assert_eq!(sim.step1_target_probability, r_one());
            assert_eq!(sim.step1_state[target], r_one());
            for i in 0..4 {
                if i != target {
                    assert_eq!(sim.step1_state[i], r_zero());
                }
            }
        }
    }

    #[test]
    fn test_grover_n2_exact_q_extension() {
        for target in 0..2 {
            let sim = ExactGroverQExtensionN2::run(target);
            assert_eq!(sim.target_probability_all_steps, rq(1, 2));
            assert!(sim.chebyshev_recurrence_satisfied);
            assert_eq!(sim.exact_period, 4);
        }
    }
}
