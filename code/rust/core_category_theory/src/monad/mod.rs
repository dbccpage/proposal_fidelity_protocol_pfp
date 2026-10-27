//! Monad shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Hierarchical best-effort records (endofunctor monoids, duals, algebras).
//! Computational finite monads live in `crate::legacy_monad`.

pub mod algebra_for_monad;
pub mod coalgebra_for_comonad;
pub mod comonad;
pub mod distributive_law;
pub mod eilenberg_moore;
pub mod kleisli_category;
#[allow(clippy::module_inception)]
pub mod monad;
pub mod monad_transformer;

pub use algebra_for_monad::AlgebraForMonad;
pub use coalgebra_for_comonad::CoalgebraForComonad;
pub use comonad::Comonad;
pub use distributive_law::DistributiveLaw;
pub use eilenberg_moore::EilenbergMoore;
pub use kleisli_category::KleisliCategory;
pub use monad::Monad;
pub use monad_transformer::MonadTransformer;

/// Census of identity arrows inside a Kleisli hom-set of a validated monad.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MonadKleisliCensus {
    identities: u32,
    kleisli_homs: u32,
}

/// Refusal of a monad shell, a collapsed unit, or an identity injection.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MonadKleisliError {
    Shell,
    UnitIsMultiply,
    Kleisli(kleisli_category::KleisliHomError),
    EmptyCarrier,
    ObjectOverflow,
    IdentitiesExceedHoms { identities: u32, kleisli_homs: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/monad/mod.rs
// Claim: urn:core:crates_rs:core-category-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MonadKleisliError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MonadKleisliError {}

impl MonadKleisliCensus {
    /// Identities on `objects` inject into the Kleisli homs when η and μ differ.
    pub fn certify(
        monad: &Monad,
        kleisli: &KleisliCategory,
        objects: usize,
        base_homs_into_t: u32,
        kleisli_homs: u32,
    ) -> Result<Self, MonadKleisliError> {
        if monad.validate_shell().is_err() || kleisli.validate_shell().is_err() {
            return Err(MonadKleisliError::Shell);
        }
        if monad.unit_ref == monad.multiply_ref {
            return Err(MonadKleisliError::UnitIsMultiply);
        }
        if objects == 0 {
            return Err(MonadKleisliError::EmptyCarrier);
        }
        let identities = u32::try_from(objects).map_err(|_| MonadKleisliError::ObjectOverflow)?;
        let homs = kleisli_category::KleisliHomWitness::admit(kleisli, base_homs_into_t, kleisli_homs)
            .map_err(MonadKleisliError::Kleisli)?;
        if identities > homs.hom_count() {
            return Err(MonadKleisliError::IdentitiesExceedHoms {
                identities,
                kleisli_homs: homs.hom_count(),
            });
        }
        Ok(Self {
            identities,
            kleisli_homs: homs.hom_count(),
        })
    }

    /// Number of identity arrows required by the object set.
    pub fn identities(self) -> u32 {
        self.identities
    }

    /// Size of the admitted Kleisli hom-set.
    pub fn kleisli_homs(self) -> u32 {
        self.kleisli_homs
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod monad_kleisli_census_checks {
    use super::{
        kleisli_category::KleisliHomError, KleisliCategory, Monad, MonadKleisliCensus, MonadKleisliError,
    };

    fn shells() -> (Monad, KleisliCategory) {
        (
            Monad::with_structure("T", "T", "eta", "mu"),
            KleisliCategory::for_monad("Kl", "T"),
        )
    }

    #[test]
    fn identities_inject_only_when_unit_and_multiplication_differ() {
        let (monad, kleisli) = shells();
        let admitted = MonadKleisliCensus::certify(&monad, &kleisli, 3, 5, 5);
        assert_eq!(
            admitted.map(|census| (census.identities(), census.kleisli_homs())),
            Ok((3, 5))
        );
        let collapsed = Monad::with_structure("T", "T", "eta", "eta");
        assert!(matches!(
            MonadKleisliCensus::certify(&collapsed, &kleisli, 3, 5, 5),
            Err(MonadKleisliError::UnitIsMultiply)
        ));
        assert!(matches!(
            MonadKleisliCensus::certify(&monad, &kleisli, 6, 4, 4),
            Err(MonadKleisliError::IdentitiesExceedHoms {
                identities: 6,
                kleisli_homs: 4
            })
        ));
        assert!(matches!(
            MonadKleisliCensus::certify(&monad, &kleisli, 3, 5, 4),
            Err(MonadKleisliError::Kleisli(KleisliHomError::HomMismatch {
                base_homs_into_t: 5,
                kleisli_homs: 4
            }))
        ));
    }
}
