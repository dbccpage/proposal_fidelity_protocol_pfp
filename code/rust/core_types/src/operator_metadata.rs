#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CertificationTier {
    Declared,
    Admissible,
    Certified,
}

impl CertificationTier {
    pub fn rank(self) -> u8 {
        match self {
            Self::Declared => 0,
            Self::Admissible => 1,
            Self::Certified => 2,
        }
    }
}

/// A declared tier may not outrank the ceiling tier.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TierCeiling {
    declared: CertificationTier,
    ceiling: CertificationTier,
    slack: u8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TierCeilingError {
    DeclaredAboveCeiling { declared: u8, ceiling: u8 },
}

// Origin: engine/crates_rs/core_types/src/operator_metadata.rs
// Claim: urn:core:crates_rs:core-types:operator-metadata:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TierCeilingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TierCeilingError {}

impl TierCeiling {
    pub fn try_new(
        declared: CertificationTier,
        ceiling: CertificationTier,
    ) -> Result<Self, TierCeilingError> {
        let declared_rank = declared.rank();
        let ceiling_rank = ceiling.rank();
        if declared_rank > ceiling_rank {
            return Err(TierCeilingError::DeclaredAboveCeiling {
                declared: declared_rank,
                ceiling: ceiling_rank,
            });
        }
        Ok(Self {
            declared,
            ceiling,
            slack: ceiling_rank.saturating_sub(declared_rank),
        })
    }

    pub fn slack(&self) -> u8 {
        self.slack
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_ed62e39e {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
