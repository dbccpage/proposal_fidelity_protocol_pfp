//! Combinatorial configurations and certificates for Mutually Unbiased Bases (MUB).
//!
//! AuthorityEffect: None.
//!
//! Provides finite geometric partitions, operator bundle certificates,
//! and verification routines for discrete MUB configurations without host I/O.

use crate::weyl_systems::{DiscreteWeylSystem, PhasePoint};
use std::collections::BTreeSet;
use thiserror::Error;

/// Mandatory authority effect declaration.
pub const AUTHORITY_EFFECT: &str = "AuthorityEffect: None";

/// Errors occurring during MUB configuration analysis.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum MubConfigError {
    #[error("dimension must be >= 2")]
    InvalidDimension,
    #[error("bundle count {found} exceeds the maximum theoretical bound {bound} for dimension {dim}")]
    TooManyBundles { found: usize, bound: usize, dim: usize },
    #[error("bundle {index} contains {found} operators, expected {expected}")]
    InvalidBundleSize { index: usize, found: usize, expected: usize },
    #[error("bundle {0} contains non-commuting operators: phase points {1:?} and {2:?}")]
    NonCommutingBundle(usize, PhasePoint, PhasePoint),
    #[error("bundles are not disjoint: phase point {0:?} appears in multiple bundles")]
    NonDisjointBundles(PhasePoint),
    #[error("operator bundle contains the trivial identity phase point (0, 0)")]
    ContainsIdentity,
}

/// A certified combinatorial MUB configuration representing the operator-space partition.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MubOperatorConfiguration {
    dim: usize,
    /// Bundles of non-identity phase points. For a complete MUB system in prime dimension $p$,
    /// there are $p+1$ bundles of size $p-1$.
    bundles: Vec<Vec<PhasePoint>>,
}

impl MubOperatorConfiguration {
    fn verify_bundle_commutativity(
        weyl: &DiscreteWeylSystem,
        index: usize,
        bundle: &[PhasePoint],
    ) -> Result<(), MubConfigError> {
        // Verify mutual commutativity within the bundle
        for j in 0..bundle.len() {
            for k in (j + 1)..bundle.len() {
                let u = bundle[j];
                let v = bundle[k];
                if !weyl.commutes(u, v).map_err(|_| MubConfigError::InvalidDimension)? {
                    return Err(MubConfigError::NonCommutingBundle(index, u, v));
                }
            }
        }
        Ok(())
    }

    /// Constructs and validates a MUB operator configuration.
    pub fn new(dim: usize, bundles: Vec<Vec<PhasePoint>>) -> Result<Self, MubConfigError> {
        if dim < 2 {
            return Err(MubConfigError::InvalidDimension);
        }
        let max_bound = dim + 1;
        if bundles.len() > max_bound {
            return Err(MubConfigError::TooManyBundles {
                found: bundles.len(),
                bound: max_bound,
                dim,
            });
        }

        let weyl = DiscreteWeylSystem::new(dim).map_err(|_| MubConfigError::InvalidDimension)?;
        let expected_size = dim - 1;
        let mut seen = BTreeSet::new();
        let identity = PhasePoint::new(0, 0);

        for (i, bundle) in bundles.iter().enumerate() {
            if bundle.len() != expected_size {
                return Err(MubConfigError::InvalidBundleSize {
                    index: i,
                    found: bundle.len(),
                    expected: expected_size,
                });
            }

            for &pt in bundle {
                if pt == identity {
                    return Err(MubConfigError::ContainsIdentity);
                }
                if !seen.insert(pt) {
                    return Err(MubConfigError::NonDisjointBundles(pt));
                }
            }

            Self::verify_bundle_commutativity(&weyl, i, bundle)?;
        }

        Ok(Self { dim, bundles })
    }

    /// Dimension of the system.
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// Number of bases/bundles in this configuration.
    pub fn num_bases(&self) -> usize {
        self.bundles.len()
    }

    /// Checks if this is a complete MUB configuration ($d+1$ bases).
    pub fn is_complete(&self) -> bool {
        self.bundles.len() == self.dim + 1
    }

    /// Operator bundles.
    pub fn bundles(&self) -> &[Vec<PhasePoint>] {
        &self.bundles
    }

    /// Builds the canonical complete MUB configuration for prime dimension $p$.
    pub fn canonical_prime(p: usize) -> Result<Self, MubConfigError> {
        let weyl = DiscreteWeylSystem::new(p).map_err(|_| MubConfigError::InvalidDimension)?;
        let rays = weyl.isotropic_rays().map_err(|_| MubConfigError::InvalidDimension)?;

        let origin = PhasePoint::new(0, 0);
        let bundles: Vec<Vec<PhasePoint>> = rays
            .into_iter()
            .map(|ray| ray.into_iter().filter(|&pt| pt != origin).collect())
            .collect();

        Self::new(p, bundles)
    }
}

/// Theoretical upper bound on the number of MUBs in dimension $d$: $d + 1$.
pub fn mub_theoretical_upper_bound(dim: usize) -> usize {
    dim + 1
}

// Origin: engine/crates_rs/core_combinatorics/src/mub_configurations.rs
// Claim: urn:core:crates_rs:core-combinatorics:mub-configurations:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_canonical_mub_configurations_prime() {
        for p in [2, 3, 5, 7] {
            let config = MubOperatorConfiguration::canonical_prime(p).unwrap();
            assert_eq!(config.dim(), p);
            assert_eq!(config.num_bases(), p + 1);
            assert!(config.is_complete());

            // Total operators across all bundles is (p+1) * (p-1) = p^2 - 1
            let total_ops: usize = config.bundles().iter().map(|b| b.len()).sum();
            assert_eq!(total_ops, p * p - 1);
        }
    }

    #[test]
    fn test_mub_theoretical_upper_bound() {
        assert_eq!(mub_theoretical_upper_bound(2), 3);
        assert_eq!(mub_theoretical_upper_bound(3), 4);
        assert_eq!(mub_theoretical_upper_bound(6), 7);
    }

    #[test]
    fn test_non_disjoint_bundle_refusal() {
        let pt1 = PhasePoint::new(0, 1);
        // Duplicate pt1 across bundles
        let bundles = vec![vec![pt1], vec![pt1]];
        assert!(matches!(
            MubOperatorConfiguration::new(2, bundles),
            Err(MubConfigError::NonDisjointBundles(_))
        ));
    }
}
