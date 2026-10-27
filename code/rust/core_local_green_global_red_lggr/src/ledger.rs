//! Residual ledger bridge — the contract-shaped declaration that EPK's residual
//! channel is a *classification*, never authority.
//!
//! EPK measures composition-residual risk: the local-green/global-red hidden
//! failure rate `ngd = Pr(Δ_E = -1)` and, when a residual report is supplied, the
//! normalized residual kernel error `nrke`. This module wraps that telemetry in
//! an [`EpkResidualLedger`] whose authority interface is **fixed regardless of
//! the values it carries**: it always reports [`AuthorityEffect::None`] and
//! always maps to [`Outcome::Refused`]`(`[`RefusalSource::Residual`]`)`.
//!
//! # Why this constructs no authority
//!
//! Authority in the Core Tower is produced ONLY by terminalized finite descent
//! (`core_types::authority::authority_from_outcome_f13` over a `Terminal`
//! outcome plus a [`DescentWitness`](core_types::authority::DescentWitness) and
//! a decided `IsAuth` token). Every `RefusalSource` — including `Residual` —
//! yields `None` from `authority_from_outcome_f13`, **even when a valid descent
//! witness and decided `IsAuth` token are supplied**. `EpkResidualLedger` adds no
//! new safety property: it pins EPK's residual channel to the `inr(φ)` / refusal
//! side of the `T + F` coproduct so the firewall already proven in `core_types`
//! applies unchanged. A clean reading (zero `ngd`, no `nrke`) is still not
//! authority.
//!
//! # Variant reuse
//!
//! `RefusalSource::Residual` is documented in `core_types` as a CODA-A
//! residual-closure residue (Sentinel). EPK's residual is the *kernel-composition*
//! residual — a different residual. EPK **reuses** the variant because the
//! "classifies, never authorizes" semantics are identical, not because EPK claims
//! CODA-A closure semantics.

use core_functional::gamma2::ExactGamma2Result;
use core_functional::phi1::VerifiedExactPhi1;
use core_policy::trichotomy::{CertifiedExactTrichotomy, ObstructionDiagnosticClass};
use crate::residual_families::{
    reconcile_verified, FamilyCollision, FamilyRegistry, RegistryWrite, ShapeSignature,
};
use core_types::authority::{AuthorityEffect, Outcome, RefusalSource};
use core_types::observer::Observer;
use serde::{Deserialize, Serialize};

use crate::epk_engine::EpkMetrics;
use num_traits::ToPrimitive;

/// Serializable receipt that EPK observed one verified stabilized family.
///
/// This is diagnostic metadata. It is not a checked packet, descent witness,
/// terminal, or authority token.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EpkResidualFamilyReceipt {
    pub shape_signature: [u8; 32],
    pub q1_class_id: u64,
    pub gamma2_class_id: u64,
    pub lookup_hit: bool,
    pub inserted: bool,
}

/// Refusal to bind EPK telemetry to an exact residual family.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum EpkResidualFamilyError {
    #[error("EPK residual-family binding requires a stabilized survivor, got {0:?}")]
    NotStabilized(ObstructionDiagnosticClass),
    #[error("the supplied trichotomy is not bound to the supplied Phi1/Gamma2 evidence")]
    EvidenceMismatch,
    #[error(transparent)]
    Family(#[from] FamilyCollision),
}

/// A contract-shaped view of EPK residual risk.
///
/// Holds the residual signals EPK computed. Its authority interface is fixed by
/// [`EpkResidualLedger::authority_effect`] and [`EpkResidualLedger::as_outcome`]
/// and does not depend on these values — the ledger classifies risk, it never
/// authorizes.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EpkResidualLedger {
    /// Negative gluing defect rate `Pr(Δ_E = -1)` — the safety-critical
    /// local-green / global-red hidden-failure rate.
    pub ngd: f64,
    /// Normalized residual kernel error, when a residual report fed the metric
    /// stack; `None` when no residual was computed.
    pub nrke: Option<f64>,
    /// The terminal classification of this residual under the finite
    /// obstruction calculus (PointedObstructionClassifier spec).
    pub obstruction_status: Option<ObstructionDiagnosticClass>,
}

impl EpkResidualLedger {
    /// Build a ledger from a computed [`EpkMetrics`] report — the natural call
    /// site, since `EpkMetrics` carries both the hidden-failure rate and the
    /// (optional) normalized residual kernel error.
    pub fn from_metrics(metrics: &EpkMetrics) -> Self {
        Self {
            ngd: metrics.ngd.to_f64().unwrap_or(0.0),
            nrke: metrics.nrke.as_ref().and_then(ToPrimitive::to_f64),
            obstruction_status: None,
        }
    }

    /// Build a ledger with a specific terminal obstruction status.
    pub fn with_obstruction_status(mut self, status: ObstructionDiagnosticClass) -> Self {
        self.obstruction_status = Some(status);
        self
    }

    /// Consult and reconcile one exact stabilized residual family.
    ///
    /// Dependency direction prevents EPK from calling `core_pipelines` (the
    /// pipeline already depends on EPK). The caller therefore supplies the
    /// sealed exact trichotomy plus its verified Phi1/Gamma2 evidence. This
    /// method checks their binding, performs the registry lookup before local
    /// class-id derivation, and returns diagnostic metadata only.
    pub fn register_stabilized_family(
        &mut self,
        registry: &mut FamilyRegistry,
        signature: ShapeSignature,
        phi1: &VerifiedExactPhi1,
        gamma2: &ExactGamma2Result,
        trichotomy: &CertifiedExactTrichotomy,
        observer: &Observer,
    ) -> Result<EpkResidualFamilyReceipt, EpkResidualFamilyError> {
        if trichotomy.diagnostic_class() != ObstructionDiagnosticClass::ClosedResidual {
            return Err(EpkResidualFamilyError::NotStabilized(
                trichotomy.diagnostic_class(),
            ));
        }
        if trichotomy.phi1_value() != phi1.value()
            || trichotomy.gamma2_value() != gamma2.value()
            || phi1.primal_residual() != gamma2.residual()
            || phi1.d0() != gamma2.d0()
        {
            return Err(EpkResidualFamilyError::EvidenceMismatch);
        }

        let consultation = registry.consult(signature);
        let resolution = reconcile_verified(registry, consultation, phi1, gamma2, observer)?;
        self.obstruction_status = Some(trichotomy.diagnostic_class());

        Ok(EpkResidualFamilyReceipt {
            shape_signature: *resolution.signature().as_bytes(),
            q1_class_id: resolution.q1_class_id().as_u64(),
            gamma2_class_id: resolution.gamma2_class_id().as_u64(),
            lookup_hit: resolution.lookup_hit(),
            inserted: resolution.registry_write() == RegistryWrite::Inserted,
        })
    }

    /// The authority effect of an EPK residual reading: **always**
    /// [`AuthorityEffect::None`]. EPK is diagnostic; it constructs no authority.
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }

    /// The pipeline outcome of an EPK residual reading: **always**
    /// [`Outcome::Refused`]`(`[`RefusalSource::Residual`]`)`, for every ledger
    /// state. This is the `inr(φ)` side of the `T + F` coproduct, so
    /// `authority_from_outcome_f13` yields `None` even with a valid descent
    /// witness and decided `IsAuth` token.
    pub fn as_outcome(&self) -> Outcome {
        Outcome::Refused(RefusalSource::Residual)
    }
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/ledger.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:ledger:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::epk_engine::{calculate_metrics, CompositionRecord};
    use core_types::authority::{
        authority_from_outcome_f13, AuthorityTerminal, DescentWitness, IsAuth,
    };

    fn valid_witness() -> DescentWitness {
        DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent:epk-residual",
            "blake3:deadbeef",
        )
        .expect("nonempty refs produce a witness")
    }

    fn valid_is_auth() -> IsAuth {
        let evidence =
            core_types::GuardEvidence::new_valid(["cand_01"], "K_carrier_01", "blake3:deadbeef");
        IsAuth::decide(AuthorityTerminal::ExactRuleDerived, evidence)
            .expect("all seven guards produce an IsAuth token")
    }

    /// Ledgers spanning the meaningful states: a clean reading, a fully-hidden
    /// failure reading, an intermediate one, and a no-residual reading. The
    /// firewall property must hold for **all** of them, not just one — a
    /// one-state test would pass even if someone later added a conditional
    /// `Terminal` branch for low-risk readings.
    fn ledgers_across_states() -> Vec<EpkResidualLedger> {
        vec![
            EpkResidualLedger {
                ngd: 0.0,
                nrke: Some(0.0),
                obstruction_status: Some(ObstructionDiagnosticClass::ExactRepair),
            }, // clean residual
            EpkResidualLedger {
                ngd: 0.4,
                nrke: Some(0.75),
                obstruction_status: Some(ObstructionDiagnosticClass::ClosedResidual),
            }, // partial hidden failures
            EpkResidualLedger {
                ngd: 1.0,
                nrke: None,
                obstruction_status: Some(ObstructionDiagnosticClass::ActiveClosureFailure),
            }, // all hidden failures, no nrke
            EpkResidualLedger {
                ngd: 0.0,
                nrke: None,
                obstruction_status: None,
            }, // clean, no residual report
        ]
    }

    #[test]
    fn outcome_is_refused_residual_for_every_state() {
        for ledger in ledgers_across_states() {
            assert_eq!(
                ledger.as_outcome(),
                Outcome::Refused(RefusalSource::Residual),
                "state {ledger:?} must map to Refused(Residual)"
            );
            assert!(
                ledger.as_outcome().authority_terminal().is_none(),
                "state {ledger:?} must yield no authority terminal"
            );
        }
    }

    #[test]
    fn authority_effect_is_none_for_every_state() {
        for ledger in ledgers_across_states() {
            assert!(
                ledger.authority_effect().is_none(),
                "state {ledger:?} must carry no authority effect"
            );
        }
    }

    #[test]
    fn firewall_no_authority_even_with_valid_witness() {
        // The crux: even a genuine descent witness cannot turn an EPK residual
        // reading into authority. This holds unconditionally across ledger
        // states, inheriting the encode-decode firewall proven in core_types.
        for ledger in ledgers_across_states() {
            let got = authority_from_outcome_f13(
                ledger.as_outcome(),
                Some(valid_witness()),
                Some(valid_is_auth()),
            );
            assert!(
                got.is_none(),
                "EPK residual must never authorize, even with a witness and IsAuth token; state {ledger:?}"
            );
        }
    }

    use num_rational::BigRational;

    #[test]
    fn from_metrics_carries_residual_signals_but_still_refuses() {
        // One composition with E1·E2 = 1 but Eg = 0: a hidden failure, Δ_E = -1.
        let comps =
            vec![CompositionRecord::new("c0", "l0", "r0", true, true, false, None).unwrap()];
        let metrics = calculate_metrics(
            &comps,
            None,
            Some(BigRational::new(1.into(), 2.into())),
            Some(BigRational::new(1.into(), 4.into())),
            None,
        )
        .unwrap();

        let ledger = EpkResidualLedger::from_metrics(&metrics);
        assert_eq!(ledger.nrke, Some(0.25));
        assert!((ledger.ngd - 1.0).abs() < 1e-12);

        // Carrying real residual signal does not change the authority interface.
        assert_eq!(
            ledger.as_outcome(),
            Outcome::Refused(RefusalSource::Residual)
        );
        assert!(ledger.authority_effect().is_none());
        assert!(authority_from_outcome_f13(
            ledger.as_outcome(),
            Some(valid_witness()),
            Some(valid_is_auth())
        )
        .is_none());
    }
}
