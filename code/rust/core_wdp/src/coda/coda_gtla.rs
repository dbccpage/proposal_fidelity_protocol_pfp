//! Canonical finite Rust composition of the CODA diagnostic path and the
//! CODA_GTLA-governed authority boundary.
//!
//! This module owns no domain algorithm. It composes the existing owners in the
//! one-engine order:
//!
//! ```text
//! PrimitiveDifference (finite validation)
//!   -> exact C0 -> C1 -> C2 evidence
//!   -> verified Phi_1 and exact Gamma_2
//!   -> Exact / Survivor / Open
//!   -> CheckedPacket
//!   -> evidence-only CheckedPacketCertificate
//! ```
//!
//! Scope is deliberately narrow. `PrimitiveDifferenceReceipt` is the finite
//! Rust shadow of the primitive-difference ontology, not a mechanization of the
//! prose CODA foundations. The pipeline emits evidence only. Host promotion,
//! receipt-DAG verification, authority-witness attestation, and human decision
//! remain outside this module.

use num_rational::BigRational;
use core_certifiers::certify_checked_packet;
use core_certifiers::checked_packet::{
    BoundaryMapsHash, CarrierManifestHash, CertificateRef, CertificateVerdict, CheckedClaimKind,
    CheckedClaimScope, CheckedPacket, CheckedPacketArgs, CheckedPacketCertificateError,
    CheckedPacketCertificateV1, CheckedPacketError, CheckerRef, DefectFieldHash, EvidenceRef,
    Hash256, ObserverBoundaryHash, ReplayHash, ToleranceProfileHash, WeightsAndGaugesHash,
};
use core_functional::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Error, ExactGamma2Result, Gamma2Functional,
};
use core_functional::phi1::{
    ExactPhi1Certificate, ExactPhi1CertificateError, Phi1Functional, VerifiedExactPhi1,
};
use core_homotopy_type_theory::primitive_difference::{
    PrimitiveDifference, PrimitiveDifferenceError, ValidatedFiniteCarrier,
};
use core_policy::trichotomy::{
    classify_exact, CertifiedExactTrichotomy, ObstructionDiagnosticClass, TrichotomyOutcome,
    TrichotomyRefusal,
};
use core_types::authority::{DescentWitness, IsAuth};
use core_types::EvidenceCeiling;

/// Evidence that the finite primitive-difference laws and delta congruence were
/// replayed on one declared carrier manifest.
///
/// The generic primitive checker cannot serialize an arbitrary carrier, so the
/// caller supplies the canonical manifest hash. The runtime binds that same hash
/// to the checked packet; producing the manifest bytes and digest remains an
/// explicit upstream trust boundary.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PrimitiveDifferenceReceipt {
    declared_carrier_hash: CarrierManifestHash,
    domain_len: usize,
    quotient_class_count: usize,
}

impl PrimitiveDifferenceReceipt {
    pub fn declared_carrier_hash(&self) -> &CarrierManifestHash {
        &self.declared_carrier_hash
    }

    pub fn domain_len(&self) -> usize {
        self.domain_len
    }

    pub fn quotient_class_count(&self) -> usize {
        self.quotient_class_count
    }
}

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum PrimitiveDifferenceReceiptError {
    #[error("the finite primitive-difference domain must be nonempty")]
    EmptyDomain,
    #[error("the declared carrier manifest hash must be nonzero")]
    MissingCarrierManifestHash,
    #[error("finite primitive-difference validation failed: {0:?}")]
    Validation(PrimitiveDifferenceError),
}

/// Replay the finite primitive-difference quotient laws before exact
/// obstruction evidence enters the shared pipeline.
pub fn validate_primitive_difference<P: PrimitiveDifference>(
    primitive: &P,
    domain: Vec<P::Carrier>,
    declared_carrier_hash: CarrierManifestHash,
) -> Result<PrimitiveDifferenceReceipt, PrimitiveDifferenceReceiptError> {
    if domain.is_empty() {
        return Err(PrimitiveDifferenceReceiptError::EmptyDomain);
    }
    if declared_carrier_hash.is_zero() {
        return Err(PrimitiveDifferenceReceiptError::MissingCarrierManifestHash);
    }

    let carrier = ValidatedFiniteCarrier::try_new(primitive, domain)
        .map_err(PrimitiveDifferenceReceiptError::Validation)?;
    carrier
        .validate_delta_congruence()
        .map_err(PrimitiveDifferenceReceiptError::Validation)?;

    Ok(PrimitiveDifferenceReceipt {
        declared_carrier_hash,
        domain_len: carrier.domain_len(),
        quotient_class_count: carrier.num_classes(),
    })
}
#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum DomainEvidenceBindingError {
    #[error("domain namespace must be nonempty")]
    EmptyNamespace,
    #[error("carrier manifest must be nonempty")]
    EmptyCarrierManifest,
    #[error("evidence manifest must be nonempty")]
    EmptyEvidenceManifest,
}

/// Deterministic binding of one domain carrier/evidence manifest to the
/// canonical checked-packet schema.
///
/// Domain adapters supply bytes, not preselected hashes. This prevents each
/// application from inventing its own packet binding convention while keeping
/// all domain-specific candidate construction outside the shared evaluator.
#[derive(Debug, Clone)]
pub struct DomainEvidenceBinding {
    carrier_hash: CarrierManifestHash,
    packet_args: CheckedPacketArgs,
}

impl DomainEvidenceBinding {
    pub fn carrier_hash(&self) -> &CarrierManifestHash {
        &self.carrier_hash
    }

    pub fn into_packet_args(self) -> CheckedPacketArgs {
        self.packet_args
    }
}

fn domain_hash(
    namespace: &str,
    label: &str,
    carrier_hash: Option<&CarrierManifestHash>,
    payload: &[u8],
) -> Hash256 {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"core-pipeline-domain-binding-v1\0");
    hasher.update(&(namespace.len() as u64).to_le_bytes());
    hasher.update(namespace.as_bytes());
    hasher.update(&(label.len() as u64).to_le_bytes());
    hasher.update(label.as_bytes());
    if let Some(carrier_hash) = carrier_hash {
        hasher.update(&carrier_hash.0 .0);
    }
    hasher.update(&(payload.len() as u64).to_le_bytes());
    hasher.update(payload);
    Hash256(*hasher.finalize().as_bytes())
}

/// Bind a domain's canonical carrier and evidence bytes to all packet hashes.
///
/// The returned packet remains evidence-only. This function neither evaluates
/// an obstruction nor constructs authority.
pub fn bind_domain_evidence(
    namespace: &str,
    carrier_manifest: &[u8],
    evidence_manifest: &[u8],
) -> Result<DomainEvidenceBinding, DomainEvidenceBindingError> {
    if namespace.trim().is_empty() {
        return Err(DomainEvidenceBindingError::EmptyNamespace);
    }
    if carrier_manifest.is_empty() {
        return Err(DomainEvidenceBindingError::EmptyCarrierManifest);
    }
    if evidence_manifest.is_empty() {
        return Err(DomainEvidenceBindingError::EmptyEvidenceManifest);
    }

    let carrier_hash = CarrierManifestHash(domain_hash(
        namespace,
        "carrier-manifest",
        None,
        carrier_manifest,
    ));
    let bound =
        |label: &str, payload: &[u8]| domain_hash(namespace, label, Some(&carrier_hash), payload);
    let packet_args = CheckedPacketArgs {
        packet_id: bound("packet", evidence_manifest),
        evidence_refs: vec![EvidenceRef(bound("evidence", evidence_manifest))],
        checker_ref: CheckerRef(format!("{namespace}::gtoc_gtla")),
        schema_hash: bound("schema", b"GtocExactInput/v1"),
        carrier_hash: carrier_hash.clone(),
        boundary_maps_hash: BoundaryMapsHash(bound("boundary-maps", evidence_manifest)),
        weights_and_gauges_hash: WeightsAndGaugesHash(bound("weights", evidence_manifest)),
        submitted_defect_hash: DefectFieldHash(bound("defect", evidence_manifest)),
        phi1_certificate_ref: CertificateRef(bound("phi1", evidence_manifest)),
        closure_certificate_ref: CertificateRef(bound("gamma2", evidence_manifest)),
        observer_boundary_hash: ObserverBoundaryHash(bound("observer", evidence_manifest)),
        tolerance_profile_hash: ToleranceProfileHash(bound("exact", b"exact-rational")),
        replay_hash: ReplayHash(bound("replay", evidence_manifest)),
        certificate_status: CertificateVerdict::Verified,
        checked_scope: CheckedClaimScope {
            claim_kind: CheckedClaimKind::ObstructionSummary,
            authority_ceiling: EvidenceCeiling::BoundaryChecked,
            law_refs: vec![],
        },
    };

    Ok(DomainEvidenceBinding {
        carrier_hash,
        packet_args,
    })
}

/// Inputs for the exact finite obstruction path.
///
/// Domain adapters are responsible for constructing these values from their
/// own candidate representation. They must not substitute floating diagnostics
/// for either exact certificate.
#[derive(Debug, Clone)]
pub struct CodaExactInput {
    primitive_receipt: PrimitiveDifferenceReceipt,
    phi1_certificate: ExactPhi1Certificate,
    complex: ExactCochainComplexQ,
    residual: Vec<BigRational>,
    packet_args: CheckedPacketArgs,
}

impl CodaExactInput {
    pub fn new(
        primitive_receipt: PrimitiveDifferenceReceipt,
        phi1_certificate: ExactPhi1Certificate,
        complex: ExactCochainComplexQ,
        residual: Vec<BigRational>,
        packet_args: CheckedPacketArgs,
    ) -> Self {
        Self {
            primitive_receipt,
            phi1_certificate,
            complex,
            residual,
            packet_args,
        }
    }
}

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum CodaGtlaEvaluationError {
    #[error("primitive-difference and checked-packet carrier manifests differ")]
    CarrierBindingMismatch,
    #[error("Phi1 and Gamma2 use different d0 boundary maps")]
    D0BindingMismatch,
    #[error("Phi1 and Gamma2 use different degree-one residuals")]
    ResidualBindingMismatch,
    #[error(transparent)]
    Phi1(#[from] ExactPhi1CertificateError),
    #[error(transparent)]
    Gamma2(#[from] ExactGamma2Error),
    #[error("exact obstruction trichotomy refused: {0:?}")]
    Trichotomy(TrichotomyRefusal),
    #[error(transparent)]
    CheckedPacket(#[from] CheckedPacketError),
}

/// Exact diagnostic result plus a checked packet at the authority boundary.
///
/// Construction establishes classification and packet well-formedness. It still
/// carries no authority. [`CodaGtlaEvaluation::certify_certificate`] seals
/// packet-bound evidence without crossing the host promotion boundary.
#[derive(Debug)]
pub struct CodaGtlaEvaluation {
    primitive_receipt: PrimitiveDifferenceReceipt,
    phi1: VerifiedExactPhi1,
    gamma2: ExactGamma2Result,
    trichotomy: CertifiedExactTrichotomy,
    packet: CheckedPacket,
}

impl CodaGtlaEvaluation {
    pub fn primitive_receipt(&self) -> &PrimitiveDifferenceReceipt {
        &self.primitive_receipt
    }

    pub fn phi1(&self) -> &VerifiedExactPhi1 {
        &self.phi1
    }

    pub fn gamma2(&self) -> &ExactGamma2Result {
        &self.gamma2
    }

    pub fn trichotomy(&self) -> &CertifiedExactTrichotomy {
        &self.trichotomy
    }

    pub fn status(&self) -> ObstructionDiagnosticClass {
        self.trichotomy.diagnostic_class()
    }

    pub fn checked_packet(&self) -> &CheckedPacket {
        &self.packet
    }

    /// Seal packet-bound evidence. Exact classification by itself is
    /// insufficient, and the returned certificate has `AuthorityEffect::None`.
    pub fn certify_certificate(
        &self,
        witness: DescentWitness,
        is_auth: IsAuth,
    ) -> Result<CheckedPacketCertificateV1, CheckedPacketCertificateError> {
        certify_checked_packet(&self.packet, witness, is_auth)
    }
}

/// Run the exact one-engine diagnostic composition and stop at a checked packet.
pub fn evaluate_exact(
    input: CodaExactInput,
) -> Result<CodaGtlaEvaluation, CodaGtlaEvaluationError> {
    if input.primitive_receipt.declared_carrier_hash != input.packet_args.carrier_hash {
        return Err(CodaGtlaEvaluationError::CarrierBindingMismatch);
    }
    if input.phi1_certificate.d0 != input.complex.d0() {
        return Err(CodaGtlaEvaluationError::D0BindingMismatch);
    }
    if input.phi1_certificate.primal_residual != input.residual {
        return Err(CodaGtlaEvaluationError::ResidualBindingMismatch);
    }

    let phi1 = Phi1Functional::verify_exact_certificate(input.phi1_certificate)?;
    let residual = DegreeOneResidualQ::try_new(&input.complex, input.residual)?;
    let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual)?;
    let trichotomy = match classify_exact(&phi1, &gamma2) {
        TrichotomyOutcome::Classified(value) => value,
        TrichotomyOutcome::TriRefused(reason) => {
            return Err(CodaGtlaEvaluationError::Trichotomy(reason));
        }
    };
    let packet = CheckedPacket::new_checked(input.packet_args, &phi1, &trichotomy)?;

    Ok(CodaGtlaEvaluation {
        primitive_receipt: input.primitive_receipt,
        phi1,
        gamma2,
        trichotomy,
        packet,
    })
}

// Origin: engine/crates_rs/core_wdp/src/coda/coda_gtla.rs
// Claim: urn:core:crates_rs:core-wdp:coda-gtla:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use num_bigint::BigInt;
    use core_certifiers::checked_packet::{
        BoundaryMapsHash, CertificateRef, CertificateVerdict, CheckedClaimKind, CheckedClaimScope,
        CheckerRef, DefectFieldHash, EvidenceRef, Hash256, ObserverBoundaryHash, ReplayHash,
        ToleranceProfileHash, WeightsAndGaugesHash,
    };
    use core_types::authority::AuthorityTerminal;
    use core_types::{EvidenceCeiling, GuardEvidence};

    use super::*;

    struct ParityDifference;

    impl PrimitiveDifference for ParityDifference {
        type Carrier = i64;
        type Diff = i64;

        fn delta(&self, x: &i64, y: &i64) -> i64 {
            (x - y).rem_euclid(2)
        }

        fn zero(&self, d: &i64) -> bool {
            *d == 0
        }
    }

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn carrier_hash(byte: u8) -> CarrierManifestHash {
        CarrierManifestHash(Hash256([byte; 32]))
    }

    fn receipt() -> PrimitiveDifferenceReceipt {
        validate_primitive_difference(&ParityDifference, vec![0, 1, 2, 3], carrier_hash(4)).unwrap()
    }

    fn packet_args() -> CheckedPacketArgs {
        CheckedPacketArgs {
            packet_id: Hash256([1; 32]),
            evidence_refs: vec![EvidenceRef(Hash256([2; 32]))],
            checker_ref: CheckerRef("gtoc-gtla-test".to_string()),
            schema_hash: Hash256([3; 32]),
            carrier_hash: carrier_hash(4),
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

    fn exact_repair_input() -> CodaExactInput {
        let phi1 = ExactPhi1Certificate {
            omega: vec![r(1)],
            d0: vec![vec![r(1)]],
            weights: vec![r(1)],
            alpha: vec![r(1)],
            primal_residual: vec![r(0)],
            dual_witness: vec![r(0)],
            reported_value: r(0),
        };
        let complex =
            ExactCochainComplexQ::try_new(1, 1, 1, phi1.d0.clone(), vec![vec![r(0)]]).unwrap();
        CodaExactInput::new(receipt(), phi1, complex, vec![r(0)], packet_args())
    }

    fn survivor_input() -> CodaExactInput {
        let phi1 = ExactPhi1Certificate {
            omega: vec![r(1)],
            d0: vec![vec![r(0)]],
            weights: vec![r(1)],
            alpha: vec![r(0)],
            primal_residual: vec![r(1)],
            dual_witness: vec![r(1)],
            reported_value: r(1),
        };
        let complex =
            ExactCochainComplexQ::try_new(1, 1, 1, phi1.d0.clone(), vec![vec![r(0)]]).unwrap();
        CodaExactInput::new(receipt(), phi1, complex, vec![r(1)], packet_args())
    }

    fn all_true_is_auth() -> IsAuth {
        let evidence = GuardEvidence::new_valid(["cand-1"], "carrier-1", "hash-1");
        IsAuth::decide(AuthorityTerminal::ExactRuleDerived, evidence).unwrap()
    }

    #[test]
    fn primitive_receipt_replays_zero_laws_and_delta_congruence() {
        let receipt = receipt();
        assert_eq!(receipt.domain_len(), 4);
        assert_eq!(receipt.quotient_class_count(), 2);
        assert_eq!(receipt.declared_carrier_hash(), &carrier_hash(4));
    }

    #[test]
    fn exact_path_classifies_before_authority_is_considered() {
        let evaluation = evaluate_exact(exact_repair_input()).unwrap();
        assert_eq!(evaluation.status(), ObstructionDiagnosticClass::ExactRepair);
        assert_eq!(evaluation.phi1().value(), &r(0));
        assert_eq!(evaluation.gamma2().value(), &r(0));
    }

    #[test]
    fn carrier_manifest_mismatch_refuses_before_exact_replay() {
        let mut input = exact_repair_input();
        input.packet_args.carrier_hash = carrier_hash(99);

        assert_eq!(
            evaluate_exact(input).unwrap_err(),
            CodaGtlaEvaluationError::CarrierBindingMismatch
        );
    }

    #[test]
    fn exact_repair_yields_only_packet_bound_certificate_evidence() {
        let evaluation = evaluate_exact(exact_repair_input()).unwrap();
        let witness = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "gtoc-gtla-test-descent",
            "0c".repeat(32),
        )
        .unwrap();

        let certificate = evaluation
            .certify_certificate(witness, all_true_is_auth())
            .unwrap();
        assert_eq!(certificate.terminal(), AuthorityTerminal::ExactRuleDerived);
        assert!(certificate.authority_effect().is_none());
    }

    #[test]
    fn stabilized_survivor_cannot_cross_the_authority_gate() {
        let evaluation = evaluate_exact(survivor_input()).unwrap();
        assert_eq!(
            evaluation.status(),
            ObstructionDiagnosticClass::ClosedResidual
        );
        let witness = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "gtoc-gtla-test-descent",
            "0c".repeat(32),
        )
        .unwrap();

        assert_eq!(
            evaluation.certify_certificate(witness, all_true_is_auth()),
            Err(CheckedPacketCertificateError::NotAuthorityBearing(
                ObstructionDiagnosticClass::ClosedResidual
            ))
        );
    }
    #[test]
    fn domain_evidence_binding_is_deterministic_and_carrier_bound() {
        let first = bind_domain_evidence("domain-a", b"carrier", b"evidence").unwrap();
        let replay = first.clone().into_packet_args().replay_hash;
        let second = bind_domain_evidence("domain-a", b"carrier", b"evidence").unwrap();
        let changed = bind_domain_evidence("domain-a", b"other-carrier", b"evidence").unwrap();

        assert_eq!(first.carrier_hash(), second.carrier_hash());
        assert_eq!(replay, second.into_packet_args().replay_hash);
        assert_ne!(first.carrier_hash(), changed.carrier_hash());
        assert!(!first.carrier_hash().is_zero());
    }

    #[test]
    fn domain_evidence_binding_refuses_unbound_inputs() {
        assert_eq!(
            bind_domain_evidence("", b"carrier", b"evidence").unwrap_err(),
            DomainEvidenceBindingError::EmptyNamespace
        );
        assert_eq!(
            bind_domain_evidence("domain", b"", b"evidence").unwrap_err(),
            DomainEvidenceBindingError::EmptyCarrierManifest
        );
        assert_eq!(
            bind_domain_evidence("domain", b"carrier", b"").unwrap_err(),
            DomainEvidenceBindingError::EmptyEvidenceManifest
        );
    }
    #[test]
    fn split_d0_rails_are_refused_before_replay() {
        let mut input = exact_repair_input();
        // ExactCochainComplexQ is sealed, so the divergent d0 must be built
        // through try_new rather than assigned into the field. The complex
        // below is internally valid (d1 = 0, so d1 * d0 = 0 holds); what the
        // test exercises is that it DISAGREES with the phi1 certificate's d0,
        // which evaluate_exact must catch as D0BindingMismatch.
        input.complex = ExactCochainComplexQ::try_new(1, 1, 1, vec![vec![r(0)]], vec![vec![r(0)]])
            .expect("a zero complex satisfies d1 * d0 = 0");

        assert_eq!(
            evaluate_exact(input).unwrap_err(),
            CodaGtlaEvaluationError::D0BindingMismatch
        );
    }

    #[test]
    fn split_residual_rails_are_refused_before_replay() {
        let mut input = exact_repair_input();
        input.residual = vec![r(1)];

        assert_eq!(
            evaluate_exact(input).unwrap_err(),
            CodaGtlaEvaluationError::ResidualBindingMismatch
        );
    }
}
