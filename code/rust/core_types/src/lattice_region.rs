use crate::operator_signature::MorphismType;

use core::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RegionCategory {
    General,
    MathSeries,
    Discrete,
    MlControl,
}

impl fmt::Display for RegionCategory {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::General => write!(f, "General"),
            Self::MathSeries => write!(f, "Math.Series"),
            Self::Discrete => write!(f, "Discrete"),
            Self::MlControl => write!(f, "ML.Control"),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LatticeRegion {
    id_range: (usize, usize),
    tier: usize,
    category: RegionCategory,
    morphism_type: MorphismType,
}

impl LatticeRegion {
    pub fn new(
        id_range: (usize, usize),
        tier: usize,
        category: RegionCategory,
        morphism_type: MorphismType,
    ) -> Result<Self, String> {
        Ok(Self {
            id_range,
            tier,
            category,
            morphism_type,
        })
    }

    pub fn id_range(&self) -> (usize, usize) {
        self.id_range
    }
    pub fn tier(&self) -> usize {
        self.tier
    }
    pub fn category(&self) -> RegionCategory {
        self.category
    }
    pub fn morphism_type(&self) -> MorphismType {
        self.morphism_type.clone()
    }
}

#[derive(Hash, Eq, PartialEq, Clone, Copy, Debug)]
pub struct RegionId(pub usize);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SpanError {
    Inverted,
}

impl LatticeRegion {
    pub fn try_closed_width(&self) -> Result<usize, SpanError> {
        let (lo, hi) = self.id_range;
        if hi < lo {
            return Err(SpanError::Inverted);
        }
        Ok(hi - lo)
    }
}

// Origin: engine/crates_rs/core_types/src/lattice_region.rs
// Claim: urn:core:crates_rs:core-types:lattice-region:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod span_tests {
    use super::*;
    use crate::operator_signature::MorphismType;

    #[test]
    fn closed_id_span_is_the_difference() {
        let region = LatticeRegion::new((2, 5), 1, RegionCategory::Discrete, MorphismType::Compute);
        assert!(matches!(region, Ok(region) if region.try_closed_width() == Ok(3)));
        let inverted = LatticeRegion::new((5, 2), 1, RegionCategory::Discrete, MorphismType::Compute);
        assert!(matches!(inverted, Ok(region) if region.try_closed_width() == Err(SpanError::Inverted)));
    }
}
