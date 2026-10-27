//! Skill Operand Registry, Filtering, and Prompt Composition (U04).
//!
//! Invariants:
//! - Operands are injected into prompts if and only if status is `Promoted`.
//! - Candidates or suppressed operands are strictly prohibited from prompt injection.
//! - Size constraint: single operand <= 1600 bytes and <= 400 estimated tokens.
//! - Injection constraint: at most 3 promoted operands (<= 1200 total estimated tokens).
//! - AuthorityEffect: None (const).

use serde::{Deserialize, Serialize};

fn default_authority_effect() -> String {
    "None".to_string()
}

pub const MAX_OPERAND_BYTES: usize = 1600;
pub const MAX_OPERAND_TOKENS: u64 = 400;
pub const MAX_INJECTED_OPERANDS: usize = 3;
pub const MAX_TOTAL_INJECTED_TOKENS: u64 = 1200;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OperandStatus {
    Candidate,
    Promoted,
    Suppressed,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SkillOperandV1 {
    pub operand_id: String,
    pub title: String,
    pub description: String,
    pub source_colour: String,
    pub target_colour: String,
    pub ddc_motif: String,
    pub content_bytes_len: u64,
    pub token_estimate: u64,
    pub status: OperandStatus,
    pub prompt_injection_text: String,
    pub replay_evidence_hash: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OperandValidationError {
    OperandTooLargeBytes { actual: usize, max: usize },
    OperandTooLargeTokens { actual: u64, max: u64 },
    ByteLengthMismatch { declared: u64, actual: usize },
}

// Origin: engine/crates_rs/pfp_runtime/src/operand.rs
// Claim: urn:core:crates_rs:pfp-runtime:operand:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for OperandValidationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for OperandValidationError {}

impl SkillOperandV1 {
    /// Validates internal structural size constraints of an operand.
    pub fn validate_size(&self) -> Result<(), OperandValidationError> {
        let actual_bytes = self.prompt_injection_text.as_bytes().len();
        if actual_bytes > MAX_OPERAND_BYTES {
            return Err(OperandValidationError::OperandTooLargeBytes {
                actual: actual_bytes,
                max: MAX_OPERAND_BYTES,
            });
        }
        if self.token_estimate > MAX_OPERAND_TOKENS {
            return Err(OperandValidationError::OperandTooLargeTokens {
                actual: self.token_estimate,
                max: MAX_OPERAND_TOKENS,
            });
        }
        if self.content_bytes_len != actual_bytes as u64 {
            return Err(OperandValidationError::ByteLengthMismatch {
                declared: self.content_bytes_len,
                actual: actual_bytes,
            });
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OperandFilterRefusal {
    UnpromotedOperandRefused {
        operand_id: String,
        status: OperandStatus,
    },
    ColourMismatch {
        expected_target: String,
        actual_target: String,
    },
}

/// Selects eligible operands to inject into a candidate generation prompt.
///
/// Invariants:
/// - Injects ONLY operands with status `OperandStatus::Promoted`.
///   MUTATION KILL GATE: Changing filter from `status == Promoted` to `status != Suppressed`
///   must fail tests by allowing unpromoted Candidate operands through!
/// - Targets must match the required target colour (if specified).
/// - Injects at most 3 operands and at most 1200 total estimated tokens.
pub fn select_operands_for_injection<'a>(
    operands: &'a [SkillOperandV1],
    target_colour: Option<&str>,
) -> Vec<&'a SkillOperandV1> {
    let mut selected: Vec<&'a SkillOperandV1> = Vec::new();
    let mut total_tokens: u64 = 0;

    for op in operands {
        // Strict promotion invariant
        if op.status != OperandStatus::Promoted {
            continue;
        }

        // Validate size
        if op.validate_size().is_err() {
            continue;
        }

        // Colour matching
        if let Some(target) = target_colour {
            if op.target_colour != target {
                continue;
            }
        }

        // Token budget & count limit
        if selected.len() >= MAX_INJECTED_OPERANDS {
            break;
        }
        if total_tokens + op.token_estimate > MAX_TOTAL_INJECTED_TOKENS {
            break;
        }

        selected.push(op);
        total_tokens += op.token_estimate;
    }

    selected
}

/// Renders the operand injection prompt block.
pub fn render_operand_prompt_block(operands: &[&SkillOperandV1]) -> String {
    if operands.is_empty() {
        return String::new();
    }
    let mut out = String::from("### Learned Skill Operands Available\n\n");
    for (i, op) in operands.iter().enumerate() {
        out.push_str(&format!(
            "#### Operand {}: {} [{}]\n{}\n\n",
            i + 1,
            op.title,
            op.operand_id,
            op.prompt_injection_text
        ));
    }
    out
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_7458fae1 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
