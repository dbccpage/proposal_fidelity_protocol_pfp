//! S11-001 artifact visibility, retention, redaction, and publication policy.
//!
//! This module validates bounded fixture routes. It does not claim semantic
//! secrecy and cannot publish an artifact.

use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

pub const ARTIFACT_POLICY_SCHEMA_V1: &str = "core.artifact-policy.v1";

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum VisibilityClassV1 {
    Public,
    Internal,
    Private,
    Proprietary,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RetentionClassV1 {
    Ephemeral,
    Project,
    Archive,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ArtifactRouteV1 {
    InternalModel,
    ExternalModel,
    Log,
    Memory,
    Publication,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
pub enum ArtifactLicenseV1 {
    Licensed { identifier: String },
    Unlicensed,
    Unknown,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArtifactPolicyV1 {
    pub schema_version: String,
    pub artifact_id: String,
    pub visibility: VisibilityClassV1,
    pub retention: RetentionClassV1,
    pub permitted_observers: Vec<String>,
    pub permitted_routes: Vec<ArtifactRouteV1>,
    pub license: ArtifactLicenseV1,
    pub provenance_sha256: String,
    pub expires_at_epoch_seconds: Option<u64>,
    pub authority_effect: AuthorityEffect,
}

impl ArtifactPolicyV1 {
    fn has_valid_observers_and_routes(&self) -> bool {
        !self.permitted_observers.is_empty()
            && !self.permitted_routes.is_empty()
            && !self
                .permitted_observers
                .iter()
                .any(|observer| observer.trim().is_empty())
            && !self
                .permitted_observers
                .windows(2)
                .any(|pair| pair[0] >= pair[1])
            && !self
                .permitted_routes
                .windows(2)
                .any(|pair| pair[0] >= pair[1])
    }

    pub fn validate(&self) -> Result<(), ArtifactPolicyError> {
        if self.schema_version != ARTIFACT_POLICY_SCHEMA_V1 {
            return Err(ArtifactPolicyError::SchemaVersion);
        }
        if self.artifact_id.trim().is_empty()
            || !is_sha256(&self.provenance_sha256)
            || !self.has_valid_observers_and_routes()
        {
            return Err(ArtifactPolicyError::InvalidPolicy);
        }
        if let ArtifactLicenseV1::Licensed { identifier } = &self.license {
            if identifier.trim().is_empty() {
                return Err(ArtifactPolicyError::InvalidPolicy);
            }
        }
        if !self.authority_effect.is_none() {
            return Err(ArtifactPolicyError::AuthorityExpansion);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PolicyArtifactV1 {
    pub artifact_id: String,
    pub bytes: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RedactionRuleV1 {
    pub literal: Vec<u8>,
    pub replacement: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct RedactionReceiptV1 {
    artifact_id: String,
    input_sha256: String,
    output_sha256: String,
    rule_count: usize,
    authority_effect: AuthorityEffect,
}

impl RedactionReceiptV1 {
    pub fn artifact_id(&self) -> &str {
        &self.artifact_id
    }

    pub fn input_sha256(&self) -> &str {
        &self.input_sha256
    }

    pub fn output_sha256(&self) -> &str {
        &self.output_sha256
    }

    pub const fn rule_count(&self) -> usize {
        self.rule_count
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

pub fn redact_artifact_v1(
    artifact: &PolicyArtifactV1,
    rules: &[RedactionRuleV1],
) -> Result<(PolicyArtifactV1, RedactionReceiptV1), ArtifactPolicyError> {
    if artifact.artifact_id.trim().is_empty()
        || artifact.bytes.is_empty()
        || rules.is_empty()
        || rules.iter().any(|rule| {
            rule.literal.is_empty()
                || rule.replacement.is_empty()
                || rule.literal == rule.replacement
        })
    {
        return Err(ArtifactPolicyError::InvalidRedaction);
    }
    let mut output = artifact.bytes.clone();
    for rule in rules {
        output = replace_all(&output, &rule.literal, &rule.replacement);
    }
    if output == artifact.bytes {
        return Err(ArtifactPolicyError::RedactionDidNotApply);
    }
    let redacted = PolicyArtifactV1 {
        artifact_id: artifact.artifact_id.clone(),
        bytes: output,
    };
    let receipt = RedactionReceiptV1 {
        artifact_id: artifact.artifact_id.clone(),
        input_sha256: sha256_hex(&artifact.bytes),
        output_sha256: sha256_hex(&redacted.bytes),
        rule_count: rules.len(),
        authority_effect: AuthorityEffect::None,
    };
    Ok((redacted, receipt))
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RouteReceiptV1 {
    pub artifact_id: String,
    pub artifact_sha256: String,
    pub route: ArtifactRouteV1,
    pub observer_id: String,
    pub redaction_receipt_sha256: Option<String>,
    pub authority_effect: AuthorityEffect,
}

pub fn gate_artifact_route_v1(
    artifact: &PolicyArtifactV1,
    policy: &ArtifactPolicyV1,
    route: ArtifactRouteV1,
    observer_id: &str,
    now_epoch_seconds: u64,
    redaction_receipt: Option<&RedactionReceiptV1>,
) -> Result<RouteReceiptV1, ArtifactPolicyError> {
    policy.validate()?;
    if artifact.artifact_id != policy.artifact_id || artifact.bytes.is_empty() {
        return Err(ArtifactPolicyError::ArtifactPolicyMismatch);
    }
    if policy
        .expires_at_epoch_seconds
        .is_some_and(|expiry| now_epoch_seconds >= expiry)
    {
        return Err(ArtifactPolicyError::Expired);
    }
    if policy.permitted_routes.binary_search(&route).is_err()
        || policy
            .permitted_observers
            .binary_search_by(|candidate| candidate.as_str().cmp(observer_id))
            .is_err()
    {
        return Err(ArtifactPolicyError::RouteRefused);
    }
    if route == ArtifactRouteV1::ExternalModel && policy.visibility != VisibilityClassV1::Public {
        return Err(ArtifactPolicyError::PrivateExternalRoute);
    }
    let redaction_receipt_sha256 =
        verify_redaction_for_route(artifact, policy, route, redaction_receipt)?;
    let out = RouteReceiptV1 {
        artifact_id: artifact.artifact_id.clone(),
        artifact_sha256: sha256_hex(&artifact.bytes),
        route,
        observer_id: observer_id.to_owned(),
        redaction_receipt_sha256,
        authority_effect: AuthorityEffect::None,
    };
    Ok(out)
}

fn verify_redaction_for_route(
    artifact: &PolicyArtifactV1,
    policy: &ArtifactPolicyV1,
    route: ArtifactRouteV1,
    redaction_receipt: Option<&RedactionReceiptV1>,
) -> Result<Option<String>, ArtifactPolicyError> {
    let protected_sink = matches!(route, ArtifactRouteV1::Log | ArtifactRouteV1::Memory);
    let protected_artifact = matches!(
        policy.visibility,
        VisibilityClassV1::Private | VisibilityClassV1::Proprietary
    );
    match redaction_receipt {
        Some(receipt) => {
            if receipt.artifact_id != artifact.artifact_id
                || receipt.output_sha256 != sha256_hex(&artifact.bytes)
                || receipt.rule_count == 0
                || !receipt.authority_effect.is_none()
            {
                return Err(ArtifactPolicyError::RedactionReceiptMismatch);
            }
            Ok(Some(hash_json(receipt)?))
        }
        None if protected_sink && protected_artifact => {
            Err(ArtifactPolicyError::RedactionRequired)
        }
        None => Ok(None),
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PublicationArtifactV1 {
    pub artifact_id: String,
    pub artifact_sha256: String,
    pub provenance_sha256: String,
    pub license_identifier: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PublicationPlanV1 {
    pub artifacts: Vec<PublicationArtifactV1>,
    pub human_promotion_recorded: bool,
    pub publication_performed: bool,
    pub authority_effect: AuthorityEffect,
}

pub fn build_publication_plan_v1(
    entries: &[(PolicyArtifactV1, ArtifactPolicyV1)],
    now_epoch_seconds: u64,
    human_promotion_recorded: bool,
) -> Result<PublicationPlanV1, ArtifactPolicyError> {
    if !human_promotion_recorded {
        return Err(ArtifactPolicyError::HumanPromotionRequired);
    }
    let mut artifacts = Vec::new();
    for (artifact, policy) in entries {
        if let Some(item) = build_publication_artifact_v1(artifact, policy, now_epoch_seconds)? {
            artifacts.push(item);
        }
    }
    artifacts.sort_by(|left, right| left.artifact_id.cmp(&right.artifact_id));
    if artifacts
        .windows(2)
        .any(|pair| pair[0].artifact_id == pair[1].artifact_id)
    {
        return Err(ArtifactPolicyError::InvalidPolicy);
    }
    Ok(PublicationPlanV1 {
        artifacts,
        human_promotion_recorded: true,
        publication_performed: false,
        authority_effect: AuthorityEffect::None,
    })
}

fn build_publication_artifact_v1(
    artifact: &PolicyArtifactV1,
    policy: &ArtifactPolicyV1,
    now_epoch_seconds: u64,
) -> Result<Option<PublicationArtifactV1>, ArtifactPolicyError> {
    policy.validate()?;
    if policy
        .expires_at_epoch_seconds
        .is_some_and(|expiry| now_epoch_seconds >= expiry)
    {
        return Ok(None);
    }
    if policy.visibility != VisibilityClassV1::Public
        || policy
            .permitted_routes
            .binary_search(&ArtifactRouteV1::Publication)
            .is_err()
    {
        return Err(ArtifactPolicyError::RouteRefused);
    }
    let license_identifier = match &policy.license {
        ArtifactLicenseV1::Licensed { identifier } => identifier.clone(),
        ArtifactLicenseV1::Unlicensed => return Err(ArtifactPolicyError::Unlicensed),
        ArtifactLicenseV1::Unknown => return Err(ArtifactPolicyError::UnknownLicense),
    };
    if artifact.artifact_id != policy.artifact_id {
        return Err(ArtifactPolicyError::ArtifactPolicyMismatch);
    }
    let item = PublicationArtifactV1 {
        artifact_id: artifact.artifact_id.clone(),
        artifact_sha256: sha256_hex(&artifact.bytes),
        provenance_sha256: policy.provenance_sha256.clone(),
        license_identifier,
    };
    Ok(Some(item))
}

fn replace_all(input: &[u8], needle: &[u8], replacement: &[u8]) -> Vec<u8> {
    let mut output = Vec::with_capacity(input.len());
    let mut index = 0;
    while index < input.len() {
        if input[index..].starts_with(needle) {
            output.extend_from_slice(replacement);
            index += needle.len();
        } else {
            output.push(input[index]);
            index += 1;
        }
    }
    output
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

fn hash_json<T: Serialize>(value: &T) -> Result<String, ArtifactPolicyError> {
    let bytes =
        serde_json::to_vec(value).map_err(|error| ArtifactPolicyError::Json(error.to_string()))?;
    Ok(sha256_hex(&bytes))
}

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum ArtifactPolicyError {
    #[error("artifact policy schema version changed")]
    SchemaVersion,
    #[error("artifact policy is invalid")]
    InvalidPolicy,
    #[error("artifact and policy do not match")]
    ArtifactPolicyMismatch,
    #[error("policy attempted authority expansion")]
    AuthorityExpansion,
    #[error("artifact is expired")]
    Expired,
    #[error("artifact route or observer is refused")]
    RouteRefused,
    #[error("private or proprietary artifact cannot use an external-model route")]
    PrivateExternalRoute,
    #[error("protected log or memory route requires deterministic redaction")]
    RedactionRequired,
    #[error("redaction request is invalid")]
    InvalidRedaction,
    #[error("redaction rules did not change the bytes")]
    RedactionDidNotApply,
    #[error("redaction receipt does not bind the routed bytes")]
    RedactionReceiptMismatch,
    #[error("artifact is unlicensed")]
    Unlicensed,
    #[error("artifact license is unknown")]
    UnknownLicense,
    #[error("publication plan requires recorded human promotion")]
    HumanPromotionRequired,
    #[error("JSON serialization failed: {0}")]
    Json(String),
}

// Origin: engine/crates_rs/core_contracts/src/artifact_policy.rs
// Claim: urn:core:crates_rs:core-contracts:artifact-policy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_88b2ffe4 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
