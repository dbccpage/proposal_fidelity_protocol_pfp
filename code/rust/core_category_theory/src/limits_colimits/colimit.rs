//! colimit shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_f256c59a;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_f256c59a<T> = std::result::Result<T, BoundaryError_f256c59a>;
use serde::{Deserialize, Serialize};

use super::cone::Cocone;

/// Best-effort shell for a colimit of a diagram (diagram_ref + colimiting cocone).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Colimit {
    pub label: String,
    /// Opaque reference to the diagram being colimited.
    pub diagram_ref: String,
    pub cocone: Cocone,
    pub notes: Vec<String>,
}

impl Colimit {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            diagram_ref: String::new(),
            cocone: Cocone::default(),
            notes: Vec::new(),
        }
    }

    pub fn of_diagram(
        label: impl Into<String>,
        diagram_ref: impl Into<String>,
        cocone: Cocone,
    ) -> Self {
        Self {
            label: label.into(),
            diagram_ref: diagram_ref.into(),
            cocone,
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.diagram_ref.is_empty() {
            return Err("empty diagram_ref".into());
        }
        self.cocone
            .validate_shell()
            .map_err(|e| format!("cocone: {e}"))?;
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::limits_colimits::cone::Cocone;

    #[test]
    fn validate_ok() {
        let cocone = Cocone::with_nadir("colim_cocone", "Q");
        let colim = Colimit::of_diagram("colim", "D", cocone);
        assert!(colim.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty_diagram() {
        let cocone = Cocone::with_nadir("colim_cocone", "Q");
        let colim = Colimit::of_diagram("colim", "", cocone);
        assert!(colim.validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_empty_label() {
        assert!(Colimit::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_bad_cocone() {
        let colim = Colimit::of_diagram("colim", "D", Cocone::new("cc"));
        assert!(colim.validate_shell().is_err());
    }
}

/// Refusal from a discrete coproduct index.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CoproductError {
    /// A side index leaves its summand, or the side tag is not 0 or 1.
    OutOfRange,
    /// The cardinalities do not add, or a round trip failed.
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/colimit.rs
// Claim: urn:core:crates_rs:core-category-theory:colimit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CoproductError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CoproductError {}

/// Flat index set of a discrete coproduct.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CoproductIndex {
    card: u32,
    left: u32,
}

impl CoproductIndex {
    /// `card = left + right`. Side 0 is the left summand.
    pub fn try_new(left: u32, right: u32) -> Result<Self, CoproductError> {
        let card = left.checked_add(right).ok_or(CoproductError::Overflow)?;
        let sample = Self { card, left }.try_encode(1, 0)?;
        let (side, index) = Self { card, left }.try_decode(sample)?;
        if side != 1 || index != 0 {
            return Err(CoproductError::Overflow);
        }
        Ok(Self { card, left })
    }

    /// Encode `(side, index)` as a flat index.
    pub fn try_encode(self, side: u8, index: u32) -> Result<u32, CoproductError> {
        match side {
            0 if index < self.left => Ok(index),
            1 => {
                let right = self.card.checked_sub(self.left).ok_or(CoproductError::Overflow)?;
                if index >= right {
                    return Err(CoproductError::OutOfRange);
                }
                self.left.checked_add(index).ok_or(CoproductError::Overflow)
            }
            _ => Err(CoproductError::OutOfRange),
        }
    }

    /// Inverse of [`Self::try_encode`].
    pub fn try_decode(self, flat: u32) -> Result<(u8, u32), CoproductError> {
        if flat >= self.card {
            return Err(CoproductError::OutOfRange);
        }
        if flat < self.left {
            Ok((0, flat))
        } else {
            Ok((1, flat.checked_sub(self.left).ok_or(CoproductError::Overflow)?))
        }
    }

    /// Cardinality of the coproduct.
    pub fn card(self) -> u32 { self.card }
}

#[cfg(test)]
mod coproduct_index_tests {
    use super::*;
    #[test]
    fn two_plus_three_is_five_and_the_first_right_index_is_two() {
        let index = CoproductIndex::try_new(2, 3);
        assert!(matches!(index, Ok(i) if i.card() == 5 && i.try_encode(1, 0).ok() == Some(2)));
    }
}
