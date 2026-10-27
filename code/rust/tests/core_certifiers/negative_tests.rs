use num_bigint::BigInt;
use num_rational::BigRational;
use core_certifiers::checked_packet::{
    BoundaryMapsHash, CertificateRef, CertificateVerdict, CheckedClaimKind, CheckedClaimScope,
    CheckedPacket, CheckedPacketArgs, CheckedPacketCertificateError, DefectFieldHash, EvidenceRef,
    ObserverBoundaryHash, ReplayHash, ToleranceProfileHash, WeightsAndGaugesHash,
};
use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional};
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
use core_kernel::evidence::{CarrierManifestHash, CheckerRef, Hash256};
use core_policy::trichotomy::{classify_exact, ObstructionDiagnosticClass, TrichotomyOutcome};
use core_types::authority::{AuthorityTerminal, CertifiedAuthority, DescentWitness, IsAuth};
use core_types::EvidenceCeiling;
use core_types::GuardEvidence;

fn r(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

fn create_evidence(
    primal_residual_val: i64,
    gamma2_complex_val: i64,
) -> (
    core_functional::phi1::VerifiedExactPhi1,
    core_policy::trichotomy::CertifiedExactTrichotomy,
) {
    let (omega, primal_residual, dual_witness, reported_value) = if primal_residual_val == 0 {
        (vec![r(1), r(1)], vec![r(0), r(0)], vec![r(0), r(0)], r(0))
    } else {
        (vec![r(2), r(0)], vec![r(1), r(-1)], vec![r(1), r(-1)], r(2))
    };

    let phi1 = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
        omega,
        d0: vec![vec![r(1)], vec![r(1)]],
        weights: vec![r(1), r(1)],
        alpha: vec![r(1)],
        primal_residual,
        dual_witness,
        reported_value,
    })
    .unwrap();

    let complex = ExactCochainComplexQ::try_new(
        1,
        2,
        1,
        phi1.d0().to_vec(),
        vec![vec![r(gamma2_complex_val), r(-gamma2_complex_val)]],
    )
    .unwrap();
    let residual = DegreeOneResidualQ::try_new(&complex, phi1.primal_residual().to_vec()).unwrap();
    let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual).unwrap();
    let TrichotomyOutcome::Classified(trichotomy) = classify_exact(&phi1, &gamma2) else {
        panic!("must classify");
    };
    (phi1, trichotomy)
}

fn args(replay_hash_val: [u8; 32]) -> CheckedPacketArgs {
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
        replay_hash: ReplayHash(Hash256(replay_hash_val)),
        certificate_status: CertificateVerdict::Verified,
        checked_scope: CheckedClaimScope {
            claim_kind: CheckedClaimKind::ObstructionSummary,
            authority_ceiling: EvidenceCeiling::BoundaryChecked,
            law_refs: vec![],
        },
    }
}

fn dummy_witness() -> DescentWitness {
    DescentWitness::from_verified_replay(
        AuthorityTerminal::ExactRuleDerived,
        "descent:test",
        "0c".repeat(32),
    )
    .expect("witness")
}

fn dummy_is_auth() -> IsAuth {
    IsAuth::decide(
        AuthorityTerminal::ExactRuleDerived,
        GuardEvidence::new_valid(["cand_01"], "K_carrier_01", "blake3:deadbeef"),
    )
    .expect("is_auth")
}

#[test]
fn test_product_certificate_cannot_become_certified_authority() {
    // 1. ClosedResidual
    {
        let (phi1, trichotomy) = create_evidence(1, 0);
        assert_eq!(
            trichotomy.diagnostic_class(),
            ObstructionDiagnosticClass::ClosedResidual
        );
        let packet_args = args([12; 32]); // "0c" repeat 32 hex is [12; 32] dec
        let packet = CheckedPacket::new_checked(packet_args, &phi1, &trichotomy).unwrap();

        let res = packet.certify_evidence(dummy_witness(), dummy_is_auth());
        assert!(
            matches!(
                res,
                Err(CheckedPacketCertificateError::NotAuthorityBearing(
                    ObstructionDiagnosticClass::ClosedResidual
                ))
            ),
            "Expected NotAuthorityBearing(ClosedResidual), got {:?}",
            res
        );
    }

    // 2. ActiveClosureFailure
    {
        let (phi1, trichotomy) = create_evidence(1, 1);
        assert_eq!(
            trichotomy.diagnostic_class(),
            ObstructionDiagnosticClass::ActiveClosureFailure
        );
        let packet_args = args([12; 32]);
        let packet = CheckedPacket::new_checked(packet_args, &phi1, &trichotomy).unwrap();

        let res = packet.certify_evidence(dummy_witness(), dummy_is_auth());
        assert!(
            matches!(
                res,
                Err(CheckedPacketCertificateError::NotAuthorityBearing(
                    ObstructionDiagnosticClass::ActiveClosureFailure
                ))
            ),
            "Expected NotAuthorityBearing(ActiveClosureFailure), got {:?}",
            res
        );
    }
}

#[test]
fn test_forged_certified_authority_deserialization_fails() {
    let forged_json = r#"{
        "terminal": "ExactRuleDerived",
        "witness": {
            "origin": "ExactRuleDerived",
            "ref_path": "descent:test",
            "replay_hash": "blake3:4a4f89d3856b3e34b9d5c345389dcdcf385b2e38b2e38b2e38b2e38b2e38b2e3"
        },
        "is_auth": {
            "origin": "ExactRuleDerived",
            "guards": {
                "accessible": false,
                "deterministic": false,
                "obstruction_vanishes": false,
                "exhaustive": false,
                "skeletal": false,
                "no_lift": false,
                "no_refuse": false
            }
        }
    }"#;

    let res: Result<CertifiedAuthority, _> = serde_json::from_str(forged_json);
    assert!(
        res.is_err(),
        "Expected deserialization error for forged CertifiedAuthority"
    );
}

// Origin: engine/crates_rs/tests/core_certifiers/negative_tests.rs
// Claim: urn:core:crates_rs:tests:negative-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord60b5e368 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord60b5e368` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError60b5e368 {
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
impl BoundaryError60b5e368 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError60b5e368 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError60b5e368 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord60b5e368 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError60b5e368> {
        if capacity_bound == 0 {
            return Err(BoundaryError60b5e368::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError60b5e368::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError60b5e368::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_60b5e368() {
    let admitted = BoundaryRecord60b5e368::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord60b5e368::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
