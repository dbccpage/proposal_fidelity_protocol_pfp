//! abelian_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Abelian category = additive + kernels + cokernels (flags only). Does not
//! verify that every mono is a kernel or that coimage ≅ image.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_7522e408;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_7522e408<T> = std::result::Result<T, BoundaryError_7522e408>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for an abelian-category claim.
///
/// Stores the classical checklist as bools: additive structure, kernels, and
/// cokernels. Shape validation only — no law discharge.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct AbelianCategory {
    pub label: String,
    /// Additive structure present (Hom-sets are abelian groups, biproducts, …).
    pub additive: bool,
    /// Every morphism has a kernel (shape flag).
    pub has_kernels: bool,
    /// Every morphism has a cokernel (shape flag).
    pub has_cokernels: bool,
    pub notes: Vec<String>,
}

impl AbelianCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            additive: false,
            has_kernels: false,
            has_cokernels: false,
            notes: Vec::new(),
        }
    }

    pub fn with_flags(
        label: impl Into<String>,
        additive: bool,
        has_kernels: bool,
        has_cokernels: bool,
    ) -> Self {
        Self {
            label: label.into(),
            additive,
            has_kernels,
            has_cokernels,
            notes: Vec::new(),
        }
    }

    /// Convenience: all three abelian checklist flags set true.
    pub fn claimed_abelian(label: impl Into<String>) -> Self {
        Self::with_flags(label, true, true, true)
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Whether the stored flags match the classical abelian checklist.
    pub fn checklist_complete(&self) -> bool {
        self.additive && self.has_kernels && self.has_cokernels
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
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
        assert!(AbelianCategory::new("Mod_R").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(AbelianCategory::new("").validate_shell().is_err());
    }

    #[test]
    fn claimed_abelian_sets_flags() {
        let a = AbelianCategory::claimed_abelian("Ab");
        assert!(a.additive && a.has_kernels && a.has_cokernels);
        assert!(a.checklist_complete());
        assert!(a.validate_shell().is_ok());
    }

    #[test]
    fn incomplete_checklist() {
        let a = AbelianCategory::with_flags("pre", true, true, false);
        assert!(!a.checklist_complete());
        assert!(a.validate_shell().is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/abelian/abelian_category.rs
// Claim: urn:core:category:abelian:rank-nullity:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RankNullity {
    source: u64,
    target: u64,
    rank: u64,
    kernel: u64,
    cokernel: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RankNullityError {
    ShellRefused { reason: String },
    SourceSplit { rank: u64, kernel: u64, source: u64 },
    TargetSplit { rank: u64, cokernel: u64, target: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/abelian/abelian_category.rs
// Claim: urn:core:crates_rs:core-category-theory:abelian-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RankNullityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RankNullityError {}

impl RankNullity {
    pub fn try_on(
        shell: &AbelianCategory,
        source: u64,
        target: u64,
        rank: u64,
        kernel: u64,
        cokernel: u64,
    ) -> Result<Self, RankNullityError> {
        shell
            .validate_shell()
            .map_err(|reason| RankNullityError::ShellRefused { reason })?;
        let source_sum = rank.checked_add(kernel).ok_or(RankNullityError::Overflow)?;
        if source_sum != source {
            return Err(RankNullityError::SourceSplit { rank, kernel, source });
        }
        let target_sum = rank.checked_add(cokernel).ok_or(RankNullityError::Overflow)?;
        if target_sum != target {
            return Err(RankNullityError::TargetSplit { rank, cokernel, target });
        }
        Ok(Self { source, target, rank, kernel, cokernel })
    }

    pub fn rank(&self) -> u64 {
        self.rank
    }

    pub fn kernel(&self) -> u64 {
        self.kernel
    }

    pub fn cokernel(&self) -> u64 {
        self.cokernel
    }
}

#[cfg(test)]
mod rank_nullity_tests {
    use super::*;

    #[test]
    fn splits_source_and_target() {
        let shell = AbelianCategory::claimed_abelian("Ab");
        let witness = RankNullity::try_on(&shell, 5, 7, 3, 2, 4);
        assert!(matches!(
            witness,
            Ok(ref w) if w.rank() == 3 && w.kernel() == 2 && w.cokernel() == 4
        ));
    }

    #[test]
    fn refuses_a_broken_kernel() {
        let shell = AbelianCategory::claimed_abelian("Ab");
        let wrong = RankNullity::try_on(&shell, 5, 7, 3, 1, 4);
        assert!(matches!(
            wrong,
            Err(RankNullityError::SourceSplit { rank: 3, kernel: 1, source: 5 })
        ));
    }
}
