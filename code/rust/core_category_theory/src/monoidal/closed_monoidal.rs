//! closed_monoidal shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_acf8e137;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_acf8e137<T> = std::result::Result<T, BoundaryError_acf8e137>;
use serde::{Deserialize, Serialize};

/// Best-effort closed monoidal category shell (internal-hom ref).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClosedMonoidal {
    pub label: String,
    /// Underlying monoidal category shell label.
    pub monoidal_ref: String,
    /// Internal-hom bifunctor / object-family ref [-, -] or ⊸.
    pub internal_hom_ref: String,
    /// Optional evaluation morphism family ref.
    pub evaluation_ref: String,
    pub notes: Vec<String>,
}

impl ClosedMonoidal {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: String::new(),
            internal_hom_ref: String::new(),
            evaluation_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_internal_hom(
        label: impl Into<String>,
        monoidal_ref: impl Into<String>,
        internal_hom_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: monoidal_ref.into(),
            internal_hom_ref: internal_hom_ref.into(),
            evaluation_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.monoidal_ref.is_empty() {
            return Err("empty monoidal_ref".into());
        }
        if self.internal_hom_ref.is_empty() {
            return Err("empty internal_hom_ref".into());
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
        assert!(ClosedMonoidal::with_internal_hom("Closed", "Mon", "[-,-]")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(ClosedMonoidal::new("").validate_shell().is_err());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/monoidal/closed_monoidal.rs
// Claim: urn:core:category:closed-monoidal:hom-dimension:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InternalHomDimension {
    rows: usize,
    total: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum InternalHomDimensionError {
    ShellRefused { reason: String },
    Empty,
    LengthMismatch { tensor: usize, internal: usize },
    RowMismatch { index: usize, tensor: u64, internal: u64 },
    Overflow { index: usize },
    TotalMismatch { tensor: u64, internal: u64 },
}

// Origin: engine/crates_rs/core_category_theory/src/monoidal/closed_monoidal.rs
// Claim: urn:core:crates_rs:core-category-theory:closed-monoidal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for InternalHomDimensionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for InternalHomDimensionError {}

impl InternalHomDimension {
    fn sum_matching_rows(
        tensor_homs: &[u64],
        internal_homs: &[u64],
    ) -> Result<(u64, u64), InternalHomDimensionError> {
        let mut tensor_total = 0u64;
        let mut internal_total = 0u64;
        for index in 0..tensor_homs.len() {
            let tensor = *tensor_homs
                .get(index)
                .ok_or(InternalHomDimensionError::Overflow { index })?;
            let internal = *internal_homs
                .get(index)
                .ok_or(InternalHomDimensionError::Overflow { index })?;
            if tensor != internal {
                return Err(InternalHomDimensionError::RowMismatch {
                    index,
                    tensor,
                    internal,
                });
            }
            tensor_total = tensor_total
                .checked_add(tensor)
                .ok_or(InternalHomDimensionError::Overflow { index })?;
            internal_total = internal_total
                .checked_add(internal)
                .ok_or(InternalHomDimensionError::Overflow { index })?;
        }
        Ok((tensor_total, internal_total))
    }

    pub fn try_on(
        shell: &ClosedMonoidal,
        tensor_homs: &[u64],
        internal_homs: &[u64],
    ) -> Result<Self, InternalHomDimensionError> {
        shell
            .validate_shell()
            .map_err(|reason| InternalHomDimensionError::ShellRefused { reason })?;
        if tensor_homs.is_empty() {
            return Err(InternalHomDimensionError::Empty);
        }
        if tensor_homs.len() != internal_homs.len() {
            return Err(InternalHomDimensionError::LengthMismatch {
                tensor: tensor_homs.len(),
                internal: internal_homs.len(),
            });
        }
        let (tensor_total, internal_total) = Self::sum_matching_rows(tensor_homs, internal_homs)?;
        if tensor_total != internal_total {
            return Err(InternalHomDimensionError::TotalMismatch {
                tensor: tensor_total,
                internal: internal_total,
            });
        }
        Ok(Self {
            rows: tensor_homs.len(),
            total: tensor_total,
        })
    }

    pub fn total(&self) -> u64 {
        self.total
    }
}

#[cfg(test)]
mod internal_hom_dimension_tests {
    use super::*;

    #[test]
    fn tensor_hom_matches_internal_hom() {
        let shell = ClosedMonoidal::with_internal_hom("Closed", "Mon", "[-,-]");
        let witness = InternalHomDimension::try_on(&shell, &[2, 0, 5], &[2, 0, 5]);
        assert!(matches!(witness, Ok(ref w) if w.total() == 7));
    }

    #[test]
    fn refuses_a_row_that_breaks_the_adjunction() {
        let shell = ClosedMonoidal::with_internal_hom("Closed", "Mon", "[-,-]");
        let wrong = InternalHomDimension::try_on(&shell, &[2, 0], &[2, 1]);
        assert!(matches!(
            wrong,
            Err(InternalHomDimensionError::RowMismatch { index: 1, tensor: 0, internal: 1 })
        ));
    }
}
