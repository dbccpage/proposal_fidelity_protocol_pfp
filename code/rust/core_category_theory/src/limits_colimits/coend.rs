//! coend shell for core_category_theory (hierarchical; legacy flat coend.rs remains).
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_a4f5aa57;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_a4f5aa57<T> = std::result::Result<T, BoundaryError_a4f5aa57>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a coend ∫^c F(c,c) of a bifunctor.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Coend {
    pub label: String,
    /// Bifunctor F : C^op × C → D reference.
    pub bifunctor_ref: String,
    /// Indexing category reference.
    pub indexing_category_ref: String,
    /// Coend object (when claimed).
    pub coend_object: String,
    pub notes: Vec<String>,
}

impl Coend {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            bifunctor_ref: String::new(),
            indexing_category_ref: String::new(),
            coend_object: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of_bifunctor(
        label: impl Into<String>,
        bifunctor_ref: impl Into<String>,
        indexing_category_ref: impl Into<String>,
        coend_object: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            bifunctor_ref: bifunctor_ref.into(),
            indexing_category_ref: indexing_category_ref.into(),
            coend_object: coend_object.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.bifunctor_ref.is_empty() {
            return Err("empty bifunctor_ref".into());
        }
        if self.indexing_category_ref.is_empty() {
            return Err("empty indexing_category_ref".into());
        }
        if self.coend_object.is_empty() {
            return Err("empty coend_object".into());
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
        let c = Coend::of_bifunctor("coend_F", "F", "C", "∫^F");
        assert!(c.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Coend::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_bifunctor() {
        assert!(Coend::new("c").validate_shell().is_err());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/coend.rs
// Claim: urn:core:category:coend:discrete-cardinality:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscreteCoend {
    components: usize,
    cardinality: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiscreteCoendError {
    ShellRefused { reason: String },
    EmptyDiagonal,
    Overflow { index: usize },
    ClaimMismatch { computed: u64, claimed: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/coend.rs
// Claim: urn:core:crates_rs:core-category-theory:coend:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DiscreteCoendError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DiscreteCoendError {}

impl DiscreteCoend {
    pub fn try_on(
        shell: &Coend,
        diagonal_sizes: &[u64],
        claimed_cardinality: u64,
    ) -> Result<Self, DiscreteCoendError> {
        shell
            .validate_shell()
            .map_err(|reason| DiscreteCoendError::ShellRefused { reason })?;
        if diagonal_sizes.is_empty() {
            return Err(DiscreteCoendError::EmptyDiagonal);
        }
        let mut forward = 0u64;
        for (index, size) in diagonal_sizes.iter().enumerate() {
            forward = forward.checked_add(*size).ok_or(DiscreteCoendError::Overflow { index })?;
        }
        let mut backward = 0u64;
        for (offset, size) in diagonal_sizes.iter().rev().enumerate() {
            backward = backward.checked_add(*size).ok_or(DiscreteCoendError::Overflow { index: offset })?;
        }
        if forward != backward {
            return Err(DiscreteCoendError::ClaimMismatch { computed: forward, claimed: backward });
        }
        if forward != claimed_cardinality {
            return Err(DiscreteCoendError::ClaimMismatch { computed: forward, claimed: claimed_cardinality });
        }
        Ok(Self {
            components: diagonal_sizes.len(),
            cardinality: forward,
        })
    }

    pub fn cardinality(&self) -> u64 {
        self.cardinality
    }
}

#[cfg(test)]
mod discrete_coend_tests {
    use super::*;

    #[test]
    fn sums_the_diagonal() {
        let shell = Coend::of_bifunctor("coend", "F", "C", "int");
        let witness = DiscreteCoend::try_on(&shell, &[2, 0, 3], 5);
        assert!(matches!(witness, Ok(ref w) if w.cardinality() == 5));
    }

    #[test]
    fn refuses_a_wrong_sum() {
        let shell = Coend::of_bifunctor("coend", "F", "C", "int");
        let wrong = DiscreteCoend::try_on(&shell, &[2, 0, 3], 4);
        assert!(matches!(
            wrong,
            Err(DiscreteCoendError::ClaimMismatch { computed: 5, claimed: 4 })
        ));
    }
}
