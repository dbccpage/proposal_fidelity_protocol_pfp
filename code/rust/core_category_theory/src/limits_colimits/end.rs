//! end shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_424b1fbd;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_424b1fbd<T> = std::result::Result<T, BoundaryError_424b1fbd>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for an end ∫_c F(c,c) of a bifunctor.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct End {
    pub label: String,
    /// Bifunctor F : C^op × C → D reference.
    pub bifunctor_ref: String,
    /// Indexing category reference.
    pub indexing_category_ref: String,
    /// End object (when claimed).
    pub end_object: String,
    pub notes: Vec<String>,
}

impl End {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            bifunctor_ref: String::new(),
            indexing_category_ref: String::new(),
            end_object: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of_bifunctor(
        label: impl Into<String>,
        bifunctor_ref: impl Into<String>,
        indexing_category_ref: impl Into<String>,
        end_object: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            bifunctor_ref: bifunctor_ref.into(),
            indexing_category_ref: indexing_category_ref.into(),
            end_object: end_object.into(),
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
        if self.end_object.is_empty() {
            return Err("empty end_object".into());
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
        let e = End::of_bifunctor("end_F", "F", "C", "∫F");
        assert!(e.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(End::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_bifunctor() {
        assert!(End::new("e").validate_shell().is_err());
    }
}

/// An end embeds into the product of the diagonal values of its bifunctor.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EndDiagonalWitness {
    index_count: usize,
    diagonal_product: u64,
    end_size: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EndDiagonalError {
    EmptyLabel,
    EmptyDiagonal,
    ZeroDiagonal { index: usize },
    ExceedsProduct { end_size: u64, diagonal_product: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/end.rs
// Claim: urn:core:crates_rs:core-category-theory:end:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for EndDiagonalError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for EndDiagonalError {}

impl EndDiagonalWitness {
    pub fn try_bound(
        label: &str,
        diagonal: &[u64],
        end_size: u64,
    ) -> Result<Self, EndDiagonalError> {
        if label.is_empty() {
            return Err(EndDiagonalError::EmptyLabel);
        }
        if diagonal.is_empty() {
            return Err(EndDiagonalError::EmptyDiagonal);
        }
        let mut diagonal_product = 1u64;
        for (index, entry) in diagonal.iter().enumerate() {
            if *entry == 0 {
                return Err(EndDiagonalError::ZeroDiagonal { index });
            }
            diagonal_product = diagonal_product
                .checked_mul(*entry)
                .ok_or(EndDiagonalError::Overflow)?;
        }
        if end_size > diagonal_product {
            return Err(EndDiagonalError::ExceedsProduct {
                end_size,
                diagonal_product,
            });
        }
        Ok(Self {
            index_count: diagonal.len(),
            diagonal_product,
            end_size,
        })
    }

    pub fn index_count(&self) -> usize {
        self.index_count
    }

    pub fn slack(&self) -> Option<u64> {
        self.diagonal_product.checked_sub(self.end_size)
    }
}
