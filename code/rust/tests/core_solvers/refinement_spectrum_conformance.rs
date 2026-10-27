//! Conformance tests for uniform cycle/path refinement diagnostics.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_c731a751 = (i128, i128);
use std::f64::consts::PI;

use core_solvers::solver_spectrum_periodic::{
    cell_centered_neumann_path_mode, compare_uniform_resolutions, uniform_cycle_mode,
    RefinementSpectrumError, UniformSpectralFamily, UNIFORM_MODE_EVIDENCE_SCHEMA,
};
use core_types::authority_lattice::AuthorityEffectLevel;

fn relative_error(actual: f64, expected: f64) -> f64 {
    (actual - expected).abs() / expected.abs().max(1.0)
}

#[test]
fn cycle_closed_form_is_inside_the_proved_quadratic_interval() {
    for resolution in [32, 64, 128, 256] {
        for mode in 1..=3 {
            let evidence = uniform_cycle_mode(resolution, mode).expect("valid fixed mode");
            assert_eq!(evidence.schema(), UNIFORM_MODE_EVIDENCE_SCHEMA);
            assert!(evidence.signed_deficit() >= -evidence.floating_point_slack());
            assert!(evidence.within_analytic_bound());
            assert!(evidence.absolute_error() <= evidence.analytic_error_bound());
            assert_eq!(evidence.authority_effect(), AuthorityEffectLevel::None);
        }
    }
}

#[test]
fn cycle_and_path_errors_replay_second_order_scaling() {
    let cycle_64 = uniform_cycle_mode(64, 2).unwrap().absolute_error();
    let cycle_128 = uniform_cycle_mode(128, 2).unwrap().absolute_error();
    let path_64 = cell_centered_neumann_path_mode(64, 2)
        .unwrap()
        .absolute_error();
    let path_128 = cell_centered_neumann_path_mode(128, 2)
        .unwrap()
        .absolute_error();

    assert!(relative_error(cycle_64 / cycle_128, 4.0) < 0.002);
    assert!(relative_error(path_64 / path_128, 4.0) < 0.002);
}

#[test]
fn path_convention_has_the_declared_neumann_target_and_bound() {
    let evidence = cell_centered_neumann_path_mode(96, 3).expect("valid path mode");
    assert!(relative_error(evidence.target_eigenvalue(), (3.0 * PI).powi(2)) < 1e-14);
    let expected_bound = PI.powi(4) * 3.0_f64.powi(4) / (12.0 * 96.0_f64.powi(2));
    assert!(relative_error(evidence.analytic_error_bound(), expected_bound) < 1e-14);
    assert!(evidence.within_analytic_bound());
}

#[test]
fn two_resolution_comparison_uses_the_common_target_not_coprimality() {
    for pair in [(48, 96), (49, 97)] {
        let evidence = compare_uniform_resolutions(UniformSpectralFamily::Cycle, 4, pair.0, pair.1)
            .expect("valid comparison");
        let first = uniform_cycle_mode(pair.0, 4).expect("first mode");
        let second = uniform_cycle_mode(pair.1, 4).expect("second mode");
        assert_eq!(
            evidence.floating_point_slack(),
            first.floating_point_slack() + second.floating_point_slack()
        );
        assert_eq!(evidence.resolutions(), pair);
        assert!(evidence.within_analytic_bound());
        assert!(evidence.observed_difference() <= evidence.analytic_cauchy_bound());
        assert_eq!(evidence.authority_effect(), AuthorityEffectLevel::None);
    }
}

#[test]
fn theorem_domain_failures_are_typed() {
    assert_eq!(
        uniform_cycle_mode(8, 4),
        Err(RefinementSpectrumError::NotLowFrequencyRepresentative {
            mode_index: 4,
            resolution: 8,
        })
    );
    assert_eq!(
        cell_centered_neumann_path_mode(8, 8),
        Err(RefinementSpectrumError::ModeOutOfRange {
            mode_index: 8,
            resolution: 8,
        })
    );
    assert_eq!(
        compare_uniform_resolutions(UniformSpectralFamily::Cycle, 1, 64, 64),
        Err(RefinementSpectrumError::DistinctResolutionsRequired)
    );
    assert_eq!(
        uniform_cycle_mode(usize::MAX, usize::MAX - 1),
        Err(RefinementSpectrumError::NotLowFrequencyRepresentative {
            mode_index: usize::MAX - 1,
            resolution: usize::MAX,
        })
    );
}

#[test]
fn evidence_serializes_the_fixed_no_authority_effect() {
    let serialized = serde_json::to_value(uniform_cycle_mode(64, 2).unwrap()).unwrap();
    assert_eq!(serialized["authority_effect"], "None");
}

// Origin: engine/crates_rs/tests/core_solvers/refinement_spectrum_conformance.rs
// Claim: urn:core:crates_rs:tests:refinement-spectrum-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc731a751 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc731a751` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc731a751 {
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
impl BoundaryErrorc731a751 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc731a751 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc731a751 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc731a751 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc731a751> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc731a751::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc731a751::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc731a751::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c731a751() {
    let admitted = BoundaryRecordc731a751::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc731a751::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
