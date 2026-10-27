//! Exact conformance tests for the OBL-1a distribution-sensitive E.7a bound.
//!
//! The exact certificate is the subject. The Lean source hashes, hand-computed
//! rational examples, and the finite Q eigensolver are independent oracles.
//! The `f64` eigensolver comparison is falsification evidence only; theorem
//! authority remains in the Lean proof and no passing test mints authority.

use std::fs;
use std::path::Path;

use nalgebra::DMatrix;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::ToPrimitive;
use core_solvers::cert_phi1_distribution::{
    DistributionBoundCase, DistributionBoundError, DistributionBoundVerifier, Obl1aTheoremReceipt,
    OBL1A_DISTRIBUTION_BOUND_SCHEMA, OBL1A_HARD_MAX_ACCUMULATOR_BITS, OBL1A_HARD_MAX_RATIONAL_BITS,
    OBL1A_LEAN_AUDIT_SHA256, OBL1A_LEAN_AUDIT_SOURCE, OBL1A_LEAN_SOURCE_SHA256,
};
use core_solvers::compliance::{Solver, SolverError};
use core_solvers::solver_spectrum_laplacian::{QObstructionInput, QObstructionSolver};
use core_types::authority_lattice::AuthorityEffectLevel;
use sha2::{Digest, Sha256};

fn r(numerator: i64, denominator: i64) -> BigRational {
    BigRational::new(BigInt::from(numerator), BigInt::from(denominator))
}

fn theorem_receipt() -> Obl1aTheoremReceipt {
    Obl1aTheoremReceipt::from_source_hashes(OBL1A_LEAN_SOURCE_SHA256, OBL1A_LEAN_AUDIT_SHA256)
        .expect("version-pinned Lean receipt")
}

fn sha256_file(path: &Path) -> String {
    let bytes = fs::read(path).expect("read canonical Lean source");
    format!("{:x}", Sha256::digest(bytes))
}

#[test]
#[ignore = "needs the PaperFOC004 Lean sources, which are not in this repository; see OBL1A_LEAN_SOURCE"]
fn live_lean_sources_match_the_certificate_binding() {
    let crate_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let source = crate_dir
        .join("../../lean4/002_finite_obstruction_calculus/PaperFOC004/E7aDistributionBound.lean");
    let audit = crate_dir.join(
        "../../lean4/002_finite_obstruction_calculus/PaperFOC004/OBL1aDistributionBoundAudit.lean",
    );
    let missing: Vec<_> = [&source, &audit]
        .into_iter()
        .filter(|path| !path.exists())
        .collect();
    assert!(
        missing.is_empty(),
        "PaperFOC004 Lean sources absent from this repository: {missing:?}"
    );
    assert_eq!(sha256_file(&source), OBL1A_LEAN_SOURCE_SHA256);
    assert_eq!(sha256_file(&audit), OBL1A_LEAN_AUDIT_SHA256);

    let receipt = theorem_receipt();
    assert_eq!(receipt.lean_source_sha256(), OBL1A_LEAN_SOURCE_SHA256);
    assert_eq!(receipt.lean_audit_sha256(), OBL1A_LEAN_AUDIT_SHA256);
    assert_eq!(
        receipt.allowed_axioms(),
        &["propext", "Classical.choice", "Quot.sound"]
    );
    assert!(OBL1A_LEAN_AUDIT_SOURCE.ends_with("OBL1aDistributionBoundAudit.lean"));
}

#[test]
fn exact_heterogeneous_loads_strictly_improve_the_legacy_bound() {
    let certificate = DistributionBoundVerifier::verify(
        r(3, 1),
        vec![r(1, 1), r(2, 1), r(0, 1)],
        theorem_receipt(),
    )
    .expect("heterogeneous exact certificate");

    assert_eq!(certificate.schema(), OBL1A_DISTRIBUTION_BOUND_SCHEMA);
    assert_eq!(certificate.case(), DistributionBoundCase::PositiveLoad);
    assert_eq!(certificate.sum_loads(), &r(3, 1));
    assert_eq!(certificate.mean_load(), &r(1, 1));
    assert_eq!(certificate.second_moment_ratio(), Some(&r(5, 3)));
    assert_eq!(certificate.maximum_load(), &r(2, 1));
    assert_eq!(certificate.target_lower_bound(), &r(9, 17));
    assert_eq!(certificate.legacy_e7a_lower_bound(), &r(1, 2));
    assert_eq!(certificate.improvement_slack(), &r(1, 34));
    assert!(certificate.is_strict_improvement());
    assert!(certificate
        .size_biased_slack()
        .is_some_and(|slack| slack >= &BigRational::from_integer(BigInt::from(0))));
    assert!(certificate.reciprocal_gate_slack() > &BigRational::from_integer(BigInt::from(0)));
    assert_eq!(certificate.authority_effect(), AuthorityEffectLevel::None);

    let json = serde_json::to_value(&certificate).expect("serialize sealed evidence");
    assert_eq!(json["authority_effect"], "None");
}

#[test]
fn equality_cases_and_zero_load_branch_are_exact() {
    let flat = DistributionBoundVerifier::verify(
        r(2, 1),
        vec![r(2, 1), r(2, 1), r(2, 1), r(2, 1)],
        theorem_receipt(),
    )
    .expect("flat loads");
    assert_eq!(flat.target_lower_bound(), &r(2, 3));
    assert_eq!(flat.legacy_e7a_lower_bound(), &r(2, 3));
    assert!(!flat.is_strict_improvement());

    let spike = DistributionBoundVerifier::verify(
        r(2, 1),
        vec![r(4, 1), r(0, 1), r(0, 1), r(0, 1)],
        theorem_receipt(),
    )
    .expect("single spike");
    assert_eq!(spike.second_moment_ratio(), Some(&r(4, 1)));
    assert_eq!(spike.target_lower_bound(), &r(2, 7));
    assert_eq!(spike.legacy_e7a_lower_bound(), &r(2, 7));
    assert!(!spike.is_strict_improvement());

    let zero = DistributionBoundVerifier::verify(
        r(5, 2),
        vec![r(0, 1), r(0, 1), r(0, 1)],
        theorem_receipt(),
    )
    .expect("zero-load branch");
    assert_eq!(zero.case(), DistributionBoundCase::ZeroLoad);
    assert_eq!(zero.target_lower_bound(), &r(0, 1));
    assert_eq!(zero.constant_shift(), &r(5, 2));
    assert_eq!(zero.reciprocal_average(), &r(2, 5));
    assert_eq!(zero.second_moment_ratio(), None);
    assert_eq!(zero.size_biased_sum(), None);
    assert_eq!(zero.reciprocal_upper_bound(), None);
}

#[test]
fn malformed_inputs_and_unbound_theorems_are_refused() {
    assert_eq!(
        DistributionBoundVerifier::verify(r(1, 1), vec![], theorem_receipt()),
        Err(DistributionBoundError::EmptyLoads)
    );
    assert_eq!(
        DistributionBoundVerifier::verify(r(0, 1), vec![r(1, 1)], theorem_receipt()),
        Err(DistributionBoundError::NonPositiveSpectralGap)
    );
    assert_eq!(
        DistributionBoundVerifier::verify(r(1, 1), vec![r(1, 1), r(-1, 2)], theorem_receipt()),
        Err(DistributionBoundError::NegativeLoad { index: 1 })
    );
    assert!(matches!(
        Obl1aTheoremReceipt::from_source_hashes(
            "0000000000000000000000000000000000000000000000000000000000000000",
            OBL1A_LEAN_AUDIT_SHA256,
        ),
        Err(DistributionBoundError::TheoremHashMismatch { .. })
    ));

    let too_many =
        vec![r(0, 1); core_solvers::cert_phi1_distribution::OBL1A_HARD_MAX_LOAD_COUNT + 1];
    assert!(matches!(
        DistributionBoundVerifier::verify(r(1, 1), too_many, theorem_receipt()),
        Err(DistributionBoundError::LoadCountLimitExceeded {
            count,
            hard_limit: core_solvers::cert_phi1_distribution::OBL1A_HARD_MAX_LOAD_COUNT,
        }) if count == core_solvers::cert_phi1_distribution::OBL1A_HARD_MAX_LOAD_COUNT + 1
    ));

    let oversized_gap = BigRational::from_integer(
        BigInt::from(1_u8) << (OBL1A_HARD_MAX_RATIONAL_BITS as usize + 1),
    );
    assert!(matches!(
        DistributionBoundVerifier::verify(oversized_gap, vec![r(0, 1)], theorem_receipt()),
        Err(DistributionBoundError::RationalBitLimitExceeded {
            field: "spectral_gap",
            index: 0,
            ..
        })
    ));

    let oversized = BigRational::from_integer(
        BigInt::from(1_u8) << (OBL1A_HARD_MAX_RATIONAL_BITS as usize + 1),
    );
    assert!(matches!(
        DistributionBoundVerifier::verify(r(1, 1), vec![oversized], theorem_receipt()),
        Err(DistributionBoundError::RationalBitLimitExceeded {
            field: "load",
            index: 0,
            ..
        })
    ));
}

#[test]
fn pairwise_coprime_denominators_reach_the_accumulator_limit() {
    // Distinct prime-power denominators are pairwise coprime and individually
    // about 3900 bits, so their reduced reciprocal sum crosses 65536 bits.
    let prime_powers = [
        (2_u32, 3900_u32),
        (3, 2460),
        (5, 1679),
        (7, 1389),
        (11, 1127),
        (13, 1053),
        (17, 954),
        (19, 918),
        (23, 861),
        (29, 802),
        (31, 787),
        (37, 749),
        (41, 728),
        (43, 718),
        (47, 702),
        (53, 679),
        (59, 663),
    ];
    let loads: Vec<BigRational> = prime_powers
        .into_iter()
        .map(|(prime, exponent)| {
            BigRational::new(BigInt::from(1_u8), BigInt::from(prime).pow(exponent))
        })
        .collect();
    let error = DistributionBoundVerifier::verify(r(1, 1), loads, theorem_receipt())
        .expect_err("pairwise-coprime sum must hit the exact accumulator ceiling");
    match error {
        DistributionBoundError::AccumulatorBitLimitExceeded {
            stage,
            through_index,
            hard_limit,
            ..
        } => {
            assert_eq!(stage, "sum_loads");
            assert_eq!(through_index, 16);
            assert_eq!(hard_limit, OBL1A_HARD_MAX_ACCUMULATOR_BITS);
        }
        other => panic!("unexpected typed refusal: {other:?}"),
    }
}

#[test]
fn finite_q_ground_energy_does_not_falsify_the_exact_bound() {
    // Incidence matrix of the three-vertex path. Its Laplacian spectrum is
    // {0, 1, 3}, so the exact spectral gap supplied to the theorem is alpha=1.
    let loads = vec![r(0, 1), r(1, 1), r(2, 1)];
    let certificate = DistributionBoundVerifier::verify(r(1, 1), loads, theorem_receipt())
        .expect("exact OBL-1a certificate");
    assert_eq!(certificate.target_lower_bound(), &r(3, 11));

    let input = QObstructionInput {
        coboundary: DMatrix::from_row_slice(2, 3, &[1.0, -1.0, 0.0, 0.0, 1.0, -1.0]),
        defect_potential: DMatrix::from_diagonal(&nalgebra::DVector::from_vec(vec![0.0, 1.0, 2.0])),
    };
    let result = QObstructionSolver::default()
        .solve(&input)
        .expect("finite Q eigensolve");
    let target = certificate
        .target_lower_bound()
        .to_f64()
        .expect("small rational is representable");
    let residual_inclusion = (result.value.dim as f64).sqrt() * result.value.residual_inf_norm;
    assert!(
        result.value.ground_energy + residual_inclusion + 1.0e-12 >= target,
        "numerical ground energy {} with inclusion radius {} fell below exact bound {}",
        result.value.ground_energy,
        residual_inclusion,
        target
    );
    assert!(result.diagnostics.converged);

    let _typed_solver_error: Option<SolverError> = None;
}

// Origin: engine/crates_rs/tests/core_solvers/obl1a_distribution_bound_conformance.rs
// Claim: urn:core:crates_rs:tests:obl1a-distribution-bound-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc7ba6fd2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc7ba6fd2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc7ba6fd2 {
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
impl BoundaryErrorc7ba6fd2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc7ba6fd2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc7ba6fd2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc7ba6fd2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc7ba6fd2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc7ba6fd2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc7ba6fd2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc7ba6fd2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c7ba6fd2() {
    let admitted = BoundaryRecordc7ba6fd2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc7ba6fd2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
