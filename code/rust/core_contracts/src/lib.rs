
#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_c17daf41;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_c17daf41<T> = std::result::Result<T, BoundaryError_c17daf41>;
pub mod artifact_policy;
pub mod authorization_basis;
pub mod binding;
pub mod contract_images;
pub mod contracts_contract;
pub mod descriptors;
pub mod enforcement;
pub mod file_contract_substring;
pub mod improvement;
pub mod in_code_contracts;
pub mod kinds;
pub mod mub_domain_ownership;
pub mod published_corpus;
pub mod registry;
pub mod runtime;
pub mod schema;
pub mod sealed;
pub mod traits;
pub mod validate;
pub mod validation;
pub mod witness;
pub use binding::*;
pub use contracts_contract::*;
pub use enforcement::*;
pub use file_contract_substring::source_satisfies_file_contract_substring;
pub use in_code_contracts::*;
pub use kinds::*;
pub use runtime::*;
pub use schema::{ArtifactFamily, EffectLawDecl, PhiLawDecl, StructureLawDecl};
pub use sealed::Sealed;
pub use validate::*;
pub use witness::*;

pub mod audit;
pub mod binding_audit {
    pub use crate::audit::*;
    pub mod summary {
        include!(concat!(env!("OUT_DIR"), "/binding_audit_summary.rs"));
    }
}
pub use binding_audit::summary;

pub mod nomos_urn;
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod nomos_urn_golden_parity;

pub use nomos_urn::{
    audit_critical_urn_sample, format_nomos_urn, is_well_formed_nomos_urn, parse_nomos_urn,
    NomosUrn, NomosUrnError, NomosUrnSampleReceipt, CRITICAL_URN_NEGATIVE_SAMPLE,
    CRITICAL_URN_SAMPLE,
};


// ── Migrated from obstruction_calculus (Wave 6) ─────────────────────────────
pub mod certificate_promotion;
pub mod no_authority;
pub mod three_role_authority;
pub mod operator_gauge;

pub use certificate_promotion::*;
pub use operator_gauge::*;

#[cfg(test)]
mod contract_property_witnesses;

pub mod contract_descriptors;

pub mod functional_property_witnesses;

pub mod normal_forms;
pub use normal_forms::*;


/// Three-role authority: exactly three distinct nonempty seats.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThreeRoleCensus {
    seats: [String; 3],
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ThreeRoleError {
    CountNotThree { got: usize },
    EmptySeat { index: usize },
    DuplicateSeat { index: usize },
}

// Origin: engine/crates_rs/core_contracts/src/lib.rs
// Claim: urn:core:crates_rs:core-contracts:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ThreeRoleError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ThreeRoleError {}

impl ThreeRoleCensus {
    pub fn admit(seats: &[String]) -> Result<Self, ThreeRoleError> {
        if seats.len() != 3 {
            return Err(ThreeRoleError::CountNotThree { got: seats.len() });
        }
        for index in 0..3 {
            if seats[index].is_empty() {
                return Err(ThreeRoleError::EmptySeat { index });
            }
            for earlier in 0..index {
                if seats[earlier] == seats[index] {
                    return Err(ThreeRoleError::DuplicateSeat { index });
                }
            }
        }
        Ok(Self {
            seats: [seats[0].clone(), seats[1].clone(), seats[2].clone()],
        })
    }

    pub fn seats(&self) -> &[String; 3] {
        &self.seats
    }
}

#[cfg(test)]
mod three_role_census_tests {
    use super::*;

    #[test]
    fn three_roles_are_distinct() {
        let admitted = ThreeRoleCensus::admit(&["proposer".into(), "falsifier".into(), "authorizer".into()]);
        assert!(admitted.is_ok());
        assert_eq!(admitted.as_ref().ok().map(|census| census.seats()[0].as_str()), Some("proposer"));
        assert!(matches!(
            ThreeRoleCensus::admit(&["proposer".into(), "proposer".into(), "authorizer".into()]),
            Err(ThreeRoleError::DuplicateSeat { index: 1 })
        ));
    }
}
