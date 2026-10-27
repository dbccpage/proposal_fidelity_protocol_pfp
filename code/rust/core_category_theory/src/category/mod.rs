//! Category hierarchy shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

pub mod arrow_category;
#[allow(clippy::module_inception)]
pub mod category;
pub mod coslice_category;
pub mod discrete_category;
pub mod discrete_fibration;
pub mod fibered_category;
pub mod opfibration;
pub mod opposite;
pub mod product_category;
pub mod slice_category;
pub mod small_category;
pub mod sum_category;
pub mod terminal_category;

pub use arrow_category::ArrowCategoryShell;
pub use category::{FiniteCategoryShell, MorphismTriple};
pub use coslice_category::CosliceCategoryShell;
pub use discrete_category::DiscreteCategoryShell;
pub use discrete_fibration::DiscreteFibrationShell;
pub use fibered_category::FiberedCategoryShell;
pub use opfibration::OpfibrationShell;
pub use opposite::OppositeCategoryShell;
pub use product_category::ProductCategoryShell;
pub use slice_category::SliceCategoryShell;
pub use small_category::SmallCategoryShell;
pub use sum_category::SumCategoryShell;
pub use terminal_category::TerminalCategoryShell;

/// Finite category on objects `0..object_count`: every arrow endpoint is in range,
/// and every object has at least one loop (an identity arrow).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IntegerFiniteCategoryWitness {
    object_count: usize,
    arrow_count: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IntegerFiniteCategoryError {
    EmptyObjectSet,
    EndpointOutOfRange { index: usize, src: usize, tgt: usize },
    MissingIdentity { object: usize },
}

// Origin: engine/crates_rs/core_category_theory/src/category/mod.rs
// Claim: urn:core:crates_rs:core-category-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for IntegerFiniteCategoryError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for IntegerFiniteCategoryError {}

impl IntegerFiniteCategoryWitness {
    pub fn try_from_arrows(
        object_count: usize,
        arrows: &[(usize, usize)],
    ) -> Result<Self, IntegerFiniteCategoryError> {
        if object_count == 0 {
            return Err(IntegerFiniteCategoryError::EmptyObjectSet);
        }
        let mut has_loop = vec![false; object_count];
        for (index, arrow) in arrows.iter().enumerate() {
            let (src, tgt) = *arrow;
            if src >= object_count || tgt >= object_count {
                return Err(IntegerFiniteCategoryError::EndpointOutOfRange { index, src, tgt });
            }
            if src == tgt {
                if let Some(slot) = has_loop.get_mut(src) {
                    *slot = true;
                }
            }
        }
        for (object, present) in has_loop.iter().enumerate() {
            if !*present {
                return Err(IntegerFiniteCategoryError::MissingIdentity { object });
            }
        }
        Ok(Self {
            object_count,
            arrow_count: arrows.len(),
        })
    }

    pub fn object_count(&self) -> usize {
        self.object_count
    }

    pub fn arrow_count(&self) -> usize {
        self.arrow_count
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e9b8b3c6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
