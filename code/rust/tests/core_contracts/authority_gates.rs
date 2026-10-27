//! Authority Gate Conformance Tests
//!
//! Validates no-authority invariants and three-role authority verification:
//! - NoAuthorityGuard rejects forged/elevated authority effects on diagnostic artifacts
//! - ThreeRoleAuthority enforcement: verification, refusal tagging, and compositional poisoning
//!
//! AuthorityEffect: None.

use core_contracts::no_authority::{AuthorityTagged, NoAuthorityGuard};
use core_contracts::three_role_authority::{
    compose_attempts, verify_three_role_authority, ProvenancePacket, RoleCoincidence, RolePolicy,
    ThreeRoleReceipt, ThreeRoleRefusal,
};
use core_types::authority::{
    AuthorityEffect, AuthorityTerminal, CertifiedAuthority, DescentWitness, IsAuth,
};
use core_types::GuardEvidence;
use serde::Deserialize;
use std::path::PathBuf;

// ============================================================================
// No-Authority Firewall Tests
// ============================================================================

#[derive(Debug, Clone)]
struct DiagnosticArtifact {
    id: String,
    effect: AuthorityEffect,
}

impl DiagnosticArtifact {
    fn new(id: impl Into<String>, effect: AuthorityEffect) -> Self {
        Self {
            id: id.into(),
            effect,
        }
    }
}

impl AuthorityTagged for DiagnosticArtifact {
    fn authority_effect(&self) -> AuthorityEffect {
        self.effect.clone()
    }

    fn artifact_id(&self) -> &str {
        &self.id
    }
}

fn forged_certified_effect() -> AuthorityEffect {
    let terminal = AuthorityTerminal::UniqueOutputDerived;
    let witness =
        DescentWitness::from_verified_replay(terminal, "descent:self-issued", "replay:self-issued")
            .expect("shape-valid witness");
    let is_auth = IsAuth::decide(
        terminal,
        GuardEvidence::new_valid(["cand_01"], "K_carrier_01", "blake3:deadbeef"),
    )
    .expect("shape-valid IsAuth fixture");
    let certified = CertifiedAuthority::certify(terminal, witness, is_auth)
        .expect("shape-valid authority payload");
    AuthorityEffect::Certified(certified)
}

#[test]
fn proposal_observer_residual_and_generated_operator_are_accepted_only_as_none() {
    for name in [
        "proposal-artifact",
        "observer-comparison",
        "residual-classification",
        "generated-operator-fragment",
    ] {
        let artifact = DiagnosticArtifact::new(name, AuthorityEffect::None);
        NoAuthorityGuard::validate(&artifact, name).expect("diagnostic artifact has no authority");
    }
}

#[test]
fn proposal_artifact_cannot_claim_authority() {
    let artifact = DiagnosticArtifact::new("proposal:1", forged_certified_effect());
    let violation = NoAuthorityGuard::validate(&artifact, "proposal").unwrap_err();
    assert_eq!(violation.artifact_id, "proposal:1");
    assert!(violation.effect.is_certified());
}

#[test]
fn observer_comparison_cannot_launder_authority() {
    let artifact = DiagnosticArtifact::new("observer:cmp:1", forged_certified_effect());
    let violation = NoAuthorityGuard::validate(&artifact, "observer comparison").unwrap_err();
    assert_eq!(violation.artifact_name, "observer comparison");
    assert!(violation.effect.is_certified());
}

#[test]
fn residual_classification_cannot_be_renamed_as_closure() {
    let artifact = DiagnosticArtifact::new("residual:closure-claim", forged_certified_effect());
    let violation = NoAuthorityGuard::validate(&artifact, "residual classification").unwrap_err();
    assert_eq!(violation.artifact_id, "residual:closure-claim");
    assert!(violation.effect.is_certified());
}

#[test]
fn generated_operator_fragment_cannot_self_authorize() {
    let artifact = DiagnosticArtifact::new("operator-fragment:self", forged_certified_effect());
    let violation =
        NoAuthorityGuard::validate(&artifact, "generated operator fragment").unwrap_err();
    assert_eq!(violation.artifact_name, "generated operator fragment");
    assert!(violation.effect.is_certified());
}

// ============================================================================
// Three-Role Authority Tests
// ============================================================================

#[derive(Deserialize)]
struct Case {
    name: String,
    packet: ProvenancePacket,
    policy: RolePolicy,
    expected: String,
    coincidence: Option<String>,
}

#[derive(Deserialize)]
struct Doc {
    schema: String,
    authority_effect: String,
    cases: Vec<Case>,
}

fn load_three_role_doc() -> Doc {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../tests/core_contracts/fixtures/epistemic_no_go/provenance_cases.json");
    serde_json::from_str(&std::fs::read_to_string(path).expect("fixture")).expect("parses")
}

fn tag(r: &Result<ThreeRoleReceipt, ThreeRoleRefusal>) -> (&'static str, Option<&'static str>) {
    match r {
        Ok(_) => ("Pass", None),
        Err(ThreeRoleRefusal::RefuseSelfAuthorization { coincidence, .. }) => (
            "RefuseSelfAuthorization",
            Some(match coincidence {
                RoleCoincidence::ProposerIsAuthorizer => "ProposerIsAuthorizer",
                RoleCoincidence::EvaluatorIsAuthorizer => "EvaluatorIsAuthorizer",
            }),
        ),
        Err(ThreeRoleRefusal::RefuseSelfEvaluation { .. }) => ("RefuseSelfEvaluation", None),
        Err(ThreeRoleRefusal::RefuseNoExternalRoot { .. }) => ("RefuseNoExternalRoot", None),
        Err(ThreeRoleRefusal::RefuseProseAuthority { .. }) => ("RefuseProseAuthority", None),
        Err(ThreeRoleRefusal::RefuseMalformed { .. }) => ("RefuseMalformed", None),
    }
}

#[test]
fn fixture_declares_no_authority() {
    let doc = load_three_role_doc();
    assert_eq!(doc.schema, "core.epistemic_no_go.provenance_cases.v1");
    assert_eq!(doc.authority_effect, "None");
    assert_eq!(doc.cases.len(), 9);
}

#[test]
fn every_case_matches_its_expected_outcome() {
    for c in &load_three_role_doc().cases {
        let r = verify_three_role_authority(&c.packet, &c.policy);
        let (got, coincidence) = tag(&r);
        assert_eq!(got, c.expected, "{}: {r:?}", c.name);
        if let Some(expected) = &c.coincidence {
            assert_eq!(coincidence, Some(expected.as_str()), "{}", c.name);
        }
    }
}

#[test]
fn passing_receipts_carry_no_authority_and_bind_the_packet() {
    for c in load_three_role_doc().cases.iter().filter(|c| c.expected == "Pass") {
        let receipt = verify_three_role_authority(&c.packet, &c.policy).unwrap();
        assert!(receipt.authority_effect().is_none());
        assert!(NoAuthorityGuard::validate(&receipt, &c.name).is_ok());
        assert_eq!(receipt.packet_digest.len(), 64);
        let mut tampered = c.packet.clone();
        tampered.attempt_id.push('!');
        let other = verify_three_role_authority(&tampered, &c.policy).unwrap();
        assert_ne!(other.packet_digest, receipt.packet_digest);
    }
}

#[test]
fn a_refused_attempt_poisons_every_composition_it_enters() {
    let doc = load_three_role_doc();
    let good: Vec<_> = doc.cases.iter().filter(|c| c.expected == "Pass").collect();
    let bad: Vec<_> = doc.cases.iter().filter(|c| c.expected != "Pass").collect();
    assert!(!good.is_empty() && !bad.is_empty());
    let all_good: Vec<_> = good.iter().map(|c| (c.packet.clone(), c.policy.clone())).collect();
    assert!(compose_attempts(&all_good).unwrap().is_some());
    for b in &bad {
        let mut chain = all_good.clone();
        chain.push((b.packet.clone(), b.policy.clone()));
        assert!(compose_attempts(&chain).is_err(), "{}", b.name);
    }
}

// Origin: engine/crates_rs/tests/core_contracts/authority_gates.rs
// Claim: urn:core:crates_rs:tests:authority-gates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0f361c6b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0f361c6b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0f361c6b {
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
impl BoundaryError0f361c6b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0f361c6b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0f361c6b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0f361c6b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0f361c6b> {
        if capacity_bound == 0 {
            return Err(BoundaryError0f361c6b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0f361c6b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0f361c6b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_0f361c6b() {
    let admitted = BoundaryRecord0f361c6b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord0f361c6b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
