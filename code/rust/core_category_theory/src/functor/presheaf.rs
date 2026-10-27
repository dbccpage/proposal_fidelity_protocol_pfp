//! presheaf shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Presheaf on C (functor C^op → Set) — shape only (label + category_ref).

use serde::{Deserialize, Serialize};

/// Best-effort shell for a presheaf on a category reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Presheaf {
    pub label: String,
    pub category_ref: String,
    pub notes: Vec<String>,
}

impl Presheaf {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn on_category(label: impl Into<String>, category_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.category_ref.is_empty() {
            return Err("empty category_ref".into());
        }
        Ok(())
    }
}


/// Restriction is a function, so the restricted section count cannot exceed
/// the original section count on any object.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PresheafRestrictionWitness {
    objects: u32,
    dropped: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PresheafRestrictionError {
    Shell,
    Overflow,
    LengthMismatch { sections: usize, restricted: usize },
    RestrictionIncreased { index: usize, domain: u32, image: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/functor/presheaf.rs
// Claim: urn:core:crates_rs:core-category-theory:presheaf:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PresheafRestrictionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PresheafRestrictionError {}

impl PresheafRestrictionWitness {
    pub fn admit(
        presheaf: &Presheaf,
        sections: &[u32],
        restricted: &[u32],
    ) -> Result<Self, PresheafRestrictionError> {
        if presheaf.validate_shell().is_err() {
            return Err(PresheafRestrictionError::Shell);
        }
        if sections.len() != restricted.len() {
            return Err(PresheafRestrictionError::LengthMismatch {
                sections: sections.len(),
                restricted: restricted.len(),
            });
        }
        let mut dropped = 0u32;
        for (index, (domain, image)) in sections.iter().zip(restricted.iter()).enumerate() {
            if image > domain {
                return Err(PresheafRestrictionError::RestrictionIncreased {
                    index,
                    domain: *domain,
                    image: *image,
                });
            }
            dropped = dropped
                .checked_add(domain - image)
                .ok_or(PresheafRestrictionError::Overflow)?;
        }
        let objects = u32::try_from(sections.len()).map_err(|_| PresheafRestrictionError::Overflow)?;
        Ok(Self { objects, dropped })
    }

    pub fn dropped(&self) -> u32 {
        self.dropped
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(Presheaf::on_category("P", "C").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Presheaf::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_ref() {
        assert!(Presheaf::new("P").validate_shell().is_err());
    }

    #[test]
    fn restriction_cannot_increase_sections() {
        let presheaf = Presheaf::on_category("P", "C");
        let admitted = PresheafRestrictionWitness::admit(&presheaf, &[4, 2], &[3, 2]);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.dropped()), Some(1));
        assert!(matches!(
            PresheafRestrictionWitness::admit(&presheaf, &[1], &[2]),
            Err(PresheafRestrictionError::RestrictionIncreased {
                index: 0,
                domain: 1,
                image: 2
            })
        ));
    }

}
