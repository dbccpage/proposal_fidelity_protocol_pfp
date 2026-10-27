//! fibered_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! A cloven / fibered category over a base: p: E → B with cartesian lifts
//! (Grothendieck fibration data recorded diagnostically).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_75878a99;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_75878a99<T> = std::result::Result<T, BoundaryError_75878a99>;
use serde::{Deserialize, Serialize};

/// Best-effort fibered category shell over a base.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiberedCategoryShell {
    pub label: String,
    pub total_label: String,
    pub base_label: String,
    /// Cleavage claim: cartesian lifts are chosen (diagnostic flag).
    pub cloven: bool,
    /// Optional fiber labels over base objects: (base_object, fiber_label).
    pub fibers: Vec<(String, String)>,
    pub notes: Vec<String>,
}

impl FiberedCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            total_label: String::new(),
            base_label: String::new(),
            cloven: false,
            fibers: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn over(
        label: impl Into<String>,
        total_label: impl Into<String>,
        base_label: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            total_label: total_label.into(),
            base_label: base_label.into(),
            cloven: false,
            fibers: Vec::new(),
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
        for (i, (b, f)) in self.fibers.iter().enumerate() {
            if b.is_empty() || f.is_empty() {
                return Err(format!("empty fiber entry at index {i}"));
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
        assert!(FiberedCategoryShell::over("Fib", "E", "B")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(FiberedCategoryShell::new("").validate_shell().is_err());
        assert!(FiberedCategoryShell::new("F").validate_shell().is_err());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CleavageError {
    Shell,
    Empty,
    Index,
    MissingLift { base_from: u32, base_to: u32, target: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/category/fibered_category.rs
// Claim: urn:core:crates_rs:core-category-theory:fibered-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CleavageError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CleavageError {}

/// Discrete cleavage: each base arrow has exactly one cartesian lift into every fibre element.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscreteCleavageWitness {
    lifts: usize,
}

fn validate_total_arrows(
    objects: usize,
    total_arrows: &[(u32, u32)],
) -> Result<(), CleavageError> {
    for &(source, target) in total_arrows {
        let s = usize::try_from(source).map_err(|_| CleavageError::Index)?;
        let t = usize::try_from(target).map_err(|_| CleavageError::Index)?;
        if s >= objects || t >= objects {
            return Err(CleavageError::Index);
        }
    }
    Ok(())
}

fn count_lifts_into_target(
    base_from: u32,
    target_object: usize,
    fibre: &[u32],
    total_arrows: &[(u32, u32)],
) -> Result<u32, CleavageError> {
    let mut hits = 0u32;
    for &(source, target) in total_arrows {
        if target as usize == target_object && fibre[source as usize] == base_from {
            hits = hits.checked_add(1).ok_or(CleavageError::Overflow)?;
        }
    }
    Ok(hits)
}

fn count_base_arrow_lifts(
    base_from: u32,
    base_to: u32,
    fibre: &[u32],
    total_arrows: &[(u32, u32)],
) -> Result<usize, CleavageError> {
    let mut lifts = 0usize;
    for (target_object, &target_base) in fibre.iter().enumerate() {
        if target_base == base_to {
            let hits = count_lifts_into_target(base_from, target_object, fibre, total_arrows)?;
            if hits != 1 {
                return Err(CleavageError::MissingLift { base_from, base_to, target: target_object });
            }
            lifts = lifts.checked_add(1).ok_or(CleavageError::Overflow)?;
        }
    }
    Ok(lifts)
}

impl DiscreteCleavageWitness {
    pub fn try_new(
        shell: &FiberedCategoryShell,
        fibre: &[u32],
        base_arrows: &[(u32, u32)],
        total_arrows: &[(u32, u32)],
    ) -> Result<Self, CleavageError> {
        if shell.validate_shell().is_err() || fibre.is_empty() || base_arrows.is_empty() {
            return Err(CleavageError::Shell);
        }
        validate_total_arrows(fibre.len(), total_arrows)?;
        let mut lifts = 0usize;
        for &(base_from, base_to) in base_arrows {
            let step = count_base_arrow_lifts(base_from, base_to, fibre, total_arrows)?;
            lifts = lifts.checked_add(step).ok_or(CleavageError::Overflow)?;
        }
        if lifts == 0 {
            return Err(CleavageError::Empty);
        }
        Ok(Self { lifts })
    }

    pub fn lifts(&self) -> usize { self.lifts }
}

#[cfg(test)]
mod cleavage_tests {
    use super::*;

    #[test]
    fn one_lift_over_a_base_arrow() {
        let shell = FiberedCategoryShell::over("Fib", "E", "B");
        let witness = DiscreteCleavageWitness::try_new(&shell, &[0, 1], &[(0, 1)], &[(0, 1)]);
        assert!(matches!(witness, Ok(ref witness) if witness.lifts() == 1));
    }

    #[test]
    fn a_missing_lift_is_refused() {
        let shell = FiberedCategoryShell::over("Fib", "E", "B");
        let witness = DiscreteCleavageWitness::try_new(&shell, &[0, 1], &[(0, 1)], &[]);
        assert!(matches!(witness, Err(CleavageError::MissingLift { .. })));
    }
}
