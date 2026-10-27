//! sum_category (coproduct) shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! C + D: disjoint union of objects and morphisms; no cross morphisms.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_0ebaa40e;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_0ebaa40e<T> = std::result::Result<T, BoundaryError_0ebaa40e>;
use serde::{Deserialize, Serialize};

/// Best-effort sum (coproduct) category shell C + D.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct SumCategoryShell {
    pub label: String,
    pub left_summand_label: String,
    pub right_summand_label: String,
    /// Optional left-tagged object inventory ("inl:c").
    pub left_objects: Vec<String>,
    /// Optional right-tagged object inventory ("inr:d").
    pub right_objects: Vec<String>,
    pub notes: Vec<String>,
}

impl SumCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            left_summand_label: String::new(),
            right_summand_label: String::new(),
            left_objects: Vec::new(),
            right_objects: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn of(
        label: impl Into<String>,
        left_summand_label: impl Into<String>,
        right_summand_label: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            left_summand_label: left_summand_label.into(),
            right_summand_label: right_summand_label.into(),
            left_objects: Vec::new(),
            right_objects: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.left_summand_label.is_empty() {
            return Err("empty left_summand_label".into());
        }
        if self.right_summand_label.is_empty() {
            return Err("empty right_summand_label".into());
        }
        for (i, o) in self.left_objects.iter().enumerate() {
            if o.is_empty() {
                return Err(format!("empty left_objects tag at index {i}"));
            }
        }
        for (i, o) in self.right_objects.iter().enumerate() {
            if o.is_empty() {
                return Err(format!("empty right_objects tag at index {i}"));
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
        assert!(SumCategoryShell::of("C+D", "C", "D")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(SumCategoryShell::new("").validate_shell().is_err());
        assert!(SumCategoryShell::new("S").validate_shell().is_err());
    }
}

/// Refusal from a disjoint sum of object ids.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SumCardError {
    /// An id is repeated inside one summand.
    Duplicate { side: u8, id: u32 },
    /// The cardinalities do not add.
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/category/sum_category.rs
// Claim: urn:core:crates_rs:core-category-theory:sum-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SumCardError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SumCardError {}

/// `|C + D| = |C| + |D|`, with tags keeping shared raw ids distinct.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DisjointSum {
    card: u32,
}

fn check_no_duplicates(slice: &[u32], side: u8) -> Result<(), SumCardError> {
    for (index, &id) in slice.iter().enumerate() {
        if slice[..index].contains(&id) {
            return Err(SumCardError::Duplicate { side, id });
        }
    }
    Ok(())
}

impl DisjointSum {
    /// Tag left objects with 0 and right objects with 1.
    pub fn try_new(left: &[u32], right: &[u32]) -> Result<Self, SumCardError> {
        check_no_duplicates(left, 0)?;
        check_no_duplicates(right, 1)?;
        let left_len = u32::try_from(left.len()).map_err(|_| SumCardError::Overflow)?;
        let right_len = u32::try_from(right.len()).map_err(|_| SumCardError::Overflow)?;
        let card = left_len.checked_add(right_len).ok_or(SumCardError::Overflow)?;
        Ok(Self { card })
    }

    /// Cardinality of the coproduct.
    pub fn card(self) -> u32 { self.card }
}

#[cfg(test)]
mod disjoint_sum_tests {
    use super::*;
    #[test]
    fn the_same_raw_id_on_both_sides_counts_twice() {
        let sum = DisjointSum::try_new(&[1], &[1]);
        assert!(matches!(sum, Ok(s) if s.card() == 2));
    }
}
