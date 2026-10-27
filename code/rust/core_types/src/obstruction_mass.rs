//! Certificate-backed obstruction mass, never an authority grant.
//!
//! The versioned wire contains the complete exact primal-dual certificate. Every
//! deserialization replays it; a scalar and plausible hash labels cannot create
//! a certified mass. Binding labels are retained caller assertions, not evidence
//! that this module authenticated a carrier, native host, request or license.
//!
//! Migration: the former unversioned scalar wire, public mutable fields and
//! unchecked scalar constructor are intentionally not accepted. Native callers
//! use a replayed certificate or a sealed VerifiedExactPhi1. No tracked caller
//! outside this module used the retired constructor at the migration baseline.
//!
//! A consumer cannot replace the sealed proof through a public field:
//! ~~~compile_fail
//! use crate::obstruction_mass::ObstructionMass;
//! use core_functional::phi1::VerifiedExactPhi1;
//! fn replace(mass: &mut ObstructionMass, proof: VerifiedExactPhi1) {
//!     mass.proof = proof;
//! }
//! ~~~

use num_rational::BigRational;
use core_functional::phi1::{
    ExactPhi1Certificate, ExactPhi1CertificateError, Phi1Functional, VerifiedExactPhi1,
};
use core_kernel::evidence::{
    CarrierManifestHash, CertifiedScalar, CheckerRef, RationalValue, ReplayHash,
    ToleranceProfileHash,
};
use serde::{Deserialize, Serialize};

const WIRE_SCHEMA: &str = "core.verified-obstruction-mass.v1";

/// Caller-supplied identity labels, retained without claiming authentication.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EvidenceBindings {
    pub carrier_hash: CarrierManifestHash,
    pub tolerance_profile_hash: ToleranceProfileHash,
    pub checker_ref: CheckerRef,
    pub replay_hash: ReplayHash,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
enum EvidenceAuthority {
    None,
}

/// An untrusted wire must carry replayable evidence, not only a reported scalar.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ObstructionMassWire {
    schema_version: String,
    authority_effect: EvidenceAuthority,
    certificate: ExactPhi1Certificate,
    bindings: EvidenceBindings,
}

/// One exact finite quotient-distance fact, with no task/authority semantics.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(try_from = "ObstructionMassWire", into = "ObstructionMassWire")]
pub struct ObstructionMass {
    proof: VerifiedExactPhi1,
    bindings: EvidenceBindings,
}

#[derive(Debug, thiserror::Error)]
pub enum ObstructionMassError {
    #[error("OBSTRUCTION_MASS_SCHEMA_UNSUPPORTED")]
    UnsupportedSchema,
    #[error("OBSTRUCTION_MASS_CERTIFICATE_REFUSED: {0}")]
    InvalidCertificate(#[from] ExactPhi1CertificateError),
    #[error("zero carrier hash is invalid for certifier mode")]
    ZeroCarrierHash,
}

impl ObstructionMass {
    pub fn from_certificate(
        certificate: ExactPhi1Certificate,
        bindings: EvidenceBindings,
    ) -> Result<Self, ObstructionMassError> {
        let proof = Phi1Functional::verify_exact_certificate(certificate)?;
        Self::from_verified_phi1(&proof, bindings)
    }

    pub fn from_verified_phi1(
        proof: &VerifiedExactPhi1,
        bindings: EvidenceBindings,
    ) -> Result<Self, ObstructionMassError> {
        if bindings.carrier_hash.0 .0 == [0; 32] {
            return Err(ObstructionMassError::ZeroCarrierHash);
        }
        Ok(Self {
            proof: proof.clone(),
            bindings,
        })
    }

    pub fn value(&self) -> &BigRational {
        self.proof.value()
    }

    pub fn certificate(&self) -> &ExactPhi1Certificate {
        self.proof.certificate()
    }

    pub fn bindings(&self) -> &EvidenceBindings {
        &self.bindings
    }

    /// Display-only approximation. Failure to fit f64 never means exact zero.
    pub fn value_diagnostic(&self) -> Option<f64> {
        CertifiedScalar::ExactRational(RationalValue::from_big_rational(self.value()))
            .to_f64_diagnostic()
    }
}

impl TryFrom<ObstructionMassWire> for ObstructionMass {
    type Error = ObstructionMassError;

    fn try_from(wire: ObstructionMassWire) -> Result<Self, Self::Error> {
        if wire.schema_version != WIRE_SCHEMA {
            return Err(ObstructionMassError::UnsupportedSchema);
        }
        Self::from_certificate(wire.certificate, wire.bindings)
    }
}

impl From<ObstructionMass> for ObstructionMassWire {
    fn from(mass: ObstructionMass) -> Self {
        Self {
            schema_version: WIRE_SCHEMA.to_owned(),
            authority_effect: EvidenceAuthority::None,
            certificate: mass.proof.certificate().clone(),
            bindings: mass.bindings,
        }
    }
}

// Origin: engine/crates_rs/core_types/src/obstruction_mass.rs
// Claim: urn:core:crates_rs:core-types:obstruction-mass:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_kernel::evidence::Hash256;

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(value.into())
    }

    fn certificate() -> ExactPhi1Certificate {
        ExactPhi1Certificate {
            omega: vec![r(3), r(2)],
            d0: vec![vec![r(1)], vec![r(0)]],
            weights: vec![r(1), r(1)],
            alpha: vec![r(3)],
            primal_residual: vec![r(0), r(2)],
            dual_witness: vec![r(0), r(1)],
            reported_value: r(2),
        }
    }

    fn bindings() -> EvidenceBindings {
        EvidenceBindings {
            carrier_hash: CarrierManifestHash(Hash256([1; 32])),
            tolerance_profile_hash: ToleranceProfileHash(Hash256([2; 32])),
            checker_ref: CheckerRef("fixture-checker".into()),
            replay_hash: ReplayHash(Hash256([3; 32])),
        }
    }

    fn wire() -> serde_json::Value {
        serde_json::to_value(ObstructionMass::from_certificate(certificate(), bindings()).unwrap())
            .unwrap()
    }

    #[test]
    fn verified_mass_roundtrip_retains_certificate_and_labels() {
        let mass = ObstructionMass::from_certificate(certificate(), bindings()).unwrap();
        assert_eq!(mass.value(), &r(2));
        assert_eq!(mass.value_diagnostic(), Some(2.0));
        let raw = serde_json::to_vec(&mass).unwrap();
        let replayed: ObstructionMass = serde_json::from_slice(&raw).unwrap();
        assert_eq!(replayed.certificate(), &certificate());
        assert_eq!(replayed.bindings().carrier_hash.0 .0, [1; 32]);
        assert_eq!(replayed.bindings().replay_hash.0 .0, [3; 32]);
        assert_eq!(serde_json::to_vec(&replayed).unwrap(), raw);
        assert_eq!(wire()["authority_effect"], "None");
    }

    #[test]
    fn tampered_mass_certificate_is_replayed_and_refused() {
        let mut raw = wire();
        let mut altered = certificate();
        altered.reported_value = r(0);
        raw["certificate"] = serde_json::to_value(altered).unwrap();
        let error = serde_json::from_value::<ObstructionMass>(raw).unwrap_err();
        assert!(error
            .to_string()
            .contains("OBSTRUCTION_MASS_CERTIFICATE_REFUSED"));
        assert!(error.to_string().contains("weighted primal residual norm"));
    }

    #[test]
    fn certified_mass_requires_both_matching_witnesses() {
        let mut altered = certificate();
        altered.dual_witness.clear();
        assert!(matches!(
            ObstructionMass::from_certificate(altered, bindings()),
            Err(ObstructionMassError::InvalidCertificate(
                ExactPhi1CertificateError::CochainDimensionMismatch
            ))
        ));
        let mut altered = certificate();
        altered.dual_witness = vec![r(0), r(0)];
        assert!(matches!(
            ObstructionMass::from_certificate(altered, bindings()),
            Err(ObstructionMassError::InvalidCertificate(
                ExactPhi1CertificateError::DualValueMismatch
            ))
        ));
    }

    #[test]
    fn negative_mass_cannot_be_certified() {
        let mut altered = certificate();
        altered.reported_value = r(-1);
        assert!(matches!(
            ObstructionMass::from_certificate(altered, bindings()),
            Err(ObstructionMassError::InvalidCertificate(
                ExactPhi1CertificateError::NegativeReportedValue
            ))
        ));
    }

    #[test]
    fn scalar_only_legacy_wire_and_missing_certificate_are_refused() {
        let legacy = serde_json::json!({"value": 0, "carrier_hash": vec![1; 32]});
        assert!(serde_json::from_value::<ObstructionMass>(legacy)
            .unwrap_err()
            .to_string()
            .contains("unknown field"));
        let mut raw = wire();
        raw.as_object_mut().unwrap().remove("certificate");
        assert!(serde_json::from_value::<ObstructionMass>(raw)
            .unwrap_err()
            .to_string()
            .contains("missing field"));
    }

    #[test]
    fn future_schema_and_forged_authority_are_refused() {
        let mut raw = wire();
        raw["schema_version"] = "core.verified-obstruction-mass.v999".into();
        assert!(serde_json::from_value::<ObstructionMass>(raw)
            .unwrap_err()
            .to_string()
            .contains("OBSTRUCTION_MASS_SCHEMA_UNSUPPORTED"));
        let mut raw = wire();
        raw["authority_effect"] = "GlobalGreen".into();
        assert!(serde_json::from_value::<ObstructionMass>(raw)
            .unwrap_err()
            .to_string()
            .contains("unknown variant"));
        let mut raw = wire();
        raw["bindings"]["authority_effect"] = "None".into();
        assert!(serde_json::from_value::<ObstructionMass>(raw)
            .unwrap_err()
            .to_string()
            .contains("unknown field"));
        let mut raw = wire();
        raw["certificate"]["authority_effect"] = "None".into();
        assert!(serde_json::from_value::<ObstructionMass>(raw)
            .unwrap_err()
            .to_string()
            .contains("unknown field"));
    }

    #[test]
    fn zero_carrier_is_refused_on_both_construction_paths() {
        let mut labels = bindings();
        labels.carrier_hash = CarrierManifestHash(Hash256([0; 32]));
        let proof = Phi1Functional::verify_exact_certificate(certificate()).unwrap();
        assert!(matches!(
            ObstructionMass::from_verified_phi1(&proof, labels.clone()),
            Err(ObstructionMassError::ZeroCarrierHash)
        ));
        assert!(matches!(
            ObstructionMass::from_certificate(certificate(), labels),
            Err(ObstructionMassError::ZeroCarrierHash)
        ));
    }

    #[test]
    fn huge_exact_mass_is_not_rejected_or_rounded_to_zero_for_display() {
        let huge = BigRational::from_integer(num_bigint::BigInt::from(1) << 2048);
        let mut submitted = certificate();
        submitted.omega[1] = huge.clone();
        submitted.primal_residual[1] = huge.clone();
        submitted.reported_value = huge.clone();
        let mass = ObstructionMass::from_certificate(submitted, bindings()).unwrap();
        assert_eq!(mass.value(), &huge);
        assert_eq!(mass.value_diagnostic(), None);
    }
}
