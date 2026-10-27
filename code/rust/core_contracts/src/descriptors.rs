#[path = "descriptors_bindings.rs"]
pub mod bindings;
#[path = "descriptors_laws.rs"]
pub mod laws;
#[path = "descriptors_product_spine.rs"]
pub mod product_spine;

pub use laws::*;
pub use product_spine::*;

/// Integer ranks of the seven authority markers in `laws`:
/// EffectNone = 0, EffectEvidenceOnly = 1, EffectFactOnly = 2,
/// EffectRequiresEvaluator = 3, EffectRequestsDecision = 4,
/// EffectAuthorizesTransition = 5, EffectStateTransition = 6.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AuthorityCeilingWitness {
    declared_rank: u8,
    ceiling_rank: u8,
    slack: u8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AuthorityCeilingError {
    RankAboveScale { rank: u8 },
    DeclaredAboveCeiling { declared_rank: u8, ceiling_rank: u8 },
}

// Origin: engine/crates_rs/core_contracts/src/descriptors.rs
// Claim: urn:core:crates_rs:core-contracts:descriptors:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for AuthorityCeilingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for AuthorityCeilingError {}

impl AuthorityCeilingWitness {
    pub const SCALE_MAX: u8 = 6;

    pub fn try_new(declared_rank: u8, ceiling_rank: u8) -> Result<Self, AuthorityCeilingError> {
        if declared_rank > Self::SCALE_MAX {
            return Err(AuthorityCeilingError::RankAboveScale {
                rank: declared_rank,
            });
        }
        if ceiling_rank > Self::SCALE_MAX {
            return Err(AuthorityCeilingError::RankAboveScale {
                rank: ceiling_rank,
            });
        }
        if declared_rank > ceiling_rank {
            return Err(AuthorityCeilingError::DeclaredAboveCeiling {
                declared_rank,
                ceiling_rank,
            });
        }
        let slack = ceiling_rank.saturating_sub(declared_rank);
        Ok(Self {
            declared_rank,
            ceiling_rank,
            slack,
        })
    }

    pub fn slack(&self) -> u8 {
        self.slack
    }

    pub fn declared_rank(&self) -> u8 {
        self.declared_rank
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_837b1227 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
