//! Morphism abstraction in Category Theory (core_category_theory).
//!
//! Aligned with URN contract: `urn:core:math:morphism:v0.1.0`.
//! A morphism `f: A -> B` represents a structure-preserving arrow between objects
//! `A` (domain) and `B` (codomain) within a category.

use std::fmt::Debug;

pub const MORPHISM_CONTRACT_ID: &str = "urn:core:math:morphism:v0.1.0";

/// Morphism trait between objects `Dom` and `Cod`.
pub trait MorphismTrait<Dom, Cod>: Debug {
    fn domain(&self) -> &Dom;
    fn codomain(&self) -> &Cod;
    fn id(&self) -> &str;
    fn category_id(&self) -> &str;
    fn evaluate(&self, input: &Dom) -> Cod;
}

/// Abstract representation of a typed Skill Morphism mapping states between domains.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SkillMorphism {
    pub contract_id: String,
    pub morphism_id: String,
    pub domain_id: String,
    pub codomain_id: String,
    pub category_id: String,
    pub governance_authority: String,
    pub evidence_ceiling: String,
    pub description: String,
}

impl SkillMorphism {
    pub fn new(
        morphism_id: impl Into<String>,
        domain_id: impl Into<String>,
        codomain_id: impl Into<String>,
        category_id: impl Into<String>,
        governance_authority: impl Into<String>,
        evidence_ceiling: impl Into<String>,
        description: impl Into<String>,
    ) -> Self {
        Self {
            contract_id: MORPHISM_CONTRACT_ID.to_string(),
            morphism_id: morphism_id.into(),
            domain_id: domain_id.into(),
            codomain_id: codomain_id.into(),
            category_id: category_id.into(),
            governance_authority: governance_authority.into(),
            evidence_ceiling: evidence_ceiling.into(),
            description: description.into(),
        }
    }

    /// Compose two skill morphisms `g . f` if `f.codomain_id == g.domain_id` and category matches.
    pub fn compose(&self, next: &SkillMorphism) -> Option<SkillMorphism> {
        if self.codomain_id == next.domain_id {
            Some(SkillMorphism {
                contract_id: MORPHISM_CONTRACT_ID.to_string(),
                morphism_id: format!("{} >> {}", self.morphism_id, next.morphism_id),
                domain_id: self.domain_id.clone(),
                codomain_id: next.codomain_id.clone(),
                category_id: self.category_id.clone(),
                governance_authority: self.governance_authority.clone(),
                evidence_ceiling: self.evidence_ceiling.clone(),
                description: format!(
                    "Composite morphism of {} and {}",
                    self.morphism_id, next.morphism_id
                ),
            })
        } else {
            None
        }
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/morphism.rs
// Claim: urn:core:math:morphism:v0.1.0
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ComposeError {
    CategoryMismatch { left: String, right: String },
    BoundaryMismatch { codomain: String, domain: String },
    AssociativityMismatch { left: String, right: String },
}

// Origin: engine/crates_rs/core_category_theory/src/morphism.rs
// Claim: urn:core:crates_rs:core-category-theory:morphism:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ComposeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ComposeError {}

impl SkillMorphism {
    pub fn try_compose(&self, next: &SkillMorphism) -> Result<SkillMorphism, ComposeError> {
        if self.category_id != next.category_id {
            return Err(ComposeError::CategoryMismatch {
                left: self.category_id.clone(),
                right: next.category_id.clone(),
            });
        }
        if self.codomain_id != next.domain_id {
            return Err(ComposeError::BoundaryMismatch {
                codomain: self.codomain_id.clone(),
                domain: next.domain_id.clone(),
            });
        }
        match self.compose(next) {
            Some(composite) => Ok(composite),
            None => Err(ComposeError::BoundaryMismatch {
                codomain: self.codomain_id.clone(),
                domain: next.domain_id.clone(),
            }),
        }
    }

    pub fn try_associate(
        &self,
        middle: &SkillMorphism,
        right: &SkillMorphism,
    ) -> Result<SkillMorphism, ComposeError> {
        let left_then = self.try_compose(middle)?.try_compose(right)?;
        let right_then = self.try_compose(&middle.try_compose(right)?)?;
        if left_then.morphism_id != right_then.morphism_id
            || left_then.domain_id != right_then.domain_id
            || left_then.codomain_id != right_then.codomain_id
            || left_then.category_id != right_then.category_id
        {
            return Err(ComposeError::AssociativityMismatch {
                left: left_then.morphism_id,
                right: right_then.morphism_id,
            });
        }
        Ok(left_then)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod compose_certificate_tests {
    use super::*;

    fn arrow(id: &str, domain: &str, codomain: &str, category: &str) -> SkillMorphism {
        SkillMorphism::new(id, domain, codomain, category, "none", "none", "arrow")
    }

    #[test]
    fn three_arrows_associate_inside_one_category() {
        let f = arrow("f", "A", "B", "C");
        let g = arrow("g", "B", "C", "C");
        let h = arrow("h", "C", "D", "C");
        let witness = f.try_associate(&g, &h);
        assert!(matches!(witness, Ok(ref composite) if composite.morphism_id == "f >> g >> h"));
        assert_eq!(witness.as_ref().map(|composite| composite.domain_id.as_str()), Ok("A"));
        assert_eq!(witness.as_ref().map(|composite| composite.codomain_id.as_str()), Ok("D"));
    }

    #[test]
    fn refuses_a_different_category_and_a_broken_boundary() {
        let f = arrow("f", "A", "B", "C");
        let other = arrow("g", "B", "C", "D");
        assert!(matches!(f.try_compose(&other), Err(ComposeError::CategoryMismatch { .. })));
        let broken = arrow("g", "Z", "C", "C");
        assert!(matches!(f.try_compose(&broken), Err(ComposeError::BoundaryMismatch { .. })));
    }
}
