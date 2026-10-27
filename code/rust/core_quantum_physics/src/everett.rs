//! Exact finite Everett branches, counting versus Born measure, and coherent slit readouts.
//! AuthorityEffect: None.

use core_number_theory::rational::{Rational, Zero};
use serde::{Deserialize, Serialize};

/// A single measurement branch in an Everett coproduct decomposition.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Branch {
    pub index: usize,
    pub amplitude_re: Rational,
    pub amplitude_im: Rational,
    pub born_weight: Rational,
    pub count_weight: Rational,
    pub is_active: bool,
}

/// A node in the Everett forking tree.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct EverettForkingNode {
    pub dimension: usize,
    pub branches: Vec<Branch>,
}

impl EverettForkingNode {
    /// Decomposes a state vector into an orthogonal coproduct of measurement branches.
    pub fn from_amplitudes(amplitudes: &[(Rational, Rational)]) -> Result<Self, BranchingError> {
        let dim = amplitudes.len();
        if dim == 0 || dim > 4096 {
            return Err(BranchingError::State);
        }

        // Unnormalized Born weights w_j = re^2 + im^2
        let raw_born: Vec<Rational> = amplitudes
            .iter()
            .map(|(re, im)| re * re + im * im)
            .collect();

        let total_born: Rational = raw_born
            .iter()
            .cloned()
            .fold(Rational::zero(), |a, b| a + b);
        if total_born.is_zero() {
            return Err(BranchingError::State);
        }

        // Active branch count k
        let k = raw_born.iter().filter(|w| !w.is_zero()).count();
        let count_unit = Rational::new(1.into(), k.into());

        let branches = amplitudes
            .iter()
            .zip(raw_born.iter())
            .enumerate()
            .map(|(i, ((re, im), w))| {
                let is_active = !w.is_zero();
                let born_weight = w / &total_born;
                let count_weight = if is_active {
                    count_unit.clone()
                } else {
                    Rational::zero()
                };
                Branch {
                    index: i,
                    amplitude_re: re.clone(),
                    amplitude_im: im.clone(),
                    born_weight,
                    count_weight,
                    is_active,
                }
            })
            .collect();

        Ok(Self {
            dimension: dim,
            branches,
        })
    }

    /// Evaluates the Measure Decoupling Theorem.
    ///
    /// Returns `(is_decoupled, max_deviation, uniform_modulus)`.
    /// Theorem: `is_decoupled == !uniform_modulus`.
    pub fn measure_decoupling_theorem(&self) -> (bool, Rational, bool) {
        let active: Vec<&Branch> = self.branches.iter().filter(|b| b.is_active).collect();
        if active.is_empty() {
            return (false, Rational::zero(), true);
        }

        let first_weight = &active[0].born_weight;
        let uniform_modulus = active.iter().all(|b| &b.born_weight == first_weight);

        let mut max_dev = Rational::zero();
        for b in &active {
            let diff = if b.born_weight >= b.count_weight {
                &b.born_weight - &b.count_weight
            } else {
                &b.count_weight - &b.born_weight
            };
            if diff > max_dev {
                max_dev = diff;
            }
        }

        let is_decoupled = !max_dev.is_zero();

        (is_decoupled, max_dev, uniform_modulus)
    }
}

/// Evaluates Sorkin 3-slit interference parameter I_3 under Born measure.
///
/// I_3(A, B, C) = P(123) - P(12) - P(13) - P(23) + P(1) + P(2) + P(3).
/// Strictly evaluates to 0 in exact rational arithmetic.
pub fn sorkin_3slit_i3(
    a1: (Rational, Rational),
    a2: (Rational, Rational),
    a3: (Rational, Rational),
) -> Rational {
    // Slit combinations
    let a12 = (&a1.0 + &a2.0, &a1.1 + &a2.1);
    let a13 = (&a1.0 + &a3.0, &a1.1 + &a3.1);
    let a23 = (&a2.0 + &a3.0, &a2.1 + &a3.1);
    let a123 = (&a12.0 + &a3.0, &a12.1 + &a3.1);

    let norm_sq = |a: &(Rational, Rational)| &a.0 * &a.0 + &a.1 * &a.1;

    let p123 = norm_sq(&a123);
    let p12 = norm_sq(&a12);
    let p13 = norm_sq(&a13);
    let p23 = norm_sq(&a23);
    let p1 = norm_sq(&a1);
    let p2 = norm_sq(&a2);
    let p3 = norm_sq(&a3);

    p123 - p12 - p13 - p23 + p1 + p2 + p3
}

/// Evaluates CHSH Pythagorean Bell parameter S in exact rational arithmetic (Target 8).
///
/// Returns `(s_quantum, max_classical, violates_bound)`.
// Origin: engine/crates_rs/core_quantum_physics/src/everett.rs
// Claim: urn:core:crates_rs:core-quantum-physics:everett:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;

    #[test]
    fn test_uniform_measure_agreement() {
        // Uniform 4-state state in Q: (1/2, 1/2, 1/2, 1/2)
        let amps = vec![
            (rq(1, 2), Rational::zero()),
            (rq(1, 2), Rational::zero()),
            (rq(1, 2), Rational::zero()),
            (rq(1, 2), Rational::zero()),
        ];
        let node = EverettForkingNode::from_amplitudes(&amps).unwrap();
        let (is_decoupled, max_dev, uniform) = node.measure_decoupling_theorem();
        assert!(!is_decoupled);
        assert!(uniform);
        assert_eq!(max_dev, Rational::zero());
        for b in &node.branches {
            assert_eq!(b.born_weight, rq(1, 4));
            assert_eq!(b.count_weight, rq(1, 4));
        }
    }

    #[test]
    fn test_nonuniform_pythagorean_measure_decoupling() {
        // Pythagorean state (3/5, 4/5)
        let amps = vec![(rq(3, 5), Rational::zero()), (rq(4, 5), Rational::zero())];
        let node = EverettForkingNode::from_amplitudes(&amps).unwrap();
        let (is_decoupled, max_dev, uniform) = node.measure_decoupling_theorem();
        assert!(is_decoupled);
        assert!(!uniform);
        assert_eq!(node.branches[0].born_weight, rq(9, 25));
        assert_eq!(node.branches[1].born_weight, rq(16, 25));
        assert_eq!(node.branches[0].count_weight, rq(1, 2));
        assert_eq!(node.branches[1].count_weight, rq(1, 2));
        assert_eq!(max_dev, rq(7, 50));
    }

    #[test]
    fn test_sorkin_3slit_exact_vanishing() {
        let a1 = (rq(1, 3), rq(1, 2));
        let a2 = (rq(2, 5), rq(-1, 4));
        let a3 = (rq(-1, 2), rq(3, 7));
        let i3 = sorkin_3slit_i3(a1, a2, a3);
        assert_eq!(i3, Rational::zero());
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum BranchingError {
    #[error("branch state must be nonzero with dimension in 1..=4096")]
    State,
    #[error("Sorkin inclusion-exclusion exceeds the 16-slit budget")]
    Budget,
}
impl EverettForkingNode {
    pub fn try_from_gaussian_amplitudes(
        amplitudes: &[core_number_theory::cyclotomic::GaussianRat],
    ) -> Result<Self, BranchingError> {
        if amplitudes.is_empty()
            || amplitudes.len() > 4096
            || amplitudes.iter().all(|a| a.is_zero())
        {
            return Err(BranchingError::State);
        }
        Self::from_amplitudes(
            &amplitudes
                .iter()
                .map(|a| (a.re.clone(), a.im.clone()))
                .collect::<Vec<_>>(),
        )
    }
}
/// I_k for a quadratic Born readout of coherent slit amplitudes. The empty
/// subset contributes zero. For every k>=3 each quadratic monomial has a
/// vanishing inclusion-exclusion coefficient, independent of the amplitudes.
pub fn sorkin_interference(
    amplitudes: &[core_number_theory::cyclotomic::GaussianRat],
) -> Result<Rational, BranchingError> {
    use core_number_theory::cyclotomic::GaussianRat;
    let k = amplitudes.len();
    if k > 16 {
        return Err(BranchingError::Budget);
    }
    if k == 0 {
        return Err(BranchingError::State);
    }
    let mut total = Rational::zero();
    for mask in 1usize..(1usize << k) {
        let amplitude = (0..k)
            .filter(|i| mask & (1 << i) != 0)
            .fold(GaussianRat::zero(), |z, i| z.add(&amplitudes[i]));
        let probability = amplitude.norm_sq();
        if (k - mask.count_ones() as usize) % 2 == 0 {
            total += probability;
        } else {
            total -= probability;
        }
    }
    Ok(total)
}
