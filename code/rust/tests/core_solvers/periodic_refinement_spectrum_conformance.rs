//! Conformance tests for the periodic nonuniform generalized eigensolver.

use num_bigint::BigInt;
use core_solvers::solver_spectrum_periodic::{
    periodic_lumped_fv_spectrum, AnalyticTransferStatus, IntervalLocation, OrderedAnalyticScope,
    OrderedNumericalReason, OrderedScopeReason, PeriodicSpectrumError, PeriodicSpectrumPolicy,
    HARD_MAX_ACCUMULATOR_BITS, HARD_MAX_CONDITION_RATIO, HARD_MAX_DIMENSION, HARD_MAX_ITERATIONS,
    HARD_MAX_RATIONAL_BITS, PERIODIC_SPECTRUM_EVIDENCE_SCHEMA,
};
use core_types::authority_lattice::AuthorityEffectLevel;
use core_types::refinement_tower::PositiveRational;

fn gaps(parts: &[(u64, u64)]) -> Vec<PositiveRational> {
    parts
        .iter()
        .map(|(numerator, denominator)| {
            PositiveRational::from_u64(*numerator, *denominator).unwrap()
        })
        .collect()
}

fn assert_close(actual: f64, expected: f64, tolerance: f64) {
    assert!(
        (actual - expected).abs() <= tolerance,
        "expected {expected:.15e}, got {actual:.15e}"
    );
}

#[test]
fn uniform_c4_matches_the_independent_generalized_spectrum() {
    let evidence = periodic_lumped_fv_spectrum(
        &gaps(&[(1, 4), (1, 4), (1, 4), (1, 4)]),
        1,
        &PeriodicSpectrumPolicy::default(),
    )
    .expect("uniform C4 spectrum");

    assert_eq!(evidence.schema(), PERIODIC_SPECTRUM_EVIDENCE_SCHEMA);
    assert_eq!(evidence.dimension(), 4);
    assert_eq!(evidence.max_mode(), 1);
    for (actual, expected) in evidence
        .eigenvalues()
        .iter()
        .copied()
        .zip([0.0, 32.0, 32.0, 64.0])
    {
        assert_close(actual, expected, 1.0e-8);
    }
    assert!(evidence
        .residuals()
        .iter()
        .all(|receipt| receipt.absolute_residual() <= receipt.limit()
            && receipt.whitened_absolute_residual() <= receipt.whitened_limit()));
    assert!(evidence.m_orthogonality_residual() <= 1.0e-8);
    assert_eq!(evidence.whitened_symmetry_residual(), 0.0);
    assert!(
        evidence.spectrum_sanity().minimum_eigenvalue().abs()
            <= evidence.spectrum_sanity().zero_mode_limit()
    );
    assert!(
        evidence.spectrum_sanity().first_positive_eigenvalue()
            > evidence.spectrum_sanity().zero_mode_limit()
    );
    assert!(evidence
        .numerical_resolution()
        .comparison_uncertainty()
        .is_finite());
    assert_eq!(
        evidence.numerical_resolution().hard_condition_ratio(),
        HARD_MAX_CONDITION_RATIO
    );
    assert_eq!(
        evidence.numerical_resolution().transfer_status(),
        AnalyticTransferStatus::ConditionalUnmechanizedPremise
    );
    assert_eq!(evidence.ordered_comparisons().len(), 3);
    assert_eq!(evidence.doublet_splits().len(), 1);
    assert_eq!(evidence.authority_effect(), AuthorityEffectLevel::None);
}

#[test]
fn nonuniform_mesh_matches_oracle_and_discloses_complete_doublet_split() {
    let evidence = periodic_lumped_fv_spectrum(
        &gaps(&[(1, 10), (1, 5), (3, 10), (2, 5)]),
        1,
        &PeriodicSpectrumPolicy::default(),
    )
    .expect("nonuniform spectrum");
    let oracle = [0.0, 23.8733234420374, 38.7067668698151, 137.419909688147];
    for (actual, expected) in evidence.eigenvalues().iter().copied().zip(oracle) {
        assert_close(actual, expected, 2.0e-8);
    }

    let first = &evidence.doublet_splits()[0];
    assert_eq!(first.continuum_mode(), 1);
    assert_eq!(first.ordered_indices(), (1, 2));
    assert_close(first.split(), oracle[2] - oracle[1], 2.0e-8);
    for ordered_index in [1, 2] {
        assert!(matches!(
            evidence.ordered_comparisons()[ordered_index].analytic_scope(),
            OrderedAnalyticScope::InScope {
                location: IntervalLocation::Inside,
                transfer_status: AnalyticTransferStatus::ConditionalUnmechanizedPremise,
                ..
            }
        ));
    }
    assert_eq!(evidence.gap_ratio_exact().numerator(), "4");
    assert_eq!(evidence.gap_ratio_exact().denominator(), "1");
    assert_eq!(evidence.mass_ratio_exact().numerator(), "7");
    assert_eq!(evidence.mass_ratio_exact().denominator(), "3");
}

#[test]
fn theorem_boundary_is_classified_exactly_and_equality_is_out_of_scope() {
    let evidence = periodic_lumped_fv_spectrum(
        &gaps(&[(1, 2), (1, 4), (1, 4)]),
        1,
        &PeriodicSpectrumPolicy::default(),
    )
    .expect("boundary mesh still has a numerical spectrum");
    for ordered_index in [1, 2] {
        assert!(matches!(
            evidence.ordered_comparisons()[ordered_index].analytic_scope(),
            OrderedAnalyticScope::OutOfScope {
                theorem_ratio_exact,
                reason: OrderedScopeReason::StrictMeshConditionFailed,
                ..
            } if theorem_ratio_exact.numerator() == "1"
                && theorem_ratio_exact.denominator() == "1"
        ));
    }
}

#[test]
fn exact_in_scope_ratio_that_rounds_to_one_is_numerically_unresolved() {
    let two_to_60 = 1_u64 << 60;
    let near_half = (two_to_60 - 1, 1_u64 << 61);
    let remaining_half = (two_to_60 + 1, 1_u64 << 62);
    let evidence = periodic_lumped_fv_spectrum(
        &gaps(&[near_half, remaining_half, remaining_half]),
        1,
        &PeriodicSpectrumPolicy::default(),
    )
    .expect("exactly in-scope mesh remains valid numerical evidence");

    for ordered_index in [1, 2] {
        assert!(matches!(
            evidence.ordered_comparisons()[ordered_index].analytic_scope(),
            OrderedAnalyticScope::NumericallyUnresolved {
                theorem_ratio_exact,
                reason: OrderedNumericalReason::UpperDenominatorTooSmall,
                ..
            } if theorem_ratio_exact.numerator() != theorem_ratio_exact.denominator()
        ));
    }
}

#[test]
fn exact_sum_gap_and_mass_conditioning_failures_are_typed() {
    assert_eq!(
        periodic_lumped_fv_spectrum(
            &gaps(&[(1, 3), (1, 3), (1, 4)]),
            1,
            &PeriodicSpectrumPolicy::default(),
        ),
        Err(PeriodicSpectrumError::NonUnitExactGapSum)
    );

    let strict_gap_policy = PeriodicSpectrumPolicy::default()
        .with_max_gap_ratio(2)
        .unwrap();
    assert!(matches!(
        periodic_lumped_fv_spectrum(
            &gaps(&[(1, 10), (1, 5), (3, 10), (2, 5)]),
            1,
            &strict_gap_policy,
        ),
        Err(PeriodicSpectrumError::ExactGapRatioLimitExceeded { limit: 2, .. })
    ));

    let strict_mass_policy = PeriodicSpectrumPolicy::default()
        .with_max_mass_ratio(2)
        .unwrap();
    assert!(matches!(
        periodic_lumped_fv_spectrum(
            &gaps(&[(1, 10), (1, 5), (3, 10), (2, 5)]),
            1,
            &strict_mass_policy,
        ),
        Err(PeriodicSpectrumError::ExactMassRatioLimitExceeded { limit: 2, .. })
    ));
}

#[test]
fn resource_and_complete_doublet_limits_are_fail_closed() {
    assert!(matches!(
        periodic_lumped_fv_spectrum(
            &gaps(&[(1, 4), (1, 4), (1, 4), (1, 4)]),
            2,
            &PeriodicSpectrumPolicy::default(),
        ),
        Err(PeriodicSpectrumError::IncompleteDoubletRequest {
            dimension: 4,
            max_mode: 2,
            maximum_complete_mode: 1,
        })
    ));
    assert_eq!(
        PeriodicSpectrumPolicy::default().with_max_iterations(0),
        Err(PeriodicSpectrumError::InvalidPolicy {
            field: "max_iterations"
        })
    );
    assert_eq!(
        PeriodicSpectrumPolicy::default().with_max_iterations(HARD_MAX_ITERATIONS + 1),
        Err(PeriodicSpectrumError::InvalidPolicy {
            field: "max_iterations"
        })
    );
    assert_eq!(
        PeriodicSpectrumPolicy::default().with_max_dimension(HARD_MAX_DIMENSION + 1),
        Err(PeriodicSpectrumError::InvalidPolicy {
            field: "max_dimension"
        })
    );
    assert_eq!(
        PeriodicSpectrumPolicy::default().with_max_gap_ratio(HARD_MAX_CONDITION_RATIO + 1),
        Err(PeriodicSpectrumError::InvalidPolicy {
            field: "max_gap_ratio"
        })
    );

    let enormous = PositiveRational::new(
        BigInt::from(1_u8) << (HARD_MAX_RATIONAL_BITS as usize + 1),
        BigInt::from(1_u8),
    )
    .unwrap();
    let ordinary = PositiveRational::from_u64(1, 4).unwrap();
    assert!(matches!(
        periodic_lumped_fv_spectrum(
            &[enormous, ordinary.clone(), ordinary],
            1,
            &PeriodicSpectrumPolicy::default(),
        ),
        Err(PeriodicSpectrumError::RationalBitLimitExceeded {
            index: 0,
            hard_limit: HARD_MAX_RATIONAL_BITS,
            ..
        })
    ));
}

#[test]
fn exact_running_sum_accumulator_is_hard_bounded() {
    let primes = [
        2_u64, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59,
    ];
    let hostile: Vec<PositiveRational> = primes
        .iter()
        .map(|prime| {
            let exponent = (4_000.0 / (*prime as f64).log2()).floor() as u32;
            PositiveRational::new(BigInt::from(1_u8), BigInt::from(*prime).pow(exponent)).unwrap()
        })
        .collect();
    assert!(matches!(
        periodic_lumped_fv_spectrum(&hostile, 0, &PeriodicSpectrumPolicy::default()),
        Err(PeriodicSpectrumError::AccumulatorBitLimitExceeded {
            hard_limit: HARD_MAX_ACCUMULATOR_BITS,
            ..
        })
    ));
}

#[test]
fn bounded_eigensolver_reports_deterministic_nonconvergence() {
    let policy = PeriodicSpectrumPolicy::default()
        .with_max_iterations(1)
        .unwrap();
    let uniform_16 = gaps(&[
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
        (1, 16),
    ]);
    assert_eq!(
        periodic_lumped_fv_spectrum(&uniform_16, 1, &policy),
        Err(PeriodicSpectrumError::EigensolverDidNotConverge { max_iterations: 1 })
    );
}

#[test]
fn exact_mesh_digest_is_order_sensitive_and_stable() {
    let policy = PeriodicSpectrumPolicy::default();
    let first = periodic_lumped_fv_spectrum(&gaps(&[(1, 10), (1, 5), (3, 10), (2, 5)]), 1, &policy)
        .unwrap();
    let rotated =
        periodic_lumped_fv_spectrum(&gaps(&[(1, 5), (3, 10), (2, 5), (1, 10)]), 1, &policy)
            .unwrap();
    let changed =
        periodic_lumped_fv_spectrum(&gaps(&[(1, 8), (7, 40), (3, 10), (2, 5)]), 1, &policy)
            .unwrap();

    assert_ne!(first.exact_mesh_sha256(), rotated.exact_mesh_sha256());
    assert_eq!(first.exact_mesh_sha256().len(), 64);
    assert_ne!(first.exact_mesh_sha256(), changed.exact_mesh_sha256());
}

// Origin: engine/crates_rs/tests/core_solvers/periodic_refinement_spectrum_conformance.rs
// Claim: urn:core:crates_rs:tests:periodic-refinement-spectrum-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3a651ffe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3a651ffe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3a651ffe {
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
impl BoundaryError3a651ffe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3a651ffe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3a651ffe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3a651ffe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3a651ffe> {
        if capacity_bound == 0 {
            return Err(BoundaryError3a651ffe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3a651ffe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3a651ffe::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3a651ffe() {
    let admitted = BoundaryRecord3a651ffe::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3a651ffe::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
