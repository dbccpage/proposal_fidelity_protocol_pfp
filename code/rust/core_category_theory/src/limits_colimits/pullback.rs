//! pullback shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_51f426d7;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_51f426d7<T> = std::result::Result<T, BoundaryError_51f426d7>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a pullback of a cospan A → C ← B.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Pullback {
    pub label: String,
    pub pullback_object: String,
    /// Cospan left leg domain A (f : A → C).
    pub left_source: String,
    /// Cospan right leg domain B (g : B → C).
    pub right_source: String,
    /// Cospan apex C.
    pub cospan_apex: String,
    /// Cospan morphism f : A → C.
    pub morphism_f: String,
    /// Cospan morphism g : B → C.
    pub morphism_g: String,
    pub projection_left: String,
    pub projection_right: String,
    pub notes: Vec<String>,
}

impl Pullback {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            pullback_object: String::new(),
            left_source: String::new(),
            right_source: String::new(),
            cospan_apex: String::new(),
            morphism_f: String::new(),
            morphism_g: String::new(),
            projection_left: String::new(),
            projection_right: String::new(),
            notes: Vec::new(),
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn of_cospan(
        label: impl Into<String>,
        pullback_object: impl Into<String>,
        left_source: impl Into<String>,
        right_source: impl Into<String>,
        cospan_apex: impl Into<String>,
        morphism_f: impl Into<String>,
        morphism_g: impl Into<String>,
        projection_left: impl Into<String>,
        projection_right: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            pullback_object: pullback_object.into(),
            left_source: left_source.into(),
            right_source: right_source.into(),
            cospan_apex: cospan_apex.into(),
            morphism_f: morphism_f.into(),
            morphism_g: morphism_g.into(),
            projection_left: projection_left.into(),
            projection_right: projection_right.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.pullback_object.is_empty() {
            return Err("empty pullback_object".into());
        }
        if self.left_source.is_empty() {
            return Err("empty left_source".into());
        }
        if self.right_source.is_empty() {
            return Err("empty right_source".into());
        }
        if self.cospan_apex.is_empty() {
            return Err("empty cospan_apex".into());
        }
        if self.morphism_f.is_empty() {
            return Err("empty morphism_f".into());
        }
        if self.morphism_g.is_empty() {
            return Err("empty morphism_g".into());
        }
        if self.projection_left.is_empty() {
            return Err("empty projection_left".into());
        }
        if self.projection_right.is_empty() {
            return Err("empty projection_right".into());
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
        let pb = Pullback::of_cospan("pb", "P", "A", "B", "C", "f", "g", "p₁", "p₂");
        assert!(pb.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Pullback::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_cospan() {
        assert!(Pullback::new("pb").validate_shell().is_err());
    }
}

// --- exact carrier witness ---
use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PullbackLawError {
    Shell,
    Empty,
    NotFunctional { domain: u32 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/pullback.rs
// Claim: urn:core:crates_rs:core-category-theory:pullback:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PullbackLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PullbackLawError {}

/// The set of pairs equalised by two functional relations into a common apex.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PullbackPairWitness {
    pairs: u32,
}

fn functional(pairs: &[(u32, u32)]) -> Result<BTreeMap<u32, u32>, PullbackLawError> {
    if pairs.is_empty() {
        return Err(PullbackLawError::Empty);
    }
    let mut map = BTreeMap::new();
    for &(domain, apex) in pairs {
        if map.insert(domain, apex).is_some() {
            return Err(PullbackLawError::NotFunctional { domain });
        }
    }
    Ok(map)
}

impl PullbackPairWitness {
    pub fn try_new(shell: &Pullback, left: &[(u32, u32)], right: &[(u32, u32)]) -> Result<Self, PullbackLawError> {
        if shell.validate_shell().is_err() {
            return Err(PullbackLawError::Shell);
        }
        let left_map = functional(left)?;
        let right_map = functional(right)?;
        let mut pairs = 0u32;
        for &left_apex in left_map.values() {
            for &right_apex in right_map.values() {
                if left_apex == right_apex {
                    pairs = pairs.checked_add(1).ok_or(PullbackLawError::Overflow)?;
                }
            }
        }
        Ok(Self { pairs })
    }

    pub fn pairs(&self) -> u32 { self.pairs }
}

#[cfg(test)]
mod pullback_law_tests {
    use super::*;

    fn shell() -> Pullback {
        Pullback::of_cospan("pb", "P", "A", "B", "C", "f", "g", "p1", "p2")
    }

    #[test]
    fn equal_apex_values_form_the_pullback() {
        let witness = PullbackPairWitness::try_new(&shell(), &[(0, 1), (1, 0)], &[(0, 1), (1, 1)]);
        assert!(matches!(witness, Ok(ref witness) if witness.pairs() == 2));
    }

    #[test]
    fn a_two_valued_leg_is_refused() {
        let witness = PullbackPairWitness::try_new(&shell(), &[(0, 1), (0, 0)], &[(0, 1)]);
        assert!(matches!(witness, Err(PullbackLawError::NotFunctional { domain: 0 })));
    }
}
