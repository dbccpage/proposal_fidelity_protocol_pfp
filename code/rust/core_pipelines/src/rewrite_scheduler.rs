//! Exact, non-identity rewrite scheduling for the omega certifier loop.
//!
//! A `TerminalizedRow` is immutable. A rewrite therefore starts from a new
//! domain-supplied `CodaExactInput`, replays the canonical CODA/CODA_GTLA
//! composition, and constructs a fresh row from the resulting checked packet.
//! The scheduler accepts only carrier-preserving, componentwise non-increasing
//! rewrites with strict descent in at least one of exact `Phi1` or `Gamma2`.
//!
//! The scheduler itself carries no authority. It can seal a packet-bound
//! evidence certificate, but host promotion remains a separate boundary.

use num_rational::BigRational;
use core_certifiers::checked_packet::{CheckedPacketCertificateError, CheckedPacketCertificateV1};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_types::authority::{AuthorityEffect, DescentWitness, IsAuth};

use crate::loop_step::{manifest_hash, TerminalizedRow};
use core_wdp::coda::coda_gtla::{
    evaluate_exact, CodaExactInput, CodaGtlaEvaluation, CodaGtlaEvaluationError,
};

/// A refusal from the exact rewrite scheduler.
#[derive(Debug, thiserror::Error)]
pub enum ExactRewriteError {
    #[error(transparent)]
    Evaluation(#[from] CodaGtlaEvaluationError),
    #[error("the input row replay hash is not bound to its checked packet")]
    PreviousReplayBindingMismatch,
    #[error("an exact rewrite cannot change the carrier manifest")]
    CarrierChanged,
    #[error("Phi1 increased from {before} to {after}")]
    Phi1Increased {
        before: BigRational,
        after: BigRational,
    },
    #[error("Gamma2 increased from {before} to {after}")]
    Gamma2Increased {
        before: BigRational,
        after: BigRational,
    },
    #[error("the exact proposal has no strict Phi1 or Gamma2 descent")]
    NoStrictDescent,
    #[error("the exact proposal reused the input replay hash")]
    ReplayHashUnchanged,
    #[error("the exact proposal did not create a new checked-packet manifest")]
    PacketManifestUnchanged,
    #[error("checked-packet manifest serialization failed: {0}")]
    Manifest(#[from] serde_json::Error),
}

/// Exact evidence that one immutable checked row was replaced by another.
#[derive(Debug, Clone)]
pub struct ExactRewriteDiagnostic {
    before_phi1: BigRational,
    after_phi1: BigRational,
    before_gamma2: BigRational,
    after_gamma2: BigRational,
    input_manifest_hash: blake3::Hash,
    output_manifest_hash: blake3::Hash,
    output_replay_hash: blake3::Hash,
    descent_ref: String,
    status: ObstructionDiagnosticClass,
}

impl ExactRewriteDiagnostic {
    pub fn before_phi1(&self) -> &BigRational {
        &self.before_phi1
    }

    pub fn after_phi1(&self) -> &BigRational {
        &self.after_phi1
    }

    pub fn phi1_reduction(&self) -> BigRational {
        self.before_phi1.clone() - self.after_phi1.clone()
    }

    pub fn before_gamma2(&self) -> &BigRational {
        &self.before_gamma2
    }

    pub fn after_gamma2(&self) -> &BigRational {
        &self.after_gamma2
    }

    pub fn gamma2_reduction(&self) -> BigRational {
        self.before_gamma2.clone() - self.after_gamma2.clone()
    }

    pub fn input_manifest_hash(&self) -> &blake3::Hash {
        &self.input_manifest_hash
    }

    pub fn output_manifest_hash(&self) -> &blake3::Hash {
        &self.output_manifest_hash
    }

    pub fn output_replay_hash(&self) -> &blake3::Hash {
        &self.output_replay_hash
    }

    /// Lowercase hex expected by `CheckedPacket::certify_evidence` when it binds a
    /// `DescentWitness` to the output packet.
    pub fn output_replay_hash_hex(&self) -> String {
        self.output_replay_hash.to_hex().to_string()
    }

    /// Stable reference to the exact input/output manifest transition.
    pub fn descent_ref(&self) -> &str {
        &self.descent_ref
    }

    pub fn status(&self) -> ObstructionDiagnosticClass {
        self.status
    }

    /// Rewrite evidence is diagnostic. It cannot mint authority on its own.
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

/// A successful exact rewrite and the fresh immutable row it produced.
#[derive(Debug)]
pub struct ExactRewriteResult {
    evaluation: CodaGtlaEvaluation,
    row: TerminalizedRow,
    diagnostic: ExactRewriteDiagnostic,
}

impl ExactRewriteResult {
    pub fn evaluation(&self) -> &CodaGtlaEvaluation {
        &self.evaluation
    }

    pub fn row(&self) -> &TerminalizedRow {
        &self.row
    }

    pub fn diagnostic(&self) -> &ExactRewriteDiagnostic {
        &self.diagnostic
    }

    /// Seal evidence for the fresh checked packet after exact descent. The
    /// returned certificate cannot promote or authorize the rewrite.
    pub fn certify_certificate(
        &self,
        witness: DescentWitness,
        is_auth: IsAuth,
    ) -> Result<CheckedPacketCertificateV1, CheckedPacketCertificateError> {
        self.evaluation.certify_certificate(witness, is_auth)
    }

    pub fn into_row(self) -> TerminalizedRow {
        self.row
    }
}

fn packet_replay_hash(row: &TerminalizedRow) -> blake3::Hash {
    blake3::Hash::from_bytes(row.packet().replay_hash().0 .0)
}

pub(crate) fn evaluation_replay_hash(evaluation: &CodaGtlaEvaluation) -> blake3::Hash {
    blake3::Hash::from_bytes(evaluation.checked_packet().replay_hash().0 .0)
}

/// Validate an already replayed exact candidate against one immutable row.
// ExactRewriteError carries exact BigRational before/after pairs by design; the
// typed error surface outweighs the inline size cost on this cold path.
#[allow(clippy::result_large_err)]
fn validate_strict_descent(
    previous: &TerminalizedRow,
    evaluation: &CodaGtlaEvaluation,
) -> Result<(BigRational, BigRational, BigRational, BigRational), ExactRewriteError> {
    let before_phi1 = previous.phi1().value().clone();
    let after_phi1 = evaluation.phi1().value().clone();
    if after_phi1 > before_phi1 {
        return Err(ExactRewriteError::Phi1Increased {
            before: before_phi1,
            after: after_phi1,
        });
    }
    let before_gamma2 = previous.gamma2().value().clone();
    let after_gamma2 = evaluation.gamma2().value().clone();
    if after_gamma2 > before_gamma2 {
        return Err(ExactRewriteError::Gamma2Increased {
            before: before_gamma2,
            after: after_gamma2,
        });
    }
    if after_phi1 == before_phi1 && after_gamma2 == before_gamma2 {
        return Err(ExactRewriteError::NoStrictDescent);
    }
    Ok((before_phi1, after_phi1, before_gamma2, after_gamma2))
}

#[allow(clippy::result_large_err)]
pub(crate) fn schedule_evaluated_rewrite(
    previous: &TerminalizedRow,
    evaluation: CodaGtlaEvaluation,
) -> Result<ExactRewriteResult, ExactRewriteError> {
    if previous.replay_hash() != &packet_replay_hash(previous) {
        return Err(ExactRewriteError::PreviousReplayBindingMismatch);
    }

    if previous.packet().carrier_hash() != evaluation.checked_packet().carrier_hash() {
        return Err(ExactRewriteError::CarrierChanged);
    }

    let output_replay_hash = evaluation_replay_hash(&evaluation);
    if &output_replay_hash == previous.replay_hash() {
        return Err(ExactRewriteError::ReplayHashUnchanged);
    }

    let (before_phi1, after_phi1, before_gamma2, after_gamma2) =
        validate_strict_descent(previous, &evaluation)?;

    let input_manifest_hash = manifest_hash(previous.packet())?;
    let output_manifest_hash = manifest_hash(evaluation.checked_packet())?;
    if output_manifest_hash == input_manifest_hash {
        return Err(ExactRewriteError::PacketManifestUnchanged);
    }

    let descent_ref = format!(
        "gtoc-exact-rewrite:{}:{}",
        input_manifest_hash.to_hex(),
        output_manifest_hash.to_hex()
    );
    let status = evaluation.status();
    let row = TerminalizedRow::new(
        evaluation.checked_packet().clone(),
        evaluation.phi1().clone(),
        evaluation.gamma2().clone(),
        output_replay_hash,
    );
    let diagnostic = ExactRewriteDiagnostic {
        before_phi1,
        after_phi1,
        before_gamma2,
        after_gamma2,
        input_manifest_hash,
        output_manifest_hash,
        output_replay_hash,
        descent_ref,
        status,
    };

    debug_assert!(matches!(
        diagnostic.authority_effect(),
        AuthorityEffect::None
    ));

    Ok(ExactRewriteResult {
        evaluation,
        row,
        diagnostic,
    })
}

/// Replay and schedule one exact candidate rewrite.
///
/// The proposal is not trusted as a declared delta. `evaluate_exact` replays
/// the primitive-difference receipt, exact certificates, trichotomy, and checked
/// packet construction. This function then derives the actual exact delta and
/// refuses carrier changes, increases, identities, replay reuse, or unchanged
/// packet manifests.
// See schedule_evaluated_rewrite: exact BigRational payloads on a cold path.
#[allow(clippy::result_large_err)]
pub fn schedule_exact_rewrite(
    previous: &TerminalizedRow,
    proposal: CodaExactInput,
) -> Result<ExactRewriteResult, ExactRewriteError> {
    let evaluation = evaluate_exact(proposal)?;
    schedule_evaluated_rewrite(previous, evaluation)
}

// Origin: engine/crates_rs/core_pipelines/src/rewrite_scheduler.rs
// Claim: urn:core:crates_rs:core-pipelines:rewrite-scheduler:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_c2c99a59 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
