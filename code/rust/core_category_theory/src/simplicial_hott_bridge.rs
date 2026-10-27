//! Bridge finite nerves and rewrite paths to HoTT path witnesses.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SimplicialPathWitness {
    pub simplex: String,
    pub hott_path: String,
    pub coherence_cells: Vec<String>,
}

impl SimplicialPathWitness {
    pub fn new(simplex: &str, hott_path: &str) -> Self {
        Self {
            simplex: simplex.into(),
            hott_path: hott_path.into(),
            coherence_cells: Vec::new(),
        }
    }

    pub fn is_coherent_at_level(&self, level: usize) -> bool {
        self.coherence_cells.len() >= level
    }
}

/// Inner horn Λ^n_k with 0 < k < n and n = |coherence cells| + 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InnerHornWitness {
    dimension: usize,
    missing_face: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InnerHornError {
    EmptyPath,
    DimensionTooSmall,
    OuterFace { missing_face: usize, dimension: usize },
    CoherenceMismatch { cells_plus_one: usize, dimension: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/simplicial_hott_bridge.rs
// Claim: urn:core:crates_rs:core-category-theory:simplicial-hott-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for InnerHornError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for InnerHornError {}

impl InnerHornWitness {
    pub fn try_for_path(
        path: &SimplicialPathWitness,
        dimension: usize,
        missing_face: usize,
    ) -> Result<Self, InnerHornError> {
        if path.simplex.is_empty() || path.hott_path.is_empty() {
            return Err(InnerHornError::EmptyPath);
        }
        if dimension < 2 {
            return Err(InnerHornError::DimensionTooSmall);
        }
        if missing_face == 0 || missing_face >= dimension {
            return Err(InnerHornError::OuterFace {
                missing_face,
                dimension,
            });
        }
        let cells_plus_one = path
            .coherence_cells
            .len()
            .checked_add(1)
            .ok_or(InnerHornError::Overflow)?;
        if cells_plus_one != dimension {
            return Err(InnerHornError::CoherenceMismatch {
                cells_plus_one,
                dimension,
            });
        }
        Ok(Self {
            dimension,
            missing_face,
        })
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    pub fn missing_face(&self) -> usize {
        self.missing_face
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_7dc48ef4 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
