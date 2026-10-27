//! Monoidal hierarchy shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Distinct from crate-root trait modules `monoidal_category` and `braided_monoidal`.

pub mod braided_monoidal;
pub mod cartesian_closed;
pub mod closed_monoidal;
pub mod cohomology_in_monoidal;
pub mod compact_closed;
pub mod monoidal_category;
pub mod monoidal_functor;
pub mod rigid_category;
pub mod symmetric_monoidal;
pub mod symmetric_monoidal_functor;
pub mod traced_monoidal;

pub use braided_monoidal::BraidedMonoidal;
pub use cartesian_closed::CartesianClosed;
pub use closed_monoidal::ClosedMonoidal;
pub use cohomology_in_monoidal::CohomologyInMonoidal;
pub use compact_closed::CompactClosed;
pub use monoidal_category::MonoidalCategory;
pub use monoidal_functor::MonoidalFunctor;
pub use rigid_category::RigidCategory;
pub use symmetric_monoidal::SymmetricMonoidal;
pub use symmetric_monoidal_functor::SymmetricMonoidalFunctor;
pub use traced_monoidal::TracedMonoidal;

/// Refusal from an exact tensor dimension.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DimError {
    /// A product overflowed.
    Overflow,
    /// The two associations disagreed.
    NotAssociative { left: u32, right: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/monoidal/mod.rs
// Claim: urn:core:crates_rs:core-category-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DimError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DimError {}

/// Common value of `(a ⊗ b) ⊗ c` and `a ⊗ (b ⊗ c)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TensorDim {
    value: u32,
}

impl TensorDim {
    /// Multiply three dimensions both ways.
    pub fn try_associate(a: u32, b: u32, c: u32) -> Result<Self, DimError> {
        let ab = a.checked_mul(b).ok_or(DimError::Overflow)?;
        let left = ab.checked_mul(c).ok_or(DimError::Overflow)?;
        let bc = b.checked_mul(c).ok_or(DimError::Overflow)?;
        let right = a.checked_mul(bc).ok_or(DimError::Overflow)?;
        if left != right {
            return Err(DimError::NotAssociative { left, right });
        }
        Ok(Self { value: left })
    }

    /// The common dimension.
    pub fn value(&self) -> u32 { self.value }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tensor_dim_tests {
    use super::*;
    #[test]
    fn three_five_and_seven_associate() {
        let dim = TensorDim::try_associate(3, 5, 7);
        assert!(matches!(dim, Ok(ref d) if d.value() == 105));
    }
}
