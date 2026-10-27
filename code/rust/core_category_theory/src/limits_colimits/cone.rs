//! cone / cocone shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// One cone/cocone leg: diagram index → morphism label.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ConeLeg {
    pub index: String,
    pub morphism_label: String,
}

/// Best-effort shell for a cone over a diagram (apex + legs).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Cone {
    pub label: String,
    pub apex: String,
    /// Legs as (index, morphism_label) pairs (apex → diagram object).
    pub legs: Vec<ConeLeg>,
    pub notes: Vec<String>,
}

impl Cone {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            apex: String::new(),
            legs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_apex(label: impl Into<String>, apex: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            apex: apex.into(),
            legs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_leg(&mut self, index: impl Into<String>, morphism_label: impl Into<String>) {
        self.legs.push(ConeLeg {
            index: index.into(),
            morphism_label: morphism_label.into(),
        });
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.apex.is_empty() {
            return Err("empty apex".into());
        }
        for (i, leg) in self.legs.iter().enumerate() {
            if leg.index.is_empty() || leg.morphism_label.is_empty() {
                return Err(format!("empty leg tag at index {i}"));
            }
        }
        Ok(())
    }
}

/// Best-effort shell for a cocone under a diagram (nadir + legs).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Cocone {
    pub label: String,
    pub nadir: String,
    /// Legs as (index, morphism_label) pairs (diagram object → nadir).
    pub legs: Vec<ConeLeg>,
    pub notes: Vec<String>,
}

impl Cocone {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            nadir: String::new(),
            legs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_nadir(label: impl Into<String>, nadir: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            nadir: nadir.into(),
            legs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_leg(&mut self, index: impl Into<String>, morphism_label: impl Into<String>) {
        self.legs.push(ConeLeg {
            index: index.into(),
            morphism_label: morphism_label.into(),
        });
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.nadir.is_empty() {
            return Err("empty nadir".into());
        }
        for (i, leg) in self.legs.iter().enumerate() {
            if leg.index.is_empty() || leg.morphism_label.is_empty() {
                return Err(format!("empty leg tag at index {i}"));
            }
        }
        Ok(())
    }
}


/// A cone or cocone has at most one leg per diagram index.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConeLegWitness {
    leg_count: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConeLegError {
    Shell,
    DuplicateIndex { index: String },
    CountOverflow,
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/cone.rs
// Claim: urn:core:crates_rs:core-category-theory:cone:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ConeLegError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ConeLegError {}

fn admit_legs(shell_ok: bool, legs: &[ConeLeg]) -> Result<ConeLegWitness, ConeLegError> {
    if !shell_ok {
        return Err(ConeLegError::Shell);
    }
    let mut seen: Vec<&str> = Vec::new();
    for leg in legs {
        if seen.iter().any(|index| *index == leg.index.as_str()) {
            return Err(ConeLegError::DuplicateIndex {
                index: leg.index.clone(),
            });
        }
        seen.push(leg.index.as_str());
    }
    let leg_count = u32::try_from(legs.len()).map_err(|_| ConeLegError::CountOverflow)?;
    Ok(ConeLegWitness { leg_count })
}

impl ConeLegWitness {
    pub fn admit_cone(cone: &Cone) -> Result<Self, ConeLegError> {
        admit_legs(cone.validate_shell().is_ok(), &cone.legs)
    }

    pub fn admit_cocone(cocone: &Cocone) -> Result<Self, ConeLegError> {
        admit_legs(cocone.validate_shell().is_ok(), &cocone.legs)
    }

    pub fn leg_count(&self) -> u32 {
        self.leg_count
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cone_validate_ok() {
        let mut c = Cone::with_apex("c", "L");
        c.with_leg("A", "π₁");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn cone_rejects_empty_apex() {
        assert!(Cone::new("c").validate_shell().is_err());
    }

    #[test]
    fn cone_rejects_empty_label() {
        assert!(Cone::with_apex("", "L").validate_shell().is_err());
    }

    #[test]
    fn cone_rejects_empty_leg() {
        let mut c = Cone::with_apex("c", "L");
        c.with_leg("", "π");
        assert!(c.validate_shell().is_err());
    }

    #[test]
    fn cocone_validate_ok() {
        let mut c = Cocone::with_nadir("cc", "Q");
        c.with_leg("A", "ι₁");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn cocone_rejects_empty_nadir() {
        assert!(Cocone::new("cc").validate_shell().is_err());
    }

    #[test]
    fn cone_legs_are_indexed_once() {
        let mut cone = Cone::with_apex("c", "L");
        cone.with_leg("A", "p");
        cone.with_leg("B", "q");
        let admitted = ConeLegWitness::admit_cone(&cone);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.leg_count()), Some(2));
        cone.with_leg("A", "r");
        assert!(matches!(
            ConeLegWitness::admit_cone(&cone),
            Err(ConeLegError::DuplicateIndex { .. })
        ));
    }

}
