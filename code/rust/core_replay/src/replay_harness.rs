//! T3 primal-dual identity replay over exact rationals.
//!
//! The packet carries a complete claim: `d0`, `omega`, the repair `alpha`, the
//! primal residual, the dual witness `phi`, and the reported value. The verifier
//! does not search or approximate. It hands the claim to the Phi1 owner,
//! [`Phi1Functional::verify_exact_certificate`], which compares it exactly under
//! unit weights (`|phi_i| <= 1`, `d0^T phi = 0`, residual and pairing equal to
//! the reported value). There is no tolerance: a claim is equal or it is not.

use num_rational::BigRational;
use num_traits::{One, Zero};
use core_functional::phi1::{ExactPhi1Certificate, ExactPhi1CertificateError, Phi1Functional};
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Domain tag bound into every packet hash; bump it when the encoding changes.
const PACKET_HASH_DOMAIN: &[u8] = b"core_replay:t3-packet:v2:exact-rational\0";

/// A replay packet containing the complete exact claim for T3 identity verification.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReplayPacket {
    /// Coboundary matrix, row-major: one row per coordinate of `omega`.
    pub d0: Vec<Vec<BigRational>>,
    pub omega: Vec<BigRational>,
    pub alpha: Vec<BigRational>,
    /// Claimed residual `omega - d0 alpha`; compared, never recomputed into the claim.
    pub primal_residual: Vec<BigRational>,
    /// Dual witness.
    pub phi: Vec<BigRational>,
    /// Claimed Phi1 value under unit weights.
    pub reported_value: BigRational,
    pub carrier_hash: [u8; 32],
}

/// The result of a T3 verification attempt.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerificationAudit {
    pub timestamp: u64,
    pub packet_hash: [u8; 32],
    /// The exactly verified Phi1 value; present only when `status` is `Admitted`.
    pub verified_value: Option<BigRational>,
    /// Stable reason code; present only when `status` is not `Admitted`.
    pub refusal: Option<String>,
    pub status: VerificationStatus,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum VerificationStatus {
    Admitted,
    Rejected,
    Inconclusive,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Error)]
pub enum ReplayPacketValidationError {
    #[error("d0 rows must match omega length")]
    D0CoreDimensionMismatch,
    #[error("every d0 row must match alpha length")]
    D0AlphaDimensionMismatch,
    #[error("phi length must match omega length")]
    PhiOmegaDimensionMismatch,
    #[error("primal residual length must match omega length")]
    ResidualOmegaDimensionMismatch,
    #[error("every rational must have a nonzero denominator")]
    ZeroDenominator,
    #[error("packet cannot be empty (zero length)")]
    EmptyPacket,
}

impl ReplayPacketValidationError {
    pub fn reason_code(self) -> &'static str {
        match self {
            Self::D0CoreDimensionMismatch => "T3_PACKET_D0_CORE_DIMENSION_MISMATCH",
            Self::D0AlphaDimensionMismatch => "T3_PACKET_D0_ALPHA_DIMENSION_MISMATCH",
            Self::PhiOmegaDimensionMismatch => "T3_PACKET_PHI_CORE_DIMENSION_MISMATCH",
            Self::ResidualOmegaDimensionMismatch => "T3_PACKET_RESIDUAL_CORE_DIMENSION_MISMATCH",
            Self::ZeroDenominator => "T3_PACKET_ZERO_DENOMINATOR",
            Self::EmptyPacket => "T3_PACKET_EMPTY",
        }
    }
}

fn certificate_shape_refusal(error: &ExactPhi1CertificateError) -> Option<(&'static str, VerificationStatus)> {
    use ExactPhi1CertificateError as E;
    use VerificationStatus::Inconclusive;
    match error {
        E::ZeroRationalDenominator => Some(("T3_CERT_ZERO_DENOMINATOR", Inconclusive)),
        E::CochainDimensionMismatch => Some(("T3_CERT_DIMENSION_MISMATCH", Inconclusive)),
        E::D0RowMismatch { .. } => Some(("T3_CERT_D0_ROW_MISMATCH", Inconclusive)),
        E::D0ColumnMismatch { .. } => Some(("T3_CERT_D0_COLUMN_MISMATCH", Inconclusive)),
        E::NonPositiveWeight { .. } => Some(("T3_CERT_NON_POSITIVE_WEIGHT", Inconclusive)),
        _ => None,
    }
}

/// Stable reason code and status for a refusal from the Phi1 owner.
/// Shape errors cannot be judged (`Inconclusive`); value mismatches are `Rejected`.
fn certificate_refusal(error: &ExactPhi1CertificateError) -> (&'static str, VerificationStatus) {
    if let Some(shape) = certificate_shape_refusal(error) {
        return shape;
    }
    use ExactPhi1CertificateError as E;
    use VerificationStatus::Rejected;
    match error {
        E::PrimalResidualMismatch { .. } => ("T3_CERT_PRIMAL_RESIDUAL_MISMATCH", Rejected),
        E::DualAnnihilatorMismatch { .. } => ("T3_CERT_DUAL_ANNIHILATOR_MISMATCH", Rejected),
        E::DualNormBoundViolation { .. } => ("T3_CERT_DUAL_NORM_BOUND_VIOLATION", Rejected),
        E::NegativeReportedValue => ("T3_CERT_NEGATIVE_REPORTED_VALUE", Rejected),
        E::PrimalValueMismatch => ("T3_CERT_PRIMAL_VALUE_MISMATCH", Rejected),
        _ => ("T3_CERT_DUAL_VALUE_MISMATCH", Rejected),
    }
}

/// Canonical text of a rational: reduced, positive denominator, integers without
/// a slash. Equal rationals give equal text, so there is no `-0`/`0` aliasing.
/// A zero denominator has no canonical value; it is marked and refused by `validate`.
fn canonical_rational(value: &BigRational) -> String {
    if value.denom().is_zero() {
        return format!("invalid:{}/0", value.numer());
    }
    let reduced = BigRational::new(value.numer().clone(), value.denom().clone());
    if reduced.denom().is_one() {
        reduced.numer().to_string()
    } else {
        format!("{}/{}", reduced.numer(), reduced.denom())
    }
}

fn hash_len(hasher: &mut blake3::Hasher, len: usize) {
    hasher.update(&(len as u64).to_le_bytes());
}

fn hash_rational(hasher: &mut blake3::Hasher, value: &BigRational) {
    let text = canonical_rational(value);
    hash_len(hasher, text.len());
    hasher.update(text.as_bytes());
}

fn hash_vector(hasher: &mut blake3::Hasher, tag: &[u8], values: &[BigRational]) {
    hasher.update(tag);
    hash_len(hasher, values.len());
    for value in values {
        hash_rational(hasher, value);
    }
}

impl ReplayPacket {
    /// Validates dimensions and denominators of the packet.
    pub fn validate(&self) -> Result<(), ReplayPacketValidationError> {
        if self.omega.is_empty() || self.phi.is_empty() {
            return Err(ReplayPacketValidationError::EmptyPacket);
        }
        if self.d0.len() != self.omega.len() {
            return Err(ReplayPacketValidationError::D0CoreDimensionMismatch);
        }
        if self.d0.iter().any(|row| row.len() != self.alpha.len()) {
            return Err(ReplayPacketValidationError::D0AlphaDimensionMismatch);
        }
        if self.phi.len() != self.omega.len() {
            return Err(ReplayPacketValidationError::PhiOmegaDimensionMismatch);
        }
        if self.primal_residual.len() != self.omega.len() {
            return Err(ReplayPacketValidationError::ResidualOmegaDimensionMismatch);
        }
        let zero_denominator = self
            .d0
            .iter()
            .flatten()
            .chain(&self.omega)
            .chain(&self.alpha)
            .chain(&self.primal_residual)
            .chain(&self.phi)
            .chain(std::iter::once(&self.reported_value))
            .any(|value| value.denom().is_zero());
        if zero_denominator {
            return Err(ReplayPacketValidationError::ZeroDenominator);
        }
        Ok(())
    }

    /// Canonical BLAKE3 hash over the exact packet: a domain tag, the shapes, every
    /// rational as length-prefixed canonical text, and the carrier hash.
    pub fn compute_hash(&self) -> [u8; 32] {
        let mut hasher = blake3::Hasher::new();
        hasher.update(PACKET_HASH_DOMAIN);
        hasher.update(b"d0");
        hash_len(&mut hasher, self.d0.len());
        for row in &self.d0 {
            hash_vector(&mut hasher, b"row", row);
        }
        hash_vector(&mut hasher, b"omega", &self.omega);
        hash_vector(&mut hasher, b"alpha", &self.alpha);
        hash_vector(&mut hasher, b"residual", &self.primal_residual);
        hash_vector(&mut hasher, b"phi", &self.phi);
        hasher.update(b"value");
        hash_rational(&mut hasher, &self.reported_value);
        hasher.update(b"carrier");
        hasher.update(&self.carrier_hash);
        *hasher.finalize().as_bytes()
    }

    /// The unit-weight Phi1 certificate this packet claims.
    fn certificate(&self) -> ExactPhi1Certificate {
        ExactPhi1Certificate {
            omega: self.omega.clone(),
            d0: self.d0.clone(),
            weights: vec![BigRational::one(); self.omega.len()],
            alpha: self.alpha.clone(),
            primal_residual: self.primal_residual.clone(),
            dual_witness: self.phi.clone(),
            reported_value: self.reported_value.clone(),
        }
    }
}

pub struct T3Verifier;

impl T3Verifier {
    /// Verifies the T3 primal-dual identity exactly. No tolerance exists.
    pub fn verify(packet: &ReplayPacket) -> VerificationAudit {
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();
        let packet_hash = packet.compute_hash();
        let refused = |code: &str, status| VerificationAudit {
            timestamp,
            packet_hash,
            verified_value: None,
            refusal: Some(code.to_string()),
            status,
        };

        if let Err(error) = packet.validate() {
            return refused(error.reason_code(), VerificationStatus::Inconclusive);
        }
        match Phi1Functional::verify_exact_certificate(packet.certificate()) {
            Ok(verified) => VerificationAudit {
                timestamp,
                packet_hash,
                verified_value: Some(verified.value().clone()),
                refusal: None,
                status: VerificationStatus::Admitted,
            },
            Err(error) => {
                let (code, status) = certificate_refusal(&error);
                refused(code, status)
            }
        }
    }
}

// Origin: engine/crates_rs/core_replay/src/replay_harness.rs
// Claim: urn:core:crates_rs:core-replay:replay-harness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    fn q(numer: i64, denom: i64) -> BigRational {
        BigRational::new(BigInt::from(numer), BigInt::from(denom))
    }

    fn ints(values: &[i64]) -> Vec<BigRational> {
        values.iter().map(|value| q(*value, 1)).collect()
    }

    /// d0 = [[1],[1]], omega = [1,0], alpha = [1/2]: residual [1/2,-1/2], Phi1 = 1,
    /// dual phi = [1,-1] (d0^T phi = 0, |phi| <= 1, pairing 1).
    fn toy_packet() -> ReplayPacket {
        ReplayPacket {
            d0: vec![ints(&[1]), ints(&[1])],
            omega: ints(&[1, 0]),
            alpha: vec![q(1, 2)],
            primal_residual: vec![q(1, 2), q(-1, 2)],
            phi: ints(&[1, -1]),
            reported_value: q(1, 1),
            carrier_hash: [0u8; 32],
        }
    }

    #[test]
    fn test_toy_parity_verification() {
        let audit = T3Verifier::verify(&toy_packet());
        assert_eq!(audit.status, VerificationStatus::Admitted);
        assert_eq!(audit.verified_value, Some(q(1, 1)));
        assert_eq!(audit.refusal, None);
    }

    #[test]
    fn test_validation_dimension_mismatch() {
        let packet = ReplayPacket {
            omega: ints(&[1, 0, 0]),
            ..toy_packet()
        };
        assert_eq!(
            packet.validate(),
            Err(ReplayPacketValidationError::D0CoreDimensionMismatch)
        );
        let audit = T3Verifier::verify(&packet);
        assert_eq!(audit.status, VerificationStatus::Inconclusive);
        assert_eq!(
            audit.refusal.as_deref(),
            Some("T3_PACKET_D0_CORE_DIMENSION_MISMATCH")
        );
        assert_eq!(audit.verified_value, None);
    }

    #[test]
    fn test_validation_zero_denominator() {
        let packet = ReplayPacket {
            reported_value: BigRational::new_raw(BigInt::from(1), BigInt::from(0)),
            ..toy_packet()
        };
        assert_eq!(
            packet.validate(),
            Err(ReplayPacketValidationError::ZeroDenominator)
        );
        let audit = T3Verifier::verify(&packet);
        assert_eq!(audit.status, VerificationStatus::Inconclusive);
        assert_eq!(audit.refusal.as_deref(), Some("T3_PACKET_ZERO_DENOMINATOR"));
    }

    #[test]
    fn test_validation_empty_packet() {
        let packet = ReplayPacket {
            d0: vec![],
            omega: vec![],
            alpha: vec![],
            primal_residual: vec![],
            phi: vec![],
            reported_value: q(0, 1),
            carrier_hash: [0u8; 32],
        };
        assert_eq!(
            packet.validate(),
            Err(ReplayPacketValidationError::EmptyPacket)
        );
        assert_eq!(
            T3Verifier::verify(&packet).status,
            VerificationStatus::Inconclusive
        );
    }

    /// The old float verifier admitted any claim within 1e-9. An exact claim off by
    /// 1/10^12 is rejected.
    #[test]
    fn test_near_miss_is_rejected_not_admitted() {
        let tiny = q(1, 1_000_000_000_000);
        let packet = ReplayPacket {
            reported_value: q(1, 1) + tiny,
            ..toy_packet()
        };
        let audit = T3Verifier::verify(&packet);
        assert_eq!(audit.status, VerificationStatus::Rejected);
        assert_eq!(audit.verified_value, None);
    }

    /// alpha = 2 with an honest residual [-1,-2] has primal value 3, but the dual
    /// pairing is 1, so the claim of 3 is not certified.
    #[test]
    fn test_well_formed_but_rejected() {
        let packet = ReplayPacket {
            alpha: ints(&[2]),
            primal_residual: ints(&[-1, -2]),
            reported_value: q(3, 1),
            ..toy_packet()
        };
        let audit = T3Verifier::verify(&packet);
        assert_eq!(audit.status, VerificationStatus::Rejected);
        assert_eq!(
            audit.refusal.as_deref(),
            Some("T3_CERT_DUAL_VALUE_MISMATCH")
        );
    }

    #[test]
    fn test_dual_not_annihilating_is_rejected() {
        let packet = ReplayPacket {
            phi: ints(&[1, 0]),
            ..toy_packet()
        };
        let audit = T3Verifier::verify(&packet);
        assert_eq!(audit.status, VerificationStatus::Rejected);
        assert_eq!(
            audit.refusal.as_deref(),
            Some("T3_CERT_DUAL_ANNIHILATOR_MISMATCH")
        );
    }

    /// Equal rationals hash equally whatever their raw representation, including
    /// zero written as 0/5 or 0/-3 (the analogue of float -0.0 vs 0.0).
    #[test]
    fn test_hash_is_canonical_over_equal_rationals() {
        let base = toy_packet();
        let unreduced = ReplayPacket {
            alpha: vec![BigRational::new_raw(BigInt::from(-3), BigInt::from(-6))],
            omega: vec![
                q(1, 1),
                BigRational::new_raw(BigInt::from(0), BigInt::from(-3)),
            ],
            ..toy_packet()
        };
        assert_eq!(base.compute_hash(), unreduced.compute_hash());

        let different = ReplayPacket {
            alpha: vec![q(1, 3)],
            ..toy_packet()
        };
        assert_ne!(base.compute_hash(), different.compute_hash());

        let other_carrier = ReplayPacket {
            carrier_hash: [1u8; 32],
            ..toy_packet()
        };
        assert_ne!(base.compute_hash(), other_carrier.compute_hash());
    }

    /// Shapes are bound: moving one value between d0 rows changes the hash.
    #[test]
    fn test_hash_binds_shape() {
        let wide = ReplayPacket {
            d0: vec![ints(&[1, 1]), vec![]],
            ..toy_packet()
        };
        let tall = ReplayPacket {
            d0: vec![ints(&[1]), ints(&[1])],
            ..toy_packet()
        };
        assert_ne!(wide.compute_hash(), tall.compute_hash());
    }

    #[test]
    fn test_packet_round_trips_through_json() {
        let packet = toy_packet();
        let json = serde_json::to_string(&packet).expect("serialize");
        let back: ReplayPacket = serde_json::from_str(&json).expect("deserialize");
        assert_eq!(packet, back);
        assert_eq!(packet.compute_hash(), back.compute_hash());
    }
}
