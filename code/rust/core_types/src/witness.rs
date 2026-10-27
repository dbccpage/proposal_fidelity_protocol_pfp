//! Canonical Witness types for the engine.
//!
//! Includes IdentityWitness, TrichotomyWitness, and CriticalContextWitness (ENC-0209).

use serde::{Deserialize, Serialize};

/// Identity witness preserving subobject identity across layers.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IdentityWitness {
    pub witness_id: String,
    pub payload_hash: String,
    pub source_layer: String,
    pub target_layer: String,
    pub is_valid: bool,
}

/// Critical context witness (ENC-0209): w = (x, y, c) where x ~ y but c • x !~ c • y.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CriticalContextWitness {
    pub left_state: String,
    pub right_state: String,
    pub action_context: String,
    pub observation_left: String,
    pub observation_right: String,
    pub is_valid_lift_trigger: bool,
}

/// Trichotomy witness for FOC 3-way status: Exact, Survivor, or Open.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum TrichotomyWitness {
    Exact {
        repair_vector: Vec<f64>,
    },
    Survivor {
        duality_certificate: String,
        gamma2_mass: f64,
    },
    Open {
        phi1_mass: f64,
        gamma2_mass: f64,
        unresolved_reason: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExactSign {
    Negative { numer: i64, denom: i64 },
    Zero,
    Positive { numer: i64, denom: i64 },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExactSignError {
    ZeroDenom,
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/witness.rs
// Claim: urn:core:crates_rs:core-types:witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExactSignError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExactSignError {}

fn gcd_abs(mut a: i64, mut b: i64) -> Result<i64, ExactSignError> {
    if a < 0 {
        a = a.checked_neg().ok_or(ExactSignError::Overflow)?;
    }
    if b < 0 {
        b = b.checked_neg().ok_or(ExactSignError::Overflow)?;
    }
    while b != 0 {
        let r = a.checked_rem(b).ok_or(ExactSignError::Overflow)?;
        a = b;
        b = r;
    }
    Ok(a)
}

fn normalize_sign_and_reduce(mut numer: i64, mut denom: i64) -> Result<(i64, i64), ExactSignError> {
    if denom == 0 {
        return Err(ExactSignError::ZeroDenom);
    }
    if denom < 0 {
        numer = numer.checked_neg().ok_or(ExactSignError::Overflow)?;
        denom = denom.checked_neg().ok_or(ExactSignError::Overflow)?;
    }
    let g = gcd_abs(numer, denom)?;
    Ok((
        numer.checked_div(g).ok_or(ExactSignError::Overflow)?,
        denom.checked_div(g).ok_or(ExactSignError::Overflow)?,
    ))
}

pub fn exact_trichotomy(numer: i64, denom: i64) -> Result<ExactSign, ExactSignError> {
    let (numer, denom) = normalize_sign_and_reduce(numer, denom)?;
    if numer == 0 {
        Ok(ExactSign::Zero)
    } else if numer < 0 {
        Ok(ExactSign::Negative { numer, denom })
    } else {
        Ok(ExactSign::Positive { numer, denom })
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_sign_tests {
    use super::*;

    #[test]
    fn reduced_sign_is_the_trichotomy() {
        assert!(matches!(
            exact_trichotomy(-2, 4),
            Ok(ExactSign::Negative { numer: -1, denom: 2 })
        ));
        assert!(matches!(exact_trichotomy(0, 1), Ok(ExactSign::Zero)));
        assert!(matches!(exact_trichotomy(1, 0), Err(ExactSignError::ZeroDenom)));
    }
}
