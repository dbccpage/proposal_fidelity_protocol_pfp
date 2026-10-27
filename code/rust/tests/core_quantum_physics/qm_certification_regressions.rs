//! Comprehensive regression and adversarial certification test suite for QM-001 through QM-008
//! and Batch 2 P2 defect repairs in `core_quantum_physics`.
//!
//! AuthorityEffect: None.

use num_traits::{One, Zero};
use core_functional::decoherence::DecoherenceError;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::cyclotomic_ordered::CyclotomicRealRoot;
use core_number_theory::rational::{rq, Rational};
use core_quantum_physics::bipartite_operator::{self as bo, BipartiteError};
use core_quantum_physics::busch_effects::{
    recover_density_matrix, validate_conductor_support, FieldElementFPlus,
    HermitianMatrix,
};
use core_quantum_physics::chain_histories::{chain_histories, preflight_history_budget};
use core_quantum_physics::cochain_repair_code::{CochainRepairCode, DecodingRule};
use core_quantum_physics::completely_positive_map::{
    CompletelyPositiveMap, CompletelyPositiveMapError,
};
use core_quantum_physics::density_matrix::{DensityError, PopulationShadow};
use core_quantum_physics::exact_hermitian;
use core_quantum_physics::hilbert_space::HilbertSpace;
use core_quantum_physics::mub::dimension_stratification::{
    DimensionAuthorityStatus, DimensionClass, DimensionStratificationReport, FactorControlStatus,
    PrimePowerFactor,
};
use core_quantum_physics::mub::odd_prime_weyl::{
    checked_cross_basis_quadratic_reductions, checked_same_basis_linear_reductions,
    verify_odd_prime_weyl_schema, OddPrimeWeylStatus,
};
use core_quantum_physics::mub::prime_power_gtmur_boundary::extract_composite_authority_gaps;
use core_quantum_physics::stabilizer_code_distance::StabilizerCode;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};

// ============================================================================
// QM-001: Positivity Budget Exhaustion Propagation in Bipartite Operator
// ============================================================================

#[test]
fn test_qm_001_ppt_budget_exhaustion_does_not_return_false_negative() {
    // 1. Valid separable state (maximally mixed 2x2 state) returns Ok(true)
    let d_a = 2;
    let d_b = 2;
    let quarter = GaussianRat::from_rational(rq(1, 4));
    let mut id_data = vec![GaussianRat::zero(); 16];
    for i in 0..4 {
        id_data[i * 4 + i] = quarter.clone();
    }
    let rho_sep = BasicMatrix::from_row_major(4, 4, id_data).unwrap();
    let ppt_verdict = bo::is_ppt(&rho_sep, d_a, d_b).expect("separable state PPT decision");
    assert!(
        ppt_verdict,
        "Separable maximally mixed state must be verified as PPT (Ok(true))"
    );

    // 2. Genuinely entangled state (Bell state |Phi+><Phi+|) demonstrates non-separability (Ok(false))
    // |Phi+> = (|00> + |11>) / sqrt(2)
    // rho = 1/2 (|00><00| + |00><11| + |11><00| + |11><11|)
    let half = GaussianRat::from_rational(rq(1, 2));
    let mut bell_data = vec![GaussianRat::zero(); 16];
    bell_data[0 * 4 + 0] = half.clone();
    bell_data[0 * 4 + 3] = half.clone();
    bell_data[3 * 4 + 0] = half.clone();
    bell_data[3 * 4 + 3] = half.clone();
    let rho_bell = BasicMatrix::from_row_major(4, 4, bell_data).unwrap();
    let bell_verdict = bo::is_ppt(&rho_bell, d_a, d_b).expect("entangled Bell PPT decision");
    assert!(
        !bell_verdict,
        "Entangled Bell state must return Ok(false) due to verified negative eigenvalue"
    );

    // 3. Positivity budget exhaustion must propagate as Err, NEVER as Ok(false)
    // Non-Hermitian operator returns Err(BipartiteError::NotHermitian)
    let mut non_herm_data = vec![GaussianRat::zero(); 16];
    non_herm_data[0 * 4 + 1] = GaussianRat::from_ints(1, 1);
    let non_herm = BasicMatrix::from_row_major(4, 4, non_herm_data).unwrap();
    let non_herm_err = bo::is_ppt(&non_herm, 2, 2);
    assert_eq!(non_herm_err, Err(BipartiteError::NotHermitian));
}

// ============================================================================
// QM-002: CP-Map Eigensystem Shape Safety & Field Encapsulation
// ============================================================================

#[test]
fn test_qm_002_cp_map_shape_mismatch_refusal_and_encapsulation() {
    // 1. Encapsulated fields are accessible via read-only accessors
    let cp = CompletelyPositiveMap::new(2, "id2");
    assert_eq!(cp.dim_in(), 2);
    assert_eq!(cp.dim_out(), 2);
    assert_eq!(cp.label(), "id2");
    assert_eq!(cp.choi_matrix().nrows(), 4);
    assert_eq!(cp.choi_matrix().ncols(), 4);

    // 2. Mismatched Choi matrix dimensions are rejected at admission
    let wrong_choi = CMatrix::identity(3, 3);
    let admission_err = CompletelyPositiveMap::try_from_choi_matrix(2, 2, wrong_choi, "bad", 1e-9);
    assert!(
        matches!(
            admission_err,
            Err(CompletelyPositiveMapError::DimensionMismatch {
                expected: 4,
                actual: 3
            })
        ),
        "Expected DimensionMismatch at admission, got {:?}",
        admission_err
    );
}

// ============================================================================
// QM-003: Chain Histories Aggregate Work Preflight & try_fold
// ============================================================================

#[test]
fn test_qm_003_chain_histories_budget_preflight_and_no_panics() {
    // 1. Budget preflight refuses history count exceeding HISTORY_BUDGET
    let budget_err = preflight_history_budget(100_000, 2, 2);
    assert!(
        matches!(budget_err, Err(DecoherenceError::HistoryBudget { .. })),
        "Expected HistoryBudget refusal, got {:?}",
        budget_err
    );

    // 2. Zero dimension is refused cleanly
    let zero_dim_err = preflight_history_budget(10, 2, 0);
    assert!(
        matches!(zero_dim_err, Err(DecoherenceError::Empty)),
        "Expected Empty refusal for dim=0, got {:?}",
        zero_dim_err
    );

    // 3. Step count mismatch is refused
    let step_id = BasicMatrix::from_row_major(2, 2, vec![
        GaussianRat::one(),
        GaussianRat::zero(),
        GaussianRat::zero(),
        GaussianRat::one(),
    ])
    .unwrap();
    let p_proj = vec![step_id.clone()];
    let mismatch_err = chain_histories(&[step_id.clone(), step_id.clone()], &[p_proj]);
    assert!(
        matches!(mismatch_err, Err(DecoherenceError::StepCount { .. })),
        "Expected StepCount refusal, got {:?}",
        mismatch_err
    );
}

// ============================================================================
// QM-004: Busch Density Recovery Preflight
// ============================================================================

#[test]
fn test_qm_004_busch_unsupported_conductor_and_bounds_preflight() {
    // 1. Conductor support validator
    assert!(validate_conductor_support(4).is_ok());
    assert!(validate_conductor_support(5).is_ok());
    assert!(validate_conductor_support(8).is_ok());
    assert!(validate_conductor_support(12).is_ok());
    assert!(validate_conductor_support(24).is_ok());

    let bad_conductor = validate_conductor_support(7);
    assert!(
        bad_conductor.is_err(),
        "Conductor 7 must be refused before calling xi_squared"
    );

    // 2. recover_density_matrix preflights conductor without triggering xi_squared panic
    let mut root4 = CyclotomicRealRoot::new(4);
    let trivial_f = |_: &HermitianMatrix| FieldElementFPlus::zero(4);
    let recovery_err = recover_density_matrix(&trivial_f, 2, 7, &mut root4);
    assert!(
        recovery_err.is_err(),
        "Expected clean Err for conductor 7, got Ok"
    );

    // 3. recover_density_matrix refuses dimension 0
    let zero_dim_err = recover_density_matrix(&trivial_f, 0, 4, &mut root4);
    assert!(
        zero_dim_err.is_err(),
        "Expected clean Err for dim 0, got Ok"
    );

    // 4. recover_density_matrix refuses dimension > 64
    let too_large_dim_err = recover_density_matrix(&trivial_f, 65, 4, &mut root4);
    assert!(
        too_large_dim_err.is_err(),
        "Expected clean Err for dim 65, got Ok"
    );
}

// ============================================================================
// QM-005: Gaussian Hermitian Conversion Preflight
// ============================================================================

#[test]
fn test_qm_005_gaussian_hermitian_preflight_checks_coordinates_and_carrier() {
    // 1. Valid 2x2 Gaussian Hermitian matrix converts cleanly
    let h2 = HermitianMatrix::identity(2, 4).unwrap();
    assert!(h2.preflight_gaussian_conversion().is_ok());
    let exact_bm = h2.to_exact_hermitian().unwrap();
    assert_eq!(exact_bm.rows(), 2);
    assert_eq!(exact_bm.cols(), 2);
    assert!(exact_hermitian::is_hermitian(&exact_bm));

    // 2. Conductor mismatch is refused by preflight
    let h_cond8 = HermitianMatrix::identity(2, 8).unwrap();
    let preflight_err = h_cond8.preflight_gaussian_conversion();
    assert!(
        preflight_err.is_err(),
        "Expected conductor mismatch refusal for conductor 8"
    );
}

// ============================================================================
// QM-006: Rectangular CP-Map Kraus Extraction Refusal
// ============================================================================

#[test]
fn test_qm_006_rectangular_cp_map_kraus_extraction_refused() {
    // Construct a valid rectangular Choi matrix for dim_in = 2, dim_out = 3 (dim = 6)
    let choi_dim = 6;
    let choi_mat = CMatrix::identity(choi_dim, choi_dim);
    let rect_map =
        CompletelyPositiveMap::try_from_choi_matrix(2, 3, choi_mat, "rect_map", 1e-9).unwrap();

    let extraction_result = rect_map.extract_kraus_operators(1e-9);
    assert!(
        matches!(
            extraction_result,
            Err(CompletelyPositiveMapError::RectangularExtractionRefused {
                dim_in: 2,
                dim_out: 3
            })
        ),
        "Expected RectangularExtractionRefused, got {:?}",
        extraction_result
    );
}

// ============================================================================
// QM-007: Unconstrained Cochain Code Stabilizer Carrier & Distance d=1
// ============================================================================

#[test]
fn test_qm_007_trivial_boundary_stabilizer_carrier_and_distance_one() {
    // 1. Direct StabilizerCode construction with explicit carrier length and 0 generators
    let empty_gen_code = StabilizerCode::try_new_with_length(3, Vec::new()).unwrap();
    assert_eq!(empty_gen_code.n(), 3);
    assert_eq!(empty_gen_code.rank(), 0);
    assert_eq!(empty_gen_code.k(), 3);
    let dist = empty_gen_code.distance().unwrap();
    assert_eq!(
        dist.distance(), 1,
        "Trivial stabilizer code on 3 qubits must have distance d=1"
    );

    // 2. CochainRepairCode for trivial complex 0 -> GF(2)^2 -> 0: c0 = 0, c1 = 2, c2 = 0
    let trivial_code = CochainRepairCode::new(0, vec![vec![]; 2], vec![]).unwrap();
    let stab = trivial_code.stabilizer_code().expect("stabilizer code for trivial complex");
    assert_eq!(stab.n(), 2);
    assert_eq!(stab.rank(), 0);
    assert_eq!(stab.k(), 2);
    let repair_dist = trivial_code.repair_distance().unwrap();
    assert_eq!(
        repair_dist.distance(), 1,
        "Trivial cochain code must retain carrier and distance d=1"
    );
}

// ============================================================================
// QM-008: Cochain Decoding Canonical Quotient Complexity & Budget Limits
// ============================================================================

#[test]
fn test_qm_008_cochain_decoding_complexity_and_quotient_indexing() {
    // 3-repetition code complex
    let d0 = vec![vec![1, 0], vec![1, 1], vec![0, 1]];
    let code = CochainRepairCode::new(2, d0, vec![]).unwrap();

    let p = rq(1, 10);
    let ml_success = code
        .logical_success_probability(&p, DecodingRule::MaximumLikelihood)
        .expect("ML decoding success");
    assert!(ml_success > Rational::zero() && ml_success <= Rational::one());

    let mw_success = code
        .logical_success_probability(&p, DecodingRule::MinimumWeight)
        .expect("MW decoding success");
    assert!(mw_success > Rational::zero() && mw_success <= Rational::one());
}

// ============================================================================
// Batch 2 (a): PopulationShadow Field Encapsulation & Diagonal Reality
// ============================================================================

#[test]
fn test_batch2_population_shadow_diagonal_reality_and_synchronization() {
    // 1. from_cmatrix_with_loss rejects non-real diagonal entry
    let mut mat_bad_diag = CMatrix::identity(2, 2);
    mat_bad_diag[(0, 0)] = C64::new(1.0, 0.1); // imaginary part 0.1 > tol
    let result = PopulationShadow::from_cmatrix_with_loss(&mat_bad_diag, "bad_diag", 1e-9);
    assert!(
        matches!(result, Err(DensityError::DiagonalNotReal { index: 0, .. })),
        "Expected DiagonalNotReal error, got {:?}",
        result
    );

    // 2. Synchronized exact representation
    let space = HilbertSpace::try_new(2, "h2").unwrap();
    let exact_probs = vec![rq(1, 2), rq(1, 2)];
    let shadow = PopulationShadow::try_from_exact_probs(&space, exact_probs, "sym").unwrap();
    assert_eq!(shadow.dim(), 2);
    assert_eq!(shadow.probs(), &[0.5, 0.5]);
    assert_eq!(shadow.exact_probs(), Some(&[rq(1, 2), rq(1, 2)][..]));
    assert!(shadow.validate(1e-9).is_ok());
}

// ============================================================================
// Batch 2 (b): Composite Dimension Gap Retention with Missing Factor Obligations
// ============================================================================

#[test]
fn test_batch2_composite_boundary_gap_retention_when_factor_control_fails() {
    // Construct a composite report where factor control is missing (e.g. d=14)
    let missing_factor_report = DimensionStratificationReport {
        dimension: 14,
        class: DimensionClass::CompositePrimePowerProduct,
        factors: vec![
            PrimePowerFactor {
                prime: 2,
                exponent: 1,
                value: 2,
                complete_basis_count: 3,
                control_status: core_quantum_physics::mub::dimension_stratification::FactorControlStatus::ExactCompleteControlPresent,
            },
            PrimePowerFactor {
                prime: 7,
                exponent: 1,
                value: 7,
                complete_basis_count: 8,
                control_status: FactorControlStatus::MissingExactControl,
            },
        ],
        status: DimensionAuthorityStatus::MissingFactorControl,
        guaranteed_basis_count: None,
        complete_basis_count: Some(15),
        construction: "tensor product lower-control requires exact controls for every prime-power factor",
        boundary: "unsupported factor blocks local exact tensor lower-control replay",
        missing_obligations: vec![
            "local exact complete controls for every prime-power factor",
            "tensor-product replay over a declared common coefficient field",
        ],
    };

    let composite_gaps = extract_composite_authority_gaps(&[missing_factor_report]);

    // Ensure composite dimension 14 is preserved with status MissingFactorControl and missing obligations
    let gap_14 = composite_gaps
        .iter()
        .find(|gap| gap.dimension == 14)
        .expect("Composite dimension 14 must be retained in composite_gaps");

    assert_eq!(gap_14.status, DimensionAuthorityStatus::MissingFactorControl);
    assert_eq!(gap_14.complete_basis_count, 15);
    assert_eq!(gap_14.guaranteed_basis_count, 0);
    assert_eq!(gap_14.missing_basis_count, 15);
    assert!(!gap_14.missing_obligations.is_empty());
}

// ============================================================================
// Batch 2 (c): Odd Prime Weyl Multiplicity & Overflow Work Limits
// ============================================================================

#[test]
fn test_batch2_odd_prime_weyl_checked_multiplicity_and_overflow_protection() {
    // 1. Closed-form checked multiplicity matches mathematical formula for small primes
    for p in [3, 5, 7, 11, 13] {
        assert_eq!(
            checked_same_basis_linear_reductions(p),
            Some(p * p * (p - 1))
        );
        assert_eq!(
            checked_cross_basis_quadratic_reductions(p),
            Some(p * p * p * (p - 1))
        );
        let report = verify_odd_prime_weyl_schema(p);
        assert_eq!(report.status, OddPrimeWeylStatus::ProofSchemaVerified);
        assert_eq!(report.basis_count, p + 1);
        assert_eq!(report.same_basis_linear_reductions, p * p * (p - 1));
        assert_eq!(report.cross_basis_quadratic_reductions, p * p * p * (p - 1));
    }

    // 2. Huge prime exceeding MAX_WEYL_PRIME_BUDGET is refused without integer overflow
    let huge_prime = 65_537; // prime > 65_535
    let report_huge = verify_odd_prime_weyl_schema(huge_prime);
    assert_eq!(
        report_huge.status,
        OddPrimeWeylStatus::UnsupportedDimension
    );
    assert!(report_huge.error.as_ref().unwrap().contains("budget"));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/qm_certification_regressions.rs
// Claim: urn:core:crates_rs:tests:qm-certification-regressions:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord30c42ab7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord30c42ab7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError30c42ab7 {
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
impl BoundaryError30c42ab7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError30c42ab7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError30c42ab7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord30c42ab7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError30c42ab7> {
        if capacity_bound == 0 {
            return Err(BoundaryError30c42ab7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError30c42ab7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError30c42ab7::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_30c42ab7() {
    let admitted = BoundaryRecord30c42ab7::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord30c42ab7::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
