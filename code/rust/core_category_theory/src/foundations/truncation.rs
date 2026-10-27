//! truncation shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Related contract (if present): `urn:core:math:truncation_level:v0.1.0`.

use serde::{Deserialize, Serialize};

/// Best-effort shell for an n-truncation claim / level tag.
///
/// Does not implement the truncation HIT; shape / inventory only.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Truncation {
    pub label: String,
    /// Truncation level n (caller convention: n ≥ -2; None = untruncated).
    pub level: Option<i32>,
    /// Optional type reference being truncated.
    pub type_ref: String,
    pub notes: Vec<String>,
}

impl Truncation {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            level: Some(0),
            type_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn at_level(label: impl Into<String>, level: i32) -> Self {
        Self {
            label: label.into(),
            level: Some(level),
            type_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn untruncated(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            level: None,
            type_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if let Some(n) = self.level {
            if n < -2 {
                return Err(format!("truncation level {n} < -2"));
            }
        }
        Ok(())
    }
}


/// HoTT truncation floor is `-2`. `above_floor = level + 2` round-trips.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TruncationWitness {
    level: i32,
    above_floor: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TruncationWitnessError {
    EmptyLabel,
    Untruncated,
    BelowContractible { level: i32 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/foundations/truncation.rs
// Claim: urn:core:crates_rs:core-category-theory:truncation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TruncationWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TruncationWitnessError {}

impl TruncationWitness {
    pub fn admit(truncation: &Truncation) -> Result<Self, TruncationWitnessError> {
        if truncation.label.is_empty() {
            return Err(TruncationWitnessError::EmptyLabel);
        }
        let Some(level) = truncation.level else {
            return Err(TruncationWitnessError::Untruncated);
        };
        let shifted = level.checked_add(2).ok_or(TruncationWitnessError::Overflow)?;
        if shifted < 0 {
            return Err(TruncationWitnessError::BelowContractible { level });
        }
        let above_floor = u32::try_from(shifted).map_err(|_| TruncationWitnessError::Overflow)?;
        let recovered = i32::try_from(above_floor)
            .map_err(|_| TruncationWitnessError::Overflow)?
            .checked_sub(2)
            .ok_or(TruncationWitnessError::Overflow)?;
        if recovered != level {
            return Err(TruncationWitnessError::Overflow);
        }
        Ok(Self { level, above_floor })
    }

    pub fn above_floor(&self) -> u32 {
        self.above_floor
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(Truncation::new("x").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Truncation::new("").validate_shell().is_err());
    }

    #[test]
    fn untruncated_ok() {
        assert!(Truncation::untruncated("∞").validate_shell().is_ok());
    }

    #[test]
    fn rejects_below_minus_two() {
        assert!(Truncation::at_level("bad", -3).validate_shell().is_err());
    }

    #[test]
    fn truncation_floor_is_minus_two() {
        let truncation = Truncation::at_level("set", 0);
        let admitted = TruncationWitness::admit(&truncation);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.above_floor()), Some(2));
        assert!(matches!(
            TruncationWitness::admit(&Truncation::at_level("bad", -3)),
            Err(TruncationWitnessError::BelowContractible { level: -3 })
        ));
    }

}
