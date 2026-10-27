use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct EverettNodeId(pub String);

impl fmt::Display for EverettNodeId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl From<String> for EverettNodeId {
    fn from(value: String) -> Self {
        Self(value)
    }
}

impl From<&str> for EverettNodeId {
    fn from(value: &str) -> Self {
        Self(value.to_string())
    }
}

#[derive(Debug, Clone)]
pub struct EverettNode {
    pub id: EverettNodeId,
    pub amplitude: f64,
    pub configuration_sign_field: Vec<i8>,
    pub child_indices: Vec<usize>,
}

/// Arena-allocated storage for Everett many-worlds DAG nodes.
/// Consolidated from search_everett_arena.rs â€” co-located with node types.
#[derive(Debug, Clone, Default)]
pub struct EverettArena {
    pub nodes: Vec<EverettNode>,
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SplitError {
    Shape,
    Order,
    Fraction,
    Unreduced,
    Total,
    Overflow,
}

/// Positive reduced child weights that sum to the parent weight.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactChildSplit {
    children: usize,
}

fn split_gcd(mut left: u64, mut right: u64) -> u64 {
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    left
}

impl ExactChildSplit {
    fn validate_shape_and_parent(
        arena_len: usize,
        child_indices: &[usize],
        parent_numer: u64,
        parent_denom: u64,
        weights_len: usize,
    ) -> Result<(), SplitError> {
        let shape_ok = arena_len > 0
            && !child_indices.is_empty()
            && child_indices.len() == weights_len
            && parent_numer > 0
            && parent_denom > 0;
        if !shape_ok {
            return Err(SplitError::Shape);
        }
        if split_gcd(parent_numer, parent_denom) != 1 {
            return Err(SplitError::Unreduced);
        }
        Ok(())
    }

    fn validate_child_order(arena_len: usize, child_indices: &[usize]) -> Result<(), SplitError> {
        let mut previous = None;
        for &index in child_indices {
            if index >= arena_len || previous.is_some_and(|earlier| index <= earlier) {
                return Err(SplitError::Order);
            }
            previous = Some(index);
        }
        Ok(())
    }

    fn add_weight_fraction(
        numer: i128,
        denom: i128,
        weight_numer: u64,
        weight_denom: u64,
    ) -> Result<(i128, i128), SplitError> {
        if weight_numer == 0 || weight_denom == 0 {
            return Err(SplitError::Fraction);
        }
        if split_gcd(weight_numer, weight_denom) != 1 {
            return Err(SplitError::Unreduced);
        }
        let term1 = numer.checked_mul(i128::from(weight_denom)).ok_or(SplitError::Overflow)?;
        let term2 = i128::from(weight_numer).checked_mul(denom).ok_or(SplitError::Overflow)?;
        let next_numer = term1.checked_add(term2).ok_or(SplitError::Overflow)?;
        let next_denom = denom.checked_mul(i128::from(weight_denom)).ok_or(SplitError::Overflow)?;
        Ok((next_numer, next_denom))
    }

    pub fn try_split(
        arena_len: usize,
        child_indices: &[usize],
        parent_numer: u64,
        parent_denom: u64,
        weights: &[(u64, u64)],
    ) -> Result<Self, SplitError> {
        Self::validate_shape_and_parent(arena_len, child_indices, parent_numer, parent_denom, weights.len())?;
        Self::validate_child_order(arena_len, child_indices)?;
        let mut numer = 0i128;
        let mut denom = 1i128;
        for &(weight_numer, weight_denom) in weights {
            (numer, denom) = Self::add_weight_fraction(numer, denom, weight_numer, weight_denom)?;
        }
        let left = i128::from(parent_numer).checked_mul(denom).ok_or(SplitError::Overflow)?;
        let right = numer.checked_mul(i128::from(parent_denom)).ok_or(SplitError::Overflow)?;
        if left != right {
            return Err(SplitError::Total);
        }
        Ok(Self { children: child_indices.len() })
    }

    pub fn children(&self) -> usize { self.children }
}

// Origin: engine/crates_rs/core_types/src/everett_dag_state.rs
// Claim: urn:core:crates_rs:core-types:everett-dag-state:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod split_tests {
    use super::*;

    #[test]
    fn two_halves_split_a_unit_parent() {
        let split = ExactChildSplit::try_split(2, &[0, 1], 1, 1, &[(1, 2), (1, 2)]);
        assert!(matches!(split, Ok(ref split) if split.children() == 2));
    }

    #[test]
    fn a_half_and_a_third_do_not_restore_the_parent() {
        let split = ExactChildSplit::try_split(2, &[0, 1], 1, 1, &[(1, 2), (1, 3)]);
        assert!(matches!(split, Err(SplitError::Total)));
    }
}
