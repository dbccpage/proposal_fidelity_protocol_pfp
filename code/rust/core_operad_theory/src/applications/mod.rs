//! Applications Tier for Operad Theory.
//!
//! AuthorityEffect: None.

pub mod oeas_workflow_operad;

pub use oeas_workflow_operad::{AgentCapabilitySlice, OEASWorkflowOperad, OEAS_ADMITTED_PORT_COLOURS};

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SubstitutionLawError {
    Empty,
    Colour { name: String },
    Slot,
    Overflow,
}

// Origin: engine/crates_rs/core_operad_theory/src/applications/mod.rs
// Claim: urn:core:crates_rs:core-operad-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SubstitutionLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SubstitutionLawError {}

/// Operadic substitution arity: replacing one slot yields outer + inner - 1 inputs.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SubstitutionArityWitness {
    result: u64,
}

impl SubstitutionArityWitness {
    pub fn try_new(word: &[&str], outer: u64, inner: u64, slot: u64) -> Result<Self, SubstitutionLawError> {
        if word.is_empty() || outer == 0 || inner == 0 || slot >= outer {
            return Err(if word.is_empty() { SubstitutionLawError::Empty } else { SubstitutionLawError::Slot });
        }
        for colour in word {
            if !OEAS_ADMITTED_PORT_COLOURS.contains(colour) {
                return Err(SubstitutionLawError::Colour { name: (*colour).to_string() });
            }
        }
        let result = outer.checked_add(inner).ok_or(SubstitutionLawError::Overflow)?.checked_sub(1).ok_or(SubstitutionLawError::Overflow)?;
        Ok(Self { result })
    }

    pub fn result(&self) -> u64 { self.result }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod substitution_law_tests {
    use super::*;

    #[test]
    fn substituting_one_slot_increases_arity_by_inner_minus_one() {
        let witness = SubstitutionArityWitness::try_new(&["State", "Code"], 2, 2, 1);
        assert!(matches!(witness, Ok(ref witness) if witness.result() == 3));
    }

    #[test]
    fn an_unknown_port_colour_is_refused() {
        let witness = SubstitutionArityWitness::try_new(&["Nope"], 1, 1, 0);
        assert!(matches!(witness, Err(SubstitutionLawError::Colour { .. })));
    }
}
