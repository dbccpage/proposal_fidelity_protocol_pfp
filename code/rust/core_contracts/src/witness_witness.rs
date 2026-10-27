//! Witness module for law enforcement.
//!
//! Canonical witness types live in `crate::witness::evidence`.
//! Test-time property macros live beside the persistent evidence producers but
//! do not emit persisted witness artifacts.

use crate::kinds::Capability;
use super::evidence::WITNESS_FORBIDDEN_CAPABILITIES;

/// The forbidden-capability fence named by `WITNESS_FORBIDDEN_CAPABILITIES`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ForbiddenCapabilityWitness {
    forbidden_count: u64,
    named_count: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ForbiddenCapabilityWitnessError {
    Overflow,
    CountDrift { forbidden_count: u64, named_count: u64 },
    DuplicateListed,
    DuplicateNamed,
    Missing { capability_index: u64 },
    Extra { capability_index: u64 },
}

// Origin: engine/crates_rs/core_contracts/src/witness_witness.rs
// Claim: urn:core:crates_rs:core-contracts:witness-witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ForbiddenCapabilityWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ForbiddenCapabilityWitnessError {}

impl ForbiddenCapabilityWitness {
    /// The slice is exactly the ten capabilities the evidence module names, once each.
    pub fn certify() -> Result<Self, ForbiddenCapabilityWitnessError> {
        const NAMED: [Capability; 10] = [
            Capability::CertificateSigning,
            Capability::SelfCertification,
            Capability::Evaluation,
            Capability::AdmissibilityDecision,
            Capability::PolicyInterpretation,
            Capability::TerminalMapping,
            Capability::ExecuteStateTransition,
            Capability::ActionLicensing,
            Capability::AuthorityPromotion,
            Capability::RuntimeMutation,
        ];
        let forbidden_count = u64::try_from(WITNESS_FORBIDDEN_CAPABILITIES.len())
            .map_err(|_| ForbiddenCapabilityWitnessError::Overflow)?;
        let named_count = u64::try_from(NAMED.len())
            .map_err(|_| ForbiddenCapabilityWitnessError::Overflow)?;
        if forbidden_count != named_count {
            return Err(ForbiddenCapabilityWitnessError::CountDrift {
                forbidden_count,
                named_count,
            });
        }
        for (i, capability) in NAMED.iter().enumerate() {
            if NAMED[..i].contains(capability) {
                return Err(ForbiddenCapabilityWitnessError::DuplicateNamed);
            }
        }
        Self::verify_capability_bijection(&NAMED)?;
        let out = Self {
            forbidden_count,
            named_count,
        };
        Ok(out)
    }

    fn verify_capability_bijection(
        named: &[Capability; 10],
    ) -> Result<(), ForbiddenCapabilityWitnessError> {
        for (i, capability) in WITNESS_FORBIDDEN_CAPABILITIES.iter().enumerate() {
            if WITNESS_FORBIDDEN_CAPABILITIES[..i].contains(capability) {
                return Err(ForbiddenCapabilityWitnessError::DuplicateListed);
            }
            if !named.contains(capability) {
                let capability_index = u64::try_from(i)
                    .map_err(|_| ForbiddenCapabilityWitnessError::Overflow)?;
                return Err(ForbiddenCapabilityWitnessError::Extra { capability_index });
            }
        }
        for (i, capability) in named.iter().enumerate() {
            if !WITNESS_FORBIDDEN_CAPABILITIES.contains(capability) {
                let capability_index = u64::try_from(i)
                    .map_err(|_| ForbiddenCapabilityWitnessError::Overflow)?;
                return Err(ForbiddenCapabilityWitnessError::Missing { capability_index });
            }
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod forbidden_capability_tests {
    use super::*;

    #[test]
    fn forbidden_slice_is_the_named_set() {
        assert!(matches!(
            ForbiddenCapabilityWitness::certify(),
            Ok(witness)
                if witness.forbidden_count == witness.named_count
                    && witness.forbidden_count == 10
        ));
    }
}
