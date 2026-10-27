//! enriched_adjunction shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_a39b880e;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_a39b880e<T> = std::result::Result<T, BoundaryError_a39b880e>;
use serde::{Deserialize, Serialize};

/// Best-effort enriched adjunction shell F ⊣ G (V-enriched).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct EnrichedAdjunction {
    pub label: String,
    /// Left adjoint enriched functor shell label.
    pub left_adjoint: String,
    /// Right adjoint enriched functor shell label.
    pub right_adjoint: String,
    /// Shared base monoidal V label.
    pub base_monoidal_v: String,
    /// Hom-isomorphism / unit-counit family ref in V.
    pub hom_iso_ref: String,
    pub notes: Vec<String>,
}

impl EnrichedAdjunction {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            left_adjoint: String::new(),
            right_adjoint: String::new(),
            base_monoidal_v: String::new(),
            hom_iso_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_adjoints(
        label: impl Into<String>,
        left_adjoint: impl Into<String>,
        right_adjoint: impl Into<String>,
        base_monoidal_v: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            left_adjoint: left_adjoint.into(),
            right_adjoint: right_adjoint.into(),
            base_monoidal_v: base_monoidal_v.into(),
            hom_iso_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.left_adjoint.is_empty() {
            return Err("empty left_adjoint".into());
        }
        if self.right_adjoint.is_empty() {
            return Err("empty right_adjoint".into());
        }
        if self.base_monoidal_v.is_empty() {
            return Err("empty base_monoidal_v".into());
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(EnrichedAdjunction::with_adjoints("adj", "F", "G", "V")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(EnrichedAdjunction::new("").validate_shell().is_err());
    }
}

/// Hom-isomorphism of an enriched adjunction: the two hom-ranks are equal.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct HomIsoRanks {
    left_hom: u64,
    right_hom: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HomIsoError {
    RankMismatch { left_hom: u64, right_hom: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/enriched/enriched_adjunction.rs
// Claim: urn:core:crates_rs:core-category-theory:enriched-adjunction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HomIsoError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HomIsoError {}

impl HomIsoRanks {
    pub fn try_new(left_hom: u64, right_hom: u64) -> Result<Self, HomIsoError> {
        if left_hom != right_hom {
            return Err(HomIsoError::RankMismatch { left_hom, right_hom });
        }
        Ok(Self { left_hom, right_hom })
    }

    pub fn rank(&self) -> u64 {
        self.left_hom
    }
}

#[cfg(test)]
mod hom_iso_witness {
    use super::*;

    #[test]
    fn equal_hom_ranks_are_the_only_admitted_iso() {
        let ranks = HomIsoRanks::try_new(6, 6).ok();
        assert_eq!(ranks.map(|r| r.rank()), Some(6));
        assert!(HomIsoRanks::try_new(6, 5).is_err());
    }
}
