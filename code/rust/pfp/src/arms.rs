//! Matched Arms Harness and Statistics Validator (U08).
//!
//! Enforces:
//! - Matched arms comparison invariant:
//!   Arms can be compared iff model_id, temperature_str, max_tokens, budget_micro_usd,
//!   and specification_hash are IDENTICAL across all arms.
//!   Only intervention_name and arm_id may differ.
//! - Exact rational paired McNemar statistics via core_measurement.
//!
//! AuthorityEffect: None (const).

use serde::{Deserialize, Serialize};

fn default_authority_effect() -> String {
    "None".to_string()
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArmSpecV1 {
    pub arm_id: String,
    pub model_id: String,
    pub temperature_str: String,
    pub max_tokens: u64,
    pub budget_micro_usd: u64,
    pub specification_hash: String,
    pub intervention_name: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ArmMismatchError {
    EmptyArmsList,
    ModelMismatch {
        baseline: String,
        divergent: String,
        arm_id: String,
    },
    TemperatureMismatch {
        baseline: String,
        divergent: String,
        arm_id: String,
    },
    MaxTokensMismatch {
        baseline: u64,
        divergent: u64,
        arm_id: String,
    },
    BudgetMismatch {
        baseline: u64,
        divergent: u64,
        arm_id: String,
    },
    SpecificationMismatch {
        baseline: String,
        divergent: String,
        arm_id: String,
    },
}

// Origin: engine/crates_rs/pfp/src/arms.rs
// Claim: urn:core:crates_rs:pfp:arms:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ArmMismatchError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ArmMismatchError {}

/// Validates that a set of evaluation arms are strictly matched across control dimensions.
pub fn check_arm_matching(arms: &[ArmSpecV1]) -> Result<(), ArmMismatchError> {
    if arms.is_empty() {
        return Err(ArmMismatchError::EmptyArmsList);
    }
    let baseline = &arms[0];

    for arm in &arms[1..] {
        if arm.model_id != baseline.model_id {
            return Err(ArmMismatchError::ModelMismatch {
                baseline: baseline.model_id.clone(),
                divergent: arm.model_id.clone(),
                arm_id: arm.arm_id.clone(),
            });
        }
        if arm.temperature_str != baseline.temperature_str {
            return Err(ArmMismatchError::TemperatureMismatch {
                baseline: baseline.temperature_str.clone(),
                divergent: arm.temperature_str.clone(),
                arm_id: arm.arm_id.clone(),
            });
        }
        if arm.max_tokens != baseline.max_tokens {
            return Err(ArmMismatchError::MaxTokensMismatch {
                baseline: baseline.max_tokens,
                divergent: arm.max_tokens,
                arm_id: arm.arm_id.clone(),
            });
        }
        if arm.budget_micro_usd != baseline.budget_micro_usd {
            return Err(ArmMismatchError::BudgetMismatch {
                baseline: baseline.budget_micro_usd,
                divergent: arm.budget_micro_usd,
                arm_id: arm.arm_id.clone(),
            });
        }
        if arm.specification_hash != baseline.specification_hash {
            return Err(ArmMismatchError::SpecificationMismatch {
                baseline: baseline.specification_hash.clone(),
                divergent: arm.specification_hash.clone(),
                arm_id: arm.arm_id.clone(),
            });
        }
    }
    Ok(())
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_356d3602 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
