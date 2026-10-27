use num_bigint::BigInt;
use num_rational::BigRational;

use core_certifiers::checked_packet::{
    BoundaryMapsHash, CarrierManifestHash, CertificateRef, CertificateVerdict, CheckedClaimKind,
    CheckedClaimScope, CheckedPacketArgs, CheckedPacketCertificateError, CheckerRef,
    DefectFieldHash, EvidenceRef, Hash256, ObserverBoundaryHash, ReplayHash, ToleranceProfileHash,
    WeightsAndGaugesHash,
};
use core_functional::gamma2::ExactCochainComplexQ;
use core_functional::phi1::ExactPhi1Certificate;
use core_homotopy_type_theory::primitive_difference::PrimitiveDifference;
use core_pipelines::bounded_rewrite::{
    run_bounded_rewrites, BoundedRewritePolicy, BoundedRewriteTerminal,
};
use core_pipelines::loop_step::{manifest_hash, TerminalizedRow};
use core_pipelines::rewrite_scheduler::{schedule_exact_rewrite, ExactRewriteError};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_types::authority::{AuthorityEffect, AuthorityTerminal, DescentWitness, IsAuth};
use core_types::{EvidenceCeiling, GuardEvidence};
use core_wdp::coda::coda_gtla::{evaluate_exact, validate_primitive_difference, CodaExactInput};

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

#[derive(Clone, Copy)]
enum ExactCase {
    Repair,
    Survivor,
    Open,
}

fn r(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

fn carrier_hash(byte: u8) -> CarrierManifestHash {
    CarrierManifestHash(Hash256([byte; 32]))
}

fn packet_args(seed: u8, carrier_byte: u8, replay_byte: u8) -> CheckedPacketArgs {
    CheckedPacketArgs {
        packet_id: Hash256([seed; 32]),
        evidence_refs: vec![EvidenceRef(Hash256([seed.wrapping_add(1); 32]))],
        checker_ref: CheckerRef(format!("exact-rewrite-test-{seed}")),
        schema_hash: Hash256([seed.wrapping_add(2); 32]),
        carrier_hash: carrier_hash(carrier_byte),
        boundary_maps_hash: BoundaryMapsHash(Hash256([seed.wrapping_add(3); 32])),
        weights_and_gauges_hash: WeightsAndGaugesHash(Hash256([seed.wrapping_add(4); 32])),
        submitted_defect_hash: DefectFieldHash(Hash256([seed.wrapping_add(5); 32])),
        phi1_certificate_ref: CertificateRef(Hash256([seed.wrapping_add(6); 32])),
        closure_certificate_ref: CertificateRef(Hash256([seed.wrapping_add(7); 32])),
        observer_boundary_hash: ObserverBoundaryHash(Hash256([seed.wrapping_add(8); 32])),
        tolerance_profile_hash: ToleranceProfileHash(Hash256([seed.wrapping_add(9); 32])),
        replay_hash: ReplayHash(Hash256([replay_byte; 32])),
        certificate_status: CertificateVerdict::Verified,
        checked_scope: CheckedClaimScope {
            claim_kind: CheckedClaimKind::ObstructionSummary,
            authority_ceiling: EvidenceCeiling::BoundaryChecked,
            law_refs: vec![],
        },
    }
}

fn exact_input(case: ExactCase, seed: u8, carrier_byte: u8, replay_byte: u8) -> CodaExactInput {
    let (phi1, d1) = match case {
        ExactCase::Repair => (
            ExactPhi1Certificate {
                omega: vec![r(1)],
                d0: vec![vec![r(1)]],
                weights: vec![r(1)],
                alpha: vec![r(1)],
                primal_residual: vec![r(0)],
                dual_witness: vec![r(0)],
                reported_value: r(0),
            },
            vec![vec![r(0)]],
        ),
        ExactCase::Survivor => (
            ExactPhi1Certificate {
                omega: vec![r(1)],
                d0: vec![vec![r(0)]],
                weights: vec![r(1)],
                alpha: vec![r(0)],
                primal_residual: vec![r(1)],
                dual_witness: vec![r(1)],
                reported_value: r(1),
            },
            vec![vec![r(0)]],
        ),
        ExactCase::Open => (
            ExactPhi1Certificate {
                omega: vec![r(1)],
                d0: vec![vec![r(0)]],
                weights: vec![r(1)],
                alpha: vec![r(0)],
                primal_residual: vec![r(1)],
                dual_witness: vec![r(1)],
                reported_value: r(1),
            },
            vec![vec![r(1)]],
        ),
    };
    let residual = phi1.primal_residual.clone();
    let complex = ExactCochainComplexQ::try_new(1, 1, 1, phi1.d0.clone(), d1).unwrap();
    let receipt = validate_primitive_difference(
        &ParityDifference,
        vec![0, 1, 2, 3],
        carrier_hash(carrier_byte),
    )
    .unwrap();

    CodaExactInput::new(
        receipt,
        phi1,
        complex,
        residual,
        packet_args(seed, carrier_byte, replay_byte),
    )
}

fn bound_row(input: CodaExactInput) -> TerminalizedRow {
    let evaluation = evaluate_exact(input).unwrap();
    let replay_hash = blake3::Hash::from_bytes(evaluation.checked_packet().replay_hash().0 .0);
    TerminalizedRow::new(
        evaluation.checked_packet().clone(),
        evaluation.phi1().clone(),
        evaluation.gamma2().clone(),
        replay_hash,
    )
}

fn all_true_is_auth() -> IsAuth {
    let evidence = GuardEvidence::new_valid(["cand-1"], "carrier-1", "hash-1");
    IsAuth::decide(AuthorityTerminal::ExactRuleDerived, evidence).unwrap()
}

#[test]
fn survivor_to_exact_repair_creates_a_fresh_strictly_descending_row() {
    let previous = bound_row(exact_input(ExactCase::Survivor, 1, 4, 12));
    let previous_manifest = manifest_hash(previous.packet()).unwrap();
    let previous_replay = *previous.replay_hash();

    let result =
        schedule_exact_rewrite(&previous, exact_input(ExactCase::Repair, 20, 4, 22)).unwrap();
    let diagnostic = result.diagnostic();

    assert_eq!(diagnostic.before_phi1(), &r(1));
    assert_eq!(diagnostic.after_phi1(), &r(0));
    assert_eq!(diagnostic.phi1_reduction(), r(1));
    assert_eq!(diagnostic.before_gamma2(), &r(0));
    assert_eq!(diagnostic.after_gamma2(), &r(0));
    assert_eq!(diagnostic.gamma2_reduction(), r(0));
    assert_eq!(diagnostic.status(), ObstructionDiagnosticClass::ExactRepair);
    assert_ne!(
        diagnostic.input_manifest_hash(),
        diagnostic.output_manifest_hash()
    );
    assert!(matches!(
        diagnostic.authority_effect(),
        AuthorityEffect::None
    ));

    assert_eq!(previous.phi1().value(), &r(1));
    assert_eq!(manifest_hash(previous.packet()).unwrap(), previous_manifest);
    assert_eq!(*previous.replay_hash(), previous_replay);

    assert_eq!(result.row().phi1().value(), &r(0));
    assert_eq!(result.row().replay_hash(), diagnostic.output_replay_hash());
    assert_eq!(
        manifest_hash(result.row().packet()).unwrap(),
        *diagnostic.output_manifest_hash()
    );
}

#[test]
fn identity_proposal_is_refused_even_when_packet_metadata_changes() {
    let previous = bound_row(exact_input(ExactCase::Survivor, 1, 4, 12));
    let error =
        schedule_exact_rewrite(&previous, exact_input(ExactCase::Survivor, 20, 4, 22)).unwrap_err();

    assert!(matches!(error, ExactRewriteError::NoStrictDescent));
}

#[test]
fn an_increase_in_either_exact_functional_is_refused() {
    let exact = bound_row(exact_input(ExactCase::Repair, 1, 4, 12));
    let phi1_error =
        schedule_exact_rewrite(&exact, exact_input(ExactCase::Survivor, 20, 4, 22)).unwrap_err();
    assert!(matches!(
        phi1_error,
        ExactRewriteError::Phi1Increased { .. }
    ));

    let survivor = bound_row(exact_input(ExactCase::Survivor, 30, 4, 32));
    let gamma2_error =
        schedule_exact_rewrite(&survivor, exact_input(ExactCase::Open, 40, 4, 42)).unwrap_err();
    assert!(matches!(
        gamma2_error,
        ExactRewriteError::Gamma2Increased { .. }
    ));
}

#[test]
fn gamma2_only_strict_descent_is_accepted_exactly() {
    let previous = bound_row(exact_input(ExactCase::Open, 1, 4, 12));
    let result =
        schedule_exact_rewrite(&previous, exact_input(ExactCase::Survivor, 20, 4, 22)).unwrap();

    assert_eq!(result.diagnostic().phi1_reduction(), r(0));
    assert_eq!(result.diagnostic().gamma2_reduction(), r(1));
    assert_eq!(
        result.diagnostic().status(),
        ObstructionDiagnosticClass::ClosedResidual
    );
}

#[test]
fn carrier_change_is_refused_after_canonical_evaluation() {
    let previous = bound_row(exact_input(ExactCase::Survivor, 1, 4, 12));
    let error =
        schedule_exact_rewrite(&previous, exact_input(ExactCase::Repair, 20, 5, 22)).unwrap_err();

    assert!(matches!(error, ExactRewriteError::CarrierChanged));
}

#[test]
fn reused_replay_hash_is_refused_for_an_otherwise_strict_descent() {
    let previous = bound_row(exact_input(ExactCase::Survivor, 1, 4, 12));
    let error =
        schedule_exact_rewrite(&previous, exact_input(ExactCase::Repair, 20, 4, 12)).unwrap_err();

    assert!(matches!(error, ExactRewriteError::ReplayHashUnchanged));
}

#[test]
fn scheduler_refuses_an_input_row_not_bound_to_its_packet_replay() {
    let evaluation = evaluate_exact(exact_input(ExactCase::Survivor, 1, 4, 12)).unwrap();
    let unbound = TerminalizedRow::new(
        evaluation.checked_packet().clone(),
        evaluation.phi1().clone(),
        evaluation.gamma2().clone(),
        blake3::hash(b"not-the-packet-replay"),
    );

    let error =
        schedule_exact_rewrite(&unbound, exact_input(ExactCase::Repair, 20, 4, 22)).unwrap_err();
    assert!(matches!(
        error,
        ExactRewriteError::PreviousReplayBindingMismatch
    ));
}

#[test]
fn certificate_evidence_requires_the_output_packet_replay_and_is_auth() {
    let previous = bound_row(exact_input(ExactCase::Survivor, 1, 4, 12));
    let result =
        schedule_exact_rewrite(&previous, exact_input(ExactCase::Repair, 20, 4, 22)).unwrap();

    let witness = DescentWitness::from_verified_replay(
        AuthorityTerminal::ExactRuleDerived,
        result.diagnostic().descent_ref(),
        result.diagnostic().output_replay_hash_hex(),
    )
    .unwrap();
    let certificate = result
        .certify_certificate(witness, all_true_is_auth())
        .unwrap();
    assert_eq!(certificate.terminal(), AuthorityTerminal::ExactRuleDerived);
    assert!(certificate.authority_effect().is_none());

    let wrong_witness = DescentWitness::from_verified_replay(
        AuthorityTerminal::ExactRuleDerived,
        result.diagnostic().descent_ref(),
        "ff".repeat(32),
    )
    .unwrap();
    assert_eq!(
        result.certify_certificate(wrong_witness, all_true_is_auth()),
        Err(CheckedPacketCertificateError::WitnessPacketMismatch)
    );
}
#[test]
fn bounded_runner_executes_a_nonvacuous_two_step_descent() {
    let initial = bound_row(exact_input(ExactCase::Open, 1, 4, 12));
    let input_manifest = manifest_hash(initial.packet()).unwrap();
    let accept_all = |_: &core_pipelines::rewrite_scheduler::ExactRewriteDiagnostic| true;
    let result = run_bounded_rewrites(
        initial,
        vec![
            vec![exact_input(ExactCase::Survivor, 20, 4, 22)],
            vec![exact_input(ExactCase::Repair, 30, 4, 32)],
        ],
        BoundedRewritePolicy {
            max_attempts: 4,
            max_steps: 4,
        },
        &accept_all,
    );

    assert_eq!(result.terminal(), BoundedRewriteTerminal::ExactRepair);
    assert_eq!(result.attempts(), 2);
    assert_eq!(result.diagnostics().len(), 2);
    assert_eq!(
        result.diagnostics()[0].input_manifest_hash(),
        &input_manifest
    );
    assert_eq!(result.diagnostics()[0].phi1_reduction(), r(0));
    assert_eq!(result.diagnostics()[0].gamma2_reduction(), r(1));
    assert_eq!(result.diagnostics()[1].phi1_reduction(), r(1));
    assert!(result.authority_effect().is_none());
}

#[test]
fn bounded_runner_prefers_phi1_descent_before_gamma2_only_descent() {
    let initial = bound_row(exact_input(ExactCase::Open, 1, 4, 12));
    let accept_all = |_: &core_pipelines::rewrite_scheduler::ExactRewriteDiagnostic| true;
    let result = run_bounded_rewrites(
        initial,
        vec![vec![
            exact_input(ExactCase::Survivor, 20, 4, 22),
            exact_input(ExactCase::Repair, 30, 4, 32),
        ]],
        BoundedRewritePolicy {
            max_attempts: 3,
            max_steps: 1,
        },
        &accept_all,
    );

    assert_eq!(result.terminal(), BoundedRewriteTerminal::ExactRepair);
    assert_eq!(result.diagnostics().len(), 1);
    assert_eq!(result.diagnostics()[0].phi1_reduction(), r(1));
}

#[test]
fn bounded_controls_terminalize_stagnation_cycle_retry_and_observer_refusal() {
    let accept_all = |_: &core_pipelines::rewrite_scheduler::ExactRewriteDiagnostic| true;
    let stagnation = run_bounded_rewrites(
        bound_row(exact_input(ExactCase::Survivor, 1, 4, 12)),
        vec![vec![exact_input(ExactCase::Survivor, 20, 4, 22)]],
        BoundedRewritePolicy {
            max_attempts: 3,
            max_steps: 2,
        },
        &accept_all,
    );
    assert_eq!(stagnation.terminal(), BoundedRewriteTerminal::Stagnation);

    let cycle = run_bounded_rewrites(
        bound_row(exact_input(ExactCase::Survivor, 1, 4, 12)),
        vec![vec![exact_input(ExactCase::Repair, 20, 4, 12)]],
        BoundedRewritePolicy {
            max_attempts: 3,
            max_steps: 2,
        },
        &accept_all,
    );
    assert_eq!(cycle.terminal(), BoundedRewriteTerminal::CycleDetected);

    let retry = run_bounded_rewrites(
        bound_row(exact_input(ExactCase::Survivor, 1, 4, 12)),
        vec![vec![exact_input(ExactCase::Open, 20, 4, 22)]],
        BoundedRewritePolicy {
            max_attempts: 1,
            max_steps: 2,
        },
        &accept_all,
    );
    assert_eq!(retry.terminal(), BoundedRewriteTerminal::RetryExhausted);

    let refuse_all = |_: &core_pipelines::rewrite_scheduler::ExactRewriteDiagnostic| false;
    let observer = run_bounded_rewrites(
        bound_row(exact_input(ExactCase::Survivor, 1, 4, 12)),
        vec![vec![exact_input(ExactCase::Repair, 20, 4, 22)]],
        BoundedRewritePolicy {
            max_attempts: 3,
            max_steps: 2,
        },
        &refuse_all,
    );
    assert_eq!(observer.terminal(), BoundedRewriteTerminal::ObserverRefused);
    assert!(observer.authority_effect().is_none());
}

// Origin: engine/crates_rs/tests/core_pipelines/exact_rewrite_scheduler.rs
// Claim: urn:core:crates_rs:tests:exact-rewrite-scheduler:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd30a436d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd30a436d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord30a436d {
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
impl BoundaryErrord30a436d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord30a436d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord30a436d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd30a436d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord30a436d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord30a436d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord30a436d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord30a436d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d30a436d() {
    let admitted = BoundaryRecordd30a436d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd30a436d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
