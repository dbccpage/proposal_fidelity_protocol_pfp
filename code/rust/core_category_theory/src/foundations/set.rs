//! set shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_31173004;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_31173004<T> = std::result::Result<T, BoundaryError_31173004>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled set (elements as string tags).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Set {
    pub label: String,
    /// Element tags (not a formal carrier; diagnostic inventory only).
    pub elements: Vec<String>,
    pub notes: Vec<String>,
}

impl Set {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            elements: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_elements(label: impl Into<String>, elements: Vec<String>) -> Self {
        Self {
            label: label.into(),
            elements,
            notes: Vec::new(),
        }
    }

    pub fn cardinality(&self) -> usize {
        self.elements.len()
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        for (i, e) in self.elements.iter().enumerate() {
            if e.is_empty() {
                return Err(format!("empty element tag at index {i}"));
            }
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
        assert!(Set::new("x").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Set::new("").validate_shell().is_err());
    }

    #[test]
    fn with_elements_cardinality() {
        let s = Set::with_elements("S", vec!["a".into(), "b".into()]);
        assert_eq!(s.cardinality(), 2);
        assert!(s.validate_shell().is_ok());
    }

    #[test]
    fn rejects_empty_element_tag() {
        let s = Set::with_elements("S", vec!["a".into(), "".into()]);
        assert!(s.validate_shell().is_err());
    }
}

/// Refusal from an integer inclusion-exclusion count.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CardError {
    /// A cardinality overflowed.
    Overflow,
    /// `|A ∪ B| + |A ∩ B|` missed `|A| + |B|`.
    IdentityFailed { got: u32, expected: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/foundations/set.rs
// Claim: urn:core:crates_rs:core-category-theory:set:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CardError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CardError {}

/// Witness of `|A ∪ B| + |A ∩ B| = |A| + |B|` for finite sets of `u32`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CardWitness {
    union: u32,
    intersection: u32,
}

impl CardWitness {
    fn dedup_sorted(slice: &[u32]) -> Vec<u32> {
        let mut v = slice.to_vec();
        v.sort_unstable();
        v.dedup();
        v
    }

    fn count_intersection(a: &[u32], b: &[u32]) -> Result<u32, CardError> {
        let mut intersection = 0u32;
        for id in a {
            if b.contains(id) {
                intersection = intersection.checked_add(1).ok_or(CardError::Overflow)?;
            }
        }
        Ok(intersection)
    }

    /// Treat the slices as sets. Duplicates inside one slice are ignored.
    pub fn try_new(left: &[u32], right: &[u32]) -> Result<Self, CardError> {
        let a = Self::dedup_sorted(left);
        let b = Self::dedup_sorted(right);
        let mut union = a.clone();
        for id in &b {
            if !union.contains(id) {
                union.push(*id);
            }
        }
        let intersection = Self::count_intersection(&a, &b)?;
        let union_len = u32::try_from(union.len()).map_err(|_| CardError::Overflow)?;
        let left_len = u32::try_from(a.len()).map_err(|_| CardError::Overflow)?;
        let right_len = u32::try_from(b.len()).map_err(|_| CardError::Overflow)?;
        let got = union_len.checked_add(intersection).ok_or(CardError::Overflow)?;
        let expected = left_len.checked_add(right_len).ok_or(CardError::Overflow)?;
        if got != expected {
            return Err(CardError::IdentityFailed { got, expected });
        }
        Ok(Self { union: union_len, intersection })
    }

    /// Cardinality of the union.
    pub fn union(self) -> u32 { self.union }
    /// Cardinality of the intersection.
    pub fn intersection(self) -> u32 { self.intersection }
}

#[cfg(test)]
mod card_tests {
    use super::*;
    #[test]
    fn inclusion_exclusion_on_two_pairs() {
        let card = CardWitness::try_new(&[1, 2], &[2, 3]);
        assert!(matches!(card, Ok(c) if c.union() == 3 && c.intersection() == 1));
    }
}
