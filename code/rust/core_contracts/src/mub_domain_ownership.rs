//! Canonical ownership ledger for the MUB application lane.
//!
//! The ledger assigns every load-bearing semantic surface to one owner.  The
//! Apache-derived `mub` crate remains an evidence provider and is never a
//! second Core-native domain or authority owner.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

pub const MUB_OWNERSHIP_CONTRACT_ID_V1: &str = "core.contracts.mub-domain-ownership.v1";
pub const CANONICAL_MUB_DOMAIN_OWNER_V1: &str = "core_mub";
pub const APACHE_MUB_EVIDENCE_PROVIDER_V1: &str = "mub";

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MubSemanticSurfaceV1 {
    DomainCarrier,
    ExactMubArithmetic,
    FiniteMubSystem,
    PrimitiveMap,
    ExactRuntimeAdapter,
    FeasibilityWallFunctional,
    #[serde(rename = "exact_gtoc_evaluation")]
    ExactCodaEvaluation,
    TerminalVocabulary,
    AuthorityCertificateBoundary,
    ApacheWallVerificationEvidence,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MubSemanticOwnerV1 {
    CoreMub,
    CoreFunctional,
    CorePipeline,
    CoreState,
    CoreCertifiers,
    CoreQuantumPhysics,
    MubApacheEvidence,
    CoreNumberTheory,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MubOwnershipRoleV1 {
    CanonicalDomainOwner,
    SharedRuntimeOwner,
    AuthorityBoundaryOwner,
    EvidenceProviderOnly,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MubConversionClassV1 {
    IdentityPreservingImport,
    EvidenceOnlyComparison,
    ForbiddenLossyPromotion,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MubOwnershipRecordV1 {
    pub surface: MubSemanticSurfaceV1,
    pub owner: MubSemanticOwnerV1,
    pub role: MubOwnershipRoleV1,
    pub type_or_module_id: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MubConversionRecordV1 {
    pub source: &'static str,
    pub target: &'static str,
    pub class: MubConversionClassV1,
}

pub const MUB_OWNERSHIP_LEDGER_V1: [MubOwnershipRecordV1; 10] = [
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::DomainCarrier,
        owner: MubSemanticOwnerV1::CoreMub,
        role: MubOwnershipRoleV1::CanonicalDomainOwner,
        type_or_module_id: "core_mub::core_native::carrier",
    },
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::ExactMubArithmetic,
        owner: MubSemanticOwnerV1::CoreNumberTheory,
        role: MubOwnershipRoleV1::SharedRuntimeOwner,
        type_or_module_id: "core_number_theory::cyclotomic",
    },
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::FiniteMubSystem,
        owner: MubSemanticOwnerV1::CoreQuantumPhysics,
        role: MubOwnershipRoleV1::SharedRuntimeOwner,
        type_or_module_id: "core_quantum_physics::mub",
    },
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::PrimitiveMap,
        owner: MubSemanticOwnerV1::CoreMub,
        role: MubOwnershipRoleV1::CanonicalDomainOwner,
        type_or_module_id: "core_mub::primitive_map",
    },
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::ExactRuntimeAdapter,
        owner: MubSemanticOwnerV1::CoreMub,
        role: MubOwnershipRoleV1::CanonicalDomainOwner,
        type_or_module_id: "core_mub::runtime_adapter",
    },
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::FeasibilityWallFunctional,
        owner: MubSemanticOwnerV1::CoreFunctional,
        role: MubOwnershipRoleV1::SharedRuntimeOwner,
        type_or_module_id: "core_functional::MubFeasibilityWallFunctional",
    },
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::ExactCodaEvaluation,
        owner: MubSemanticOwnerV1::CorePipeline,
        role: MubOwnershipRoleV1::SharedRuntimeOwner,
        type_or_module_id: "core_wdp::coda::gtoc_gtla::evaluate_exact",
    },
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::TerminalVocabulary,
        owner: MubSemanticOwnerV1::CoreState,
        role: MubOwnershipRoleV1::SharedRuntimeOwner,
        type_or_module_id: "core_state::GtocTerminal",
    },
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::AuthorityCertificateBoundary,
        owner: MubSemanticOwnerV1::CoreCertifiers,
        role: MubOwnershipRoleV1::AuthorityBoundaryOwner,
        type_or_module_id: "core_certifiers::certify_checked_packet",
    },
    MubOwnershipRecordV1 {
        surface: MubSemanticSurfaceV1::ApacheWallVerificationEvidence,
        owner: MubSemanticOwnerV1::MubApacheEvidence,
        role: MubOwnershipRoleV1::EvidenceProviderOnly,
        type_or_module_id: "mub::apache_verifier",
    },
];

pub const MUB_CONVERSION_LEDGER_V1: [MubConversionRecordV1; 3] = [
    MubConversionRecordV1 {
        source: "core_mub::runtime_adapter",
        target: "core_wdp::coda::gtoc_gtla::GtocExactInput",
        class: MubConversionClassV1::IdentityPreservingImport,
    },
    MubConversionRecordV1 {
        source: "mub::apache_verifier",
        target: "core_mub::runtime_adapter",
        class: MubConversionClassV1::EvidenceOnlyComparison,
    },
    MubConversionRecordV1 {
        source: "core_functional::MubFeasibilityWallEvidenceKind::F64Diagnostic",
        target: "core_wdp::coda::gtoc_gtla::GtocExactInput",
        class: MubConversionClassV1::ForbiddenLossyPromotion,
    },
];

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MubOwnershipContractError {
    #[error("MUB ownership ledger contains a duplicate semantic surface")]
    DuplicateSurface,
    #[error("MUB ownership ledger no longer has exactly one canonical domain owner")]
    CanonicalDomainOwnerChanged,
    #[error("the Apache-derived mub crate was promoted beyond evidence-provider scope")]
    ApacheEvidenceBoundaryChanged,
    #[error("the floating feasibility-wall diagnostic can enter the exact runtime")]
    FloatingPromotionBoundaryChanged,
}

pub fn validate_mub_ownership_contract_v1() -> Result<(), MubOwnershipContractError> {
    let surfaces = MUB_OWNERSHIP_LEDGER_V1
        .iter()
        .map(|record| record.surface)
        .collect::<BTreeSet<_>>();
    if surfaces.len() != MUB_OWNERSHIP_LEDGER_V1.len() {
        return Err(MubOwnershipContractError::DuplicateSurface);
    }

    let domain_owners = MUB_OWNERSHIP_LEDGER_V1
        .iter()
        .filter(|record| record.role == MubOwnershipRoleV1::CanonicalDomainOwner)
        .map(|record| record.owner)
        .collect::<BTreeSet<_>>();
    if domain_owners != BTreeSet::from([MubSemanticOwnerV1::CoreMub]) {
        return Err(MubOwnershipContractError::CanonicalDomainOwnerChanged);
    }

    let apache = MUB_OWNERSHIP_LEDGER_V1
        .iter()
        .find(|record| record.surface == MubSemanticSurfaceV1::ApacheWallVerificationEvidence);
    if !matches!(
        apache,
        Some(MubOwnershipRecordV1 {
            owner: MubSemanticOwnerV1::MubApacheEvidence,
            role: MubOwnershipRoleV1::EvidenceProviderOnly,
            ..
        })
    ) {
        return Err(MubOwnershipContractError::ApacheEvidenceBoundaryChanged);
    }

    if !MUB_CONVERSION_LEDGER_V1.iter().any(|record| {
        record.source.contains("F64Diagnostic")
            && record.class == MubConversionClassV1::ForbiddenLossyPromotion
    }) {
        return Err(MubOwnershipContractError::FloatingPromotionBoundaryChanged);
    }
    Ok(())
}

// Origin: engine/crates_rs/core_contracts/src/mub_domain_ownership.rs
// Claim: urn:core:crates_rs:core-contracts:mub-domain-ownership:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_ledger_has_one_domain_owner_and_no_duplicate_surface() {
        validate_mub_ownership_contract_v1().unwrap();
    }

    #[test]
    fn finite_mub_kernel_has_a_distinct_physics_owner() {
        let record = MUB_OWNERSHIP_LEDGER_V1
            .iter()
            .find(|r| r.surface == MubSemanticSurfaceV1::FiniteMubSystem)
            .expect("finite kernel has explicit ownership");
        assert_eq!(record.owner, MubSemanticOwnerV1::CoreQuantumPhysics);
        assert_eq!(record.role, MubOwnershipRoleV1::SharedRuntimeOwner);
        assert_eq!(record.type_or_module_id, "core_quantum_physics::mub");
    }
}
