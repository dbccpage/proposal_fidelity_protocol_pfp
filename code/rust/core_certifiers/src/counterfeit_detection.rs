//! Counterfeit Packet Detection
//!
//! Implements the **Exactness Fraud Criterion** from Paper 029 (AI Control):
//! a `CheckedPacket` claiming `ExactRepair` status must have obstruction mass
//! and closure defect exactly zero. Any mismatch is counterfeit.
//!
//! Both detectors decide on exact rational predicates of the evidence. Neither
//! projects to `f64`, reads the sign of an interval midpoint, or relaxes a
//! test by a tolerance band.

use crate::checked_packet::CheckedPacket;
use crate::closure_certificate::{has_zero_denominator, ClosureStatus};
use num_traits::Zero;
use core_kernel::evidence::Hash256;
use core_policy::trichotomy::ObstructionDiagnosticClass;
use serde::{Deserialize, Serialize};

/// Why a packet was judged counterfeit.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum CounterfeitReason {
    /// Claims `ExactRepair` but obstruction mass is not exactly zero.
    ObstructionMassFraud,
    /// Claims `ExactRepair` but closure defect `Gamma2` is not exactly zero.
    ClosureDefectFraud,
    /// Packet `carrier_hash` differs from closure certificate `carrier_hash`.
    CarrierHashTamper,
    /// Closure certificate claims `Closed` but `Gamma2` is not exactly zero.
    ClosureInconsistency,
    /// Obstruction mass has a zero denominator (no value).
    NonFiniteObstructionMass,
    /// Obstruction mass is not certified non-negative: an exact value below
    /// zero, or an interval with `lower < 0` (e.g. `[-1, 2]`) or `upper < lower`.
    NegativeObstructionMass,
    /// Closure defect has a zero denominator (no value).
    NonFiniteClosureDefect,
    /// Closure defect is not certified non-negative (as for the mass).
    NegativeClosureDefect,
    MissingReplayHash,
}

/// Result of counterfeit detection on a `CheckedPacket`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CounterfeitVerdict {
    pub is_counterfeit: bool,
    pub reasons: Vec<CounterfeitReason>,
}

impl CounterfeitVerdict {
    fn no_counterfeit_detected() -> Self {
        Self {
            is_counterfeit: false,
            reasons: vec![],
        }
    }

    fn counterfeit(reasons: Vec<CounterfeitReason>) -> Self {
        Self {
            is_counterfeit: true,
            reasons,
        }
    }
}

fn check_packet_headers(
    packet: &CheckedPacket,
    closure_cert: &crate::closure_certificate::ClosureCertificate,
    reasons: &mut Vec<CounterfeitReason>,
) {
    if packet.replay_hash().0 == Hash256([0u8; 32])
        || closure_cert.replay_hash.0 == Hash256([0u8; 32])
    {
        reasons.push(CounterfeitReason::MissingReplayHash);
    }

    if packet.carrier_hash() != &closure_cert.carrier_hash {
        reasons.push(CounterfeitReason::CarrierHashTamper);
    }
}

fn check_exact_zero_claims(
    packet: &CheckedPacket,
    closure_status: ClosureStatus,
    mass: &Option<num_rational::BigRational>,
    gamma: &Option<num_rational::BigRational>,
    reasons: &mut Vec<CounterfeitReason>,
) {
    if closure_status == ClosureStatus::Closed {
        if let Some(ref g) = gamma {
            if !g.is_zero() {
                reasons.push(CounterfeitReason::ClosureInconsistency);
            }
        }
    }

    if packet.status() == ObstructionDiagnosticClass::ExactRepair {
        if let Some(ref m) = mass {
            if !m.is_zero() {
                reasons.push(CounterfeitReason::ObstructionMassFraud);
            }
        }
        if let Some(ref g) = gamma {
            if !g.is_zero() {
                reasons.push(CounterfeitReason::ClosureDefectFraud);
            }
        }
    }
}

fn finalize_verdict(reasons: Vec<CounterfeitReason>) -> CounterfeitVerdict {
    if reasons.is_empty() {
        CounterfeitVerdict::no_counterfeit_detected()
    } else {
        CounterfeitVerdict::counterfeit(reasons)
    }
}

/// Detect counterfeit packets using the Exactness Fraud Criterion in exact rational mode.
pub fn detect_exact(
    packet: &CheckedPacket,
    closure_cert: &crate::closure_certificate::ClosureCertificate,
) -> CounterfeitVerdict {
    let mut reasons = Vec::new();
    check_packet_headers(packet, closure_cert, &mut reasons);

    let mass_opt = packet.obstruction_mass().try_exact_rational();
    let mass = match mass_opt {
        Some(m) => {
            if m < num_rational::BigRational::zero() {
                reasons.push(CounterfeitReason::NegativeObstructionMass);
            }
            Some(m)
        }
        None => {
            reasons.push(CounterfeitReason::NonFiniteObstructionMass);
            None
        }
    };

    let gamma_opt = closure_cert.gamma_2.try_exact_rational();
    let gamma = match gamma_opt {
        Some(g) => {
            if g < num_rational::BigRational::zero() {
                reasons.push(CounterfeitReason::NegativeClosureDefect);
            }
            Some(g)
        }
        None => {
            reasons.push(CounterfeitReason::NonFiniteClosureDefect);
            None
        }
    };

    check_exact_zero_claims(
        packet,
        closure_cert.closure_status,
        &mass,
        &gamma,
        &mut reasons,
    );
    finalize_verdict(reasons)
}

fn check_approx_zero_claims(
    packet: &CheckedPacket,
    closure_status: ClosureStatus,
    mass_exactly_zero: bool,
    gamma_exactly_zero: bool,
    reasons: &mut Vec<CounterfeitReason>,
) {
    if closure_status == ClosureStatus::Closed && !gamma_exactly_zero {
        reasons.push(CounterfeitReason::ClosureInconsistency);
    }

    if packet.status() == ObstructionDiagnosticClass::ExactRepair {
        if !mass_exactly_zero {
            reasons.push(CounterfeitReason::ObstructionMassFraud);
        }
        if !gamma_exactly_zero {
            reasons.push(CounterfeitReason::ClosureDefectFraud);
        }
    }
}

/// Detect counterfeit packets when the evidence may be an interval enclosure.
///
/// Every test is an exact predicate on the certified evidence:
/// - non-finite: a zero denominator in the value or in either endpoint;
/// - negative: not `is_nonnegative_exact_or_interval()`, so an interval is
///   non-negative only when `0 <= lower <= upper` (`[-1, 2]` is refused);
/// - `Closed` and `ExactRepair` are exact-zero claims, checked with
///   `is_exactly_zero()` (an interval is zero only when both endpoints are).
///
/// No `f64` projection, midpoint or tolerance is consulted, so a value below
/// the `f64` floor cannot read as zero and a straddling interval cannot read
/// as non-negative.
pub fn detect_approx(
    packet: &CheckedPacket,
    closure_cert: &crate::closure_certificate::ClosureCertificate,
) -> CounterfeitVerdict {
    let mut reasons = Vec::new();
    check_packet_headers(packet, closure_cert, &mut reasons);

    let mass = packet.obstruction_mass();
    if has_zero_denominator(mass) {
        reasons.push(CounterfeitReason::NonFiniteObstructionMass);
    } else if !mass.is_nonnegative_exact_or_interval() {
        reasons.push(CounterfeitReason::NegativeObstructionMass);
    }

    let gamma = &closure_cert.gamma_2;
    if has_zero_denominator(gamma) {
        reasons.push(CounterfeitReason::NonFiniteClosureDefect);
    } else if !gamma.is_nonnegative_exact_or_interval() {
        reasons.push(CounterfeitReason::NegativeClosureDefect);
    }

    check_approx_zero_claims(
        packet,
        closure_cert.closure_status,
        mass.is_exactly_zero(),
        gamma.is_exactly_zero(),
        &mut reasons,
    );
    finalize_verdict(reasons)
}

// Origin: engine/crates_rs/core_certifiers/src/counterfeit_detection.rs
// Claim: urn:core:crates_rs:core-certifiers:counterfeit-detection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda0d4c84b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda0d4c84b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora0d4c84b {
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
impl BoundaryErrora0d4c84b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora0d4c84b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora0d4c84b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda0d4c84b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora0d4c84b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora0d4c84b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora0d4c84b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora0d4c84b::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use num_bigint::BigInt;
    use num_rational::BigRational;
    use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional};
    use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
    use core_policy::trichotomy::{classify_exact, TrichotomyOutcome};
    use core_types::EvidenceCeiling;

    use super::*;
    use crate::checked_packet::*;
    use crate::closure_certificate::{ClosureCertificate, ClosureStatus};

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn make_packet(
        gamma_2_num: i64,
        gamma_2_den: i64,
        carrier_hash: [u8; 32],
        cert_carrier_hash: [u8; 32],
        closure_status: ClosureStatus,
        closure_replay_hash: [u8; 32],
    ) -> (CheckedPacket, ClosureCertificate) {
        let phi1 = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
            omega: vec![r(1)],
            d0: vec![vec![r(1)]],
            weights: vec![r(1)],
            alpha: vec![r(1)],
            primal_residual: vec![r(0)],
            dual_witness: vec![r(0)],
            reported_value: r(0),
        })
        .unwrap();
        let complex =
            ExactCochainComplexQ::try_new(1, 1, 1, phi1.d0().to_vec(), vec![vec![r(0)]]).unwrap();
        let residual =
            DegreeOneResidualQ::try_new(&complex, phi1.primal_residual().to_vec()).unwrap();
        let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual).unwrap();

        let TrichotomyOutcome::Classified(trichotomy) = classify_exact(&phi1, &gamma2) else {
            panic!("exact packet evidence must classify");
        };
        let cert = ClosureCertificate {
            gamma_2: CertifiedScalar::ExactRational(RationalValue {
                numerator: BigInt::from(gamma_2_num),
                denominator: BigInt::from(gamma_2_den),
            }),
            closure_status,
            carrier_hash: CarrierManifestHash(Hash256(cert_carrier_hash)),
            checker_ref: CheckerRef("test".to_string()),
            replay_hash: ReplayHash(Hash256(closure_replay_hash)),
        };
        let pkt = CheckedPacket::new_checked(
            CheckedPacketArgs {
                packet_id: Hash256([0u8; 32]),
                evidence_refs: vec![EvidenceRef(Hash256([0u8; 32]))],
                checker_ref: CheckerRef("test".to_string()),
                schema_hash: Hash256([0u8; 32]),
                carrier_hash: CarrierManifestHash(Hash256(carrier_hash)),
                boundary_maps_hash: BoundaryMapsHash(Hash256([0u8; 32])),
                weights_and_gauges_hash: WeightsAndGaugesHash(Hash256([0u8; 32])),
                submitted_defect_hash: DefectFieldHash(Hash256([0u8; 32])),
                phi1_certificate_ref: CertificateRef(Hash256([0xCC; 32])),
                closure_certificate_ref: CertificateRef(Hash256([0xDD; 32])),
                observer_boundary_hash: ObserverBoundaryHash(Hash256([0u8; 32])),
                tolerance_profile_hash: ToleranceProfileHash(Hash256([0u8; 32])),
                replay_hash: ReplayHash(Hash256(REPLAY)),
                certificate_status: CertificateVerdict::Verified,
                checked_scope: CheckedClaimScope {
                    claim_kind: CheckedClaimKind::ObstructionSummary,
                    authority_ceiling: EvidenceCeiling::BoundaryChecked,
                    law_refs: vec![],
                },
            },
            &phi1,
            &trichotomy,
        )
        .unwrap();
        (pkt, cert)
    }

    const HASH_A: [u8; 32] = [0xAA; 32];
    const HASH_B: [u8; 32] = [0xBB; 32];
    const REPLAY: [u8; 32] = [0x11; 32];

    #[test]
    fn test_counterfeit_rejects_zero_closure_replay_hash_in_production_mode() {
        let (pkt, cert) = make_packet(0, 1, HASH_A, HASH_A, ClosureStatus::Closed, [0u8; 32]);
        let verdict = detect_exact(&pkt, &cert);
        assert!(verdict.is_counterfeit);
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::MissingReplayHash));
    }

    #[test]
    fn test_counterfeit_rejects_negative_closure_defect() {
        let (pkt, cert) = make_packet(-1, 1, HASH_A, HASH_A, ClosureStatus::Closed, REPLAY);
        let verdict = detect_exact(&pkt, &cert);
        assert!(verdict.is_counterfeit);
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::NegativeClosureDefect));
    }

    #[test]
    fn test_counterfeit_reports_multiple_reasons() {
        let (pkt, cert) = make_packet(-1, 1, HASH_A, HASH_B, ClosureStatus::Closed, [0u8; 32]);
        let verdict = detect_exact(&pkt, &cert);
        assert!(verdict.is_counterfeit);
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::NegativeClosureDefect));
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::CarrierHashTamper));
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::MissingReplayHash));
    }

    #[test]
    fn test_counterfeit_exact_gamma2_fraud() {
        // Packet claims ExactRepair (obstruction = 0), but certified closure defect Gamma2 is > 0 (e.g. 1/2)
        let (pkt, cert) = make_packet(1, 2, HASH_A, HASH_A, ClosureStatus::Open, REPLAY);
        let verdict = detect_exact(&pkt, &cert);
        assert!(verdict.is_counterfeit);
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::ClosureDefectFraud));
    }

    #[test]
    fn test_counterfeit_closure_status_inconsistency() {
        // Closure certificate claims Closed, but Gamma2 is > 0 (e.g. 1/1000)
        let (pkt, cert) = make_packet(1, 1000, HASH_A, HASH_A, ClosureStatus::Closed, REPLAY);
        let verdict = detect_exact(&pkt, &cert);
        assert!(verdict.is_counterfeit);
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::ClosureInconsistency));
    }

    /// Build a closure cert whose `gamma_2` is a non-zero rational so small it
    /// underflows to f64 `0.0` (denominator `10^400`). `make_packet`'s i64
    /// denominator cannot express this, so we rebuild the cert with a huge
    /// `BigInt` denominator.
    fn cert_with_subfloor_gamma2(base: ClosureCertificate) -> ClosureCertificate {
        let huge_den = BigInt::from(10u32).pow(400);
        ClosureCertificate {
            gamma_2: CertifiedScalar::ExactRational(RationalValue {
                numerator: BigInt::from(1),
                denominator: huge_den,
            }),
            ..base
        }
    }

    /// Red-team #911 P2: `detect_approx` must NOT miss obstruction/closure fraud
    /// on a non-zero rational below the f64 floor (`gamma_2 = 1 / 10^400`).
    /// The detector decides on the exact rational, so the ExactRepair claim is
    /// fraudulent and MUST be flagged.
    #[test]
    fn detect_approx_catches_subfloor_gamma2_fraud_via_exact_zero_test() {
        let (pkt, base_cert) = make_packet(0, 1, HASH_A, HASH_A, ClosureStatus::Open, REPLAY);
        let cert = cert_with_subfloor_gamma2(base_cert);

        // The EXACT rational is non-zero.
        assert!(!cert
            .gamma_2
            .try_exact_rational()
            .expect("exact rational present")
            .is_zero());

        let verdict = detect_approx(&pkt, &cert);
        assert!(
            verdict.is_counterfeit,
            "sub-f64-floor non-zero gamma_2 on an ExactRepair packet MUST be counterfeit"
        );
        assert!(
            verdict
                .reasons
                .contains(&CounterfeitReason::ClosureDefectFraud),
            "must flag ClosureDefectFraud via the exact-zero test; reasons: {:?}",
            verdict.reasons
        );
    }

    /// Positive control: a GENUINELY zero gamma_2 (`0/1`) on an ExactRepair
    /// packet passes `detect_approx` cleanly. Paired with the negative control
    /// above, this establishes the exact-zero gate discriminates (it does not flag
    /// every ExactRepair packet).
    #[test]
    fn detect_approx_passes_genuinely_zero_gamma2() {
        let (pkt, cert) = make_packet(0, 1, HASH_A, HASH_A, ClosureStatus::Open, REPLAY);
        let verdict = detect_approx(&pkt, &cert);
        assert!(
            !verdict.is_counterfeit,
            "a genuinely zero gamma_2 ExactRepair packet must NOT be counterfeit; reasons: {:?}",
            verdict.reasons
        );
    }
    fn interval(lower: (i64, i64), upper: (i64, i64)) -> CertifiedScalar {
        CertifiedScalar::Interval {
            lower: RationalValue {
                numerator: BigInt::from(lower.0),
                denominator: BigInt::from(lower.1),
            },
            upper: RationalValue {
                numerator: BigInt::from(upper.0),
                denominator: BigInt::from(upper.1),
            },
        }
    }

    /// `[-1, 2]` has a positive midpoint; the old f64-midpoint sign test read
    /// it as non-negative. It is not certified non-negative and must be flagged.
    #[test]
    fn detect_approx_refuses_straddling_interval_as_nonnegative() {
        let (pkt, base_cert) = make_packet(0, 1, HASH_A, HASH_A, ClosureStatus::Open, REPLAY);
        let cert = ClosureCertificate {
            gamma_2: interval((-1, 1), (2, 1)),
            ..base_cert
        };
        assert!(!cert.gamma_2.is_nonnegative_exact_or_interval());
        let verdict = detect_approx(&pkt, &cert);
        assert!(verdict.is_counterfeit);
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::NegativeClosureDefect));
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::ClosureDefectFraud));
    }

    #[test]
    fn detect_approx_closed_with_nonzero_interval_is_inconsistent() {
        let (pkt, base_cert) = make_packet(0, 1, HASH_A, HASH_A, ClosureStatus::Closed, REPLAY);
        let cert = ClosureCertificate {
            gamma_2: interval((0, 1), (1, 1_000_000_000)),
            ..base_cert
        };
        let verdict = detect_approx(&pkt, &cert);
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::ClosureInconsistency));
        assert!(!verdict
            .reasons
            .contains(&CounterfeitReason::NegativeClosureDefect));
    }

    #[test]
    fn detect_approx_exact_zero_interval_passes() {
        let (pkt, base_cert) = make_packet(0, 1, HASH_A, HASH_A, ClosureStatus::Closed, REPLAY);
        let cert = ClosureCertificate {
            gamma_2: interval((0, 1), (0, 5)),
            ..base_cert
        };
        let verdict = detect_approx(&pkt, &cert);
        assert!(!verdict.is_counterfeit, "reasons: {:?}", verdict.reasons);
    }

    #[test]
    fn detect_approx_zero_denominator_is_non_finite_without_panic() {
        let (pkt, base_cert) = make_packet(0, 1, HASH_A, HASH_A, ClosureStatus::Closed, REPLAY);
        let cert = ClosureCertificate {
            gamma_2: interval((0, 1), (1, 0)),
            ..base_cert
        };
        let verdict = detect_approx(&pkt, &cert);
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::NonFiniteClosureDefect));
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::ClosureInconsistency));
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::ClosureDefectFraud));

        let (pkt, base_cert) = make_packet(0, 1, HASH_A, HASH_A, ClosureStatus::Open, REPLAY);
        let cert = ClosureCertificate {
            gamma_2: CertifiedScalar::ExactRational(RationalValue {
                numerator: BigInt::from(0),
                denominator: BigInt::from(0),
            }),
            ..base_cert
        };
        let verdict = detect_approx(&pkt, &cert);
        assert!(verdict
            .reasons
            .contains(&CounterfeitReason::NonFiniteClosureDefect));
    }
}

#[cfg(test)]
mod l4_boundary_tests_a0d4c84b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda0d4c84b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda0d4c84b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda0d4c84b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda0d4c84b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda0d4c84b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora0d4c84b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora0d4c84b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
