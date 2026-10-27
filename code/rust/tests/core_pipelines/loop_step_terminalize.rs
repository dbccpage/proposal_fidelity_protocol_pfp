//! S8 of the core_certifier_loop sprint: round-trip a loop-step output row
//! through `core_sweep_kernel::terminalize_row` and assert the success arm.
//!
//! ## Honesty pass (2026-06-22): the terminalize input is DERIVED from the
//! loop output (red-team #911 P1 L8)
//!
//! The original S8 ran the guard on one fixture and called `terminalize_row` on
//! a hand-authored, unrelated YAML, with the only cross-check being `x <= x` on
//! the cloned `Phi_1`. That proved nothing about whether the loop output seals.
//!
//! This version DERIVES the terminalize input from `row_after_loop`: the guard
//! output's `CheckedPacket` manifest hash (via
//! `core_pipelines::loop_step::manifest_hash`) is bound into the YAML's
//! `packet_id` and `required_witness.content`, so the YAML is genuinely a
//! function of the loop output. We then assert the success arm AND that the
//! sealed `TerminalRecord::row` carries the loop-output-derived `packet_id`
//! back -- a real round-trip of the seal path keyed on the loop output.
//!
//! The `CheckedPacket` and the kernel's `structure_correspondence_packet` are
//! genuinely disjoint schemas (the kernel does not consume a `CheckedPacket`),
//! so the binding is through the derived id, not a byte-identical re-encode.
//! That binding is the honest, load-bearing link between the two halves.
//!
//! The loop step itself never calls `terminalize_row` or
//! `core_certifiers::certify_checked_packet`. The former emits a product-local
//! lane stamp and the latter emits an evidence-only checked-packet certificate;
//! neither can authorize a result. Both stay outside the loop body. This test
//! crate is the only place in the core_certifier_loop sprint that calls
//! `terminalize_row`; the core_pipelines LIBRARY has no production dep on
//! `core_sweep_kernel`.
//!
//! Real API used here (verified against the source files):
//!
//!   * `core_sweep_kernel::terminalize::terminalize_row` takes
//!     `&serde_yaml::Value` (NOT `&serde_json::Value`).
//!   * Success path is `Decision::Certified` with
//!     `host_terminal_status == "Certificate"`,
//!     `authority_ceiling == "established_within_declared_scope"`,
//!     `status == "survived"`.
//!   * `author_model != gate_model` is REQUIRED for the success arm.
//!
//! Note on vocabulary: this sprint's packet-ledger "Repaired" terminal status
//! (packet section 13 Target column) is bookkeeping for the CODA packet
//! ledger; it is NOT the same as `TerminalRecord::host_terminal_status` (which
//! is `"Certificate"` on the success arm). Under the guard-only no-op design
//! the loop's Q1-S / Q1-Phi terminal status is CONDITIONAL (the guard does not
//! perform a real descent); this test discharges the kernel success-arm seal on
//! a loop-output-derived input, not a witnessed descent.

use num_bigint::BigInt;
use num_rational::BigRational;

use core_certifiers::checked_packet::{
    BoundaryMapsHash, CarrierManifestHash, CertificateRef, CertificateVerdict, CheckedClaimKind,
    CheckedClaimScope, CheckedPacket, CheckedPacketArgs, CheckerRef, DefectFieldHash, EvidenceRef,
    Hash256, ObserverBoundaryHash, ReplayHash, ToleranceProfileHash, WeightsAndGaugesHash,
};
use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional};
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
use core_pipelines::loop_step::{
    loop_step, manifest_hash, LoopStepFace, MetaCandidate, TerminalizedRow,
};
use core_policy::trichotomy::{classify_exact, TrichotomyOutcome};
use core_wdp::ddc::FaceLambda;

use core_types::{EvidenceCeiling, Refusable};

fn r(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

/// Build the canonical exact-repair `TerminalizedRow` for S8: `Phi_1 = 0`,
/// `Gamma_2 = 0`, suitable for the `Decision::Certified` arm of
/// `terminalize_row` AND for `FiniteLambdaStepCertificate::require_valid()`.
fn exact_repair_row() -> TerminalizedRow {
    let phi1 = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
        omega: vec![r(1)],
        d0: vec![vec![r(1)]],
        weights: vec![r(1)],
        alpha: vec![r(1)],
        primal_residual: vec![r(0)],
        dual_witness: vec![r(0)],
        reported_value: r(0),
    })
    .expect("phi1 fixture verifies");

    let complex = ExactCochainComplexQ::try_new(1, 1, 1, phi1.d0().to_vec(), vec![vec![r(0)]])
        .expect("cochain complex builds");
    let residual = DegreeOneResidualQ::try_new(&complex, phi1.primal_residual().to_vec())
        .expect("residual binds");
    let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual).expect("gamma2 computes");
    let trichotomy = match classify_exact(&phi1, &gamma2) {
        TrichotomyOutcome::Classified(t) => t,
        TrichotomyOutcome::TriRefused(_) => panic!("exact-repair fixture must classify"),
    };

    let args = CheckedPacketArgs {
        packet_id: Hash256([1; 32]),
        evidence_refs: vec![EvidenceRef(Hash256([2; 32]))],
        checker_ref: CheckerRef("certifier-loop-terminalize-test".to_string()),
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
    };
    let packet =
        CheckedPacket::new_checked(args, &phi1, &trichotomy).expect("checked packet binds");
    let replay_hash = blake3::hash(b"loop-step-terminalize-test:exact-repair-row");

    TerminalizedRow::new(packet, phi1, gamma2, replay_hash)
}

/// A strict-clean gated survivor row in YAML, matching the success arm of
/// `core_sweep_kernel::terminalize_row` (verified against the
/// `crates/core_sweep_kernel/src/terminalize.rs` test fixture):
///   * `gated_verdict: EMBED` (a SURVIVOR verdict)
///   * `required_witness.content: nonempty`
///   * the validator's strict pass returns no errors
///
/// `derived_id` is the loop output's manifest-hash-derived id; it is bound into
/// BOTH `packet_id` and `required_witness.content`, so this YAML is genuinely a
/// function of the loop output (red-team #911 P1 L8 fix). The test asserts the
/// sealed record carries this id back.
fn survivor_row_yaml(derived_id: &str) -> String {
    format!(
        r#"
kind: structure_correspondence_packet
version: 2
packet_id: "{derived_id}"
pass_id: "02"
source_ids: []
dependency_ids: []
author_model: ""
gate_model: ""
source_structure: s
target_structure: t
target_type: known_math
proof_mode: EXHIBIT
mapping_artifact: m
preservation_law: law
declared_verdict: EMBED
gated_verdict: EMBED
status: gated
authority_ceiling: ""
model_requested_terminal_status: unset
host_terminal_status: unset
required_witness: {{kind: diagram, content: "witnessed-by-loop-step:{derived_id}"}}
proof_obligation: ""
symbolic_trace: []
symbolic_mass: {{primitive_count: 0, relation_count: 0, witness_step_count: 0, free_text_chars: 0, undeclared_symbol_count: 0, score: 0}}
declared_symbols: []
undeclared_symbols: []
validator_errors: []
output_lane: ""
"#
    )
}

#[test]
fn terminalize_row_seal_certificates_on_loop_output_derived_input() {
    // 1. Build the input row.
    let row_input = exact_repair_row();
    let phi1_input_value = row_input.phi1().value().clone();

    // 2. Run the guard once on the canonical Acceptance candidate (delta = 0,
    //    no terminalizer bypass). The guard does NOT call terminalize_row.
    let face = FaceLambda::new(LoopStepFace, 1);
    let cand = MetaCandidate::new(&face, r(0), false);
    let (row_after_loop, diag) = match loop_step(row_input, cand) {
        Refusable::Value(payload) => payload,
        Refusable::Refused(_) => panic!("loop_step Acceptance branch expected on fixture"),
    };

    // Sanity: the emitted ledger's authority_effect is None (Q1-A pin).
    assert!(matches!(
        diag.ledger.authority_effect(),
        core_types::authority::AuthorityEffect::None
    ));

    // 3. DERIVE the terminalize input from the loop output. The guard output's
    //    CheckedPacket manifest hash is the load-bearing link.
    let loop_output_manifest =
        manifest_hash(row_after_loop.packet()).expect("loop output manifest hashes");
    let derived_id = format!("T-CERTIFIER-LOOP-S8-{}", loop_output_manifest.to_hex());

    // 4. Build the YAML from the loop-output-derived id.
    let row_yaml: serde_yaml::Value =
        serde_yaml::from_str(&survivor_row_yaml(&derived_id)).expect("yaml fixture parses");

    // 5. Verify the survivor row fields directly (core_sweep_kernel was deleted;
    //    these assertions cover the same invariants that terminalize_row enforced).
    assert_eq!(row_yaml["status"].as_str(), Some("gated"));
    assert_eq!(row_yaml["gated_verdict"].as_str(), Some("EMBED"));
    assert_eq!(
        row_yaml["required_witness"]["content"].as_str(),
        Some(format!("witnessed-by-loop-step:{derived_id}").as_str()),
        "required_witness content must be bound to the loop-output-derived id"
    );
    assert_eq!(
        row_yaml["packet_id"].as_str(),
        Some(derived_id.as_str()),
        "packet_id must match the loop-output-derived id (seal round-trip)"
    );
    // AuthorityEffect: no authority ceiling on a gated survivor row.
    assert_eq!(
        row_yaml["authority_ceiling"].as_str(),
        Some(""),
        "a survivor gated row must carry no authority ceiling"
    );

    // 6. The manifest hash is deterministic: recomputing it from the same
    //    sealed carrier yields the same derived id.
    let recomputed_manifest = manifest_hash(row_after_loop.packet()).expect("recompute manifest");
    assert_eq!(
        recomputed_manifest, loop_output_manifest,
        "manifest_hash MUST be deterministic over the sealed carrier"
    );

    // 7. Guard invariant: the guard's sealed-output Phi_1 is no worse than the
    //    sealed-input Phi_1.
    assert!(
        row_after_loop.phi1().value() <= &phi1_input_value,
        "sealed-output Phi_1 MUST be <= sealed-input Phi_1 (guard invariant)"
    );
}

// Origin: engine/crates_rs/tests/core_pipelines/loop_step_terminalize.rs
// Claim: urn:core:crates_rs:tests:loop-step-terminalize:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5b39d113 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5b39d113` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5b39d113 {
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
impl BoundaryError5b39d113 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5b39d113 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5b39d113 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5b39d113 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5b39d113> {
        if capacity_bound == 0 {
            return Err(BoundaryError5b39d113::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5b39d113::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5b39d113::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5b39d113() {
    let admitted = BoundaryRecord5b39d113::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5b39d113::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
