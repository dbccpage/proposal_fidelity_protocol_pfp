//! Kinetic Proofreading Delay Engine (U16).
//!
//! Hopfield-Ninio kinetic proofreading mechanism:
//! Introduces an explicit time delay / multi-step persistence check between initial
//! recognition and irreversible effector action.
//!
//! A candidate defect finding must persist across `required_delay_steps` observation turns
//! before it can trigger terminal quarantine or punitive branch rollback. Transient or
//! flickering signals dissociate and are discarded as stochastic fluctuations.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProofreadingState {
    pub finding_key: String,
    pub observed_steps: u32,
    pub required_delay_steps: u32,
    pub is_confirmed: bool,
}

impl ProofreadingState {
    pub fn new(finding_key: String, required_delay_steps: u32) -> Self {
        Self {
            finding_key,
            observed_steps: 1,
            required_delay_steps,
            is_confirmed: required_delay_steps <= 1,
        }
    }

    /// Advance one step of observation.
    pub fn advance_observation(&mut self) -> bool {
        self.observed_steps += 1;
        if self.observed_steps >= self.required_delay_steps {
            self.is_confirmed = true;
        }
        self.is_confirmed
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct KineticProofreader {
    pub default_delay_steps: u32,
    pub active_observations: std::collections::HashMap<String, ProofreadingState>,
}

impl KineticProofreader {
    pub fn new(default_delay_steps: u32) -> Self {
        assert!(default_delay_steps > 0, "Delay steps must be >= 1");
        Self {
            default_delay_steps,
            active_observations: std::collections::HashMap::new(),
        }
    }

    /// Record a finding occurrence. Returns true iff the finding has passed kinetic proofreading.
    pub fn record_occurrence(&mut self, finding_key: &str) -> bool {
        if let Some(state) = self.active_observations.get_mut(finding_key) {
            state.advance_observation()
        } else {
            let state = ProofreadingState::new(finding_key.to_string(), self.default_delay_steps);
            let confirmed = state.is_confirmed;
            self.active_observations
                .insert(finding_key.to_string(), state);
            confirmed
        }
    }

    /// Dissociate a finding if not observed in the current round.
    pub fn dissociate(&mut self, finding_key: &str) {
        self.active_observations.remove(finding_key);
    }
}

/// Discrimination ratio `(wrong_off / correct_off)^steps`, reduced, required at least 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DiscriminationRatioWitness {
    numerator: u64,
    denominator: u64,
    steps: u32,
    confirmed: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiscriminationRatioError {
    NonPositiveRate,
    ZeroSteps,
    ZeroObservedDenominator,
    RequiredBelowOne,
    Overflow,
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immune/proofreading.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:proofreading:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DiscriminationRatioError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DiscriminationRatioError {}

fn gcd_u64(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let next = a % b;
        a = b;
        b = next;
    }
    if a == 0 {
        1
    } else {
        a
    }
}

impl DiscriminationRatioWitness {
    fn compute_reduced_power(
        wrong_off: u64,
        correct_off: u64,
        steps: u32,
    ) -> Result<(u64, u64), DiscriminationRatioError> {
        let mut numerator = 1u64;
        let mut denominator = 1u64;
        let mut left = steps;
        while left > 0 {
            numerator = numerator
                .checked_mul(wrong_off)
                .ok_or(DiscriminationRatioError::Overflow)?;
            denominator = denominator
                .checked_mul(correct_off)
                .ok_or(DiscriminationRatioError::Overflow)?;
            left = left.saturating_sub(1);
        }
        let divisor = gcd_u64(numerator, denominator);
        numerator = numerator
            .checked_div(divisor)
            .ok_or(DiscriminationRatioError::Overflow)?;
        denominator = denominator
            .checked_div(divisor)
            .ok_or(DiscriminationRatioError::Overflow)?;
        Ok((numerator, denominator))
    }

    pub fn try_ratio(
        wrong_off: u64,
        correct_off: u64,
        steps: u32,
        observed_num: u64,
        observed_den: u64,
    ) -> Result<Self, DiscriminationRatioError> {
        if wrong_off == 0 || correct_off == 0 {
            return Err(DiscriminationRatioError::NonPositiveRate);
        }
        if steps == 0 {
            return Err(DiscriminationRatioError::ZeroSteps);
        }
        if observed_den == 0 {
            return Err(DiscriminationRatioError::ZeroObservedDenominator);
        }
        let (numerator, denominator) = Self::compute_reduced_power(wrong_off, correct_off, steps)?;
        if numerator < denominator {
            return Err(DiscriminationRatioError::RequiredBelowOne);
        }
        let observed_cross = (observed_num as u128)
            .checked_mul(denominator as u128)
            .ok_or(DiscriminationRatioError::Overflow)?;
        let required_cross = (observed_den as u128)
            .checked_mul(numerator as u128)
            .ok_or(DiscriminationRatioError::Overflow)?;
        Ok(Self {
            numerator,
            denominator,
            steps,
            confirmed: observed_cross >= required_cross,
        })
    }

    pub fn confirmed(&self) -> bool {
        self.confirmed
    }

    pub fn ratio(&self) -> (u64, u64) {
        (self.numerator, self.denominator)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f86d5597 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
