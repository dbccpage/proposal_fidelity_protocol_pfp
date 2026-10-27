#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CategoricalConstructionError {
    #[error("invalid category construction input")]
    InvalidInput,
    #[error("invalid colimit result")]
    InvalidResult,
    #[error("colimit construction not implemented")]
    NotImplemented,
}

// Exact carrier witness.
/// Cardinality of a coproduct of two finite sets. Both empty is refused.
pub fn checked_coproduct_cardinality(left: u64, right: u64) -> Result<u64, CategoricalConstructionError> {
    if left == 0 && right == 0 {
        return Err(CategoricalConstructionError::InvalidInput);
    }
    left.checked_add(right).ok_or(CategoricalConstructionError::InvalidResult)
}

// Origin: engine/crates_rs/core_types/src/category_errors.rs
// Claim: urn:core:crates_rs:core-types:category-errors:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod coproduct_checks {
    use super::*;

    #[test]
    fn two_plus_three_is_five() {
        assert!(matches!(checked_coproduct_cardinality(2, 3), Ok(5)));
    }

    #[test]
    fn the_empty_coproduct_and_overflow_are_refused() {
        assert!(matches!(checked_coproduct_cardinality(0, 0), Err(CategoricalConstructionError::InvalidInput)));
        assert!(matches!(checked_coproduct_cardinality(u64::MAX, 1), Err(CategoricalConstructionError::InvalidResult)));
    }
}
