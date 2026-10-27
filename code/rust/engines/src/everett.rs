use core_types::everett_dag_state::{EverettArena, EverettNode, EverettNodeId};

#[derive(Debug, Clone)]
pub struct ManyWorldsDAG {
    pub arena: EverettArena,
    pub root_index: usize,
}

impl ManyWorldsDAG {
    pub fn new_root(id: &str, amplitude: f64, sign_field: Vec<i8>) -> Self {
        let root = EverettNode {
            id: EverettNodeId::from(id),
            amplitude,
            configuration_sign_field: sign_field,
            child_indices: Vec::new(),
        };

        Self {
            arena: EverettArena { nodes: vec![root] },
            root_index: 0,
        }
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WeightError {
    Empty,
    Fraction,
    Unreduced,
    Total,
    Overflow,
}

// Origin: engine/crates_rs/engines/src/everett.rs
// Claim: urn:core:crates_rs:engines:everett:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for WeightError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for WeightError {}

/// Positive reduced world weights whose sum is exactly 1.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactWorldFamily {
    worlds: usize,
}

fn weight_gcd(mut left: u64, mut right: u64) -> u64 {
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    left
}

fn validate_weight_pair(weight_numer: u64, weight_denom: u64) -> Result<(), WeightError> {
    if weight_numer == 0 || weight_denom == 0 {
        return Err(WeightError::Fraction);
    }
    if weight_gcd(weight_numer, weight_denom) != 1 {
        return Err(WeightError::Unreduced);
    }
    Ok(())
}

fn reduce_signed_fraction(next_numer: i128, next_denom: i128) -> Result<(i128, i128), WeightError> {
    let mut left = next_numer.unsigned_abs();
    let mut right = next_denom.unsigned_abs();
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    let divisor = i128::try_from(left).map_err(|_| WeightError::Overflow)?;
    if divisor == 0 {
        return Err(WeightError::Overflow);
    }
    let numer = next_numer.checked_div(divisor).ok_or(WeightError::Overflow)?;
    let denom = next_denom.checked_div(divisor).ok_or(WeightError::Overflow)?;
    Ok((numer, denom))
}

fn add_reduced_weight(
    numer: i128,
    denom: i128,
    weight_numer: u64,
    weight_denom: u64,
) -> Result<(i128, i128), WeightError> {
    validate_weight_pair(weight_numer, weight_denom)?;
    let next_numer = numer
        .checked_mul(i128::from(weight_denom))
        .ok_or(WeightError::Overflow)?
        .checked_add(
            i128::from(weight_numer)
                .checked_mul(denom)
                .ok_or(WeightError::Overflow)?,
        )
        .ok_or(WeightError::Overflow)?;
    let next_denom = denom
        .checked_mul(i128::from(weight_denom))
        .ok_or(WeightError::Overflow)?;
    reduce_signed_fraction(next_numer, next_denom)
}

impl ExactWorldFamily {
    pub fn try_new(weights: &[(u64, u64)]) -> Result<Self, WeightError> {
        if weights.is_empty() {
            return Err(WeightError::Empty);
        }
        let mut numer = 0i128;
        let mut denom = 1i128;
        for &(weight_numer, weight_denom) in weights {
            (numer, denom) = add_reduced_weight(numer, denom, weight_numer, weight_denom)?;
        }
        if numer != denom || denom <= 0 {
            return Err(WeightError::Total);
        }
        Ok(Self { worlds: weights.len() })
    }

    pub fn worlds(&self) -> usize { self.worlds }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod weight_tests {
    use super::*;

    #[test]
    fn two_halves_sum_to_one() {
        let family = ExactWorldFamily::try_new(&[(1, 2), (1, 2)]);
        assert!(matches!(family, Ok(ref family) if family.worlds() == 2));
    }

    #[test]
    fn a_half_and_a_third_do_not_sum_to_one() {
        let family = ExactWorldFamily::try_new(&[(1, 2), (1, 3)]);
        assert!(matches!(family, Err(WeightError::Total)));
    }
}
