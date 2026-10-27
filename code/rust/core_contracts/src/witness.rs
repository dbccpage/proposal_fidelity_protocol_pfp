#[path = "witness_capability.rs"]
pub mod capability;
#[path = "witness_directive.rs"]
pub mod directive;
#[path = "witness_empirical.rs"]
pub mod empirical;
#[path = "witness_evidence.rs"]
pub mod evidence;
#[path = "witness_law_checker.rs"]
pub mod law_checker;
// Renaming the inner module would break the public `witness::witness` path.
#[allow(clippy::module_inception)]
#[path = "witness_witness.rs"]
pub mod witness;

#[macro_use]
#[path = "witness_property_macros.rs"]
pub mod property_macros;

#[macro_use]
#[path = "witness_totality_macros.rs"]
pub mod totality_macros;

pub use capability::*;
pub use directive::witness_properties;
pub use directive::*;
pub use empirical::*;
pub use evidence::*;
pub use law_checker::*;

/// Dimension of a basis whose admissibility and independence witnesses agree.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BasisCard {
    dimension: u64,
}

/// Refusal of a basis card.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BasisCardError {
    NotStructural { property: &'static str },
    CertaintyTooLow { property: &'static str, rank: u8 },
    Empty,
    BasisHashMismatch,
    DimensionMismatch { admissibility: usize, independence: usize },
    VectorCountMismatch { dimension: usize, vectors: usize },
    UnverifiedAdmissibility,
    UnverifiedIndependence,
    DimensionOverflow,
}

// Origin: engine/crates_rs/core_contracts/src/witness.rs
// Claim: urn:core:crates_rs:core-contracts:witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BasisCardError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BasisCardError {}

impl BasisCard {
    fn verify_structural_certainty(
        class: WitnessClass,
        property: &'static str,
        rank: WitnessCertainty,
    ) -> Result<(), BasisCardError> {
        if class != WitnessClass::Structural {
            return Err(BasisCardError::NotStructural { property });
        }
        if rank < WitnessCertainty::ExhaustiveFiniteProof {
            return Err(BasisCardError::CertaintyTooLow {
                property,
                rank: rank as u8,
            });
        }
        Ok(())
    }

    fn verify_nonempty_and_matching(
        admissibility: &VectorSpaceAdmissibilityWitness,
        independence: &BasisLinearIndependenceWitness,
        vector_count: usize,
    ) -> Result<(), BasisCardError> {
        if admissibility.dimension == 0 || independence.dimension == 0 || vector_count == 0 {
            return Err(BasisCardError::Empty);
        }
        if admissibility.basis_hash != independence.basis_hash {
            return Err(BasisCardError::BasisHashMismatch);
        }
        if admissibility.dimension != independence.dimension {
            return Err(BasisCardError::DimensionMismatch {
                admissibility: admissibility.dimension,
                independence: independence.dimension,
            });
        }
        Ok(())
    }

    /// Store the dimension when both structural witnesses name the same positive basis.
    pub fn admit_basis(
        admissibility: &VectorSpaceAdmissibilityWitness,
        independence: &BasisLinearIndependenceWitness,
        vector_count: usize,
    ) -> Result<Self, BasisCardError> {
        Self::verify_structural_certainty(
            admissibility.class(),
            admissibility.property(),
            admissibility.witness_certainty(),
        )?;
        Self::verify_structural_certainty(
            independence.class(),
            independence.property(),
            independence.witness_certainty(),
        )?;
        Self::verify_nonempty_and_matching(admissibility, independence, vector_count)?;
        if !admissibility.operations_verified {
            return Err(BasisCardError::UnverifiedAdmissibility);
        }
        if !independence.rank_verified {
            return Err(BasisCardError::UnverifiedIndependence);
        }
        if admissibility.dimension != vector_count {
            return Err(BasisCardError::VectorCountMismatch {
                dimension: admissibility.dimension,
                vectors: vector_count,
            });
        }
        let dimension = u64::try_from(admissibility.dimension)
            .map_err(|_| BasisCardError::DimensionOverflow)?;
        Ok(Self { dimension })
    }

    /// Agreed basis dimension.
    pub fn dimension(self) -> u64 {
        self.dimension
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod basis_card_checks {
    use super::{
        BasisCard, BasisCardError, BasisLinearIndependenceWitness, VectorSpaceAdmissibilityWitness,
    };

    fn space(dimension: usize, basis_hash: &str, operations_verified: bool) -> VectorSpaceAdmissibilityWitness {
        VectorSpaceAdmissibilityWitness {
            witness_id: "vs".into(),
            contract_id: "basis".into(),
            schema_hash: "schema".into(),
            witness_hash: "witness".into(),
            produced_by: "basis-card".into(),
            dimension,
            basis_hash: basis_hash.into(),
            operations_verified,
        }
    }

    fn independence(dimension: usize, basis_hash: &str, rank_verified: bool) -> BasisLinearIndependenceWitness {
        BasisLinearIndependenceWitness {
            witness_id: "ind".into(),
            contract_id: "basis".into(),
            schema_hash: "schema".into(),
            witness_hash: "witness".into(),
            produced_by: "basis-card".into(),
            dimension,
            basis_hash: basis_hash.into(),
            rank_verified,
        }
    }

    #[test]
    fn the_card_stores_only_an_agreed_positive_dimension() {
        let card = BasisCard::admit_basis(&space(4, "b", true), &independence(4, "b", true), 4);
        assert_eq!(card.map(BasisCard::dimension), Ok(4));
        assert!(matches!(
            BasisCard::admit_basis(&space(0, "b", true), &independence(0, "b", true), 0),
            Err(BasisCardError::Empty)
        ));
        assert!(matches!(
            BasisCard::admit_basis(&space(3, "b", true), &independence(2, "b", true), 3),
            Err(BasisCardError::DimensionMismatch {
                admissibility: 3,
                independence: 2
            })
        ));
        assert!(matches!(
            BasisCard::admit_basis(&space(3, "b", true), &independence(3, "b", true), 2),
            Err(BasisCardError::VectorCountMismatch {
                dimension: 3,
                vectors: 2
            })
        ));
    }
}
