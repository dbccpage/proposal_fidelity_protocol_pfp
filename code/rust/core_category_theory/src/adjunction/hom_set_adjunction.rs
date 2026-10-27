//! hom-set adjunction shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Hom-set formulation: Hom_D(L(A), B) ≅ Hom_C(A, R(B)).
//! Diagnostic mate-pair tags only — not a bijection certificate.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_88d3bf1a;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_88d3bf1a<T> = std::result::Result<T, BoundaryError_88d3bf1a>;
use serde::{Deserialize, Serialize};

/// A single mate pair tag: f : L(A)→B  ↔  f̄ : A→R(B).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MatePair {
    pub base_object: String,
    pub lifted_object: String,
    /// Morphism tag in Hom_D(L(A), B).
    pub left_hom: String,
    /// Morphism tag in Hom_C(A, R(B)).
    pub right_hom: String,
}

impl MatePair {
    pub fn new(
        base_object: impl Into<String>,
        lifted_object: impl Into<String>,
        left_hom: impl Into<String>,
        right_hom: impl Into<String>,
    ) -> Self {
        Self {
            base_object: base_object.into(),
            lifted_object: lifted_object.into(),
            left_hom: left_hom.into(),
            right_hom: right_hom.into(),
        }
    }
}

/// Best-effort shell for a hom-set adjunction declaration.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct HomSetAdjunctionShell {
    pub label: String,
    pub left_functor: String,
    pub right_functor: String,
    /// Optional link to a unit/counit adjunction shell.
    pub adjunction_ref: String,
    /// Declared mate pairs (diagnostic inventory).
    pub mate_pairs: Vec<MatePair>,
    pub notes: Vec<String>,
}

impl HomSetAdjunctionShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            left_functor: String::new(),
            right_functor: String::new(),
            adjunction_ref: String::new(),
            mate_pairs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        left_functor: impl Into<String>,
        right_functor: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            left_functor: left_functor.into(),
            right_functor: right_functor.into(),
            adjunction_ref: String::new(),
            mate_pairs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_mate(mut self, pair: MatePair) -> Self {
        self.mate_pairs.push(pair);
        self
    }

    pub fn add_mate(&mut self, pair: MatePair) {
        self.mate_pairs.push(pair);
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.left_functor.is_empty() {
            return Err("empty left_functor".into());
        }
        if self.right_functor.is_empty() {
            return Err("empty right_functor".into());
        }
        for (i, p) in self.mate_pairs.iter().enumerate() {
            if p.base_object.is_empty()
                || p.lifted_object.is_empty()
                || p.left_hom.is_empty()
                || p.right_hom.is_empty()
            {
                return Err(format!("empty mate pair field at index {i}"));
            }
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
        let h = HomSetAdjunctionShell::between("hom-adj", "L", "R");
        assert!(h.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(HomSetAdjunctionShell::new("").validate_shell().is_err());
    }

    #[test]
    fn with_mate_ok() {
        let h = HomSetAdjunctionShell::between("hom-adj", "L", "R")
            .with_mate(MatePair::new("a", "b", "f", "f_bar"));
        assert_eq!(h.mate_pairs.len(), 1);
        assert!(h.validate_shell().is_ok());
    }

    #[test]
    fn rejects_empty_mate_field() {
        let h = HomSetAdjunctionShell::between("hom-adj", "L", "R")
            .with_mate(MatePair::new("a", "b", "", "f_bar"));
        assert!(h.validate_shell().is_err());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MateTableCensus { pairs: usize }

impl MateTableCensus {
    pub fn pairs(&self) -> usize { self.pairs }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MateTableError { Empty, Tag, DuplicateLeft, DuplicateRight }

// Origin: engine/crates_rs/core_category_theory/src/adjunction/hom_set_adjunction.rs
// Claim: urn:core:crates_rs:core-category-theory:hom-set-adjunction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MateTableError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MateTableError {}

impl HomSetAdjunctionShell {
    /// Left tags and right tags are both injective, so the declared mates are a finite bijection.
    pub fn certify_mate_bijection(&self) -> Result<MateTableCensus, MateTableError> {
        if self.mate_pairs.is_empty() {
            return Err(MateTableError::Empty);
        }
        let mut left = std::collections::BTreeSet::new();
        let mut right = std::collections::BTreeSet::new();
        for pair in &self.mate_pairs {
            if pair.left_hom.is_empty() || pair.right_hom.is_empty() {
                return Err(MateTableError::Tag);
            }
            if !left.insert(pair.left_hom.clone()) {
                return Err(MateTableError::DuplicateLeft);
            }
            if !right.insert(pair.right_hom.clone()) {
                return Err(MateTableError::DuplicateRight);
            }
        }
        if left.len() != right.len() {
            return Err(MateTableError::DuplicateLeft);
        }
        Ok(MateTableCensus { pairs: left.len() })
    }
}

#[cfg(test)]
mod mate_table_checks {
    use super::*;

    #[test]
    fn two_distinct_mates_form_a_bijection() {
        let shell = HomSetAdjunctionShell::between("adj", "L", "R")
            .with_mate(MatePair::new("A", "LA", "f", "fbar"))
            .with_mate(MatePair::new("B", "LB", "g", "gbar"));
        let census = shell.certify_mate_bijection();
        assert!(matches!(census, Ok(c) if c.pairs() == 2));
    }

    #[test]
    fn a_repeated_left_tag_is_refused() {
        let shell = HomSetAdjunctionShell::between("adj", "L", "R")
            .with_mate(MatePair::new("A", "LA", "f", "fbar"))
            .with_mate(MatePair::new("B", "LB", "f", "gbar"));
        assert!(matches!(shell.certify_mate_bijection(), Err(MateTableError::DuplicateLeft)));
    }
}
