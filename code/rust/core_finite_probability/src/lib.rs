//! `core_finite_probability` -- exact finite probability for the engine.
//!
//! Finite probability is pure mathematics, so it lives below the physics and the programme
//! crates that use it. Every quantity is exact: masses, kernels, tables and majorization
//! data are `BigRational`; entropies are exact rational combinations of logarithms of
//! primes; there is no floating point and no tolerance anywhere. Failures are typed values
//! and no function panics on caller data.
//!
//! | module | content |
//! |---|---|
//! | [`classical_instrument`] | finite classical instruments (composition, coarse-graining, adaptive control) and conditional boxes with no-signalling and hidden-variable questions kept apart |
//! | [`error`] | the refusals of the finite-set, simplex and kernel layer |
//! | [`finite_set`] | the carrier `Fin n` |
//! | [`joint_table`] | joint tables: marginals, conditionals, independence decided several independent ways, couplings and Frechet bounds, local maps |
//! | [`log_form`] | entropies as exact rational combinations of logarithms of primes: Shannon, relative, Renyi, mutual; certified enclosures and ordering |
//! | [`majorization`] | the majorization preorder on probability vectors, thermal ladders, Nielsen's criterion, T-transform chains |
//! | [`markov_chain`] | finite chains: classes, recurrence, period, stationary laws, absorption, hitting and return times, exact mixing |
//! | [`simplex`] | probability simplices: events, expectations, total variation, products, mixtures |
//! | [`stochastic_map`] | row-stochastic maps: the category of finite kernels, its monoidal (Markov) structure, Bayesian inversion, the Dobrushin coefficient |
//!
//! Exact linear algebra (rank, kernel, `solve_in_image`) is `core_linear_algebra`'s; the
//! exact scalar is `core_number_theory`'s. This crate owns the probabilistic structure built
//! on them and carries no private copy of either.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_691bfd89;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_691bfd89<T> = std::result::Result<T, BoundaryError_691bfd89>;
pub mod classical_instrument;
pub mod error;
pub mod finite_set;
pub mod joint_table;
pub mod log_form;
pub mod majorization;
pub mod markov_chain;
pub mod paired_tests;
pub mod simplex;
pub mod stochastic_map;

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod test_support;

pub mod finite_valuation;

pub mod local_deterministic;
pub mod marginal_compatibility;
pub mod signed_representation;


/// A finite probability mass is a nonempty list of integer weights that sum
/// to a positive normalizer.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteMassWitness {
    bins: u32,
    total: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FiniteMassError {
    Empty,
    ZeroNormalizer,
    Overflow,
    NotNormalized { total: u64, normalizer: u64 },
}

// Origin: engine/crates_rs/core_finite_probability/src/lib.rs
// Claim: urn:core:crates_rs:core-finite-probability:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FiniteMassError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FiniteMassError {}

impl FiniteMassWitness {
    pub fn admit(weights: &[u64], normalizer: u64) -> Result<Self, FiniteMassError> {
        if weights.is_empty() {
            return Err(FiniteMassError::Empty);
        }
        if normalizer == 0 {
            return Err(FiniteMassError::ZeroNormalizer);
        }
        let mut total = 0u64;
        for weight in weights {
            total = total.checked_add(*weight).ok_or(FiniteMassError::Overflow)?;
        }
        if total != normalizer {
            return Err(FiniteMassError::NotNormalized { total, normalizer });
        }
        let bins = u32::try_from(weights.len()).map_err(|_| FiniteMassError::Overflow)?;
        Ok(Self { bins, total })
    }

    pub fn total(&self) -> u64 {
        self.total
    }
}

#[cfg(test)]
mod finite_mass_witness_tests {
    use super::*;

    #[test]
    fn weights_sum_to_the_normalizer() {
        let admitted = FiniteMassWitness::admit(&[1, 2, 3], 6);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.total()), Some(6));
        assert!(matches!(
            FiniteMassWitness::admit(&[1, 2], 4),
            Err(FiniteMassError::NotNormalized {
                total: 3,
                normalizer: 4
            })
        ));
    }
}
