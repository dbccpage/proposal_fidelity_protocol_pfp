use core_contracts::{seal_checked_packet_certificate_v1, CertificatePromotionContractError};
use core_functional::phi1::VerifiedExactPhi1;
use core_policy::trichotomy::{CertifiedExactTrichotomy, ObstructionDiagnosticClass};
use core_types::authority::{AuthorityTerminal, DescentWitness, IsAuth};
use core_types::{EvidenceCeiling, FactLabel};
use serde::{Deserialize, Serialize};

fn hash_hex(hash: &Hash256) -> String {
    use std::fmt::Write;
    let mut s = String::with_capacity(64);
    for b in &hash.0 {
        let _ = write!(s, "{:02x}", b);
    }
    s
}

pub use core_contracts::CheckedPacketCertificateV1;
pub use core_kernel::evidence::BoundaryMapsHash;
pub use core_kernel::evidence::CarrierManifestHash;
pub use core_kernel::evidence::CertificateRef;
pub use core_kernel::evidence::CheckerRef;
pub use core_kernel::evidence::DefectFieldHash;
pub use core_kernel::evidence::EvidenceRef;
pub use core_kernel::evidence::Hash256;
pub use core_kernel::evidence::ObserverBoundaryHash;
pub use core_kernel::evidence::ReplayHash;
pub use core_kernel::evidence::ToleranceProfileHash;
pub use core_kernel::evidence::WeightsAndGaugesHash;
pub use core_kernel::evidence::*;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum CertificateVerdict {
    Verified,
    Invalid,
    Pending,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum CheckedClaimKind {
    ObstructionSummary,
    Closure,
    Replay,
    Boundary,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckedClaimScope {
    pub claim_kind: CheckedClaimKind,
    pub authority_ceiling: EvidenceCeiling,
    pub law_refs: Vec<LawId>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProposedPacket {
    pub packet_id: Hash256,
    pub schema_hash: Hash256,
    pub raw_payload_hash: Hash256,
    pub authority_effect: FactLabel, // EvidenceOnly
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UncheckedPacket {
    pub packet_id: Hash256,
    pub schema_hash: Hash256,
    pub carrier_hash: CarrierManifestHash,
    pub payload_hash: Hash256,
    pub parse_report_hash: Hash256,
    pub authority_effect: FactLabel, // EvidenceOnly
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckedPacketArgs {
    pub packet_id: Hash256,
    pub evidence_refs: Vec<EvidenceRef>,
    pub checker_ref: CheckerRef,
    pub schema_hash: Hash256,

    pub carrier_hash: CarrierManifestHash,
    pub boundary_maps_hash: BoundaryMapsHash,
    pub weights_and_gauges_hash: WeightsAndGaugesHash,
    pub submitted_defect_hash: DefectFieldHash,

    pub phi1_certificate_ref: CertificateRef,
    pub closure_certificate_ref: CertificateRef,
    pub observer_boundary_hash: ObserverBoundaryHash,

    pub tolerance_profile_hash: ToleranceProfileHash,
    pub replay_hash: ReplayHash,

    pub certificate_status: CertificateVerdict,
    pub checked_scope: CheckedClaimScope,
}

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum CheckedPacketError {
    #[error("missing checker reference")]
    MissingChecker,
    #[error("missing replay hash")]
    MissingReplayHash,
    #[error("missing Phi1 primal-dual certificate reference")]
    MissingPhi1CertificateRef,
    #[error("missing Gamma2 closure certificate reference")]
    MissingClosureCertificateRef,
    #[error("Phi1 certificate and exact trichotomy evidence disagree")]
    TrichotomyPhi1Mismatch,
    #[error("certificate status is not verified")]
    UnverifiedCertificateStatus,
    #[error("missing evidence refs")]
    MissingEvidenceRefs,
}

/// Refusals while sealing a packet-bound evidence certificate.
///
/// The certificate carries `AuthorityEffect::None`. It records an exact packet,
/// a witness bound to that packet's replay hash, and a decided `IsAuth` token;
/// it cannot construct `CertifiedAuthority` or `AuthorizedLocalResult`.
#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum CheckedPacketCertificateError {
    #[error("certificate status is not verified")]
    UnverifiedCertificate,
    #[error("obstruction status {0:?} is not certificate-eligible (only ExactRepair)")]
    NotAuthorityBearing(ObstructionDiagnosticClass),
    #[error("descent witness is not bound to this packet (replay-hash mismatch)")]
    WitnessPacketMismatch,
    #[error(transparent)]
    Contract(#[from] CertificatePromotionContractError),
}

/// Checked cochain obstruction packet.
///
/// The fields are private and this type is serialize-only. Construction
/// requires replayed Phi1 primal-dual evidence and an exact trichotomy result,
/// so raw representative norms and floating heuristics cannot become packet
/// claims.
#[derive(Debug, Clone, Serialize)]
pub struct CheckedPacket {
    packet_id: Hash256,
    evidence_refs: Vec<EvidenceRef>,
    checker_ref: CheckerRef,
    schema_hash: Hash256,

    carrier_hash: CarrierManifestHash,
    boundary_maps_hash: BoundaryMapsHash,
    weights_and_gauges_hash: WeightsAndGaugesHash,
    submitted_defect_hash: DefectFieldHash,

    obstruction_mass: CertifiedScalar,
    phi1_certificate_ref: CertificateRef,
    closure_certificate_ref: CertificateRef,
    observer_boundary_hash: ObserverBoundaryHash,

    tolerance_profile_hash: ToleranceProfileHash,
    replay_hash: ReplayHash,

    certificate_status: CertificateVerdict,
    status: ObstructionDiagnosticClass,
    checked_scope: CheckedClaimScope,
    authority_effect: FactLabel,
}

impl CheckedPacket {
    pub fn new_checked(
        args: CheckedPacketArgs,
        verified_phi1: &VerifiedExactPhi1,
        trichotomy: &CertifiedExactTrichotomy,
    ) -> Result<Self, CheckedPacketError> {
        if args.evidence_refs.is_empty() {
            return Err(CheckedPacketError::MissingEvidenceRefs);
        }
        if args.checker_ref.0.is_empty() {
            return Err(CheckedPacketError::MissingChecker);
        }
        if args.replay_hash.0 == Hash256([0; 32]) {
            return Err(CheckedPacketError::MissingReplayHash);
        }
        if args.phi1_certificate_ref.0 == Hash256([0; 32]) {
            return Err(CheckedPacketError::MissingPhi1CertificateRef);
        }
        if args.closure_certificate_ref.0 == Hash256([0; 32]) {
            return Err(CheckedPacketError::MissingClosureCertificateRef);
        }
        if trichotomy.phi1_value() != verified_phi1.value() {
            return Err(CheckedPacketError::TrichotomyPhi1Mismatch);
        }
        if args.certificate_status != CertificateVerdict::Verified {
            return Err(CheckedPacketError::UnverifiedCertificateStatus);
        }

        Ok(Self {
            packet_id: args.packet_id,
            evidence_refs: args.evidence_refs,
            checker_ref: args.checker_ref,
            schema_hash: args.schema_hash,

            carrier_hash: args.carrier_hash,
            boundary_maps_hash: args.boundary_maps_hash,
            weights_and_gauges_hash: args.weights_and_gauges_hash,
            submitted_defect_hash: args.submitted_defect_hash,

            obstruction_mass: CertifiedScalar::ExactRational(RationalValue::from_big_rational(
                verified_phi1.value(),
            )),
            phi1_certificate_ref: args.phi1_certificate_ref,
            closure_certificate_ref: args.closure_certificate_ref,
            observer_boundary_hash: args.observer_boundary_hash,

            tolerance_profile_hash: args.tolerance_profile_hash,
            replay_hash: args.replay_hash,

            certificate_status: args.certificate_status,
            status: trichotomy.diagnostic_class(),
            checked_scope: args.checked_scope,
            authority_effect: FactLabel::FactOnly,
        })
    }

    pub fn carrier_hash(&self) -> &CarrierManifestHash {
        &self.carrier_hash
    }

    pub fn obstruction_mass(&self) -> &CertifiedScalar {
        &self.obstruction_mass
    }

    pub fn phi1_certificate_ref(&self) -> &CertificateRef {
        &self.phi1_certificate_ref
    }

    pub fn replay_hash(&self) -> &ReplayHash {
        &self.replay_hash
    }

    pub fn status(&self) -> ObstructionDiagnosticClass {
        self.status
    }

    /// Seal exact packet, replay, witness, and guard evidence into a canonical
    /// certificate with `AuthorityEffect::None`.
    pub fn certify_evidence(
        &self,
        witness: DescentWitness,
        is_auth: IsAuth,
    ) -> Result<CheckedPacketCertificateV1, CheckedPacketCertificateError> {
        if self.certificate_status != CertificateVerdict::Verified {
            return Err(CheckedPacketCertificateError::UnverifiedCertificate);
        }
        let terminal = match self.status {
            ObstructionDiagnosticClass::ExactRepair => AuthorityTerminal::ExactRuleDerived,
            other => return Err(CheckedPacketCertificateError::NotAuthorityBearing(other)),
        };
        let replay_hash = hash_hex(&self.replay_hash.0);
        if witness.replay_hash() != replay_hash {
            return Err(CheckedPacketCertificateError::WitnessPacketMismatch);
        }
        Ok(seal_checked_packet_certificate_v1(
            hash_hex(&self.packet_id),
            replay_hash,
            terminal,
            witness,
            is_auth,
            self.checked_scope.authority_ceiling,
        )?)
    }
}

pub trait PacketCertifier {
    fn certify(
        &self,
        packet: &UncheckedPacket,
        verified_phi1: &VerifiedExactPhi1,
        trichotomy: &CertifiedExactTrichotomy,
    ) -> Result<CheckedPacket, CheckedPacketError>;
}

// Origin: engine/crates_rs/core_certifiers/src/checked_packet.rs
// Claim: urn:core:crates_rs:core-certifiers:checked-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use num_bigint::BigInt;
    use num_rational::BigRational;
    use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional};
    use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
    use core_policy::trichotomy::{classify_exact, TrichotomyOutcome};
    use core_types::GuardEvidence;

    use super::*;

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn exact_evidence() -> (VerifiedExactPhi1, CertifiedExactTrichotomy) {
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
            panic!("exact evidence must classify");
        };
        (phi1, trichotomy)
    }

    fn args() -> CheckedPacketArgs {
        CheckedPacketArgs {
            packet_id: Hash256([1; 32]),
            evidence_refs: vec![EvidenceRef(Hash256([2; 32]))],
            checker_ref: CheckerRef("test-checker".to_string()),
            schema_hash: Hash256([3; 32]),
            carrier_hash: CarrierManifestHash(Hash256([4; 32])),
            boundary_maps_hash: BoundaryMapsHash(Hash256([5; 32])),
            weights_and_gauges_hash: WeightsAndGaugesHash(Hash256([6; 32])),
            submitted_defect_hash: DefectFieldHash(Hash256([7; 32])),
            phi1_certificate_ref: CertificateRef(Hash256([8; 32])),
            closure_certificate_ref: CertificateRef(Hash256([9; 32])),
            observer_boundary_hash: ObserverBoundaryHash(Hash256([10; 32])),
            tolerance_profile_hash: ToleranceProfileHash(Hash256([11; 32])),
            replay_hash: ReplayHash(Hash256([12; 32])),
            certificate_status: CertificateVerdict::Verified,
            checked_scope: CheckedClaimScope {
                claim_kind: CheckedClaimKind::ObstructionSummary,
                authority_ceiling: EvidenceCeiling::BoundaryChecked,
                law_refs: vec![],
            },
        }
    }

    #[test]
    fn checked_packet_binds_verified_phi1_value_and_status() {
        let (phi1, trichotomy) = exact_evidence();
        let packet = CheckedPacket::new_checked(args(), &phi1, &trichotomy).unwrap();

        assert_eq!(
            packet.obstruction_mass(),
            &CertifiedScalar::ExactRational(RationalValue {
                numerator: BigInt::from(0),
                denominator: BigInt::from(1),
            })
        );
        assert_eq!(packet.status(), ObstructionDiagnosticClass::ExactRepair);
    }

    #[test]
    fn checked_packet_refuses_missing_phi1_certificate_ref() {
        let (phi1, trichotomy) = exact_evidence();
        let mut args = args();
        args.phi1_certificate_ref = CertificateRef(Hash256([0; 32]));

        assert!(matches!(
            CheckedPacket::new_checked(args, &phi1, &trichotomy),
            Err(CheckedPacketError::MissingPhi1CertificateRef)
        ));
    }

    #[test]
    fn checked_packet_refuses_missing_closure_certificate_ref() {
        let (phi1, trichotomy) = exact_evidence();
        let mut args = args();
        args.closure_certificate_ref = CertificateRef(Hash256([0; 32]));

        assert!(matches!(
            CheckedPacket::new_checked(args, &phi1, &trichotomy),
            Err(CheckedPacketError::MissingClosureCertificateRef)
        ));
    }

    // ── evidence-certificate firewall (S14-001) ─────────────────────────────
    //
    // The packet in args() has replay_hash = ReplayHash(Hash256([12; 32])),
    // whose hex is "0c" repeated 32 times. A witness is bound to THIS packet iff
    // its replay_hash string equals that hex.

    fn bound_replay_hex() -> String {
        "0c".repeat(32)
    }

    fn exact_packet() -> CheckedPacket {
        let (phi1, trichotomy) = exact_evidence();
        let packet = CheckedPacket::new_checked(args(), &phi1, &trichotomy).unwrap();
        // Precondition: this fixture is an ExactRepair evidence terminal.
        assert_eq!(packet.status(), ObstructionDiagnosticClass::ExactRepair);
        packet
    }

    fn all_true_is_auth(terminal: AuthorityTerminal) -> IsAuth {
        IsAuth::decide(
            terminal,
            GuardEvidence::new_valid(["cand_01"], "K_carrier_01", "blake3:deadbeef"),
        )
        .expect("fixture guards satisfy IsAuth")
    }

    /// Positive control: an ExactRepair packet plus packet-bound witness and
    /// matching guards seals evidence while retaining `AuthorityEffect::None`.
    #[test]
    fn certify_evidence_seals_bound_exact_witness_without_authority() {
        let packet = exact_packet();
        let witness = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent-A",
            bound_replay_hex(),
        )
        .unwrap();

        let certificate = packet
            .certify_evidence(
                witness,
                all_true_is_auth(AuthorityTerminal::ExactRuleDerived),
            )
            .expect("bound exact witness seals evidence");
        assert_eq!(certificate.terminal(), AuthorityTerminal::ExactRuleDerived);
        assert_eq!(certificate.witness().replay_hash(), bound_replay_hex());
        assert!(certificate.authority_effect().is_none());
    }

    /// THE binding test (advisor-caught leak vector): a witness that is valid in
    /// itself but bound to a DIFFERENT descent (different replay hash) must not
    /// certify this packet. This prevents cross-packet witness reuse.
    #[test]
    fn certify_evidence_refuses_cross_packet_witness() {
        let packet = exact_packet();
        let foreign = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent-B",
            "ff".repeat(32), // valid witness, wrong packet
        )
        .unwrap();

        assert_eq!(
            packet.certify_evidence(
                foreign,
                all_true_is_auth(AuthorityTerminal::ExactRuleDerived)
            ),
            Err(CheckedPacketCertificateError::WitnessPacketMismatch)
        );
    }

    /// A witness bound to this packet's replay but carrying the wrong authority
    /// terminal is refused by the certificate contract.
    #[test]
    fn certify_evidence_refuses_terminal_mismatch() {
        let packet = exact_packet();
        let wrong_terminal = DescentWitness::from_verified_replay(
            AuthorityTerminal::UniqueOutputDerived, // packet maps to ExactRuleDerived
            "descent-A",
            bound_replay_hex(),
        )
        .unwrap();

        assert_eq!(
            packet.certify_evidence(
                wrong_terminal,
                all_true_is_auth(AuthorityTerminal::ExactRuleDerived)
            ),
            Err(CheckedPacketCertificateError::Contract(
                CertificatePromotionContractError::TerminalMismatch
            ))
        );
    }

    // ── non-ExactRepair refusal (STORY-120-0-002) ───────────────────────────
    //
    // A Phi1>0 fixture: a single coordinate with a zero coboundary column, so
    // omega=[1] is irreparable (residual = omega) -> Phi1 = 1 > 0. The `d1`
    // argument then selects the closure defect: d1=[[0]] -> Gamma2 = 0 (Survivor),
    // d1=[[1]] -> Gamma2 > 0 (Open). d1·d0 = 0 holds since the d0 column is zero.
    fn nonexact_evidence(d1: &[Vec<BigRational>]) -> (VerifiedExactPhi1, CertifiedExactTrichotomy) {
        let phi1 = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
            omega: vec![r(1)],
            d0: vec![vec![r(0)]],
            weights: vec![r(1)],
            alpha: vec![r(0)],
            primal_residual: vec![r(1)],
            dual_witness: vec![r(1)],
            reported_value: r(1),
        })
        .unwrap();
        let complex =
            ExactCochainComplexQ::try_new(1, 1, d1.len(), phi1.d0().to_vec(), d1.to_vec()).unwrap();
        let residual =
            DegreeOneResidualQ::try_new(&complex, phi1.primal_residual().to_vec()).unwrap();
        let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual).unwrap();
        let TrichotomyOutcome::Classified(trichotomy) = classify_exact(&phi1, &gamma2) else {
            panic!("non-exact evidence must classify");
        };
        (phi1, trichotomy)
    }

    /// A `ClosedResidual` packet cannot certify, even with a correctly bound
    /// witness. The bound witness isolates status as the refusal cause.
    #[test]
    fn certify_evidence_refuses_survivor_not_certificate_eligible() {
        let (phi1, trichotomy) = nonexact_evidence(&[vec![r(0)]]);
        let packet = CheckedPacket::new_checked(args(), &phi1, &trichotomy).unwrap();
        assert_eq!(packet.status(), ObstructionDiagnosticClass::ClosedResidual);

        let witness = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent-A",
            bound_replay_hex(),
        )
        .unwrap();
        assert_eq!(
            packet.certify_evidence(
                witness,
                all_true_is_auth(AuthorityTerminal::ExactRuleDerived)
            ),
            Err(CheckedPacketCertificateError::NotAuthorityBearing(
                ObstructionDiagnosticClass::ClosedResidual
            ))
        );
    }

    /// An `ActiveClosureFailure` packet cannot certify either.
    #[test]
    fn certify_evidence_refuses_open_not_certificate_eligible() {
        let (phi1, trichotomy) = nonexact_evidence(&[vec![r(1)]]);
        let packet = CheckedPacket::new_checked(args(), &phi1, &trichotomy).unwrap();
        assert_eq!(
            packet.status(),
            ObstructionDiagnosticClass::ActiveClosureFailure
        );

        let witness = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent-A",
            bound_replay_hex(),
        )
        .unwrap();
        assert_eq!(
            packet.certify_evidence(
                witness,
                all_true_is_auth(AuthorityTerminal::ExactRuleDerived)
            ),
            Err(CheckedPacketCertificateError::NotAuthorityBearing(
                ObstructionDiagnosticClass::ActiveClosureFailure
            ))
        );
    }
}
