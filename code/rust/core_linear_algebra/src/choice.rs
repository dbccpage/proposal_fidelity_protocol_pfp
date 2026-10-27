//! Linear algebra specific choice metadata.

pub trait Choice {}

pub struct WithChoice<T, C: Choice> {
    pub value: T,
    choice: C,
}

impl<T, C: Choice> WithChoice<T, C> {
    pub fn new(value: T, choice: C) -> Self {
        Self { value, choice }
    }

    pub fn inner(&self) -> &T {
        &self.value
    }

    pub fn choice(&self) -> &C {
        &self.choice
    }

    pub fn forget(self) -> T {
        self.value
    }
}

use crate::basis::{BasisDescriptor, BasisError};
use crate::change_basis::BasisIsomorphism;
use thiserror::Error;

/// Errors for linear algebra choices.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum BasisChoiceError {
    #[error("basis error: {0}")]
    Basis(#[from] BasisError),
}

/// A selected basis descriptor for an object.
///
/// This is choice metadata, not a proof that every object admits a basis.
/// It records a declared coordinate convention.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BasisChoice {
    descriptor: BasisDescriptor,
}

impl BasisChoice {
    #[must_use]
    pub fn new(descriptor: BasisDescriptor) -> Self {
        Self { descriptor }
    }

    #[must_use]
    pub fn descriptor(&self) -> &BasisDescriptor {
        &self.descriptor
    }

    #[must_use]
    pub fn into_descriptor(self) -> BasisDescriptor {
        self.descriptor
    }
}

impl Choice for BasisChoice {}

/// Types that can be explicitly equipped with a declared basis choice.
///
/// This is declaration-level metadata. It does not certify that the object
/// actually has the declared basis.
pub trait WithChosenBasis: Sized {
    fn with_chosen_basis(self, basis: BasisDescriptor) -> WithChoice<Self, BasisChoice> {
        WithChoice::new(self, BasisChoice::new(basis))
    }
}

/// Apply a basis isomorphism to an already basis-equipped object.
///
/// Certification strength is inherited from `BasisIsomorphism<T>`.
pub trait ChangeBasisExt<T>: Sized {
    type Output;

    fn change_basis(
        self,
        iso: &BasisIsomorphism<T>,
    ) -> Result<WithChoice<Self::Output, BasisChoice>, BasisChoiceError>;
}

// Origin: engine/crates_rs/core_linear_algebra/src/choice.rs
// Claim: urn:core:crates_rs:core-linear-algebra:choice:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::basis::BasisId;

    #[derive(Debug, Clone, PartialEq, Eq)]
    struct DummyVectorSpace;

    impl WithChosenBasis for DummyVectorSpace {}

    #[test]
    fn attaches_basis_choice_metadata() -> Result<(), BasisError> {
        let basis = BasisDescriptor::new(BasisId::new("B")?, 3);

        let chosen = DummyVectorSpace.with_chosen_basis(basis.clone());

        assert_eq!(chosen.choice().descriptor(), &basis);

        Ok(())
    }

    #[test]
    fn attaches_basis_without_changing_value() -> Result<(), BasisError> {
        let basis = BasisDescriptor::new(BasisId::new("B")?, 3);

        let value = DummyVectorSpace;
        let chosen = value.clone().with_chosen_basis(basis.clone());

        assert_eq!(chosen.choice().descriptor(), &basis);
        assert_eq!(chosen.inner(), &value);

        Ok(())
    }
}
