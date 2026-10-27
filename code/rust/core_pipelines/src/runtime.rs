//! --- Math Contract: a bounded proposal/evaluation metabolism totalizes every admitted problem.
//!
//! This module is the pure entry contract for Engine. It retains only a
//! domain-separated prompt hash, keeps producer and evaluator identities
//! distinct, makes every upper-role handoff typed, and cannot mint authority.
//! CODA-FDA completion here is evidence for a later sealed-witness and human
//! promotion process; this runtime therefore emits only the canonical
//! [`core_types::authority::AuthorityEffect::None`] effect.

pub use core_types::authority::AuthorityEffect;
use serde::de::Error as _;
use serde::{Deserialize, Deserializer, Serialize};
use std::collections::BTreeSet;

/// A domain-separated BLAKE3 digest.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct ContentHash([u8; 32]);

impl ContentHash {
    pub fn domain_separated(domain: &[u8], value: &[u8]) -> Self {
        let material = [domain, b"\0".as_slice(), value].concat();
        Self(*blake3::hash(&material).as_bytes())
    }

    pub const fn bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

/// Hash-only identity of the submitted prompt. Raw prompt text is never retained.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct PromptIdentity(ContentHash);

impl PromptIdentity {
    pub fn from_prompt(prompt: &str) -> Option<Self> {
        (!prompt.trim().is_empty()).then(|| {
            Self(ContentHash::domain_separated(
                b"core.prompt-identity.v1",
                prompt.as_bytes(),
            ))
        })
    }

    pub const fn hash(&self) -> ContentHash {
        self.0
    }
}

macro_rules! validated_string {
    ($name:ident) => {
        #[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
        pub struct $name(String);

        impl $name {
            pub fn new(value: impl Into<String>) -> Option<Self> {
                let value = value.into();
                (!value.trim().is_empty()).then_some(Self(value))
            }

            pub fn as_str(&self) -> &str {
                &self.0
            }
        }

        impl<'de> Deserialize<'de> for $name {
            fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
            where
                D: Deserializer<'de>,
            {
                let value = String::deserialize(deserializer)?;
                Self::new(value).ok_or_else(|| {
                    D::Error::custom(concat!(stringify!($name), " must be nonempty"))
                })
            }
        }
    };
}

validated_string!(RoleIdentity);
validated_string!(ContextRef);
validated_string!(OperatorId);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoreBudgets {
    pub max_repairs: u16,
    pub max_operator_calls: u16,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RequestedEffect {
    None,
    Evidence,
    Artifact,
    StateChange,
    Authority,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CoreTerminal {
    Completed,
    Refused,
    OpenResidual,
    NoPacket,
    BudgetExhausted,
    InfrastructureFailure,
    Halted,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CoreRole {
    Admission,
    Producer,
    IndependentEvaluator,
    Gtfoc,
    Dda,
    Gtfda,
    Gtmur,
    Gtor,
    Gttc,
    Gtta,
    #[serde(rename = "GtlaGovernance")]
    CodaGtlaGovernance,
    Q,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RegistryStatus {
    Discovered,
    SchemaValid,
    Registered,
    Disabled,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExecutionStatus {
    Unavailable,
    Available,
    Contained,
    Enabled,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvidenceStatus {
    Untested,
    EvaluationRecorded,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AuthorityStatus {
    None,
    Refused,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EffectStatus {
    NotRequested,
    NotApplied,
    Requested,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RawProblemPacket")]
pub struct ProblemPacket {
    prompt_identity: PromptIdentity,
    carrier: String,
    regime: String,
    assumptions: Vec<String>,
    constraints: Vec<String>,
    observer: String,
    budgets: CoreBudgets,
    context_refs: Vec<ContextRef>,
    requested_effect: RequestedEffect,
    permitted_operators: Vec<OperatorId>,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
struct RawProblemPacket {
    prompt_identity: PromptIdentity,
    carrier: String,
    regime: String,
    assumptions: Vec<String>,
    constraints: Vec<String>,
    observer: String,
    budgets: CoreBudgets,
    context_refs: Vec<ContextRef>,
    requested_effect: RequestedEffect,
    permitted_operators: Vec<OperatorId>,
}

impl TryFrom<RawProblemPacket> for ProblemPacket {
    type Error = String;

    fn try_from(raw: RawProblemPacket) -> Result<Self, Self::Error> {
        if raw.carrier.trim().is_empty()
            || raw.regime.trim().is_empty()
            || raw.observer.trim().is_empty()
            || raw.permitted_operators.is_empty()
        {
            return Err(
                "problem packet is missing a carrier, regime, observer, or permitted operator"
                    .to_owned(),
            );
        }
        Ok(Self {
            prompt_identity: raw.prompt_identity,
            carrier: raw.carrier,
            regime: raw.regime,
            assumptions: raw.assumptions,
            constraints: raw.constraints,
            observer: raw.observer,
            budgets: raw.budgets,
            context_refs: raw.context_refs,
            requested_effect: raw.requested_effect,
            permitted_operators: raw.permitted_operators,
        })
    }
}

pub struct ProblemPacketSpec<'a> {
    pub prompt: &'a str,
    pub carrier: String,
    pub regime: String,
    pub assumptions: Vec<String>,
    pub constraints: Vec<String>,
    pub observer: String,
    pub budgets: CoreBudgets,
    pub context_refs: Vec<ContextRef>,
    pub requested_effect: RequestedEffect,
    pub permitted_operators: Vec<OperatorId>,
}

impl ProblemPacket {
    pub fn from_prompt(spec: ProblemPacketSpec<'_>) -> Option<Self> {
        PromptIdentity::from_prompt(spec.prompt).map(|prompt_identity| Self {
            prompt_identity,
            carrier: spec.carrier,
            regime: spec.regime,
            assumptions: spec.assumptions,
            constraints: spec.constraints,
            observer: spec.observer,
            budgets: spec.budgets,
            context_refs: spec.context_refs,
            requested_effect: spec.requested_effect,
            permitted_operators: spec.permitted_operators,
        })
    }

    pub const fn prompt_identity(&self) -> PromptIdentity {
        self.prompt_identity
    }

    pub fn carrier(&self) -> &str {
        &self.carrier
    }

    pub fn regime(&self) -> &str {
        &self.regime
    }

    pub fn assumptions(&self) -> &[String] {
        &self.assumptions
    }

    pub fn constraints(&self) -> &[String] {
        &self.constraints
    }

    pub fn observer(&self) -> &str {
        &self.observer
    }

    pub const fn budgets(&self) -> CoreBudgets {
        self.budgets
    }

    pub fn context_refs(&self) -> &[ContextRef] {
        &self.context_refs
    }

    pub const fn requested_effect(&self) -> RequestedEffect {
        self.requested_effect
    }

    pub fn permitted_operators(&self) -> &[OperatorId] {
        &self.permitted_operators
    }

    fn is_admissible(&self) -> bool {
        !self.carrier.trim().is_empty()
            && !self.regime.trim().is_empty()
            && !self.observer.trim().is_empty()
            && !self.permitted_operators.is_empty()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SeparationMode {
    ContextSeparated,
    ProviderSeparated,
    ProcessSeparated,
    HoldoutSeparated,
    PromptSeparated,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum IndependenceError {
    #[error("producer and evaluator must have distinct identities")]
    SameIdentity,
    #[error("at least one exact evaluator-separation mode is required")]
    MissingSeparationMode,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RawSeparationClaim")]
pub struct SeparationClaim {
    producer: RoleIdentity,
    evaluator: RoleIdentity,
    modes: BTreeSet<SeparationMode>,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
struct RawSeparationClaim {
    producer: RoleIdentity,
    evaluator: RoleIdentity,
    modes: BTreeSet<SeparationMode>,
}

impl TryFrom<RawSeparationClaim> for SeparationClaim {
    type Error = IndependenceError;

    fn try_from(raw: RawSeparationClaim) -> Result<Self, Self::Error> {
        Self::try_new(raw.producer, raw.evaluator, raw.modes)
    }
}

impl SeparationClaim {
    pub fn try_new(
        producer: RoleIdentity,
        evaluator: RoleIdentity,
        modes: BTreeSet<SeparationMode>,
    ) -> Result<Self, IndependenceError> {
        if producer == evaluator {
            return Err(IndependenceError::SameIdentity);
        }
        if modes.is_empty() {
            return Err(IndependenceError::MissingSeparationMode);
        }
        Ok(Self {
            producer,
            evaluator,
            modes,
        })
    }

    pub fn producer(&self) -> &RoleIdentity {
        &self.producer
    }

    pub fn evaluator(&self) -> &RoleIdentity {
        &self.evaluator
    }

    pub fn modes(&self) -> &BTreeSet<SeparationMode> {
        &self.modes
    }

    pub fn has_mode(&self, mode: SeparationMode) -> bool {
        self.modes.contains(&mode)
    }

    pub fn is_merely_prompt_separated(&self) -> bool {
        self.modes.len() == 1 && self.has_mode(SeparationMode::PromptSeparated)
    }
}

/// Host-attested independence. The pure runtime has no constructor for this
/// receipt; distinct strings and self-declared modes produce only a
/// SeparationClaim.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct IndependenceReceipt {
    claim: SeparationClaim,
    host_attestation_hash: ContentHash,
}

impl IndependenceReceipt {
    pub fn claim(&self) -> &SeparationClaim {
        &self.claim
    }

    pub const fn host_attestation_hash(&self) -> ContentHash {
        self.host_attestation_hash
    }
}

impl<'de> Deserialize<'de> for IndependenceReceipt {
    fn deserialize<D>(_deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Err(D::Error::custom(
            "host independence receipts cannot be reconstructed from wire data",
        ))
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RawResidual")]
pub struct Residual {
    pub id: ContentHash,
    pub origin: CoreRole,
    pub summary: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
struct RawResidual {
    id: ContentHash,
    origin: CoreRole,
    summary: String,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ResidualIntegrityError {
    #[error("residual summary must be nonempty")]
    EmptySummary,
    #[error("residual id does not bind its origin and summary")]
    IdentityMismatch,
}

impl Residual {
    pub fn new(origin: CoreRole, summary: impl Into<String>) -> Self {
        let summary = summary.into();
        let material = format!("{origin:?}\0{summary}");
        Self {
            id: ContentHash::domain_separated(b"core.residual.v1", material.as_bytes()),
            origin,
            summary,
        }
    }

    fn validate(&self) -> Result<(), ResidualIntegrityError> {
        if self.summary.trim().is_empty() {
            return Err(ResidualIntegrityError::EmptySummary);
        }
        let material = format!("{:?}\0{}", self.origin, self.summary);
        if self.id != ContentHash::domain_separated(b"core.residual.v1", material.as_bytes()) {
            return Err(ResidualIntegrityError::IdentityMismatch);
        }
        Ok(())
    }
}

impl TryFrom<RawResidual> for Residual {
    type Error = ResidualIntegrityError;

    fn try_from(raw: RawResidual) -> Result<Self, Self::Error> {
        let residual = Self {
            id: raw.id,
            origin: raw.origin,
            summary: raw.summary,
        };
        residual.validate()?;
        Ok(residual)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum GtmurRouteOutcome {
    TransportRequired { residual: Residual },
    LossCertificateRequired { residual: Residual },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum GtorRouteOutcome {
    ComparisonRequired { residual: Residual },
    CompletionRequired { residual: Residual },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum GttcRouteOutcome {
    FiniteShadowRequired { residual: Residual },
    NonAbsorption { residual: Residual },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum GttaRouteOutcome {
    TypedResidual {
        residual: Residual,
        type_tag: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum QRouteOutcome {
    Quarantined {
        residual: Residual,
        next_probe: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RawRouteOutcome")]
pub enum RouteOutcome {
    Gtmur(GtmurRouteOutcome),
    Gtor(GtorRouteOutcome),
    Gttc(GttcRouteOutcome),
    Gtta(GttaRouteOutcome),
    Q(QRouteOutcome),
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
enum RawRouteOutcome {
    Gtmur(GtmurRouteOutcome),
    Gtor(GtorRouteOutcome),
    Gttc(GttcRouteOutcome),
    Gtta(GttaRouteOutcome),
    Q(QRouteOutcome),
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RouteIntegrityError {
    #[error("route residual origin {actual:?} does not match route role {expected:?}")]
    OriginMismatch {
        expected: CoreRole,
        actual: CoreRole,
    },
    #[error("CODA-A residual type tag must be nonempty")]
    EmptyTypeTag,
    #[error("Q next admissible probe must be nonempty")]
    EmptyNextProbe,
}

impl RouteOutcome {
    pub const fn role(&self) -> CoreRole {
        match self {
            Self::Gtmur(_) => CoreRole::Gtmur,
            Self::Gtor(_) => CoreRole::Gtor,
            Self::Gttc(_) => CoreRole::Gttc,
            Self::Gtta(_) => CoreRole::Gtta,
            Self::Q(_) => CoreRole::Q,
        }
    }

    pub fn residual(&self) -> &Residual {
        match self {
            Self::Gtmur(GtmurRouteOutcome::TransportRequired { residual })
            | Self::Gtmur(GtmurRouteOutcome::LossCertificateRequired { residual }) => residual,
            Self::Gtor(GtorRouteOutcome::ComparisonRequired { residual })
            | Self::Gtor(GtorRouteOutcome::CompletionRequired { residual }) => residual,
            Self::Gttc(GttcRouteOutcome::FiniteShadowRequired { residual })
            | Self::Gttc(GttcRouteOutcome::NonAbsorption { residual }) => residual,
            Self::Gtta(GttaRouteOutcome::TypedResidual { residual, .. }) => residual,
            Self::Q(QRouteOutcome::Quarantined { residual, .. }) => residual,
        }
    }

    fn validate(&self) -> Result<(), RouteIntegrityError> {
        let expected = self.role();
        let actual = self.residual().origin;
        if actual != expected {
            return Err(RouteIntegrityError::OriginMismatch { expected, actual });
        }
        match self {
            Self::Gtta(GttaRouteOutcome::TypedResidual { type_tag, .. })
                if type_tag.trim().is_empty() =>
            {
                Err(RouteIntegrityError::EmptyTypeTag)
            }
            Self::Q(QRouteOutcome::Quarantined { next_probe, .. })
                if next_probe.trim().is_empty() =>
            {
                Err(RouteIntegrityError::EmptyNextProbe)
            }
            _ => Ok(()),
        }
    }
}

impl TryFrom<RawRouteOutcome> for RouteOutcome {
    type Error = RouteIntegrityError;

    fn try_from(raw: RawRouteOutcome) -> Result<Self, Self::Error> {
        let outcome = match raw {
            RawRouteOutcome::Gtmur(value) => Self::Gtmur(value),
            RawRouteOutcome::Gtor(value) => Self::Gtor(value),
            RawRouteOutcome::Gttc(value) => Self::Gttc(value),
            RawRouteOutcome::Gtta(value) => Self::Gtta(value),
            RawRouteOutcome::Q(value) => Self::Q(value),
        };
        outcome.validate()?;
        Ok(outcome)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProposalIntegrityState {
    ReferenceOnly,
    Committed,
    Rejected { reason: String },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RawProposal")]
pub struct Proposal {
    pub proposal_id: String,
    pub artifact_ref: String,
    artifact_hash: Option<ContentHash>,
    artifact_len: Option<u64>,
    artifact_binding_hash: Option<ContentHash>,
    integrity: ProposalIntegrityState,
    #[serde(skip)]
    artifact_bytes: Option<Vec<u8>>,
}

fn proposal_binding_hash(
    proposal_id: &str,
    artifact_ref: &str,
    artifact_hash: ContentHash,
    artifact_len: u64,
) -> ContentHash {
    let mut material = Vec::new();
    [proposal_id.as_bytes(), artifact_ref.as_bytes()]
        .into_iter()
        .for_each(|part| {
            material.extend_from_slice(&(part.len() as u64).to_le_bytes());
            material.extend_from_slice(part);
        });
    material.extend_from_slice(artifact_hash.bytes());
    material.extend_from_slice(&artifact_len.to_le_bytes());
    ContentHash::domain_separated(b"core.proposal-binding.v1", &material)
}

impl Proposal {
    /// Construct a reference-only proposal without claiming an artifact hash.
    pub fn new(proposal_id: impl Into<String>, artifact_ref: impl Into<String>) -> Self {
        Self {
            proposal_id: proposal_id.into(),
            artifact_ref: artifact_ref.into(),
            artifact_hash: None,
            artifact_len: None,
            artifact_binding_hash: None,
            integrity: ProposalIntegrityState::ReferenceOnly,
            artifact_bytes: None,
        }
    }

    /// Bind proposal identity, artifact reference, length, and exact artifact bytes.
    pub fn from_artifact(
        proposal_id: impl Into<String>,
        artifact_ref: impl Into<String>,
        artifact: impl AsRef<[u8]>,
    ) -> Self {
        let proposal_id = proposal_id.into();
        let artifact_ref = artifact_ref.into();
        let artifact = artifact.as_ref().to_vec();
        let artifact_hash = ContentHash::domain_separated(b"core.proposal-artifact.v1", &artifact);
        let artifact_len = artifact.len() as u64;
        let artifact_binding_hash =
            proposal_binding_hash(&proposal_id, &artifact_ref, artifact_hash, artifact_len);
        Self {
            proposal_id,
            artifact_ref,
            artifact_hash: Some(artifact_hash),
            artifact_len: Some(artifact_len),
            artifact_binding_hash: Some(artifact_binding_hash),
            integrity: ProposalIntegrityState::Committed,
            artifact_bytes: Some(artifact),
        }
    }

    pub const fn artifact_hash(&self) -> Option<ContentHash> {
        self.artifact_hash
    }

    pub const fn artifact_len(&self) -> Option<u64> {
        self.artifact_len
    }

    pub const fn artifact_binding_hash(&self) -> Option<ContentHash> {
        self.artifact_binding_hash
    }

    pub const fn integrity(&self) -> &ProposalIntegrityState {
        &self.integrity
    }

    pub fn attached_artifact(&self) -> Option<&[u8]> {
        self.artifact_bytes.as_deref()
    }

    pub fn is_artifact_bound(&self) -> bool {
        matches!(&self.integrity, ProposalIntegrityState::Committed)
            && self.executable_integrity_error().is_none()
    }

    pub fn verify_artifact(&self, artifact: &[u8]) -> bool {
        if !matches!(&self.integrity, ProposalIntegrityState::Committed) {
            return false;
        }
        let Some((expected_hash, expected_len, expected_binding)) = self
            .artifact_hash
            .zip(self.artifact_len)
            .zip(self.artifact_binding_hash)
            .map(|((hash, len), binding)| (hash, len, binding))
        else {
            return false;
        };
        let actual_hash = ContentHash::domain_separated(b"core.proposal-artifact.v1", artifact);
        expected_len == artifact.len() as u64
            && expected_hash == actual_hash
            && expected_binding
                == proposal_binding_hash(
                    &self.proposal_id,
                    &self.artifact_ref,
                    expected_hash,
                    expected_len,
                )
    }

    fn executable_integrity_error(&self) -> Option<ProposalIntegrityError> {
        if self.proposal_id.trim().is_empty() {
            return Some(ProposalIntegrityError::EmptyProposalId);
        }
        if self.artifact_ref.trim().is_empty() {
            return Some(ProposalIntegrityError::EmptyArtifactRef);
        }
        match &self.integrity {
            ProposalIntegrityState::ReferenceOnly => (self.artifact_hash.is_some()
                || self.artifact_len.is_some()
                || self.artifact_binding_hash.is_some()
                || self.artifact_bytes.is_some())
            .then_some(ProposalIntegrityError::InconsistentCommitment),
            ProposalIntegrityState::Committed => {
                let Some((hash, len, binding)) = self
                    .artifact_hash
                    .zip(self.artifact_len)
                    .zip(self.artifact_binding_hash)
                    .map(|((hash, len), binding)| (hash, len, binding))
                else {
                    return Some(ProposalIntegrityError::InconsistentCommitment);
                };
                if binding
                    != proposal_binding_hash(&self.proposal_id, &self.artifact_ref, hash, len)
                {
                    return Some(ProposalIntegrityError::MetadataBindingMismatch);
                }
                self.artifact_bytes
                    .as_deref()
                    .filter(|bytes| !self.verify_artifact(bytes))
                    .map(|_| ProposalIntegrityError::ArtifactBytesMismatch)
            }
            ProposalIntegrityState::Rejected { reason } => {
                if reason.trim().is_empty() {
                    Some(ProposalIntegrityError::MissingRejectionReason)
                } else {
                    Some(ProposalIntegrityError::RejectedCommitment)
                }
            }
        }
    }

    fn wire_integrity_error(&self) -> Option<ProposalIntegrityError> {
        match &self.integrity {
            ProposalIntegrityState::Rejected { reason } if reason.trim().is_empty() => {
                Some(ProposalIntegrityError::MissingRejectionReason)
            }
            ProposalIntegrityState::Rejected { .. } if self.artifact_bytes.is_some() => {
                Some(ProposalIntegrityError::InconsistentCommitment)
            }
            ProposalIntegrityState::Rejected { .. } => None,
            _ => self.executable_integrity_error(),
        }
    }

    fn stored_artifact_is_valid(&self) -> bool {
        self.executable_integrity_error().is_none()
    }

    fn into_detached(mut self) -> Self {
        self.artifact_bytes = None;
        self
    }

    fn into_rejected_receipt(mut self, error: &ProposalIntegrityError) -> Self {
        self.integrity = ProposalIntegrityState::Rejected {
            reason: error.to_string(),
        };
        self.artifact_bytes = None;
        self
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
struct RawProposal {
    proposal_id: String,
    artifact_ref: String,
    artifact_hash: Option<ContentHash>,
    artifact_len: Option<u64>,
    artifact_binding_hash: Option<ContentHash>,
    integrity: ProposalIntegrityState,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ProposalIntegrityError {
    #[error("proposal id must be nonempty")]
    EmptyProposalId,
    #[error("artifact reference must be nonempty")]
    EmptyArtifactRef,
    #[error("artifact commitment fields are inconsistent")]
    InconsistentCommitment,
    #[error("artifact commitment does not bind the current proposal id and artifact reference")]
    MetadataBindingMismatch,
    #[error("attached artifact bytes do not match the declared commitment")]
    ArtifactBytesMismatch,
    #[error("rejected proposal evidence cannot execute")]
    RejectedCommitment,
    #[error("rejected proposal evidence must retain a reason")]
    MissingRejectionReason,
}

impl TryFrom<RawProposal> for Proposal {
    type Error = ProposalIntegrityError;

    fn try_from(raw: RawProposal) -> Result<Self, Self::Error> {
        let proposal = Self {
            proposal_id: raw.proposal_id,
            artifact_ref: raw.artifact_ref,
            artifact_hash: raw.artifact_hash,
            artifact_len: raw.artifact_len,
            artifact_binding_hash: raw.artifact_binding_hash,
            integrity: raw.integrity,
            artifact_bytes: None,
        };
        if let Some(error) = proposal.wire_integrity_error() {
            return Err(error);
        }
        Ok(proposal)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProposalStatus {
    Proposed(Proposal),
    Refused(String),
    NoPacket(String),
    InfrastructureFailure(String),
    Halted(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvaluationStatus {
    Accepted,
    Repair { residual: Residual },
    Refused(String),
    NoPacket(String),
    Route(RouteOutcome),
    InfrastructureFailure(String),
    Halted(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RawEvaluation")]
pub struct Evaluation {
    pub evaluation_ref: String,
    pub status: EvaluationStatus,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
struct RawEvaluation {
    evaluation_ref: String,
    status: EvaluationStatus,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum EvaluationIntegrityError {
    #[error("evaluation reference must be nonempty")]
    EmptyReference,
    #[error("evaluation terminal reason must be nonempty")]
    EmptyReason,
    #[error("evaluation residual is invalid: {0}")]
    InvalidResidual(String),
    #[error("evaluation route is invalid: {0}")]
    InvalidRoute(String),
}

impl Evaluation {
    pub fn new(evaluation_ref: impl Into<String>, status: EvaluationStatus) -> Self {
        Self {
            evaluation_ref: evaluation_ref.into(),
            status,
        }
    }

    fn validate(&self) -> Result<(), EvaluationIntegrityError> {
        if self.evaluation_ref.trim().is_empty() {
            return Err(EvaluationIntegrityError::EmptyReference);
        }
        match &self.status {
            EvaluationStatus::Accepted => Ok(()),
            EvaluationStatus::Repair { residual } => residual
                .validate()
                .map_err(|error| EvaluationIntegrityError::InvalidResidual(error.to_string())),
            EvaluationStatus::Route(outcome) => outcome
                .validate()
                .map_err(|error| EvaluationIntegrityError::InvalidRoute(error.to_string())),
            EvaluationStatus::Refused(reason)
            | EvaluationStatus::NoPacket(reason)
            | EvaluationStatus::InfrastructureFailure(reason)
            | EvaluationStatus::Halted(reason) => {
                if reason.trim().is_empty() {
                    Err(EvaluationIntegrityError::EmptyReason)
                } else {
                    Ok(())
                }
            }
        }
    }

    fn rejected_receipt(error: &EvaluationIntegrityError) -> Self {
        Self::new(
            "core.runtime.rejected-evaluation.v1",
            EvaluationStatus::Refused(format!("malformed evaluator output: {error}")),
        )
    }
}

impl TryFrom<RawEvaluation> for Evaluation {
    type Error = EvaluationIntegrityError;

    fn try_from(raw: RawEvaluation) -> Result<Self, Self::Error> {
        let evaluation = Self::new(raw.evaluation_ref, raw.status);
        evaluation.validate()?;
        Ok(evaluation)
    }
}

/// Proposal authority. Implementations receive no mutable runtime state.
pub trait Producer {
    fn identity(&self) -> RoleIdentity;

    fn propose(
        &self,
        packet: &ProblemPacket,
        repair_round: u16,
        prior_evaluation: Option<&Evaluation>,
    ) -> ProposalStatus;
}

/// Oppositional evaluation authority, separate from the producer identity.
pub trait IndependentEvaluator {
    fn identity(&self) -> RoleIdentity;

    fn separation_modes(&self) -> BTreeSet<SeparationMode>;

    fn evaluate(&self, packet: &ProblemPacket, proposal: &Proposal) -> Evaluation;
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AttemptReceipt {
    pub repair_round: u16,
    pub proposal: Proposal,
    pub evaluation: Option<Evaluation>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceBundle {
    pub evaluation_refs: Vec<String>,
    pub residual_ids: Vec<ContentHash>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TraceStage {
    Proposed,
    Evaluated,
    Routed,
    Recorded,
    Terminalized,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TraceEvent {
    pub sequence: u32,
    pub role: CoreRole,
    pub stage: TraceStage,
    pub reference: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EffectReceipt {
    pub effect: RequestedEffect,
    pub status: EffectStatus,
    pub receipt_ref: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RawOmegaResult")]
pub struct CoreResult {
    pub prompt_identity: Option<PromptIdentity>,
    pub terminal: CoreTerminal,
    pub terminal_role: CoreRole,
    pub registry_status: RegistryStatus,
    pub execution_status: ExecutionStatus,
    pub evidence_status: EvidenceStatus,
    pub authority_status: AuthorityStatus,
    pub authority_effect: AuthorityEffect,
    pub effect_status: EffectStatus,
    pub separation_claim: Option<SeparationClaim>,
    /// Reserved for a future host-authenticated receipt; never self-issued by this core.
    pub independence_receipt: Option<IndependenceReceipt>,
    pub attempts: Vec<AttemptReceipt>,
    pub artifact_refs: Vec<String>,
    pub evidence_bundle: EvidenceBundle,
    pub trace: Vec<TraceEvent>,
    pub effect_receipt: Option<EffectReceipt>,
    pub route_outcome: Option<RouteOutcome>,
    pub residuals: Vec<Residual>,
    pub next_admissible_probe: Option<String>,
    pub reason: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
struct RawOmegaResult {
    prompt_identity: Option<PromptIdentity>,
    terminal: CoreTerminal,
    terminal_role: CoreRole,
    registry_status: RegistryStatus,
    execution_status: ExecutionStatus,
    evidence_status: EvidenceStatus,
    authority_status: AuthorityStatus,
    authority_effect: AuthorityEffect,
    effect_status: EffectStatus,
    separation_claim: Option<SeparationClaim>,
    independence_receipt: Option<IndependenceReceipt>,
    attempts: Vec<AttemptReceipt>,
    artifact_refs: Vec<String>,
    evidence_bundle: EvidenceBundle,
    trace: Vec<TraceEvent>,
    effect_receipt: Option<EffectReceipt>,
    route_outcome: Option<RouteOutcome>,
    residuals: Vec<Residual>,
    next_admissible_probe: Option<String>,
    reason: String,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CoreResultIntegrityError {
    #[error("Completed is sealed and cannot be reconstructed without a CODA-FDA witness")]
    UnsealedCompletion,
    #[error("wire result claims a runtime state that this vertical slice cannot issue")]
    UnsupportedRuntimeClaim,
    #[error("wire result authority effect must remain None in this vertical slice")]
    UnsupportedAuthorityEffect,
    #[error("wire result execution status contradicts its terminal")]
    ExecutionStatusMismatch,
    #[error("wire result evidence status contradicts its attempts")]
    EvidenceStatusMismatch,
    #[error("wire result contains an invalid attempt: {0}")]
    InvalidAttempt(String),
    #[error("wire result evidence references do not match its attempts")]
    EvidenceReferenceMismatch,
    #[error("wire result residual ids do not match its residuals")]
    ResidualReferenceMismatch,
    #[error("wire result artifact references do not begin with its proposal references")]
    ArtifactReferenceMismatch,
    #[error("wire result trace is not contiguous or lacks terminalization")]
    InvalidTrace,
    #[error("wire result terminal and terminal role are inconsistent")]
    TerminalRoleMismatch,
    #[error("wire result route, terminal, residual, or next probe is inconsistent")]
    RouteMismatch,
    #[error("open residual terminal must retain at least one residual")]
    MissingOpenResidual,
    #[error("wire result reason must be nonempty")]
    EmptyReason,
    #[error("refused authority status cannot accompany this terminal")]
    AuthorityStatusMismatch,
}

impl CoreResult {
    pub fn final_proposal(&self) -> Option<&Proposal> {
        self.attempts
            .iter()
            .rev()
            .map(|attempt| &attempt.proposal)
            .find(|proposal| {
                !matches!(
                    proposal.integrity(),
                    ProposalIntegrityState::Rejected { .. }
                )
            })
    }

    fn validate_execution_and_evidence(&self) -> Result<(), CoreResultIntegrityError> {
        let expected_execution = match self.terminal {
            CoreTerminal::NoPacket
            | CoreTerminal::InfrastructureFailure
            | CoreTerminal::Halted => ExecutionStatus::Unavailable,
            _ => ExecutionStatus::Available,
        };
        if self.execution_status != expected_execution {
            return Err(CoreResultIntegrityError::ExecutionStatusMismatch);
        }
        let expected_evidence = if self.attempts.iter().any(|a| a.evaluation.is_some()) {
            EvidenceStatus::EvaluationRecorded
        } else {
            EvidenceStatus::Untested
        };
        if self.evidence_status != expected_evidence {
            return Err(CoreResultIntegrityError::EvidenceStatusMismatch);
        }
        Ok(())
    }

    fn validate_statuses(&self) -> Result<(), CoreResultIntegrityError> {
        if self.reason.trim().is_empty() {
            return Err(CoreResultIntegrityError::EmptyReason);
        }
        if self.terminal == CoreTerminal::Completed {
            return Err(CoreResultIntegrityError::UnsealedCompletion);
        }
        let unsupported = self.registry_status != RegistryStatus::Discovered
            || self.effect_status == EffectStatus::Requested
            || self.effect_receipt.is_some()
            || self.independence_receipt.is_some();
        if unsupported {
            return Err(CoreResultIntegrityError::UnsupportedRuntimeClaim);
        }
        if self.authority_effect != AuthorityEffect::None {
            return Err(CoreResultIntegrityError::UnsupportedAuthorityEffect);
        }
        self.validate_execution_and_evidence()
    }

    fn validate_attempts_and_references(&self) -> Result<(), CoreResultIntegrityError> {
        self.attempts.iter().try_for_each(|attempt| {
            attempt
                .proposal
                .wire_integrity_error()
                .map_or(Ok(()), |error| {
                    Err(CoreResultIntegrityError::InvalidAttempt(error.to_string()))
                })?;
            attempt.evaluation.as_ref().map_or(Ok(()), |evaluation| {
                evaluation
                    .validate()
                    .map_err(|error| CoreResultIntegrityError::InvalidAttempt(error.to_string()))
            })
        })?;
        let expected_evaluations = self
            .attempts
            .iter()
            .filter_map(|attempt| attempt.evaluation.as_ref())
            .map(|evaluation| evaluation.evaluation_ref.clone())
            .collect::<Vec<_>>();
        if self.evidence_bundle.evaluation_refs != expected_evaluations {
            return Err(CoreResultIntegrityError::EvidenceReferenceMismatch);
        }
        let expected_residuals = self.residuals.iter().map(|r| r.id).collect::<Vec<_>>();
        if self.evidence_bundle.residual_ids != expected_residuals {
            return Err(CoreResultIntegrityError::ResidualReferenceMismatch);
        }
        let expected_artifacts = self
            .attempts
            .iter()
            .map(|attempt| attempt.proposal.artifact_ref.clone())
            .filter(|reference| !reference.trim().is_empty())
            .collect::<Vec<_>>();
        if self.artifact_refs.len() < expected_artifacts.len()
            || self.artifact_refs[..expected_artifacts.len()] != expected_artifacts
        {
            return Err(CoreResultIntegrityError::ArtifactReferenceMismatch);
        }
        Ok(())
    }

    fn validate_trace_and_terminal(&self) -> Result<(), CoreResultIntegrityError> {
        let trace_valid = !self.trace.is_empty()
            && self
                .trace
                .iter()
                .enumerate()
                .all(|(index, event)| event.sequence == u32::try_from(index).unwrap_or(u32::MAX))
            && self
                .trace
                .iter()
                .any(|event| event.stage == TraceStage::Terminalized);
        if !trace_valid {
            return Err(CoreResultIntegrityError::InvalidTrace);
        }
        if !terminal_role_is_valid(self.terminal, self.terminal_role) {
            return Err(CoreResultIntegrityError::TerminalRoleMismatch);
        }
        if self.terminal == CoreTerminal::OpenResidual && self.residuals.is_empty() {
            return Err(CoreResultIntegrityError::MissingOpenResidual);
        }
        if self.authority_status == AuthorityStatus::Refused
            && !matches!(
                self.terminal,
                CoreTerminal::Refused
                    | CoreTerminal::InfrastructureFailure
                    | CoreTerminal::Halted
            )
        {
            return Err(CoreResultIntegrityError::AuthorityStatusMismatch);
        }
        Ok(())
    }

    fn is_route_role_consistent(&self, outcome: &RouteOutcome) -> bool {
        let route_is_current =
            self.terminal == CoreTerminal::OpenResidual && self.terminal_role == outcome.role();
        let route_was_host_overridden = matches!(
            self.terminal,
            CoreTerminal::InfrastructureFailure | CoreTerminal::Halted
        ) && self.terminal_role == CoreRole::CodaGtlaGovernance;
        (route_is_current || route_was_host_overridden)
            && self.residuals.contains(outcome.residual())
    }

    fn validate_route_outcome(&self) -> Result<(), CoreResultIntegrityError> {
        match &self.route_outcome {
            Some(outcome) => {
                outcome
                    .validate()
                    .map_err(|_| CoreResultIntegrityError::RouteMismatch)?;
                if !self.is_route_role_consistent(outcome) {
                    return Err(CoreResultIntegrityError::RouteMismatch);
                }
                let expected_probe = match outcome {
                    RouteOutcome::Q(QRouteOutcome::Quarantined { next_probe, .. }) => {
                        Some(next_probe.as_str())
                    }
                    _ => None,
                };
                if self.next_admissible_probe.as_deref() != expected_probe {
                    return Err(CoreResultIntegrityError::RouteMismatch);
                }
            }
            None if self.next_admissible_probe.is_some() => {
                return Err(CoreResultIntegrityError::RouteMismatch)
            }
            None => {}
        }
        Ok(())
    }

    fn validate(&self) -> Result<(), CoreResultIntegrityError> {
        self.validate_statuses()?;
        self.validate_attempts_and_references()?;
        self.validate_trace_and_terminal()?;
        self.validate_route_outcome()
    }
}

fn terminal_role_is_valid(terminal: CoreTerminal, role: CoreRole) -> bool {
    match terminal {
        CoreTerminal::Completed => false,
        CoreTerminal::Refused => matches!(
            role,
            CoreRole::Producer
                | CoreRole::IndependentEvaluator
                | CoreRole::Gtfda
                | CoreRole::CodaGtlaGovernance
        ),
        CoreTerminal::OpenResidual => matches!(
            role,
            CoreRole::Gtfoc
                | CoreRole::Gtmur
                | CoreRole::Gtor
                | CoreRole::Gttc
                | CoreRole::Gtta
                | CoreRole::Q
        ),
        CoreTerminal::NoPacket => matches!(
            role,
            CoreRole::Admission | CoreRole::Producer | CoreRole::IndependentEvaluator
        ),
        CoreTerminal::BudgetExhausted => role == CoreRole::Dda,
        CoreTerminal::InfrastructureFailure | CoreTerminal::Halted => matches!(
            role,
            CoreRole::Producer | CoreRole::IndependentEvaluator | CoreRole::CodaGtlaGovernance
        ),
    }
}

impl TryFrom<RawOmegaResult> for CoreResult {
    type Error = CoreResultIntegrityError;

    fn try_from(raw: RawOmegaResult) -> Result<Self, Self::Error> {
        let result = Self {
            prompt_identity: raw.prompt_identity,
            terminal: raw.terminal,
            terminal_role: raw.terminal_role,
            registry_status: raw.registry_status,
            execution_status: raw.execution_status,
            evidence_status: raw.evidence_status,
            authority_status: raw.authority_status,
            authority_effect: raw.authority_effect,
            effect_status: raw.effect_status,
            separation_claim: raw.separation_claim,
            independence_receipt: raw.independence_receipt,
            attempts: raw.attempts,
            artifact_refs: raw.artifact_refs,
            evidence_bundle: raw.evidence_bundle,
            trace: raw.trace,
            effect_receipt: raw.effect_receipt,
            route_outcome: raw.route_outcome,
            residuals: raw.residuals,
            next_admissible_probe: raw.next_admissible_probe,
            reason: raw.reason,
        };
        result.validate()?;
        Ok(result)
    }
}

/// Pure, bounded Core entrance.
///
/// The function totalizes missing/invalid packets, role refusals, open
/// residuals, budget exhaustion, infrastructure failures, and explicit halts.
/// It deliberately performs no persistence, external effect, or authority
/// promotion.
///
/// Totalization covers values returned by the role traits. Panic, nontermination,
/// and process containment remain obligations of the future host adapter.
pub fn run_omega(
    packet: Option<ProblemPacket>,
    producer: &dyn Producer,
    evaluator: &dyn IndependentEvaluator,
) -> CoreResult {
    let Some(packet) = packet else {
        return finish(
            None,
            RequestedEffect::None,
            CoreTerminal::NoPacket,
            CoreRole::Admission,
            None,
            Vec::new(),
            None,
            Vec::new(),
            "no problem packet was admitted".to_owned(),
        );
    };

    if !packet.is_admissible() {
        return finish(
            Some(packet.prompt_identity()),
            packet.requested_effect(),
            CoreTerminal::NoPacket,
            CoreRole::Admission,
            None,
            Vec::new(),
            None,
            Vec::new(),
            "problem packet is missing a carrier, regime, observer, or permitted operator"
                .to_owned(),
        );
    }

    if packet.requested_effect() == RequestedEffect::Authority {
        return finish(
            Some(packet.prompt_identity()),
            packet.requested_effect(),
            CoreTerminal::Refused,
            CoreRole::Gtfda,
            None,
            Vec::new(),
            None,
            Vec::new(),
            "authority requires a sealed witness and human promotion".to_owned(),
        );
    }

    let independence_receipt = match SeparationClaim::try_new(
        producer.identity(),
        evaluator.identity(),
        evaluator.separation_modes(),
    ) {
        Ok(receipt) => receipt,
        Err(error) => {
            return finish(
                Some(packet.prompt_identity()),
                packet.requested_effect(),
                CoreTerminal::Refused,
                CoreRole::CodaGtlaGovernance,
                None,
                Vec::new(),
                None,
                Vec::new(),
                format!("independent evaluator admission failed: {error}"),
            )
        }
    };

    metabolize(&packet, producer, evaluator, &independence_receipt)
}

fn unpack_proposal_status(status: ProposalStatus) -> Result<Proposal, (CoreTerminal, String)> {
    match status {
        ProposalStatus::Proposed(proposal) => Ok(proposal),
        ProposalStatus::Refused(reason) => Err((
            CoreTerminal::Refused,
            nonempty_reason(reason, "producer refused without a reason"),
        )),
        ProposalStatus::NoPacket(reason) => Err((
            CoreTerminal::NoPacket,
            nonempty_reason(reason, "producer returned no packet without a reason"),
        )),
        ProposalStatus::InfrastructureFailure(reason) => Err((
            CoreTerminal::InfrastructureFailure,
            nonempty_reason(reason, "producer infrastructure failed without a reason"),
        )),
        ProposalStatus::Halted(reason) => Err((
            CoreTerminal::Halted,
            nonempty_reason(reason, "producer halted without a reason"),
        )),
    }
}

fn finish_terminal_evaluation_status(
    packet: &ProblemPacket,
    independence_receipt: &SeparationClaim,
    attempts: Vec<AttemptReceipt>,
    mut residuals: Vec<Residual>,
    status: EvaluationStatus,
) -> CoreResult {
    let (terminal, role, route_outcome, reason) = match status {
        EvaluationStatus::Refused(reason) => {
            (CoreTerminal::Refused, CoreRole::IndependentEvaluator, None, reason)
        }
        EvaluationStatus::NoPacket(reason) => {
            (CoreTerminal::NoPacket, CoreRole::IndependentEvaluator, None, reason)
        }
        EvaluationStatus::Route(outcome) => {
            let terminal_role = outcome.role();
            residuals.push(outcome.residual().clone());
            (
                CoreTerminal::OpenResidual,
                terminal_role,
                Some(outcome),
                "proposal remains open at a typed upper-role boundary".to_owned(),
            )
        }
        EvaluationStatus::InfrastructureFailure(reason) => (
            CoreTerminal::InfrastructureFailure,
            CoreRole::IndependentEvaluator,
            None,
            reason,
        ),
        EvaluationStatus::Halted(reason) => {
            (CoreTerminal::Halted, CoreRole::IndependentEvaluator, None, reason)
        }
        _ => unreachable!(),
    };
    finish(
        Some(packet.prompt_identity()),
        packet.requested_effect(),
        terminal,
        role,
        Some(independence_receipt.clone()),
        attempts,
        route_outcome,
        residuals,
        reason,
    )
}

fn metabolize(
    packet: &ProblemPacket,
    producer: &dyn Producer,
    evaluator: &dyn IndependentEvaluator,
    independence_receipt: &SeparationClaim,
) -> CoreResult {
    let mut repair_round = 0_u16;
    let mut prior_evaluation = None;
    let mut attempts = Vec::new();
    let mut residuals = Vec::new();

    // This loop is bounded by both u16 repair and operator-call budgets. It is
    // deliberately iterative so the largest admitted budget cannot consume the call stack.
    loop {
        let required_calls = 2 * (u32::from(repair_round) + 1);
        if required_calls > u32::from(packet.budgets().max_operator_calls) {
            return finish(
                Some(packet.prompt_identity()),
                packet.requested_effect(),
                CoreTerminal::BudgetExhausted,
                CoreRole::Dda,
                Some(independence_receipt.clone()),
                attempts,
                None,
                residuals,
                "operator-call budget exhausted before the next bounded attempt".to_owned(),
            );
        }

        let proposal = match unpack_proposal_status(
            producer.propose(packet, repair_round, prior_evaluation.as_ref()),
        ) {
            Ok(proposal) => proposal,
            Err((terminal, reason)) => {
                return finish(
                    Some(packet.prompt_identity()),
                    packet.requested_effect(),
                    terminal,
                    CoreRole::Producer,
                    Some(independence_receipt.clone()),
                    attempts,
                    None,
                    residuals,
                    reason,
                )
            }
        };

        if let Some(error) = proposal.executable_integrity_error() {
            let reason = format!("proposal integrity refused before evaluation: {error}");
            residuals.push(Residual::new(CoreRole::CodaGtlaGovernance, reason.clone()));
            attempts.push(AttemptReceipt {
                repair_round,
                proposal: proposal.into_rejected_receipt(&error),
                evaluation: None,
            });
            return finish(
                Some(packet.prompt_identity()),
                packet.requested_effect(),
                CoreTerminal::Refused,
                CoreRole::CodaGtlaGovernance,
                Some(independence_receipt.clone()),
                attempts,
                None,
                residuals,
                reason,
            );
        }

        debug_assert!(proposal.stored_artifact_is_valid());
        let evaluation = evaluator.evaluate(packet, &proposal);
        if let Err(error) = evaluation.validate() {
            let reason = format!("evaluator output refused before routing: {error}");
            residuals.push(Residual::new(CoreRole::CodaGtlaGovernance, reason.clone()));
            attempts.push(AttemptReceipt {
                repair_round,
                proposal: proposal.into_detached(),
                evaluation: Some(Evaluation::rejected_receipt(&error)),
            });
            return finish(
                Some(packet.prompt_identity()),
                packet.requested_effect(),
                CoreTerminal::Refused,
                CoreRole::CodaGtlaGovernance,
                Some(independence_receipt.clone()),
                attempts,
                None,
                residuals,
                reason,
            );
        }

        let status = evaluation.status.clone();
        attempts.push(AttemptReceipt {
            repair_round,
            proposal: proposal.into_detached(),
            evaluation: Some(evaluation.clone()),
        });

        match status {
            EvaluationStatus::Accepted => {
                residuals.push(Residual::new(
                    CoreRole::Gtfda,
                    "a verified CODA-FDA descent packet, replay, and terminal seal are absent",
                ));
                return finish(
                    Some(packet.prompt_identity()),
                    packet.requested_effect(),
                    CoreTerminal::OpenResidual,
                    CoreRole::Gtfoc,
                    Some(independence_receipt.clone()),
                    attempts,
                    None,
                    residuals,
                    "CODA-FOC evaluator acceptance recorded without claiming CODA-FDA completion"
                        .to_owned(),
                );
            }
            EvaluationStatus::Repair { residual } => {
                residuals.push(residual);
                if repair_round < packet.budgets().max_repairs {
                    repair_round = repair_round.saturating_add(1);
                    prior_evaluation = Some(evaluation);
                    continue;
                }
                return finish(
                    Some(packet.prompt_identity()),
                    packet.requested_effect(),
                    CoreTerminal::BudgetExhausted,
                    CoreRole::Dda,
                    Some(independence_receipt.clone()),
                    attempts,
                    None,
                    residuals,
                    "repair budget exhausted with an explicit residual".to_owned(),
                );
            }
            other => {
                return finish_terminal_evaluation_status(
                    packet,
                    independence_receipt,
                    attempts,
                    residuals,
                    other,
                );
            }
        }
    }
}

fn nonempty_reason(reason: String, fallback: &str) -> String {
    if reason.trim().is_empty() {
        fallback.to_owned()
    } else {
        reason
    }
}

#[allow(clippy::too_many_arguments)]
fn finish(
    prompt_identity: Option<PromptIdentity>,
    requested_effect: RequestedEffect,
    terminal: CoreTerminal,
    terminal_role: CoreRole,
    independence_receipt: Option<SeparationClaim>,
    attempts: Vec<AttemptReceipt>,
    route_outcome: Option<RouteOutcome>,
    residuals: Vec<Residual>,
    reason: String,
) -> CoreResult {
    let effect_status = match (requested_effect, terminal) {
        (RequestedEffect::None, _) => EffectStatus::NotRequested,
        (_, CoreTerminal::Completed) => EffectStatus::Requested,
        _ => EffectStatus::NotApplied,
    };
    let authority_status = match requested_effect {
        RequestedEffect::Authority => AuthorityStatus::Refused,
        _ => AuthorityStatus::None,
    };
    // Admission does not prove schema validation or registry membership.
    let registry_status = RegistryStatus::Discovered;
    let execution_status = match terminal {
        CoreTerminal::NoPacket | CoreTerminal::InfrastructureFailure | CoreTerminal::Halted => {
            ExecutionStatus::Unavailable
        }
        _ => ExecutionStatus::Available,
    };
    let evidence_status = if attempts.iter().any(|attempt| attempt.evaluation.is_some()) {
        EvidenceStatus::EvaluationRecorded
    } else {
        EvidenceStatus::Untested
    };
    let artifact_refs = attempts
        .iter()
        .map(|attempt| attempt.proposal.artifact_ref.clone())
        .filter(|artifact_ref| !artifact_ref.trim().is_empty())
        .collect::<Vec<_>>();
    let evidence_bundle = EvidenceBundle {
        evaluation_refs: attempts
            .iter()
            .filter_map(|attempt| attempt.evaluation.as_ref())
            .map(|evaluation| evaluation.evaluation_ref.clone())
            .collect(),
        residual_ids: residuals.iter().map(|residual| residual.id).collect(),
    };
    let attempt_trace = attempts
        .iter()
        .flat_map(|attempt| {
            let proposal_reference = (!attempt.proposal.artifact_ref.trim().is_empty())
                .then(|| attempt.proposal.artifact_ref.clone());
            std::iter::once((
                CoreRole::Producer,
                TraceStage::Proposed,
                proposal_reference,
            ))
            .chain(attempt.evaluation.as_ref().map(|evaluation| {
                (
                    CoreRole::IndependentEvaluator,
                    TraceStage::Evaluated,
                    Some(evaluation.evaluation_ref.clone()),
                )
            }))
        })
        .enumerate()
        .map(|(index, (role, stage, reference))| TraceEvent {
            sequence: u32::try_from(index).unwrap_or(u32::MAX),
            role,
            stage,
            reference,
        })
        .collect::<Vec<_>>();
    let route_trace = route_outcome.as_ref().map(|outcome| TraceEvent {
        sequence: u32::try_from(attempt_trace.len()).unwrap_or(u32::MAX),
        role: outcome.role(),
        stage: TraceStage::Routed,
        reference: Some(outcome.residual().summary.clone()),
    });
    let terminal_sequence =
        u32::try_from(attempt_trace.len()).unwrap_or(u32::MAX) + u32::from(route_trace.is_some());
    let trace = attempt_trace
        .into_iter()
        .chain(route_trace)
        .chain(std::iter::once(TraceEvent {
            sequence: terminal_sequence,
            role: terminal_role,
            stage: TraceStage::Terminalized,
            reference: Some(reason.clone()),
        }))
        .collect();
    let next_admissible_probe = route_outcome.as_ref().and_then(|outcome| match outcome {
        RouteOutcome::Q(QRouteOutcome::Quarantined { next_probe, .. }) => Some(next_probe.clone()),
        _ => None,
    });

    CoreResult {
        prompt_identity,
        terminal,
        terminal_role,
        registry_status,
        execution_status,
        evidence_status,
        authority_status,
        authority_effect: AuthorityEffect::None,
        effect_status,
        separation_claim: independence_receipt,
        independence_receipt: None,
        attempts,
        artifact_refs,
        evidence_bundle,
        trace,
        effect_receipt: None,
        route_outcome,
        residuals,
        next_admissible_probe,
        reason,
    }
}

// Origin: engine/crates_rs/core_pipelines/src/runtime.rs
// Claim: urn:core:crates_rs:core-pipelines:runtime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod contract_negative_tests {
    use super::*;
    use std::collections::BTreeSet;

    fn identity(value: &str) -> RoleIdentity {
        RoleIdentity::new(value).expect("fixture role identity is nonempty")
    }

    fn operator(value: &str) -> OperatorId {
        OperatorId::new(value).expect("fixture operator identifier is nonempty")
    }

    fn modes(values: impl IntoIterator<Item = SeparationMode>) -> BTreeSet<SeparationMode> {
        values.into_iter().collect()
    }

    fn packet_with(budgets: CoreBudgets, requested_effect: RequestedEffect) -> ProblemPacket {
        ProblemPacket::from_prompt(ProblemPacketSpec {
            prompt: "classify the obstruction without minting authority",
            carrier: "finite carrier".to_owned(),
            regime: "exact".to_owned(),
            assumptions: vec!["declared carrier is complete".to_owned()],
            constraints: vec!["preserve the observer boundary".to_owned()],
            observer: "canonical observer".to_owned(),
            budgets,
            context_refs: vec![ContextRef::new("ctx:canonical").expect("fixture context")],
            requested_effect,
            permitted_operators: vec![operator("op:classify")],
        })
        .expect("fixture prompt is nonempty")
    }

    fn standard_packet() -> ProblemPacket {
        packet_with(
            CoreBudgets {
                max_repairs: 1,
                max_operator_calls: 4,
            },
            RequestedEffect::Evidence,
        )
    }

    struct FixedProducer {
        id: RoleIdentity,
        proposal: Proposal,
    }

    impl Producer for FixedProducer {
        fn identity(&self) -> RoleIdentity {
            self.id.clone()
        }

        fn propose(
            &self,
            _packet: &ProblemPacket,
            _repair_round: u16,
            _prior_evaluation: Option<&Evaluation>,
        ) -> ProposalStatus {
            ProposalStatus::Proposed(self.proposal.clone())
        }
    }

    struct AcceptingEvaluator {
        id: RoleIdentity,
        modes: BTreeSet<SeparationMode>,
    }

    impl IndependentEvaluator for AcceptingEvaluator {
        fn identity(&self) -> RoleIdentity {
            self.id.clone()
        }

        fn separation_modes(&self) -> BTreeSet<SeparationMode> {
            self.modes.clone()
        }

        fn evaluate(&self, _packet: &ProblemPacket, _proposal: &Proposal) -> Evaluation {
            Evaluation::new("eval:accepted", EvaluationStatus::Accepted)
        }
    }

    struct RoundProducer {
        id: RoleIdentity,
    }

    impl Producer for RoundProducer {
        fn identity(&self) -> RoleIdentity {
            self.id.clone()
        }

        fn propose(
            &self,
            _packet: &ProblemPacket,
            repair_round: u16,
            _prior_evaluation: Option<&Evaluation>,
        ) -> ProposalStatus {
            ProposalStatus::Proposed(Proposal::new(
                format!("proposal:round:{repair_round}"),
                format!("artifact:round:{repair_round}"),
            ))
        }
    }

    struct AlwaysRepairEvaluator {
        id: RoleIdentity,
    }

    impl IndependentEvaluator for AlwaysRepairEvaluator {
        fn identity(&self) -> RoleIdentity {
            self.id.clone()
        }

        fn separation_modes(&self) -> BTreeSet<SeparationMode> {
            modes([SeparationMode::ProcessSeparated])
        }

        fn evaluate(&self, _packet: &ProblemPacket, proposal: &Proposal) -> Evaluation {
            Evaluation::new(
                format!("eval:{}", proposal.proposal_id),
                EvaluationStatus::Repair {
                    residual: Residual::new(
                        CoreRole::Dda,
                        format!("repair {}", proposal.proposal_id),
                    ),
                },
            )
        }
    }

    #[test]
    fn core_result_wire_refuses_completion_evidence_and_independence_forgery() {
        let producer = FixedProducer {
            id: identity("role:producer"),
            proposal: Proposal::new("proposal:wire", "artifact:wire"),
        };
        let evaluator = AcceptingEvaluator {
            id: identity("role:evaluator"),
            modes: modes([SeparationMode::HoldoutSeparated]),
        };
        let result = run_omega(Some(standard_packet()), &producer, &evaluator);

        let mut completed = serde_json::to_value(&result).expect("result serializes");
        completed["terminal"] = serde_json::json!("Completed");
        completed["terminal_role"] = serde_json::json!("Gtfda");
        let completion_error = serde_json::from_value::<CoreResult>(completed)
            .expect_err("wire completion without a sealed witness must be rejected");
        assert!(completion_error.to_string().contains("Completed is sealed"));

        let mut forged_authority_effect = serde_json::to_value(&result).expect("result serializes");
        forged_authority_effect["authority_effect"] = serde_json::json!("Uncertified");
        let authority_effect_error = serde_json::from_value::<CoreResult>(forged_authority_effect)
            .expect_err("wire authority effects outside this slice must be rejected");
        assert!(authority_effect_error
            .to_string()
            .contains("authority effect must remain None"));

        let mut forged_receipt = serde_json::to_value(&result).expect("result serializes");
        let separation_claim = forged_receipt["separation_claim"].clone();
        forged_receipt["independence_receipt"] = serde_json::json!({
            "claim": separation_claim,
            "host_attestation_hash": vec![0_u8; 32],
        });
        let mut forged_evidence = serde_json::to_value(&result).expect("result serializes");
        forged_evidence["evidence_bundle"]["evaluation_refs"] = serde_json::json!(["eval:forged"]);
        let evidence_error = serde_json::from_value::<CoreResult>(forged_evidence)
            .expect_err("evidence references must be derived from attempt receipts");
        assert!(evidence_error.to_string().contains("evidence references"));

        let receipt_error = serde_json::from_value::<CoreResult>(forged_receipt)
            .expect_err("host independence cannot be reconstructed from wire data");
        assert!(receipt_error
            .to_string()
            .contains("host independence receipts cannot be reconstructed"));
    }

    #[test]
    fn bounded_repair_exhaustion_preserves_complete_residual_history() {
        let producer = RoundProducer {
            id: identity("role:producer"),
        };
        let evaluator = AlwaysRepairEvaluator {
            id: identity("role:evaluator"),
        };

        let result = run_omega(Some(standard_packet()), &producer, &evaluator);

        assert_eq!(result.terminal, CoreTerminal::BudgetExhausted);
        assert_eq!(result.terminal_role, CoreRole::Dda);
        assert_eq!(result.attempts.len(), 2);
        assert_eq!(
            result
                .attempts
                .iter()
                .map(|attempt| attempt.repair_round)
                .collect::<Vec<_>>(),
            vec![0, 1]
        );
        assert_eq!(result.residuals.len(), 2);
        assert_eq!(result.residuals[0].summary, "repair proposal:round:0");
        assert_eq!(result.residuals[1].summary, "repair proposal:round:1");
        assert_eq!(
            result.evidence_bundle.residual_ids,
            result
                .residuals
                .iter()
                .map(|residual| residual.id)
                .collect::<Vec<_>>()
        );
        assert_eq!(result.authority_status, AuthorityStatus::None);
        assert_eq!(result.authority_effect, AuthorityEffect::None);
        assert_eq!(result.effect_status, EffectStatus::NotApplied);
    }

    #[test]
    fn plain_evaluator_acceptance_stays_open_without_descent_replay_or_host_independence() {
        let producer = FixedProducer {
            id: identity("role:producer"),
            proposal: Proposal::new("proposal:one", "artifact:one"),
        };
        let evaluator = AcceptingEvaluator {
            id: identity("role:evaluator"),
            modes: modes([
                SeparationMode::ContextSeparated,
                SeparationMode::ProviderSeparated,
            ]),
        };

        let result = run_omega(Some(standard_packet()), &producer, &evaluator);

        assert_eq!(result.terminal, CoreTerminal::OpenResidual);
        assert_eq!(result.terminal_role, CoreRole::Gtfoc);
        assert_eq!(result.attempts.len(), 1);
        assert_eq!(
            result
                .final_proposal()
                .map(|proposal| proposal.proposal_id.as_str()),
            Some("proposal:one")
        );
        assert_eq!(result.authority_status, AuthorityStatus::None);
        assert_eq!(result.authority_effect, AuthorityEffect::None);
        assert_eq!(result.effect_status, EffectStatus::NotApplied);

        let claim = result
            .separation_claim
            .as_ref()
            .expect("the exact self-declared separation claim must be retained");
        assert_eq!(claim.producer().as_str(), "role:producer");
        assert_eq!(claim.evaluator().as_str(), "role:evaluator");
        assert_eq!(
            claim.modes(),
            &modes([
                SeparationMode::ContextSeparated,
                SeparationMode::ProviderSeparated,
            ])
        );
        assert!(!claim.is_merely_prompt_separated());
        assert_eq!(result.independence_receipt, None);
        assert_eq!(result.registry_status, RegistryStatus::Discovered);
        assert_eq!(result.execution_status, ExecutionStatus::Available);
        assert_eq!(result.evidence_status, EvidenceStatus::EvaluationRecorded);
        assert_eq!(result.residuals.len(), 1);
        assert!(result.residuals[0].summary.contains("descent packet"));
        assert_eq!(result.artifact_refs, vec!["artifact:one".to_owned()]);
        assert_eq!(
            result.evidence_bundle.evaluation_refs,
            vec!["eval:accepted".to_owned()]
        );
        assert_eq!(
            result
                .trace
                .iter()
                .map(|event| event.stage)
                .collect::<Vec<_>>(),
            vec![
                TraceStage::Proposed,
                TraceStage::Evaluated,
                TraceStage::Terminalized,
            ]
        );
        assert_eq!(result.effect_receipt, None);
        assert_eq!(result.next_admissible_probe, None);

        let serialized = serde_json::to_string(&result).expect("result must serialize");
        assert!(!serialized.contains("classify the obstruction without minting authority"));
        let round_trip: CoreResult =
            serde_json::from_str(&serialized).expect("serialized result must round-trip");
        assert_eq!(round_trip, result);
    }
}
