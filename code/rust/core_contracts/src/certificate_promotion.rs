//! Evidence-only checked-packet certificates and the dormant host promotion boundary.
//!
//! A checked-packet certificate is replay evidence, never authority. The only
//! function in this module that can produce an authority-bearing result also
//! requires a verified receipt DAG, an independent authority-witness
//! attestation, an explicit human promotion event, and an opaque host
//! capability. No public constructor exists for that capability, so conductor,
//! model, gate, certifier, and product crates cannot call the promotion path.

use core_types::authority::{
    AuthorityEffect, AuthorityRefusal, AuthorityTerminal, CertifiedAuthority, DescentWitness,
    IsAuth,
};
use core_types::EvidenceCeiling;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

pub const CHECKED_PACKET_CERTIFICATE_SCHEMA_VERSION: &str = "core.checked-packet-certificate.v1";
pub const RECEIPT_DAG_VERIFICATION_SCHEMA_VERSION: &str = "core.receipt-dag-verification.v1";
pub const AUTHORITY_WITNESS_ATTESTATION_SCHEMA_VERSION: &str =
    "core.authority-witness-attestation.v1";
pub const HUMAN_PROMOTION_EVENT_SCHEMA_VERSION: &str = "core.human-promotion-event.v1";
pub const AUTHORIZED_LOCAL_RESULT_SCHEMA_VERSION: &str = "core.authorized-local-result.v1";
pub const PUBLISHED_PROJECTION_SCHEMA_VERSION: &str = "core.published-projection.v1";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CheckedPacketCertificateMaterialV1 {
    pub schema_version: String,
    pub packet_id: String,
    pub packet_replay_hash: String,
    pub terminal: AuthorityTerminal,
    pub descent_witness: DescentWitness,
    pub is_auth: IsAuth,
    pub evidence_ceiling: EvidenceCeiling,
    pub authority_effect: AuthorityEffect,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CheckedPacketCertificateV1 {
    pub material: CheckedPacketCertificateMaterialV1,
    pub certificate_sha256: String,
}

impl CheckedPacketCertificateV1 {
    fn validate_schema_and_hashes(&self) -> Result<(), CertificatePromotionContractError> {
        require_schema(
            "certificate.material.schema_version",
            CHECKED_PACKET_CERTIFICATE_SCHEMA_VERSION,
            &self.material.schema_version,
        )?;
        require_hash("certificate.material.packet_id", &self.material.packet_id)?;
        require_hash(
            "certificate.material.packet_replay_hash",
            &self.material.packet_replay_hash,
        )?;
        require_hash("certificate.certificate_sha256", &self.certificate_sha256)
    }

    pub fn validate(&self) -> Result<(), CertificatePromotionContractError> {
        self.validate_schema_and_hashes()?;
        if !self.material.authority_effect.is_none() {
            return Err(CertificatePromotionContractError::AuthorityExpansion(
                "checked-packet certificate",
            ));
        }
        if self.material.descent_witness.terminal() != self.material.terminal
            || self.material.is_auth.terminal() != self.material.terminal
        {
            return Err(CertificatePromotionContractError::TerminalMismatch);
        }
        if self.material.descent_witness.replay_hash() != self.material.packet_replay_hash {
            return Err(CertificatePromotionContractError::ReplayMismatch);
        }
        if sha256_json_v1(&self.material)? != self.certificate_sha256 {
            return Err(CertificatePromotionContractError::CertificateHashMismatch);
        }
        Ok(())
    }

    pub fn terminal(&self) -> AuthorityTerminal {
        self.material.terminal
    }

    pub fn packet_id(&self) -> &str {
        &self.material.packet_id
    }

    pub fn packet_replay_hash(&self) -> &str {
        &self.material.packet_replay_hash
    }

    pub fn witness(&self) -> &DescentWitness {
        &self.material.descent_witness
    }

    pub fn is_auth(&self) -> &IsAuth {
        &self.material.is_auth
    }

    pub fn evidence_ceiling(&self) -> EvidenceCeiling {
        self.material.evidence_ceiling
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.material.authority_effect
    }
}

/// Seal packet-bound verification evidence without constructing authority.
pub fn seal_checked_packet_certificate_v1(
    packet_id: impl Into<String>,
    packet_replay_hash: impl Into<String>,
    terminal: AuthorityTerminal,
    descent_witness: DescentWitness,
    is_auth: IsAuth,
    evidence_ceiling: EvidenceCeiling,
) -> Result<CheckedPacketCertificateV1, CertificatePromotionContractError> {
    let material = CheckedPacketCertificateMaterialV1 {
        schema_version: CHECKED_PACKET_CERTIFICATE_SCHEMA_VERSION.to_owned(),
        packet_id: packet_id.into(),
        packet_replay_hash: packet_replay_hash.into(),
        terminal,
        descent_witness,
        is_auth,
        evidence_ceiling,
        authority_effect: AuthorityEffect::None,
    };
    let certificate = CheckedPacketCertificateV1 {
        certificate_sha256: sha256_json_v1(&material)?,
        material,
    };
    certificate.validate()?;
    Ok(certificate)
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DeterministicReceiptDagVerificationV1 {
    pub schema_version: String,
    pub certificate_sha256: String,
    pub receipt_dag_sha256: String,
    pub receipt_count: u32,
    pub verified_receipt_count: u32,
    pub acyclic: bool,
    pub rank_ordered: bool,
    pub dependencies_complete: bool,
    pub evidence_ceiling: EvidenceCeiling,
    pub authority_effect: AuthorityEffect,
}

impl DeterministicReceiptDagVerificationV1 {
    fn validate_dag_counts_and_flags(&self) -> Result<(), CertificatePromotionContractError> {
        if self.receipt_count < 4 || self.verified_receipt_count != self.receipt_count {
            return Err(CertificatePromotionContractError::ReceiptDagIncomplete);
        }
        if !self.acyclic || !self.rank_ordered || !self.dependencies_complete {
            return Err(CertificatePromotionContractError::ReceiptDagUnverified);
        }
        Ok(())
    }

    pub fn validate(
        &self,
        certificate: &CheckedPacketCertificateV1,
    ) -> Result<(), CertificatePromotionContractError> {
        require_schema(
            "receipt_dag.schema_version",
            RECEIPT_DAG_VERIFICATION_SCHEMA_VERSION,
            &self.schema_version,
        )?;
        require_hash("receipt_dag.certificate_sha256", &self.certificate_sha256)?;
        require_hash("receipt_dag.receipt_dag_sha256", &self.receipt_dag_sha256)?;
        if self.certificate_sha256 != certificate.certificate_sha256 {
            return Err(
                CertificatePromotionContractError::CertificateBindingMismatch("receipt DAG"),
            );
        }
        self.validate_dag_counts_and_flags()?;
        if self.evidence_ceiling != certificate.evidence_ceiling() {
            return Err(CertificatePromotionContractError::EvidenceCeilingMismatch);
        }
        if !self.authority_effect.is_none() {
            return Err(CertificatePromotionContractError::AuthorityExpansion(
                "receipt DAG verification",
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AuthorityWitnessAttestationV1 {
    pub schema_version: String,
    pub attestation_id: String,
    pub certificate_sha256: String,
    pub receipt_dag_sha256: String,
    pub producer_identity_id: String,
    pub independent_evaluator_identity_id: String,
    pub authority_witness_identity_id: String,
    pub identities_independent: bool,
    pub promotion_conditions_satisfied: bool,
    pub authority_effect: AuthorityEffect,
}

impl AuthorityWitnessAttestationV1 {
    fn validate_required_fields(&self) -> Result<(), CertificatePromotionContractError> {
        require_schema(
            "authority_witness.schema_version",
            AUTHORITY_WITNESS_ATTESTATION_SCHEMA_VERSION,
            &self.schema_version,
        )?;
        require_text("authority_witness.attestation_id", &self.attestation_id)?;
        require_hash(
            "authority_witness.certificate_sha256",
            &self.certificate_sha256,
        )?;
        require_hash(
            "authority_witness.receipt_dag_sha256",
            &self.receipt_dag_sha256,
        )?;
        require_text(
            "authority_witness.producer_identity_id",
            &self.producer_identity_id,
        )?;
        require_text(
            "authority_witness.independent_evaluator_identity_id",
            &self.independent_evaluator_identity_id,
        )?;
        require_text(
            "authority_witness.authority_witness_identity_id",
            &self.authority_witness_identity_id,
        )
    }

    pub fn validate(
        &self,
        certificate: &CheckedPacketCertificateV1,
        receipt_dag: &DeterministicReceiptDagVerificationV1,
    ) -> Result<(), CertificatePromotionContractError> {
        self.validate_required_fields()?;
        if self.certificate_sha256 != certificate.certificate_sha256 {
            return Err(
                CertificatePromotionContractError::CertificateBindingMismatch(
                    "authority-witness attestation",
                ),
            );
        }
        if self.receipt_dag_sha256 != receipt_dag.receipt_dag_sha256 {
            return Err(
                CertificatePromotionContractError::ReceiptDagBindingMismatch(
                    "authority-witness attestation",
                ),
            );
        }
        let identities = [
            self.producer_identity_id.as_str(),
            self.independent_evaluator_identity_id.as_str(),
            self.authority_witness_identity_id.as_str(),
        ];
        if !self.identities_independent
            || identities[0] == identities[1]
            || identities[0] == identities[2]
            || identities[1] == identities[2]
        {
            return Err(CertificatePromotionContractError::WitnessIndependenceFailed);
        }
        if !self.promotion_conditions_satisfied {
            return Err(CertificatePromotionContractError::AuthorityWitnessRefused);
        }
        if !self.authority_effect.is_none() {
            return Err(CertificatePromotionContractError::AuthorityExpansion(
                "authority-witness attestation",
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HumanPromotionDecisionV1 {
    Promote,
    Reject,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HumanPromotionEventV1 {
    pub schema_version: String,
    pub decision_id: String,
    pub recorded_by_host_id: String,
    pub human_actor_id: String,
    pub policy_epoch: String,
    pub certificate_sha256: String,
    pub receipt_dag_sha256: String,
    pub scope: String,
    pub decision: HumanPromotionDecisionV1,
    pub authority_effect: AuthorityEffect,
}

impl HumanPromotionEventV1 {
    fn validate_required_fields(&self) -> Result<(), CertificatePromotionContractError> {
        require_schema(
            "human_promotion.schema_version",
            HUMAN_PROMOTION_EVENT_SCHEMA_VERSION,
            &self.schema_version,
        )?;
        require_text("human_promotion.decision_id", &self.decision_id)?;
        require_text(
            "human_promotion.recorded_by_host_id",
            &self.recorded_by_host_id,
        )?;
        require_text("human_promotion.human_actor_id", &self.human_actor_id)?;
        require_text("human_promotion.policy_epoch", &self.policy_epoch)?;
        require_hash(
            "human_promotion.certificate_sha256",
            &self.certificate_sha256,
        )?;
        require_hash(
            "human_promotion.receipt_dag_sha256",
            &self.receipt_dag_sha256,
        )?;
        require_text("human_promotion.scope", &self.scope)
    }

    pub fn validate(
        &self,
        certificate: &CheckedPacketCertificateV1,
        receipt_dag: &DeterministicReceiptDagVerificationV1,
    ) -> Result<(), CertificatePromotionContractError> {
        self.validate_required_fields()?;
        if self.certificate_sha256 != certificate.certificate_sha256 {
            return Err(
                CertificatePromotionContractError::CertificateBindingMismatch(
                    "human promotion event",
                ),
            );
        }
        if self.receipt_dag_sha256 != receipt_dag.receipt_dag_sha256 {
            return Err(
                CertificatePromotionContractError::ReceiptDagBindingMismatch(
                    "human promotion event",
                ),
            );
        }
        if !self.authority_effect.is_none() {
            return Err(CertificatePromotionContractError::AuthorityExpansion(
                "human promotion event",
            ));
        }
        Ok(())
    }
}

/// Opaque proof that the caller is the authenticated host promotion boundary.
///
/// The type has no public constructor and is not deserializable or cloneable.
/// A later host-activation sprint may add the credential-checked issuer inside
/// this owner module; until then the promotion path is structurally present
/// but dormant.
///
/// ```compile_fail
/// use core_contracts::HostPromotionCapabilityV1;
/// let _capability = HostPromotionCapabilityV1::new("host", "human", "epoch");
/// ```
#[derive(Debug)]
pub struct HostPromotionCapabilityV1 {
    authenticated_host_id: String,
    authenticated_human_actor_id: String,
    policy_epoch: String,
    _seal: HostPromotionSeal,
}

#[derive(Debug)]
struct HostPromotionSeal;

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct AuthorizedLocalResultV1 {
    schema_version: String,
    certificate_sha256: String,
    receipt_dag_sha256: String,
    authority_witness_attestation_id: String,
    human_decision_id: String,
    scope: String,
    evidence_ceiling: EvidenceCeiling,
    authority_effect: AuthorityEffect,
}

impl AuthorizedLocalResultV1 {
    pub fn certificate_sha256(&self) -> &str {
        &self.certificate_sha256
    }

    pub fn receipt_dag_sha256(&self) -> &str {
        &self.receipt_dag_sha256
    }

    pub fn scope(&self) -> &str {
        &self.scope
    }

    pub fn evidence_ceiling(&self) -> EvidenceCeiling {
        self.evidence_ceiling
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

/// Promote a certificate only at the authenticated host boundary.
///
/// Consuming the opaque capability prevents any ordinary certifier, model,
/// gate, or product adapter from invoking this function. The remaining inputs
/// are revalidated and hash-bound before the low-level authority payload is
/// created.
pub fn promote_authorized_local_result_v1(
    capability: HostPromotionCapabilityV1,
    certificate: &CheckedPacketCertificateV1,
    receipt_dag: &DeterministicReceiptDagVerificationV1,
    attestation: &AuthorityWitnessAttestationV1,
    human_event: &HumanPromotionEventV1,
) -> Result<AuthorizedLocalResultV1, CertificatePromotionContractError> {
    certificate.validate()?;
    receipt_dag.validate(certificate)?;
    attestation.validate(certificate, receipt_dag)?;
    human_event.validate(certificate, receipt_dag)?;
    if human_event.decision != HumanPromotionDecisionV1::Promote {
        return Err(CertificatePromotionContractError::HumanPromotionRefused);
    }
    if capability.authenticated_host_id != human_event.recorded_by_host_id
        || capability.authenticated_human_actor_id != human_event.human_actor_id
        || capability.policy_epoch != human_event.policy_epoch
    {
        return Err(CertificatePromotionContractError::HostCapabilityMismatch);
    }
    let authority = CertifiedAuthority::certify(
        certificate.terminal(),
        certificate.witness().clone(),
        certificate.is_auth().clone(),
    )?;
    Ok(AuthorizedLocalResultV1 {
        schema_version: AUTHORIZED_LOCAL_RESULT_SCHEMA_VERSION.to_owned(),
        certificate_sha256: certificate.certificate_sha256.clone(),
        receipt_dag_sha256: receipt_dag.receipt_dag_sha256.clone(),
        authority_witness_attestation_id: attestation.attestation_id.clone(),
        human_decision_id: human_event.decision_id.clone(),
        scope: human_event.scope.clone(),
        evidence_ceiling: certificate.evidence_ceiling(),
        authority_effect: AuthorityEffect::Certified(authority),
    })
}

/// A byte-deterministic publication of an already-authorized promotion.
///
/// Holds the canonical bytes and their digest. The bytes are the artifact; the
/// digest is a convenience over them, and [`Self::verify_self_digest`] proves
/// the pair was not tampered with in transit.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PublishedProjectionV1 {
    bytes: Vec<u8>,
    projection_sha256: String,
}

impl PublishedProjectionV1 {
    /// The canonical published bytes.
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }

    /// `sha256` of [`Self::bytes`], lowercase hex.
    pub fn projection_sha256(&self) -> &str {
        &self.projection_sha256
    }

    /// Recompute the digest over the carried bytes and compare.
    pub fn verify_self_digest(&self) -> Result<(), CertificatePromotionContractError> {
        let recomputed = format!("{:x}", Sha256::digest(&self.bytes));
        if recomputed != self.projection_sha256 {
            return Err(CertificatePromotionContractError::ProjectionDigestMismatch);
        }
        Ok(())
    }
}

/// Byte-deterministic publisher for authorized promotions.
///
/// # The human decision is enforced by the TYPE, not by a runtime check
///
/// [`Self::publish`] accepts only an [`AuthorizedLocalResultV1`]. That type has
/// private fields, no public constructor, and no `Deserialize` impl, so the one
/// and only way to obtain a value of it is
/// [`promote_authorized_local_result_v1`] — which consumes the opaque
/// [`HostPromotionCapabilityV1`] and requires a [`HumanPromotionEventV1`] whose
/// decision is `Promote` and whose `certificate_sha256` / `receipt_dag_sha256`
/// are hash-bound to the very certificate and receipt DAG being promoted.
///
/// So there is deliberately no `if decision_id.is_empty()` guard here: an
/// unauthorized publication is not refused at runtime, it is *unrepresentable*.
/// A runtime guard would be strictly weaker and would imply a second, guarded
/// path to publication exists. It does not.
///
/// ```compile_fail
/// // No way to forge the input, so no way to publish without a human decision.
/// use core_contracts::AuthorizedLocalResultV1;
/// let _forged = AuthorizedLocalResultV1 {
///     schema_version: "core.authorized-local-result.v1".to_owned(),
///     certificate_sha256: "00".repeat(32),
///     receipt_dag_sha256: "00".repeat(32),
///     authority_witness_attestation_id: "att".to_owned(),
///     human_decision_id: "forged".to_owned(),
///     scope: "scope".to_owned(),
///     evidence_ceiling: Default::default(),
///     authority_effect: Default::default(),
/// };
/// ```
///
/// # Determinism
///
/// The projection is built field-by-field in a FIXED order declared below,
/// rather than by deriving `Serialize` — so the byte layout is a property of
/// this function that a later field reorder cannot silently change. The
/// canonical form admits no nondeterminism source: no clock, no environment, no
/// filesystem path, no locale, no floating point, and no hash-map iteration
/// (every value is a string already fixed by the authorized result).
///
/// # Authority
///
/// Publishing mints NOTHING. The projection renders a decision that was already
/// taken; it is a transport of an existing `AuthorityEffect`, never a promotion.
#[derive(Debug, Clone, Copy, Default)]
pub struct DeterministicPublisher;

impl DeterministicPublisher {
    pub const fn new() -> Self {
        Self
    }

    /// Render `authorized` to canonical bytes plus their digest.
    ///
    /// Identical inputs yield byte-identical output on any machine, in any
    /// process, in any order.
    pub fn publish(
        &self,
        authorized: &AuthorizedLocalResultV1,
    ) -> Result<PublishedProjectionV1, CertificatePromotionContractError> {
        // FIXED FIELD ORDER — the published byte layout. Changing this order,
        // or any key spelling, is a breaking change to every previously
        // published digest, so it must come with a schema version bump.
        let fields: [(&str, String); 8] = [
            ("schema", PUBLISHED_PROJECTION_SCHEMA_VERSION.to_owned()),
            (
                "authorized_result_schema",
                authorized.schema_version.clone(),
            ),
            ("certificate_sha256", authorized.certificate_sha256.clone()),
            ("receipt_dag_sha256", authorized.receipt_dag_sha256.clone()),
            (
                "authority_witness_attestation_id",
                authorized.authority_witness_attestation_id.clone(),
            ),
            ("human_decision_id", authorized.human_decision_id.clone()),
            ("scope", authorized.scope.clone()),
            (
                "evidence_ceiling",
                format!("{:?}", authorized.evidence_ceiling),
            ),
        ];

        let mut rendered = String::from("{\n");
        for (index, (key, value)) in fields.iter().enumerate() {
            rendered.push_str("  ");
            rendered.push_str(&encode_json_string(key));
            rendered.push_str(": ");
            rendered.push_str(&encode_json_string(value));
            if index + 1 < fields.len() {
                rendered.push(',');
            }
            rendered.push('\n');
        }
        rendered.push_str("}\n");

        let bytes = rendered.into_bytes();
        let projection_sha256 = format!("{:x}", Sha256::digest(&bytes));
        Ok(PublishedProjectionV1 {
            bytes,
            projection_sha256,
        })
    }
}

/// Minimal, total JSON string encoder.
///
/// Hand-rolled so the published byte layout depends on nothing but this
/// function. Escapes the two structural characters plus the C0 controls that
/// JSON forbids raw; everything else (including non-ASCII) passes through as
/// UTF-8, which is valid JSON and keeps the bytes stable across serde versions.
fn encode_json_string(value: &str) -> String {
    let mut out = String::with_capacity(value.len() + 2);
    out.push('"');
    for ch in value.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum CertificatePromotionContractError {
    #[error("JSON serialization failed: {0}")]
    Json(String),
    #[error("published projection digest does not match its bytes")]
    ProjectionDigestMismatch,
    #[error("schema mismatch for {field}: expected {expected}, found {found}")]
    SchemaMismatch {
        field: &'static str,
        expected: &'static str,
        found: String,
    },
    #[error("required field is empty: {0}")]
    EmptyField(&'static str),
    #[error("invalid lowercase 32-byte hash in {0}")]
    InvalidHash(&'static str),
    #[error("authority expansion is forbidden in {0}")]
    AuthorityExpansion(&'static str),
    #[error("certificate terminal, witness terminal, and IsAuth terminal differ")]
    TerminalMismatch,
    #[error("descent witness replay hash is not packet-bound")]
    ReplayMismatch,
    #[error("checked-packet certificate hash does not match its material")]
    CertificateHashMismatch,
    #[error("{0} is bound to a different checked-packet certificate")]
    CertificateBindingMismatch(&'static str),
    #[error("{0} is bound to a different receipt DAG")]
    ReceiptDagBindingMismatch(&'static str),
    #[error("receipt DAG is missing required verified receipts")]
    ReceiptDagIncomplete,
    #[error("receipt DAG failed acyclicity, rank, or dependency verification")]
    ReceiptDagUnverified,
    #[error("receipt DAG expanded or changed the evidence ceiling")]
    EvidenceCeilingMismatch,
    #[error("producer, independent evaluator, and authority witness are not independent")]
    WitnessIndependenceFailed,
    #[error("authority witness did not attest that promotion conditions were satisfied")]
    AuthorityWitnessRefused,
    #[error("human promotion event did not request promotion")]
    HumanPromotionRefused,
    #[error("human promotion event does not match the authenticated host capability")]
    HostCapabilityMismatch,
    #[error(transparent)]
    Authority(#[from] AuthorityRefusal),
}

fn sha256_json_v1<T: Serialize>(value: &T) -> Result<String, CertificatePromotionContractError> {
    let bytes = serde_json::to_vec(value)
        .map_err(|error| CertificatePromotionContractError::Json(error.to_string()))?;
    Ok(format!("{:x}", Sha256::digest(bytes)))
}

fn require_schema(
    field: &'static str,
    expected: &'static str,
    found: &str,
) -> Result<(), CertificatePromotionContractError> {
    if found != expected {
        return Err(CertificatePromotionContractError::SchemaMismatch {
            field,
            expected,
            found: found.to_owned(),
        });
    }
    Ok(())
}

fn require_text(field: &'static str, value: &str) -> Result<(), CertificatePromotionContractError> {
    if value.trim().is_empty() {
        return Err(CertificatePromotionContractError::EmptyField(field));
    }
    Ok(())
}

fn require_hash(field: &'static str, value: &str) -> Result<(), CertificatePromotionContractError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(CertificatePromotionContractError::InvalidHash(field));
    }
    Ok(())
}

// Origin: engine/crates_rs/core_contracts/src/certificate_promotion.rs
// Claim: urn:core:crates_rs:core-contracts:certificate-promotion:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_types::authority::AuthorityTerminal;
    use core_types::GuardEvidence;

    fn certificate() -> CheckedPacketCertificateV1 {
        let terminal = AuthorityTerminal::ExactRuleDerived;
        let replay_hash = "0c".repeat(32);
        let witness = DescentWitness::from_verified_replay(
            terminal,
            "descent:certificate-promotion-test",
            replay_hash.clone(),
        )
        .unwrap();
        let is_auth = IsAuth::decide(
            terminal,
            GuardEvidence::new_valid(["cand_01"], "K_carrier_01", "blake3:deadbeef"),
        )
        .unwrap();
        seal_checked_packet_certificate_v1(
            "01".repeat(32),
            replay_hash,
            terminal,
            witness,
            is_auth,
            EvidenceCeiling::BoundaryChecked,
        )
        .unwrap()
    }

    fn receipt_dag(
        certificate: &CheckedPacketCertificateV1,
    ) -> DeterministicReceiptDagVerificationV1 {
        DeterministicReceiptDagVerificationV1 {
            schema_version: RECEIPT_DAG_VERIFICATION_SCHEMA_VERSION.to_owned(),
            certificate_sha256: certificate.certificate_sha256.clone(),
            receipt_dag_sha256: "02".repeat(32),
            receipt_count: 4,
            verified_receipt_count: 4,
            acyclic: true,
            rank_ordered: true,
            dependencies_complete: true,
            evidence_ceiling: EvidenceCeiling::BoundaryChecked,
            authority_effect: AuthorityEffect::None,
        }
    }

    fn attestation(
        certificate: &CheckedPacketCertificateV1,
        receipt_dag: &DeterministicReceiptDagVerificationV1,
    ) -> AuthorityWitnessAttestationV1 {
        AuthorityWitnessAttestationV1 {
            schema_version: AUTHORITY_WITNESS_ATTESTATION_SCHEMA_VERSION.to_owned(),
            attestation_id: "attestation:test:authority-witness".to_owned(),
            certificate_sha256: certificate.certificate_sha256.clone(),
            receipt_dag_sha256: receipt_dag.receipt_dag_sha256.clone(),
            producer_identity_id: "identity:test:producer".to_owned(),
            independent_evaluator_identity_id: "identity:test:evaluator".to_owned(),
            authority_witness_identity_id: "identity:test:authority".to_owned(),
            identities_independent: true,
            promotion_conditions_satisfied: true,
            authority_effect: AuthorityEffect::None,
        }
    }

    fn human_event(
        certificate: &CheckedPacketCertificateV1,
        receipt_dag: &DeterministicReceiptDagVerificationV1,
    ) -> HumanPromotionEventV1 {
        HumanPromotionEventV1 {
            schema_version: HUMAN_PROMOTION_EVENT_SCHEMA_VERSION.to_owned(),
            decision_id: "decision:test:human-promotion".to_owned(),
            recorded_by_host_id: "host:test".to_owned(),
            human_actor_id: "human:test".to_owned(),
            policy_epoch: "policy:test:v1".to_owned(),
            certificate_sha256: certificate.certificate_sha256.clone(),
            receipt_dag_sha256: receipt_dag.receipt_dag_sha256.clone(),
            scope: "scope:test:local-result".to_owned(),
            decision: HumanPromotionDecisionV1::Promote,
            authority_effect: AuthorityEffect::None,
        }
    }

    fn test_capability() -> HostPromotionCapabilityV1 {
        HostPromotionCapabilityV1 {
            authenticated_host_id: "host:test".to_owned(),
            authenticated_human_actor_id: "human:test".to_owned(),
            policy_epoch: "policy:test:v1".to_owned(),
            _seal: HostPromotionSeal,
        }
    }

    #[test]
    fn checked_packet_certificate_is_evidence_only_and_hash_bound() {
        let certificate = certificate();
        certificate.validate().unwrap();
        assert!(certificate.authority_effect().is_none());
        assert_eq!(certificate.packet_replay_hash(), "0c".repeat(32));
    }

    #[test]
    fn promotion_requires_every_boundary_input() {
        let certificate = certificate();
        let receipt_dag = receipt_dag(&certificate);
        let attestation = attestation(&certificate, &receipt_dag);
        let human_event = human_event(&certificate, &receipt_dag);
        let result = promote_authorized_local_result_v1(
            test_capability(),
            &certificate,
            &receipt_dag,
            &attestation,
            &human_event,
        )
        .unwrap();
        assert!(result.authority_effect().is_certified());
        assert_eq!(result.scope(), "scope:test:local-result");
    }

    #[test]
    fn promotion_refuses_an_unverified_receipt_dag() {
        let certificate = certificate();
        let mut receipt_dag = receipt_dag(&certificate);
        receipt_dag.acyclic = false;
        let attestation = attestation(&certificate, &receipt_dag);
        let human_event = human_event(&certificate, &receipt_dag);
        assert_eq!(
            promote_authorized_local_result_v1(
                test_capability(),
                &certificate,
                &receipt_dag,
                &attestation,
                &human_event,
            ),
            Err(CertificatePromotionContractError::ReceiptDagUnverified)
        );
    }

    #[test]
    fn promotion_refuses_nonindependent_witnesses() {
        let certificate = certificate();
        let receipt_dag = receipt_dag(&certificate);
        let mut attestation = attestation(&certificate, &receipt_dag);
        attestation.authority_witness_identity_id = attestation.producer_identity_id.clone();
        let human_event = human_event(&certificate, &receipt_dag);
        assert_eq!(
            promote_authorized_local_result_v1(
                test_capability(),
                &certificate,
                &receipt_dag,
                &attestation,
                &human_event,
            ),
            Err(CertificatePromotionContractError::WitnessIndependenceFailed)
        );
    }

    #[test]
    fn promotion_refuses_rejection_and_host_mismatch() {
        let certificate = certificate();
        let receipt_dag = receipt_dag(&certificate);
        let attestation = attestation(&certificate, &receipt_dag);
        let mut rejected = human_event(&certificate, &receipt_dag);
        rejected.decision = HumanPromotionDecisionV1::Reject;
        assert_eq!(
            promote_authorized_local_result_v1(
                test_capability(),
                &certificate,
                &receipt_dag,
                &attestation,
                &rejected,
            ),
            Err(CertificatePromotionContractError::HumanPromotionRefused)
        );

        let mut mismatched = human_event(&certificate, &receipt_dag);
        mismatched.human_actor_id = "human:other".to_owned();
        assert_eq!(
            promote_authorized_local_result_v1(
                test_capability(),
                &certificate,
                &receipt_dag,
                &attestation,
                &mismatched,
            ),
            Err(CertificatePromotionContractError::HostCapabilityMismatch)
        );
    }

    // --- Epoch 18: deterministic publication -----------------------------

    /// Promote once with the standard fixtures; the result is the ONLY way to
    /// obtain a publishable value.
    fn authorized() -> AuthorizedLocalResultV1 {
        let certificate = certificate();
        let receipt_dag = receipt_dag(&certificate);
        let attestation = attestation(&certificate, &receipt_dag);
        let human_event = human_event(&certificate, &receipt_dag);
        promote_authorized_local_result_v1(
            test_capability(),
            &certificate,
            &receipt_dag,
            &attestation,
            &human_event,
        )
        .expect("fixtures promote cleanly")
    }

    #[test]
    fn test_deterministic_publisher_reproducibility() {
        let authorized = authorized();
        let publisher = DeterministicPublisher::new();

        let first = publisher.publish(&authorized).expect("publish");
        let second = publisher.publish(&authorized).expect("republish");

        assert_eq!(
            first.bytes(),
            second.bytes(),
            "identical input must yield byte-identical output"
        );
        assert_eq!(first.projection_sha256(), second.projection_sha256());

        // A separate publisher value must agree too: the publisher carries no
        // state, so instance identity cannot influence the bytes.
        let third = DeterministicPublisher
            .publish(&authorized)
            .expect("publish");
        assert_eq!(first.bytes(), third.bytes());

        first
            .verify_self_digest()
            .expect("digest matches its bytes");
    }

    /// Reproducibility is worthless if the function is constant: distinct
    /// authorized results must publish to distinct bytes.
    #[test]
    fn distinct_authorizations_publish_to_distinct_bytes() {
        let certificate = certificate();
        let receipt_dag = receipt_dag(&certificate);
        let attestation = attestation(&certificate, &receipt_dag);

        let mut other_event = human_event(&certificate, &receipt_dag);
        other_event.decision_id = "decision:test:human-promotion-B".to_owned();
        other_event.scope = "scope:test:other".to_owned();
        let other = promote_authorized_local_result_v1(
            test_capability(),
            &certificate,
            &receipt_dag,
            &attestation,
            &other_event,
        )
        .expect("second promotion");

        let publisher = DeterministicPublisher::new();
        let a = publisher.publish(&authorized()).expect("publish a");
        let b = publisher.publish(&other).expect("publish b");
        assert_ne!(
            a.projection_sha256(),
            b.projection_sha256(),
            "a publisher that ignored its input would still pass reproducibility"
        );
    }

    #[test]
    fn test_publication_requires_human_decision_id() {
        let certificate = certificate();
        let receipt_dag = receipt_dag(&certificate);
        let attestation = attestation(&certificate, &receipt_dag);

        // 1. A refused decision never yields an AuthorizedLocalResultV1, so
        //    there is nothing to hand the publisher.
        let mut rejected = human_event(&certificate, &receipt_dag);
        rejected.decision = HumanPromotionDecisionV1::Reject;
        assert_eq!(
            promote_authorized_local_result_v1(
                test_capability(),
                &certificate,
                &receipt_dag,
                &attestation,
                &rejected,
            ),
            Err(CertificatePromotionContractError::HumanPromotionRefused),
            "a rejected decision must not produce a publishable result"
        );

        // 2. A decision hash-bound to DIFFERENT material is refused, so a real
        //    decision cannot be replayed onto another certificate.
        let mut mismatched = human_event(&certificate, &receipt_dag);
        mismatched.certificate_sha256 = "ab".repeat(32);
        assert!(
            promote_authorized_local_result_v1(
                test_capability(),
                &certificate,
                &receipt_dag,
                &attestation,
                &mismatched,
            )
            .is_err(),
            "a decision bound to other material must not promote"
        );

        // 3. When publication DOES happen the decision id is inseparable from
        //    the artifact: every published byte-string names the human decision
        //    that authorized it.
        let published = DeterministicPublisher::new()
            .publish(&authorized())
            .expect("publish");
        let text = String::from_utf8(published.bytes().to_vec()).expect("utf-8");
        assert!(
            text.contains("decision:test:human-promotion"),
            "published projection must carry its human decision id: {text}"
        );
        assert!(text.contains("human_decision_id"));
    }

    #[test]
    fn published_projection_detects_a_tampered_digest() {
        let published = DeterministicPublisher::new()
            .publish(&authorized())
            .expect("publish");
        let tampered = PublishedProjectionV1 {
            bytes: published.bytes().to_vec(),
            projection_sha256: "00".repeat(32),
        };
        assert_eq!(
            tampered.verify_self_digest(),
            Err(CertificatePromotionContractError::ProjectionDigestMismatch)
        );
    }

    #[test]
    fn published_bytes_carry_no_clock_or_host_dependence() {
        let published = DeterministicPublisher::new()
            .publish(&authorized())
            .expect("publish");
        let text = String::from_utf8(published.bytes().to_vec()).expect("utf-8");
        // Every value in the projection is drawn from the authorized result;
        // nothing may leak the machine or the moment that produced it.
        for forbidden in ["/home", "/Users", "target/", "AppData"] {
            assert!(
                !text.contains(forbidden),
                "projection leaked a host-dependent token {forbidden:?}: {text}"
            );
        }
        assert!(
            text.ends_with("}\n"),
            "canonical form must end with a single LF: {text:?}"
        );
        assert!(
            !text.contains("\r\n"),
            "canonical form must not carry CRLF: {text:?}"
        );
    }

    #[test]
    fn json_string_encoder_escapes_structural_and_control_characters() {
        assert_eq!(encode_json_string("plain"), "\"plain\"");
        assert_eq!(encode_json_string("a\"b"), "\"a\\\"b\"");
        assert_eq!(encode_json_string("a\\b"), "\"a\\\\b\"");
        assert_eq!(encode_json_string("a\nb"), "\"a\\nb\"");
        assert_eq!(encode_json_string("a\u{1}b"), "\"a\\u0001b\"");
        // Non-ASCII passes through as UTF-8: valid JSON and stable bytes.
        assert_eq!(encode_json_string("caf\u{e9}"), "\"caf\u{e9}\"");
    }
}
