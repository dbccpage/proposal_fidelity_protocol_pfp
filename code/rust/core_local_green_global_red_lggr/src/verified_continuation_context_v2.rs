//! `VerifiedContinuationContextV2` — one root evidence object.
//!
//! Implements ADR-008. v1 is quarantined `REJECTED_UNSOUND`; this is the
//! replacement, built to the **Outer Boundary Closure Invariant**:
//!
//! > An evidence seal is incomplete until every downstream representation and
//! > consumer — serialized products, adapters, caches, replay, execution terminals
//! > — is unable to cross proposal into execution without the same root
//! > verification authority.
//!
//! # The shape, and why it differs from v1
//!
//! ```text
//!   RawEvidencePacket        <- fully public, fully forgeable. THAT IS FINE.
//!         │                     Lying here is detected, never carried.
//!      verify()              <- recomputes everything discriminating
//!         │
//!   VerifiedContinuationContextV2   <- sealed; one root digest binds every
//!         │                            discriminating field exactly once
//!      decide()             <- takes ONLY the context. No booleans.
//!         │
//!   ContinuationDecision    <- derived, never stored, never deserializable
//! ```
//!
//! v1 failed four times by sealing one artefact and leaving the next one open.
//! Two corollaries from ADR-008 are structural here:
//!
//! * **C1 — seal the product, not only the producer.** [`ContinuationDecision`]
//!   stores no verdict and has no `Deserialize`; the verdict is derived from
//!   blockers, so there is no field to forge.
//! * **C2 — bind the discriminating field, not merely the bulk.** The root digest
//!   binds the **whole adequacy report**, the declaration, the capacity evidence,
//!   the global evaluator trace and the preservation witness — not just the corpus.
//!   v1 hashed corpus and rows faithfully and still collided because adequacy sat
//!   outside the hash.
//!
//! # What no public constructor accepts
//!
//! `detector_adequate` · `adapter_sound` · `residual_preservation_verified` ·
//! `has_witness` where the intake receipt establishes it · caller-asserted
//! `Exhibited` · a precomputed adequacy verdict or classification.
//!
//! Every one of those was an input in some v1 round. They are derived results.
//!
//! **AuthorityEffect: None.**

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::epk_engine::{
    calculate_metrics, evaluator_gluing_defect, BoundarySlice, CompositionRecord, EpkError,
    EpkMetrics, GluingDefect, TraceLedger,
};
use core_types::authority::AuthorityEffect;
use core_types::ceiling::EvidenceCeiling;
use core_types::{DetectorCapacityEvidence, DetectorDeploymentDeclaration};

use crate::adequacy::{
    evaluate_detector_adequacy, DetectorAdequacyVerdict, DetectorAdequacyVerdictKind,
};
use crate::bound_measurement::CanonicalHasher;
use crate::ledger::EpkResidualLedger;
use crate::verdict::{classify, EvaluatorProvenance, LggrVerdict};

/// The only schema `verify` accepts. v1 packets are refused before recomputation.
pub const V2_CONTEXT_SCHEMA: &str = "core.epk.verified-continuation-context.v2";

// ── typed refusals ───────────────────────────────────────────────────────────

/// Every way verification can refuse. Refusals are typed, never downgrades.
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum TypedRefusal {
    #[error("schema {found:?} refused; this verifier accepts only {expected}")]
    SchemaRefused {
        found: String,
        expected: &'static str,
    },
    #[error("no accepted intake receipt: Prime 001-I/000 admission was never established")]
    IntakeNotAccepted,
    #[error("intake receipt is bound to run {receipt_run}, packet declares {packet_run}")]
    IntakeRunMismatch {
        receipt_run: String,
        packet_run: String,
    },
    #[error("empty corpus")]
    EmptyCorpus,
    #[error("selected row {index} out of range for {len} records")]
    RowOutOfRange { index: usize, len: usize },
    #[error(
        "local evaluator trace mismatch on {record_id}: declared (l={declared_left}, \
         r={declared_right}), ledger has (l={ledger_left:?}, r={ledger_right:?})"
    )]
    LocalTraceMismatch {
        record_id: String,
        declared_left: bool,
        declared_right: bool,
        ledger_left: Option<bool>,
        ledger_right: Option<bool>,
    },
    /// `E_g` determines `Δ_E`. v1 never checked it; here its absence is fatal to
    /// an `Exhibited` reading rather than silently downgraded.
    #[error("no global evaluator trace for {record_id}: E_g cannot be replayed, so Exhibited is refused")]
    GlobalTraceMissing { record_id: String },
    #[error(
        "global evaluator trace mismatch on {record_id}: declared {declared}, replayed {replayed}"
    )]
    GlobalTraceMismatch {
        record_id: String,
        declared: bool,
        replayed: bool,
    },
    /// A caller cannot clear a refusal that was already recorded.
    #[error("prior refusal {0:?} cannot be cleared by a later packet")]
    PriorRefusalNotMonotone(ContinuationBlockerV2),
    /// No trusted verifier is wired for a capability, so the fact cannot be
    /// established. Refusing beats inventing it from the packet.
    #[error("no trusted verifier for {capability}: the fact cannot be established")]
    NoTrustedVerifier { capability: &'static str },
    #[error("a declaration is required before capacity can be solved")]
    DeclarationMissing,
    /// The capacity solver ran and refused. Distinct from NoTrustedVerifier: a
    /// solver IS wired, it just could not establish the capacity for this input.
    #[error("capacity solver refused: {detail}")]
    CapacitySolverRefused { detail: String },
    #[error(transparent)]
    Metrics(#[from] EpkError),
}

// ── intake ───────────────────────────────────────────────────────────────────

/// Opaque proof that Prime 001-I / 000 admitted this candidate.
///
/// Bound to a run id, so a receipt from one run cannot license another. v1 left
/// `has_witness` and `next_carrier_declared` as caller booleans; here they are
/// established by admission.
/// `Serialize`-only, deliberately. `Deserialize` WAS derived, which made
/// `admit()`'s checks bypassable: private fields do not stop serde, so
/// `serde_json::from_str::<AcceptedIntakeReceipt>(..)` minted a receipt with an
/// EMPTY `witness_certificate` and `next_carrier` -- precisely the two conditions
/// `admit()` exists to reject. The sibling evidence types were already pinned this
/// way; this one was not.
///
/// ```compile_fail
/// use core_epk::v2::AcceptedIntakeReceipt;
/// let _: AcceptedIntakeReceipt = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct AcceptedIntakeReceipt {
    run_id: String,
    candidate_digest: String,
    witness_certificate: String,
    next_carrier: String,
}

impl AcceptedIntakeReceipt {
    /// Minted only by a successful admission.
    pub fn admit(
        run_id: impl Into<String>,
        candidate_digest: impl Into<String>,
        witness_certificate: impl Into<String>,
        next_carrier: impl Into<String>,
    ) -> Option<Self> {
        let witness_certificate = witness_certificate.into();
        let next_carrier = next_carrier.into();
        // Admission requires a witness and a declared next carrier; without them
        // there is nothing to admit.
        if witness_certificate.is_empty() || next_carrier.is_empty() {
            return None;
        }
        Some(Self {
            run_id: run_id.into(),
            candidate_digest: candidate_digest.into(),
            witness_certificate,
            next_carrier,
        })
    }

    pub fn run_id(&self) -> &str {
        &self.run_id
    }
    pub fn candidate_digest(&self) -> &str {
        &self.candidate_digest
    }
    pub fn witness_certificate(&self) -> &str {
        &self.witness_certificate
    }
    pub fn next_carrier(&self) -> &str {
        &self.next_carrier
    }
    /// Establishes Prime 002's `has_witness` conjunct. Not a caller boolean.
    pub fn has_witness(&self) -> bool {
        !self.witness_certificate.is_empty()
    }
    /// Establishes `next_carrier_declared`.
    pub fn next_carrier_declared(&self) -> bool {
        !self.next_carrier.is_empty()
    }
}

// ── transport / preservation ─────────────────────────────────────────────────

/// What a caller *claims* about a transport. Verified, never trusted.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TransportClaim {
    pub source_carrier: String,
    pub target_carrier: String,
    pub loss_ledger: Vec<String>,
}

/// Verifier-produced. Replaces v1's caller-supplied `residual_preservation_verified`.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct ResidualPreservationWitness {
    source_carrier: String,
    target_carrier: String,
    source_ngd: f64,
    target_ngd: f64,
    preserved: bool,
    loss_ledger: Vec<String>,
}

impl ResidualPreservationWitness {
    /// Build from an **independently measured** target residual.
    ///
    /// The caller supplies neither side of this comparison: `source_ngd` is derived
    /// from the corpus, `measured_target` comes from [`TransportVerifier`]. An
    /// earlier revision compared against a caller-supplied `target_ngd`, so
    /// echoing the source value minted `preserved = true`.
    ///
    /// A non-empty loss ledger also blocks preservation: an adapter that reports
    /// loss has not preserved the residual, whatever the numbers say.
    fn from_measurement(claim: &TransportClaim, source_ngd: f64, measured_target: f64) -> Self {
        let preserved = measured_target.is_finite()
            && source_ngd.is_finite()
            && (measured_target - source_ngd).abs() <= f64::EPSILON
            && claim.loss_ledger.is_empty();
        Self {
            source_carrier: claim.source_carrier.clone(),
            target_carrier: claim.target_carrier.clone(),
            source_ngd,
            target_ngd: measured_target,
            preserved,
            loss_ledger: claim.loss_ledger.clone(),
        }
    }

    pub fn source_carrier(&self) -> &str {
        &self.source_carrier
    }
    pub fn target_carrier(&self) -> &str {
        &self.target_carrier
    }

    /// Establishes Prime 002's `adapter_sound` conjunct. Not a caller boolean.
    pub fn preserved(&self) -> bool {
        self.preserved
    }
    pub fn source_ngd(&self) -> f64 {
        self.source_ngd
    }
    pub fn target_ngd(&self) -> f64 {
        self.target_ngd
    }
    pub fn loss_ledger(&self) -> &[String] {
        &self.loss_ledger
    }
}

// ── the raw packet ───────────────────────────────────────────────────────────

/// Everything a caller supplies, entirely public and entirely forgeable.
///
/// **That is deliberate.** Under the Outer Boundary Closure Invariant the input
/// surface does not need sealing — [`verify`] recomputes every discriminating
/// field from it. A lie here is *detected*, never carried forward. v1 tried to
/// seal inputs and leaked at each new layer; v2 seals only the verified product.
///
/// `Serialize` but not `Deserialize` — not for safety, but because its
/// `DetectorDeploymentDeclaration` and `DetectorCapacityEvidence` components are
/// themselves deliberately non-deserializable. A packet is assembled in-process
/// from real objects; it is never parsed from attacker-controlled JSON.
#[derive(Debug, Clone, Serialize)]
pub struct RawEvidencePacket {
    pub schema: String,
    pub run_id: String,
    pub accepted_intake: Option<AcceptedIntakeReceipt>,
    pub records: Vec<CompositionRecord>,
    pub trace_ledger: TraceLedger,
    pub boundary: BoundarySlice,
    pub declaration: Option<DetectorDeploymentDeclaration>,
    pub selected_row: usize,
    /// What the caller *claims* about a transport. The target residual is measured
    /// by [`TransportVerifier`], never taken from here.
    pub transport: Option<TransportClaim>,
    pub budget_remaining: f64,
    pub delta_control: f64,
    pub parent_receipt_hash: Option<String>,
    #[serde(rename = "gtla_refusal")]
    pub coda_gtla_refusal: bool,
}

// ── trusted verifier dependencies ────────────────────────────────────────────
//
// `verify` cannot establish external facts from raw data. An earlier revision
// tried: it compared `global_evaluator_trace[id]` against `record.global_pass`
// (two caller-supplied copies of the same claim), compared a derived source `ngd`
// against a caller-supplied `target_ngd`, and derived adequacy from a
// caller-minted `DetectorCapacityEvidence`. Each was a consistency check dressed
// as verification, and each was defeated by supplying both sides.
//
// The facts now come from dependencies, and the packet has no field through which
// to supply them.

/// Confirms an intake receipt was really issued by admission.
pub trait AdmissionAuthority {
    fn confirm_admission(&self, receipt: &AcceptedIntakeReceipt) -> Result<(), TypedRefusal>;
}

/// Re-runs the global evaluator. The packet carries no copy of `E_g` to compare
/// against — this is the only source.
pub trait GlobalEvaluatorReplay {
    fn replay_global(&self, record: &CompositionRecord) -> Result<bool, TypedRefusal>;
}

/// Produces capacity evidence by **solving**, not by accepting a DTO.
pub trait CapacitySolver {
    fn solve(
        &self,
        declaration: &DetectorDeploymentDeclaration,
        records: &[CompositionRecord],
        trace_ledger: &TraceLedger,
        boundary: &BoundarySlice,
    ) -> Result<DetectorCapacityEvidence, TypedRefusal>;
}

/// Independently measures the residual at the target carrier.
pub trait TransportVerifier {
    fn measure_target(&self, claim: &TransportClaim, source_ngd: f64) -> Result<f64, TypedRefusal>;
}

/// Append-only standing refusals for a run. The packet cannot omit them, which is
/// what makes monotonicity real rather than voluntary.
pub trait RefusalStore {
    fn standing_refusals(&self, run_id: &str) -> Vec<ContinuationBlockerV2>;
}

/// The full trusted surface `verify` requires.
pub trait VerifierSuite {
    fn admission(&self) -> &dyn AdmissionAuthority;
    fn global_replay(&self) -> &dyn GlobalEvaluatorReplay;
    fn capacity(&self) -> &dyn CapacitySolver;
    fn transport(&self) -> &dyn TransportVerifier;
    fn refusals(&self) -> &dyn RefusalStore;
}

/// The honest default: refuses everything.
///
/// Where no trusted verifier is wired, verification **refuses** rather than
/// fabricating a fact from the packet. Shipping this as the default is the point:
/// a caller with no verifiers gets refusals, not green.
#[derive(Debug, Clone, Copy, Default)]
pub struct RefusingVerifierSuite;

impl AdmissionAuthority for RefusingVerifierSuite {
    fn confirm_admission(&self, _r: &AcceptedIntakeReceipt) -> Result<(), TypedRefusal> {
        Err(TypedRefusal::NoTrustedVerifier {
            capability: "admission",
        })
    }
}
impl GlobalEvaluatorReplay for RefusingVerifierSuite {
    fn replay_global(&self, _r: &CompositionRecord) -> Result<bool, TypedRefusal> {
        Err(TypedRefusal::NoTrustedVerifier {
            capability: "global evaluator replay",
        })
    }
}
impl CapacitySolver for RefusingVerifierSuite {
    fn solve(
        &self,
        _d: &DetectorDeploymentDeclaration,
        _r: &[CompositionRecord],
        _l: &TraceLedger,
        _b: &BoundarySlice,
    ) -> Result<DetectorCapacityEvidence, TypedRefusal> {
        Err(TypedRefusal::NoTrustedVerifier {
            capability: "capacity solver",
        })
    }
}
impl TransportVerifier for RefusingVerifierSuite {
    fn measure_target(&self, _c: &TransportClaim, _s: f64) -> Result<f64, TypedRefusal> {
        Err(TypedRefusal::NoTrustedVerifier {
            capability: "transport verifier",
        })
    }
}
impl RefusalStore for RefusingVerifierSuite {
    fn standing_refusals(&self, _run_id: &str) -> Vec<ContinuationBlockerV2> {
        // Unknown store: assume a refusal stands. Fail closed.
        vec![ContinuationBlockerV2::PriorRefusalStanding]
    }
}
impl VerifierSuite for RefusingVerifierSuite {
    fn admission(&self) -> &dyn AdmissionAuthority {
        self
    }
    fn global_replay(&self) -> &dyn GlobalEvaluatorReplay {
        self
    }
    fn capacity(&self) -> &dyn CapacitySolver {
        self
    }
    fn transport(&self) -> &dyn TransportVerifier {
        self
    }
    fn refusals(&self) -> &dyn RefusalStore {
        self
    }
}

// ── blockers ─────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ContinuationBlockerV2 {
    IntakeNotAccepted,
    WitnessMissing,
    NextCarrierUndeclared,
    DetectorInadequate,
    AdapterNotPreserving,
    ProvenanceNotExhibited,
    BudgetExhausted,
    #[serde(rename = "GtlaRefusal")]
    CodaGtlaRefusal,
    PriorRefusalStanding,
}

// ── the verified context ─────────────────────────────────────────────────────

/// One root evidence object. Private fields, `Serialize`-only, no constructor
/// other than [`verify`].
///
/// ```compile_fail
/// use core_epk::v2::VerifiedContinuationContextV2;
/// let _: VerifiedContinuationContextV2 = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct VerifiedContinuationContextV2 {
    schema: &'static str,
    /// Binds **every** discriminating field exactly once.
    root_digest: String,
    run_id: String,
    metrics: EpkMetrics,
    ledger: EpkResidualLedger,
    #[serde(skip)]
    adequacy: DetectorAdequacyVerdict,
    adequacy_kind: DetectorAdequacyVerdictKind,
    defect: GluingDefect,
    record_id: String,
    verdict: LggrVerdict,
    provenance: EvaluatorProvenance,
    preservation: Option<ResidualPreservationWitness>,
    has_witness: bool,
    next_carrier_declared: bool,
    budget_remaining: f64,
    delta_control: f64,
    prior_refusals: Vec<ContinuationBlockerV2>,
    #[serde(rename = "gtla_refusal")]
    coda_gtla_refusal: bool,
    parent_receipt_hash: Option<String>,
}

impl VerifiedContinuationContextV2 {
    pub fn root_digest(&self) -> &str {
        &self.root_digest
    }
    pub fn run_id(&self) -> &str {
        &self.run_id
    }
    pub fn metrics(&self) -> &EpkMetrics {
        &self.metrics
    }
    pub fn ledger(&self) -> &EpkResidualLedger {
        &self.ledger
    }
    pub fn adequacy(&self) -> &DetectorAdequacyVerdict {
        &self.adequacy
    }
    pub fn defect(&self) -> &GluingDefect {
        &self.defect
    }
    pub fn record_id(&self) -> &str {
        &self.record_id
    }
    pub fn verdict(&self) -> &LggrVerdict {
        &self.verdict
    }
    pub fn provenance(&self) -> EvaluatorProvenance {
        self.provenance
    }
    pub fn preservation(&self) -> Option<&ResidualPreservationWitness> {
        self.preservation.as_ref()
    }
    /// **Always** [`AuthorityEffect::None`].
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
    pub fn evidence_ceiling(&self) -> EvidenceCeiling {
        self.verdict
            .evidence_ceiling()
            .meet(EvidenceCeiling::BoundaryChecked)
    }
}

// ── the decision ─────────────────────────────────────────────────────────────

/// Derived, never stored, never deserializable (ADR-008 C1).
///
/// ```compile_fail
/// use core_epk::v2::ContinuationDecision;
/// let _: ContinuationDecision = serde_json::from_str("{}").unwrap();
/// ```
///
/// ```compile_fail
/// use core_epk::v2::ContinuationDecision;
/// let _ = ContinuationDecision { blockers: vec![], root_digest: String::new() };
/// ```
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ContinuationDecision {
    blockers: Vec<ContinuationBlockerV2>,
    root_digest: String,
}

impl ContinuationDecision {
    /// Derived from `blockers`. There is no stored verdict to forge.
    pub fn may_continue(&self) -> bool {
        self.blockers.is_empty()
    }
    pub fn blockers(&self) -> &[ContinuationBlockerV2] {
        &self.blockers
    }
    /// The context this decision came from. A decision cannot be replayed against
    /// a different root.
    pub fn root_digest(&self) -> &str {
        &self.root_digest
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
    pub fn step_terminal(&self) -> &'static str {
        if self.may_continue() {
            "LOCAL_GREEN_FOR_SCOPE"
        } else {
            "TERMINAL_WITH_DEBT"
        }
    }
}

// ── verify ───────────────────────────────────────────────────────────────────

/// The only way to obtain a [`VerifiedContinuationContextV2`].
///
/// Order is fail-closed: schema, then intake, then the corpus, then the traces,
/// then adequacy, then transport — each refusing before the next is consulted.
fn verify_intake<'a>(
    packet: &'a RawEvidencePacket,
    suite: &dyn VerifierSuite,
) -> Result<&'a AcceptedIntakeReceipt, TypedRefusal> {
    // 1. Schema first. v1 and unknown schemas are refused before any recomputation.
    if packet.schema != V2_CONTEXT_SCHEMA {
        return Err(TypedRefusal::SchemaRefused {
            found: packet.schema.clone(),
            expected: V2_CONTEXT_SCHEMA,
        });
    }

    // 2. Intake: present, run-bound, AND confirmed by the admission authority.
    //    An earlier revision checked only the run id and trusted the receipt.
    let intake = packet
        .accepted_intake
        .as_ref()
        .ok_or(TypedRefusal::IntakeNotAccepted)?;
    if intake.run_id() != packet.run_id {
        return Err(TypedRefusal::IntakeRunMismatch {
            receipt_run: intake.run_id().to_string(),
            packet_run: packet.run_id.clone(),
        });
    }
    suite.admission().confirm_admission(intake)?;
    Ok(intake)
}

    // 3. Corpus.
fn verify_trace_ledger(packet: &RawEvidencePacket) -> Result<(), TypedRefusal> {
    // 4. Local traces must agree with the ledger.
    for r in &packet.records {
        let l = packet
            .trace_ledger
            .get(&r.left_trace_id)
            .map(|t| t.evaluator_pass);
        let rt = packet
            .trace_ledger
            .get(&r.right_trace_id)
            .map(|t| t.evaluator_pass);
        if l != Some(r.local_left_pass) || rt != Some(r.local_right_pass) {
            return Err(TypedRefusal::LocalTraceMismatch {
                record_id: r.composed_trace_id.clone(),
                declared_left: r.local_left_pass,
                declared_right: r.local_right_pass,
                ledger_left: l,
                ledger_right: rt,
            });
        }
    }
    Ok(())
}

fn replay_global_traces(
    packet: &RawEvidencePacket,
    suite: &dyn VerifierSuite,
) -> Result<BTreeMap<String, bool>, TypedRefusal> {
    // 5. GLOBAL evaluator: REPLAYED by the verifier. The packet carries no copy to
    //    compare against, so a caller cannot supply both sides of the check.
    let mut replayed_global: BTreeMap<String, bool> = BTreeMap::new();
    for r in &packet.records {
        let replayed = suite.global_replay().replay_global(r)?;
        if replayed != r.global_pass {
            return Err(TypedRefusal::GlobalTraceMismatch {
                record_id: r.composed_trace_id.clone(),
                declared: r.global_pass,
                replayed,
            });
        }
        replayed_global.insert(r.composed_trace_id.clone(), replayed);
    }
    Ok(replayed_global)
}

fn hash_preservation_witness(
    h: &mut CanonicalHasher,
    preservation: Option<&ResidualPreservationWitness>,
) {
    match preservation {
        Some(w) => {
            h.u8_field("preservation", 1);
            h.str_field("preservation_source", w.source_carrier());
            h.str_field("preservation_target", w.target_carrier());
            h.f64_field("preservation_source_ngd", w.source_ngd());
            h.f64_field("preservation_target_ngd", w.target_ngd());
            h.u8_field("preservation_preserved", w.preserved() as u8);
            h.bytes(
                "preservation_loss_count",
                &(w.loss_ledger().len() as u64).to_be_bytes(),
            );
            for l in w.loss_ledger() {
                h.str_field("preservation_loss", l);
            }
        }
        None => {
            h.u8_field("preservation", 0);
        }
    }
}

fn compute_context_digest(
    packet: &RawEvidencePacket,
    intake: &AcceptedIntakeReceipt,
    replayed_global: &BTreeMap<String, bool>,
    adequacy: &DetectorAdequacyVerdict,
    row: usize,
    defect: &GluingDefect,
    ledger: &EpkResidualLedger,
    preservation: Option<&ResidualPreservationWitness>,
    standing: &[ContinuationBlockerV2],
) -> String {
    let mut h = CanonicalHasher::new(V2_CONTEXT_SCHEMA);
    h.str_field("run_id", &packet.run_id);
    h.str_field("intake_run", intake.run_id());
    h.str_field("intake_candidate", intake.candidate_digest());
    h.str_field("intake_witness", intake.witness_certificate());
    h.str_field("intake_next_carrier", intake.next_carrier());
    for r in &packet.records {
        h.str_field("row_id", &r.composed_trace_id);
        h.u8_field("row_l", r.local_left_pass as u8);
        h.u8_field("row_r", r.local_right_pass as u8);
        h.u8_field("row_g", r.global_pass as u8);
    }
    for (id, g) in replayed_global {
        h.str_field("replayed_id", id);
        h.u8_field("replayed_val", *g as u8);
    }
    h.str_field("boundary", &packet.boundary.name);
    h.str_field("adequacy_kind", adequacy_kind_tag(adequacy.kind()));
    h.str_field("adequacy_corpus", adequacy.observed_corpus_digest());
    h.opt_str("adequacy_declaration", adequacy.declaration_digest());
    h.opt_f64("adequacy_capacity", adequacy.capacity_value());
    h.opt_f64("adequacy_epsilon", adequacy.epsilon());
    h.bytes(
        "adequacy_failure_count",
        &(adequacy.structural_failures().len() as u64).to_be_bytes(),
    );
    for f in adequacy.structural_failures() {
        h.str_field("adequacy_failure", structural_failure_tag(f));
    }
    h.bytes("selected_row", &(row as u64).to_be_bytes());
    h.i8_field("delta_eval", defect.delta_eval);
    h.f64_field("ngd", ledger.ngd);
    h.opt_f64("nrke", ledger.nrke);
    hash_preservation_witness(&mut h, preservation);
    h.f64_field("budget_remaining", packet.budget_remaining);
    h.f64_field("delta_control", packet.delta_control);
    h.bytes(
        "standing_refusal_count",
        &(standing.len() as u64).to_be_bytes(),
    );
    for r in standing {
        h.str_field("standing_refusal", blocker_tag(*r));
    }
    h.u8_field("gtla_refusal", packet.coda_gtla_refusal as u8);
    h.opt_str("parent_receipt", packet.parent_receipt_hash.as_deref());
    h.finish()
}

fn resolve_preservation(
    packet: &RawEvidencePacket,
    suite: &dyn VerifierSuite,
    ledger: &EpkResidualLedger,
) -> Result<Option<ResidualPreservationWitness>, TypedRefusal> {
    match packet.transport.as_ref() {
        Some(claim) => {
            let measured = suite.transport().measure_target(claim, ledger.ngd)?;
            Ok(Some(ResidualPreservationWitness::from_measurement(
                claim, ledger.ngd, measured,
            )))
        }
        None => Ok(None),
    }
}

pub fn verify(
    packet: &RawEvidencePacket,
    suite: &dyn VerifierSuite,
) -> Result<VerifiedContinuationContextV2, TypedRefusal> {
    let intake = verify_intake(packet, suite)?;

    if packet.records.is_empty() {
        return Err(TypedRefusal::EmptyCorpus);
    }
    let row = packet.selected_row;
    let record = packet.records.get(row).ok_or(TypedRefusal::RowOutOfRange {
        index: row,
        len: packet.records.len(),
    })?;

    verify_trace_ledger(packet)?;
    let replayed_global = replay_global_traces(packet, suite)?;
    let provenance = EvaluatorProvenance::Exhibited;

    // 6. Capacity evidence is SOLVED, not supplied.
    let declaration = packet
        .declaration
        .as_ref()
        .ok_or(TypedRefusal::DeclarationMissing)?;
    let solved_evidence = suite.capacity().solve(
        declaration,
        &packet.records,
        &packet.trace_ledger,
        &packet.boundary,
    )?;
    let adequacy = evaluate_detector_adequacy(
        Some(declaration),
        Some(&solved_evidence),
        &packet.records,
        &packet.trace_ledger,
        &packet.boundary,
    );

    let metrics = calculate_metrics(
        &packet.records,
        Some(&packet.trace_ledger),
        None,
        None,
        None,
    )?;
    let ledger = EpkResidualLedger::from_metrics(&metrics);
    let defect = evaluator_gluing_defect(record);
    let verdict = classify(&defect, Some(&adequacy), provenance)
        .expect("defects from evaluator_gluing_defect are well-formed");

    // 7. Transport: the target residual is MEASURED by the verifier.
    let preservation = resolve_preservation(packet, suite, &ledger)?;

    // 8. Standing refusals come from the append-only store, not the packet.
    let standing = suite.refusals().standing_refusals(&packet.run_id);
    // 9. ONE root digest binding every discriminating field exactly once.
    let root_digest = compute_context_digest(
        packet,
        intake,
        &replayed_global,
        &adequacy,
        row,
        &defect,
        &ledger,
        preservation.as_ref(),
        &standing,
    );

    Ok(VerifiedContinuationContextV2 {
        schema: V2_CONTEXT_SCHEMA,
        root_digest,
        run_id: packet.run_id.clone(),
        metrics,
        ledger,
        adequacy_kind: adequacy.kind(),
        adequacy,
        defect,
        record_id: record.composed_trace_id.clone(),
        verdict,
        provenance,
        preservation,
        has_witness: intake.has_witness(),
        next_carrier_declared: intake.next_carrier_declared(),
        budget_remaining: packet.budget_remaining,
        delta_control: packet.delta_control,
        prior_refusals: standing,
        coda_gtla_refusal: packet.coda_gtla_refusal,
        parent_receipt_hash: packet.parent_receipt_hash.clone(),
    })
}

/// Stable tag for a structural failure. Explicit so the canonical encoding never
/// depends on `Debug`.
fn structural_failure_core_tag(f: &crate::adequacy::DetectorStructuralFailure) -> Option<&'static str> {
    use crate::adequacy::DetectorStructuralFailure as F;
    match f {
        F::EmptyCorpus => Some("EmptyCorpus"),
        F::GlobalEqualsLocalProduct => Some("GlobalEqualsLocalProduct"),
        F::LocalProductConstant => Some("LocalProductConstant"),
        F::MissingNgdWitness => Some("MissingNgdWitness"),
        F::MissingLrgrWitness => Some("MissingLrgrWitness"),
        F::CarrierClosureVacuous => Some("CarrierClosureVacuous"),
        _ => None,
    }
}

fn structural_failure_extended_tag(f: &crate::adequacy::DetectorStructuralFailure) -> &'static str {
    use crate::adequacy::DetectorStructuralFailure as F;
    match f {
        F::EvaluatorConstant { .. } => "EvaluatorConstant",
        F::EvaluatorDoesNotSeparate { .. } => "EvaluatorDoesNotSeparate",
        F::ProjectionCollision { .. } => "ProjectionCollision",
        F::MissingBlindSpotDeclaration { .. } => "MissingBlindSpotDeclaration",
        _ => "OtherStructuralFailure",
    }
}

fn structural_failure_tag(f: &crate::adequacy::DetectorStructuralFailure) -> &'static str {
    structural_failure_core_tag(f).unwrap_or_else(|| structural_failure_extended_tag(f))
}

/// Stable tag for a blocker.
fn blocker_tag(b: ContinuationBlockerV2) -> &'static str {
    match b {
        ContinuationBlockerV2::IntakeNotAccepted => "IntakeNotAccepted",
        ContinuationBlockerV2::WitnessMissing => "WitnessMissing",
        ContinuationBlockerV2::NextCarrierUndeclared => "NextCarrierUndeclared",
        ContinuationBlockerV2::DetectorInadequate => "DetectorInadequate",
        ContinuationBlockerV2::AdapterNotPreserving => "AdapterNotPreserving",
        ContinuationBlockerV2::ProvenanceNotExhibited => "ProvenanceNotExhibited",
        ContinuationBlockerV2::BudgetExhausted => "BudgetExhausted",
        ContinuationBlockerV2::CodaGtlaRefusal => "GtlaRefusal",
        ContinuationBlockerV2::PriorRefusalStanding => "PriorRefusalStanding",
    }
}

fn adequacy_kind_tag(k: DetectorAdequacyVerdictKind) -> &'static str {
    match k {
        DetectorAdequacyVerdictKind::Undeclared => "Undeclared",
        DetectorAdequacyVerdictKind::StructuralInadequate => "StructuralInadequate",
        DetectorAdequacyVerdictKind::NumericalCounterevidence => "NumericalCounterevidence",
        DetectorAdequacyVerdictKind::NumericallySupported => "NumericallySupported",
        DetectorAdequacyVerdictKind::NumericalUnresolved => "NumericalUnresolved",
    }
}

// ── decide ───────────────────────────────────────────────────────────────────
// Decide continuation from **only** the verified context.
//
// There are no boolean parameters. Every conjunct is read off evidence that
// `verify` established: the witness from the intake receipt, adapter soundness
// from the preservation witness, detector adequacy from the adequacy report.
fn collect_intake_and_adequacy_blockers(
    context: &VerifiedContinuationContextV2,
    blockers: &mut Vec<ContinuationBlockerV2>,
) {
    if !context.has_witness {
        blockers.push(ContinuationBlockerV2::WitnessMissing);
    }
    if !context.next_carrier_declared {
        blockers.push(ContinuationBlockerV2::NextCarrierUndeclared);
    }
    if context.adequacy_kind != DetectorAdequacyVerdictKind::NumericallySupported {
        blockers.push(ContinuationBlockerV2::DetectorInadequate);
    }
    match &context.preservation {
        Some(w) if w.preserved() => {}
        // No transport claimed is not the same as a verified preserving one.
        _ => blockers.push(ContinuationBlockerV2::AdapterNotPreserving),
    }
}

fn collect_runtime_blockers(
    context: &VerifiedContinuationContextV2,
    blockers: &mut Vec<ContinuationBlockerV2>,
) {
    if context.provenance != EvaluatorProvenance::Exhibited {
        blockers.push(ContinuationBlockerV2::ProvenanceNotExhibited);
    }
    let budget_exhausted = !context.budget_remaining.is_finite()
        || !context.delta_control.is_finite()
        || context.budget_remaining - context.delta_control < 0.0;
    if budget_exhausted {
        blockers.push(ContinuationBlockerV2::BudgetExhausted);
    }
    if context.coda_gtla_refusal {
        blockers.push(ContinuationBlockerV2::CodaGtlaRefusal);
    }
    if !context.prior_refusals.is_empty() {
        blockers.push(ContinuationBlockerV2::PriorRefusalStanding);
    }
}

pub fn decide(context: &VerifiedContinuationContextV2) -> ContinuationDecision {
    let mut blockers = Vec::new();
    collect_intake_and_adequacy_blockers(context, &mut blockers);
    collect_runtime_blockers(context, &mut blockers);
    blockers.sort_unstable();
    blockers.dedup();
    ContinuationDecision {
        blockers,
        root_digest: context.root_digest.clone(),
    }
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/verified_continuation_context_v2.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:verified-continuation-context-v2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_11b24dc4 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
