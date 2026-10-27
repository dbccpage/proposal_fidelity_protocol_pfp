//! # Display-Only Closure Regime
//!
//! This module provides a display-only view of the exact finite obstruction trichotomy.
//!
//! **Warning**:
//! - This represents a display-only/diagnostic view of exact quotient-level trichotomy.
//! - It must not be used for authority minting, lift acceptance, or terminal classification.

use crate::trichotomy::{CertifiedExactTrichotomy, ObstructionDiagnosticClass};
use serde::{Deserialize, Serialize};

/// Display/diagnostic-only view of exact closure regime.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ClosureRegime {
    /// Exact: Φ₁ = 0 (no obstruction)
    Exact,

    /// Closed residual: Φ₁ > 0, Γ₂ = 0 (H¹ element)
    ClosedResidual,

    /// Open obstruction: Φ₁ > 0, Γ₂ > 0 (non-closed)
    ActiveClosureFailure,
}

impl ClosureRegime {
    /// Construct a display-only `ClosureRegime` from a `CertifiedExactTrichotomy`.
    pub fn from_certified(certified: &CertifiedExactTrichotomy) -> Self {
        match certified.diagnostic_class() {
            ObstructionDiagnosticClass::ExactRepair => Self::Exact,
            ObstructionDiagnosticClass::ClosedResidual => Self::ClosedResidual,
            ObstructionDiagnosticClass::ActiveClosureFailure => Self::ActiveClosureFailure,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ClosureComparisonMode {
    ExactRational,
    ToleranceDiagnostic,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ClosureRegimeError {
    #[error("comparison mode must be named")]
    UnnamedComparisonMode,
    #[error("tolerance/diagnostic mode must not emit exact trichotomy")]
    ToleranceModeEmitsExactTrichotomy,
    #[error("regime profile identity changed across replay")]
    SilentProfileSwap,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct ClosureRegimeDeclaration {
    comparison_mode: ClosureComparisonMode,
    norm_profile_id: String,
    weight_profile_id: String,
    carrier_layer_id: String,
}

impl ClosureRegimeDeclaration {
    pub fn try_new(
        comparison_mode: Option<ClosureComparisonMode>,
        norm_profile_id: impl Into<String>,
        weight_profile_id: impl Into<String>,
        carrier_layer_id: impl Into<String>,
    ) -> Result<Self, ClosureRegimeError> {
        let comparison_mode = comparison_mode.ok_or(ClosureRegimeError::UnnamedComparisonMode)?;
        Ok(Self {
            comparison_mode,
            norm_profile_id: norm_profile_id.into(),
            weight_profile_id: weight_profile_id.into(),
            carrier_layer_id: carrier_layer_id.into(),
        })
    }

    pub fn admit_exact_trichotomy(&self) -> Result<(), ClosureRegimeError> {
        match self.comparison_mode {
            ClosureComparisonMode::ExactRational => Ok(()),
            ClosureComparisonMode::ToleranceDiagnostic => {
                Err(ClosureRegimeError::ToleranceModeEmitsExactTrichotomy)
            }
        }
    }

    pub fn assert_replay_identity(&self, replayed: &Self) -> Result<(), ClosureRegimeError> {
        if self == replayed {
            Ok(())
        } else {
            Err(ClosureRegimeError::SilentProfileSwap)
        }
    }
}

// Origin: engine/crates_rs/core_policy/src/closure_regime.rs
// Claim: urn:core:crates_rs:core-policy:closure-regime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn named_regime(mode: ClosureComparisonMode) -> ClosureRegimeDeclaration {
        ClosureRegimeDeclaration::try_new(
            Some(mode),
            "norm:l1",
            "weight:uniform",
            "carrier:layer-1",
        )
        .expect("named comparison mode is admissible")
    }

    #[test]
    fn unnamed_comparison_mode_rejected() {
        let error =
            ClosureRegimeDeclaration::try_new(None, "norm:l1", "weight:uniform", "carrier:layer-1")
                .expect_err("unnamed comparison mode must be rejected");
        assert_eq!(error, ClosureRegimeError::UnnamedComparisonMode);
    }

    #[test]
    fn tolerance_mode_emitting_exact_trichotomy_rejected() {
        let tolerance = named_regime(ClosureComparisonMode::ToleranceDiagnostic);
        assert_eq!(
            tolerance.admit_exact_trichotomy(),
            Err(ClosureRegimeError::ToleranceModeEmitsExactTrichotomy)
        );
        let exact = named_regime(ClosureComparisonMode::ExactRational);
        assert_eq!(exact.admit_exact_trichotomy(), Ok(()));
    }

    #[test]
    fn silent_profile_swap_across_replay_rejected() {
        let original = named_regime(ClosureComparisonMode::ExactRational);
        let swapped = ClosureRegimeDeclaration::try_new(
            Some(ClosureComparisonMode::ExactRational),
            "norm:l1",
            "weight:swapped",
            "carrier:layer-1",
        )
        .expect("named comparison mode is admissible");
        assert_eq!(
            original.assert_replay_identity(&swapped),
            Err(ClosureRegimeError::SilentProfileSwap)
        );
        assert_eq!(original.assert_replay_identity(&original), Ok(()));
    }
}
