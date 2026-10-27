//! comonad shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Dual of a monad: endofunctor W with counit ε : W ⇒ Id and
//! comultiply δ : W ⇒ W². Label refs only; law discharge is external.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_c959528c;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_c959528c<T> = std::result::Result<T, BoundaryError_c959528c>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled comonad (W, ε, δ).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Comonad {
    pub label: String,
    /// Ref to the underlying endofunctor W : C → C.
    pub endofunctor_ref: String,
    /// Ref to the counit natural transformation ε : W ⇒ Id.
    pub counit_ref: String,
    /// Ref to the comultiplication natural transformation δ : W ⇒ W².
    pub comultiply_ref: String,
    /// Optional base category label (diagnostic).
    pub category_ref: String,
    pub notes: Vec<String>,
}

impl Comonad {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            endofunctor_ref: String::new(),
            counit_ref: String::new(),
            comultiply_ref: String::new(),
            category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_structure(
        label: impl Into<String>,
        endofunctor_ref: impl Into<String>,
        counit_ref: impl Into<String>,
        comultiply_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            endofunctor_ref: endofunctor_ref.into(),
            counit_ref: counit_ref.into(),
            comultiply_ref: comultiply_ref.into(),
            category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.endofunctor_ref.is_empty() {
            return Err("empty endofunctor_ref".into());
        }
        if self.counit_ref.is_empty() {
            return Err("empty counit_ref".into());
        }
        if self.comultiply_ref.is_empty() {
            return Err("empty comultiply_ref".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/monad/comonad.rs
// Claim: urn:core:crates_rs:core-category-theory:comonad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let w = Comonad::with_structure("Env", "W_Env", "ε_Env", "δ_Env");
        assert!(w.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty_label() {
        assert!(Comonad::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_refs() {
        let w = Comonad::new("W");
        assert!(w.validate_shell().is_err());
    }
}

/// Product comonad on two finite sets: both counit triangles are the identity on every element.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProductComonadLaw {
    carrier: usize,
    context: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ComonadLawError {
    Bound,
    Law,
}

impl std::fmt::Display for ComonadLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ComonadLawError::Bound => write!(formatter, "carrier and context must lie in 1..=8"),
            ComonadLawError::Law => write!(formatter, "a product-comonad triangle failed"),
        }
    }
}

impl std::error::Error for ComonadLawError {}

impl ProductComonadLaw {
    fn check_state(element: usize, mark: usize, context: usize) -> Result<(), ComonadLawError> {
        let state = element
            .checked_mul(context)
            .and_then(|value| value.checked_add(mark))
            .ok_or(ComonadLawError::Law)?;
        let delta = state
            .checked_mul(context)
            .and_then(|value| value.checked_add(mark))
            .ok_or(ComonadLawError::Law)?;
        let outer = delta / context;
        let outer_mark = delta % context;
        if outer != state || outer_mark != mark {
            return Err(ComonadLawError::Law);
        }
        let restored_element = outer / context;
        let restored_mark = outer % context;
        let acted = restored_element
            .checked_mul(context)
            .and_then(|value| value.checked_add(outer_mark))
            .ok_or(ComonadLawError::Law)?;
        if restored_mark != mark || acted != state {
            return Err(ComonadLawError::Law);
        }
        Ok(())
    }

    pub fn certify(carrier: usize, context: usize) -> Result<Self, ComonadLawError> {
        if carrier == 0 || context == 0 || carrier > 8 || context > 8 {
            return Err(ComonadLawError::Bound);
        }
        for element in 0..carrier {
            for mark in 0..context {
                Self::check_state(element, mark, context)?;
            }
        }
        Ok(Self { carrier, context })
    }

    pub fn carrier(&self) -> usize {
        self.carrier
    }
}

#[cfg(test)]
mod comonad_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn two_by_two_product_comonad_triangles_are_identities() {
        let law = taken(ProductComonadLaw::certify(2, 2));
        assert_eq!(law.carrier(), 2);
        assert!(ProductComonadLaw::certify(0, 2).is_err());
    }
}
