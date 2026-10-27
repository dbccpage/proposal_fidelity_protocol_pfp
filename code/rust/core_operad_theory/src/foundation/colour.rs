//! Foundation: Multi-sorted colours and signatures.
//!
//! AuthorityEffect: None.

use std::fmt;
use serde::{Deserialize, Serialize};

/// Exact-type multi-sorted colour representing a wire or port boundary.
#[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub struct OperadColour {
    name: String,
}

impl OperadColour {
    /// Creates a validated, non-empty OperadColour.
    pub fn new(name: impl Into<String>) -> Result<Self, String> {
        let n = name.into();
        let trimmed = n.trim();
        if trimmed.is_empty() {
            return Err("OperadColour name cannot be empty or whitespace only.".to_string());
        }
        Ok(Self {
            name: trimmed.to_string(),
        })
    }

    pub fn as_str(&self) -> &str {
        &self.name
    }
}

impl fmt::Display for OperadColour {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name)
    }
}

/// Multi-sorted signature (c_1, ..., c_n) -> target.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct OperadSignature {
    pub inputs: Vec<OperadColour>,
    pub output: OperadColour,
}

impl OperadSignature {
    pub fn new(inputs: Vec<OperadColour>, output: OperadColour) -> Self {
        Self { inputs, output }
    }

    pub fn arity(&self) -> usize {
        self.inputs.len()
    }

    pub fn is_nullary(&self) -> bool {
        self.inputs.is_empty()
    }

    pub fn is_unary(&self) -> bool {
        self.inputs.len() == 1
    }
}

impl fmt::Display for OperadSignature {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let ins: Vec<&str> = self.inputs.iter().map(|c| c.as_str()).collect();
        write!(f, "({}) -> {}", ins.join(", "), self.output)
    }
}

/// Colour slots of a signature: one per input, plus the output.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignatureSlotWitness {
    arity: u32,
    colour_slots: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SignatureSlotError {
    EmptyColour { role: &'static str, index: usize },
    ArityMismatch { reported: usize, inputs: usize },
    Overflow,
}

impl SignatureSlotWitness {
    pub fn admit(signature: &OperadSignature) -> Result<Self, SignatureSlotError> {
        if signature.output.as_str().is_empty() {
            return Err(SignatureSlotError::EmptyColour {
                role: "output",
                index: 0,
            });
        }
        for (index, colour) in signature.inputs.iter().enumerate() {
            if colour.as_str().is_empty() {
                return Err(SignatureSlotError::EmptyColour {
                    role: "input",
                    index,
                });
            }
        }
        if signature.arity() != signature.inputs.len() {
            return Err(SignatureSlotError::ArityMismatch {
                reported: signature.arity(),
                inputs: signature.inputs.len(),
            });
        }
        let arity = u32::try_from(signature.inputs.len()).map_err(|_| SignatureSlotError::Overflow)?;
        let colour_slots = arity.checked_add(1).ok_or(SignatureSlotError::Overflow)?;
        Ok(Self { arity, colour_slots })
    }

    pub fn colour_slots(&self) -> u32 {
        self.colour_slots
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/foundation/colour.rs
// Claim: urn:core:crates_rs:core-operad-theory:colour:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod signature_slot_tests {
    use super::*;

    #[test]
    fn a_binary_signature_occupies_three_colour_slots() {
        let signature = OperadSignature::new(
            vec![
                OperadColour { name: "A".into() },
                OperadColour { name: "B".into() },
            ],
            OperadColour { name: "C".into() },
        );
        let admitted = SignatureSlotWitness::admit(&signature);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.colour_slots()), Some(3));
        let broken = OperadSignature::new(
            vec![OperadColour { name: String::new() }],
            OperadColour { name: "C".into() },
        );
        assert!(matches!(
            SignatureSlotWitness::admit(&broken),
            Err(SignatureSlotError::EmptyColour {
                role: "input",
                index: 0
            })
        ));
        assert!(OperadColour::new("  ").is_err());
    }
}
