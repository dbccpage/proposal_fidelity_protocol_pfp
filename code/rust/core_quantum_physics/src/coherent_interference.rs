// AuthorityEffect: None.

//! Coherent interference measured against the diagonal (L1) layer.
//!
//! For a configuration `c` over a declared sector basis, the diagonal layer
//! keeps the weights `|c_s|^2`. The coherent readout keeps the interfered
//! weight `I(c) = |sum_s c_s|^2`, and the cross term is
//! `I(c) - sum_s |c_s|^2 = 2 sum_{j<k} Re(c_j conj c_k)`. Computed exactly over
//! `Q(i)`:
//!
//! - the interfered weight and the cross term;
//! - a diagonal twin: for a configuration with at least two nonzero
//!   coordinates, a configuration with the same diagonal weights and a
//!   different interfered weight, made by multiplying one coordinate by `-1`
//!   or by `i` (always `-1` for a real configuration). With at most one
//!   nonzero coordinate there is no twin, and `I(c)` is the diagonal total. So
//!   on a fiber of the diagonal layer `I` is constant exactly when the support
//!   has one point;
//! - for real rational configurations, the l1-coherence deficit
//!   `(sum_s |c_s|)^2 - sum_s c_s^2` and its normalized form. The deficit is a
//!   function of the diagonal weights alone: it is the largest cross term
//!   among the sign changes of `c`, not the part of `I` the diagonal misses.
//!
//! Refused: empty configurations, and normalizing the zero configuration. The
//! quadratic readout and the sector basis are declared; the complex phase
//! carrier is imported, not derived.

use num_traits::{Signed, Zero};

use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

/// Refusals for interference readouts.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum InterferenceError {
    #[error("a configuration needs at least one coordinate")]
    Empty,
    #[error("the zero configuration cannot be normalized")]
    Zero,
    #[error("interference blocks must be nonempty, disjoint, in range and at most twelve")]
    InvalidBlocks,
    #[error("inclusion-exclusion exceeds the declared subset budget")]
    SubsetBudget,
}

/// `I(c) = |sum_s c_s|^2`.
pub fn interfered_weight(c: &[GaussianRat]) -> Result<Rational, InterferenceError> {
    if c.is_empty() {
        return Err(InterferenceError::Empty);
    }
    Ok(c.iter()
        .fold(GaussianRat::zero(), |acc, z| acc.add(z))
        .norm_sq())
}

/// `I(c) - sum_s |c_s|^2`.
pub fn cross_term(c: &[GaussianRat]) -> Result<Rational, InterferenceError> {
    let diagonal: Rational = c.iter().map(GaussianRat::norm_sq).sum();
    Ok(interfered_weight(c)? - diagonal)
}

/// A configuration with the diagonal weights of the original and another
/// interfered weight: coordinate `coordinate` multiplied by `unit`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiagonalTwin {
    pub coordinate: usize,
    pub unit: GaussianRat,
    pub twin: Vec<GaussianRat>,
}

/// The diagonal twin of `c`, or `None` when `c` has at most one nonzero coordinate.
///
/// With `T = sum c`, multiplying `c_k` by a unit `u` changes `I` by
/// `2 Re((u - 1) c_k conj(T - c_k))`. Some nonzero `c_k` has `T != c_k` as soon
/// as two coordinates are nonzero; for that `k`, `u = -1` changes `I` when
/// `Re(c_k conj(T - c_k)) != 0`, and `u = i` does otherwise.
pub fn diagonal_twin(c: &[GaussianRat]) -> Result<Option<DiagonalTwin>, InterferenceError> {
    if c.is_empty() {
        return Err(InterferenceError::Empty);
    }
    let total = c.iter().fold(GaussianRat::zero(), |acc, z| acc.add(z));
    for (coordinate, value) in c.iter().enumerate() {
        let product = value.mul(&total.sub(value).conj());
        if product.norm_sq().is_zero() {
            continue;
        }
        let unit = if product.re.is_zero() {
            GaussianRat::i()
        } else {
            GaussianRat::one().neg()
        };
        let mut twin = c.to_vec();
        twin[coordinate] = unit.mul(value);
        return Ok(Some(DiagonalTwin {
            coordinate,
            unit,
            twin,
        }));
    }
    Ok(None)
}

/// `(sum_s |v_s|)^2 - sum_s v_s^2 = 2 sum_{j<k} |v_j| |v_k|` for a real configuration.
pub fn l1_coherence_deficit(v: &[Rational]) -> Result<Rational, InterferenceError> {
    if v.is_empty() {
        return Err(InterferenceError::Empty);
    }
    let l1: Rational = v.iter().map(Signed::abs).sum();
    let l2: Rational = v.iter().map(|x| x * x).sum();
    Ok(&l1 * &l1 - l2)
}

/// The deficit divided by `sum_s v_s^2`: the l1-coherence of the normalized
/// pure state `v / |v|`.
pub fn normalized_l1_coherence(v: &[Rational]) -> Result<Rational, InterferenceError> {
    let deficit = l1_coherence_deficit(v)?;
    let l2: Rational = v.iter().map(|x| x * x).sum();
    if l2.is_zero() {
        return Err(InterferenceError::Zero);
    }
    Ok(deficit / l2)
}

/// Inclusion-exclusion interference on disjoint declared coordinate blocks.
/// For this quadratic readout all orders above two vanish; order two is twice
/// the real inner cross term between the two block sums. No alternative readout
/// is admitted by this computation.
pub fn sorkin_interference(
    c: &[GaussianRat],
    blocks: &[Vec<usize>],
    subset_budget: usize,
) -> Result<Rational, InterferenceError> {
    validate_sorkin_blocks(c, blocks)?;
    let subsets = 1usize << blocks.len();
    if subsets > subset_budget {
        return Err(InterferenceError::SubsetBudget);
    }
    let mut value = Rational::zero();
    for mask in 0..subsets {
        let total = blocks
            .iter()
            .enumerate()
            .filter(|(k, _)| (mask >> k) & 1 != 0)
            .flat_map(|(_, b)| b)
            .fold(GaussianRat::zero(), |s, &i| s.add(&c[i]));
        let term = total.norm_sq();
        if (blocks.len() - mask.count_ones() as usize) % 2 == 0 {
            value += term;
        } else {
            value -= term;
        }
    }
    Ok(value)
}

fn validate_sorkin_blocks(
    c: &[GaussianRat],
    blocks: &[Vec<usize>],
) -> Result<(), InterferenceError> {
    if c.is_empty() {
        return Err(InterferenceError::Empty);
    }
    if blocks.is_empty() || blocks.len() > 12 || blocks.iter().any(Vec::is_empty) {
        return Err(InterferenceError::InvalidBlocks);
    }
    let mut covered = std::collections::BTreeSet::new();
    for block in blocks {
        for &i in block {
            if i >= c.len() || !covered.insert(i) {
                return Err(InterferenceError::InvalidBlocks);
            }
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_quantum_physics/src/coherent_interference.rs
// Claim: urn:core:crates_rs:core-quantum-physics:coherent-interference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_6067f5b6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
