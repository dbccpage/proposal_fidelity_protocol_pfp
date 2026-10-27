//! Core category theory crate.
//!
//! Hierarchical shells under `foundations/`, `category/`, `functor/`, …
//! plus legacy finite-category records at crate root.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

// --- Hierarchical catalog (new) ---
pub mod abelian;
pub mod adjunction;
pub mod category;
pub mod enriched;
pub mod finite_continuation;
pub mod foundations;
pub mod functor;
pub mod limits_colimits;
pub mod monad;
pub mod monoidal;

// --- Legacy arithmos / finite records (pre-hierarchy) ---
pub mod core {
    pub trait Category {
        type Ob: Clone + PartialEq + Eq + std::fmt::Debug;
        type Mor: Clone + PartialEq + Eq + std::fmt::Debug;

        fn identity<A>(object: &A) -> Self::Mor;
        fn compose<A, B, C>(first: &Self::Mor, second: &Self::Mor) -> Option<Self::Mor>;
    }

    pub trait MorphismEq: Category {
        fn morphism_eq<A, B>(left: &Self::Mor, right: &Self::Mor) -> bool {
            left == right
        }
    }
}

pub mod errors {
    #[derive(Debug, Clone, PartialEq, Eq)]
    pub enum ArithmosError {
        LawViolation(String),
        PreconditionFailed(String),
        InvalidShape(String),
    }

// Origin: engine/crates_rs/core_category_theory/src/lib.rs
// Claim: urn:core:crates_rs:core-category-theory:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ArithmosError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ArithmosError {}
}

pub mod witness {
    #[derive(Debug, Clone, PartialEq, Eq)]
    pub struct Witness {
        pub name: String,
    }

    impl Witness {
        pub fn new(name: impl Into<String>) -> Self {
            Self { name: name.into() }
        }
    }
}

pub mod law {
    use super::errors::ArithmosError;
    use super::witness::Witness;

    pub trait Law {
        type Subject;
        fn check(subject: &Self::Subject) -> Result<Witness, ArithmosError>;
    }
}

pub mod braided_monoidal {
    pub trait BraidedMonoidalCategory: super::monoidal_category::MonoidalCategory {
        fn braiding<A, B>() -> Self::Mor
        where
            Self: super::core::Category;
    }
}

pub mod monoidal_category {
    use super::core::Category;

    pub trait MonoidalCategory: Category {
        type TensorProduct<A, B>: Clone;
        fn unit() -> Self::Ob;
    }
}

pub mod agent_functor;
pub mod arrow;
pub mod bridges;
pub mod cat_functor;
pub mod category_contract_alignment;
pub mod cauchy;
pub mod coend;
pub mod colimits;
pub mod condensation;
pub mod density_matrix_functor;
pub mod eilenberg_moore;
pub mod family_category;
pub mod finite_category;
pub mod finite_category_builder;
pub mod finite_category_validation;
pub mod finite_groupoid;
pub mod finite_profunctor;
pub mod functor_composition;
pub mod grothendieck_construction;
pub mod higher;
pub mod higher_functor;
pub mod hom_adjunction;
pub mod hott_topos_bridge;
pub mod kleisli_category;
pub mod lawvere;
pub mod legacy_adjunction;
pub mod legacy_monad;
pub mod limits;
pub mod morphism;
pub mod mssn_functor_bridge;
pub mod natural_trans;
pub mod natural_trans_composition;
pub mod nerve;
pub mod operad;
pub mod rewriting;
pub mod simplicial_hott_bridge;
pub mod topos_hott_model;
pub mod validation;
pub mod zeta_functor;

// Compatibility aliases for older import paths
pub use legacy_adjunction as adjunction_legacy;
pub use legacy_monad as monad_legacy;

pub mod bounded_counter;
pub mod finite_functional_dependencies;
pub mod finite_moore;
pub mod finite_path;
pub mod finite_relational;

pub mod context_reflection;

pub mod finite_functional_classification;
pub mod finite_retention_choices;
pub mod finite_self_reference;

pub mod dagger;
pub mod finite_history_context;
pub mod finite_partial_structure;
pub mod finite_question_family;
pub mod finite_report_repair;
pub mod finite_report_descent;
pub mod finite_report_query;
pub mod finite_section_separation;

pub mod finite_independence;
pub mod finite_trace;
pub mod finite_joint_carrier;
pub mod finite_joint_dynamics;
pub mod finite_simulation;

pub mod identity_census {
/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IdentityArrowCensus {
    objects: u64,
    identities: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IdentityArrowCensusError {
    Empty,
    OutOfRange { arrow: u64, objects: u64 },
    NotBijective { arrow: u64, hits: u64 },
    Overflow,
}

impl IdentityArrowCensus {
    fn count_hits(
        identity_of: &[u64],
        objects: u64,
        arrow: u64,
    ) -> Result<u64, IdentityArrowCensusError> {
        let mut hits = 0u64;
        let mut scan = 0u64;
        while scan < objects {
            let scan_us = usize::try_from(scan).map_err(|_| IdentityArrowCensusError::Overflow)?;
            let other = *identity_of
                .get(scan_us)
                .ok_or(IdentityArrowCensusError::Overflow)?;
            if other == arrow {
                hits = hits
                    .checked_add(1)
                    .ok_or(IdentityArrowCensusError::Overflow)?;
            }
            scan = scan
                .checked_add(1)
                .ok_or(IdentityArrowCensusError::Overflow)?;
        }
        Ok(hits)
    }

    pub fn certify(identity_of: &[u64]) -> Result<Self, IdentityArrowCensusError> {
        let objects = u64::try_from(identity_of.len()).map_err(|_| IdentityArrowCensusError::Overflow)?;
        if objects == 0 { return Err(IdentityArrowCensusError::Empty); }
        let mut index = 0u64;
        while index < objects {
            let index_us = usize::try_from(index).map_err(|_| IdentityArrowCensusError::Overflow)?;
            let arrow = *identity_of.get(index_us).ok_or(IdentityArrowCensusError::Overflow)?;
            if arrow >= objects { return Err(IdentityArrowCensusError::OutOfRange { arrow, objects }); }
            let hits = Self::count_hits(identity_of, objects, arrow)?;
            if hits != 1 { return Err(IdentityArrowCensusError::NotBijective { arrow, hits }); }
            index = index.checked_add(1).ok_or(IdentityArrowCensusError::Overflow)?;
        }
        Ok(Self { objects, identities: objects })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(IdentityArrowCensus::certify(&[0, 1, 2]), Ok(w) if w.objects == 3 && w.identities == 3));
        assert!(matches!(IdentityArrowCensus::certify(&[1, 0]), Ok(w) if w.objects == 2));
        assert!(matches!(IdentityArrowCensus::certify(&[1, 1]), Err(IdentityArrowCensusError::NotBijective { .. })));
        assert!(matches!(IdentityArrowCensus::certify(&[2]), Err(IdentityArrowCensusError::OutOfRange { .. })));
        assert!(matches!(IdentityArrowCensus::certify(&[]), Err(IdentityArrowCensusError::Empty)));
    }
}
}
