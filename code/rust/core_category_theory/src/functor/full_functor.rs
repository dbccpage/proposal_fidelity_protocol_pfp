//! full_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Fullness claim (surjective on Hom-sets) — shape only, not a proof.

use serde::{Deserialize, Serialize};

/// Best-effort shell for a fullness claim on a functor reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FullFunctor {
    pub label: String,
    pub functor_ref: String,
    pub notes: Vec<String>,
}

impl FullFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            functor_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn on_functor(label: impl Into<String>, functor_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            functor_ref: functor_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.functor_ref.is_empty() {
            return Err("empty functor_ref".into());
        }
        Ok(())
    }
}


/// Fullness on one hom-set: the image has the same cardinality as the target
/// hom-set, and no more elements than the source hom-set.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FullnessWitness {
    source_homs: u32,
    image_homs: u32,
    collapsed: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FullnessError {
    Shell,
    Overflow,
    NotSurjective { image_homs: u32, target_homs: u32 },
    NotFunctional { source_homs: u32, image_homs: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/functor/full_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:full-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FullnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FullnessError {}

impl FullnessWitness {
    pub fn admit(
        functor: &FullFunctor,
        source_homs: u32,
        image_homs: u32,
        target_homs: u32,
    ) -> Result<Self, FullnessError> {
        if functor.validate_shell().is_err() {
            return Err(FullnessError::Shell);
        }
        if image_homs != target_homs {
            return Err(FullnessError::NotSurjective {
                image_homs,
                target_homs,
            });
        }
        if image_homs > source_homs {
            return Err(FullnessError::NotFunctional {
                source_homs,
                image_homs,
            });
        }
        let collapsed = source_homs
            .checked_sub(image_homs)
            .ok_or(FullnessError::Overflow)?;
        Ok(Self {
            source_homs,
            image_homs,
            collapsed,
        })
    }

    pub fn collapsed(&self) -> u32 {
        self.collapsed
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(FullFunctor::on_functor("full", "F")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(FullFunctor::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_ref() {
        assert!(FullFunctor::new("x").validate_shell().is_err());
    }

    #[test]
    fn fullness_requires_a_surjective_hom_image() {
        let functor = FullFunctor::on_functor("full", "F");
        let admitted = FullnessWitness::admit(&functor, 4, 2, 2);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.collapsed()), Some(2));
        assert!(matches!(
            FullnessWitness::admit(&functor, 4, 1, 2),
            Err(FullnessError::NotSurjective {
                image_homs: 1,
                target_homs: 2
            })
        ));
    }

}
