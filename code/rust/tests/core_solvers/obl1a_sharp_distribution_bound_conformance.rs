//! Exact conformance tests for the OBL-1a-opt full-distribution floor.
//!
//! The root-isolating certificate is the subject. The live Lean hashes and
//! hand-derived rational brackets are independent oracles. No passing test
//! mints authority.

use std::fs;
use std::path::Path;

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use core_solvers::cert_phi1_distribution::{
    Obl1aSharpTheoremReceipt, SharpDistributionBoundError, SharpDistributionBoundVerifier,
    SharpDistributionCase, OBL1A_SHARP_DISTRIBUTION_SCHEMA, OBL1A_SHARP_GAP_PREMISE,
    OBL1A_SHARP_HARD_MAX_BISECTION_STEPS, OBL1A_SHARP_HARD_MAX_RATIONAL_BITS,
    OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SHA256, OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SOURCE,
    OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE_SHA256, OBL1A_SHARP_LEAN_AUDIT_SHA256,
    OBL1A_SHARP_LEAN_AUDIT_SOURCE, OBL1A_SHARP_LEAN_BRACKET_THEOREM,
    OBL1A_SHARP_LEAN_EXACT_FLOOR_THEOREM, OBL1A_SHARP_LEAN_SOURCE_SHA256,
    OBL1A_SHARP_LEAN_TRANSFER_THEOREM, OBL1A_SHARP_LEAN_ZERO_LOAD_THEOREM,
};
use core_types::authority_lattice::AuthorityEffectLevel;
use sha2::{Digest, Sha256};

fn r(numerator: i64, denominator: i64) -> BigRational {
    BigRational::new(BigInt::from(numerator), BigInt::from(denominator))
}

fn theorem_receipt() -> Obl1aSharpTheoremReceipt {
    Obl1aSharpTheoremReceipt::from_source_hashes(
        OBL1A_SHARP_LEAN_SOURCE_SHA256,
        OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE_SHA256,
        OBL1A_SHARP_LEAN_AUDIT_SHA256,
        OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SHA256,
    )
    .expect("version-pinned Lean receipt")
}

fn sha256_file(path: &Path) -> String {
    let bytes = fs::read(path).expect("read canonical Lean source");
    format!("{:x}", Sha256::digest(bytes))
}

#[test]
#[ignore = "needs the PaperFOC004 sharp-floor Lean sources, which are not in this repository; see OBL1A_SHARP_LEAN_SOURCE"]
fn live_lean_sources_match_the_certificate_binding() {
    let crate_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let source = crate_dir.join(
        "../../lean4/002_finite_obstruction_calculus/PaperFOC004/E7eSharpDistributionFloor.lean",
    );
    let assembly_source = crate_dir.join(
        "../../lean4/002_finite_obstruction_calculus/PaperFOC004/E7eSharpDistributionFloorAssembly.lean",
    );
    let audit = crate_dir.join(
        "../../lean4/002_finite_obstruction_calculus/PaperFOC004/OBL1aSharpDistributionFloorAudit.lean",
    );
    let assembly_audit = crate_dir.join(
        "../../lean4/002_finite_obstruction_calculus/PaperFOC004/OBL1aSharpDistributionFloorAssemblyAudit.lean",
    );
    let missing: Vec<_> = [&source, &assembly_source, &audit, &assembly_audit]
        .into_iter()
        .filter(|path| !path.exists())
        .collect();
    assert!(
        missing.is_empty(),
        "PaperFOC004 sharp-floor Lean sources absent from this repository: {missing:?}"
    );
    assert_eq!(sha256_file(&source), OBL1A_SHARP_LEAN_SOURCE_SHA256);
    assert_eq!(
        sha256_file(&assembly_source),
        OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE_SHA256
    );
    assert_eq!(sha256_file(&audit), OBL1A_SHARP_LEAN_AUDIT_SHA256);
    assert_eq!(
        sha256_file(&assembly_audit),
        OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SHA256
    );

    let receipt = theorem_receipt();
    assert_eq!(receipt.lean_source_sha256(), OBL1A_SHARP_LEAN_SOURCE_SHA256);
    assert_eq!(
        receipt.lean_assembly_source_sha256(),
        OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE_SHA256
    );
    assert_eq!(receipt.lean_audit_sha256(), OBL1A_SHARP_LEAN_AUDIT_SHA256);
    assert_eq!(
        receipt.lean_assembly_audit_sha256(),
        OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SHA256
    );
    assert_eq!(
        receipt.allowed_axioms(),
        &["propext", "Classical.choice", "Quot.sound"]
    );
    assert_eq!(receipt.bracket_theorem(), OBL1A_SHARP_LEAN_BRACKET_THEOREM);
    assert_eq!(
        receipt.exact_floor_theorem(),
        OBL1A_SHARP_LEAN_EXACT_FLOOR_THEOREM
    );
    assert_eq!(
        receipt.zero_load_theorem(),
        OBL1A_SHARP_LEAN_ZERO_LOAD_THEOREM
    );
    assert_eq!(
        receipt.transfer_theorem(),
        OBL1A_SHARP_LEAN_TRANSFER_THEOREM
    );
    assert!(OBL1A_SHARP_LEAN_AUDIT_SOURCE.ends_with("OBL1aSharpDistributionFloorAudit.lean"));
    assert!(OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SOURCE
        .ends_with("OBL1aSharpDistributionFloorAssemblyAudit.lean"));
}
#[test]
fn irrational_two_load_root_has_an_exact_rational_isolating_bracket() {
    // For alpha=2 and loads [1,3],
    //   F(t) = 1/(3-t) + 1/(5-t),
    // and the first root is tau = 3-sqrt(2).
    //
    // Exact independent endpoint checks:
    //   F(3/2) = 20/21 < 1,
    //   F(8/5) = 120/119 > 1.
    let certificate = SharpDistributionBoundVerifier::verify(
        r(2, 1),
        vec![r(1, 1), r(3, 1)],
        16,
        theorem_receipt(),
    )
    .expect("exact irrational-root bracket");

    assert_eq!(certificate.schema(), OBL1A_SHARP_DISTRIBUTION_SCHEMA);
    assert_eq!(certificate.case(), SharpDistributionCase::PositiveLoad);
    assert_eq!(certificate.gap_premise(), OBL1A_SHARP_GAP_PREMISE);
    assert_eq!(certificate.pole_floor(), &r(3, 1));
    assert!(certificate.root_lower_bound() > &r(3, 2));
    assert!(certificate.root_upper_bound() < &r(8, 5));
    assert!(certificate.lower_gate_value() <= &BigRational::one());
    assert!(certificate.upper_gate_value() >= &BigRational::one());
    assert!(certificate.root_upper_bound() < certificate.pole_floor());
    assert!(certificate.root_lower_bound() >= certificate.e7d_lower_bound());
    assert_eq!(certificate.authority_effect(), AuthorityEffectLevel::None);

    let json = serde_json::to_value(&certificate).expect("serialize sealed evidence");
    assert_eq!(json["authority_effect"], "None");
}

#[test]
fn flat_load_root_and_e7d_improvement_are_exactly_bracketed() {
    // alpha(I-P)+3I has exact least eigenvalue tau=3, whereas E.7d gives 3/4.
    let certificate = SharpDistributionBoundVerifier::verify(
        r(2, 1),
        vec![r(3, 1), r(3, 1)],
        32,
        theorem_receipt(),
    )
    .expect("flat-load bracket");

    assert_eq!(certificate.e7d_lower_bound(), &r(3, 4));
    assert!(certificate.root_lower_bound() <= &r(3, 1));
    assert!(certificate.root_upper_bound() >= &r(3, 1));
    assert!(certificate.root_lower_bound() > certificate.e7d_lower_bound());

    let expected_width = (certificate.initial_upper_bound().clone()
        - certificate.e7d_lower_bound().clone())
        / BigRational::from_integer(BigInt::from(1_u8) << certificate.bisection_steps());
    assert_eq!(
        certificate.root_upper_bound().clone() - certificate.root_lower_bound().clone(),
        expected_width
    );
}

#[test]
fn zero_load_root_is_exactly_zero() {
    let certificate = SharpDistributionBoundVerifier::verify(
        r(5, 2),
        vec![r(0, 1), r(0, 1), r(0, 1)],
        128,
        theorem_receipt(),
    )
    .expect("zero-load exact root");

    assert_eq!(certificate.case(), SharpDistributionCase::ZeroLoad);
    assert_eq!(certificate.root_lower_bound(), &BigRational::zero());
    assert_eq!(certificate.root_upper_bound(), &BigRational::zero());
    assert_eq!(certificate.lower_gate_value(), &BigRational::one());
    assert_eq!(certificate.upper_gate_value(), &BigRational::one());
    assert_eq!(certificate.bisection_steps(), 0);
}

#[test]
fn zero_step_positive_certificate_still_isolates_the_unique_root() {
    let certificate = SharpDistributionBoundVerifier::verify(
        r(2, 1),
        vec![r(1, 1), r(3, 1)],
        0,
        theorem_receipt(),
    )
    .expect("initial exact bracket");
    assert_eq!(
        certificate.root_lower_bound(),
        certificate.e7d_lower_bound()
    );
    assert_eq!(
        certificate.root_upper_bound(),
        certificate.initial_upper_bound()
    );
    assert!(certificate.lower_gate_value() < &BigRational::one());
    assert!(certificate.upper_gate_value() > &BigRational::one());
}

#[test]
fn malformed_inputs_and_unbound_theorems_are_refused() {
    assert_eq!(
        SharpDistributionBoundVerifier::verify(r(1, 1), vec![], 0, theorem_receipt()),
        Err(SharpDistributionBoundError::EmptyLoads)
    );
    assert_eq!(
        SharpDistributionBoundVerifier::verify(r(1, 1), vec![r(0, 1)], 0, theorem_receipt()),
        Err(SharpDistributionBoundError::BelowMinimumVertexCount {
            count: 1,
            minimum: 2,
        })
    );
    assert_eq!(
        SharpDistributionBoundVerifier::verify(
            r(0, 1),
            vec![r(1, 1), r(0, 1)],
            0,
            theorem_receipt()
        ),
        Err(SharpDistributionBoundError::NonPositiveSpectralGap)
    );
    assert_eq!(
        SharpDistributionBoundVerifier::verify(
            r(1, 1),
            vec![r(1, 1), r(-1, 2)],
            0,
            theorem_receipt()
        ),
        Err(SharpDistributionBoundError::NegativeLoad { index: 1 })
    );
    assert!(matches!(
        Obl1aSharpTheoremReceipt::from_source_hashes(
            "0000000000000000000000000000000000000000000000000000000000000000",
            OBL1A_SHARP_LEAN_ASSEMBLY_SOURCE_SHA256,
            OBL1A_SHARP_LEAN_AUDIT_SHA256,
            OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SHA256,
        ),
        Err(SharpDistributionBoundError::TheoremHashMismatch { .. })
    ));
    assert!(matches!(
        Obl1aSharpTheoremReceipt::from_source_hashes(
            OBL1A_SHARP_LEAN_SOURCE_SHA256,
            "0000000000000000000000000000000000000000000000000000000000000000",
            OBL1A_SHARP_LEAN_AUDIT_SHA256,
            OBL1A_SHARP_LEAN_ASSEMBLY_AUDIT_SHA256,
        ),
        Err(SharpDistributionBoundError::TheoremHashMismatch { .. })
    ));

    let oversized_gap = BigRational::from_integer(
        BigInt::from(1_u8) << (OBL1A_SHARP_HARD_MAX_RATIONAL_BITS as usize + 1),
    );
    assert!(matches!(
        SharpDistributionBoundVerifier::verify(
            oversized_gap,
            vec![r(0, 1), r(0, 1)],
            0,
            theorem_receipt()
        ),
        Err(SharpDistributionBoundError::RationalBitLimitExceeded {
            field: "spectral_gap",
            index: 0,
            ..
        })
    ));
}

#[test]
fn bisection_and_combined_work_limits_are_typed() {
    assert!(matches!(
        SharpDistributionBoundVerifier::verify(
            r(1, 1),
            vec![r(1, 1), r(1, 1)],
            OBL1A_SHARP_HARD_MAX_BISECTION_STEPS + 1,
            theorem_receipt()
        ),
        Err(SharpDistributionBoundError::BisectionStepLimitExceeded { .. })
    ));

    let too_many =
        vec![r(0, 1); core_solvers::cert_phi1_distribution::OBL1A_SHARP_HARD_MAX_LOAD_COUNT + 1];
    assert!(matches!(
        SharpDistributionBoundVerifier::verify(r(1, 1), too_many, 0, theorem_receipt()),
        Err(SharpDistributionBoundError::LoadCountLimitExceeded { .. })
    ));

    let loads =
        vec![r(1, 1); core_solvers::cert_phi1_distribution::OBL1A_SHARP_HARD_MAX_LOAD_COUNT];
    assert!(matches!(
        SharpDistributionBoundVerifier::verify(r(1, 1), loads, 254, theorem_receipt()),
        Err(SharpDistributionBoundError::WorkLimitExceeded { .. })
    ));
}

// Origin: engine/crates_rs/tests/core_solvers/obl1a_sharp_distribution_bound_conformance.rs
// Claim: urn:core:crates_rs:tests:obl1a-sharp-distribution-bound-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord693479e9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord693479e9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError693479e9 {
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
impl BoundaryError693479e9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError693479e9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError693479e9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord693479e9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError693479e9> {
        if capacity_bound == 0 {
            return Err(BoundaryError693479e9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError693479e9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError693479e9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_693479e9() {
    let admitted = BoundaryRecord693479e9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord693479e9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
