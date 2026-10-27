//! Target 7 — Q/CODA product vertical slice (diagnostic / experimental).
//!
//! Pipeline:
//! Proposal → PromptReview → ScopedResearch → DraftPaper →
//! AdversarialReview → FullReview → ManifestBoundZip
//!
//! --- Product Contract:
//! - `AuthorityEffect` is always `"None"`.
//! - Human-only promotion firewall: this module **never** sets `PROMOTED`.
//! - If Targets 1–7 are incomplete, Q/CODA product integration is exposed as
//!   [`FeatureStatus::ExperimentalDisabled`] (or experimental only).
//! - Silent PROD enablement is refused; hosts must not treat this surface as
//!   launch-ready GlobalGreen.
//! - Manifest-bound packages may still build with residual OPEN claims, but
//!   then `release_status = "NOT_RELEASE_CANDIDATE"`.

use std::collections::BTreeMap;
use std::fmt;

use serde::{Deserialize, Serialize};

// ---------------------------------------------------------------------------
// Feature / launch gates
// ---------------------------------------------------------------------------

/// Product feature surface status for Q/CODA integration.
///
/// Production enablement is intentionally a distinct variant so silent or
/// accidental PROD mounts are type-checkable and refuse-able.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum FeatureStatus {
    /// Integration is off for product consumers; diagnostic verticals may run.
    ExperimentalDisabled,
    /// Explicit experimental opt-in at the host layer (not PROD).
    ExperimentalEnabled,
    /// Production enablement — **never** constructed by this crate's constants
    /// or automatic gates while Targets 1–7 remain incomplete.
    ProductionEnabled,
}

impl FeatureStatus {
    /// Human-readable product banner.
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ExperimentalDisabled => "experimental_disabled",
            Self::ExperimentalEnabled => "experimental_enabled",
            Self::ProductionEnabled => "production_enabled",
        }
    }

    /// Whether product HTTP/CLI may mount Q/CODA as a first-class integration.
    pub fn allows_product_mount(self) -> bool {
        matches!(self, Self::ExperimentalEnabled | Self::ProductionEnabled)
    }

    /// Whether this status is production.
    pub fn is_production(self) -> bool {
        matches!(self, Self::ProductionEnabled)
    }
}

/// Standing product gate for Q/CODA integration.
///
/// Targets 1–7 are incomplete at this launch gate, so product surfaces must
/// expose Q/CODA as disabled or experimental — never silent PROD.
pub const Q_CODA_PRODUCT_INTEGRATION: FeatureStatus = FeatureStatus::ExperimentalDisabled;

/// Universal product authority declaration for this vertical.
pub const AUTHORITY_EFFECT: &str = "None";

/// Package release status when residual OPEN claims remain (or anytime this
/// vertical builds a package without human promotion).
pub const RELEASE_NOT_CANDIDATE: &str = "NOT_RELEASE_CANDIDATE";

/// Package release status when all claims are resolved inside the diagnostic
/// pipeline but promotion still did not occur (human-only firewall).
pub const RELEASE_DIAGNOSTIC_ONLY: &str = "DIAGNOSTIC_ONLY_NOT_PROMOTED";

/// Explicit non-promotion stamp. Never rewritten to `PROMOTED` by this module.
pub const PROMOTION_NOT_PROMOTED: &str = "NOT_PROMOTED";

/// Forbidden auto-promotion label (documented for gate tests).
pub const PROMOTION_PROMOTED: &str = "PROMOTED";

/// Launch-gate targets required before product may even *consider* PROD enablement.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum LaunchTarget {
    Target1 = 1,
    Target2 = 2,
    Target3 = 3,
    Target4 = 4,
    Target5 = 5,
    Target6 = 6,
    /// This vertical slice itself.
    Target7 = 7,
}

impl LaunchTarget {
    pub const ALL: [LaunchTarget; 7] = [
        Self::Target1,
        Self::Target2,
        Self::Target3,
        Self::Target4,
        Self::Target5,
        Self::Target6,
        Self::Target7,
    ];

    pub fn id(self) -> u8 {
        self as u8
    }
}

/// Completeness board for Targets 1–7.
///
/// Honest default: all incomplete. Completing a target is an explicit host /
/// human action recorded on the board; this module does not invent completion.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LaunchTargetBoard {
    complete: BTreeMap<u8, bool>,
}

impl Default for LaunchTargetBoard {
    fn default() -> Self {
        let mut complete = BTreeMap::new();
        for t in LaunchTarget::ALL {
            complete.insert(t.id(), false);
        }
        Self { complete }
    }
}

impl LaunchTargetBoard {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn is_complete(&self, target: LaunchTarget) -> bool {
        self.complete.get(&target.id()).copied().unwrap_or(false)
    }

    /// Record completion. Does not enable PROD and does not mint authority.
    pub fn mark_complete(&mut self, target: LaunchTarget) {
        self.complete.insert(target.id(), true);
    }

    pub fn all_complete(&self) -> bool {
        LaunchTarget::ALL.iter().all(|t| self.is_complete(*t))
    }

    /// Incomplete target IDs (1–7), sorted.
    pub fn incomplete(&self) -> Vec<u8> {
        LaunchTarget::ALL
            .iter()
            .filter(|t| !self.is_complete(**t))
            .map(|t| t.id())
            .collect()
    }
}

/// Errors from product / promotion gates.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProductGateError {
    /// Targets 1–7 incomplete; product must stay disabled or experimental.
    TargetsIncomplete { incomplete: Vec<u8> },
    /// Silent or automated PROD enablement is refused.
    SilentProdEnablementRefused {
        requested: FeatureStatus,
        standing: FeatureStatus,
    },
    /// Promotion is human-only; agents/modules never set PROMOTED.
    HumanOnlyPromotionFirewall,
    /// Product mount refused while integration is ExperimentalDisabled.
    ProductMountDisabled { standing: FeatureStatus },
}

impl fmt::Display for ProductGateError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::TargetsIncomplete { incomplete } => {
                write!(
                    f,
                    "Q/CODA product integration disabled: launch targets incomplete {incomplete:?}"
                )
            }
            Self::SilentProdEnablementRefused {
                requested,
                standing,
            } => write!(
                f,
                "refused silent PROD enablement (requested={}, standing={})",
                requested.as_str(),
                standing.as_str()
            ),
            Self::HumanOnlyPromotionFirewall => {
                write!(
                    f,
                    "promotion is human-only; PROMOTED is never set by this module"
                )
            }
            Self::ProductMountDisabled { standing } => write!(
                f,
                "Q/CODA product mount disabled (standing={})",
                standing.as_str()
            ),
        }
    }
}

impl std::error::Error for ProductGateError {}

/// Standing integration status, always honouring incompleteness of Targets 1–7.
///
/// When any target is incomplete, returns [`FeatureStatus::ExperimentalDisabled`].
/// Even when all targets are complete, this function **does not** auto-enable
/// PROD — it returns the standing constant (experimental/disabled) so a human
/// host must still opt in explicitly.
pub fn evaluate_q_coda_integration(board: &LaunchTargetBoard) -> FeatureStatus {
    if !board.all_complete() {
        FeatureStatus::ExperimentalDisabled
    } else {
        // Completeness is necessary but not sufficient for PROD. Keep product
        // from silently flipping to ProductionEnabled.
        Q_CODA_PRODUCT_INTEGRATION
    }
}

/// Refuse silent PROD enablement. Only a future human-operated host path may
/// ever set ProductionEnabled; this crate always refuses automatic elevation.
pub fn refuse_silent_prod_enablement(requested: FeatureStatus) -> Result<(), ProductGateError> {
    if requested.is_production() {
        return Err(ProductGateError::SilentProdEnablementRefused {
            requested,
            standing: Q_CODA_PRODUCT_INTEGRATION,
        });
    }
    Ok(())
}

/// Whether product surfaces may mount Q/CODA as a first-class integration.
///
/// With the standing constant [`Q_CODA_PRODUCT_INTEGRATION`] =
/// [`FeatureStatus::ExperimentalDisabled`], this returns `false`.
pub fn q_coda_product_mount_allowed() -> bool {
    Q_CODA_PRODUCT_INTEGRATION.allows_product_mount()
}

/// Gate a product mount attempt. Fails closed while ExperimentalDisabled or
/// when Targets 1–7 are incomplete.
pub fn gate_product_mount(board: &LaunchTargetBoard) -> Result<FeatureStatus, ProductGateError> {
    let status = evaluate_q_coda_integration(board);
    if !board.all_complete() {
        return Err(ProductGateError::TargetsIncomplete {
            incomplete: board.incomplete(),
        });
    }
    if !status.allows_product_mount() {
        return Err(ProductGateError::ProductMountDisabled { standing: status });
    }
    refuse_silent_prod_enablement(status)?;
    Ok(status)
}

/// Human-only promotion firewall: always refuses. Never returns Ok with PROMOTED.
pub fn try_auto_promote() -> Result<(), ProductGateError> {
    Err(ProductGateError::HumanOnlyPromotionFirewall)
}

// ---------------------------------------------------------------------------
// Claims + proposal
// ---------------------------------------------------------------------------

/// Claim resolution inside the diagnostic vertical (not authority).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ClaimStatus {
    Open,
    Resolved,
    Blocked,
}

impl ClaimStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Open => "OPEN",
            Self::Resolved => "RESOLVED",
            Self::Blocked => "BLOCKED",
        }
    }
}

/// One claim tracked through the pipeline.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClaimRecord {
    pub claim_id: String,
    pub statement: String,
    pub status: ClaimStatus,
}

impl ClaimRecord {
    pub fn open(claim_id: impl Into<String>, statement: impl Into<String>) -> Self {
        Self {
            claim_id: claim_id.into(),
            statement: statement.into(),
            status: ClaimStatus::Open,
        }
    }

    pub fn resolved(claim_id: impl Into<String>, statement: impl Into<String>) -> Self {
        Self {
            claim_id: claim_id.into(),
            statement: statement.into(),
            status: ClaimStatus::Resolved,
        }
    }
}

/// Input proposal for the vertical slice.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProductProposal {
    pub proposal_id: String,
    pub title: String,
    pub body: String,
    pub seed_claims: Vec<ClaimRecord>,
}

impl ProductProposal {
    pub fn new(
        proposal_id: impl Into<String>,
        title: impl Into<String>,
        body: impl Into<String>,
    ) -> Self {
        Self {
            proposal_id: proposal_id.into(),
            title: title.into(),
            body: body.into(),
            seed_claims: Vec::new(),
        }
    }

    pub fn with_claim(mut self, claim: ClaimRecord) -> Self {
        self.seed_claims.push(claim);
        self
    }
}

// ---------------------------------------------------------------------------
// Pipeline stages + receipts
// ---------------------------------------------------------------------------

/// Ordered pipeline stages for Target 7.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PipelineStage {
    Proposal,
    PromptReview,
    ScopedResearch,
    DraftPaper,
    AdversarialReview,
    FullReview,
    ManifestBoundZip,
}

impl PipelineStage {
    pub const ALL: [PipelineStage; 7] = [
        Self::Proposal,
        Self::PromptReview,
        Self::ScopedResearch,
        Self::DraftPaper,
        Self::AdversarialReview,
        Self::FullReview,
        Self::ManifestBoundZip,
    ];

    pub fn id(self) -> &'static str {
        match self {
            Self::Proposal => "proposal",
            Self::PromptReview => "prompt_review",
            Self::ScopedResearch => "scoped_research",
            Self::DraftPaper => "draft_paper",
            Self::AdversarialReview => "adversarial_review",
            Self::FullReview => "full_review",
            Self::ManifestBoundZip => "manifest_bound_zip",
        }
    }
}

/// Per-stage terminal (diagnostic only; not authority).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum StageStatus {
    Passed,
    Blocked,
    UnresolvedClaims,
}

impl StageStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Passed => "Passed",
            Self::Blocked => "Blocked",
            Self::UnresolvedClaims => "UnresolvedClaims",
        }
    }
}

/// Receipt produced by one pipeline stage.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct StageReceipt {
    pub stage_id: PipelineStage,
    pub status: StageStatus,
    pub unresolved_claims: Vec<String>,
    pub artifact_hash: Option<String>,
}

impl StageReceipt {
    pub fn new(stage_id: PipelineStage, status: StageStatus) -> Self {
        Self {
            stage_id,
            status,
            unresolved_claims: Vec::new(),
            artifact_hash: None,
        }
    }

    pub fn with_unresolved(mut self, claims: Vec<String>) -> Self {
        self.unresolved_claims = claims;
        self
    }

    pub fn with_artifact_hash(mut self, hash: impl Into<String>) -> Self {
        self.artifact_hash = Some(hash.into());
        self
    }
}

// ---------------------------------------------------------------------------
// Manifest-bound package (deterministic in-memory "ZIP")
// ---------------------------------------------------------------------------

/// Manifest listing claim IDs and residual OPEN claims.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PackageManifest {
    pub schema: String,
    pub proposal_id: String,
    pub claim_ids: Vec<String>,
    pub residual_open_claims: Vec<String>,
    pub release_status: String,
    pub promotion: String,
    pub authority_effect: String,
    pub feature_status: String,
    pub package_note: String,
}

/// Deterministic in-memory archive bound to the claim manifest.
///
/// Entries are sorted by path. The byte payload is a stable, ZIP-shaped
/// logical package (path + content records) without depending on a host ZIP
/// library — suitable for diagnostic hashing and temp-dir materialization.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManifestBoundZip {
    pub manifest: PackageManifest,
    /// Sorted path → UTF-8 text payload.
    pub entries: BTreeMap<String, String>,
    /// Deterministic hash of the serialized package payload.
    pub package_hash: String,
}

impl ManifestBoundZip {
    /// Build a package. Unresolved claims force `NOT_RELEASE_CANDIDATE` but
    /// still allow the package to build (no auto-promotion either way).
    pub fn build(
        proposal_id: &str,
        claims: &[ClaimRecord],
        draft_paper: &str,
        stage_receipts: &[StageReceipt],
    ) -> Self {
        let mut claim_ids: Vec<String> = claims.iter().map(|c| c.claim_id.clone()).collect();
        claim_ids.sort();
        claim_ids.dedup();

        let mut residual_open_claims: Vec<String> = claims
            .iter()
            .filter(|c| c.status == ClaimStatus::Open || c.status == ClaimStatus::Blocked)
            .map(|c| format!("{}:{}:{}", c.claim_id, c.status.as_str(), c.statement))
            .collect();
        residual_open_claims.sort();

        let has_residuals = !residual_open_claims.is_empty();
        let release_status = if has_residuals {
            RELEASE_NOT_CANDIDATE.to_string()
        } else {
            // Resolved claims still do not promote.
            RELEASE_DIAGNOSTIC_ONLY.to_string()
        };

        let manifest = PackageManifest {
            schema: "core.q_coda.product_vertical_slice.manifest.v1".to_string(),
            proposal_id: proposal_id.to_string(),
            claim_ids: claim_ids.clone(),
            residual_open_claims: residual_open_claims.clone(),
            release_status: release_status.clone(),
            promotion: PROMOTION_NOT_PROMOTED.to_string(),
            authority_effect: AUTHORITY_EFFECT.to_string(),
            feature_status: Q_CODA_PRODUCT_INTEGRATION.as_str().to_string(),
            package_note: if has_residuals {
                "residuals remain OPEN/BLOCKED; package is not a release candidate; never auto-promoted"
                    .to_string()
            } else {
                "all claims resolved inside diagnostic pipeline; still NOT_PROMOTED (human-only firewall)"
                    .to_string()
            },
        };

        let mut entries = BTreeMap::new();
        entries.insert("MANIFEST.json".to_string(), stable_json_manifest(&manifest));
        entries.insert("draft_paper.md".to_string(), draft_paper.to_string());
        entries.insert(
            "claims.jsonl".to_string(),
            claims
                .iter()
                .map(|c| {
                    format!(
                        "{{\"claim_id\":{},\"status\":{},\"statement\":{}}}",
                        json_escape(&c.claim_id),
                        json_escape(c.status.as_str()),
                        json_escape(&c.statement)
                    )
                })
                .collect::<Vec<_>>()
                .join("\n"),
        );
        entries.insert(
            "receipts.jsonl".to_string(),
            stage_receipts
                .iter()
                .map(|r| {
                    format!(
                        "{{\"stage_id\":{},\"status\":{},\"unresolved_claims\":{},\"artifact_hash\":{}}}",
                        json_escape(r.stage_id.id()),
                        json_escape(r.status.as_str()),
                        json_string_array(&r.unresolved_claims),
                        r.artifact_hash
                            .as_ref()
                            .map(|h| json_escape(h))
                            .unwrap_or_else(|| "null".to_string())
                    )
                })
                .collect::<Vec<_>>()
                .join("\n"),
        );
        entries.insert(
            "AUTHORITY".to_string(),
            format!(
                "authority_effect={AUTHORITY_EFFECT}\npromotion={PROMOTION_NOT_PROMOTED}\nrelease_status={release_status}\n"
            ),
        );

        let package_hash = hash_hex(&serialize_package_bytes(&entries));

        Self {
            manifest,
            entries,
            package_hash,
        }
    }

    /// Deterministic byte payload of the logical package (for hashing / export).
    pub fn to_bytes(&self) -> Vec<u8> {
        serialize_package_bytes(&self.entries)
    }

    pub fn release_status(&self) -> &str {
        &self.manifest.release_status
    }

    pub fn residual_open_claims(&self) -> &[String] {
        &self.manifest.residual_open_claims
    }

    /// Materialize into a temp-style directory map (path → bytes) without I/O.
    pub fn as_temp_dir_map(&self) -> BTreeMap<String, Vec<u8>> {
        self.entries
            .iter()
            .map(|(k, v)| (k.clone(), v.as_bytes().to_vec()))
            .collect()
    }
}

fn serialize_package_bytes(entries: &BTreeMap<String, String>) -> Vec<u8> {
    // Stable archive: for each path (BTreeMap order):
    //   "FILE\n" + path + "\n" + decimal length + "\n" + content + "\n"
    let mut out = Vec::new();
    out.extend_from_slice(b"CORE_MANIFEST_BOUND_ZIP_V1\n");
    for (path, content) in entries {
        out.extend_from_slice(b"FILE\n");
        out.extend_from_slice(path.as_bytes());
        out.push(b'\n');
        out.extend_from_slice(content.len().to_string().as_bytes());
        out.push(b'\n');
        out.extend_from_slice(content.as_bytes());
        out.push(b'\n');
    }
    out
}

fn stable_json_manifest(m: &PackageManifest) -> String {
    format!(
        "{{\n  \"schema\": {},\n  \"proposal_id\": {},\n  \"claim_ids\": {},\n  \"residual_open_claims\": {},\n  \"release_status\": {},\n  \"promotion\": {},\n  \"authority_effect\": {},\n  \"feature_status\": {},\n  \"package_note\": {}\n}}\n",
        json_escape(&m.schema),
        json_escape(&m.proposal_id),
        json_string_array(&m.claim_ids),
        json_string_array(&m.residual_open_claims),
        json_escape(&m.release_status),
        json_escape(&m.promotion),
        json_escape(&m.authority_effect),
        json_escape(&m.feature_status),
        json_escape(&m.package_note),
    )
}

fn json_escape(s: &str) -> String {
    let mut out = String::from("\"");
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c.is_control() => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

fn json_string_array(items: &[String]) -> String {
    let inner = items
        .iter()
        .map(|s| json_escape(s))
        .collect::<Vec<_>>()
        .join(",");
    format!("[{inner}]")
}

/// Deterministic non-crypto hex digest (FNV-1a 64-bit) for diagnostic artifact hashes.
///
/// Not a security hash and not a release seal — only stability for receipts.
fn hash_hex(bytes: impl AsRef<[u8]>) -> String {
    const FNV_OFFSET: u64 = 0xcbf29ce484222325;
    const FNV_PRIME: u64 = 0x100000001b3;
    let mut hash = FNV_OFFSET;
    for b in bytes.as_ref() {
        hash ^= u64::from(*b);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    format!("fnv1a64:{hash:016x}")
}

// ---------------------------------------------------------------------------
// Orchestrator
// ---------------------------------------------------------------------------

/// Working state accumulated across stages (diagnostic only).
#[derive(Clone, Debug, PartialEq, Eq)]
struct PipelineState {
    proposal: ProductProposal,
    claims: Vec<ClaimRecord>,
    research_notes: String,
    draft_paper: String,
    receipts: Vec<StageReceipt>,
    package: Option<ManifestBoundZip>,
    blocked_reason: Option<String>,
}

/// Full vertical-slice run result.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerticalSliceRun {
    pub run_id: String,
    pub proposal_id: String,
    pub receipts: Vec<StageReceipt>,
    pub package: Option<ManifestBoundZip>,
    pub authority_effect: String,
    pub feature_status: FeatureStatus,
    pub release_status: String,
    pub promotion: String,
    pub unresolved_claims: Vec<String>,
}

impl VerticalSliceRun {
    /// Aggregate OPEN/BLOCKED claim ids still residual after the run.
    pub fn has_unresolved(&self) -> bool {
        !self.unresolved_claims.is_empty()
    }

    /// Never true: this module does not promote.
    pub fn is_promoted(&self) -> bool {
        self.promotion == PROMOTION_PROMOTED
    }
}

/// Pure diagnostic orchestrator for the Target 7 product vertical.
#[derive(Clone, Debug, Default)]
pub struct ProductVerticalSlice;

impl ProductVerticalSlice {
    pub fn new() -> Self {
        Self
    }

    /// Run the full 7-stage pipeline. Always stamps AuthorityEffect None and
    /// never sets PROMOTED. Unresolved claims remain explicit on receipts and
    /// on the package manifest.
    fn run_stage(&self, stage: PipelineStage, state: &mut PipelineState) -> StageReceipt {
        match stage {
            PipelineStage::Proposal => self.stage_proposal(state),
            PipelineStage::PromptReview => self.stage_prompt_review(state),
            PipelineStage::ScopedResearch => self.stage_scoped_research(state),
            PipelineStage::DraftPaper => self.stage_draft_paper(state),
            PipelineStage::AdversarialReview => self.stage_adversarial_review(state),
            PipelineStage::FullReview => self.stage_full_review(state),
            PipelineStage::ManifestBoundZip => self.stage_manifest_bound_zip(state),
        }
    }

    pub fn run(&self, proposal: ProductProposal) -> VerticalSliceRun {
        let run_id = format!("pvs:{}", proposal.proposal_id);
        let mut state = PipelineState {
            claims: proposal.seed_claims.clone(),
            proposal,
            research_notes: String::new(),
            draft_paper: String::new(),
            receipts: Vec::new(),
            package: None,
            blocked_reason: None,
        };

        for stage in PipelineStage::ALL {
            if state.blocked_reason.is_some() && stage != PipelineStage::ManifestBoundZip {
                // Still emit a blocked receipt for remaining non-zip stages so
                // the stage set is complete and residuals stay explicit.
                let open = open_claim_ids(&state.claims);
                state.receipts.push(
                    StageReceipt::new(stage, StageStatus::Blocked)
                        .with_unresolved(open)
                        .with_artifact_hash(hash_hex(
                            state.blocked_reason.as_deref().unwrap_or("blocked"),
                        )),
                );
                continue;
            }
            let receipt = self.run_stage(stage, &mut state);
            state.receipts.push(receipt);
        }

        let unresolved = open_claim_ids(&state.claims);
        let release_status = state
            .package
            .as_ref()
            .map(|p| p.release_status().to_string())
            .unwrap_or_else(|| RELEASE_NOT_CANDIDATE.to_string());

        VerticalSliceRun {
            run_id,
            proposal_id: state.proposal.proposal_id,
            receipts: state.receipts,
            package: state.package,
            authority_effect: AUTHORITY_EFFECT.to_string(),
            feature_status: Q_CODA_PRODUCT_INTEGRATION,
            release_status,
            promotion: PROMOTION_NOT_PROMOTED.to_string(),
            unresolved_claims: unresolved,
        }
    }

    fn stage_proposal(&self, state: &mut PipelineState) -> StageReceipt {
        let empty_id = state.proposal.proposal_id.trim().is_empty();
        let empty_title = state.proposal.title.trim().is_empty();
        if empty_id || empty_title {
            state.blocked_reason = Some("proposal missing id or title".to_string());
            return StageReceipt::new(PipelineStage::Proposal, StageStatus::Blocked)
                .with_unresolved(open_claim_ids(&state.claims))
                .with_artifact_hash(hash_hex("proposal:blocked"));
        }
        // Ensure every seed claim is present; do not silently drop OPEN.
        if state.claims.is_empty() {
            state.claims.push(ClaimRecord::open(
                format!("claim:{}:implicit-scope", state.proposal.proposal_id),
                "proposal carried no seed claims; scope residual remains OPEN",
            ));
        }
        let payload = format!(
            "{}|{}|{}",
            state.proposal.proposal_id, state.proposal.title, state.proposal.body
        );
        let open = open_claim_ids(&state.claims);
        let status = if open.is_empty() {
            StageStatus::Passed
        } else {
            StageStatus::UnresolvedClaims
        };
        StageReceipt::new(PipelineStage::Proposal, status)
            .with_unresolved(open)
            .with_artifact_hash(hash_hex(payload))
    }

    fn stage_prompt_review(&self, state: &mut PipelineState) -> StageReceipt {
        let body_ok = state.proposal.body.trim().len() >= 8;
        if !body_ok {
            state.claims.push(ClaimRecord::open(
                format!("claim:{}:prompt-thin", state.proposal.proposal_id),
                "proposal body too thin for scoped research",
            ));
        }
        let open = open_claim_ids(&state.claims);
        let status = if open.is_empty() {
            StageStatus::Passed
        } else {
            StageStatus::UnresolvedClaims
        };
        let review = format!(
            "prompt_review:title_len={}:body_len={}:open={}",
            state.proposal.title.len(),
            state.proposal.body.len(),
            open.len()
        );
        StageReceipt::new(PipelineStage::PromptReview, status)
            .with_unresolved(open)
            .with_artifact_hash(hash_hex(review))
    }

    fn stage_scoped_research(&self, state: &mut PipelineState) -> StageReceipt {
        let mut notes = String::new();
        notes.push_str("# Scoped research (diagnostic)\n");
        notes.push_str(&format!("proposal: {}\n", state.proposal.proposal_id));
        for c in &state.claims {
            notes.push_str(&format!(
                "- [{}] {} — {}\n",
                c.status.as_str(),
                c.claim_id,
                c.statement
            ));
        }
        state.research_notes = notes.clone();
        let open = open_claim_ids(&state.claims);
        let status = if open.is_empty() {
            StageStatus::Passed
        } else {
            StageStatus::UnresolvedClaims
        };
        StageReceipt::new(PipelineStage::ScopedResearch, status)
            .with_unresolved(open)
            .with_artifact_hash(hash_hex(notes))
    }

    fn stage_draft_paper(&self, state: &mut PipelineState) -> StageReceipt {
        let mut draft = String::new();
        draft.push_str(&format!("# {}\n\n", state.proposal.title));
        draft.push_str(&format!(
            "**AuthorityEffect:** `{AUTHORITY_EFFECT}`  \n**Promotion:** `{PROMOTION_NOT_PROMOTED}`  \n**Feature:** `{}`\n\n",
            Q_CODA_PRODUCT_INTEGRATION.as_str()
        ));
        draft.push_str("## Proposal\n\n");
        draft.push_str(&state.proposal.body);
        draft.push_str("\n\n## Research notes\n\n");
        draft.push_str(&state.research_notes);
        draft.push_str("\n## Claims ledger\n\n");
        for c in &state.claims {
            draft.push_str(&format!(
                "- `{}` ({}) {}\n",
                c.claim_id,
                c.status.as_str(),
                c.statement
            ));
        }
        draft.push_str(
            "\n## Residual policy\n\nUnresolved claims remain explicit. This draft is not a release candidate and is never auto-promoted.\n",
        );
        state.draft_paper = draft.clone();
        let open = open_claim_ids(&state.claims);
        let status = if open.is_empty() {
            StageStatus::Passed
        } else {
            StageStatus::UnresolvedClaims
        };
        StageReceipt::new(PipelineStage::DraftPaper, status)
            .with_unresolved(open)
            .with_artifact_hash(hash_hex(draft))
    }

    fn stage_adversarial_review(&self, state: &mut PipelineState) -> StageReceipt {
        // Adversarial pass: every OPEN claim is re-listed; empty drafts are blocked.
        if state.draft_paper.trim().is_empty() {
            state.blocked_reason = Some("adversarial review: empty draft".to_string());
            return StageReceipt::new(PipelineStage::AdversarialReview, StageStatus::Blocked)
                .with_unresolved(open_claim_ids(&state.claims))
                .with_artifact_hash(hash_hex("adversarial:empty"));
        }
        let open = open_claim_ids(&state.claims);
        let status = if open.is_empty() {
            StageStatus::Passed
        } else {
            StageStatus::UnresolvedClaims
        };
        let artifact = format!("adversarial:open={}", open.join(","));
        StageReceipt::new(PipelineStage::AdversarialReview, status)
            .with_unresolved(open)
            .with_artifact_hash(hash_hex(artifact))
    }

    fn stage_full_review(&self, state: &mut PipelineState) -> StageReceipt {
        let open = open_claim_ids(&state.claims);
        // Full review never promotes. Unresolved claims stay UnresolvedClaims;
        // clean runs still only Pass as diagnostic.
        let status = if open.is_empty() {
            StageStatus::Passed
        } else {
            StageStatus::UnresolvedClaims
        };
        // Human-only firewall: refuse any auto-promote attempt as part of review.
        let _ = try_auto_promote();
        StageReceipt::new(PipelineStage::FullReview, status)
            .with_unresolved(open.clone())
            .with_artifact_hash(hash_hex(format!(
                "full_review:open={}:promotion={PROMOTION_NOT_PROMOTED}",
                open.len()
            )))
    }

    fn stage_manifest_bound_zip(&self, state: &mut PipelineState) -> StageReceipt {
        let package = ManifestBoundZip::build(
            &state.proposal.proposal_id,
            &state.claims,
            &state.draft_paper,
            &state.receipts,
        );
        let open = open_claim_ids(&state.claims);
        let status = if state.blocked_reason.is_some() && state.draft_paper.is_empty() {
            StageStatus::Blocked
        } else if !open.is_empty() {
            StageStatus::UnresolvedClaims
        } else {
            StageStatus::Passed
        };
        let hash = package.package_hash.clone();
        // Invariant: never PROMOTED
        debug_assert_ne!(package.manifest.promotion, PROMOTION_PROMOTED);
        debug_assert_eq!(package.manifest.authority_effect, AUTHORITY_EFFECT);
        state.package = Some(package);
        StageReceipt::new(PipelineStage::ManifestBoundZip, status)
            .with_unresolved(open)
            .with_artifact_hash(hash)
    }
}

fn open_claim_ids(claims: &[ClaimRecord]) -> Vec<String> {
    let mut ids: Vec<String> = claims
        .iter()
        .filter(|c| c.status == ClaimStatus::Open || c.status == ClaimStatus::Blocked)
        .map(|c| c.claim_id.clone())
        .collect();
    ids.sort();
    ids.dedup();
    ids
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

// Origin: engine/crates_rs/core_wdp/src/coda/q/product_vertical_slice.rs
// Claim: urn:core:crates_rs:core-wdp:product-vertical-slice:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn proposal_with_open_claim() -> ProductProposal {
        ProductProposal::new(
            "prop-001",
            "Q/CODA diagnostic paper",
            "Seed body for scoped research on residual honesty.",
        )
        .with_claim(ClaimRecord::open(
            "claim:coda-cs-bridge",
            "finite-shadow bridge to continuum claim remains OPEN",
        ))
    }

    fn proposal_all_resolved() -> ProductProposal {
        ProductProposal::new(
            "prop-002",
            "Resolved claims diagnostic",
            "Body long enough for prompt review stage.",
        )
        .with_claim(ClaimRecord::resolved(
            "claim:local-finite",
            "finite local claim closed inside diagnostic scope",
        ))
    }

    #[test]
    fn standing_integration_is_experimental_disabled() {
        assert_eq!(
            Q_CODA_PRODUCT_INTEGRATION,
            FeatureStatus::ExperimentalDisabled
        );
        assert!(!q_coda_product_mount_allowed());
        assert!(!Q_CODA_PRODUCT_INTEGRATION.allows_product_mount());
        assert!(!Q_CODA_PRODUCT_INTEGRATION.is_production());
    }

    #[test]
    fn incomplete_targets_force_disabled_integration() {
        let board = LaunchTargetBoard::default();
        assert!(!board.all_complete());
        assert_eq!(
            evaluate_q_coda_integration(&board),
            FeatureStatus::ExperimentalDisabled
        );
        let err = gate_product_mount(&board).expect_err("mount must fail closed");
        match err {
            ProductGateError::TargetsIncomplete { incomplete } => {
                assert_eq!(incomplete, vec![1, 2, 3, 4, 5, 6, 7]);
            }
            other => panic!("unexpected gate error: {other}"),
        }
    }

    #[test]
    fn complete_targets_still_refuse_silent_prod() {
        let mut board = LaunchTargetBoard::new();
        for t in LaunchTarget::ALL {
            board.mark_complete(t);
        }
        assert!(board.all_complete());
        // Standing constant remains ExperimentalDisabled — no silent PROD.
        assert_eq!(
            evaluate_q_coda_integration(&board),
            FeatureStatus::ExperimentalDisabled
        );
        assert!(matches!(
            refuse_silent_prod_enablement(FeatureStatus::ProductionEnabled),
            Err(ProductGateError::SilentProdEnablementRefused { .. })
        ));
        // Experimental opt-in request is not PROD; refuse_silent allows it
        // (host still decides whether to flip the constant).
        assert!(refuse_silent_prod_enablement(FeatureStatus::ExperimentalEnabled).is_ok());
    }

    #[test]
    fn human_only_promotion_firewall() {
        assert!(matches!(
            try_auto_promote(),
            Err(ProductGateError::HumanOnlyPromotionFirewall)
        ));
    }

    #[test]
    fn pipeline_emits_seven_receipts_and_keeps_open_claims() {
        let run = ProductVerticalSlice::new().run(proposal_with_open_claim());
        assert_eq!(run.receipts.len(), 7);
        assert_eq!(
            run.receipts.iter().map(|r| r.stage_id).collect::<Vec<_>>(),
            PipelineStage::ALL.to_vec()
        );
        assert_eq!(run.authority_effect, AUTHORITY_EFFECT);
        assert_eq!(run.promotion, PROMOTION_NOT_PROMOTED);
        assert!(!run.is_promoted());
        assert!(run.has_unresolved());
        assert!(run
            .unresolved_claims
            .iter()
            .any(|c| c == "claim:coda-cs-bridge"));
        assert_eq!(run.feature_status, FeatureStatus::ExperimentalDisabled);

        // Stages that see OPEN claims report UnresolvedClaims (not silent pass).
        let adv = run
            .receipts
            .iter()
            .find(|r| r.stage_id == PipelineStage::AdversarialReview)
            .expect("adversarial receipt");
        assert_eq!(adv.status, StageStatus::UnresolvedClaims);
        assert!(!adv.unresolved_claims.is_empty());
    }

    #[test]
    fn manifest_zip_not_release_candidate_when_residuals_remain() {
        let run = ProductVerticalSlice::new().run(proposal_with_open_claim());
        let pkg = run.package.expect("package built even with residuals");
        assert_eq!(pkg.release_status(), RELEASE_NOT_CANDIDATE);
        assert_eq!(pkg.manifest.promotion, PROMOTION_NOT_PROMOTED);
        assert_eq!(pkg.manifest.authority_effect, AUTHORITY_EFFECT);
        assert!(!pkg.residual_open_claims().is_empty());
        assert!(pkg.entries.contains_key("MANIFEST.json"));
        assert!(pkg.entries.contains_key("draft_paper.md"));
        assert!(pkg.entries.contains_key("claims.jsonl"));
        assert!(pkg.entries.contains_key("receipts.jsonl"));
        assert!(pkg.entries.contains_key("AUTHORITY"));
        // Deterministic package hash + payload.
        assert_eq!(pkg.package_hash, hash_hex(pkg.to_bytes()));
        let again = ProductVerticalSlice::new().run(proposal_with_open_claim());
        assert_eq!(
            again.package.as_ref().map(|p| p.package_hash.clone()),
            Some(pkg.package_hash.clone())
        );
    }

    #[test]
    fn resolved_claims_still_not_promoted() {
        let run = ProductVerticalSlice::new().run(proposal_all_resolved());
        assert!(!run.has_unresolved());
        assert_eq!(run.promotion, PROMOTION_NOT_PROMOTED);
        let pkg = run.package.expect("package");
        assert_eq!(pkg.release_status(), RELEASE_DIAGNOSTIC_ONLY);
        assert_eq!(pkg.manifest.promotion, PROMOTION_NOT_PROMOTED);
        assert_ne!(pkg.manifest.promotion, PROMOTION_PROMOTED);
        // Full review passed diagnostically but firewall holds.
        let full = run
            .receipts
            .iter()
            .find(|r| r.stage_id == PipelineStage::FullReview)
            .expect("full review");
        assert_eq!(full.status, StageStatus::Passed);
    }

    #[test]
    fn empty_proposal_blocks_without_promotion() {
        let run = ProductVerticalSlice::new().run(ProductProposal::new("", "", ""));
        assert_eq!(run.promotion, PROMOTION_NOT_PROMOTED);
        assert_eq!(run.authority_effect, AUTHORITY_EFFECT);
        let first = &run.receipts[0];
        assert_eq!(first.stage_id, PipelineStage::Proposal);
        assert_eq!(first.status, StageStatus::Blocked);
    }

    #[test]
    fn product_disables_q_coda_when_targets_incomplete() {
        // Product rule: If Targets 1–7 incomplete, expose Q/CODA as disabled
        // or experimental — never PROD, never silent mount.
        let board = LaunchTargetBoard::default();
        assert!(!board.all_complete());
        assert_eq!(
            evaluate_q_coda_integration(&board),
            FeatureStatus::ExperimentalDisabled
        );
        assert_eq!(Q_CODA_PRODUCT_INTEGRATION.as_str(), "experimental_disabled");
        assert!(gate_product_mount(&board).is_err());
        assert!(!q_coda_product_mount_allowed());
    }

    #[test]
    fn stage_receipts_carry_optional_artifact_hash() {
        let run = ProductVerticalSlice::new().run(proposal_with_open_claim());
        for r in &run.receipts {
            assert!(
                r.artifact_hash.is_some(),
                "stage {} missing artifact_hash",
                r.stage_id.id()
            );
        }
    }
}
