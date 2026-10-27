//! pushout shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_93a5b968;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_93a5b968<T> = std::result::Result<T, BoundaryError_93a5b968>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a pushout of a span A ← C → B.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Pushout {
    pub label: String,
    pub pushout_object: String,
    /// Span left leg codomain A (f : C → A).
    pub left_target: String,
    /// Span right leg codomain B (g : C → B).
    pub right_target: String,
    /// Span base C.
    pub span_base: String,
    /// Span morphism f : C → A.
    pub morphism_f: String,
    /// Span morphism g : C → B.
    pub morphism_g: String,
    pub injection_left: String,
    pub injection_right: String,
    pub notes: Vec<String>,
}

impl Pushout {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            pushout_object: String::new(),
            left_target: String::new(),
            right_target: String::new(),
            span_base: String::new(),
            morphism_f: String::new(),
            morphism_g: String::new(),
            injection_left: String::new(),
            injection_right: String::new(),
            notes: Vec::new(),
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn of_span(
        label: impl Into<String>,
        pushout_object: impl Into<String>,
        left_target: impl Into<String>,
        right_target: impl Into<String>,
        span_base: impl Into<String>,
        morphism_f: impl Into<String>,
        morphism_g: impl Into<String>,
        injection_left: impl Into<String>,
        injection_right: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            pushout_object: pushout_object.into(),
            left_target: left_target.into(),
            right_target: right_target.into(),
            span_base: span_base.into(),
            morphism_f: morphism_f.into(),
            morphism_g: morphism_g.into(),
            injection_left: injection_left.into(),
            injection_right: injection_right.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.pushout_object.is_empty() {
            return Err("empty pushout_object".into());
        }
        if self.left_target.is_empty() {
            return Err("empty left_target".into());
        }
        if self.right_target.is_empty() {
            return Err("empty right_target".into());
        }
        if self.span_base.is_empty() {
            return Err("empty span_base".into());
        }
        if self.morphism_f.is_empty() {
            return Err("empty morphism_f".into());
        }
        if self.morphism_g.is_empty() {
            return Err("empty morphism_g".into());
        }
        if self.injection_left.is_empty() {
            return Err("empty injection_left".into());
        }
        if self.injection_right.is_empty() {
            return Err("empty injection_right".into());
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
        let po = Pushout::of_span("po", "P", "A", "B", "C", "f", "g", "i₁", "i₂");
        assert!(po.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Pushout::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_span() {
        assert!(Pushout::new("po").validate_shell().is_err());
    }
}

/// Cardinality of a pushout along monic legs: |P| = |A| + |B| − |C|.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MonicPushoutWitness {
    left_card: u64,
    right_card: u64,
    apex_card: u64,
    pushout_card: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MonicPushoutError {
    EmptyLabel,
    ApexNotEmbedded,
    CardinalityMismatch { expected: u64, actual: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/pushout.rs
// Claim: urn:core:crates_rs:core-category-theory:pushout:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MonicPushoutError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MonicPushoutError {}

impl MonicPushoutWitness {
    pub fn try_cards(
        label: &str,
        left_card: u64,
        right_card: u64,
        apex_card: u64,
        pushout_card: u64,
    ) -> Result<Self, MonicPushoutError> {
        if label.is_empty() {
            return Err(MonicPushoutError::EmptyLabel);
        }
        if apex_card > left_card || apex_card > right_card {
            return Err(MonicPushoutError::ApexNotEmbedded);
        }
        let union = left_card
            .checked_add(right_card)
            .ok_or(MonicPushoutError::Overflow)?;
        let expected = union
            .checked_sub(apex_card)
            .ok_or(MonicPushoutError::Overflow)?;
        if pushout_card != expected {
            return Err(MonicPushoutError::CardinalityMismatch {
                expected,
                actual: pushout_card,
            });
        }
        Ok(Self {
            left_card,
            right_card,
            apex_card,
            pushout_card,
        })
    }

    pub fn pushout_card(&self) -> u64 {
        self.pushout_card
    }
}
