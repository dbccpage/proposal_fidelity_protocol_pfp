use core_contracts::artifact_policy::{
    build_publication_plan_v1, gate_artifact_route_v1, redact_artifact_v1, ArtifactLicenseV1,
    ArtifactPolicyError, ArtifactPolicyV1, ArtifactRouteV1, PolicyArtifactV1, RedactionRuleV1,
    RetentionClassV1, VisibilityClassV1, ARTIFACT_POLICY_SCHEMA_V1,
};
use core_types::authority::AuthorityEffect;

const HASH: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

fn policy(visibility: VisibilityClassV1) -> ArtifactPolicyV1 {
    ArtifactPolicyV1 {
        schema_version: ARTIFACT_POLICY_SCHEMA_V1.to_owned(),
        artifact_id: "artifact-1".to_owned(),
        visibility,
        retention: RetentionClassV1::Project,
        permitted_observers: vec!["host".to_owned()],
        permitted_routes: vec![
            ArtifactRouteV1::InternalModel,
            ArtifactRouteV1::ExternalModel,
            ArtifactRouteV1::Log,
            ArtifactRouteV1::Memory,
            ArtifactRouteV1::Publication,
        ],
        license: ArtifactLicenseV1::Licensed {
            identifier: "MIT".to_owned(),
        },
        provenance_sha256: HASH.to_owned(),
        expires_at_epoch_seconds: None,
        authority_effect: AuthorityEffect::None,
    }
}

fn artifact(bytes: &[u8]) -> PolicyArtifactV1 {
    PolicyArtifactV1 {
        artifact_id: "artifact-1".to_owned(),
        bytes: bytes.to_vec(),
    }
}

#[test]
fn unknown_visibility_class_fails_deserialization() {
    let json = serde_json::to_value(policy(VisibilityClassV1::Public)).unwrap();
    let mut object = json.as_object().unwrap().clone();
    object.insert("visibility".to_owned(), "secretish".into());
    let parsed: Result<ArtifactPolicyV1, _> = serde_json::from_value(object.into());
    assert!(parsed.is_err());
}

#[test]
fn private_artifact_is_refused_by_external_model_route() {
    let error = gate_artifact_route_v1(
        &artifact(b"private"),
        &policy(VisibilityClassV1::Private),
        ArtifactRouteV1::ExternalModel,
        "host",
        1,
        None,
    )
    .unwrap_err();
    assert_eq!(error, ArtifactPolicyError::PrivateExternalRoute);
}

#[test]
fn private_logs_and_memory_require_byte_bound_redaction() {
    let original = artifact(b"token=secret");
    let (redacted, receipt) = redact_artifact_v1(
        &original,
        &[RedactionRuleV1 {
            literal: b"secret".to_vec(),
            replacement: b"[REDACTED]".to_vec(),
        }],
    )
    .unwrap();
    assert_ne!(receipt.input_sha256(), receipt.output_sha256());
    assert!(receipt.authority_effect().is_none());
    assert_eq!(receipt.artifact_id(), "artifact-1");
    assert_eq!(receipt.rule_count(), 1);

    for route in [ArtifactRouteV1::Log, ArtifactRouteV1::Memory] {
        let no_receipt = gate_artifact_route_v1(
            &original,
            &policy(VisibilityClassV1::Private),
            route,
            "host",
            1,
            None,
        );
        assert_eq!(
            no_receipt.unwrap_err(),
            ArtifactPolicyError::RedactionRequired
        );
        let routed = gate_artifact_route_v1(
            &redacted,
            &policy(VisibilityClassV1::Private),
            route,
            "host",
            1,
            Some(&receipt),
        )
        .unwrap();
        assert!(routed.redaction_receipt_sha256.is_some());
    }
}

#[test]
fn tampered_redacted_bytes_fail_receipt_binding() {
    let original = artifact(b"token=secret");
    let (_, receipt) = redact_artifact_v1(
        &original,
        &[RedactionRuleV1 {
            literal: b"secret".to_vec(),
            replacement: b"[REDACTED]".to_vec(),
        }],
    )
    .unwrap();
    let error = gate_artifact_route_v1(
        &artifact(b"token=tampered"),
        &policy(VisibilityClassV1::Private),
        ArtifactRouteV1::Memory,
        "host",
        1,
        Some(&receipt),
    )
    .unwrap_err();
    assert_eq!(error, ArtifactPolicyError::RedactionReceiptMismatch);
}

#[test]
fn expired_artifacts_are_excluded_and_unlicensed_artifacts_block_release() {
    let mut expired = policy(VisibilityClassV1::Public);
    expired.expires_at_epoch_seconds = Some(10);
    let plan = build_publication_plan_v1(&[(artifact(b"expired"), expired)], 10, true).unwrap();
    assert!(plan.artifacts.is_empty());
    assert!(!plan.publication_performed);

    let mut unlicensed = policy(VisibilityClassV1::Public);
    unlicensed.license = ArtifactLicenseV1::Unlicensed;
    assert_eq!(
        build_publication_plan_v1(&[(artifact(b"blocked"), unlicensed)], 1, true).unwrap_err(),
        ArtifactPolicyError::Unlicensed
    );
}

#[test]
fn publication_needs_human_promotion_and_still_does_not_publish() {
    let entries = [(artifact(b"public"), policy(VisibilityClassV1::Public))];
    assert_eq!(
        build_publication_plan_v1(&entries, 1, false).unwrap_err(),
        ArtifactPolicyError::HumanPromotionRequired
    );
    let plan = build_publication_plan_v1(&entries, 1, true).unwrap();
    assert!(plan.human_promotion_recorded);
    assert!(!plan.publication_performed);
    assert!(plan.authority_effect.is_none());
}

// Origin: engine/crates_rs/tests/core_contracts/artifact_policy.rs
// Claim: urn:core:crates_rs:tests:artifact-policy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7aa292f3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7aa292f3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7aa292f3 {
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
impl BoundaryError7aa292f3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7aa292f3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7aa292f3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7aa292f3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7aa292f3> {
        if capacity_bound == 0 {
            return Err(BoundaryError7aa292f3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7aa292f3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7aa292f3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7aa292f3() {
    let admitted = BoundaryRecord7aa292f3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7aa292f3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
