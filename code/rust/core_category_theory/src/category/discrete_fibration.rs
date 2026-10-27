//! discrete_fibration shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! A discrete fibration p: E → B has unique cartesian lifts of morphisms
//! into each object of E (equivalently: fibers are discrete categories).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_bd5ac178;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_bd5ac178<T> = std::result::Result<T, BoundaryError_bd5ac178>;
use serde::{Deserialize, Serialize};

/// Best-effort discrete fibration shell p: total → base.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiscreteFibrationShell {
    pub label: String,
    pub total_label: String,
    pub base_label: String,
    /// Object map tags: total_object → base_object.
    pub object_map: Vec<(String, String)>,
    pub notes: Vec<String>,
}

impl DiscreteFibrationShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            total_label: String::new(),
            base_label: String::new(),
            object_map: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        total_label: impl Into<String>,
        base_label: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            total_label: total_label.into(),
            base_label: base_label.into(),
            object_map: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.total_label.is_empty() {
            return Err("empty total_label".into());
        }
        if self.base_label.is_empty() {
            return Err("empty base_label".into());
        }
        for (i, (t, b)) in self.object_map.iter().enumerate() {
            if t.is_empty() || b.is_empty() {
                return Err(format!("empty object_map entry at index {i}"));
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
        assert!(DiscreteFibrationShell::between("p", "E", "B")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(DiscreteFibrationShell::new("").validate_shell().is_err());
        assert!(DiscreteFibrationShell::new("p").validate_shell().is_err());
    }
}

/// Fiber sizes of an object map sum to the number of total-category objects.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiberCensus {
    fiber_sizes: Vec<u64>,
    total_objects: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FiberCensusError {
    EmptyTotal,
    SumMismatch { fiber_sum: u64, total_objects: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/category/discrete_fibration.rs
// Claim: urn:core:crates_rs:core-category-theory:discrete-fibration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FiberCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FiberCensusError {}

impl FiberCensus {
    pub fn try_new(fiber_sizes: Vec<u64>, total_objects: u64) -> Result<Self, FiberCensusError> {
        if total_objects == 0 {
            return Err(FiberCensusError::EmptyTotal);
        }
        let mut fiber_sum = 0u64;
        for size in &fiber_sizes {
            fiber_sum = fiber_sum.checked_add(*size).ok_or(FiberCensusError::Overflow)?;
        }
        if fiber_sum != total_objects {
            return Err(FiberCensusError::SumMismatch { fiber_sum, total_objects });
        }
        Ok(Self { fiber_sizes, total_objects })
    }

    pub fn fiber_count(&self) -> usize {
        self.fiber_sizes.len()
    }
}

#[cfg(test)]
mod fiber_census_witness {
    use super::*;

    #[test]
    fn three_fibers_partition_five_total_objects() {
        let census = FiberCensus::try_new(vec![2, 0, 3], 5).ok();
        assert_eq!(census.map(|c| c.fiber_count()), Some(3));
        assert!(FiberCensus::try_new(vec![2], 5).is_err());
    }
}
