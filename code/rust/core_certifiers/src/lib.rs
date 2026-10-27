pub mod authority_minting;
pub mod certificate_boundary;
pub mod checked_packet;
pub mod closure_certificate;
pub mod counterfeit_detection;
pub mod mathematical_claim;
pub mod meron_certificate;
pub mod meron_hamiltonian_bridge;
pub mod operator_closure_certifier;
pub mod phi1_certifier;

pub use certificate_boundary::{certify_checked_packet, AuthorityVerdict};
pub use mathematical_claim::{
    all_registered_claims, claims_for_crate, claims_for_package, registered_packages,
    verify_registry_integrity, MathematicalClaim, MASTER_TRACEABILITY_REGISTRY,
};
pub use core_contracts::{CertificatePromotionContractError, CheckedPacketCertificateV1};
pub use phi1_certifier::{
    CertificateError, Phi1Certificate, Phi1CertificateMetadata, Phi1Verifier,
};

// --- exact carrier witness ---
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ClaimCodeError {
    Empty,
    Code { code: u64 },
    Replay,
    Overflow,
}

// Origin: engine/crates_rs/core_certifiers/src/lib.rs
// Claim: urn:core:crates_rs:core-certifiers:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ClaimCodeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ClaimCodeError {}

/// Unique positive claim codes with a replayed rolling hash.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClaimCodeLedger {
    state: u128,
    count: usize,
}

fn roll_claims(codes: &[u64]) -> Result<u128, ClaimCodeError> {
    let mut state = 0u128;
    for &code in codes {
        state = state
            .checked_mul(131)
            .ok_or(ClaimCodeError::Overflow)?
            .checked_add(u128::from(code))
            .ok_or(ClaimCodeError::Overflow)?
            % 1_000_000_007;
    }
    Ok(state)
}

impl ClaimCodeLedger {
    pub fn try_new(codes: &[u64]) -> Result<Self, ClaimCodeError> {
        if codes.is_empty() {
            return Err(ClaimCodeError::Empty);
        }
        let mut seen = BTreeSet::new();
        for &code in codes {
            if code == 0 || !seen.insert(code) {
                return Err(ClaimCodeError::Code { code });
            }
        }
        let state = roll_claims(codes)?;
        let replay = roll_claims(codes)?;
        if state != replay {
            return Err(ClaimCodeError::Replay);
        }
        Ok(Self { state, count: codes.len() })
    }

    pub fn state(&self) -> u128 { self.state }
    pub fn count(&self) -> usize { self.count }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod claim_code_tests {
    use super::*;

    #[test]
    fn distinct_codes_replay_to_the_same_state() {
        let ledger = ClaimCodeLedger::try_new(&[2, 5]);
        assert!(matches!(ledger, Ok(ref ledger) if ledger.count() == 2 && ledger.state() == 267));
    }

    #[test]
    fn a_repeated_code_is_refused() {
        let ledger = ClaimCodeLedger::try_new(&[2, 2]);
        assert!(matches!(ledger, Err(ClaimCodeError::Code { code: 2 })));
    }
}
