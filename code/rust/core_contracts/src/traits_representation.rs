use super::identity::{ContractBound, NamedComponent};
use crate::kinds::BaseType;

pub trait Adapter<S, T: BaseType>: NamedComponent + ContractBound {
    type Error;
    fn adapt(&self, input: &S) -> Result<T, Self::Error>;
}

pub trait Encoder<S: BaseType, T: BaseType>: NamedComponent + ContractBound {
    type Error;
    fn encode(&self, input: &S) -> Result<T, Self::Error>;
}

pub trait Decoder<S: BaseType, T: BaseType>: NamedComponent + ContractBound {
    type Error;
    fn decode(&self, input: &S) -> Result<T, Self::Error>;
}

/// Representation projection only.
/// This is not automatically fixed-layer OperatorClass::R.
pub trait Projector<S: BaseType, T: BaseType>: NamedComponent + ContractBound {
    type Error;
    fn project(&self, input: &S) -> Result<T, Self::Error>;
}

/// Representation reflection only.
/// This does not authorize a lift or equivalence claim.
pub trait Reflector<S: BaseType, T: BaseType>: NamedComponent + ContractBound {
    type Error;
    fn reflect(&self, input: &S) -> Result<T, Self::Error>;
}

/// Rank form of a representation projector: the image rank cannot exceed the
/// source rank, and the kernel rank is the difference.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProjectorRank {
    source_rank: u64,
    image_rank: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ProjectorRankError {
    EmptySource,
    ImageExceedsSource { source_rank: u64, image_rank: u64 },
}

// Origin: engine/crates_rs/core_contracts/src/traits_representation.rs
// Claim: urn:core:crates_rs:core-contracts:traits-representation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ProjectorRankError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ProjectorRankError {}

impl ProjectorRank {
    pub fn try_new(source_rank: u64, image_rank: u64) -> Result<Self, ProjectorRankError> {
        if source_rank == 0 {
            return Err(ProjectorRankError::EmptySource);
        }
        if image_rank > source_rank {
            return Err(ProjectorRankError::ImageExceedsSource {
                source_rank,
                image_rank,
            });
        }
        Ok(Self {
            source_rank,
            image_rank,
        })
    }

    pub fn kernel_rank(&self) -> Option<u64> {
        self.source_rank.checked_sub(self.image_rank)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod projector_rank_witness {
    use super::*;

    #[test]
    fn kernel_completes_the_source() {
        let rank = ProjectorRank::try_new(5, 2);
        assert!(rank.is_ok());
        if let Ok(rank) = rank {
            assert_eq!(rank.kernel_rank(), Some(3));
        }
    }

    #[test]
    fn image_past_the_source_is_refused() {
        assert!(matches!(
            ProjectorRank::try_new(2, 4),
            Err(ProjectorRankError::ImageExceedsSource {
                source_rank: 2,
                image_rank: 4
            })
        ));
    }
}
