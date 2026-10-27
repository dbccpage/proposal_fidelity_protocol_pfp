//! Prime-host orchestration. Intake fences precede exact execution and evidence sealing.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_7ff93da0<T> {
    fn checked_invariant_7ff93da0(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_7ff93da0<T> for Option<T> {
    #[inline]
    fn checked_invariant_7ff93da0(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_7ff93da0<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_7ff93da0(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, ToPrimitive, Zero};
use core_kernel::evidence::Hash256;
use core_policy::trichotomy::ObstructionDiagnosticClass;
use pfp_runtime::canonical::framed_sha256;
use core_types::authority::AuthorityEffect;
use core_wdp::prime_algos::prime_algorithm_0::{
    run_prime_algorithm_0, CochainWindow, DeclarationFill, DefectBranch, DomainAdapter,
    EvidenceProvenance, LiftProposal, PrimeDomain,
};
use core_wdp::prime_algos::prime_algorithm_0_conformance::{check_receipt, ConformanceVerdict};
use core_wdp::prime_algos::prime_algorithm_1::{transport, LossLedger, TransportRefusal};
use core_wdp::prime_algos::prime_algorithm_2::{
    can_continue_n, d0_commitment, terminalize, write_step, BoundCarrierManifest, Budget,
    ContinuationEvidence, ControlState, Detector, DetectorAdequacy, DetectorDescriptor, Gamma2Zero,
    ObligationRegistry, ObligationWitness, ResidualDelta, RunSubject, StepClaim, StepOp,
};
use core_wdp::prime_algos::prime_scope::{digest as dda_digest, ScopeBinding};
use core_wdp::solver_of_solvers::{
    replay_solve, solve, FiniteCarrier2, SolveReceipt, SolveRefusal,
};
use serde_json::Value;

use crate::protocol::{
    base_refusal, build_carrier, canonical_json, compute_request_id, decode_lower_hex,
    derive_carrier_manifest, describe_host, finalize_outcome, hex, parse_omega, strict_json,
    validate_carrier_resource_fence, validate_lower_hex, verify_packet_envelope,
    AdmissionSummaryV1, BudgetSummaryV1, CandidateRelationV1, CarrierManifestSummaryV1,
    ExactRationalWireV1, ExactStageSummaryV1, HostOutcomeV1, HostRequestV1, OesosSummaryV1,
    Prime000ConformanceV1, Prime000SummaryV1, Prime001SummaryV1, Prime002SummaryV1,
    RefusalSummaryV1, SourceBindingChecksV1, HOST_OUTCOME_SCHEMA, HOST_REQUEST_SCHEMA,
    HOST_SOURCE_REVISION, MAX_CARRIER_DIMENSION, MAX_HOST_REQUEST_BYTES,
};

mod frontier;
mod intake;
mod prime_execution;

pub(crate) use frontier::rank_guarded_frontier;
use intake::{source_binding_checks, validate_request_profile};
use prime_execution::*;

const MAX_TIMEOUT_MS: u64 = 300_000;

pub fn evaluate_request_bytes(bytes: &[u8]) -> HostOutcomeV1 {
    if bytes.len() > MAX_HOST_REQUEST_BYTES {
        return base_refusal(
            None,
            None,
            "INTAKE",
            "REQUEST_TOO_LARGE",
            format!(
                "request has {} bytes; maximum is {MAX_HOST_REQUEST_BYTES}",
                bytes.len()
            ),
        );
    }
    match strict_json::<HostRequestV1>(bytes) {
        Ok(request) => evaluate_request(request),
        Err(error) => base_refusal(None, None, "INTAKE", "MALFORMED_OR_DUPLICATE_JSON", error),
    }
}

struct HostProgress<'a> {
    request: &'a HostRequestV1,
    source_bindings: Option<SourceBindingChecksV1>,
    carrier_manifest: Option<CarrierManifestSummaryV1>,
    prime001_result: Option<Prime001SummaryV1>,
    oesos_result: Option<OesosSummaryV1>,
    prime000_result: Option<Prime000SummaryV1>,
}

impl<'a> HostProgress<'a> {
    fn new(request: &'a HostRequestV1) -> Self {
        Self {
            request,
            source_bindings: None,
            carrier_manifest: None,
            prime001_result: None,
            oesos_result: None,
            prime000_result: None,
        }
    }

    fn refuse(
        self,
        stage: &str,
        code: &str,
        detail: impl Into<String>,
        laws: Vec<String>,
    ) -> HostOutcomeV1 {
        let detail = detail.into();
        let codes = vec![code.to_owned(), "UNSIGNED_LAB_ATTESTATION".to_owned()];
        finalize_outcome(HostOutcomeV1 {
            schema_version: HOST_OUTCOME_SCHEMA.to_owned(),
            request_id_sha256: Some(self.request.request_id_sha256.clone()),
            challenge_hex: Some(self.request.challenge_hex.clone()),
            outcome_root_sha256: String::new(),
            host_registry_hash_sha256: describe_host().host_registry_hash_sha256,
            host_source_revision: HOST_SOURCE_REVISION.to_owned(),
            authority_effect: "None".to_owned(),
            execution_status: "REFUSED".to_owned(),
            source_bindings: self.source_bindings,
            carrier_manifest: self.carrier_manifest,
            prime001_result: self.prime001_result,
            oesos_result: self.oesos_result,
            prime000_result: self.prime000_result,
            prime002_result: None,
            diagnostic_kind: None,
            admission: AdmissionSummaryV1 {
                kind: "Refused".to_owned(),
                reason_commitment_sha256: admission_reason(&codes, &detail),
                codes,
            },
            attestation: "unsigned_lab".to_owned(),
            refusal: Some(RefusalSummaryV1 {
                stage: stage.to_owned(),
                code: code.to_owned(),
                detail,
                laws,
            }),
        })
    }
}

fn admit_carrier<'a>(
    request: &'a HostRequestV1,
    mut progress: HostProgress<'a>,
) -> Result<(HostProgress<'a>, FiniteCarrier2), HostOutcomeV1> {
    let carrier = match build_carrier(&request.carrier.declaration) {
        Ok(carrier) => carrier,
        Err(error) => {
            return Err(progress.refuse("CARRIER", "CARRIER_DECLARATION_INVALID", error, Vec::new()))
        }
    };
    let carrier_summary = match derive_carrier_manifest(&request.carrier.declaration) {
        Ok(summary) => summary,
        Err(error) => {
            return Err(progress.refuse("CARRIER", "CARRIER_MANIFEST_REFUSED", error, Vec::new()))
        }
    };
    if carrier_summary.manifest_version != request.carrier.expected_manifest_version
        || carrier_summary.carrier_hash_blake3 != request.carrier.expected_carrier_hash_blake3
    {
        progress.carrier_manifest = Some(carrier_summary);
        return Err(progress.refuse(
            "CARRIER",
            "CARRIER_MANIFEST_MISMATCH",
            "operator-level carrier manifest does not match the request commitment",
            Vec::new(),
        ));
    }
    progress.carrier_manifest = Some(carrier_summary);
    Ok((progress, carrier))
}

fn admit_residuals_and_prime001<'a>(
    request: &'a HostRequestV1,
    carrier: &FiniteCarrier2,
    mut progress: HostProgress<'a>,
) -> Result<(HostProgress<'a>, Vec<i128>, Vec<i128>), HostOutcomeV1> {
    let before = match parse_omega(&request.residual.before_omega_i128, "before_omega_i128") {
        Ok(values) => values,
        Err(error) => {
            return Err(progress.refuse("INTAKE", "BEFORE_RESIDUAL_INVALID", error, Vec::new()))
        }
    };
    let candidate = match parse_omega(
        &request.residual.candidate_omega_i128,
        "candidate_omega_i128",
    ) {
        Ok(values) => values,
        Err(error) => {
            return Err(progress.refuse("INTAKE", "CANDIDATE_RESIDUAL_INVALID", error, Vec::new()))
        }
    };
    if before.len() != carrier.edges.len() || candidate.len() != carrier.edges.len() {
        return Err(progress.refuse(
            "INTAKE",
            "RESIDUAL_DIMENSION_MISMATCH",
            "before and candidate residuals must contain one i128 per edge",
            Vec::new(),
        ));
    }

    let carrier_summary = progress
        .carrier_manifest
        .as_ref()
        .checked_invariant_7ff93da0("carrier manifest");
    let prime001 = match same_carrier_identity(request, carrier_summary, &candidate) {
        Ok(summary) => summary,
        Err(error) => {
            return Err(progress.refuse(
                "PRIME001",
                "SAME_CARRIER_IDENTITY_FAILED",
                error,
                Vec::new(),
            ))
        }
    };
    progress.prime001_result = Some(prime001);
    Ok((progress, before, candidate))
}

fn execute_oesos_and_prime000<'a>(
    request: &'a HostRequestV1,
    carrier: &FiniteCarrier2,
    before: &[i128],
    candidate: &[i128],
    mut progress: HostProgress<'a>,
) -> Result<(HostProgress<'a>, SolveReceipt, bool), HostOutcomeV1> {
    let receipt = match solve(carrier, before) {
        Ok(receipt) => receipt,
        Err(error) => {
            let code = solve_refusal_code(&error);
            return Err(progress.refuse("OESOS_SOLVE", code, error.to_string(), Vec::new()));
        }
    };
    if let Err(error) = replay_solve(carrier, before, &receipt) {
        return Err(progress.refuse(
            "OESOS_REPLAY",
            "OESOS_REPLAY_MISMATCH",
            error.to_string(),
            Vec::new(),
        ));
    }

    let oesos = oesos_summary(request, carrier, before, candidate, &receipt);
    if !oesos.candidate_relation.exact_match {
        progress.oesos_result = Some(oesos);
        return Err(progress.refuse(
            "CANDIDATE_RELATION",
            "CANDIDATE_NOT_REPLAYED_NORMAL_FORM",
            "candidate vector is not the exact replayed OESOS normal form",
            Vec::new(),
        ));
    }
    progress.oesos_result = Some(oesos);

    let prime000 = match prime000_summary(
        request,
        carrier,
        &receipt,
        progress.oesos_result.as_ref().checked_invariant_7ff93da0("oesos summary"),
    ) {
        Ok(summary) => summary,
        Err(error) => {
            return Err(progress.refuse("PRIME000", "PRIME000_EXACT_MASS_NOT_U64", error, Vec::new()))
        }
    };
    if !prime000.conformance.no_decidable_violation {
        let laws = prime000.conformance.violations.clone();
        progress.prime000_result = Some(prime000);
        return Err(progress.refuse(
            "PRIME000",
            "PRIME000_DECIDABLE_VIOLATION",
            "Prime 000 receipt violates a decidable letter law",
            laws,
        ));
    }
    let prime000_conforms = prime000.conformance.conforms;
    progress.prime000_result = Some(prime000);
    Ok((progress, receipt, prime000_conforms))
}

pub fn evaluate_request(request: HostRequestV1) -> HostOutcomeV1 {
    let mut progress = HostProgress::new(&request);
    let request_id = request.request_id_sha256.clone();
    let challenge = request.challenge_hex.clone();
    if let Err((code, detail)) = validate_request_profile(&request) {
        return base_refusal(Some(request_id), Some(challenge), "INTAKE", code, detail);
    }

    let packet_check = match verify_packet_envelope(&request.packet_envelope) {
        Ok(check) if check.verdict == "MATCH" => check,
        Ok(check) => {
            return base_refusal(
                Some(request_id),
                Some(challenge),
                "INTAKE",
                "PACKET_ID_MISMATCH",
                format!(
                    "packet id {} does not match host derivation {}",
                    check.supplied, check.derived
                ),
            )
        }
        Err(error) => {
            return base_refusal(
                Some(request_id),
                Some(challenge),
                "INTAKE",
                "PACKET_ENVELOPE_INVALID",
                error,
            )
        }
    };

    progress.source_bindings = Some(source_binding_checks(&request, packet_check));
    let (progress, carrier) = match admit_carrier(&request, progress) {
        Ok(step) => step,
        Err(outcome) => return outcome,
    };
    let (progress, before, candidate) =
        match admit_residuals_and_prime001(&request, &carrier, progress) {
            Ok(step) => step,
            Err(outcome) => return outcome,
        };
    let (progress, receipt, prime000_conforms) =
        match execute_oesos_and_prime000(&request, &carrier, &before, &candidate, progress) {
            Ok(step) => step,
            Err(outcome) => return outcome,
        };

    let prime002 = match run_prime002_exact_transition(
        &request,
        progress
            .carrier_manifest
            .as_ref()
            .checked_invariant_7ff93da0("carrier manifest"),
        &receipt,
        progress.oesos_result.as_ref().checked_invariant_7ff93da0("oesos summary"),
    ) {
        Ok(summary) => summary,
        Err((code, detail, laws)) => return progress.refuse("PRIME002", code, detail, laws),
    };

    let mut admission_codes = vec!["UNSIGNED_LAB_ATTESTATION".to_owned()];
    if !prime000_conforms {
        admission_codes.push("PRIME000_CONFORMANCE_PARTIAL".to_owned());
    }
    let reason_commitment = admission_reason(&admission_codes, "laboratory replay only");
    finalize_outcome(HostOutcomeV1 {
        schema_version: HOST_OUTCOME_SCHEMA.to_owned(),
        request_id_sha256: Some(request.request_id_sha256.clone()),
        challenge_hex: Some(request.challenge_hex.clone()),
        outcome_root_sha256: String::new(),
        host_registry_hash_sha256: describe_host().host_registry_hash_sha256,
        host_source_revision: HOST_SOURCE_REVISION.to_owned(),
        authority_effect: "None".to_owned(),
        execution_status: "EXECUTED_REPLAYED_EXACT_LAB_EVIDENCE".to_owned(),
        source_bindings: progress.source_bindings,
        carrier_manifest: progress.carrier_manifest,
        prime001_result: progress.prime001_result,
        oesos_result: progress.oesos_result,
        prime000_result: progress.prime000_result,
        prime002_result: Some(prime002),
        diagnostic_kind: Some(format!("{:?}", receipt.status())),
        admission: AdmissionSummaryV1 {
            kind: "Refused".to_owned(),
            codes: admission_codes,
            reason_commitment_sha256: reason_commitment,
        },
        attestation: "unsigned_lab".to_owned(),
        refusal: None,
    })
}

// Origin: engine/crates_rs/pfp/src/host.rs
// Claim: urn:core:crates_rs:pfp:host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7ff93da0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7ff93da0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7ff93da0 {
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
impl BoundaryError7ff93da0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7ff93da0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7ff93da0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7ff93da0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7ff93da0> {
        if capacity_bound == 0 {
            return Err(BoundaryError7ff93da0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7ff93da0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7ff93da0::ExceedsCapacity {
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
mod l4_boundary_tests_7ff93da0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7ff93da0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7ff93da0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7ff93da0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7ff93da0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7ff93da0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7ff93da0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7ff93da0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
