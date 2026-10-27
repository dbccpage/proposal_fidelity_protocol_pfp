//! Numerical falsifier for periodic nonuniform refinement spectra.
//!
//! --- Math Contract:
//! - Purpose: assemble and solve the periodic lumped finite-volume generalized
//!   eigenproblem used by One Regime D2.
//! - Inputs: positive exact rational gaps summing exactly to one, a requested
//!   complete-doublet cutoff, and a bounded numerical policy.
//! - Outputs: ordered eigenvalues, two independent residual receipts,
//!   orthogonality evidence, ordered continuum-mode comparisons, and complete
//!   doublet splitting diagnostics.
//! - Invariants: `K` is assembled edgewise, `M` is positive diagonal,
//!   diagonalization uses the symmetric whitening `M^{-1/2} K M^{-1/2}`,
//!   theorem scope is classified with exact rationals, and every returned
//!   eigenpair passes generalized and whitened residual gates.
//! - Failure: exact mesh, resource, finite conversion, conditioning,
//!   eigensolver, residual, orthogonality, PSD, and zero-mode failures are
//!   typed. A comparison outside a conditional analytic interval is evidence,
//!   not a solver failure.
//! - Numerical status: `f64` falsification evidence only. This module cannot
//!   construct a theorem-bound convergence certificate.
//! - Authority: every output has `AuthorityEffectLevel::None`.

use std::f64::consts::PI;

use nalgebra::{DMatrix, DVector, SymmetricEigen};
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::ToPrimitive;
use core_types::authority_lattice::AuthorityEffectLevel;
use core_types::refinement_tower::PositiveRational;
use serde::Serialize;
use sha2::{Digest, Sha256};
use thiserror::Error;

pub const PERIODIC_SPECTRUM_EVIDENCE_SCHEMA: &str =
    "core.periodic-refinement-spectrum-evidence.v2";
pub const HARD_MAX_DIMENSION: usize = 512;
pub const HARD_MAX_ITERATIONS: usize = 1_000_000;
pub const HARD_MAX_RATIONAL_BITS: u64 = 4_096;
pub const HARD_MAX_ACCUMULATOR_BITS: u64 = 65_536;
pub const HARD_MAX_CONDITION_RATIO: u64 = 10_000;

/// Bounded numerical policy for the dense periodic generalized eigensolver.
///
/// Gap and mass conditioning ceilings are integers so their gates can be
/// evaluated exactly before any conversion to `f64`.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct PeriodicSpectrumPolicy {
    max_dimension: usize,
    max_gap_ratio: u64,
    max_mass_ratio: u64,
    eigensolver_epsilon: f64,
    max_iterations: usize,
    residual_absolute_tolerance: f64,
    residual_relative_tolerance: f64,
    orthogonality_tolerance: f64,
    negative_eigenvalue_tolerance: f64,
    zero_mode_tolerance: f64,
    minimum_upper_denominator: f64,
}

impl Default for PeriodicSpectrumPolicy {
    fn default() -> Self {
        Self {
            max_dimension: HARD_MAX_DIMENSION,
            max_gap_ratio: HARD_MAX_CONDITION_RATIO,
            max_mass_ratio: HARD_MAX_CONDITION_RATIO,
            eigensolver_epsilon: 1.0e-12,
            max_iterations: 100_000,
            residual_absolute_tolerance: 1.0e-10,
            residual_relative_tolerance: 1.0e-9,
            orthogonality_tolerance: 1.0e-8,
            negative_eigenvalue_tolerance: 1.0e-8,
            zero_mode_tolerance: 1.0e-8,
            minimum_upper_denominator: 1.0e-10,
        }
    }
}

impl PeriodicSpectrumPolicy {
    pub fn with_max_gap_ratio(mut self, value: u64) -> Result<Self, PeriodicSpectrumError> {
        if value == 0 || value > HARD_MAX_CONDITION_RATIO {
            return Err(PeriodicSpectrumError::InvalidPolicy {
                field: "max_gap_ratio",
            });
        }
        self.max_gap_ratio = value;
        Ok(self)
    }

    pub fn with_max_mass_ratio(mut self, value: u64) -> Result<Self, PeriodicSpectrumError> {
        if value == 0 || value > HARD_MAX_CONDITION_RATIO {
            return Err(PeriodicSpectrumError::InvalidPolicy {
                field: "max_mass_ratio",
            });
        }
        self.max_mass_ratio = value;
        Ok(self)
    }

    pub fn with_max_dimension(mut self, value: usize) -> Result<Self, PeriodicSpectrumError> {
        if !(3..=HARD_MAX_DIMENSION).contains(&value) {
            return Err(PeriodicSpectrumError::InvalidPolicy {
                field: "max_dimension",
            });
        }
        self.max_dimension = value;
        Ok(self)
    }

    pub fn with_max_iterations(mut self, value: usize) -> Result<Self, PeriodicSpectrumError> {
        if value == 0 || value > HARD_MAX_ITERATIONS {
            return Err(PeriodicSpectrumError::InvalidPolicy {
                field: "max_iterations",
            });
        }
        self.max_iterations = value;
        Ok(self)
    }

    pub fn max_dimension(&self) -> usize {
        self.max_dimension
    }

    pub fn max_gap_ratio(&self) -> u64 {
        self.max_gap_ratio
    }

    pub fn max_mass_ratio(&self) -> u64 {
        self.max_mass_ratio
    }

    pub fn max_iterations(&self) -> usize {
        self.max_iterations
    }
}

/// Canonical decimal representation of an exact nonnegative ratio.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ExactRatioReceipt {
    numerator: String,
    denominator: String,
}

impl ExactRatioReceipt {
    pub fn numerator(&self) -> &str {
        &self.numerator
    }

    pub fn denominator(&self) -> &str {
        &self.denominator
    }
}

/// Residual receipt for one ordered generalized eigenpair.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct GeneralizedModeResidual {
    ordered_index: usize,
    generalized_absolute_residual: f64,
    generalized_scale: f64,
    generalized_limit: f64,
    whitened_absolute_residual: f64,
    whitened_scale: f64,
    whitened_limit: f64,
}

impl GeneralizedModeResidual {
    pub fn ordered_index(&self) -> usize {
        self.ordered_index
    }

    pub fn absolute_residual(&self) -> f64 {
        self.generalized_absolute_residual
    }

    pub fn scale(&self) -> f64 {
        self.generalized_scale
    }

    pub fn limit(&self) -> f64 {
        self.generalized_limit
    }

    pub fn whitened_absolute_residual(&self) -> f64 {
        self.whitened_absolute_residual
    }

    pub fn whitened_scale(&self) -> f64 {
        self.whitened_scale
    }

    pub fn whitened_limit(&self) -> f64 {
        self.whitened_limit
    }
}

/// Location of a numerical value relative to a conditional analytic interval.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum IntervalLocation {
    Below,
    Inside,
    Above,
}

/// The comparison interval depends on a required, unmechanized FE transfer premise.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AnalyticTransferStatus {
    ConditionalUnmechanizedPremise,
}

/// Applicability and interval for one ordered continuum comparison.
#[derive(Clone, Debug, PartialEq, Serialize)]
#[serde(tag = "scope", rename_all = "snake_case")]
pub enum OrderedAnalyticScope {
    ZeroMode {
        numerical_uncertainty: f64,
        within_interval: bool,
    },
    InScope {
        theorem_ratio_exact: ExactRatioReceipt,
        theorem_ratio: f64,
        lower_bound: f64,
        upper_bound: f64,
        numerical_uncertainty: f64,
        location: IntervalLocation,
        transfer_status: AnalyticTransferStatus,
    },
    OutOfScope {
        theorem_ratio_exact: ExactRatioReceipt,
        theorem_ratio: f64,
        reason: OrderedScopeReason,
    },
    NumericallyUnresolved {
        theorem_ratio_exact: ExactRatioReceipt,
        theorem_ratio: f64,
        reason: OrderedNumericalReason,
        lower_bound: Option<f64>,
        upper_bound: Option<f64>,
        numerical_uncertainty: Option<f64>,
    },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum OrderedScopeReason {
    StrictMeshConditionFailed,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum OrderedNumericalReason {
    UpperDenominatorTooSmall,
    NonFiniteBoundArithmetic,
    ComparisonUncertaintyTouchesBoundary,
}

/// One ordered member of the discrete spectrum.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct OrderedModeComparison {
    ordered_index: usize,
    continuum_mode: usize,
    eigenvalue: f64,
    continuum_target: f64,
    analytic_scope: OrderedAnalyticScope,
}

impl OrderedModeComparison {
    pub fn ordered_index(&self) -> usize {
        self.ordered_index
    }

    pub fn continuum_mode(&self) -> usize {
        self.continuum_mode
    }

    pub fn eigenvalue(&self) -> f64 {
        self.eigenvalue
    }

    pub fn continuum_target(&self) -> f64 {
        self.continuum_target
    }

    pub fn analytic_scope(&self) -> &OrderedAnalyticScope {
        &self.analytic_scope
    }
}

/// Ordered splitting of one requested positive continuum doublet.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct DoubletSplitEvidence {
    continuum_mode: usize,
    left_ordered_index: usize,
    right_ordered_index: usize,
    left_eigenvalue: f64,
    right_eigenvalue: f64,
    split: f64,
}

impl DoubletSplitEvidence {
    pub fn continuum_mode(&self) -> usize {
        self.continuum_mode
    }

    pub fn ordered_indices(&self) -> (usize, usize) {
        (self.left_ordered_index, self.right_ordered_index)
    }

    pub fn eigenvalues(&self) -> (f64, f64) {
        (self.left_eigenvalue, self.right_eigenvalue)
    }

    pub fn split(&self) -> f64 {
        self.split
    }
}

/// Scale-aware PSD, null-mode, and spectral-gap receipt.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct SpectrumSanityReceipt {
    minimum_eigenvalue: f64,
    first_positive_eigenvalue: f64,
    spectral_scale: f64,
    psd_limit: f64,
    zero_mode_limit: f64,
}

impl SpectrumSanityReceipt {
    pub fn minimum_eigenvalue(&self) -> f64 {
        self.minimum_eigenvalue
    }

    pub fn first_positive_eigenvalue(&self) -> f64 {
        self.first_positive_eigenvalue
    }

    pub fn spectral_scale(&self) -> f64 {
        self.spectral_scale
    }

    pub fn psd_limit(&self) -> f64 {
        self.psd_limit
    }

    pub fn zero_mode_limit(&self) -> f64 {
        self.zero_mode_limit
    }
}

/// Machine-readable conditioning and numerical-resolution disclosure.
///
/// The residual inclusion radius concerns the rounded symmetric matrix. The
/// roundoff guard additionally scales with the exact conditioning ratios, but
/// is a declared falsifier guard rather than a theorem about forward error.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct NumericalResolutionReceipt {
    whitened_matrix_infinity_norm: f64,
    maximum_whitened_residual: f64,
    residual_inclusion_radius: f64,
    declared_roundoff_guard: f64,
    comparison_uncertainty: f64,
    hard_condition_ratio: u64,
    transfer_status: AnalyticTransferStatus,
}

impl NumericalResolutionReceipt {
    pub fn whitened_matrix_infinity_norm(&self) -> f64 {
        self.whitened_matrix_infinity_norm
    }

    pub fn maximum_whitened_residual(&self) -> f64 {
        self.maximum_whitened_residual
    }

    pub fn residual_inclusion_radius(&self) -> f64 {
        self.residual_inclusion_radius
    }

    pub fn declared_roundoff_guard(&self) -> f64 {
        self.declared_roundoff_guard
    }

    pub fn comparison_uncertainty(&self) -> f64 {
        self.comparison_uncertainty
    }

    pub fn hard_condition_ratio(&self) -> u64 {
        self.hard_condition_ratio
    }

    pub fn transfer_status(&self) -> AnalyticTransferStatus {
        self.transfer_status
    }
}

/// Validated numerical evidence for one exact periodic mesh.
///
/// There is deliberately no unchecked deserialization route:
///
/// ```compile_fail
/// use serde::de::DeserializeOwned;
/// use core_solvers::solver_spectrum_periodic::PeriodicSpectrumEvidence;
/// fn require_deserialize<T: DeserializeOwned>() {}
/// require_deserialize::<PeriodicSpectrumEvidence>();
/// ```
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct PeriodicSpectrumEvidence {
    schema: String,
    exact_mesh_sha256: String,
    dimension: usize,
    max_mode: usize,
    minimum_gap: f64,
    maximum_gap: f64,
    gap_ratio: f64,
    gap_ratio_exact: ExactRatioReceipt,
    mass_ratio: f64,
    mass_ratio_exact: ExactRatioReceipt,
    eigenvalues: Vec<f64>,
    residuals: Vec<GeneralizedModeResidual>,
    m_orthogonality_residual: f64,
    whitened_symmetry_residual: f64,
    spectrum_sanity: SpectrumSanityReceipt,
    numerical_resolution: NumericalResolutionReceipt,
    ordered_comparisons: Vec<OrderedModeComparison>,
    doublet_splits: Vec<DoubletSplitEvidence>,
    policy: PeriodicSpectrumPolicy,
    authority_effect: AuthorityEffectLevel,
}

impl PeriodicSpectrumEvidence {
    pub fn schema(&self) -> &str {
        &self.schema
    }

    pub fn exact_mesh_sha256(&self) -> &str {
        &self.exact_mesh_sha256
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    pub fn max_mode(&self) -> usize {
        self.max_mode
    }

    pub fn gap_extrema(&self) -> (f64, f64) {
        (self.minimum_gap, self.maximum_gap)
    }

    pub fn gap_ratio(&self) -> f64 {
        self.gap_ratio
    }

    pub fn gap_ratio_exact(&self) -> &ExactRatioReceipt {
        &self.gap_ratio_exact
    }

    pub fn mass_ratio(&self) -> f64 {
        self.mass_ratio
    }

    pub fn mass_ratio_exact(&self) -> &ExactRatioReceipt {
        &self.mass_ratio_exact
    }

    pub fn eigenvalues(&self) -> &[f64] {
        &self.eigenvalues
    }

    pub fn residuals(&self) -> &[GeneralizedModeResidual] {
        &self.residuals
    }

    pub fn m_orthogonality_residual(&self) -> f64 {
        self.m_orthogonality_residual
    }

    pub fn whitened_symmetry_residual(&self) -> f64 {
        self.whitened_symmetry_residual
    }

    pub fn spectrum_sanity(&self) -> &SpectrumSanityReceipt {
        &self.spectrum_sanity
    }

    pub fn numerical_resolution(&self) -> &NumericalResolutionReceipt {
        &self.numerical_resolution
    }

    pub fn ordered_comparisons(&self) -> &[OrderedModeComparison] {
        &self.ordered_comparisons
    }

    pub fn doublet_splits(&self) -> &[DoubletSplitEvidence] {
        &self.doublet_splits
    }

    pub fn policy(&self) -> &PeriodicSpectrumPolicy {
        &self.policy
    }

    pub fn authority_effect(&self) -> AuthorityEffectLevel {
        self.authority_effect
    }
}

/// Solves the exact-gap periodic lumped finite-volume generalized spectrum.
///
/// `max_mode` requests the complete doublets `1..=max_mode`; consequently the
/// finite carrier must satisfy `2 * max_mode < gaps.len()`.
fn validate_carrier_dimensions_and_sum(
    gaps: &[PositiveRational],
    max_mode: usize,
    policy: &PeriodicSpectrumPolicy,
) -> Result<usize, PeriodicSpectrumError> {
    let dimension = gaps.len();
    if dimension < 3 {
        return Err(PeriodicSpectrumError::DimensionTooSmall(dimension));
    }
    if dimension > HARD_MAX_DIMENSION || dimension > policy.max_dimension {
        return Err(PeriodicSpectrumError::DimensionLimitExceeded {
            dimension,
            policy_limit: policy.max_dimension,
            hard_limit: HARD_MAX_DIMENSION,
        });
    }
    let maximum_complete_mode = (dimension - 1) / 2;
    if max_mode > maximum_complete_mode {
        return Err(PeriodicSpectrumError::IncompleteDoubletRequest {
            dimension,
            max_mode,
            maximum_complete_mode,
        });
    }

    validate_rational_bit_caps(gaps)?;
    let exact_sum = exact_unit_sum(gaps)?;
    if exact_sum != BigRational::from_integer(BigInt::from(1_u8)) {
        return Err(PeriodicSpectrumError::NonUnitExactGapSum);
    }
    Ok(dimension)
}

fn compute_exact_gaps_and_masses(
    gaps: &[PositiveRational],
    policy: &PeriodicSpectrumPolicy,
) -> Result<(BigRational, BigRational, Vec<BigRational>, BigRational), PeriodicSpectrumError> {
    let dimension = gaps.len();
    let first_gap = gaps
        .first()
        .ok_or(PeriodicSpectrumError::DimensionTooSmall(dimension))?;
    let minimum_gap_exact = gaps
        .iter()
        .map(PositiveRational::value)
        .fold(first_gap.value().clone(), |minimum, gap| {
            minimum.min(gap.clone())
        });
    let maximum_gap_exact = gaps
        .iter()
        .map(PositiveRational::value)
        .fold(first_gap.value().clone(), |maximum, gap| {
            maximum.max(gap.clone())
        });
    let gap_ratio_exact = maximum_gap_exact.clone() / minimum_gap_exact;
    enforce_exact_conditioning(
        &gap_ratio_exact,
        policy.max_gap_ratio,
        ConditioningKind::Gap,
    )?;

    let two = BigRational::from_integer(BigInt::from(2_u8));
    let exact_masses: Vec<BigRational> = (0..dimension)
        .map(|index| {
            let previous = (index + dimension - 1) % dimension;
            (gaps[previous].value().clone() + gaps[index].value().clone()) / two.clone()
        })
        .collect();
    let first_mass = exact_masses
        .first()
        .ok_or(PeriodicSpectrumError::DimensionTooSmall(dimension))?;
    let minimum_mass_exact = exact_masses
        .iter()
        .fold(first_mass.clone(), |minimum, mass| {
            minimum.min(mass.clone())
        });
    let maximum_mass_exact = exact_masses
        .iter()
        .fold(first_mass.clone(), |maximum, mass| {
            maximum.max(mass.clone())
        });
    let mass_ratio_exact = maximum_mass_exact / minimum_mass_exact;
    enforce_exact_conditioning(
        &mass_ratio_exact,
        policy.max_mass_ratio,
        ConditioningKind::Mass,
    )?;
    Ok((maximum_gap_exact, gap_ratio_exact, exact_masses, mass_ratio_exact))
}

fn convert_gaps_and_masses_to_f64(
    gaps: &[PositiveRational],
    exact_masses: &[BigRational],
) -> Result<(Vec<f64>, Vec<f64>), PeriodicSpectrumError> {
    let dimension = gaps.len();
    let mut float_gaps = Vec::with_capacity(dimension);
    for (index, gap) in gaps.iter().enumerate() {
        float_gaps.push(exact_positive_f64(
            gap.value(),
            PeriodicSpectrumError::GapNotRepresentableAsFiniteF64 { index },
        )?);
    }
    let masses: Vec<f64> = exact_masses
        .iter()
        .enumerate()
        .map(|(index, mass)| {
            exact_positive_f64(
                mass,
                PeriodicSpectrumError::MassNotRepresentableAsFiniteF64 { index },
            )
        })
        .collect::<Result<_, _>>()?;

    let float_sum: f64 = float_gaps.iter().sum();
    let unit_sum_tolerance = 128.0 * (dimension as f64).max(1.0) * f64::EPSILON;
    if (float_sum - 1.0).abs() > unit_sum_tolerance {
        return Err(PeriodicSpectrumError::UnitSumDrift {
            observed: float_sum,
            tolerance: unit_sum_tolerance,
        });
    }
    Ok((float_gaps, masses))
}

fn assemble_stiffness_and_whitened(
    float_gaps: &[f64],
    masses: &[f64],
) -> Result<(DMatrix<f64>, DMatrix<f64>, Vec<f64>, f64), PeriodicSpectrumError> {
    let dimension = float_gaps.len();
    let mut stiffness = DMatrix::<f64>::zeros(dimension, dimension);
    for (index, gap) in float_gaps.iter().copied().enumerate() {
        let next = (index + 1) % dimension;
        let weight = 1.0 / gap;
        if !weight.is_finite() {
            return Err(PeriodicSpectrumError::MatrixAssemblyOverflow);
        }
        stiffness[(index, index)] += weight;
        stiffness[(next, next)] += weight;
        stiffness[(index, next)] -= weight;
        stiffness[(next, index)] -= weight;
    }

    let inverse_sqrt_mass: Vec<f64> = masses.iter().map(|mass| 1.0 / mass.sqrt()).collect();
    if inverse_sqrt_mass.iter().any(|value| !value.is_finite()) {
        return Err(PeriodicSpectrumError::MatrixAssemblyOverflow);
    }
    let mut whitened = DMatrix::<f64>::zeros(dimension, dimension);
    for row in 0..dimension {
        for column in 0..=row {
            let value =
                inverse_sqrt_mass[row] * stiffness[(row, column)] * inverse_sqrt_mass[column];
            if !value.is_finite() {
                return Err(PeriodicSpectrumError::MatrixAssemblyOverflow);
            }
            whitened[(row, column)] = value;
            whitened[(column, row)] = value;
        }
    }
    let whitened_symmetry_residual = matrix_symmetry_residual(&whitened);
    if !whitened_symmetry_residual.is_finite() || whitened_symmetry_residual != 0.0 {
        return Err(PeriodicSpectrumError::WhitenedSymmetryViolation {
            residual: whitened_symmetry_residual,
        });
    }
    Ok((stiffness, whitened, inverse_sqrt_mass, whitened_symmetry_residual))
}

fn solve_ordered_eigenpairs(
    whitened: DMatrix<f64>,
    inverse_sqrt_mass: &[f64],
    policy: &PeriodicSpectrumPolicy,
) -> Result<(Vec<f64>, Vec<DVector<f64>>, Vec<DVector<f64>>), PeriodicSpectrumError> {
    let dimension = inverse_sqrt_mass.len();
    let decomposition =
        SymmetricEigen::try_new(whitened, policy.eigensolver_epsilon, policy.max_iterations)
            .ok_or(PeriodicSpectrumError::EigensolverDidNotConverge {
                max_iterations: policy.max_iterations,
            })?;

    let mut order: Vec<usize> = (0..dimension).collect();
    order.sort_by(|left, right| {
        decomposition.eigenvalues[*left].total_cmp(&decomposition.eigenvalues[*right])
    });

    let mut eigenvalues = Vec::with_capacity(dimension);
    let mut whitened_eigenvectors = Vec::with_capacity(dimension);
    let mut generalized_eigenvectors = Vec::with_capacity(dimension);
    for raw_index in order {
        let ordered_index = eigenvalues.len();
        let eigenvalue = decomposition.eigenvalues[raw_index];
        if !eigenvalue.is_finite() {
            return Err(PeriodicSpectrumError::NonFiniteEigenpair { ordered_index });
        }
        let y = decomposition.eigenvectors.column(raw_index).into_owned();
        let x = DVector::from_iterator(
            dimension,
            (0..dimension).map(|row| inverse_sqrt_mass[row] * y[row]),
        );
        if y.iter().chain(x.iter()).any(|value| !value.is_finite()) {
            return Err(PeriodicSpectrumError::NonFiniteEigenpair { ordered_index });
        }
        eigenvalues.push(eigenvalue);
        whitened_eigenvectors.push(y);
        generalized_eigenvectors.push(x);
    }
    Ok((eigenvalues, whitened_eigenvectors, generalized_eigenvectors))
}

fn convert_exact_ratios_to_f64(
    gap_ratio_exact: &BigRational,
    mass_ratio_exact: &BigRational,
) -> Result<(f64, f64), PeriodicSpectrumError> {
    let gap_ratio = exact_positive_f64(
        gap_ratio_exact,
        PeriodicSpectrumError::ExactRatioNotRepresentableAsFiniteF64 { kind: "gap" },
    )?;
    let mass_ratio = exact_positive_f64(
        mass_ratio_exact,
        PeriodicSpectrumError::ExactRatioNotRepresentableAsFiniteF64 { kind: "mass" },
    )?;
    Ok((gap_ratio, mass_ratio))
}

#[allow(clippy::too_many_arguments)]
fn compute_all_mode_residuals_and_orthogonality(
    dimension: usize,
    stiffness: &DMatrix<f64>,
    masses: &[f64],
    whitened_for_validation: &DMatrix<f64>,
    eigenvalues: &[f64],
    generalized_eigenvectors: &[DVector<f64>],
    whitened_eigenvectors: &[DVector<f64>],
    policy: &PeriodicSpectrumPolicy,
) -> Result<(Vec<GeneralizedModeResidual>, f64), PeriodicSpectrumError> {
    let mut residuals = Vec::with_capacity(dimension);
    for ordered_index in 0..dimension {
        residuals.push(validate_mode_residuals(
            ordered_index,
            stiffness,
            masses,
            whitened_for_validation,
            eigenvalues[ordered_index],
            &generalized_eigenvectors[ordered_index],
            &whitened_eigenvectors[ordered_index],
            policy,
        )?);
    }

    let m_orthogonality_residual = m_orthogonality_residual(masses, generalized_eigenvectors);
    if !m_orthogonality_residual.is_finite()
        || m_orthogonality_residual > policy.orthogonality_tolerance
    {
        return Err(PeriodicSpectrumError::OrthogonalityExceeded {
            residual: m_orthogonality_residual,
            limit: policy.orthogonality_tolerance,
        });
    }
    Ok((residuals, m_orthogonality_residual))
}

struct PreparedPeriodicMesh {
    dimension: usize,
    maximum_gap_exact: BigRational,
    gap_ratio_exact: BigRational,
    mass_ratio_exact: BigRational,
    exact_mesh_sha256: String,
    float_gaps: Vec<f64>,
    masses: Vec<f64>,
    minimum_gap: f64,
    maximum_gap: f64,
    gap_ratio: f64,
    mass_ratio: f64,
}

fn prepare_periodic_mesh_data(
    gaps: &[PositiveRational],
    max_mode: usize,
    policy: &PeriodicSpectrumPolicy,
) -> Result<PreparedPeriodicMesh, PeriodicSpectrumError> {
    validate_policy(policy)?;
    let dimension = validate_carrier_dimensions_and_sum(gaps, max_mode, policy)?;
    let (maximum_gap_exact, gap_ratio_exact, exact_masses, mass_ratio_exact) =
        compute_exact_gaps_and_masses(gaps, policy)?;
    let exact_mesh_sha256 = exact_mesh_digest(gaps)?;
    let (float_gaps, masses) = convert_gaps_and_masses_to_f64(gaps, &exact_masses)?;
    let minimum_gap = float_gaps.iter().copied().fold(f64::INFINITY, f64::min);
    let maximum_gap = float_gaps.iter().copied().fold(0.0_f64, f64::max);
    let (gap_ratio, mass_ratio) =
        convert_exact_ratios_to_f64(&gap_ratio_exact, &mass_ratio_exact)?;
    Ok(PreparedPeriodicMesh {
        dimension,
        maximum_gap_exact,
        gap_ratio_exact,
        mass_ratio_exact,
        exact_mesh_sha256,
        float_gaps,
        masses,
        minimum_gap,
        maximum_gap,
        gap_ratio,
        mass_ratio,
    })
}

pub fn periodic_lumped_fv_spectrum(
    gaps: &[PositiveRational],
    max_mode: usize,
    policy: &PeriodicSpectrumPolicy,
) -> Result<PeriodicSpectrumEvidence, PeriodicSpectrumError> {
    let PreparedPeriodicMesh {
        dimension,
        maximum_gap_exact,
        gap_ratio_exact,
        mass_ratio_exact,
        exact_mesh_sha256,
        float_gaps,
        masses,
        minimum_gap,
        maximum_gap,
        gap_ratio,
        mass_ratio,
    } = prepare_periodic_mesh_data(gaps, max_mode, policy)?;

    let (stiffness, whitened, inverse_sqrt_mass, whitened_symmetry_residual) =
        assemble_stiffness_and_whitened(&float_gaps, &masses)?;
    let whitened_for_validation = whitened.clone();

    let (eigenvalues, whitened_eigenvectors, generalized_eigenvectors) =
        solve_ordered_eigenpairs(whitened, &inverse_sqrt_mass, policy)?;

    let spectrum_sanity = validate_spectrum_sanity(&eigenvalues, policy)?;
    let (residuals, m_orthogonality_residual) = compute_all_mode_residuals_and_orthogonality(
        dimension,
        &stiffness,
        &masses,
        &whitened_for_validation,
        &eigenvalues,
        &generalized_eigenvectors,
        &whitened_eigenvectors,
        policy,
    )?;

    let numerical_resolution = numerical_resolution_receipt(
        &whitened_for_validation,
        &residuals,
        dimension,
        gap_ratio,
        mass_ratio,
    )?;
    let ordered_comparisons = compare_ordered_modes(
        &eigenvalues,
        max_mode,
        maximum_gap,
        &maximum_gap_exact,
        spectrum_sanity.zero_mode_limit,
        &numerical_resolution,
        policy,
    )?;
    let doublet_splits = doublet_splits(&eigenvalues, max_mode);

    Ok(PeriodicSpectrumEvidence {
        schema: PERIODIC_SPECTRUM_EVIDENCE_SCHEMA.to_string(),
        exact_mesh_sha256,
        dimension,
        max_mode,
        minimum_gap,
        maximum_gap,
        gap_ratio,
        gap_ratio_exact: exact_ratio_receipt(&gap_ratio_exact),
        mass_ratio,
        mass_ratio_exact: exact_ratio_receipt(&mass_ratio_exact),
        eigenvalues,
        residuals,
        m_orthogonality_residual,
        whitened_symmetry_residual,
        spectrum_sanity,
        numerical_resolution,
        ordered_comparisons,
        doublet_splits,
        policy: policy.clone(),
        authority_effect: AuthorityEffectLevel::None,
    })
}

#[allow(clippy::too_many_arguments)]
fn classify_nonzero_mode_scope(
    continuum_mode: usize,
    eigenvalue: f64,
    continuum_target: f64,
    numerical_uncertainty: f64,
    maximum_gap: f64,
    maximum_gap_exact: &BigRational,
    policy: &PeriodicSpectrumPolicy,
) -> Result<OrderedAnalyticScope, PeriodicSpectrumError> {
    let k = BigInt::from(continuum_mode);
    let coefficient = BigRational::from_integer(BigInt::from(4_u8) * k.clone() * k);
    let theorem_ratio_exact = coefficient * maximum_gap_exact.clone() * maximum_gap_exact.clone();
    let theorem_ratio = theorem_ratio_exact
        .to_f64()
        .filter(|value| value.is_finite())
        .ok_or(
            PeriodicSpectrumError::AnalyticRatioNotRepresentableAsFiniteF64 { continuum_mode },
        )?;
    let theorem_ratio_receipt = exact_ratio_receipt(&theorem_ratio_exact);
    if theorem_ratio_exact >= BigRational::from_integer(BigInt::from(1_u8)) {
        return Ok(OrderedAnalyticScope::OutOfScope {
            theorem_ratio_exact: theorem_ratio_receipt,
            theorem_ratio,
            reason: OrderedScopeReason::StrictMeshConditionFailed,
        });
    }
    let upper_denominator = 1.0 - theorem_ratio;
    if !upper_denominator.is_finite() || upper_denominator <= policy.minimum_upper_denominator {
        return Ok(OrderedAnalyticScope::NumericallyUnresolved {
            theorem_ratio_exact: theorem_ratio_receipt,
            theorem_ratio,
            reason: OrderedNumericalReason::UpperDenominatorTooSmall,
            lower_bound: None,
            upper_bound: None,
            numerical_uncertainty: None,
        });
    }
    let lower_bound = continuum_target / (1.0 + continuum_target * maximum_gap.powi(2) / 6.0);
    let upper_bound = continuum_target / upper_denominator.powi(2);
    if !lower_bound.is_finite() || !upper_bound.is_finite() {
        return Ok(OrderedAnalyticScope::NumericallyUnresolved {
            theorem_ratio_exact: theorem_ratio_receipt,
            theorem_ratio,
            reason: OrderedNumericalReason::NonFiniteBoundArithmetic,
            lower_bound: None,
            upper_bound: None,
            numerical_uncertainty: None,
        });
    }
    Ok(
        match resolved_interval_location(eigenvalue, lower_bound, upper_bound, numerical_uncertainty)
        {
            Some(location) => OrderedAnalyticScope::InScope {
                theorem_ratio_exact: theorem_ratio_receipt,
                theorem_ratio,
                lower_bound,
                upper_bound,
                numerical_uncertainty,
                location,
                transfer_status: AnalyticTransferStatus::ConditionalUnmechanizedPremise,
            },
            None => OrderedAnalyticScope::NumericallyUnresolved {
                theorem_ratio_exact: theorem_ratio_receipt,
                theorem_ratio,
                reason: OrderedNumericalReason::ComparisonUncertaintyTouchesBoundary,
                lower_bound: Some(lower_bound),
                upper_bound: Some(upper_bound),
                numerical_uncertainty: Some(numerical_uncertainty),
            },
        },
    )
}

fn compare_ordered_modes(
    eigenvalues: &[f64],
    max_mode: usize,
    maximum_gap: f64,
    maximum_gap_exact: &BigRational,
    zero_mode_limit: f64,
    numerical_resolution: &NumericalResolutionReceipt,
    policy: &PeriodicSpectrumPolicy,
) -> Result<Vec<OrderedModeComparison>, PeriodicSpectrumError> {
    let comparison_count = 2 * max_mode + 1;
    let mut comparisons = Vec::with_capacity(comparison_count);
    for (ordered_index, eigenvalue) in eigenvalues[..comparison_count].iter().copied().enumerate() {
        let continuum_mode = if ordered_index == 0 {
            0
        } else {
            ordered_index.div_ceil(2)
        };
        let continuum_mode_f64 = continuum_mode as f64;
        let continuum_target = (2.0 * PI * continuum_mode_f64).powi(2);
        let numerical_uncertainty = numerical_resolution.comparison_uncertainty
            + 512.0 * f64::EPSILON * continuum_target.abs().max(eigenvalue.abs()).max(1.0);

        let analytic_scope = if ordered_index == 0 {
            OrderedAnalyticScope::ZeroMode {
                numerical_uncertainty,
                within_interval: eigenvalue.abs() <= zero_mode_limit,
            }
        } else {
            classify_nonzero_mode_scope(
                continuum_mode,
                eigenvalue,
                continuum_target,
                numerical_uncertainty,
                maximum_gap,
                maximum_gap_exact,
                policy,
            )?
        };

        comparisons.push(OrderedModeComparison {
            ordered_index,
            continuum_mode,
            eigenvalue,
            continuum_target,
            analytic_scope,
        });
    }
    Ok(comparisons)
}

fn resolved_interval_location(
    value: f64,
    lower_bound: f64,
    upper_bound: f64,
    numerical_uncertainty: f64,
) -> Option<IntervalLocation> {
    if value + numerical_uncertainty < lower_bound {
        Some(IntervalLocation::Below)
    } else if value - numerical_uncertainty > upper_bound {
        Some(IntervalLocation::Above)
    } else if value - numerical_uncertainty >= lower_bound
        && value + numerical_uncertainty <= upper_bound
    {
        Some(IntervalLocation::Inside)
    } else {
        None
    }
}

fn doublet_splits(eigenvalues: &[f64], max_mode: usize) -> Vec<DoubletSplitEvidence> {
    (1..=max_mode)
        .map(|continuum_mode| {
            let left_ordered_index = 2 * continuum_mode - 1;
            let right_ordered_index = left_ordered_index + 1;
            let left_eigenvalue = eigenvalues[left_ordered_index];
            let right_eigenvalue = eigenvalues[right_ordered_index];
            DoubletSplitEvidence {
                continuum_mode,
                left_ordered_index,
                right_ordered_index,
                left_eigenvalue,
                right_eigenvalue,
                split: (right_eigenvalue - left_eigenvalue).abs(),
            }
        })
        .collect()
}

#[allow(clippy::too_many_arguments)]
fn validate_mode_residuals(
    ordered_index: usize,
    stiffness: &DMatrix<f64>,
    masses: &[f64],
    whitened: &DMatrix<f64>,
    eigenvalue: f64,
    generalized_eigenvector: &DVector<f64>,
    whitened_eigenvector: &DVector<f64>,
    policy: &PeriodicSpectrumPolicy,
) -> Result<GeneralizedModeResidual, PeriodicSpectrumError> {
    let kx = stiffness * generalized_eigenvector;
    let mx = DVector::from_iterator(
        generalized_eigenvector.len(),
        generalized_eigenvector
            .iter()
            .zip(masses)
            .map(|(value, mass)| value * mass),
    );
    let generalized_residual = &kx - eigenvalue * &mx;
    let generalized_absolute_residual = infinity_norm(&generalized_residual);
    let generalized_scale = infinity_norm(&kx) + eigenvalue.abs() * infinity_norm(&mx);
    let generalized_limit =
        policy.residual_absolute_tolerance + policy.residual_relative_tolerance * generalized_scale;
    if !generalized_absolute_residual.is_finite()
        || generalized_absolute_residual > generalized_limit
    {
        return Err(PeriodicSpectrumError::GeneralizedResidualExceeded {
            ordered_index,
            residual: generalized_absolute_residual,
            limit: generalized_limit,
        });
    }

    let ay = whitened * whitened_eigenvector;
    let whitened_residual = &ay - eigenvalue * whitened_eigenvector;
    let whitened_absolute_residual = infinity_norm(&whitened_residual);
    let whitened_scale =
        infinity_norm(&ay) + eigenvalue.abs() * infinity_norm(whitened_eigenvector);
    let whitened_limit =
        policy.residual_absolute_tolerance + policy.residual_relative_tolerance * whitened_scale;
    if !whitened_absolute_residual.is_finite() || whitened_absolute_residual > whitened_limit {
        return Err(PeriodicSpectrumError::WhitenedResidualExceeded {
            ordered_index,
            residual: whitened_absolute_residual,
            limit: whitened_limit,
        });
    }

    Ok(GeneralizedModeResidual {
        ordered_index,
        generalized_absolute_residual,
        generalized_scale,
        generalized_limit,
        whitened_absolute_residual,
        whitened_scale,
        whitened_limit,
    })
}

fn validate_spectrum_sanity(
    eigenvalues: &[f64],
    policy: &PeriodicSpectrumPolicy,
) -> Result<SpectrumSanityReceipt, PeriodicSpectrumError> {
    let spectral_scale = eigenvalues
        .iter()
        .map(|value| value.abs())
        .fold(1.0_f64, f64::max);
    let psd_limit =
        policy.negative_eigenvalue_tolerance + policy.residual_relative_tolerance * spectral_scale;
    let zero_mode_limit =
        policy.zero_mode_tolerance + policy.residual_relative_tolerance * spectral_scale;
    if eigenvalues[0] < -psd_limit {
        return Err(PeriodicSpectrumError::NegativeSpectrumBeyondTolerance {
            minimum_eigenvalue: eigenvalues[0],
            spectral_scale,
            tolerance: psd_limit,
        });
    }
    if eigenvalues[0].abs() > zero_mode_limit {
        return Err(PeriodicSpectrumError::ZeroModeOutsideTolerance {
            eigenvalue: eigenvalues[0],
            spectral_scale,
            tolerance: zero_mode_limit,
        });
    }
    if eigenvalues[1] <= zero_mode_limit {
        return Err(PeriodicSpectrumError::AdditionalZeroMode {
            first_positive_eigenvalue: eigenvalues[1],
            spectral_scale,
            tolerance: zero_mode_limit,
        });
    }
    Ok(SpectrumSanityReceipt {
        minimum_eigenvalue: eigenvalues[0],
        first_positive_eigenvalue: eigenvalues[1],
        spectral_scale,
        psd_limit,
        zero_mode_limit,
    })
}

fn matrix_symmetry_residual(matrix: &DMatrix<f64>) -> f64 {
    let mut residual = 0.0_f64;
    for row in 0..matrix.nrows() {
        for column in 0..row {
            residual = residual.max((matrix[(row, column)] - matrix[(column, row)]).abs());
        }
    }
    residual
}

fn numerical_resolution_receipt(
    whitened: &DMatrix<f64>,
    residuals: &[GeneralizedModeResidual],
    dimension: usize,
    gap_ratio: f64,
    mass_ratio: f64,
) -> Result<NumericalResolutionReceipt, PeriodicSpectrumError> {
    let whitened_matrix_infinity_norm = matrix_infinity_norm(whitened);
    let maximum_whitened_residual = residuals
        .iter()
        .map(GeneralizedModeResidual::whitened_absolute_residual)
        .fold(0.0_f64, f64::max);
    let residual_inclusion_radius = (dimension as f64).sqrt() * maximum_whitened_residual;
    let declared_roundoff_guard = 256.0
        * dimension as f64
        * f64::EPSILON
        * whitened_matrix_infinity_norm
        * gap_ratio.max(mass_ratio).max(1.0);
    let comparison_uncertainty = residual_inclusion_radius + declared_roundoff_guard;
    if [
        whitened_matrix_infinity_norm,
        maximum_whitened_residual,
        residual_inclusion_radius,
        declared_roundoff_guard,
        comparison_uncertainty,
    ]
    .iter()
    .any(|value| !value.is_finite())
    {
        return Err(PeriodicSpectrumError::NumericalResolutionUnavailable);
    }
    Ok(NumericalResolutionReceipt {
        whitened_matrix_infinity_norm,
        maximum_whitened_residual,
        residual_inclusion_radius,
        declared_roundoff_guard,
        comparison_uncertainty,
        hard_condition_ratio: HARD_MAX_CONDITION_RATIO,
        transfer_status: AnalyticTransferStatus::ConditionalUnmechanizedPremise,
    })
}

fn matrix_infinity_norm(matrix: &DMatrix<f64>) -> f64 {
    (0..matrix.nrows())
        .map(|row| {
            (0..matrix.ncols())
                .map(|column| matrix[(row, column)].abs())
                .sum()
        })
        .fold(0.0_f64, f64::max)
}

fn m_orthogonality_residual(masses: &[f64], eigenvectors: &[DVector<f64>]) -> f64 {
    let mut maximum = 0.0_f64;
    for (left_index, left) in eigenvectors.iter().enumerate() {
        for (right_index, right) in eigenvectors.iter().enumerate() {
            let product: f64 = masses
                .iter()
                .zip(left.iter())
                .zip(right.iter())
                .map(|((mass, left_value), right_value)| mass * left_value * right_value)
                .sum();
            let target = if left_index == right_index { 1.0 } else { 0.0 };
            maximum = maximum.max((product - target).abs());
        }
    }
    maximum
}

fn infinity_norm(vector: &DVector<f64>) -> f64 {
    vector
        .iter()
        .map(|value| value.abs())
        .fold(0.0_f64, f64::max)
}

fn validate_rational_bit_caps(gaps: &[PositiveRational]) -> Result<(), PeriodicSpectrumError> {
    for (index, gap) in gaps.iter().enumerate() {
        let numerator_bits = gap.numerator().bits();
        let denominator_bits = gap.denominator().bits();
        if numerator_bits > HARD_MAX_RATIONAL_BITS || denominator_bits > HARD_MAX_RATIONAL_BITS {
            return Err(PeriodicSpectrumError::RationalBitLimitExceeded {
                index,
                numerator_bits,
                denominator_bits,
                hard_limit: HARD_MAX_RATIONAL_BITS,
            });
        }
    }
    Ok(())
}

fn exact_unit_sum(gaps: &[PositiveRational]) -> Result<BigRational, PeriodicSpectrumError> {
    let mut sum = BigRational::from_integer(BigInt::from(0_u8));
    for (through_index, gap) in gaps.iter().enumerate() {
        sum += gap.value().clone();
        let numerator_bits = sum.numer().bits();
        let denominator_bits = sum.denom().bits();
        if numerator_bits > HARD_MAX_ACCUMULATOR_BITS
            || denominator_bits > HARD_MAX_ACCUMULATOR_BITS
        {
            return Err(PeriodicSpectrumError::AccumulatorBitLimitExceeded {
                through_index,
                numerator_bits,
                denominator_bits,
                hard_limit: HARD_MAX_ACCUMULATOR_BITS,
            });
        }
    }
    Ok(sum)
}

#[derive(Clone, Copy)]
enum ConditioningKind {
    Gap,
    Mass,
}

fn enforce_exact_conditioning(
    ratio: &BigRational,
    limit: u64,
    kind: ConditioningKind,
) -> Result<(), PeriodicSpectrumError> {
    let limit_exact = BigRational::from_integer(BigInt::from(limit));
    if ratio <= &limit_exact {
        return Ok(());
    }
    let receipt = exact_ratio_receipt(ratio);
    match kind {
        ConditioningKind::Gap => Err(PeriodicSpectrumError::ExactGapRatioLimitExceeded {
            ratio_numerator: receipt.numerator,
            ratio_denominator: receipt.denominator,
            limit,
        }),
        ConditioningKind::Mass => Err(PeriodicSpectrumError::ExactMassRatioLimitExceeded {
            ratio_numerator: receipt.numerator,
            ratio_denominator: receipt.denominator,
            limit,
        }),
    }
}

fn exact_positive_f64(
    value: &BigRational,
    error: PeriodicSpectrumError,
) -> Result<f64, PeriodicSpectrumError> {
    value
        .to_f64()
        .filter(|converted| converted.is_finite() && *converted > 0.0)
        .ok_or(error)
}

fn exact_ratio_receipt(value: &BigRational) -> ExactRatioReceipt {
    ExactRatioReceipt {
        numerator: value.numer().to_string(),
        denominator: value.denom().to_string(),
    }
}

fn exact_mesh_digest(gaps: &[PositiveRational]) -> Result<String, PeriodicSpectrumError> {
    let payload = serde_json::to_vec(&("core.periodic-fv-mesh.v1", gaps))
        .map_err(|_| PeriodicSpectrumError::ExactMeshSerializationFailed)?;
    let digest = Sha256::digest(payload);
    Ok(digest.iter().map(|byte| format!("{byte:02x}")).collect())
}

fn validate_integer_policy_bounds(
    policy: &PeriodicSpectrumPolicy,
) -> Result<(), PeriodicSpectrumError> {
    if !(3..=HARD_MAX_DIMENSION).contains(&policy.max_dimension) {
        return Err(PeriodicSpectrumError::InvalidPolicy {
            field: "max_dimension",
        });
    }
    for (field, val, max_val) in [
        (
            "max_iterations",
            policy.max_iterations as u64,
            HARD_MAX_ITERATIONS as u64,
        ),
        ("max_gap_ratio", policy.max_gap_ratio, HARD_MAX_CONDITION_RATIO),
        ("max_mass_ratio", policy.max_mass_ratio, HARD_MAX_CONDITION_RATIO),
    ] {
        if val == 0 || val > max_val {
            return Err(PeriodicSpectrumError::InvalidPolicy { field });
        }
    }
    Ok(())
}

fn validate_policy(policy: &PeriodicSpectrumPolicy) -> Result<(), PeriodicSpectrumError> {
    validate_integer_policy_bounds(policy)?;
    for (field, value) in [
        ("eigensolver_epsilon", policy.eigensolver_epsilon),
        (
            "residual_absolute_tolerance",
            policy.residual_absolute_tolerance,
        ),
        (
            "residual_relative_tolerance",
            policy.residual_relative_tolerance,
        ),
        ("orthogonality_tolerance", policy.orthogonality_tolerance),
        (
            "negative_eigenvalue_tolerance",
            policy.negative_eigenvalue_tolerance,
        ),
        ("zero_mode_tolerance", policy.zero_mode_tolerance),
        (
            "minimum_upper_denominator",
            policy.minimum_upper_denominator,
        ),
    ] {
        require_positive_finite_policy(field, value)?;
    }
    if policy.minimum_upper_denominator >= 1.0 {
        return Err(PeriodicSpectrumError::InvalidPolicy {
            field: "minimum_upper_denominator",
        });
    }
    Ok(())
}

fn require_positive_finite_policy(
    field: &'static str,
    value: f64,
) -> Result<(), PeriodicSpectrumError> {
    if !value.is_finite() || value <= 0.0 {
        Err(PeriodicSpectrumError::InvalidPolicy { field })
    } else {
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Error)]
pub enum PeriodicSpectrumError {
    #[error("periodic spectrum requires at least three gaps, got {0}")]
    DimensionTooSmall(usize),
    #[error(
        "mesh dimension {dimension} exceeds policy limit {policy_limit} or hard limit {hard_limit}"
    )]
    DimensionLimitExceeded {
        dimension: usize,
        policy_limit: usize,
        hard_limit: usize,
    },
    #[error(
        "max_mode {max_mode} requests an incomplete periodic doublet at dimension {dimension}; maximum complete mode is {maximum_complete_mode}"
    )]
    IncompleteDoubletRequest {
        dimension: usize,
        max_mode: usize,
        maximum_complete_mode: usize,
    },
    #[error(
        "gap {index} uses {numerator_bits}/{denominator_bits} numerator/denominator bits, exceeding hard limit {hard_limit}"
    )]
    RationalBitLimitExceeded {
        index: usize,
        numerator_bits: u64,
        denominator_bits: u64,
        hard_limit: u64,
    },
    #[error(
        "exact sum through gap {through_index} uses {numerator_bits}/{denominator_bits} numerator/denominator bits, exceeding hard limit {hard_limit}"
    )]
    AccumulatorBitLimitExceeded {
        through_index: usize,
        numerator_bits: u64,
        denominator_bits: u64,
        hard_limit: u64,
    },
    #[error("exact rational gaps do not sum to one")]
    NonUnitExactGapSum,
    #[error(
        "exact gap ratio {ratio_numerator}/{ratio_denominator} exceeds integer ceiling {limit}"
    )]
    ExactGapRatioLimitExceeded {
        ratio_numerator: String,
        ratio_denominator: String,
        limit: u64,
    },
    #[error(
        "exact lumped-mass ratio {ratio_numerator}/{ratio_denominator} exceeds integer ceiling {limit}"
    )]
    ExactMassRatioLimitExceeded {
        ratio_numerator: String,
        ratio_denominator: String,
        limit: u64,
    },
    #[error("gap {index} cannot be represented as a positive finite f64")]
    GapNotRepresentableAsFiniteF64 { index: usize },
    #[error("lumped mass {index} cannot be represented as a positive finite f64")]
    MassNotRepresentableAsFiniteF64 { index: usize },
    #[error("exact {kind} ratio cannot be represented as a positive finite f64")]
    ExactRatioNotRepresentableAsFiniteF64 { kind: &'static str },
    #[error("converted gap sum {observed:e} differs from one beyond {tolerance:e}")]
    UnitSumDrift { observed: f64, tolerance: f64 },
    #[error("matrix assembly produced non-finite arithmetic")]
    MatrixAssemblyOverflow,
    #[error("whitened matrix is not exactly symmetric; residual {residual:e}")]
    WhitenedSymmetryViolation { residual: f64 },
    #[error("bounded exact mesh serialization failed")]
    ExactMeshSerializationFailed,
    #[error("conditioning-aware numerical resolution receipt is non-finite")]
    NumericalResolutionUnavailable,
    #[error("symmetric eigensolver did not converge within {max_iterations} iterations")]
    EigensolverDidNotConverge { max_iterations: usize },
    #[error("ordered eigenpair {ordered_index} contains non-finite arithmetic")]
    NonFiniteEigenpair { ordered_index: usize },
    #[error(
        "ordered eigenpair {ordered_index} generalized residual {residual:e} exceeds {limit:e}"
    )]
    GeneralizedResidualExceeded {
        ordered_index: usize,
        residual: f64,
        limit: f64,
    },
    #[error("ordered eigenpair {ordered_index} whitened residual {residual:e} exceeds {limit:e}")]
    WhitenedResidualExceeded {
        ordered_index: usize,
        residual: f64,
        limit: f64,
    },
    #[error("M-orthogonality residual {residual:e} exceeds {limit:e}")]
    OrthogonalityExceeded { residual: f64, limit: f64 },
    #[error("minimum eigenvalue {minimum_eigenvalue:e} is below PSD tolerance {tolerance:e}")]
    NegativeSpectrumBeyondTolerance {
        minimum_eigenvalue: f64,
        spectral_scale: f64,
        tolerance: f64,
    },
    #[error(
        "zero-mode eigenvalue {eigenvalue:e} exceeds scale-aware tolerance {tolerance:e} at spectral scale {spectral_scale:e}"
    )]
    ZeroModeOutsideTolerance {
        eigenvalue: f64,
        spectral_scale: f64,
        tolerance: f64,
    },
    #[error(
        "first positive eigenvalue {first_positive_eigenvalue:e} is not separated from zero beyond scale-aware tolerance {tolerance:e} at spectral scale {spectral_scale:e}"
    )]
    AdditionalZeroMode {
        first_positive_eigenvalue: f64,
        spectral_scale: f64,
        tolerance: f64,
    },
    #[error("exact theorem ratio for continuum mode {continuum_mode} is not finite in f64")]
    AnalyticRatioNotRepresentableAsFiniteF64 { continuum_mode: usize },
    #[error("invalid periodic spectrum policy field {field}")]
    InvalidPolicy { field: &'static str },
}

// Origin: engine/crates_rs/core_solvers/src/solver_spectrum_periodic.rs
// Claim: urn:core:crates_rs:core-solvers:solver-spectrum-periodic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn perturbed_generalized_eigenpair_hits_the_production_residual_gate() {
        let stiffness = DMatrix::from_row_slice(2, 2, &[1.0, -1.0, -1.0, 1.0]);
        let whitened = DMatrix::from_row_slice(2, 2, &[2.0, -2.0, -2.0, 2.0]);
        let masses = [0.5, 0.5];
        let perturbed = DVector::from_vec(vec![1.0, 0.1]);
        let error = validate_mode_residuals(
            1,
            &stiffness,
            &masses,
            &whitened,
            2.0,
            &perturbed,
            &perturbed,
            &PeriodicSpectrumPolicy::default(),
        )
        .expect_err("perturbed generalized eigenpair must fail");
        assert!(matches!(
            error,
            PeriodicSpectrumError::GeneralizedResidualExceeded {
                ordered_index: 1,
                ..
            }
        ));
    }

    #[test]
    fn perturbed_whitened_eigenpair_hits_the_independent_residual_gate() {
        let stiffness = DMatrix::from_row_slice(2, 2, &[1.0, -1.0, -1.0, 1.0]);
        let whitened = DMatrix::from_row_slice(2, 2, &[2.0, -2.0, -2.0, 2.0]);
        let masses = [0.5, 0.5];
        let generalized = DVector::from_vec(vec![1.0, -1.0]);
        let perturbed_whitened = DVector::from_vec(vec![1.0, 0.0]);
        let error = validate_mode_residuals(
            1,
            &stiffness,
            &masses,
            &whitened,
            4.0,
            &generalized,
            &perturbed_whitened,
            &PeriodicSpectrumPolicy::default(),
        )
        .expect_err("perturbed whitened eigenpair must fail");
        assert!(matches!(
            error,
            PeriodicSpectrumError::WhitenedResidualExceeded {
                ordered_index: 1,
                ..
            }
        ));
    }

    #[test]
    fn analytic_interval_mismatch_is_returned_as_evidence() {
        let eigenvalues = [0.0, 0.0, 0.0];
        let exact_h = BigRational::new(BigInt::from(1_u8), BigInt::from(10_u8));
        let comparisons = compare_ordered_modes(
            &eigenvalues,
            1,
            0.1,
            &exact_h,
            1.0e-8,
            &NumericalResolutionReceipt {
                whitened_matrix_infinity_norm: 1.0,
                maximum_whitened_residual: 0.0,
                residual_inclusion_radius: 0.0,
                declared_roundoff_guard: 1.0e-12,
                comparison_uncertainty: 1.0e-12,
                hard_condition_ratio: HARD_MAX_CONDITION_RATIO,
                transfer_status: AnalyticTransferStatus::ConditionalUnmechanizedPremise,
            },
            &PeriodicSpectrumPolicy::default(),
        )
        .expect("conditional interval mismatch must not censor numerical evidence");
        assert!(matches!(
            comparisons[1].analytic_scope(),
            OrderedAnalyticScope::InScope {
                location: IntervalLocation::Below,
                ..
            }
        ));
    }

    #[test]
    fn interval_boundary_overlap_is_numerically_unresolved() {
        assert_eq!(resolved_interval_location(1.0, 1.0, 2.0, 1.0e-6), None);
    }

    #[test]
    fn zero_mode_and_extra_zero_gates_are_fail_closed() {
        assert!(matches!(
            validate_spectrum_sanity(&[1.0e-3, 1.0], &PeriodicSpectrumPolicy::default()),
            Err(PeriodicSpectrumError::ZeroModeOutsideTolerance { .. })
        ));
        assert!(matches!(
            validate_spectrum_sanity(&[0.0, 1.0e-12], &PeriodicSpectrumPolicy::default()),
            Err(PeriodicSpectrumError::AdditionalZeroMode { .. })
        ));
    }
}

mod uniform {
    //! Numerical diagnostics for certified uniform spectral refinement towers.
    //!
    //! --- Math Contract:
    //! - Purpose: replay the closed-form spectra used by the cycle/path
    //!   convergence theorems and disclose their finite-precision residuals.
    //! - Inputs: a finite resolution `n` and fixed mode `k`.
    //! - Outputs: [`UniformModeEvidence`] and [`TwoResolutionEvidence`], both
    //!   explicitly numerical evidence.
    //! - Invariants: cycle values use `4 n² sin²(pi k/n)`; cell-centred Neumann
    //!   path values use `4 n² sin²(pi k/(2n))`; theorem domains are checked.
    //! - Failure: invalid modes, non-finite arithmetic, or an analytic error scale
    //!   below the declared f64 resolution are refused with [`RefinementSpectrumError`].
    //! - Numerical status: f64 diagnostic only. It never constructs the structured
    //!   proof-bound `core_types::refinement_tower::ConvergenceCertificate`.
    //! - Authority: every output has `AuthorityEffectLevel::None`.

    use std::f64::consts::PI;

    use core_types::authority_lattice::AuthorityEffectLevel;
    use serde::{Deserialize, Serialize};
    use thiserror::Error;

    /// Schema stamped on uniform finite-shadow numerical evidence.
    pub const UNIFORM_MODE_EVIDENCE_SCHEMA: &str = "core.refinement-uniform-mode-evidence.v1";

    /// Uniform family whose closed-form spectrum is replayed.
    #[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
    #[serde(rename_all = "snake_case")]
    pub enum UniformSpectralFamily {
        /// Periodic cycle, target `(2 pi k)^2`.
        Cycle,
        /// Cell-centred zero-flux path, target `(pi k)^2`.
        CellCenteredNeumannPath,
    }

    /// Finite-precision replay of one exact closed-form mode.
    ///
    /// The evidence has no unchecked deserialization route:
    ///
    /// ```compile_fail
    /// use serde::de::DeserializeOwned;
    /// use core_solvers::solver_spectrum_periodic::UniformModeEvidence;
    /// fn require_deserialize<T: DeserializeOwned>() {}
    /// require_deserialize::<UniformModeEvidence>();
    /// ```
    #[derive(Clone, Debug, PartialEq, Serialize)]
    pub struct UniformModeEvidence {
        schema: String,
        family: UniformSpectralFamily,
        resolution: usize,
        mode_index: usize,
        observed_eigenvalue: f64,
        target_eigenvalue: f64,
        signed_deficit: f64,
        absolute_error: f64,
        analytic_error_bound: f64,
        floating_point_slack: f64,
        within_analytic_bound: bool,
        authority_effect: AuthorityEffectLevel,
    }

    impl UniformModeEvidence {
        pub fn schema(&self) -> &str {
            &self.schema
        }

        pub fn family(&self) -> UniformSpectralFamily {
            self.family
        }

        pub fn resolution(&self) -> usize {
            self.resolution
        }

        pub fn mode_index(&self) -> usize {
            self.mode_index
        }

        pub fn observed_eigenvalue(&self) -> f64 {
            self.observed_eigenvalue
        }

        pub fn target_eigenvalue(&self) -> f64 {
            self.target_eigenvalue
        }

        pub fn signed_deficit(&self) -> f64 {
            self.signed_deficit
        }

        pub fn absolute_error(&self) -> f64 {
            self.absolute_error
        }

        pub fn analytic_error_bound(&self) -> f64 {
            self.analytic_error_bound
        }

        pub fn floating_point_slack(&self) -> f64 {
            self.floating_point_slack
        }

        pub fn within_analytic_bound(&self) -> bool {
            self.within_analytic_bound
        }

        pub fn authority_effect(&self) -> AuthorityEffectLevel {
            self.authority_effect
        }
    }

    /// Numerical comparison of the same fixed mode at two resolutions.
    ///
    /// The evidence has no unchecked deserialization route:
    ///
    /// ```compile_fail
    /// use serde::de::DeserializeOwned;
    /// use core_solvers::solver_spectrum_periodic::TwoResolutionEvidence;
    /// fn require_deserialize<T: DeserializeOwned>() {}
    /// require_deserialize::<TwoResolutionEvidence>();
    /// ```
    #[derive(Clone, Debug, PartialEq, Serialize)]
    pub struct TwoResolutionEvidence {
        family: UniformSpectralFamily,
        mode_index: usize,
        first_resolution: usize,
        second_resolution: usize,
        observed_difference: f64,
        analytic_cauchy_bound: f64,
        floating_point_slack: f64,
        within_analytic_bound: bool,
        authority_effect: AuthorityEffectLevel,
    }

    impl TwoResolutionEvidence {
        pub fn family(&self) -> UniformSpectralFamily {
            self.family
        }

        pub fn mode_index(&self) -> usize {
            self.mode_index
        }

        pub fn resolutions(&self) -> (usize, usize) {
            (self.first_resolution, self.second_resolution)
        }

        pub fn observed_difference(&self) -> f64 {
            self.observed_difference
        }

        pub fn analytic_cauchy_bound(&self) -> f64 {
            self.analytic_cauchy_bound
        }

        pub fn floating_point_slack(&self) -> f64 {
            self.floating_point_slack
        }

        pub fn within_analytic_bound(&self) -> bool {
            self.within_analytic_bound
        }

        pub fn authority_effect(&self) -> AuthorityEffectLevel {
            self.authority_effect
        }
    }

    /// Replays the uniform-cycle mode formula and its proved fixed-mode rate.
    ///
    /// The theorem domain is `n >= 3`, `k < n`, and `n > 2k`. The last condition
    /// chooses the low-frequency representative of the cycle doublet.
    pub fn uniform_cycle_mode(
        resolution: usize,
        mode_index: usize,
    ) -> Result<UniformModeEvidence, RefinementSpectrumError> {
        if resolution < 3 {
            return Err(RefinementSpectrumError::ResolutionTooSmall {
                family: UniformSpectralFamily::Cycle,
                minimum: 3,
                actual: resolution,
            });
        }
        if mode_index >= resolution {
            return Err(RefinementSpectrumError::ModeOutOfRange {
                mode_index,
                resolution,
            });
        }
        if mode_index > 0 && mode_index >= resolution.div_ceil(2) {
            return Err(RefinementSpectrumError::NotLowFrequencyRepresentative {
                mode_index,
                resolution,
            });
        }
        let n = exact_usize_as_f64(resolution)?;
        let k = exact_usize_as_f64(mode_index)?;
        let angle = PI * k / n;
        let observed = 4.0 * n.powi(2) * angle.sin().powi(2);
        let target = (2.0 * PI * k).powi(2);
        let bound = 4.0 * PI.powi(4) * k.powi(4) / (3.0 * n.powi(2));
        mode_evidence(
            UniformSpectralFamily::Cycle,
            resolution,
            mode_index,
            observed,
            target,
            bound,
        )
    }

    /// Replays the cell-centred Neumann-path mode formula and its proved rate.
    ///
    /// This is the `n`-cell, full cell-mass convention. It is not the inconsistent
    /// `(n-1)^2` scaling of an equal-endpoint-mass ordinary path graph.
    pub fn cell_centered_neumann_path_mode(
        resolution: usize,
        mode_index: usize,
    ) -> Result<UniformModeEvidence, RefinementSpectrumError> {
        if resolution < 2 {
            return Err(RefinementSpectrumError::ResolutionTooSmall {
                family: UniformSpectralFamily::CellCenteredNeumannPath,
                minimum: 2,
                actual: resolution,
            });
        }
        if mode_index >= resolution {
            return Err(RefinementSpectrumError::ModeOutOfRange {
                mode_index,
                resolution,
            });
        }
        let n = exact_usize_as_f64(resolution)?;
        let k = exact_usize_as_f64(mode_index)?;
        let angle = PI * k / (2.0 * n);
        let observed = 4.0 * n.powi(2) * angle.sin().powi(2);
        let target = (PI * k).powi(2);
        let bound = PI.powi(4) * k.powi(4) / (12.0 * n.powi(2));
        mode_evidence(
            UniformSpectralFamily::CellCenteredNeumannPath,
            resolution,
            mode_index,
            observed,
            target,
            bound,
        )
    }

    /// Compares two valid resolutions of the same fixed mode.
    ///
    /// Because both uniform eigenvalues approach the common target from below,
    /// their difference is bounded by the larger of their individual deficits.
    pub fn compare_uniform_resolutions(
        family: UniformSpectralFamily,
        mode_index: usize,
        first_resolution: usize,
        second_resolution: usize,
    ) -> Result<TwoResolutionEvidence, RefinementSpectrumError> {
        if first_resolution == second_resolution {
            return Err(RefinementSpectrumError::DistinctResolutionsRequired);
        }
        let first = mode_for_family(family, first_resolution, mode_index)?;
        let second = mode_for_family(family, second_resolution, mode_index)?;
        let observed_difference = (first.observed_eigenvalue - second.observed_eigenvalue).abs();
        let analytic_cauchy_bound = first.analytic_error_bound.max(second.analytic_error_bound);
        let floating_point_slack = first.floating_point_slack + second.floating_point_slack;
        let within_analytic_bound =
            observed_difference <= analytic_cauchy_bound + floating_point_slack;
        Ok(TwoResolutionEvidence {
            family,
            mode_index,
            first_resolution,
            second_resolution,
            observed_difference,
            analytic_cauchy_bound,
            floating_point_slack,
            within_analytic_bound,
            authority_effect: AuthorityEffectLevel::None,
        })
    }

    fn mode_for_family(
        family: UniformSpectralFamily,
        resolution: usize,
        mode_index: usize,
    ) -> Result<UniformModeEvidence, RefinementSpectrumError> {
        match family {
            UniformSpectralFamily::Cycle => uniform_cycle_mode(resolution, mode_index),
            UniformSpectralFamily::CellCenteredNeumannPath => {
                cell_centered_neumann_path_mode(resolution, mode_index)
            }
        }
    }

    fn mode_evidence(
        family: UniformSpectralFamily,
        resolution: usize,
        mode_index: usize,
        observed_eigenvalue: f64,
        target_eigenvalue: f64,
        analytic_error_bound: f64,
    ) -> Result<UniformModeEvidence, RefinementSpectrumError> {
        if !observed_eigenvalue.is_finite()
            || !target_eigenvalue.is_finite()
            || !analytic_error_bound.is_finite()
        {
            return Err(RefinementSpectrumError::NonFiniteComputation);
        }
        let floating_point_slack = 64.0 * f64::EPSILON * target_eigenvalue.abs().max(1.0);
        if mode_index > 0 && analytic_error_bound < floating_point_slack {
            return Err(RefinementSpectrumError::BelowF64Resolution {
                analytic_error_bound,
                floating_point_slack,
            });
        }
        let signed_deficit = target_eigenvalue - observed_eigenvalue;
        let absolute_error = signed_deficit.abs();
        let within_analytic_bound = signed_deficit >= -floating_point_slack
            && absolute_error <= analytic_error_bound + floating_point_slack;
        Ok(UniformModeEvidence {
            schema: UNIFORM_MODE_EVIDENCE_SCHEMA.to_string(),
            family,
            resolution,
            mode_index,
            observed_eigenvalue,
            target_eigenvalue,
            signed_deficit,
            absolute_error,
            analytic_error_bound,
            floating_point_slack,
            within_analytic_bound,
            authority_effect: AuthorityEffectLevel::None,
        })
    }

    fn exact_usize_as_f64(value: usize) -> Result<f64, RefinementSpectrumError> {
        const MAX_EXACT_F64_INTEGER: usize = 1_usize << f64::MANTISSA_DIGITS;
        if value > MAX_EXACT_F64_INTEGER {
            return Err(RefinementSpectrumError::IntegerNotExactlyRepresentable(
                value,
            ));
        }
        Ok(value as f64)
    }

    /// Typed refusals for uniform spectral diagnostics.
    #[derive(Clone, Debug, PartialEq, Error)]
    pub enum RefinementSpectrumError {
        #[error("{family:?} resolution {actual} is below the minimum {minimum}")]
        ResolutionTooSmall {
            family: UniformSpectralFamily,
            minimum: usize,
            actual: usize,
        },
        #[error("mode {mode_index} is outside resolution {resolution}")]
        ModeOutOfRange {
            mode_index: usize,
            resolution: usize,
        },
        #[error("cycle mode {mode_index} at resolution {resolution} is not the low-frequency representative; require n > 2k")]
        NotLowFrequencyRepresentative {
            mode_index: usize,
            resolution: usize,
        },
        #[error("two-resolution evidence requires distinct resolutions")]
        DistinctResolutionsRequired,
        #[error("integer {0} is not represented exactly by f64")]
        IntegerNotExactlyRepresentable(usize),
        #[error("non-finite arithmetic while evaluating a closed-form mode")]
        NonFiniteComputation,
        #[error("analytic error bound {analytic_error_bound:e} is below declared f64 slack {floating_point_slack:e}")]
        BelowF64Resolution {
            analytic_error_bound: f64,
            floating_point_slack: f64,
        },
    }
}
pub use uniform::*;
