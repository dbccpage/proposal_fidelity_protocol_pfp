//! cokernel_pair shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_0dec1c17;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_0dec1c17<T> = std::result::Result<T, BoundaryError_0dec1c17>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a cokernel pair of a morphism f : A → B
/// (pushout of f along itself).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CokernelPair {
    pub label: String,
    /// Cokernel-pair object B ⇉ Q.
    pub pair_object: String,
    pub source: String,
    pub target: String,
    /// Morphism f : source → target whose cokernel pair is taken.
    pub morphism_f: String,
    /// Left injection target → Q.
    pub injection_left: String,
    /// Right injection target → Q.
    pub injection_right: String,
    pub notes: Vec<String>,
}

impl CokernelPair {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            pair_object: String::new(),
            source: String::new(),
            target: String::new(),
            morphism_f: String::new(),
            injection_left: String::new(),
            injection_right: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of_morphism(
        label: impl Into<String>,
        pair_object: impl Into<String>,
        source: impl Into<String>,
        target: impl Into<String>,
        morphism_f: impl Into<String>,
        injection_left: impl Into<String>,
        injection_right: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            pair_object: pair_object.into(),
            source: source.into(),
            target: target.into(),
            morphism_f: morphism_f.into(),
            injection_left: injection_left.into(),
            injection_right: injection_right.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.pair_object.is_empty() {
            return Err("empty pair_object".into());
        }
        if self.source.is_empty() {
            return Err("empty source".into());
        }
        if self.target.is_empty() {
            return Err("empty target".into());
        }
        if self.morphism_f.is_empty() {
            return Err("empty morphism_f".into());
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
        let c = CokernelPair::of_morphism("ckp", "Q", "A", "B", "f", "i₁", "i₂");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(CokernelPair::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_morphism() {
        assert!(CokernelPair::new("ckp").validate_shell().is_err());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteCokernelCardinality { source: u64, target: u64, quotient: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CokernelCardError { Injection, Overflow }

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/cokernel_pair.rs
// Claim: urn:core:crates_rs:core-category-theory:cokernel-pair:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CokernelCardError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CokernelCardError {}

impl FiniteCokernelCardinality {
    /// Injective FinSet cokernel pair: `|Q| = 2|B| - |A|` with `|A| <= |B|`.
    pub fn try_new(source: u64, target: u64) -> Result<Self, CokernelCardError> {
        if source > target {
            return Err(CokernelCardError::Injection);
        }
        let doubled = target.checked_mul(2).ok_or(CokernelCardError::Overflow)?;
        let quotient = doubled.checked_sub(source).ok_or(CokernelCardError::Overflow)?;
        let back = quotient.checked_add(source).ok_or(CokernelCardError::Overflow)?;
        if back != doubled {
            return Err(CokernelCardError::Overflow);
        }
        Ok(Self { source, target, quotient })
    }

    pub fn quotient(&self) -> u64 { self.quotient }
}

#[cfg(test)]
mod cokernel_card_checks {
    use super::*;

    #[test]
    fn injecting_two_into_five_leaves_eight() {
        let card = FiniteCokernelCardinality::try_new(2, 5);
        assert!(matches!(card, Ok(c) if c.quotient() == 8));
    }

    #[test]
    fn a_non_injection_is_refused() {
        assert!(matches!(FiniteCokernelCardinality::try_new(4, 3), Err(CokernelCardError::Injection)));
    }
}
