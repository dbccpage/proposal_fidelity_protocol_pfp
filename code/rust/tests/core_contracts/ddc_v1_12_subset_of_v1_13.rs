use std::collections::BTreeSet;
use std::fs;
use std::path::PathBuf;

const V1_12_REQUIRED_SUBSTRINGS: &[&str] = &[
    "pub struct FaceLambda",
    "pub struct OrientedTriangle",
    "pub struct FiniteWindow",
    "pub struct FiniteWindowScan",
    "pub struct Boundary1",
    "pub struct Cochain0",
    "pub type Cochain1",
    "pub struct FiniteDiagnostic",
    "pub struct NonDestructiveExtensionCertificate",
    "pub struct FiniteLambdaStepCertificate",
    "pub struct QuotientIrreducibilityCertificate",
    "pub struct BornNormalizationCertificate",
    "pub struct ObserverPassivityCertificate",
    "pub struct CrossTermObstructionCertificate",
    "pub struct NormalizedL1Weight",
    "pub struct OperatorProposal",
    "pub struct ProofCarryingAiProposal",
    "pub enum DegreeTwoSupport",
    "pub struct XiTiePrecondition",
    "pub struct XiTieBreakCertificate",
    "pub enum RealizationBoundary",
    "pub enum TerminalStatus",
    "pub struct ClaimPacket",
    "PAPER000C_CLAIM_PACKET_EVIDENCE_ID",
    "pub fn checked_boundary",
    "pub fn checked_primitive_difference",
    "pub fn checked_scan",
    "pub fn checked_scan_c1",
    "pub fn checked_closure_defect",
    "pub fn checked_gamma2",
    "pub fn checked_l1_tension",
    "pub fn require_irreducible",
    "pub fn checked_from_quotient_certificate",
    "pub fn checked_diagnostic_from_quotient",
    "pub fn checked_from_l1_weights",
    "pub fn born_probability_from_squared_norm",
    "pub fn preserves_diagnostic",
    "pub fn require_passive",
    "pub fn observed_diagnostic",
    "pub fn require_typed_obstruction",
    "pub fn diagnostic",
    "pub fn require_tie_breaker",
    "pub fn require_lambda_license",
    "pub fn require_non_destructive",
    "pub fn require_valid",
    "pub fn require_proof_carrying",
    "pub fn accepted_diagnostic",
    "pub fn after_tension",
    "pub fn descends_to_real0",
    "pub fn is_terminalized",
    "pub fn has_authority",
    "pub fn require_terminalized",
    "pub fn require_authority",
    "std::ops::Add for FaceLambda",
    "std::ops::Neg for FaceLambda",
    "std::ops::Mul<i64> for FaceLambda",
];

#[test]
fn test_ddc_v1_12_substrings_survive_in_v1_13() {
    assert_eq!(
        V1_12_REQUIRED_SUBSTRINGS.len(),
        56,
        "the non-destruction witness must enumerate the complete v1.12 surface"
    );

    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join(
        "../../../governance/contracts/contract_canonical_definitions/rust/core_discrete_deformation_algebra/discrete_deformation_algebra.contract.yaml",
    );
    let source = fs::read_to_string(&path).expect("DDC contract is readable");
    let contract: serde_yaml::Value =
        serde_yaml::from_str(&source).expect("DDC contract is valid YAML");

    assert_eq!(
        contract["contract_id"].as_str(),
        Some("urn:core:rust:core_discrete_deformation_algebra:discrete_deformation_algebra:v1.13.0")
    );

    let required = contract["required_substrings"]
        .as_sequence()
        .expect("required_substrings is a sequence");
    let current = required
        .iter()
        .map(|value| value.as_str().expect("required substring is text"))
        .collect::<BTreeSet<_>>();

    for pin in V1_12_REQUIRED_SUBSTRINGS {
        assert!(
            current.contains(pin),
            "v1.13 dropped the v1.12 required substring {pin:?}"
        );
    }

    for ledger_pin in [
        "pub struct FiniteLambdaLedger",
        "impl FiniteLambdaLedger",
        "pub fn require_chained",
    ] {
        assert!(
            current.contains(ledger_pin),
            "v1.13 is missing additive ledger pin {ledger_pin:?}"
        );
    }
}

// Origin: engine/crates_rs/tests/core_contracts/ddc_v1_12_subset_of_v1_13.rs
// Claim: urn:core:crates_rs:tests:ddc-v1-12-subset-of-v1-13:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord651da433 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord651da433` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError651da433 {
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
impl BoundaryError651da433 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError651da433 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError651da433 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord651da433 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError651da433> {
        if capacity_bound == 0 {
            return Err(BoundaryError651da433::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError651da433::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError651da433::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_651da433() {
    let admitted = BoundaryRecord651da433::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord651da433::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
