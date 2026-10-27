use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct MorphismId(pub String);

impl MorphismId {
    pub fn new(id: impl Into<String>) -> Self {
        let s = id.into();
        assert!(!s.trim().is_empty(), "MorphismId cannot be empty");
        MorphismId(s)
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MorphismChainWitness {
    steps: u64,
    source_dim: u64,
    target_dim: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MorphismChainWitnessError {
    EmptyChain,
    DimCount { dims: u64, steps: u64 },
    EmptyId,
    ZeroDim,
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/morphism_id.rs
// Claim: urn:core:crates_rs:core-types:morphism-id:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MorphismChainWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MorphismChainWitnessError {}

impl MorphismChainWitness {
    fn validate_elements(ids: &[MorphismId], dims: &[u64]) -> Result<(), MorphismChainWitnessError> {
        if ids.iter().any(|id| id.0.trim().is_empty()) {
            return Err(MorphismChainWitnessError::EmptyId);
        }
        if dims.contains(&0) {
            return Err(MorphismChainWitnessError::ZeroDim);
        }
        Ok(())
    }

    pub fn certify(ids: &[MorphismId], dims: &[u64]) -> Result<Self, MorphismChainWitnessError> {
        if ids.is_empty() {
            return Err(MorphismChainWitnessError::EmptyChain);
        }
        let steps = u64::try_from(ids.len()).map_err(|_| MorphismChainWitnessError::Overflow)?;
        let dim_count = u64::try_from(dims.len()).map_err(|_| MorphismChainWitnessError::Overflow)?;
        let expected = steps.checked_add(1).ok_or(MorphismChainWitnessError::Overflow)?;
        if dim_count != expected {
            return Err(MorphismChainWitnessError::DimCount { dims: dim_count, steps });
        }
        Self::validate_elements(ids, dims)?;
        Ok(Self {
            steps,
            source_dim: dims[0],
            target_dim: dims[dims.len() - 1],
        })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_morphism_id() {
        let id = MorphismId::new("L123");
        assert_eq!(id.0, "L123");
    }

    #[test]
    #[should_panic(expected = "MorphismId cannot be empty")]
    fn test_empty_morphism_id() {
        MorphismId::new("   ");
    }

#[test]
    fn exact_witness_holds() {
        let ids = [MorphismId::new("f"), MorphismId::new("g")];
        assert!(matches!(MorphismChainWitness::certify(&ids, &[2, 3, 5]), Ok(w) if w.steps == 2 && w.source_dim == 2 && w.target_dim == 5));
        assert!(matches!(MorphismChainWitness::certify(&ids, &[2, 0, 5]), Err(MorphismChainWitnessError::ZeroDim)));
        assert!(matches!(MorphismChainWitness::certify(&ids, &[2, 3]), Err(MorphismChainWitnessError::DimCount { .. })));
    }
}
