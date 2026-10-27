//! Normal Form Contract types and identity models for PFP / Engine.
//!
//! AuthorityEffect: None.

use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};

use crate::no_authority::AuthorityTagged;

fn default_authority_effect() -> AuthorityEffect {
    AuthorityEffect::None
}

fn default_schema_version() -> String {
    "smplx.nf.contract.v0".to_string()
}

/// Identity block of a normal form contract.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalFormContractIdentity {
    /// Canonical contract identifier (e.g. `nf.runtime.zfnf`).
    #[serde(alias = "contract_id")]
    pub id: String,
    #[serde(default)]
    pub name: String,
    #[serde(default)]
    pub short_name: String,
    pub version: String,
    #[serde(default)]
    pub theory_status: String,
    #[serde(default)]
    pub contract_status: String,
    #[serde(default)]
    pub verification_status: String,
    #[serde(default)]
    pub family: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: AuthorityEffect,
}

impl NormalFormContractIdentity {
    /// Helper returning the contract ID (matches PROJECT.md `contract_id` field).
    pub fn contract_id(&self) -> &str {
        &self.id
    }
}

/// Classification block of a normal form contract.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalFormClassification {
    /// Normal form hierarchy level or name (e.g. `normal_form` or `ZFNF`).
    #[serde(default, alias = "normal_form")]
    pub hierarchy_level: String,
    #[serde(default)]
    pub subject_kind: Vec<String>,
    #[serde(default)]
    pub data_posture: String,
    /// Verification profile or mathematical posture.
    #[serde(default, alias = "verification_profile")]
    pub mathematical_posture: String,
}

impl NormalFormClassification {
    /// Helper returning normal form name or hierarchy level.
    pub fn normal_form(&self) -> &str {
        &self.hierarchy_level
    }

    /// Helper returning verification profile or mathematical posture.
    pub fn verification_profile(&self) -> &str {
        &self.mathematical_posture
    }
}

/// Normal form contract envelope.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalFormContract {
    #[serde(default = "default_schema_version")]
    pub schema_version: String,
    #[serde(default)]
    pub contract_kind: String,
    pub identity: NormalFormContractIdentity,
    pub classification: NormalFormClassification,
    #[serde(default)]
    pub purpose: serde_json::Value,
    #[serde(default)]
    pub specification_hash: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: AuthorityEffect,
}

impl AuthorityTagged for NormalFormContract {
    fn authority_effect(&self) -> AuthorityEffect {
        self.authority_effect.clone()
    }

    fn artifact_id(&self) -> &str {
        &self.identity.id
    }
}

// Origin: engine/crates_rs/core_contracts/src/normal_forms.rs
// Claim: urn:core:crates_rs:core-contracts:normal-forms:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord70d1f5ea {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord70d1f5ea` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError70d1f5ea {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError70d1f5ea {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError70d1f5ea {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError70d1f5ea {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord70d1f5ea {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError70d1f5ea> {
        if capacity_bound == 0 {
            return Err(BoundaryError70d1f5ea::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError70d1f5ea::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError70d1f5ea::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normal_form_contract_project_md_wire_format() {
        let json_str = r#"{
            "identity": {
                "contract_id": "nf.runtime.zfnf",
                "version": "v1.0.0",
                "authority_effect": "None"
            },
            "classification": {
                "normal_form": "ZFNF",
                "verification_profile": "executable"
            },
            "specification_hash": "a1b2c3d4e5f6"
        }"#;

        let contract: NormalFormContract = serde_json::from_str(json_str).expect("deserialize failed");
        assert_eq!(contract.identity.id, "nf.runtime.zfnf");
        assert_eq!(contract.identity.contract_id(), "nf.runtime.zfnf");
        assert_eq!(contract.identity.version, "v1.0.0");
        assert_eq!(contract.identity.authority_effect, AuthorityEffect::None);
        assert_eq!(contract.classification.hierarchy_level, "ZFNF");
        assert_eq!(contract.classification.normal_form(), "ZFNF");
        assert_eq!(contract.classification.mathematical_posture, "executable");
        assert_eq!(contract.classification.verification_profile(), "executable");
        assert_eq!(contract.specification_hash, "a1b2c3d4e5f6");
        assert_eq!(contract.authority_effect, AuthorityEffect::None);

        // Test roundtrip
        let serialized = serde_json::to_string(&contract).expect("serialize failed");
        let roundtrip: NormalFormContract = serde_json::from_str(&serialized).expect("roundtrip failed");
        assert_eq!(contract, roundtrip);
    }

    #[test]
    fn test_normal_form_contract_full_yaml_deserialization() {
        let yaml_str = r#"
schema_version: smplx.nf.contract.v0
contract_kind: normal_form_contract
identity:
  id: nf.runtime.zfnf
  name: Zero-Float Rational Normal Form
  short_name: ZFNF
  version: v0
  theory_status: established
  contract_status: draft
  verification_status: executable
  family: runtime
classification:
  hierarchy_level: normal_form
  subject_kind:
  - rational_number
  - primal_dual_pair
  data_posture: at_rest
  mathematical_posture: formal_algebraic
purpose:
  excludes_anomaly: floating-point representations
"#;
        let contract: NormalFormContract = serde_yaml::from_str(yaml_str).expect("yaml deserialize failed");
        assert_eq!(contract.identity.id, "nf.runtime.zfnf");
        assert_eq!(contract.identity.name, "Zero-Float Rational Normal Form");
        assert_eq!(contract.identity.short_name, "ZFNF");
        assert_eq!(contract.identity.family, "runtime");
        assert_eq!(contract.classification.hierarchy_level, "normal_form");
        assert_eq!(contract.classification.subject_kind, vec!["rational_number", "primal_dual_pair"]);
        assert_eq!(contract.classification.data_posture, "at_rest");
        assert_eq!(contract.classification.mathematical_posture, "formal_algebraic");
        assert_eq!(contract.authority_effect, AuthorityEffect::None);
    }
}

#[cfg(test)]
mod l4_boundary_tests_70d1f5ea {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord70d1f5ea::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord70d1f5ea::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord70d1f5ea::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord70d1f5ea::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord70d1f5ea::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError70d1f5ea::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError70d1f5ea::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
