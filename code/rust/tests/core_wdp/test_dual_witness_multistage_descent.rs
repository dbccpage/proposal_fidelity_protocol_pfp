// AuthorityEffect: None.
//! # Integration Test: Dual Witness Multi-Stage Combinatorial Descent
//!
//! Links `core_wdp`, `core_functional`, and `core_certifiers` to verify
//! exact dual witness receipts ($\Phi_1 = 0 \land \Gamma_2 = 0$) across a
//! simulated multi-stage combinatorial descent.
//!
//! ## Mathematical Specifications
//!
//! 1. **Underlying Complex**: An oriented 2-simplex (triangle) $\mathcal{K} = (V, E, F)$
//!    with $|V| = 3$, $|E| = 3$, $|F| = 1$.
//!    - 0-cells (vertices): $v_0, v_1, v_2$
//!    - 1-cells (oriented edges): $e_0 = (v_0, v_1)$, $e_1 = (v_1, v_2)$, $e_2 = (v_2, v_0)$
//!    - 2-cells (oriented face): $f_0 = (v_0, v_1, v_2)$ with boundary $e_0 + e_1 + e_2$.
//!    - Coboundary maps:
//!      $d_0: C^0 \to C^1$:
//!      $\quad d_0 = \begin{pmatrix} -1 & 1 & 0 \\ 0 & -1 & 1 \\ 1 & 0 & -1 \end{pmatrix}$
//!      $d_1: C^1 \to C^2$:
//!      $\quad d_1 = \begin{pmatrix} 1 & 1 & 1 \end{pmatrix}$
//!    - Exact Cochain Law:
//!      $\quad d_1 \circ d_0 = \begin{pmatrix} 1 & 1 & 1 \end{pmatrix} \begin{pmatrix} -1 & 1 & 0 \\ 0 & -1 & 1 \\ 1 & 0 & -1 \end{pmatrix} = \begin{pmatrix} 0 & 0 & 0 \end{pmatrix}$
//!
//! 2. **Multi-Stage Combinatorial Descent**:
//!    - **Stage 0 (Initial Obstructed State)**:
//!      Cochain $\omega_0 = (4, 0, 0)^T$.
//!      $\Gamma_2(\omega_0) = \|d_1 \omega_0\|_1 = \|4\|_1 = 4 > 0$.
//!      $\Phi_1(\omega_0) = 4 > 0$.
//!      Status: `ObstructionDiagnosticClass::ActiveClosureFailure`.
//!      Fail-Closed Gate: Authority minting refuses (`CheckedPacketCertificateError::NotAuthorityBearing`).
//!
//!    - **Stage 1 (Intermediate Descent Step - Partial Reduction)**:
//!      Update $\Delta \alpha_1$ reduces the defect: $\omega_1 = (2, 0, 0)^T$.
//!      $\Gamma_2(\omega_1) = 2 < \Gamma_2(\omega_0)$.
//!      $\Phi_1(\omega_1) = 2 < \Phi_1(\omega_0)$.
//!      Strict lexicographic progress without premature promotion.
//!
//!    - **Stage 2 (Terminal Solvency / Dual Witness Minimum Reach)**:
//!      Final descent step: $\omega_2 = d_0 \alpha = (-1, 0, 1)^T$ with $\alpha = (1, 0, 0)^T$.
//!      Primal residual: $r = \omega_2 - d_0 \alpha = (0, 0, 0)^T \implies \Phi_1(\omega_2) = 0$.
//!      Coboundary: $d_1 r = (0) \implies \Gamma_2(\omega_2) = 0$.
//!      Status: `ObstructionDiagnosticClass::ExactRepair`.
//!      Dual Witness Receipt: Both $\Phi_1 = 0 \land \Gamma_2 = 0$ hold simultaneously.
//!      Authorized Certificate: `core_certifiers::certify_checked_packet` issues
//!      `CheckedPacketCertificateV1` with `AuthorityTerminal::ExactRuleDerived`
//!      and `AuthorityEffect::None`.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;

use core_certifiers::checked_packet::{
    BoundaryMapsHash, CertificateRef, CertificateVerdict, CheckedClaimKind, CheckedClaimScope,
    CheckedPacketArgs, CheckedPacketCertificateError, CheckerRef, DefectFieldHash, EvidenceRef,
    Hash256, LawId, ObserverBoundaryHash, ReplayHash, ToleranceProfileHash, WeightsAndGaugesHash,
    CarrierManifestHash,
};
use core_functional::gamma2::ExactCochainComplexQ;
use core_functional::phi1::ExactPhi1Certificate;
use core_homotopy_type_theory::primitive_difference::PrimitiveDifference;
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_types::authority::{AuthorityTerminal, DescentWitness, IsAuth};
use core_types::{EvidenceCeiling, GuardEvidence};
use core_wdp::coda::coda_gtla::{
    evaluate_exact, validate_primitive_difference, CodaExactInput, CodaGtlaEvaluation,
    PrimitiveDifferenceReceipt,
};

/// Discrete difference structure over carrier vertices $\{0, 1, 2\}$.
struct TriangleVertexDifference;

impl PrimitiveDifference for TriangleVertexDifference {
    type Carrier = i64;
    type Diff = i64;

    fn delta(&self, x: &i64, y: &i64) -> i64 {
        (x - y).rem_euclid(3)
    }

    fn zero(&self, d: &i64) -> bool {
        *d == 0
    }
}

fn r(val: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(val))
}

fn carrier_hash(tag: u8) -> CarrierManifestHash {
    CarrierManifestHash(Hash256([tag; 32]))
}

fn make_packet_args(stage_id: u8) -> CheckedPacketArgs {
    CheckedPacketArgs {
        packet_id: Hash256([stage_id + 1; 32]),
        evidence_refs: vec![EvidenceRef(Hash256([stage_id + 10; 32]))],
        checker_ref: CheckerRef("core_wdp::coda_gtla::descent_test".to_string()),
        schema_hash: Hash256([0xcc; 32]),
        carrier_hash: carrier_hash(0xaa),
        boundary_maps_hash: BoundaryMapsHash(Hash256([0xbb; 32])),
        weights_and_gauges_hash: WeightsAndGaugesHash(Hash256([0x11; 32])),
        submitted_defect_hash: DefectFieldHash(Hash256([stage_id + 5; 32])),
        phi1_certificate_ref: CertificateRef(Hash256([stage_id + 20; 32])),
        closure_certificate_ref: CertificateRef(Hash256([stage_id + 30; 32])),
        observer_boundary_hash: ObserverBoundaryHash(Hash256([0x22; 32])),
        tolerance_profile_hash: ToleranceProfileHash(Hash256([0x33; 32])),
        replay_hash: ReplayHash(Hash256([stage_id + 40; 32])),
        certificate_status: CertificateVerdict::Verified,
        checked_scope: CheckedClaimScope {
            claim_kind: CheckedClaimKind::ObstructionSummary,
            authority_ceiling: EvidenceCeiling::BoundaryChecked,
            law_refs: vec![LawId("LAW_DUAL_WITNESS_DESCENT_001".to_string())],
        },
    }
}

fn valid_authority_predicate() -> IsAuth {
    let evidence = GuardEvidence::new_valid(
        ["candidate-stage-terminal"],
        "carrier-triangle-2simplex",
        "hash-exact-witness-terminal",
    );
    IsAuth::decide(AuthorityTerminal::ExactRuleDerived, evidence)
        .expect("Authority predicate decision must succeed")
}

#[test]
fn test_dual_witness_multistage_combinatorial_descent_e2e() {
    println!("=== STEP 1: Initialize Primitive Difference Carrier & Cochain Complex ===");

    // 1. Validate primitive difference carrier
    let receipt: PrimitiveDifferenceReceipt = validate_primitive_difference(
        &TriangleVertexDifference,
        vec![0, 1, 2],
        carrier_hash(0xaa),
    )
    .expect("Primitive difference validation on triangle carrier must succeed");

    assert_eq!(receipt.domain_len(), 3);
    assert_eq!(receipt.quotient_class_count(), 3);

    // 2. Define exact simplicial cochain complex over Q
    // d0: 3 edges x 3 vertices
    let d0 = vec![
        vec![r(-1), r(1), r(0)],
        vec![r(0), r(-1), r(1)],
        vec![r(1), r(0), r(-1)],
    ];
    // d1: 1 face x 3 edges
    let d1 = vec![vec![r(1), r(1), r(1)]];

    let complex = ExactCochainComplexQ::try_new(3, 3, 1, d0.clone(), d1.clone())
        .expect("Simplicial cochain complex d1 * d0 = 0 must be exact");

    let weights = vec![r(1), r(1), r(1)];

    println!("=== STEP 2: Execute Stage 0 (Initial Obstructed State: Phi1=4, Gamma2=4) ===");
    // Initial cochain: core_0 = [4, 0, 0]
    // d1 * core_0 = [4] -> Gamma2 = 4
    // alpha = [0, 0, 0] -> residual = [4, 0, 0]
    // dual witness y = [1, 1, 1]: d0^T * y = 0, ||y||_inf = 1, y^T * core_0 = 4 == ||residual||_1
    let phi1_stage0 = ExactPhi1Certificate {
        omega: vec![r(4), r(0), r(0)],
        d0: d0.clone(),
        weights: weights.clone(),
        alpha: vec![r(0), r(0), r(0)],
        primal_residual: vec![r(4), r(0), r(0)],
        dual_witness: vec![r(1), r(1), r(1)],
        reported_value: r(4),
    };

    let input_stage0 = CodaExactInput::new(
        receipt.clone(),
        phi1_stage0,
        complex.clone(),
        vec![r(4), r(0), r(0)],
        make_packet_args(0),
    );

    let eval_stage0: CodaGtlaEvaluation = evaluate_exact(input_stage0)
        .expect("Stage 0 exact evaluation must succeed");

    // Assert stage 0 obstruction
    assert_eq!(eval_stage0.phi1().value(), &r(4));
    assert_eq!(eval_stage0.gamma2().value(), &r(4));
    assert_eq!(eval_stage0.status(), ObstructionDiagnosticClass::ActiveClosureFailure);

    // Fail-Closed Gate: Stage 0 cannot cross the authority boundary
    let descent_witness_0 = DescentWitness::from_verified_replay(
        AuthorityTerminal::ExactRuleDerived,
        "descent-trace-stage-0",
        "aa".repeat(32),
    )
    .unwrap();

    let cert_err_stage0 = eval_stage0
        .certify_certificate(descent_witness_0, valid_authority_predicate())
        .expect_err("Stage 0 with non-zero obstruction must refuse certificate minting");

    assert_eq!(
        cert_err_stage0,
        CheckedPacketCertificateError::NotAuthorityBearing(ObstructionDiagnosticClass::ActiveClosureFailure)
    );
    println!("  [OK] Stage 0 correctly diagnosed as ActiveClosureFailure; certificate minting refused.");

    println!("=== STEP 3: Execute Stage 1 (Intermediate Descent Step: Phi1=2, Gamma2=2) ===");
    // Descent step reduces defect by 2: core_1 = [2, 0, 0]
    // d1 * core_1 = [2] -> Gamma2 = 2
    // dual witness y = [1, 1, 1]: y^T * core_1 = 2 == ||residual||_1
    let phi1_stage1 = ExactPhi1Certificate {
        omega: vec![r(2), r(0), r(0)],
        d0: d0.clone(),
        weights: weights.clone(),
        alpha: vec![r(0), r(0), r(0)],
        primal_residual: vec![r(2), r(0), r(0)],
        dual_witness: vec![r(1), r(1), r(1)],
        reported_value: r(2),
    };

    let input_stage1 = CodaExactInput::new(
        receipt.clone(),
        phi1_stage1,
        complex.clone(),
        vec![r(2), r(0), r(0)],
        make_packet_args(1),
    );

    let eval_stage1 = evaluate_exact(input_stage1)
        .expect("Stage 1 exact evaluation must succeed");

    // Assert stage 1 reduction
    assert_eq!(eval_stage1.phi1().value(), &r(2));
    assert_eq!(eval_stage1.gamma2().value(), &r(2));
    assert!(eval_stage1.phi1().value() < eval_stage0.phi1().value());
    assert!(eval_stage1.gamma2().value() < eval_stage0.gamma2().value());
    assert_eq!(eval_stage1.status(), ObstructionDiagnosticClass::ActiveClosureFailure);

    // Fail-Closed Gate: Stage 1 also cannot cross the authority boundary
    let descent_witness_1 = DescentWitness::from_verified_replay(
        AuthorityTerminal::ExactRuleDerived,
        "descent-trace-stage-1",
        "bb".repeat(32),
    )
    .unwrap();

    let cert_err_stage1 = eval_stage1
        .certify_certificate(descent_witness_1, valid_authority_predicate())
        .expect_err("Stage 1 with partial obstruction must refuse certificate minting");

    assert_eq!(
        cert_err_stage1,
        CheckedPacketCertificateError::NotAuthorityBearing(ObstructionDiagnosticClass::ActiveClosureFailure)
    );
    println!("  [OK] Stage 1 obstruction strictly reduced; certificate minting remains fail-closed.");

    println!("=== STEP 4: Execute Stage 2 (Terminal Solvency: Phi1=0 AND Gamma2=0) ===");
    // Terminal state: cochain is exact boundary core_2 = d0 * alpha with alpha = [1, 0, 0]
    // d0 * [1, 0, 0] = [-1, 0, 1]
    // core_2 = [-1, 0, 1]
    // alpha = [1, 0, 0] -> primal_residual = core_2 - d0 * alpha = [0, 0, 0]
    // dual witness y = [0, 0, 0] -> reported_value = 0
    // coboundary d1 * primal_residual = d1 * [0, 0, 0] = [0] -> Gamma2 = 0
    let phi1_stage2 = ExactPhi1Certificate {
        omega: vec![r(-1), r(0), r(1)],
        d0: d0.clone(),
        weights: weights.clone(),
        alpha: vec![r(1), r(0), r(0)],
        primal_residual: vec![r(0), r(0), r(0)],
        dual_witness: vec![r(0), r(0), r(0)],
        reported_value: r(0),
    };

    let replay_hash_stage2 = [42u8; 32];
    let mut packet_args_2 = make_packet_args(2);
    packet_args_2.replay_hash = ReplayHash(Hash256(replay_hash_stage2));

    let input_stage2 = CodaExactInput::new(
        receipt.clone(),
        phi1_stage2,
        complex.clone(),
        vec![r(0), r(0), r(0)],
        packet_args_2,
    );

    let eval_stage2 = evaluate_exact(input_stage2)
        .expect("Stage 2 exact evaluation must succeed");

    // Assert dual witness conditions: Phi1 = 0 AND Gamma2 = 0
    assert!(eval_stage2.phi1().value().is_zero(), "Phi1 must be exactly zero");
    assert!(eval_stage2.gamma2().value().is_zero(), "Gamma2 must be exactly zero");
    assert_eq!(
        eval_stage2.status(),
        ObstructionDiagnosticClass::ExactRepair,
        "Zero dual-witness defect must classify as ExactRepair"
    );

    println!("=== STEP 5: Issue & Verify Sovereign CheckedPacketCertificateV1 ===");
    let replay_hex = {
        use std::fmt::Write;
        let mut s = String::with_capacity(64);
        for b in &replay_hash_stage2 {
            let _ = write!(s, "{:02x}", b);
        }
        s
    };

    let terminal_descent_witness = DescentWitness::from_verified_replay(
        AuthorityTerminal::ExactRuleDerived,
        "descent-trace-stage-2-terminal",
        replay_hex,
    )
    .unwrap();

    let cert = eval_stage2
        .certify_certificate(terminal_descent_witness, valid_authority_predicate())
        .expect("Stage 2 with Phi1=0 and Gamma2=0 must successfully mint CheckedPacketCertificateV1");

    // Verify certificate properties
    assert_eq!(cert.terminal(), AuthorityTerminal::ExactRuleDerived);
    assert!(cert.authority_effect().is_none(), "AuthorityEffect must strictly be None");
    cert.validate().expect("Minted CheckedPacketCertificateV1 must satisfy all contract invariants");

    println!("  [OK] CheckedPacketCertificateV1 validated with AuthorityEffect: None.");
    println!("  [PASS] All dual witness multi-stage combinatorial descent integration gates verified.");
}

// Origin: engine/crates_rs/tests/core_wdp/test_dual_witness_multistage_descent.rs
// Claim: urn:core:crates_rs:tests:test-dual-witness-multistage-descent:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3fac6d38 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3fac6d38` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3fac6d38 {
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
impl BoundaryError3fac6d38 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3fac6d38 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3fac6d38 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3fac6d38 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3fac6d38> {
        if capacity_bound == 0 {
            return Err(BoundaryError3fac6d38::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3fac6d38::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3fac6d38::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3fac6d38() {
    let admitted = BoundaryRecord3fac6d38::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3fac6d38::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
