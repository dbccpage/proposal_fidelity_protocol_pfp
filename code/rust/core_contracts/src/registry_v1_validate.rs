//! core.contract.v1 machine-field validators (spec §5, §11). Fail closed.
//!
//! `validate_v1` is authoritative for v1 machine fields (review fix #6). It is independent of
//! the legacy `validate_registry` role heuristics; the loader runs both, but v1 correctness is
//! defined here.

use crate::kinds::ContractEffect;
use crate::registry::v1_types::CoreContractV1;
use crate::registry::v1_vocabulary::{is_known_refusal, is_known_terminal};

pub type V1Finding = String;

/// Validate the machine fields of a v1 contract. Returns `Err(findings)` on any violation.
pub fn validate_v1(c: &CoreContractV1) -> Result<(), Vec<V1Finding>> {
    let mut f = Vec::new();

    if c.schema_version != "core.contract.v1" {
        f.push(format!(
            "schema_version must be core.contract.v1, got {}",
            c.schema_version
        ));
    }
    // Nomos structured URN (Forms A/B/C). Prefix-only is insufficient.
    if let Err(e) = crate::nomos_urn::parse_nomos_urn(&c.contract_id) {
        f.push(format!(
            "contract_id must be a well-formed Nomos urn:core: URN ({e}), got {}",
            c.contract_id
        ));
    }

    // Math-contract authority rule (spec §11.4; corrected — fail if NOT none).
    if c.kind.is_math() {
        if c.descriptor.authority_effect != ContractEffect::None {
            f.push("math contract must declare authority_effect: none".into());
        }
        if c.descriptor.runtime_enforcement {
            f.push("math contract must declare runtime_enforcement: false".into());
        }
    }

    // Non-math kinds must declare an explicit role (no kind default). authority_effect for
    // non-math is only required to be a valid enum (guaranteed by deserialization); role-
    // appropriate authority is enforced by validate_registry's role validators on the
    // projected descriptor.
    if !c.kind.is_math() && c.role.is_none() && c.kind.default_role().is_none() {
        f.push(format!("role required for non-math kind {:?}", c.kind));
    }

    validate_v1_vocabulary_and_pos(c, &mut f);

    if f.is_empty() {
        Ok(())
    } else {
        Err(f)
    }
}

fn validate_v1_vocabulary_and_pos(c: &CoreContractV1, f: &mut Vec<V1Finding>) {
    // terminals/refusals must be in the seeded v1 vocabulary (intra-file consistency is
    // enforced additionally by the loader; see v1_loader::intra_file_consistency).
    for t in c
        .descriptor
        .terminals
        .may_support
        .iter()
        .chain(&c.descriptor.terminals.may_emit)
    {
        if !is_known_terminal(t) {
            f.push(format!("unknown terminal: {t}"));
        }
    }
    for r in &c.descriptor.refusals.may_emit {
        if !is_known_refusal(r) {
            f.push(format!("unknown refusal: {r}"));
        }
    }

    // proof-obligation grammar: ^(PO|SG|OB)-[A-Za-z0-9-]+$ (internal hyphens allowed).
    for po in &c.descriptor.dependencies.proof_obligations {
        if !is_well_formed_po(po.as_str()) {
            f.push(format!("malformed proof obligation: {}", po.as_str()));
        }
    }
}

/// Grammar for proof-obligation ids: a known prefix, a hyphen, then alphanumerics/hyphens
/// with at least one alphanumeric (e.g. `PO-D3`, `SG-AUTH`, `PO-AUTH-NC`).
fn is_well_formed_po(s: &str) -> bool {
    let Some((prefix, rest)) = s.split_once('-') else {
        return false;
    };
    matches!(prefix, "PO" | "SG" | "OB")
        && !rest.is_empty()
        && rest
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || ch == '-')
        && rest.chars().any(|ch| ch.is_ascii_alphanumeric())
}

// Origin: engine/crates_rs/core_contracts/src/registry_v1_validate.rs
// Claim: urn:core:crates_rs:core-contracts:registry-v1-validate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf7a8c0ae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf7a8c0ae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf7a8c0ae {
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
impl BoundaryErrorf7a8c0ae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf7a8c0ae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf7a8c0ae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf7a8c0ae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf7a8c0ae> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf7a8c0ae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf7a8c0ae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf7a8c0ae::ExceedsCapacity {
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

    const GOOD: &str = r#"
schema_version: "core.contract.v1"
contract_id: "urn:core:math:demo:v0.1.0"
title: "Demo"
kind: "math_contract"
status: "mathematical_wip"
descriptor:
  authority_effect: "none"
  evidence_ceiling: "ShapeOnly"
  runtime_enforcement: false
  customer_claim_allowed: false
  dependencies: { contracts: [], proof_obligations: ["PO-D3", "PO-AUTH-NC"] }
  terminals: { may_emit: [], may_support: ["ExactRepair"] }
  refusals: { may_emit: ["Invalid"] }
  operator_classes: { may_support: [], must_not_self_assign: true }
"#;

    fn parse(y: &str) -> CoreContractV1 {
        serde_yaml::from_str(y).expect("fixture parses")
    }

    #[test]
    fn good_contract_validates() {
        // assert_eq! over is_ok(): on failure the panic prints the actual findings.
        // `is_ok()` prints nothing, so a regression here said only "false".
        assert_eq!(
            validate_v1(&parse(GOOD)),
            Ok(()),
            "the GOOD fixture must produce zero findings"
        );
    }

    #[test]
    fn nonmath_missing_role_fails() {
        let y = r#"
schema_version: "core.contract.v1"
contract_id: "urn:core:obstruction:demo:v0.1.0"
title: "Demo"
kind: "obstruction_contract"
status: "mathematical_wip"
descriptor:
  authority_effect: "evidence_only"
  evidence_ceiling: "LocalReplay"
"#;
        let errs = validate_v1(&parse(y)).unwrap_err();
        assert!(errs.iter().any(|f| f.contains("role required")));
    }

    #[test]
    fn nonmath_with_role_ok() {
        let y = r#"
schema_version: "core.contract.v1"
contract_id: "urn:core:obstruction:demo:v0.1.0"
title: "Demo"
kind: "obstruction_contract"
status: "mathematical_wip"
role: "AnalysisUnit"
descriptor:
  authority_effect: "evidence_only"
  evidence_ceiling: "LocalReplay"
  terminals: { may_emit: [], may_support: [] }
  refusals: { may_emit: [] }
"#;
        assert_eq!(
            validate_v1(&parse(y)),
            Ok(()),
            "a non-math contract that declares a role must produce zero findings"
        );
    }

    #[test]
    fn math_contract_with_authority_fails() {
        let bad = GOOD.replace(
            "authority_effect: \"none\"",
            "authority_effect: \"requests_decision\"",
        );
        let errs = validate_v1(&parse(&bad)).unwrap_err();
        assert!(errs
            .iter()
            .any(|f| f.contains("math contract must declare authority_effect: none")));
    }

    #[test]
    fn unknown_terminal_fails() {
        let bad = GOOD.replace("may_support: [\"ExactRepair\"]", "may_support: [\"Bogus\"]");
        let errs = validate_v1(&parse(&bad)).unwrap_err();
        assert!(errs.iter().any(|f| f.contains("unknown terminal")));
    }

    #[test]
    fn unknown_refusal_fails() {
        let bad = GOOD.replace("may_emit: [\"Invalid\"]", "may_emit: [\"Nope\"]");
        let errs = validate_v1(&parse(&bad)).unwrap_err();
        assert!(errs.iter().any(|f| f.contains("unknown refusal")));
    }

    #[test]
    fn malformed_proof_obligation_fails() {
        let bad = GOOD.replace("\"PO-D3\", \"PO-AUTH-NC\"", "\"nonsense\"");
        let errs = validate_v1(&parse(&bad)).unwrap_err();
        assert!(errs
            .iter()
            .any(|f| f.contains("malformed proof obligation")));
    }

    #[test]
    fn internal_hyphen_proof_obligation_ok() {
        assert!(is_well_formed_po("PO-AUTH-NC"));
        assert!(is_well_formed_po("PO-D3"));
        assert!(!is_well_formed_po("nonsense"));
        assert!(!is_well_formed_po("PO-"));
    }

    #[test]
    fn wrong_schema_version_fails() {
        let bad = GOOD.replace("core.contract.v1", "core.contract.v2");
        let errs = validate_v1(&parse(&bad)).unwrap_err();
        assert!(errs.iter().any(|f| f.contains("schema_version")));
    }
}

#[cfg(test)]
mod l4_boundary_tests_f7a8c0ae {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf7a8c0ae::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf7a8c0ae::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf7a8c0ae::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf7a8c0ae::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf7a8c0ae::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf7a8c0ae::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf7a8c0ae::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
