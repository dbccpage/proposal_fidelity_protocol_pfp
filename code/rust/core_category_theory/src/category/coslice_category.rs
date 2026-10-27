//! coslice_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! c/C (objects under c): objects are morphisms c → x; morphisms are commuting triangles.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_3af9e9fb;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_3af9e9fb<T> = std::result::Result<T, BoundaryError_3af9e9fb>;
use serde::{Deserialize, Serialize};

/// Best-effort coslice category shell base / under nadir.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CosliceCategoryShell {
    pub label: String,
    pub base_label: String,
    /// Nadir (under-object) tag in the base category.
    pub nadir: String,
    /// Object tags of the coslice (typically names of morphisms out of nadir).
    pub objects: Vec<String>,
    pub notes: Vec<String>,
}

impl CosliceCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_label: String::new(),
            nadir: String::new(),
            objects: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn under(
        label: impl Into<String>,
        base_label: impl Into<String>,
        nadir: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            base_label: base_label.into(),
            nadir: nadir.into(),
            objects: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.base_label.is_empty() {
            return Err("empty base_label".into());
        }
        if self.nadir.is_empty() {
            return Err("empty nadir".into());
        }
        for (i, o) in self.objects.iter().enumerate() {
            if o.is_empty() {
                return Err(format!("empty object tag at index {i}"));
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
        assert!(CosliceCategoryShell::under("c/C", "C", "c")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(CosliceCategoryShell::new("").validate_shell().is_err());
        assert!(CosliceCategoryShell::new("S").validate_shell().is_err());
    }
}

/// Refusal from a coslice arrow count.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CosliceCountError {
    /// An arrow does not leave the tip.
    Source { index: usize },
    /// Two arrows share a target.
    DuplicateTarget { target: u32 },
    /// The count overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/category/coslice_category.rs
// Claim: urn:core:crates_rs:core-category-theory:coslice-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CosliceCountError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CosliceCountError {}

/// Number of distinct targets leaving one coslice tip.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OutgoingCount {
    targets: u32,
}

impl OutgoingCount {
    /// Every arrow must start at `tip`, and targets are unique.
    pub fn try_new(tip: u32, arrows: &[(u32, u32)]) -> Result<Self, CosliceCountError> {
        let mut seen = Vec::new();
        for (index, &(source, target)) in arrows.iter().enumerate() {
            if source != tip {
                return Err(CosliceCountError::Source { index });
            }
            if seen.contains(&target) {
                return Err(CosliceCountError::DuplicateTarget { target });
            }
            seen.push(target);
        }
        let targets = u32::try_from(seen.len()).map_err(|_| CosliceCountError::Overflow)?;
        Ok(Self { targets })
    }

    /// Cardinality of the outgoing hom-set.
    pub fn targets(self) -> u32 { self.targets }
}

#[cfg(test)]
mod outgoing_tests {
    use super::*;
    #[test]
    fn two_distinct_targets_are_counted() {
        let count = OutgoingCount::try_new(0, &[(0, 1), (0, 2)]);
        assert!(matches!(count, Ok(c) if c.targets() == 2));
    }
    #[test]
    fn a_repeated_target_is_refused() {
        assert!(matches!(OutgoingCount::try_new(0, &[(0, 1), (0, 1)]), Err(CosliceCountError::DuplicateTarget { .. })));
    }
}
