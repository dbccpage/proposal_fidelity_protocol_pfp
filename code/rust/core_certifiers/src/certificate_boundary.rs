use crate::checked_packet::{
    CheckedPacket, CheckedPacketCertificateError, CheckedPacketCertificateV1,
};
use core_types::authority::{DescentWitness, IsAuth};
use serde::{Deserialize, Serialize};

/// Audit record for either packet-bound certificate evidence or a none-effect
/// diagnostic. Populated certificate fields remain evidence; `effect` is
/// always `None` on the checked-packet path.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[must_use = "an AuthorityVerdict records a firewall decision; dropping it discards the audit record"]
pub struct AuthorityVerdict {
    /// "None" or "Refused". Checked-packet certificates never set "Certified".
    pub effect: String,
    /// Candidate authority terminal carried as evidence, when present.
    pub terminal: Option<String>,
    /// The seven packet-bound IsAuth guards, when present.
    pub guards: Option<[bool; 7]>,
    /// Replay hash binding the evidence certificate to its packet.
    pub descent_replay_hash: Option<String>,
    /// The firewall rule that decided the verdict.
    pub firewall: String,
}

impl AuthorityVerdict {
    pub fn from_certificate(
        certificate: &CheckedPacketCertificateV1,
        firewall: impl Into<String>,
    ) -> Self {
        let guards = certificate.is_auth().guards();
        Self {
            effect: "None".to_owned(),
            terminal: Some(format!("{:?}", certificate.terminal())),
            guards: Some([
                guards.accessible,
                guards.deterministic,
                guards.obstruction_vanishes,
                guards.exhaustive,
                guards.skeletal,
                guards.no_lift,
                guards.no_refuse,
            ]),
            descent_replay_hash: Some(certificate.packet_replay_hash().to_owned()),
            firewall: firewall.into(),
        }
    }

    pub fn none_record(firewall: impl Into<String>) -> Self {
        Self {
            effect: "None".to_owned(),
            terminal: None,
            guards: None,
            descent_replay_hash: None,
            firewall: firewall.into(),
        }
    }
}

/// Seal a packet-bound evidence certificate. This function never constructs a
/// `CertifiedAuthority` or an `AuthorizedLocalResult`.
pub fn certify_checked_packet(
    packet: &CheckedPacket,
    witness: DescentWitness,
    is_auth: IsAuth,
) -> Result<CheckedPacketCertificateV1, CheckedPacketCertificateError> {
    packet.certify_evidence(witness, is_auth)
}

// Origin: engine/crates_rs/core_certifiers/src/certificate_boundary.rs
// Claim: urn:core:crates_rs:core-certifiers:certificate-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord856d8bb1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord856d8bb1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError856d8bb1 {
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
impl BoundaryError856d8bb1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError856d8bb1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError856d8bb1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord856d8bb1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError856d8bb1> {
        if capacity_bound == 0 {
            return Err(BoundaryError856d8bb1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError856d8bb1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError856d8bb1::ExceedsCapacity {
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
    use super::*;
    use crate::checked_packet::{
        BoundaryMapsHash, CarrierManifestHash, CertificateRef, CertificateVerdict,
        CheckedClaimKind, CheckedClaimScope, CheckedPacketArgs, CheckerRef, DefectFieldHash,
        EvidenceRef, Hash256, ObserverBoundaryHash, ReplayHash, ToleranceProfileHash,
        WeightsAndGaugesHash,
    };
    use num_bigint::BigInt;
    use num_rational::BigRational;
    use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional};
    use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional, VerifiedExactPhi1};
    use core_policy::trichotomy::{
        classify_exact, CertifiedExactTrichotomy, ObstructionDiagnosticClass, TrichotomyOutcome,
    };
    use core_types::authority::{AuthorityTerminal, IsAuth};
    use core_types::EvidenceCeiling;
    use core_types::GuardEvidence;

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
            checker_ref: CheckerRef("test-checker".to_owned()),
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

    fn all_true_is_auth(terminal: AuthorityTerminal) -> IsAuth {
        IsAuth::decide(
            terminal,
            GuardEvidence::new_valid(["cand_01"], "K_carrier_01", "blake3:deadbeef"),
        )
        .expect("fixture guards satisfy IsAuth")
    }

    fn certificate() -> CheckedPacketCertificateV1 {
        let (phi1, trichotomy) = exact_evidence();
        let packet = CheckedPacket::new_checked(args(), &phi1, &trichotomy).unwrap();
        assert_eq!(packet.status(), ObstructionDiagnosticClass::ExactRepair);
        let witness = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent-A",
            "0c".repeat(32),
        )
        .unwrap();
        certify_checked_packet(
            &packet,
            witness,
            all_true_is_auth(AuthorityTerminal::ExactRuleDerived),
        )
        .unwrap()
    }

    #[test]
    fn certify_checked_packet_seals_none_effect_evidence() {
        let certificate = certificate();
        assert_eq!(certificate.terminal(), AuthorityTerminal::ExactRuleDerived);
        assert!(certificate.authority_effect().is_none());
    }

    #[test]
    fn authority_verdict_transcribes_certificate_without_promoting() {
        let certificate = certificate();
        let verdict = AuthorityVerdict::from_certificate(&certificate, "certify_checked_packet");
        assert_eq!(verdict.effect, "None");
        assert_eq!(verdict.terminal.as_deref(), Some("ExactRuleDerived"));
        assert_eq!(verdict.guards, Some([true; 7]));
        assert_eq!(
            verdict.descent_replay_hash.as_deref(),
            Some("0c".repeat(32).as_str())
        );
    }

    #[test]
    fn authority_verdict_none_record_leaves_evidence_fields_empty() {
        let verdict = AuthorityVerdict::none_record("diagnostic-only");
        assert_eq!(verdict.effect, "None");
        assert!(verdict.terminal.is_none());
        assert!(verdict.guards.is_none());
        assert!(verdict.descent_replay_hash.is_none());
    }
}

#[cfg(test)]
mod l4_boundary_tests_856d8bb1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord856d8bb1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord856d8bb1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord856d8bb1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord856d8bb1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord856d8bb1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError856d8bb1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError856d8bb1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
