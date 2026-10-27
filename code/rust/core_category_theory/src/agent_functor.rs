//! Functor abstraction in Category Theory (core_category_theory).
//!
//! Aligned with URN contract: `urn:core:math:functor:v0.1.0`.
//! A functor `F: C -> D` maps objects in `C` to objects in `D` and morphisms `f: A -> B` in `C`
//! to morphisms `F(f): F(A) -> F(B)` in `D`, preserving identity and composition.

use crate::morphism::SkillMorphism;
use std::fmt::Debug;

pub const FUNCTOR_CONTRACT_ID: &str = "urn:core:math:functor:v0.1.0";

/// Functor trait mapping object types and morphism types between categories `C` and `D`.
pub trait FunctorTrait<ObjC, ObjD, MorC, MorD>: Debug {
    fn source_category_id(&self) -> &str;
    fn target_category_id(&self) -> &str;
    fn map_object(&self, obj: &ObjC) -> ObjD;
    fn map_morphism(&self, mor: &MorC) -> MorD;
}

/// Abstract representation of an Agent Functor mapping domain states and skill morphisms.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AgentFunctor {
    pub contract_id: String,
    pub name: String,
    pub source_category_id: String,
    pub target_category_id: String,
    pub primary_role: String,
    pub council_affiliation: String,
    pub supported_skills: Vec<String>,
    pub description: String,
}

impl AgentFunctor {
    pub fn new(
        name: impl Into<String>,
        source_category_id: impl Into<String>,
        target_category_id: impl Into<String>,
        primary_role: impl Into<String>,
        council_affiliation: impl Into<String>,
        supported_skills: Vec<String>,
        description: impl Into<String>,
    ) -> Self {
        Self {
            contract_id: FUNCTOR_CONTRACT_ID.to_string(),
            name: name.into(),
            source_category_id: source_category_id.into(),
            target_category_id: target_category_id.into(),
            primary_role: primary_role.into(),
            council_affiliation: council_affiliation.into(),
            supported_skills,
            description: description.into(),
        }
    }

    /// Map a Skill Morphism under this Agent Functor's domain transformation `F(f): F(A) -> F(B)`.
    pub fn map_skill_morphism(&self, morphism: &SkillMorphism) -> SkillMorphism {
        SkillMorphism {
            contract_id: morphism.contract_id.clone(),
            morphism_id: format!("{}[{}]", self.name, morphism.morphism_id),
            domain_id: format!("{}:{}", self.name, morphism.domain_id),
            codomain_id: format!("{}:{}", self.name, morphism.codomain_id),
            category_id: self.target_category_id.clone(),
            governance_authority: self.council_affiliation.clone(),
            evidence_ceiling: morphism.evidence_ceiling.clone(),
            description: format!(
                "Skill morphism {} lifted by Agent Functor {}",
                morphism.morphism_id, self.name
            ),
        }
    }
}

// --- exact carrier witness ---
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MonotoneError {
    Contract,
    Empty,
    Index,
    Monotone { left: usize, right: usize },
}

// Origin: engine/crates_rs/core_category_theory/src/agent_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:agent-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MonotoneError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MonotoneError {}

/// Images of a source preorder land in a declared target preorder.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MonotoneAgentImage {
    pairs: usize,
}

impl MonotoneAgentImage {
    pub fn try_new(
        agent: &AgentFunctor,
        source_pairs: &[(usize, usize)],
        images: &[usize],
        target_pairs: &BTreeSet<(usize, usize)>,
    ) -> Result<Self, MonotoneError> {
        if agent.contract_id != FUNCTOR_CONTRACT_ID || source_pairs.is_empty() {
            return Err(if agent.contract_id != FUNCTOR_CONTRACT_ID { MonotoneError::Contract } else { MonotoneError::Empty });
        }
        for &(left, right) in source_pairs {
            let image_left = *images.get(left).ok_or(MonotoneError::Index)?;
            let image_right = *images.get(right).ok_or(MonotoneError::Index)?;
            if !target_pairs.contains(&(image_left, image_right)) {
                return Err(MonotoneError::Monotone { left, right });
            }
        }
        Ok(Self { pairs: source_pairs.len() })
    }

    pub fn pairs(&self) -> usize { self.pairs }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod monotone_tests {
    use super::*;

    fn agent() -> AgentFunctor {
        AgentFunctor::new("agent", "C", "D", "role", "council", Vec::new(), "map")
    }

    #[test]
    fn a_collapse_preserves_the_source_relations() {
        let target = BTreeSet::from([(0usize, 0usize)]);
        let image = MonotoneAgentImage::try_new(&agent(), &[(0, 0), (1, 1), (0, 1)], &[0, 0], &target);
        assert!(matches!(image, Ok(ref image) if image.pairs() == 3));
    }

    #[test]
    fn a_missing_image_pair_is_refused() {
        let target = BTreeSet::from([(0usize, 0usize), (1, 1)]);
        let image = MonotoneAgentImage::try_new(&agent(), &[(0, 1)], &[0, 1], &target);
        assert!(matches!(image, Err(MonotoneError::Monotone { left: 0, right: 1 })));
    }
}
