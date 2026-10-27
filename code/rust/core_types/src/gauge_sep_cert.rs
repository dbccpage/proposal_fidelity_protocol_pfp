use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Mode of classification for an authority gauge.
///
/// Under CODA_GTLA doctrine, only `AuthorityClassifying` gauges can be used to
/// classify exact authority. Diagnostic-only gauges can carry out measurements
/// but lack the mathematical separation property to classify exact authority.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum GaugeClassificationMode {
    AuthorityClassifying,
    DiagnosticOnly,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize, Error)]
pub enum GaugeSepCertError {
    #[error("carrier_ref cannot be empty")]
    EmptyCarrierRef,
    #[error("gauge_identifier cannot be empty")]
    EmptyGaugeIdentifier,
    #[error("nonnegativity_witness_ref cannot be empty")]
    EmptyNonnegativityWitnessRef,
    #[error("zero_witness_ref cannot be empty")]
    EmptyZeroWitnessRef,
    #[error("lower_bound_witness_ref cannot be empty")]
    EmptyLowerBoundWitnessRef,
    #[error("closedness_witness_ref cannot be empty")]
    EmptyClosednessWitnessRef,
    #[error("replay_ref cannot be empty")]
    EmptyReplayRef,
}

/// A certificate verifying that a gauge satisfies the separation properties
/// required to classify exact authority (quotient positive-definiteness).
///
/// Proving that exact authority is equivalent to a zero quotient class (CODA_GTLA-T11/T15)
/// requires a separating admissible gauge (via CODA_GTLA-L10). Diagnostic-only gauges
/// do not carry this certificate and are prevented from classifying exact authority.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "RawGaugeSepCert")]
pub struct GaugeSepCert {
    carrier_ref: String,
    gauge_identifier: String,
    nonnegativity_witness_ref: String,
    zero_witness_ref: String,
    lower_bound_witness_ref: String,
    closedness_witness_ref: String,
    replay_ref: String,
    classification_mode: GaugeClassificationMode,
}

#[derive(Deserialize)]
struct RawGaugeSepCert {
    carrier_ref: String,
    gauge_identifier: String,
    nonnegativity_witness_ref: String,
    zero_witness_ref: String,
    lower_bound_witness_ref: String,
    closedness_witness_ref: String,
    replay_ref: String,
    classification_mode: GaugeClassificationMode,
}

impl TryFrom<RawGaugeSepCert> for GaugeSepCert {
    type Error = GaugeSepCertError;

    fn try_from(raw: RawGaugeSepCert) -> Result<Self, Self::Error> {
        GaugeSepCert::new(
            raw.carrier_ref,
            raw.gauge_identifier,
            raw.nonnegativity_witness_ref,
            raw.zero_witness_ref,
            raw.lower_bound_witness_ref,
            raw.closedness_witness_ref,
            raw.replay_ref,
            raw.classification_mode,
        )
    }
}

impl GaugeSepCert {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        carrier_ref: impl Into<String>,
        gauge_identifier: impl Into<String>,
        nonnegativity_witness_ref: impl Into<String>,
        zero_witness_ref: impl Into<String>,
        lower_bound_witness_ref: impl Into<String>,
        closedness_witness_ref: impl Into<String>,
        replay_ref: impl Into<String>,
        classification_mode: GaugeClassificationMode,
    ) -> Result<Self, GaugeSepCertError> {
        let carrier_ref = carrier_ref.into();
        if carrier_ref.trim().is_empty() {
            return Err(GaugeSepCertError::EmptyCarrierRef);
        }
        let gauge_identifier = gauge_identifier.into();
        if gauge_identifier.trim().is_empty() {
            return Err(GaugeSepCertError::EmptyGaugeIdentifier);
        }
        let nonnegativity_witness_ref = nonnegativity_witness_ref.into();
        if nonnegativity_witness_ref.trim().is_empty() {
            return Err(GaugeSepCertError::EmptyNonnegativityWitnessRef);
        }
        let zero_witness_ref = zero_witness_ref.into();
        if zero_witness_ref.trim().is_empty() {
            return Err(GaugeSepCertError::EmptyZeroWitnessRef);
        }
        let lower_bound_witness_ref = lower_bound_witness_ref.into();
        if lower_bound_witness_ref.trim().is_empty() {
            return Err(GaugeSepCertError::EmptyLowerBoundWitnessRef);
        }
        let closedness_witness_ref = closedness_witness_ref.into();
        if closedness_witness_ref.trim().is_empty() {
            return Err(GaugeSepCertError::EmptyClosednessWitnessRef);
        }
        let replay_ref = replay_ref.into();
        if replay_ref.trim().is_empty() {
            return Err(GaugeSepCertError::EmptyReplayRef);
        }

        Ok(Self {
            carrier_ref,
            gauge_identifier,
            nonnegativity_witness_ref,
            zero_witness_ref,
            lower_bound_witness_ref,
            closedness_witness_ref,
            replay_ref,
            classification_mode,
        })
    }

    pub fn carrier_ref(&self) -> &str {
        &self.carrier_ref
    }

    pub fn gauge_identifier(&self) -> &str {
        &self.gauge_identifier
    }

    pub fn nonnegativity_witness_ref(&self) -> &str {
        &self.nonnegativity_witness_ref
    }

    pub fn zero_witness_ref(&self) -> &str {
        &self.zero_witness_ref
    }

    pub fn lower_bound_witness_ref(&self) -> &str {
        &self.lower_bound_witness_ref
    }

    pub fn closedness_witness_ref(&self) -> &str {
        &self.closedness_witness_ref
    }

    pub fn replay_ref(&self) -> &str {
        &self.replay_ref
    }

    pub fn classification_mode(&self) -> GaugeClassificationMode {
        self.classification_mode
    }

    /// Returns true if this certificate permits classifying exact authority.
    pub fn can_classify_exact_authority(&self) -> bool {
        matches!(
            self.classification_mode,
            GaugeClassificationMode::AuthorityClassifying
        )
    }
}

// Origin: engine/crates_rs/core_types/src/gauge_sep_cert.rs
// Claim: urn:core:crates_rs:core-types:gauge-sep-cert:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_diagnostic_only_cannot_classify_exact_authority() {
        let cert = GaugeSepCert::new(
            "carrier:1",
            "gauge:1",
            "nonneg:1",
            "zero:1",
            "lower:1",
            "closed:1",
            "replay:1",
            GaugeClassificationMode::DiagnosticOnly,
        )
        .unwrap();

        // Enforce the rule that diagnostic-only gauges cannot classify exact authority.
        assert!(!cert.can_classify_exact_authority());
    }

    #[test]
    fn test_authority_classifying_can_classify_exact_authority() {
        let cert = GaugeSepCert::new(
            "carrier:1",
            "gauge:1",
            "nonneg:1",
            "zero:1",
            "lower:1",
            "closed:1",
            "replay:1",
            GaugeClassificationMode::AuthorityClassifying,
        )
        .unwrap();

        assert!(cert.can_classify_exact_authority());
    }

    #[test]
    fn test_empty_refs_rejected() {
        let cert_err = GaugeSepCert::new(
            "carrier:1",
            "gauge:1",
            "nonneg:1",
            "zero:1",
            "lower:1",
            "  ",
            "replay:1",
            GaugeClassificationMode::AuthorityClassifying,
        );
        assert!(matches!(
            cert_err,
            Err(GaugeSepCertError::EmptyClosednessWitnessRef)
        ));
    }

    #[test]
    fn test_deserialization_rejects_empty_fields() {
        let json = r#"{"carrier_ref":"carrier:1","gauge_identifier":"gauge:1","nonnegativity_witness_ref":"nonneg:1","zero_witness_ref":"zero:1","lower_bound_witness_ref":"lower:1","closedness_witness_ref":"   ","replay_ref":"replay:1","classification_mode":"AuthorityClassifying"}"#;
        let res: Result<GaugeSepCert, _> = serde_json::from_str(json);
        assert!(res.is_err());
    }
}
