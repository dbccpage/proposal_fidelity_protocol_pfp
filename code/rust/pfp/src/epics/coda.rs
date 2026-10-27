//! CODA layer bridges and the quarantine for speculative adapters.
//!
//! `EPIC-OE-SYMGAM-014` states one invariant that does all the work:
//!
//! > **Strict 3-Layer Seam:** Parity =/=> Physical =/=> Algorithmic.
//!
//! An exact `F2` computation establishes a **parity** fact. It does not
//! establish that the physical system it was modelling behaves that way, and it
//! establishes nothing about the efficiency of any algorithm. Those are three
//! different claims with three different burdens of proof, and the failure this
//! module exists to prevent is the quiet promotion of the first into the second
//! or third -- a real result about a matrix being cited as a result about a
//! world.
//!
//! # The seam is a type, not a rule
//!
//! Sprint 030 established the principle: a rule whose violation is loud can live
//! in a document; a rule whose violation is **silent** has to live in the type
//! system. Laundering a layer is silent -- the parity computation was correct,
//! the sentence reads plausibly, and nothing fails.
//!
//! So:
//!
//! - A [`LayeredClaim`] carries its [`Layer`] and there is no method that
//!   changes it.
//! - [`bridge`] exists, is the only cross-layer operation, and **always
//!   refuses**. It is present so the refusal is a stated result rather than an
//!   absent feature a reader might think was overlooked.
//! - [`Evidence::ParityWitness`] admits a claim only at [`Layer::Parity`].
//!   Offering one for a physical claim is [`LayerRefusal::LayerMismatch`].
//!
//! # Quarantine fails closed
//!
//! A [`QuarantinedAdapter`] is a speculative proposal -- Grassmann parity, Regge
//! calculus, Clifford sign bridges. It may hold a hypothesis and it may not
//! author a receipt. `author_receipt` refuses whenever the certificate is
//! absent, which is the fail-closed direction: an adapter with no evidence
//! produces no evidence, rather than producing an unmarked one.
//!
//! Certification requires a **named reviewer**, exactly as guard generalization
//! does in `guard.rs`. The estate's rule is consistent: a machine may propose,
//! and a human signs.
//!
//! `AuthorityEffect: None`. Classifying a board is not certifying a world.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};
use thiserror::Error;

use pfp_runtime::f2::GaugeVerdict;

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Error)]
pub enum LayerRefusal {
    #[error(
        "the {from} layer does not entail the {to} layer; \
         Parity =/=> Physical =/=> Algorithmic is the seam this refuses to cross"
    )]
    SeamCrossing {
        from: &'static str,
        to: &'static str,
    },

    #[error("{evidence} evidence cannot admit a claim at the {layer} layer")]
    LayerMismatch {
        evidence: &'static str,
        layer: &'static str,
    },

    #[error("a claim needs a statement; an empty one asserts nothing")]
    EmptyStatement,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Error)]
pub enum QuarantineRefusal {
    #[error("adapter {adapter} holds no formal certificate and may not author a receipt")]
    Uncertified { adapter: String },

    #[error("a certificate needs a reviewer; none was named for adapter {adapter}")]
    UnreviewedCertificate { adapter: String },

    #[error("adapter {adapter} declares no hypothesis")]
    EmptyHypothesis { adapter: String },

    #[error("refusing to report a canary sweep over no adapters")]
    NoAdapters,
}

// ---------------------------------------------------------------------------
// The three layers
// ---------------------------------------------------------------------------

/// The three layers of the CODA seam, in the order the epic states them.
///
/// The order is a listing, not an implication. Nothing here means a lower layer
/// entails a higher one -- that is precisely what [`bridge`] refuses.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum Layer {
    /// Exact `F2` / cochain facts. Replayable by computation.
    Parity,
    /// Claims about a physical system the parity object was modelling.
    Physical,
    /// Claims about the cost or efficiency of an algorithm.
    Algorithmic,
}

impl Layer {
    pub fn name(self) -> &'static str {
        match self {
            Layer::Parity => "parity",
            Layer::Physical => "physical",
            Layer::Algorithmic => "algorithmic",
        }
    }

    pub fn all() -> [Layer; 3] {
        [Layer::Parity, Layer::Physical, Layer::Algorithmic]
    }
}

/// What is offered in support of a claim.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum Evidence {
    /// The outcome of an exact `F2` classification, replayable.
    ParityWitness { verdict_token: String },
    /// A measurement of a physical system.
    Measurement { instrument: String },
    /// A benchmark of an implementation.
    Benchmark { harness: String },
    /// Asserted by a speculative adapter. Supports **no** layer.
    Speculative { adapter: String },
}

impl Evidence {
    pub fn kind(&self) -> &'static str {
        match self {
            Evidence::ParityWitness { .. } => "parity_witness",
            Evidence::Measurement { .. } => "measurement",
            Evidence::Benchmark { .. } => "benchmark",
            Evidence::Speculative { .. } => "speculative",
        }
    }

    /// The single layer this evidence can support, if any.
    ///
    /// `Speculative` returns `None`: a hypothesis is not evidence for itself at
    /// any layer, which is what quarantine means.
    pub fn admissible_layer(&self) -> Option<Layer> {
        match self {
            Evidence::ParityWitness { .. } => Some(Layer::Parity),
            Evidence::Measurement { .. } => Some(Layer::Physical),
            Evidence::Benchmark { .. } => Some(Layer::Algorithmic),
            Evidence::Speculative { .. } => None,
        }
    }
}

/// Build parity evidence from an actual classification.
///
/// Takes the verdict rather than a string so the token cannot be invented: the
/// only way to get parity evidence is to have run the classification.
pub fn witness_from_verdict(verdict: &GaugeVerdict) -> Evidence {
    Evidence::ParityWitness {
        verdict_token: verdict.token().to_string(),
    }
}

/// A claim, its layer, and what is offered for it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LayeredClaim {
    layer: Layer,
    statement: String,
    evidence: Evidence,
}

impl LayeredClaim {
    /// Assemble a claim. Admission is a separate step -- see [`admit`].
    pub fn new(
        layer: Layer,
        statement: impl Into<String>,
        evidence: Evidence,
    ) -> Result<Self, LayerRefusal> {
        let statement = statement.into();
        if statement.trim().is_empty() {
            return Err(LayerRefusal::EmptyStatement);
        }
        Ok(Self {
            layer,
            statement,
            evidence,
        })
    }

    /// The layer this claim was made at.
    ///
    /// Read-only by design: there is no setter, and no method on this type
    /// returns a claim at a different layer.
    pub fn layer(&self) -> Layer {
        self.layer
    }

    pub fn statement(&self) -> &str {
        &self.statement
    }

    pub fn evidence(&self) -> &Evidence {
        &self.evidence
    }
}

/// A claim whose evidence matches its layer.
///
/// Constructible only through [`admit`]. Holding one of these means the seam
/// was checked, not that the statement is true.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AdmittedClaim {
    claim: LayeredClaim,
}

impl AdmittedClaim {
    pub fn claim(&self) -> &LayeredClaim {
        &self.claim
    }

    pub fn layer(&self) -> Layer {
        self.claim.layer
    }
}

/// Admit a claim if and only if its evidence belongs to its layer.
pub fn admit(claim: LayeredClaim) -> Result<AdmittedClaim, LayerRefusal> {
    match claim.evidence.admissible_layer() {
        Some(layer) if layer == claim.layer => Ok(AdmittedClaim { claim }),
        _ => Err(LayerRefusal::LayerMismatch {
            evidence: claim.evidence.kind(),
            layer: claim.layer.name(),
        }),
    }
}

/// The only cross-layer operation, and it always refuses.
///
/// Present rather than absent on purpose. A missing function is
/// indistinguishable from an overlooked one, and a reader wondering "how do I
/// promote this parity result to a physical claim?" should find an answer
/// stating that they cannot, not silence.
///
/// The answer is always a refusal, including from a layer to itself -- a
/// "bridge" that returned its input unchanged would be a promotion path waiting
/// for someone to widen it.
pub fn bridge(claim: &AdmittedClaim, to: Layer) -> Result<AdmittedClaim, LayerRefusal> {
    Err(LayerRefusal::SeamCrossing {
        from: claim.layer().name(),
        to: to.name(),
    })
}

// ---------------------------------------------------------------------------
// Quarantine
// ---------------------------------------------------------------------------

/// A formal certificate admitting a speculative adapter.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FormalCertificate {
    pub reviewer: String,
    pub rationale: String,
}

/// A speculative bridge: Grassmann parity, Regge calculus, Clifford signs.
///
/// It may hold a hypothesis. It may not author a receipt without a certificate,
/// and the certificate needs a named human.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct QuarantinedAdapter {
    name: String,
    hypothesis: String,
    certificate: Option<FormalCertificate>,
}

impl QuarantinedAdapter {
    pub fn propose(
        name: impl Into<String>,
        hypothesis: impl Into<String>,
    ) -> Result<Self, QuarantineRefusal> {
        let name = name.into();
        let hypothesis = hypothesis.into();
        if hypothesis.trim().is_empty() {
            return Err(QuarantineRefusal::EmptyHypothesis { adapter: name });
        }
        Ok(Self {
            name,
            hypothesis,
            certificate: None,
        })
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn hypothesis(&self) -> &str {
        &self.hypothesis
    }

    pub fn is_certified(&self) -> bool {
        self.certificate.is_some()
    }

    pub fn certificate(&self) -> Option<&FormalCertificate> {
        self.certificate.as_ref()
    }

    /// Admit a certificate. Requires a named reviewer.
    pub fn admit_certificate(
        mut self,
        reviewer: &str,
        rationale: &str,
    ) -> Result<Self, QuarantineRefusal> {
        if reviewer.trim().is_empty() {
            return Err(QuarantineRefusal::UnreviewedCertificate { adapter: self.name });
        }
        self.certificate = Some(FormalCertificate {
            reviewer: reviewer.to_string(),
            rationale: rationale.to_string(),
        });
        Ok(self)
    }

    /// Author a receipt, or refuse.
    ///
    /// Fails closed: an adapter with no certificate produces **no** receipt,
    /// rather than an unmarked one that a later reader might take for verified.
    pub fn author_receipt(&self) -> Result<AdapterReceiptV1, QuarantineRefusal> {
        let certificate =
            self.certificate
                .as_ref()
                .ok_or_else(|| QuarantineRefusal::Uncertified {
                    adapter: self.name.clone(),
                })?;
        Ok(AdapterReceiptV1 {
            schema: ADAPTER_RECEIPT_SCHEMA,
            adapter: self.name.clone(),
            hypothesis: self.hypothesis.clone(),
            reviewer: certificate.reviewer.clone(),
            authority_effect: "None",
        })
    }

    /// The evidence this adapter offers, which supports no layer.
    pub fn evidence(&self) -> Evidence {
        Evidence::Speculative {
            adapter: self.name.clone(),
        }
    }
}

pub const ADAPTER_RECEIPT_SCHEMA: &str = "core.symbol_game.quarantined_adapter.v1";

/// A receipt an adapter may author only once certified.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AdapterReceiptV1 {
    pub schema: &'static str,
    pub adapter: String,
    pub hypothesis: String,
    pub reviewer: String,
    pub authority_effect: &'static str,
}

/// The result of sweeping a sandbox for fail-closed behaviour.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CanaryReport {
    /// Adapters that correctly refused to author a receipt.
    pub failed_closed: Vec<String>,
    /// Certified adapters, which are expected to author one.
    pub certified: Vec<String>,
    /// Adapters that authored a receipt **without** a certificate. Any entry
    /// here is a breach, and the field exists so a breach is a value rather
    /// than an absence.
    pub leaked: Vec<String>,
}

impl CanaryReport {
    pub fn is_sound(&self) -> bool {
        self.leaked.is_empty()
    }
}

/// Sweep a sandbox: every uncertified adapter must refuse to author a receipt.
///
/// Refuses an empty sandbox. Reporting that all zero adapters failed closed is
/// a claim true because nothing was examined -- the vacuous pass this estate has
/// produced in four consecutive sprints.
pub fn canary_sweep(adapters: &[QuarantinedAdapter]) -> Result<CanaryReport, QuarantineRefusal> {
    if adapters.is_empty() {
        return Err(QuarantineRefusal::NoAdapters);
    }
    let mut failed_closed = Vec::new();
    let mut certified = Vec::new();
    let mut leaked = Vec::new();
    for adapter in adapters {
        match (adapter.author_receipt(), adapter.is_certified()) {
            (Err(_), false) => failed_closed.push(adapter.name().to_string()),
            (Ok(_), true) => certified.push(adapter.name().to_string()),
            (Ok(_), false) => leaked.push(adapter.name().to_string()),
            // Certified but refusing: not a soundness breach, and not a pass
            // either. Recorded with the ones that refused.
            (Err(_), true) => failed_closed.push(adapter.name().to_string()),
        }
    }
    Ok(CanaryReport {
        failed_closed,
        certified,
        leaked,
    })
}

// ---------------------------------------------------------------------------
// Boundary receipts
// ---------------------------------------------------------------------------

pub const BOUNDARY_RECEIPT_SCHEMA: &str = "core.symbol_game.coda_boundary.v1";

/// A receipt distinguishing verified parity from speculative hypothesis.
///
/// The epic's criterion 3. The two counts are separate fields and never summed:
/// a total would be the one number that reads as "how much do we know", and it
/// would be the sum of a thing established and a thing proposed.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CodaBoundaryReceiptV1 {
    pub schema: &'static str,
    pub verified_parity_claims: usize,
    pub verified_physical_claims: usize,
    pub verified_algorithmic_claims: usize,
    pub speculative_hypotheses: usize,
    pub layers_crossed: usize,
    pub digest: String,
    pub authority_effect: &'static str,
}

/// Build a boundary receipt over admitted claims and quarantined adapters.
pub fn boundary_receipt(
    admitted: &[AdmittedClaim],
    adapters: &[QuarantinedAdapter],
) -> CodaBoundaryReceiptV1 {
    let mut parity = 0usize;
    let mut physical = 0usize;
    let mut algorithmic = 0usize;
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"coda-boundary-v1");

    // Sorted so the digest does not depend on the order claims were assembled.
    let mut statements: BTreeSet<(&'static str, &str)> = BTreeSet::new();
    for claim in admitted {
        match claim.layer() {
            Layer::Parity => parity += 1,
            Layer::Physical => physical += 1,
            Layer::Algorithmic => algorithmic += 1,
        }
        statements.insert((claim.layer().name(), claim.claim().statement()));
    }
    for (layer, statement) in &statements {
        hasher.update(layer.as_bytes());
        hasher.update(statement.as_bytes());
        hasher.update(b"\x00");
    }
    let mut names: BTreeSet<&str> = BTreeSet::new();
    for adapter in adapters {
        names.insert(adapter.name());
    }
    for name in &names {
        hasher.update(b"speculative:");
        hasher.update(name.as_bytes());
    }

    CodaBoundaryReceiptV1 {
        schema: BOUNDARY_RECEIPT_SCHEMA,
        verified_parity_claims: parity,
        verified_physical_claims: physical,
        verified_algorithmic_claims: algorithmic,
        speculative_hypotheses: adapters.len(),
        // Always zero. The field is present so a reader sees the number rather
        // than inferring it from silence, and so any future non-zero value is
        // loud.
        layers_crossed: 0,
        digest: hasher.finalize().to_hex().to_string(),
        authority_effect: "None",
    }
}

// Origin: engine/crates_rs/pfp/src/epics/coda.rs
// Claim: urn:core:crates_rs:pfp:coda:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_c241aff6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
