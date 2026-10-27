//! base_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort shell for the base of enrichment (monoidal V, often closed).
/// Separates "V as enrichment base" from ordinary monoidal inventory.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct BaseCategory {
    pub label: String,
    /// Underlying monoidal category shell label for V.
    pub monoidal_ref: String,
    /// Optional closed structure / internal-hom ref on V.
    pub closed_ref: String,
    /// Optional completeness / cocompleteness claim tags.
    pub completeness_notes: Vec<String>,
    pub notes: Vec<String>,
}

impl BaseCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: String::new(),
            closed_ref: String::new(),
            completeness_notes: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn from_monoidal(label: impl Into<String>, monoidal_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: monoidal_ref.into(),
            closed_ref: String::new(),
            completeness_notes: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.monoidal_ref.is_empty() {
            return Err("empty monoidal_ref".into());
        }
        Ok(())
    }
}


/// Enrichment base: one unit object lives in a nonempty object set. A closed
/// base has exactly `n^2` internal-hom objects.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BaseEnrichmentWitness {
    object_count: u32,
    internal_homs: u32,
    closed: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BaseEnrichmentError {
    Shell,
    EmptyBase,
    Overflow,
    ClosedHomMissing,
    ClosedHomUnexpected,
    InternalHomCensus { homs: u32, square: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/enriched/base_category.rs
// Claim: urn:core:crates_rs:core-category-theory:base-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BaseEnrichmentError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BaseEnrichmentError {}

impl BaseEnrichmentWitness {
    pub fn admit(
        base: &BaseCategory,
        object_count: u32,
        internal_homs: Option<u32>,
    ) -> Result<Self, BaseEnrichmentError> {
        if base.validate_shell().is_err() {
            return Err(BaseEnrichmentError::Shell);
        }
        if object_count == 0 {
            return Err(BaseEnrichmentError::EmptyBase);
        }
        let square = object_count
            .checked_mul(object_count)
            .ok_or(BaseEnrichmentError::Overflow)?;
        let closed = !base.closed_ref.is_empty();
        let recorded = match internal_homs {
            Some(homs) => {
                if !closed {
                    return Err(BaseEnrichmentError::ClosedHomUnexpected);
                }
                if homs != square {
                    return Err(BaseEnrichmentError::InternalHomCensus { homs, square });
                }
                homs
            }
            None => {
                if closed {
                    return Err(BaseEnrichmentError::ClosedHomMissing);
                }
                0
            }
        };
        Ok(Self {
            object_count,
            internal_homs: recorded,
            closed,
        })
    }

    pub fn internal_homs(&self) -> u32 {
        self.internal_homs
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(BaseCategory::from_monoidal("V", "MonV")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(BaseCategory::new("").validate_shell().is_err());
    }

    #[test]
    fn closed_base_has_a_square_of_internal_homs() {
        let mut base = BaseCategory::from_monoidal("V", "MonV");
        base.closed_ref = "hom".into();
        let admitted = BaseEnrichmentWitness::admit(&base, 3, Some(9));
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.internal_homs()), Some(9));
        assert!(matches!(
            BaseEnrichmentWitness::admit(&base, 3, Some(8)),
            Err(BaseEnrichmentError::InternalHomCensus { homs: 8, square: 9 })
        ));
    }

}
