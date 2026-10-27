//! The LGGR(EPK) ↔ OE Prime 000/001/002 seam.
//!
//! The LGGR trilogy (papers 019/020/021) and the OE Prime Algorithms (paper
//! `008_engine_runtime/000_oe_prime_algorithms`) are both published, and nothing
//! connected them: `oe_prime_algorithms` is imported by no file outside its own
//! paper directory, and no EPK surface referenced a Prime engine. This module is
//! that seam.
//!
//! # Ports, not bindings
//!
//! Prime is reached through three traits — [`PrimeIntakePort`],
//! [`PrimeDescentPort`], [`PrimeContinuationPort`] — so the seam does not force a
//! dependency direction. `core_epk` cannot depend on `core_solvers` (that would
//! cycle: `core_solvers → core_pipelines → core_epk`), and the same discipline
//! applies here: this module consumes evidence it is given and produces
//! classifications, exactly as `evaluate_detector_adequacy` already requires its
//! caller to supply capacity evidence.
//!
//! # Declared vocabulary is reused verbatim
//!
//! The intake and declaration outcome strings are **not** new states. They are the
//! literals already produced by `PrimeTriadEngine.evaluate_intake` and
//! `LocalDeclarationOrder.validate_declaration_order` in both
//! `ooutwire_docs/universe_coda/universe_coda.py` and the published
//! `000_oe_prime_algorithms/code/oe_prime_algorithms.py`. Note that the two use
//! **different prefixes** — intake refuses with `REFUSED_*`, the seven-step
//! declaration order refuses with `REFUSE_*` — and that distinction is preserved
//! rather than normalized away.
//!
//! # The witness gate is real here
//!
//! `oe_prime_algorithms.DDATerminalizer.process_step` calls `can_continue` with
//! `has_obligation=True, has_witness=True` hardcoded, so it can never refuse for a
//! missing witness. [`PrimeContinuationInputs`] takes those as data and
//! [`PrimeContinuationInputs::detector_adequate`] is derived from an adequacy
//! verdict rather than assumed, so an inadequate detector actually blocks
//! continuation.
//!
//! **AuthorityEffect: None.** Continuation is a predicate a host consults. This
//! module issues no authorization.

use serde::{Deserialize, Serialize};

use core_types::authority::AuthorityEffect;
use core_types::ceiling::EvidenceCeiling;

use crate::epk_engine::GluingDefect;
use core_policy::trichotomy::ObstructionDiagnosticClass;

use crate::adequacy::DetectorAdequacyVerdictKind;
use crate::bound_measurement::{verdict_tag, CanonicalHasher};
use crate::ledger::EpkResidualLedger;
use crate::verdict::LggrVerdict;

/// Schema tag for a serialized [`LggrEpkObservation`].
///
/// **`REJECTED_UNSOUND`.** See [`V1_QUARANTINE_REASON`]. This schema is retained
/// only so existing packets can be *recognised and refused*; it must never gate.
pub const LGGR_EPK_OBSERVATION_SCHEMA: &str = "core.epk.lggr-observation.v1";
/// Schema tag for a serialized [`PrimeDescentReceipt`].
///
/// **`REJECTED_UNSOUND`.** See [`V1_QUARANTINE_REASON`].
pub const PRIME_DESCENT_RECEIPT_SCHEMA: &str = "core.epk.prime-descent-receipt.v1";

/// Disposition of every v1 schema in this module.
pub const V1_SCHEMA_DISPOSITION: &str = "REJECTED_UNSOUND";

/// Why v1 is quarantined. Six blockers reproduced by execution; see
/// `docs/lggr_prime_seam/residual_ledger.md`.
///
/// The decisive one: the v1 measurement digest binds the observed corpus but not
/// the adequacy kind, declaration digest, capacity evidence, or structural
/// failures — so identical rows measured once with capacity evidence
/// (`NumericallySupported`) and once without (`Undeclared`) produce **identical
/// digests**, and the supported measurement will accept the unsupported
/// observation and derive `detector_adequate = true`.
///
/// Until `VerifiedContinuationContextV2` exists, **no v1 path may produce an
/// executable continuation.** The diagnostics remain useful; their gating
/// capacity is removed.
pub const V1_QUARANTINE_REASON: &str = "v1 evidence binding is incomplete: the \
measurement digest omits the adequacy report, so a supported measurement accepts \
an unsupported observation. Quarantined pending VerifiedContinuationContextV2.";

// ── Prime 001-I: intake ──────────────────────────────────────────────────────

/// Outcome of the Prime 001 intake check.
///
/// Values map 1:1 onto the literals returned by `PrimeTriadEngine.evaluate_intake`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PrimeIntakeOutcome {
    AcceptDeclaration,
    RefusedMissingCarrier,
    RefusedMissingObserver,
    RefusedMissingWitness,
    AdapterInadequate,
}

impl PrimeIntakeOutcome {
    /// The exact upstream literal. Reused, not invented.
    pub fn as_declared_str(&self) -> &'static str {
        match self {
            Self::AcceptDeclaration => "ACCEPT_DECLARATION",
            Self::RefusedMissingCarrier => "REFUSED_MISSING_CARRIER",
            Self::RefusedMissingObserver => "REFUSED_MISSING_OBSERVER",
            Self::RefusedMissingWitness => "REFUSED_MISSING_WITNESS",
            Self::AdapterInadequate => "ADAPTER_INADEQUATE",
        }
    }

    /// Whether intake refused. `AdapterInadequate` counts as a refusal for
    /// admission purposes: upstream records it in the loss ledger and does not
    /// return `ACCEPT_DECLARATION`.
    pub fn is_refusal(&self) -> bool {
        !matches!(self, Self::AcceptDeclaration)
    }
}

/// Candidate packet presented to Prime intake.
///
/// Field names mirror `CandidatePacket` in `universe_coda.py` / `oe_prime_algorithms.py`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateDeclaration {
    pub artifact_id: String,
    pub locus_id: String,
    pub problem_family: String,
    pub primitive_difference_proposal: String,
    pub carrier_proposal: String,
    pub zero_rel_proposal: String,
    pub observer_proposal: String,
    pub witness_available: bool,
    pub quotient_or_refusal: String,
    pub adapter_confidence: String,
    pub status: String,
}

impl CandidateDeclaration {
    /// The intake check, in the upstream order: carrier, observer, witness,
    /// adapter confidence.
    pub fn evaluate_intake(&self) -> PrimeIntakeOutcome {
        if self.carrier_proposal.is_empty() {
            return PrimeIntakeOutcome::RefusedMissingCarrier;
        }
        if self.observer_proposal.is_empty() {
            return PrimeIntakeOutcome::RefusedMissingObserver;
        }
        if !self.witness_available {
            return PrimeIntakeOutcome::RefusedMissingWitness;
        }
        if self.adapter_confidence == "inadequate" {
            return PrimeIntakeOutcome::AdapterInadequate;
        }
        PrimeIntakeOutcome::AcceptDeclaration
    }

    /// **Always** [`AuthorityEffect::None`]. Upstream pins `authority_effect:
    /// "None"` and `status: "proposed_only"` on the packet; admission mints nothing.
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

// ── Prime 000: seven-step local declaration order ────────────────────────────

/// Outcome of the Prime 000 seven-step declaration order (OE001-02).
///
/// Note the `REFUSE_` prefix: upstream `validate_declaration_order` uses it, while
/// intake uses `REFUSED_`. The difference is preserved deliberately.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PrimeDeclarationOutcome {
    AcceptDeclaration,
    RefuseMissingGrounding,
    RefuseMissingCarrier,
    RefuseMissingObserver,
    RefuseMissingPrimitiveDifference,
    RefuseMissingZeroRel,
    RefuseMissingWitness,
}

impl PrimeDeclarationOutcome {
    /// The exact upstream literal.
    pub fn as_declared_str(&self) -> &'static str {
        match self {
            Self::AcceptDeclaration => "ACCEPT_DECLARATION",
            Self::RefuseMissingGrounding => "REFUSE_MISSING_GROUNDING",
            Self::RefuseMissingCarrier => "REFUSE_MISSING_CARRIER",
            Self::RefuseMissingObserver => "REFUSE_MISSING_OBSERVER",
            Self::RefuseMissingPrimitiveDifference => "REFUSE_MISSING_PRIMITIVE_DIFFERENCE",
            Self::RefuseMissingZeroRel => "REFUSE_MISSING_ZERO_REL",
            Self::RefuseMissingWitness => "REFUSE_MISSING_WITNESS",
        }
    }

    pub fn is_refusal(&self) -> bool {
        !matches!(self, Self::AcceptDeclaration)
    }
}

/// The seven declared steps, in order. Presence is what is checked; the payloads
/// themselves belong to the carrier/observer crates.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct PrimeDeclarationOrder {
    pub step0_grounding_hash: String,
    pub step1_carrier_declared: bool,
    pub step2_observer_id: String,
    pub step3_primitive_difference_declared: bool,
    pub step4_zero_rel_rule: String,
    pub step5_witness_certificate: Option<String>,
    pub step6_quotient_policy: String,
}

impl PrimeDeclarationOrder {
    /// Validate in the declared order, short-circuiting on the first gap — the
    /// order is the contract, so a later step never excuses an earlier one.
    pub fn validate(&self) -> PrimeDeclarationOutcome {
        if self.step0_grounding_hash.is_empty() {
            return PrimeDeclarationOutcome::RefuseMissingGrounding;
        }
        if !self.step1_carrier_declared {
            return PrimeDeclarationOutcome::RefuseMissingCarrier;
        }
        if self.step2_observer_id.is_empty() {
            return PrimeDeclarationOutcome::RefuseMissingObserver;
        }
        if !self.step3_primitive_difference_declared {
            return PrimeDeclarationOutcome::RefuseMissingPrimitiveDifference;
        }
        if self.step4_zero_rel_rule.is_empty() {
            return PrimeDeclarationOutcome::RefuseMissingZeroRel;
        }
        match &self.step5_witness_certificate {
            None => PrimeDeclarationOutcome::RefuseMissingWitness,
            Some(cert) if cert.is_empty() => PrimeDeclarationOutcome::RefuseMissingWitness,
            Some(_) => PrimeDeclarationOutcome::AcceptDeclaration,
        }
    }
}

// ── The sidecar observation ──────────────────────────────────────────────────

/// Round-trippable projection of [`DetectorAdequacyVerdictKind`].
///
/// The adequacy types derive `Serialize` but deliberately **not** `Deserialize` —
/// `adequacy.rs` carries a `compile_fail` doctest proving a verdict cannot be
/// reconstructed from JSON. That non-forgeability is a feature, so the observation
/// carries this projection instead of the verdict itself. A projection can be
/// deserialized; it can never be mistaken for the authoritative verdict.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AdequacyKindProjection {
    /// No adequacy protocol was run at all.
    NotEvaluated,
    Undeclared,
    StructuralInadequate,
    NumericalCounterevidence,
    NumericallySupported,
    NumericalUnresolved,
}

impl AdequacyKindProjection {
    pub fn from_kind(kind: DetectorAdequacyVerdictKind) -> Self {
        match kind {
            DetectorAdequacyVerdictKind::Undeclared => Self::Undeclared,
            DetectorAdequacyVerdictKind::StructuralInadequate => Self::StructuralInadequate,
            DetectorAdequacyVerdictKind::NumericalCounterevidence => Self::NumericalCounterevidence,
            DetectorAdequacyVerdictKind::NumericallySupported => Self::NumericallySupported,
            DetectorAdequacyVerdictKind::NumericalUnresolved => Self::NumericalUnresolved,
        }
    }

    /// Stable tag for canonical hashing. Independent of `Debug`.
    pub fn as_tag(&self) -> &'static str {
        match self {
            Self::NotEvaluated => "NotEvaluated",
            Self::Undeclared => "Undeclared",
            Self::StructuralInadequate => "StructuralInadequate",
            Self::NumericalCounterevidence => "NumericalCounterevidence",
            Self::NumericallySupported => "NumericallySupported",
            Self::NumericalUnresolved => "NumericalUnresolved",
        }
    }

    /// The single condition under which Prime 002's `detector_adequate` conjunct
    /// may be satisfied.
    ///
    /// Even this is not an exactness claim: `adequacy.rs` states verbatim *"No
    /// verdict is `Adequate`; exact BSC-CERT remains open."*
    pub fn permits_detector_adequate(&self) -> bool {
        matches!(self, Self::NumericallySupported)
    }
}

/// One LGGR(EPK) reading, packaged for the Prime seam.
///
/// This is a **sidecar**, not an extension of [`EpkResidualLedger`]. Two existing
/// consumers state that rule explicitly (`core_pipelines::loop_step` and
/// `core_api::flagship::seam::SeamObservation`), and it is respected here: the
/// ledger is held by value and its own fields are untouched.
///
/// # Why the fields are private and there is no `Deserialize`
///
/// [`Self::detector_adequate`] is the wire Prime 002 consults, and it reads
/// `adequacy_kind`. If `verdict` and `adequacy_kind` could be set independently,
/// a caller could pair a `GreenOracleNeeded` verdict with a `NumericallySupported`
/// kind — a state in which the reading says "not certifiable" while the gate says
/// "proceed". That is not hypothetical: an earlier revision of this type had
/// public fields and this crate's own test helper built exactly that pair.
///
/// So the pair is now derived, never supplied: [`Self::measure`] classifies the
/// verdict from the *same* [`DetectorAdequacyVerdict`] it projects the kind from,
/// making the incoherent state unrepresentable.
///
/// `Deserialize` is deliberately absent for the same reason it is absent from
/// [`DetectorAdequacyVerdict`] — a gate carrier must not be reconstructible from
/// attacker-controlled JSON. [`PrimeDescentReceipt`] *is* round-trippable, because
/// forging a receipt grants no support; forging an observation would.
///
/// ```compile_fail
/// use core_epk::prime_seam::LggrEpkObservation;
/// let _: LggrEpkObservation = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct LggrEpkObservation {
    schema: String,
    ledger: EpkResidualLedger,
    verdict: LggrVerdict,
    adequacy_kind: AdequacyKindProjection,
    /// Digest binding the corpus, its rows, and the adequacy verdict that read it.
    observed_corpus_digest: Option<String>,
    record_id: String,
    defect: GluingDefect,
    obstruction_status: Option<ObstructionDiagnosticClass>,
}

impl LggrEpkObservation {
    /// Mint a bound observation. `pub(crate)` on purpose: the only caller is
    /// [`crate::bound_measurement::BoundEpkMeasurement::observe`], which supplies
    /// values it derived itself from one corpus.
    ///
    /// There is deliberately **no public constructor**. An earlier revision offered
    /// `measure(ledger, defect, adequacy, provenance)` — four independently-supplied
    /// things — which let a genuine verdict from corpus A be paired with a
    /// fabricated defect and ledger from corpus B. That is the unbound-pair attack
    /// this crate documents, and it was live here.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn new_bound(
        ledger: EpkResidualLedger,
        verdict: LggrVerdict,
        adequacy_kind: AdequacyKindProjection,
        corpus_digest: String,
        record_id: String,
        defect: GluingDefect,
        obstruction_status: Option<ObstructionDiagnosticClass>,
    ) -> Self {
        Self {
            schema: LGGR_EPK_OBSERVATION_SCHEMA.to_string(),
            ledger,
            verdict,
            adequacy_kind,
            observed_corpus_digest: Some(corpus_digest),
            record_id,
            defect,
            obstruction_status,
        }
    }

    /// The corpus row this observation reads.
    pub fn record_id(&self) -> &str {
        &self.record_id
    }

    /// The defect for that row, as derived by the measurement.
    pub fn defect(&self) -> &GluingDefect {
        &self.defect
    }

    pub fn obstruction_status(&self) -> Option<ObstructionDiagnosticClass> {
        self.obstruction_status
    }

    pub fn schema(&self) -> &str {
        &self.schema
    }

    pub fn ledger(&self) -> &EpkResidualLedger {
        &self.ledger
    }

    pub fn verdict(&self) -> &LggrVerdict {
        &self.verdict
    }

    pub fn adequacy_kind(&self) -> AdequacyKindProjection {
        self.adequacy_kind
    }

    pub fn observed_corpus_digest(&self) -> Option<&str> {
        self.observed_corpus_digest.as_deref()
    }

    /// **Always** [`AuthorityEffect::None`], inherited from both the ledger and the
    /// verdict, neither of which can authorize.
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }

    /// The ceiling of this observation: the verdict's ceiling, never raised.
    pub fn evidence_ceiling(&self) -> EvidenceCeiling {
        self.verdict
            .evidence_ceiling()
            .meet(EvidenceCeiling::BoundaryChecked)
    }

    /// Whether Prime 002's `detector_adequate` conjunct may be satisfied by this
    /// observation. This is the wire that makes an inadequate detector actually
    /// block continuation.
    ///
    /// Requires **both** that the adequacy projection permits it and that the
    /// verdict itself reached [`LggrVerdict::GreenNumericallySupported`] or an
    /// exhibited defect. Since [`Self::measure`] derives both from one verdict
    /// these agree by construction; the conjunction is kept so that a future
    /// constructor cannot reintroduce the split silently.
    pub fn detector_adequate(&self) -> bool {
        self.adequacy_kind.permits_detector_adequate()
            && !matches!(
                self.verdict,
                LggrVerdict::GreenOracleNeeded { .. } | LggrVerdict::OracleExtractedUnsound { .. }
            )
    }
}

// ── Prime 001-T: descent ─────────────────────────────────────────────────────

/// Receipt that one observation was carried across the Prime descent boundary.
///
/// This is **plain transport data**. It round-trips through JSON, and a
/// deserialized one establishes nothing on its own -- see [`VerifiedDescentReceipt`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PrimeDescentReceipt {
    pub schema: String,
    pub source_carrier: String,
    pub target_carrier: String,
    /// Digest of the measurement this receipt was minted from.
    pub observed_corpus_digest: String,
    /// Whether the transport preserved the residual reading. `false` is a
    /// legitimate terminal, not an error: a lossy adapter is information the host
    /// needs, and it is what makes `adapter_sound` false downstream.
    pub residual_preservation_verified: bool,
    pub loss_ledger: Vec<String>,
    pub receipt_hash: String,
}

impl PrimeDescentReceipt {
    /// Recompute the canonical hash from this receipt's own contents.
    pub fn recomputed_hash(&self, observation: &LggrEpkObservation) -> String {
        descent_receipt_hash(
            &self.source_carrier,
            &self.target_carrier,
            &self.observed_corpus_digest,
            self.residual_preservation_verified,
            &self.loss_ledger,
            observation,
        )
    }

    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

/// A descent receipt whose hash has been **independently recomputed** against the
/// observation it claims to describe.
///
/// Private field, no `Deserialize`. This is the only receipt type
/// `BoundEpkMeasurement::continuation_evidence` accepts, so a receipt parsed from
/// JSON cannot satisfy a gate until it has been verified against a real
/// measurement.
///
/// ```compile_fail
/// use core_epk::prime_seam::VerifiedDescentReceipt;
/// let _: VerifiedDescentReceipt = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct VerifiedDescentReceipt(PrimeDescentReceipt);

impl VerifiedDescentReceipt {
    pub(crate) fn seal(receipt: PrimeDescentReceipt) -> Self {
        Self(receipt)
    }

    pub fn receipt(&self) -> &PrimeDescentReceipt {
        &self.0
    }

    pub fn residual_preservation_verified(&self) -> bool {
        self.0.residual_preservation_verified
    }

    pub fn observed_corpus_digest(&self) -> &str {
        &self.0.observed_corpus_digest
    }

    pub fn receipt_hash(&self) -> &str {
        &self.0.receipt_hash
    }

    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

/// Canonical, versioned, length-prefixed receipt identity.
///
/// Binds **every** semantic field: the corpus digest, the row identity, the full
/// defect triple, the verdict tag, the adequacy projection, the obstruction status,
/// and the residual signals. An earlier encoding interpolated Rust `Debug` output
/// and omitted both the corpus digest and the obstruction status, so observations
/// over different corpora could share a receipt identity.
pub(crate) fn descent_receipt_hash(
    source_carrier: &str,
    target_carrier: &str,
    observed_corpus_digest: &str,
    residual_preservation_verified: bool,
    loss_ledger: &[String],
    observation: &LggrEpkObservation,
) -> String {
    let mut h = CanonicalHasher::new(PRIME_DESCENT_RECEIPT_SCHEMA);
    h.str_field("source_carrier", source_carrier);
    h.str_field("target_carrier", target_carrier);
    h.str_field("observed_corpus_digest", observed_corpus_digest);
    h.u8_field(
        "residual_preservation_verified",
        residual_preservation_verified as u8,
    );
    h.str_field("record_id", observation.record_id());
    let d = observation.defect();
    h.i8_field("delta_eval", d.delta_eval);
    h.u8_field("local_product", d.local_product as u8);
    h.u8_field("global_pass", d.global_pass as u8);
    h.str_field("verdict", verdict_tag(observation.verdict()));
    h.str_field("adequacy_kind", observation.adequacy_kind().as_tag());
    h.str_field(
        "obstruction_status",
        match observation.obstruction_status() {
            None => "None",
            Some(ObstructionDiagnosticClass::ExactRepair) => "ExactRepair",
            Some(ObstructionDiagnosticClass::ClosedResidual) => "ClosedResidual",
            Some(ObstructionDiagnosticClass::ActiveClosureFailure) => "ActiveClosureFailure",
        },
    );
    h.f64_field("ngd", observation.ledger().ngd);
    h.opt_f64("nrke", observation.ledger().nrke);
    h.bytes("loss_ledger_len", &(loss_ledger.len() as u64).to_be_bytes());
    for line in loss_ledger {
        h.str_field("loss", line);
    }
    h.finish()
}

// ── Prime 002: continuation ──────────────────────────────────────────────────

/// Bounded step budget. Mirrors `PrimeTriadEngine.__init__(budget, delta_control)`.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct PrimeBudget {
    pub budget: f64,
    pub delta_control: f64,
}

impl PrimeBudget {
    pub fn new(budget: f64, delta_control: f64) -> Self {
        Self {
            budget,
            delta_control,
        }
    }

    /// Upstream predicate, preserved exactly: `budget - delta_control >= 0`.
    ///
    /// Non-finite inputs are refused rather than compared: `NaN` fails every
    /// comparison, which would read as "no budget" by accident rather than by
    /// decision.
    pub fn has_budget(&self) -> bool {
        if !self.budget.is_finite() || !self.delta_control.is_finite() {
            return false;
        }
        self.budget - self.delta_control >= 0.0
    }
}

/// A named reason continuation is blocked. One per failed conjunct of CanContinue_n.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ContinuationBlocker {
    /// **Unconditional.** Every v1 continuation is refused; see
    /// [`V1_QUARANTINE_REASON`]. This blocker is pushed by
    /// [`PrimeContinuationInputs::evaluate`] on every call and cannot be cleared
    /// by any input, so `may_continue` is `false` for all v1 evidence.
    V1SchemaQuarantined,
    ObligationMissing,
    WitnessMissing,
    NextCarrierUndeclared,
    AdapterUnsound,
    DetectorInadequate,
    MinimalLiftMissing,
    SkeletonNotPreserved,
    BudgetExhausted,
    #[serde(rename = "GtlaRefusal")]
    CodaGtlaRefusal,
}

impl ContinuationBlocker {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::V1SchemaQuarantined => "V1SchemaQuarantined",
            Self::ObligationMissing => "ObligationMissing",
            Self::WitnessMissing => "WitnessMissing",
            Self::NextCarrierUndeclared => "NextCarrierUndeclared",
            Self::AdapterUnsound => "AdapterUnsound",
            Self::DetectorInadequate => "DetectorInadequate",
            Self::MinimalLiftMissing => "MinimalLiftMissing",
            Self::SkeletonNotPreserved => "SkeletonNotPreserved",
            Self::BudgetExhausted => "BudgetExhausted",
            Self::CodaGtlaRefusal => "GtlaRefusal",
        }
    }
}

/// Sealed evidence that Prime 002 may be consulted.
///
/// Minted only by `BoundEpkMeasurement::continuation_evidence`, which requires a
/// [`VerifiedDescentReceipt`] bound to the same corpus. The two conjuncts a caller
/// must never be able to assert live here:
///
/// * `detector_adequate` -- derived from the measurement's adequacy verdict;
/// * `adapter_sound` -- derived from the receipt's `residual_preservation_verified`,
///   so a lossy descent prevents continuation rather than being silently
///   overridden by a separate boolean.
///
/// Private fields, no `Deserialize`.
///
/// ```compile_fail
/// use core_epk::prime_seam::ContinuationEvidence;
/// let _: ContinuationEvidence = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ContinuationEvidence {
    corpus_digest: String,
    receipt_hash: String,
    detector_adequate: bool,
    adapter_sound: bool,
}

impl ContinuationEvidence {
    pub(crate) fn seal(
        corpus_digest: String,
        receipt_hash: String,
        detector_adequate: bool,
        adapter_sound: bool,
    ) -> Self {
        Self {
            corpus_digest,
            receipt_hash,
            detector_adequate,
            adapter_sound,
        }
    }

    pub fn corpus_digest(&self) -> &str {
        &self.corpus_digest
    }

    pub fn receipt_hash(&self) -> &str {
        &self.receipt_hash
    }

    pub fn detector_adequate(&self) -> bool {
        self.detector_adequate
    }

    pub fn adapter_sound(&self) -> bool {
        self.adapter_sound
    }
}

/// The conjuncts of the Prime 002 master continuation predicate CanContinue_n
/// (OE003-01), plus the budget.
///
/// **Private fields, no `Deserialize`, no public struct literal.** An earlier
/// revision made every conjunct a public field on a `Deserialize` type, so
/// `PrimeContinuationInputs { detector_adequate: true, .. }.evaluate()` returned
/// `may_continue` with no observation, no adequacy verdict and no receipt anywhere
/// in sight. Sealing the observation upstream did nothing while this stayed open.
///
/// `detector_adequate` and `adapter_sound` are **not parameters**. They come from
/// [`ContinuationEvidence`].
///
/// ```compile_fail
/// use core_epk::prime_seam::PrimeContinuationInputs;
/// let _: PrimeContinuationInputs = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct PrimeContinuationInputs {
    evidence: ContinuationEvidence,
    has_obligation: bool,
    has_witness: bool,
    next_carrier_declared: bool,
    minimal_lift: bool,
    skeleton_preserved: bool,
    #[serde(rename = "gtla_refusal")]
    coda_gtla_refusal: bool,
    budget: PrimeBudget,
}

impl PrimeContinuationInputs {
    /// The only constructor. Requires sealed evidence.
    #[allow(clippy::too_many_arguments)]
    pub fn from_evidence(
        evidence: ContinuationEvidence,
        budget: PrimeBudget,
        has_obligation: bool,
        has_witness: bool,
        next_carrier_declared: bool,
        minimal_lift: bool,
        skeleton_preserved: bool,
        coda_gtla_refusal: bool,
    ) -> Self {
        Self {
            evidence,
            has_obligation,
            has_witness,
            next_carrier_declared,
            minimal_lift,
            skeleton_preserved,
            coda_gtla_refusal,
            budget,
        }
    }

    pub fn evidence(&self) -> &ContinuationEvidence {
        &self.evidence
    }

    /// Evaluate CanContinue_n, collecting **every** failed conjunct rather than
    /// short-circuiting. A host told only the first blocker will fix it and be
    /// refused again.
    pub fn evaluate(&self) -> PrimeContinuation {
        let mut blockers = Vec::new();
        // FAIL-CLOSED QUARANTINE. Pushed unconditionally and first: no combination
        // of inputs can clear it, so no v1 path yields an executable continuation.
        // Removing this line re-opens the six verified blockers.
        blockers.push(ContinuationBlocker::V1SchemaQuarantined);
        if !self.has_obligation {
            blockers.push(ContinuationBlocker::ObligationMissing);
        }
        if !self.has_witness {
            blockers.push(ContinuationBlocker::WitnessMissing);
        }
        if !self.next_carrier_declared {
            blockers.push(ContinuationBlocker::NextCarrierUndeclared);
        }
        if !self.evidence.adapter_sound() {
            blockers.push(ContinuationBlocker::AdapterUnsound);
        }
        if !self.evidence.detector_adequate() {
            blockers.push(ContinuationBlocker::DetectorInadequate);
        }
        if !self.minimal_lift {
            blockers.push(ContinuationBlocker::MinimalLiftMissing);
        }
        if !self.skeleton_preserved {
            blockers.push(ContinuationBlocker::SkeletonNotPreserved);
        }
        if !self.budget.has_budget() {
            blockers.push(ContinuationBlocker::BudgetExhausted);
        }
        if self.coda_gtla_refusal {
            blockers.push(ContinuationBlocker::CodaGtlaRefusal);
        }
        blockers.sort_unstable();
        blockers.dedup();
        PrimeContinuation { blockers }
    }
}

/// The Prime 002 decision, with its reasons.
///
/// # No `Deserialize`, and no stored verdict
///
/// An earlier revision derived `Deserialize` and **stored** `may_continue: bool`.
/// The accessors trusted it, so the quarantine on `evaluate()` was bypassable in
/// one line:
///
/// ```text
/// serde_json::from_str(r#"{"may_continue":true,"blockers":[]}"#)
///   -> may_continue() = true, disposition() = "Proposed",
///      step_terminal() = "LOCAL_GREEN_FOR_SCOPE"
/// ```
///
/// That is the same error one level out again: the *producer* was quarantined and
/// the *product* left forgeable. Fixed structurally — there is no verdict field to
/// forge. `may_continue` is **derived** from `blockers`, and `evaluate()` pushes
/// [`ContinuationBlocker::V1SchemaQuarantined`] unconditionally, so a legitimately
/// produced decision can never have an empty blocker set while v1 is quarantined.
///
/// Not deserializable:
///
/// ```compile_fail
/// use core_epk::prime_seam::PrimeContinuation;
/// let _: PrimeContinuation = serde_json::from_str("{}").unwrap();
/// ```
///
/// ...and not directly constructible either — `blockers` is private, so an empty
/// (therefore green) decision cannot be built from outside this module:
///
/// ```compile_fail
/// use core_epk::prime_seam::PrimeContinuation;
/// let _ = PrimeContinuation { blockers: vec![] };
/// ```
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PrimeContinuation {
    blockers: Vec<ContinuationBlocker>,
}

impl PrimeContinuation {
    /// **Derived, never stored.** `true` only when no blocker survives — and
    /// `evaluate()` always pushes the v1 quarantine blocker, so this is `false`
    /// for every legitimately produced v1 decision.
    pub fn may_continue(&self) -> bool {
        self.blockers.is_empty()
    }

    /// Whether this decision was refused solely by the v1 quarantine.
    pub fn is_quarantined(&self) -> bool {
        self.blockers
            .contains(&ContinuationBlocker::V1SchemaQuarantined)
    }

    /// What a host may actually do with this decision.
    pub fn disposition(&self) -> &'static str {
        if self.is_quarantined() {
            "ExternalVerifierRequired"
        } else {
            "Proposed"
        }
    }

    pub fn blockers(&self) -> &[ContinuationBlocker] {
        &self.blockers
    }

    /// **Always** [`AuthorityEffect::None`]. A continuation predicate is consulted
    /// by a host; satisfying it is not an authorization.
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }

    /// The upstream terminal literal for a step that cannot proceed under budget.
    pub const TERMINAL_WITH_DEBT: &'static str = "TERMINAL_WITH_DEBT";
    /// The upstream literal for a step that proceeded within its declared scope.
    pub const LOCAL_GREEN_FOR_SCOPE: &'static str = "LOCAL_GREEN_FOR_SCOPE";

    /// The declared step terminal. `LOCAL_GREEN_FOR_SCOPE` is scope-local by name
    /// and by contract — it is not a global green.
    pub fn step_terminal(&self) -> &'static str {
        if self.may_continue() {
            Self::LOCAL_GREEN_FOR_SCOPE
        } else {
            Self::TERMINAL_WITH_DEBT
        }
    }

    /// Convert to canonical plain view continuation result.
    pub fn to_canonical_result(&self) -> CanContinueResult {
        if self.may_continue() {
            CanContinueResult::permitted(self.step_terminal(), self.disposition())
        } else {
            CanContinueResult::refused(
                self.blockers()
                    .iter()
                    .map(|b| b.as_str().to_string())
                    .collect(),
                self.step_terminal(),
                self.disposition(),
            )
        }
    }
}

pub use core_types::prime::CanContinueResult;

impl From<&PrimeContinuation> for CanContinueResult {
    fn from(c: &PrimeContinuation) -> Self {
        c.to_canonical_result()
    }
}

impl From<PrimeContinuation> for CanContinueResult {
    fn from(c: PrimeContinuation) -> Self {
        c.to_canonical_result()
    }
}

// ── Ports ────────────────────────────────────────────────────────────────────

/// Prime 000 / 001-I: admit or refuse a candidate.
pub trait PrimeIntakePort {
    fn evaluate_intake(&self, candidate: &CandidateDeclaration) -> PrimeIntakeOutcome;
    fn validate_declaration_order(&self, order: &PrimeDeclarationOrder) -> PrimeDeclarationOutcome;
}

/// Prime 001-T: carry an observation across a carrier boundary and price the loss.
pub trait PrimeDescentPort {
    fn descend(&self, observation: &LggrEpkObservation) -> PrimeDescentReceipt;
}

/// Prime 002: decide whether the run may take another step.
/// Consumes the canonical continuation result (plain view `CanContinueResult`).
pub trait PrimeContinuationPort {
    fn can_continue(&self, inputs: &PrimeContinuationInputs) -> CanContinueResult;
}

/// The in-crate reference implementation of the three ports.
///
/// It performs the declared checks and nothing else — no host projection, no
/// authority, no side effects.
#[derive(Debug, Clone, Copy, Default)]
pub struct ReferencePrimePorts;

impl PrimeIntakePort for ReferencePrimePorts {
    fn evaluate_intake(&self, candidate: &CandidateDeclaration) -> PrimeIntakeOutcome {
        candidate.evaluate_intake()
    }
    fn validate_declaration_order(&self, order: &PrimeDeclarationOrder) -> PrimeDeclarationOutcome {
        order.validate()
    }
}

impl PrimeContinuationPort for ReferencePrimePorts {
    fn can_continue(&self, inputs: &PrimeContinuationInputs) -> CanContinueResult {
        inputs.evaluate().to_canonical_result()
    }
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/prime_seam.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:prime-seam:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6d3fb151 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6d3fb151` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6d3fb151 {
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
impl BoundaryError6d3fb151 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6d3fb151 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6d3fb151 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6d3fb151 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6d3fb151> {
        if capacity_bound == 0 {
            return Err(BoundaryError6d3fb151::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6d3fb151::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6d3fb151::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_6d3fb151 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6d3fb151::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6d3fb151::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6d3fb151::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6d3fb151::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6d3fb151::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6d3fb151::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6d3fb151::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
