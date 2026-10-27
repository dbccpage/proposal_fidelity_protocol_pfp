//! slice_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! C/c (objects over c): objects are morphisms x → c; morphisms are commuting triangles.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_48ca7680;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_48ca7680<T> = std::result::Result<T, BoundaryError_48ca7680>;
use serde::{Deserialize, Serialize};

/// Best-effort slice category shell C / apex.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct SliceCategoryShell {
    pub label: String,
    pub base_label: String,
    /// Apex object tag in the base category.
    pub apex: String,
    /// Object tags of the slice (typically names of morphisms into apex).
    pub objects: Vec<String>,
    pub notes: Vec<String>,
}

impl SliceCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_label: String::new(),
            apex: String::new(),
            objects: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn over(
        label: impl Into<String>,
        base_label: impl Into<String>,
        apex: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            base_label: base_label.into(),
            apex: apex.into(),
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
        if self.apex.is_empty() {
            return Err("empty apex".into());
        }
        for (i, o) in self.objects.iter().enumerate() {
            if o.is_empty() {
                return Err(format!("empty object tag at index {i}"));
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/category/slice_category.rs
// Claim: urn:core:crates_rs:core-category-theory:slice-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(SliceCategoryShell::over("C/c", "C", "c")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(SliceCategoryShell::new("").validate_shell().is_err());
        assert!(SliceCategoryShell::new("S").validate_shell().is_err());
    }
}

/// Finite slice over an apex fixed by `step`: every leg lands on the apex, and each mediator tracks `step`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SliceTriangle {
    legs: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SliceError {
    Bound,
    Apex,
    Leg,
    Triangle,
}

impl std::fmt::Display for SliceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SliceError::Bound => write!(formatter, "base size must lie in 1..=12"),
            SliceError::Apex => write!(formatter, "the apex is not a fixed point of the step"),
            SliceError::Leg => write!(formatter, "a leg does not land on the apex"),
            SliceError::Triangle => write!(formatter, "a mediator does not follow the step"),
        }
    }
}

impl std::error::Error for SliceError {}

fn validate_slice_step(base: usize, apex: usize, step: &[usize]) -> Result<(), SliceError> {
    if base == 0 || base > 12 || step.len() != base || apex >= base {
        return Err(SliceError::Bound);
    }
    if step.iter().any(|&image| image >= base) {
        return Err(SliceError::Bound);
    }
    if step[apex] != apex {
        return Err(SliceError::Apex);
    }
    Ok(())
}

fn validate_slice_legs(
    base: usize,
    apex: usize,
    step: &[usize],
    leg_sources: &[usize],
) -> Result<(), SliceError> {
    if leg_sources.is_empty() || leg_sources.len() > 12 {
        return Err(SliceError::Leg);
    }
    for &source in leg_sources {
        if source >= base || step[source] != apex {
            return Err(SliceError::Leg);
        }
    }
    Ok(())
}

fn validate_slice_mediators(
    step: &[usize],
    leg_sources: &[usize],
    mediators: &[(usize, usize)],
) -> Result<(), SliceError> {
    for &(from, to) in mediators {
        let source = *leg_sources.get(from).ok_or(SliceError::Triangle)?;
        let target = *leg_sources.get(to).ok_or(SliceError::Triangle)?;
        if step[source] != target {
            return Err(SliceError::Triangle);
        }
    }
    Ok(())
}

impl SliceTriangle {
    pub fn certify(
        base: usize,
        apex: usize,
        step: &[usize],
        leg_sources: &[usize],
        mediators: &[(usize, usize)],
    ) -> Result<Self, SliceError> {
        validate_slice_step(base, apex, step)?;
        validate_slice_legs(base, apex, step, leg_sources)?;
        validate_slice_mediators(step, leg_sources, mediators)?;
        Ok(Self {
            legs: leg_sources.len(),
        })
    }

    pub fn legs(&self) -> usize {
        self.legs
    }
}

#[cfg(test)]
mod slice_tests {
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
    fn a_step_into_the_apex_commutes_and_a_loop_does_not() {
        let slice = taken(SliceTriangle::certify(3, 2, &[1, 2, 2], &[1, 2], &[(0, 1)]));
        assert_eq!(slice.legs(), 2);
        assert!(SliceTriangle::certify(3, 2, &[1, 2, 2], &[1, 2], &[(0, 0)]).is_err());
    }
}
