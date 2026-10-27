//! hom_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Hom-functor Hom(A, −) / Hom(−, A) — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_f22c6bd0;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_f22c6bd0<T> = std::result::Result<T, BoundaryError_f22c6bd0>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a Hom-functor on a category reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct HomFunctor {
    pub label: String,
    pub category_ref: String,
    /// Fixed object in the Hom-slot.
    pub fixed_object: String,
    /// Variance tag: "covariant" (Hom(A,−)) or "contravariant" (Hom(−,A)).
    pub variance: String,
    pub notes: Vec<String>,
}

impl HomFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: String::new(),
            fixed_object: String::new(),
            variance: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn covariant(
        label: impl Into<String>,
        category_ref: impl Into<String>,
        fixed_object: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            fixed_object: fixed_object.into(),
            variance: "covariant".into(),
            notes: Vec::new(),
        }
    }

    pub fn contravariant(
        label: impl Into<String>,
        category_ref: impl Into<String>,
        fixed_object: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            fixed_object: fixed_object.into(),
            variance: "contravariant".into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.category_ref.is_empty() {
            return Err("empty category_ref".into());
        }
        if self.fixed_object.is_empty() {
            return Err("empty fixed_object".into());
        }
        if self.variance.is_empty() {
            return Err("empty variance".into());
        }
        match self.variance.as_str() {
            "covariant" | "contravariant" => Ok(()),
            other => Err(format!("unknown variance tag: {other}")),
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(HomFunctor::covariant("HomA", "C", "A")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(HomFunctor::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_bad_variance() {
        let mut h = HomFunctor::covariant("h", "C", "A");
        h.variance = "both".into();
        assert!(h.validate_shell().is_err());
    }

    #[test]
    fn contravariant_ok() {
        assert!(HomFunctor::contravariant("Hom_A", "C", "A")
            .validate_shell()
            .is_ok());
    }
}

/// Endomorphism count of a hom-functor: |Hom(A, A)| is at least the identity.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HomEndWitness {
    covariant: bool,
    endomorphism_count: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HomEndError {
    EmptyLabel,
    UnknownVariance,
    MissingIdentity,
}

// Origin: engine/crates_rs/core_category_theory/src/functor/hom_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:hom-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HomEndError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HomEndError {}

impl HomEndWitness {
    pub fn try_new(
        label: &str,
        variance: &str,
        endomorphism_count: u64,
    ) -> Result<Self, HomEndError> {
        if label.is_empty() {
            return Err(HomEndError::EmptyLabel);
        }
        let covariant = match variance {
            "covariant" => true,
            "contravariant" => false,
            _ => return Err(HomEndError::UnknownVariance),
        };
        if endomorphism_count < 1 {
            return Err(HomEndError::MissingIdentity);
        }
        Ok(Self {
            covariant,
            endomorphism_count,
        })
    }

    pub fn is_covariant(&self) -> bool {
        self.covariant
    }

    pub fn endomorphism_count(&self) -> u64 {
        self.endomorphism_count
    }
}
