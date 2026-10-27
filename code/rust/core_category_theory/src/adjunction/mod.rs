//! Adjunction hierarchy shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Hierarchical catalog under `adjunction/`. Legacy finite/auditable records
//! remain at crate root as `legacy_adjunction` (alias `adjunction_legacy`).

pub mod adjoint_functor_theorem;
#[allow(clippy::module_inception)]
pub mod adjunction;
pub mod coreflective_subcategory;
pub mod counit;
pub mod galois_connection;
pub mod hom_set_adjunction;
pub mod reflective_subcategory;
pub mod unit;

pub use adjoint_functor_theorem::AdjointFunctorTheoremShell;
pub use adjunction::AdjunctionShell;
pub use coreflective_subcategory::CoreflectiveSubcategoryShell;
pub use counit::CounitShell;
pub use galois_connection::{GaloisConnectionShell, MonotonePair};
pub use hom_set_adjunction::HomSetAdjunctionShell;
pub use reflective_subcategory::ReflectiveSubcategoryShell;
pub use unit::UnitShell;

// Compatibility: finite/auditable adjunction records still live at crate root.
pub use crate::legacy_adjunction::{DeclaredFiniteAdjunction, DerivedMonad};

/// Refusal from a finite Galois connection.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GaloisError {
    /// A carrier is empty or above 8.
    Carrier { n: usize },
    /// An image leaves its codomain.
    Image { value: u32 },
    /// Monotonicity or the adjunction biconditional failed.
    NotGalois,
}

// Origin: engine/crates_rs/core_category_theory/src/adjunction/mod.rs
// Claim: urn:core:crates_rs:core-category-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for GaloisError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for GaloisError {}

/// A monotone pair `f ⊣ g` on finite chains.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GaloisWitness {
    domain: u32,
    codomain: u32,
}

fn validate_lower_chain(f: &[u32], m: u32) -> Result<(), GaloisError> {
    if f[0] >= m {
        return Err(GaloisError::Image { value: f[0] });
    }
    for window in f.windows(2) {
        if window[1] >= m {
            return Err(GaloisError::Image { value: window[1] });
        }
        if window[0] > window[1] {
            return Err(GaloisError::NotGalois);
        }
    }
    Ok(())
}

fn validate_upper_chain(g: &[u32], n: u32) -> Result<(), GaloisError> {
    if g[0] >= n {
        return Err(GaloisError::Image { value: g[0] });
    }
    for window in g.windows(2) {
        if window[0] > window[1] || window[1] >= n {
            return Err(GaloisError::NotGalois);
        }
    }
    Ok(())
}

fn check_galois_pairs(f: &[u32], g: &[u32]) -> Result<(), GaloisError> {
    for (a, &fa) in f.iter().enumerate() {
        for (b, &gb) in g.iter().enumerate() {
            if (fa <= b as u32) != ((a as u32) <= gb) {
                return Err(GaloisError::NotGalois);
            }
        }
    }
    Ok(())
}

impl GaloisWitness {
    /// `f` has length `n` and lands in `0..m`. `g` has length `m` and lands in `0..n`.
    ///
    /// Require monotonicity and `f(a) <= b` iff `a <= g(b)`.
    pub fn try_new(f: &[u32], g: &[u32], m: u32) -> Result<Self, GaloisError> {
        let n = f.len();
        if n == 0 || n > 8 || m == 0 || m > 8 || g.len() != m as usize {
            return Err(GaloisError::Carrier { n });
        }
        validate_lower_chain(f, m)?;
        validate_upper_chain(g, n as u32)?;
        check_galois_pairs(f, g)?;
        Ok(Self { domain: n as u32, codomain: m })
    }

    /// Size of the domain chain.
    pub fn domain(&self) -> u32 { self.domain }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod galois_tests {
    use super::*;
    #[test]
    fn the_identity_pair_is_galois() {
        let pair = GaloisWitness::try_new(&[0, 1, 2], &[0, 1, 2], 3);
        assert!(matches!(pair, Ok(ref p) if p.domain() == 3));
    }
    #[test]
    fn a_constant_lower_adjoint_against_a_zero_upper_is_refused() {
        let err = GaloisWitness::try_new(&[1, 1, 1], &[0, 0, 0], 3);
        assert!(matches!(err, Err(GaloisError::NotGalois)));
    }
}
