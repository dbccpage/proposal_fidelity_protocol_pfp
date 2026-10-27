//! CODA_CS → Q profile-factorization adapter (experimental).
//!
//! --- Math Contract:
//! - Purpose: admit a **finite-domain** profile-factorization receipt into a
//!   diagnostic Q residual bundle under the FORWARD_ONLY direction
//!   \(q = \bar{q} \circ \operatorname{Prof}\) ⇒ fiber constancy.
//! - Inputs: one [`ProfileFactorizationReceipt`] carrying Fin samples, Prof/q
//!   values, optional \(\bar{q}\), fiber-constancy witness id, residual list.
//! - Outputs: [`AdapterDecision`] in `{ConditionalSupport, OpenResidual, Refused}`
//!   aligned with [`QTerminal`], plus a diagnostic [`QPacket`].
//! - Invariants: AuthorityEffect is always [`AuthorityEffectLevel::None`];
//!   never emits [`QTerminal::TerminalWithinScope`]; reverse factorization
//!   (fiber constancy ⇒ continuum \(\bar{q}\)) remains OPEN and is not claimed.
//! - Failure: missing Prof/q samples fail closed as [`AdapterError`]; evidence
//!   defects that are still well-formed receipts return typed refuse / residual
//!   decisions rather than panicking.
//! - Numerical status: values are opaque strings (no floating-point promotion).
//! - Authority: diagnostic only. **Disabled for PROD product** until Targets 1–7
//!   of the finite-QM / CODA_CS–Q parity program are green.
//!
//! Module path: `crate::coda::q::coda_cs_adapter` (bridge surface for `core_q` as the
//! named consumer; no `core_api` coupling).

use std::collections::BTreeMap;

use core_types::authority_lattice::AuthorityEffectLevel;
use core_types::q_continuum::{ObstructionKind, Residual};
use serde::{Deserialize, Serialize};
use thiserror::Error;

use super::packet::{QPacket, QTerminal, ResidualSpec, TransportSpec};

/// Experimental status marker. PROD product surfaces must not enable this adapter
/// until Targets 1–7 of the CODA_CS–Q parity program are receipted green.
pub const CODA_CS_Q_ADAPTER_STATUS: &str = "experimental";

/// One finite domain sample with its profile and query evaluations.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DomainSample {
    /// Stable domain-element label (finite sample id).
    pub domain_id: String,
    /// Profile value \(\operatorname{Prof}(x)\) as an opaque string.
    pub prof: String,
    /// Query value \(q(x)\) as an opaque string.
    pub q: String,
}

impl DomainSample {
    pub fn new(
        domain_id: impl Into<String>,
        prof: impl Into<String>,
        q: impl Into<String>,
    ) -> Self {
        Self {
            domain_id: domain_id.into(),
            prof: prof.into(),
            q: q.into(),
        }
    }
}

/// Optional factor-map entry \(\bar{q}(\operatorname{Prof}) = v\).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QBarEntry {
    pub prof: String,
    pub value: String,
}

impl QBarEntry {
    pub fn new(prof: impl Into<String>, value: impl Into<String>) -> Self {
        Self {
            prof: prof.into(),
            value: value.into(),
        }
    }
}

/// Finite-domain profile-factorization receipt consumed by the adapter.
///
/// Carries Fin samples, Prof/q evaluations, optional \(\bar{q}\), a
/// fiber-constancy witness id/hash, and a residual list. Completeness is
/// derived by the adapter; the receipt never mints authority.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProfileFactorizationReceipt {
    /// Stable receipt identifier.
    pub receipt_id: String,
    /// Finite domain samples with Prof and q values.
    pub samples: Vec<DomainSample>,
    /// Optional factor map \(\bar{q}\) on image of Prof (finite table).
    pub q_bar: Option<Vec<QBarEntry>>,
    /// Optional fiber-constancy witness hash or id.
    pub fiber_constancy_witness_id: Option<String>,
    /// Optional claim that a pointwise factorization check already passed.
    /// When `Some(true)`, the adapter re-verifies; a claim without evidence
    /// refuses closed.
    pub pointwise_check_passed: Option<bool>,
    /// Residual list. Required non-empty when factorization is incomplete.
    pub residuals: Vec<String>,
}

impl ProfileFactorizationReceipt {
    pub fn new(receipt_id: impl Into<String>) -> Self {
        Self {
            receipt_id: receipt_id.into(),
            samples: Vec::new(),
            q_bar: None,
            fiber_constancy_witness_id: None,
            pointwise_check_passed: None,
            residuals: Vec::new(),
        }
    }

    pub fn with_sample(mut self, sample: DomainSample) -> Self {
        self.samples.push(sample);
        self
    }

    pub fn with_samples(mut self, samples: impl IntoIterator<Item = DomainSample>) -> Self {
        self.samples.extend(samples);
        self
    }

    pub fn with_q_bar(mut self, q_bar: impl IntoIterator<Item = QBarEntry>) -> Self {
        self.q_bar = Some(q_bar.into_iter().collect());
        self
    }

    pub fn with_fiber_constancy_witness_id(mut self, witness_id: impl Into<String>) -> Self {
        self.fiber_constancy_witness_id = Some(witness_id.into());
        self
    }

    pub fn with_pointwise_check_passed(mut self, passed: bool) -> Self {
        self.pointwise_check_passed = Some(passed);
        self
    }

    pub fn with_residual(mut self, residual: impl Into<String>) -> Self {
        self.residuals.push(residual.into());
        self
    }

    pub fn with_residuals(mut self, residuals: impl IntoIterator<Item = String>) -> Self {
        self.residuals.extend(residuals);
        self
    }
}

/// Typed fail-closed errors for structurally missing receipt evidence.
#[derive(Clone, Debug, PartialEq, Eq, Error)]
pub enum AdapterError {
    #[error("profile factorization receipt has no finite domain samples")]
    MissingDomainSamples,
    #[error("missing Prof sample for domain element `{domain_id}`")]
    MissingProfSample { domain_id: String },
    #[error("missing q sample for domain element `{domain_id}`")]
    MissingQSample { domain_id: String },
}

/// Diagnostic adapter decision aligned with [`QTerminal`].
///
/// Authority effect is always None. `TerminalWithinScope` is never produced.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum AdapterDecision {
    /// Finite-domain factorization checks passed; conditional support only.
    ConditionalSupport {
        packet: QPacket,
        residuals: Vec<Residual>,
        obligations: Vec<String>,
    },
    /// Factorization incomplete with declared residuals.
    OpenResidual {
        packet: QPacket,
        residuals: Vec<Residual>,
        obligations: Vec<String>,
    },
    /// Evidence present but fails closed (fiber violation, bare claim, unpaid residual).
    Refused {
        packet: QPacket,
        residuals: Vec<Residual>,
        obligations: Vec<String>,
    },
}

impl AdapterDecision {
    pub fn terminal(&self) -> QTerminal {
        match self {
            Self::ConditionalSupport { .. } => QTerminal::ConditionalSupport,
            Self::OpenResidual { .. } => QTerminal::OpenResidual,
            Self::Refused { .. } => QTerminal::Refused,
        }
    }

    pub fn packet(&self) -> &QPacket {
        match self {
            Self::ConditionalSupport { packet, .. }
            | Self::OpenResidual { packet, .. }
            | Self::Refused { packet, .. } => packet,
        }
    }

    pub fn residuals(&self) -> &[Residual] {
        match self {
            Self::ConditionalSupport { residuals, .. }
            | Self::OpenResidual { residuals, .. }
            | Self::Refused { residuals, .. } => residuals,
        }
    }

    pub fn obligations(&self) -> &[String] {
        match self {
            Self::ConditionalSupport { obligations, .. }
            | Self::OpenResidual { obligations, .. }
            | Self::Refused { obligations, .. } => obligations,
        }
    }

    /// Always [`AuthorityEffectLevel::None`]; the adapter never mints authority.
    pub fn authority_effect(&self) -> AuthorityEffectLevel {
        AuthorityEffectLevel::None
    }
}

/// Pure CODA_CS → Q adapter. Fail-closed; AuthorityEffect None.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct CodaCsToQAdapter;

impl CodaCsToQAdapter {
    pub fn new() -> Self {
        Self
    }

    /// Admit a profile-factorization receipt into a diagnostic Q decision.
    ///
    /// Returns [`AdapterError`] when Prof/q samples are missing. Well-formed
    /// receipts that fail evidence checks return `Ok(Refused | OpenResidual)`.
    pub fn admit(
        &self,
        receipt: &ProfileFactorizationReceipt,
    ) -> Result<AdapterDecision, AdapterError> {
        validate_samples(receipt)?;

        let mut obligations = vec![
            "verify finite-domain fiber constancy on provided Prof fibers".to_string(),
            "verify pointwise factorization q = q_bar ∘ Prof when q_bar is claimed".to_string(),
            "record residual when factorization is incomplete".to_string(),
            "never mint AuthorityEffect ≠ None; never claim TerminalWithinScope".to_string(),
        ];

        // Fiber constancy: Prof(x) = Prof(y) ⇒ q(x) = q(y).
        if let Some(violation) = fiber_constancy_violation(receipt) {
            obligations.push(format!(
                "fiber constancy violated on Prof=`{}` (domain `{}` vs `{}`)",
                violation.prof, violation.domain_a, violation.domain_b
            ));
            let residual = Residual::new(
                format!("residual:coda-cs:{}:fiber-constancy", receipt.receipt_id),
                receipt.receipt_id.clone(),
                ObstructionKind::CounterexampleFound,
                format!(
                    "fiber constancy violation: Prof({}) = Prof({}) = `{}` but q differs (`{}` vs `{}`)",
                    violation.domain_a,
                    violation.domain_b,
                    violation.prof,
                    violation.q_a,
                    violation.q_b
                ),
            );
            let packet = diagnostic_packet(
                receipt,
                QTerminal::Refused,
                ResidualSpec::new(
                    residual.description.clone(),
                    ObstructionKind::CounterexampleFound,
                ),
            );
            return Ok(AdapterDecision::Refused {
                packet,
                residuals: collect_residuals(receipt, residual),
                obligations,
            });
        }

        // Factorization claim without a re-verified pointwise pass → refuse.
        let claims_factorization = receipt.pointwise_check_passed == Some(true)
            || receipt.q_bar.as_ref().is_some_and(|t| !t.is_empty());

        let pointwise = if claims_factorization {
            verify_pointwise_factorization(receipt)
        } else {
            PointwiseStatus::NotClaimed
        };

        match &pointwise {
            PointwiseStatus::ClaimWithoutEvidence { reason } => {
                obligations.push(reason.clone());
                let residual = Residual::new(
                    format!("residual:coda-cs:{}:pointwise-claim", receipt.receipt_id),
                    receipt.receipt_id.clone(),
                    ObstructionKind::MissingWitness,
                    reason.clone(),
                );
                let packet = diagnostic_packet(
                    receipt,
                    QTerminal::Refused,
                    ResidualSpec::new(reason.clone(), ObstructionKind::MissingWitness),
                );
                return Ok(AdapterDecision::Refused {
                    packet,
                    residuals: collect_residuals(receipt, residual),
                    obligations,
                });
            }
            PointwiseStatus::Failed { reason } => {
                obligations.push(reason.clone());
                let residual = Residual::new(
                    format!("residual:coda-cs:{}:pointwise-fail", receipt.receipt_id),
                    receipt.receipt_id.clone(),
                    ObstructionKind::CounterexampleFound,
                    reason.clone(),
                );
                let packet = diagnostic_packet(
                    receipt,
                    QTerminal::Refused,
                    ResidualSpec::new(reason.clone(), ObstructionKind::CounterexampleFound),
                );
                return Ok(AdapterDecision::Refused {
                    packet,
                    residuals: collect_residuals(receipt, residual),
                    obligations,
                });
            }
            PointwiseStatus::Passed | PointwiseStatus::NotClaimed => {}
        }

        let factorization_complete = matches!(pointwise, PointwiseStatus::Passed)
            && receipt
                .fiber_constancy_witness_id
                .as_ref()
                .is_some_and(|id| !id.trim().is_empty());

        if factorization_complete {
            obligations.push(
                "finite-domain factorization verified; ConditionalSupport only (not TerminalWithinScope)"
                    .to_string(),
            );
            let packet = diagnostic_packet(
                receipt,
                QTerminal::ConditionalSupport,
                ResidualSpec::new(
                    "finite-domain profile factorization held; continuum reverse OPEN; AuthorityEffect None",
                    ObstructionKind::NonFiniteProjection,
                )
                .with_next_probe_hint(
                    "do not promote to continuum or TerminalWithinScope without paid descent debts",
                ),
            );
            // Success still carries a diagnostic residual fence (continuum reverse OPEN).
            let fence = Residual::new(
                format!("residual:coda-cs:{}:finite-scope-fence", receipt.receipt_id),
                receipt.receipt_id.clone(),
                ObstructionKind::NonFiniteProjection,
                "FINITE scope only: reverse continuum factorization remains OPEN; no TerminalWithinScope",
            );
            return Ok(AdapterDecision::ConditionalSupport {
                packet,
                residuals: vec![fence],
                obligations,
            });
        }

        // Incomplete factorization: residual list is mandatory.
        if receipt.residuals.iter().all(|r| r.trim().is_empty()) {
            obligations
                .push("factorization incomplete but residual field missing or empty".to_string());
            let residual = Residual::new(
                format!(
                    "residual:coda-cs:{}:missing-residual-field",
                    receipt.receipt_id
                ),
                receipt.receipt_id.clone(),
                ObstructionKind::Underdefined,
                "missing residual field when profile factorization is incomplete",
            );
            let packet = diagnostic_packet(
                receipt,
                QTerminal::Refused,
                ResidualSpec::new(
                    "missing residual field when factorization incomplete",
                    ObstructionKind::Underdefined,
                ),
            );
            return Ok(AdapterDecision::Refused {
                packet,
                residuals: vec![residual],
                obligations,
            });
        }

        obligations.push("factorization incomplete; open residual recorded".to_string());
        let primary = Residual::new(
            format!("residual:coda-cs:{}:open", receipt.receipt_id),
            receipt.receipt_id.clone(),
            ObstructionKind::Underdefined,
            receipt.residuals.join("; "),
        );
        let packet = diagnostic_packet(
            receipt,
            QTerminal::OpenResidual,
            ResidualSpec::new(receipt.residuals.join("; "), ObstructionKind::Underdefined)
                .with_next_probe_hint(
                    "supply q_bar table + fiber-constancy witness + pointwise pass, or keep residual open",
                ),
        );
        Ok(AdapterDecision::OpenResidual {
            packet,
            residuals: collect_residuals(receipt, primary),
            obligations,
        })
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct FiberViolation {
    prof: String,
    domain_a: String,
    domain_b: String,
    q_a: String,
    q_b: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
enum PointwiseStatus {
    NotClaimed,
    Passed,
    Failed { reason: String },
    ClaimWithoutEvidence { reason: String },
}

fn validate_samples(receipt: &ProfileFactorizationReceipt) -> Result<(), AdapterError> {
    if receipt.samples.is_empty() {
        return Err(AdapterError::MissingDomainSamples);
    }
    for sample in &receipt.samples {
        if sample.prof.trim().is_empty() {
            return Err(AdapterError::MissingProfSample {
                domain_id: sample.domain_id.clone(),
            });
        }
        if sample.q.trim().is_empty() {
            return Err(AdapterError::MissingQSample {
                domain_id: sample.domain_id.clone(),
            });
        }
    }
    Ok(())
}

fn fiber_constancy_violation(receipt: &ProfileFactorizationReceipt) -> Option<FiberViolation> {
    // prof -> (domain_id, q) first witness
    let mut first: BTreeMap<&str, (&str, &str)> = BTreeMap::new();
    for sample in &receipt.samples {
        match first.get(sample.prof.as_str()) {
            None => {
                first.insert(
                    sample.prof.as_str(),
                    (sample.domain_id.as_str(), sample.q.as_str()),
                );
            }
            Some((domain_a, q_a)) if *q_a != sample.q.as_str() => {
                return Some(FiberViolation {
                    prof: sample.prof.clone(),
                    domain_a: (*domain_a).to_string(),
                    domain_b: sample.domain_id.clone(),
                    q_a: (*q_a).to_string(),
                    q_b: sample.q.clone(),
                });
            }
            Some(_) => {}
        }
    }
    None
}

fn verify_samples_against_q_bar(
    receipt: &ProfileFactorizationReceipt,
    q_bar_map: &BTreeMap<&str, &str>,
) -> Option<PointwiseStatus> {
    for sample in &receipt.samples {
        match q_bar_map.get(sample.prof.as_str()) {
            None => {
                return Some(PointwiseStatus::Failed {
                    reason: format!(
                        "pointwise factorization failed: Prof=`{}` (domain `{}`) not in q_bar domain",
                        sample.prof, sample.domain_id
                    ),
                });
            }
            Some(q_bar_val) if *q_bar_val != sample.q.as_str() => {
                return Some(PointwiseStatus::Failed {
                    reason: format!(
                        "pointwise factorization failed: q({})=`{}` != q_bar(Prof={})=`{}`",
                        sample.domain_id, sample.q, sample.prof, q_bar_val
                    ),
                });
            }
            Some(_) => {}
        }
    }
    None
}

fn verify_pointwise_factorization(receipt: &ProfileFactorizationReceipt) -> PointwiseStatus {
    let Some(table) = receipt.q_bar.as_ref() else {
        return PointwiseStatus::ClaimWithoutEvidence {
            reason: "factorization claimed (pointwise_check_passed=true) without q_bar table"
                .to_string(),
        };
    };
    if table.is_empty() {
        return PointwiseStatus::ClaimWithoutEvidence {
            reason: "factorization claimed with empty q_bar table".to_string(),
        };
    }

    let mut q_bar_map: BTreeMap<&str, &str> = BTreeMap::new();
    for entry in table {
        if entry.prof.trim().is_empty() || entry.value.trim().is_empty() {
            return PointwiseStatus::ClaimWithoutEvidence {
                reason: "q_bar entry missing prof or value".to_string(),
            };
        }
        q_bar_map.insert(entry.prof.as_str(), entry.value.as_str());
    }

    if let Some(failed) = verify_samples_against_q_bar(receipt, &q_bar_map) {
        return failed;
    }

    // Claimed true is only accepted when re-verification succeeded.
    if receipt.pointwise_check_passed == Some(false) {
        return PointwiseStatus::Failed {
            reason: "pointwise_check_passed explicitly false despite table".to_string(),
        };
    }

    PointwiseStatus::Passed
}

fn collect_residuals(receipt: &ProfileFactorizationReceipt, primary: Residual) -> Vec<Residual> {
    let mut out = vec![primary];
    for (idx, text) in receipt.residuals.iter().enumerate() {
        if text.trim().is_empty() {
            continue;
        }
        out.push(Residual::new(
            format!("residual:coda-cs:{}:declared:{}", receipt.receipt_id, idx),
            receipt.receipt_id.clone(),
            ObstructionKind::Underdefined,
            text.clone(),
        ));
    }
    out
}

fn diagnostic_packet(
    receipt: &ProfileFactorizationReceipt,
    terminal: QTerminal,
    residual: ResidualSpec,
) -> QPacket {
    let sample_ids: Vec<&str> = receipt
        .samples
        .iter()
        .map(|s| s.domain_id.as_str())
        .collect();
    QPacket::new(format!("q:coda-cs:{}", receipt.receipt_id))
        .with_carrier(format!(
            "finite domain samples [{}]",
            sample_ids.join(", ")
        ))
        .with_composition(
            "finite-domain profile factorization q = q_bar ∘ Prof (FORWARD_ONLY; reverse OPEN)",
        )
        .with_observer("CODA_CS profile / query observer on Fin samples")
        .with_finite_prediction(format!(
            "Fin-{} profile factorization audit; AuthorityEffect=None; status={}",
            receipt.samples.len(),
            CODA_CS_Q_ADAPTER_STATUS
        ))
        .with_transport(
            TransportSpec::new("CODA_CS finite shadow → Q residual bundle")
                .with_equivalence_scope("finite-domain query conservativity only")
                .with_failure_mode(
                    "fiber-constancy or pointwise factorization defect; continuum reverse not claimed",
                ),
        )
        .with_residual(residual)
        .with_terminal_request(terminal)
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/coda_cs_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:coda-cs-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    /// Happy path: Fin-small fiber-constant query with q_bar and witness.
    fn happy_fin_small_receipt() -> ProfileFactorizationReceipt {
        // Domain {a0,a1,a2}, Prof(x)=parity class, q(x)=parity (fiber constant).
        ProfileFactorizationReceipt::new("fin-small-parity")
            .with_samples([
                DomainSample::new("a0", "even", "0"),
                DomainSample::new("a1", "odd", "1"),
                DomainSample::new("a2", "even", "0"),
            ])
            .with_q_bar([QBarEntry::new("even", "0"), QBarEntry::new("odd", "1")])
            .with_fiber_constancy_witness_id("witness:fin-small-parity:blake3:deadbeef")
            .with_pointwise_check_passed(true)
    }

    #[test]
    fn status_is_experimental() {
        assert_eq!(CODA_CS_Q_ADAPTER_STATUS, "experimental");
    }

    #[test]
    fn happy_path_fin_small_conditional_support() {
        let receipt = happy_fin_small_receipt();
        let decision = CodaCsToQAdapter::new()
            .admit(&receipt)
            .expect("happy path admits");

        assert_eq!(decision.terminal(), QTerminal::ConditionalSupport);
        assert_eq!(decision.authority_effect(), AuthorityEffectLevel::None);
        assert!(matches!(
            decision,
            AdapterDecision::ConditionalSupport { .. }
        ));
        assert!(decision.packet().validate_mandatory().is_ok());
        assert_eq!(
            decision.packet().terminal_request,
            Some(QTerminal::ConditionalSupport)
        );
        // Fence residual present; never TerminalWithinScope.
        assert!(!decision.residuals().is_empty());
        assert_ne!(decision.terminal(), QTerminal::TerminalWithinScope);
    }

    #[test]
    fn fail_closed_missing_domain_samples() {
        let receipt = ProfileFactorizationReceipt::new("empty");
        let err = CodaCsToQAdapter::new()
            .admit(&receipt)
            .expect_err("empty samples must error");
        assert_eq!(err, AdapterError::MissingDomainSamples);
    }

    #[test]
    fn fail_closed_missing_prof_sample() {
        let receipt = ProfileFactorizationReceipt::new("no-prof")
            .with_sample(DomainSample::new("x0", "", "1"));
        let err = CodaCsToQAdapter::new()
            .admit(&receipt)
            .expect_err("missing prof must error");
        assert_eq!(
            err,
            AdapterError::MissingProfSample {
                domain_id: "x0".to_string()
            }
        );
    }

    #[test]
    fn fail_closed_missing_q_sample() {
        let receipt = ProfileFactorizationReceipt::new("no-q")
            .with_sample(DomainSample::new("x0", "p", "  "));
        let err = CodaCsToQAdapter::new()
            .admit(&receipt)
            .expect_err("missing q must error");
        assert_eq!(
            err,
            AdapterError::MissingQSample {
                domain_id: "x0".to_string()
            }
        );
    }

    #[test]
    fn fail_closed_fiber_constancy_violation() {
        let receipt = ProfileFactorizationReceipt::new("fiber-break")
            .with_samples([
                DomainSample::new("x0", "same", "0"),
                DomainSample::new("x1", "same", "1"),
            ])
            .with_residual("R_factor: predeclared");

        let decision = CodaCsToQAdapter::new()
            .admit(&receipt)
            .expect("well-formed receipt yields decision");

        assert_eq!(decision.terminal(), QTerminal::Refused);
        assert_eq!(decision.authority_effect(), AuthorityEffectLevel::None);
        assert!(decision
            .residuals()
            .iter()
            .any(|r| r.obstruction == ObstructionKind::CounterexampleFound));
        assert!(decision
            .residuals()
            .iter()
            .any(|r| r.description.contains("fiber constancy")));
    }

    #[test]
    fn fail_closed_factorization_claim_without_pointwise_evidence() {
        let receipt = ProfileFactorizationReceipt::new("bare-claim")
            .with_samples([
                DomainSample::new("x0", "p0", "0"),
                DomainSample::new("x1", "p1", "1"),
            ])
            .with_pointwise_check_passed(true)
            // no q_bar table
            .with_residual("claimed complete");

        let decision = CodaCsToQAdapter::new()
            .admit(&receipt)
            .expect("well-formed receipt yields decision");

        assert_eq!(decision.terminal(), QTerminal::Refused);
        assert!(decision
            .residuals()
            .iter()
            .any(|r| r.obstruction == ObstructionKind::MissingWitness));
        assert!(decision
            .residuals()
            .iter()
            .any(|r| r.description.contains("without q_bar")));
    }

    #[test]
    fn fail_closed_pointwise_mismatch_refuses() {
        let receipt = ProfileFactorizationReceipt::new("pointwise-break")
            .with_samples([
                DomainSample::new("x0", "even", "0"),
                DomainSample::new("x1", "odd", "1"),
            ])
            .with_q_bar([
                QBarEntry::new("even", "0"),
                QBarEntry::new("odd", "9"), // wrong
            ])
            .with_pointwise_check_passed(true)
            .with_fiber_constancy_witness_id("w")
            .with_residual("R_factor");

        let decision = CodaCsToQAdapter::new().admit(&receipt).expect("decision");

        assert_eq!(decision.terminal(), QTerminal::Refused);
        assert!(decision
            .residuals()
            .iter()
            .any(|r| r.description.contains("pointwise factorization failed")));
    }

    #[test]
    fn fail_closed_missing_residual_when_incomplete() {
        let receipt = ProfileFactorizationReceipt::new("incomplete-no-residual").with_samples([
            DomainSample::new("x0", "p0", "0"),
            DomainSample::new("x1", "p1", "1"),
        ]);
        // fiber constant, but no q_bar / witness → incomplete; residuals empty → refuse

        let decision = CodaCsToQAdapter::new().admit(&receipt).expect("decision");

        assert_eq!(decision.terminal(), QTerminal::Refused);
        assert!(decision
            .residuals()
            .iter()
            .any(|r| r.description.contains("missing residual field")));
        assert_eq!(decision.authority_effect(), AuthorityEffectLevel::None);
    }

    #[test]
    fn incomplete_with_residual_is_open_residual() {
        let receipt = ProfileFactorizationReceipt::new("incomplete-open")
            .with_samples([
                DomainSample::new("x0", "p0", "0"),
                DomainSample::new("x1", "p1", "1"),
            ])
            .with_residual("R_factor: q_bar not yet constructed on Fin sample");

        let decision = CodaCsToQAdapter::new().admit(&receipt).expect("decision");

        assert_eq!(decision.terminal(), QTerminal::OpenResidual);
        assert!(matches!(decision, AdapterDecision::OpenResidual { .. }));
        assert_eq!(decision.authority_effect(), AuthorityEffectLevel::None);
        assert!(decision.packet().validate_mandatory().is_ok());
    }

    #[test]
    fn never_emits_terminal_within_scope() {
        let receipt = happy_fin_small_receipt();
        let decision = CodaCsToQAdapter::new().admit(&receipt).expect("happy path");
        assert_ne!(decision.terminal(), QTerminal::TerminalWithinScope);
        assert_ne!(
            decision.packet().terminal_request,
            Some(QTerminal::TerminalWithinScope)
        );
    }
}
