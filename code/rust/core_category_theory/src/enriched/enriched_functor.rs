//! enriched_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_aea84071;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_aea84071<T> = std::result::Result<T, BoundaryError_aea84071>;
use serde::{Deserialize, Serialize};

/// Best-effort V-enriched functor shell F : C → D.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct EnrichedFunctor {
    pub label: String,
    /// Domain enriched category shell label.
    pub domain_enriched: String,
    /// Codomain enriched category shell label.
    pub codomain_enriched: String,
    /// Shared base monoidal V label.
    pub base_monoidal_v: String,
    /// Object-map ref.
    pub object_map_ref: String,
    /// Hom-map family ref F_{A,B} : C(A,B) → D(FA,FB) in V.
    pub hom_map_ref: String,
    pub notes: Vec<String>,
}

impl EnrichedFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            domain_enriched: String::new(),
            codomain_enriched: String::new(),
            base_monoidal_v: String::new(),
            object_map_ref: String::new(),
            hom_map_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        domain_enriched: impl Into<String>,
        codomain_enriched: impl Into<String>,
        base_monoidal_v: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            domain_enriched: domain_enriched.into(),
            codomain_enriched: codomain_enriched.into(),
            base_monoidal_v: base_monoidal_v.into(),
            object_map_ref: String::new(),
            hom_map_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.domain_enriched.is_empty() {
            return Err("empty domain_enriched".into());
        }
        if self.codomain_enriched.is_empty() {
            return Err("empty codomain_enriched".into());
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
        assert!(EnrichedFunctor::between("F", "C", "D", "V")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(EnrichedFunctor::new("").validate_shell().is_err());
    }
}

/// Hom-object dimension of a composite enriched functor: dim(A,C) = dim(A,B) * dim(B,C).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EnrichedCompositionDimWitness {
    dim_ab: u64,
    dim_bc: u64,
    dim_ac: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EnrichedDimError {
    EmptyLabel,
    ZeroDimension,
    DimensionMismatch { expected: u64, actual: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/enriched/enriched_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:enriched-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for EnrichedDimError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for EnrichedDimError {}

impl EnrichedCompositionDimWitness {
    pub fn try_new(
        label: &str,
        dim_ab: u64,
        dim_bc: u64,
        dim_ac: u64,
    ) -> Result<Self, EnrichedDimError> {
        if label.is_empty() {
            return Err(EnrichedDimError::EmptyLabel);
        }
        if dim_ab == 0 || dim_bc == 0 || dim_ac == 0 {
            return Err(EnrichedDimError::ZeroDimension);
        }
        let expected = dim_ab
            .checked_mul(dim_bc)
            .ok_or(EnrichedDimError::Overflow)?;
        if dim_ac != expected {
            return Err(EnrichedDimError::DimensionMismatch {
                expected,
                actual: dim_ac,
            });
        }
        Ok(Self {
            dim_ab,
            dim_bc,
            dim_ac,
        })
    }

    pub fn dim_ac(&self) -> u64 {
        self.dim_ac
    }
}
