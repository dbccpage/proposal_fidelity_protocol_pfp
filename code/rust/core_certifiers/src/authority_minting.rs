//! Deprecated compatibility module.
//!
//! The old module name is retained so downstream imports keep compiling, but
//! every exported operation now seals evidence only. No item in this module
//! constructs authority.

#[deprecated(note = "use core_certifiers::certificate_boundary")]
pub use crate::certificate_boundary::{certify_checked_packet, AuthorityVerdict};

/// Count of the seven packet-bound guards. Absence is the none-record.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GuardCensus {
    effect: String,
    affirmative: u8,
    negative: u8,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum GuardCensusError {
    Certified,
    Effect,
    Width,
}

impl std::fmt::Display for GuardCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Certified => write!(formatter, "a checked-packet verdict must not say Certified"),
            Self::Effect => write!(formatter, "effect is outside None and Refused"),
            Self::Width => write!(formatter, "guard bits do not sum to seven"),
        }
    }
}

impl std::error::Error for GuardCensusError {}

impl GuardCensus {
    pub fn effect(&self) -> &str {
        &self.effect
    }

    pub fn affirmative(&self) -> u8 {
        self.affirmative
    }

    pub fn negative(&self) -> u8 {
        self.negative
    }
}

fn tally_guard_bits(guards: Option<[bool; 7]>) -> Result<(u8, u8), GuardCensusError> {
    let Some(guards) = guards else {
        return Ok((0u8, 0u8));
    };
    let mut yes = 0u8;
    let mut no = 0u8;
    for bit in guards {
        if bit {
            yes = yes.checked_add(1).ok_or(GuardCensusError::Width)?;
        } else {
            no = no.checked_add(1).ok_or(GuardCensusError::Width)?;
        }
    }
    let width = yes.checked_add(no).ok_or(GuardCensusError::Width)?;
    if width != 7 {
        return Err(GuardCensusError::Width);
    }
    Ok((yes, no))
}

/// The firewall record is either a none-record or seven IsAuth bits, and it never says Certified.
pub fn admit_verdict(verdict: &AuthorityVerdict) -> Result<GuardCensus, GuardCensusError> {
    if verdict.effect == "Certified" {
        return Err(GuardCensusError::Certified);
    }
    if verdict.effect != "None" && verdict.effect != "Refused" {
        return Err(GuardCensusError::Effect);
    }
    let (affirmative, negative) = tally_guard_bits(verdict.guards)?;
    Ok(GuardCensus {
        effect: verdict.effect.clone(),
        affirmative,
        negative,
    })
}

// Origin: engine/crates_rs/core_certifiers/src/authority_minting.rs
// Claim: urn:core:crates_rs:core-certifiers:authority-minting:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn taken(result: Result<GuardCensus, GuardCensusError>) -> GuardCensus {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn a_full_guard_record_sums_to_seven() {
        let verdict = AuthorityVerdict {
            effect: "None".to_owned(),
            terminal: None,
            guards: Some([true, true, true, false, true, false, true]),
            descent_replay_hash: None,
            firewall: "packet".to_owned(),
        };
        let census = taken(admit_verdict(&verdict));
        assert_eq!(census.affirmative() + census.negative(), 7);
        assert_eq!(census.effect(), "None");
    }

    #[test]
    fn certified_is_refused() {
        let verdict = AuthorityVerdict {
            effect: "Certified".to_owned(),
            terminal: None,
            guards: None,
            descent_replay_hash: None,
            firewall: "packet".to_owned(),
        };
        assert!(matches!(
            admit_verdict(&verdict),
            Err(GuardCensusError::Certified)
        ));
    }
}
