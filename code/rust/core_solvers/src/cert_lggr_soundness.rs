//! --- Math Contract:
//! Object: finite-dimensional real LGGR carriers and observer-kernel subspaces.
//! Preconditions: finite inputs with one kernel basis per covering edge.
//! Postconditions: residual-disclosed `f64` numerical estimates only.
//! Authority: None. No estimate, witness, or replay result mints authority.
//! ---
//!
//! Local Green / Global Red soundness: the decidable NEC check.
//!
//! Epoch 19 (`PKT-20260722-RES-EPOCH19`), resolution of proposal 004 obligation
//! O1 (`o1_resolution.md`). Theorem 3 there classifies the carriers on which
//! every sound full-coverage observer family must have trivial joint kernels:
//! exactly those where each edge's **isolation space**
//!
//! ```text
//!     D_iso(e) = { Δ(s)_e : Δ(s)_e' = 0 for every e' ≠ e }
//! ```
//!
//! fills its fiber. `D_iso` is the image of a restricted linear map, so the
//! classification is a rank computation per edge — implemented here.
//!
//! Diagnostic only: a NEC verdict says every sound family over this carrier has
//! trivial kernels; it does not certify any particular family, and no verdict
//! mints authority. Green tests support only the instances they run.

use nalgebra::{DMatrix, DVector};
use serde::{Deserialize, Serialize};
use thiserror::Error;

pub use crate::cert_channel_capacity::{
    hidden_mass_l2_on_subspace, DetectorCapacityError, DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
};

pub use core_epk::lggr_v::{
    check_soundness, verify_unsoundness_witness, LggrSoundnessError, LggrSoundnessReport,
    LGGR_SOUNDNESS_SCHEMA, MAX_LGGR_CELLS,
};

use crate::compliance::SolverError;

/// A finite covering-edge carrier with uniform fiber dimension.
///
/// Edge `(a, b, r)`: lower endpoint `a`, upper endpoint `b`, and the matrix `r`
/// of the restriction `r_{b,a} : F(b) → F(a)` (`dim × dim`). Contractivity is
/// the caller's declaration; it is not verified here because the NEC
/// classification is norm-independent (a statement about subspaces).
#[derive(Debug, Clone, PartialEq)]
pub struct CoveringCarrier {
    /// Number of vertices.
    pub num_vertices: usize,
    /// Fiber dimension (uniform across vertices).
    pub dim: usize,
    /// Edges `(lower, upper, restriction)`.
    pub edges: Vec<(usize, usize, DMatrix<f64>)>,
}

/// Per-edge isolation-space report.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EdgeIsolationReport {
    /// Edge index into `carrier.edges`.
    pub edge: usize,
    /// `dim D_iso(e)`.
    pub isolation_rank: usize,
    /// Fiber dimension; the edge is "full" iff `isolation_rank == fiber_dim`.
    pub fiber_dim: usize,
}

/// Numerical rank threshold used by the finite `f64` routines in this module.
/// This is a disclosed convention, not an exact algebraic threshold.
pub const BLIND_SPOT_NUMERICAL_TOLERANCE: f64 = 1e-9;

/// Replay acceptance threshold for residual-disclosed numerical evidence.
pub const BLIND_SPOT_REPLAY_TOLERANCE: f64 = 1e-7;

/// Literal evidence label carried by every blind-spot output.
pub const BLIND_SPOT_EVIDENCE_KIND: &str = "f64 NumericalEvidence/Estimate";

/// Literal authority ceiling carried by every blind-spot output.
pub const BLIND_SPOT_AUTHORITY: &str = "None";

/// Scope fence for the Courant--Fischer audit-budget floor.
pub const AUDIT_BUDGET_SCOPE: &str = "unrestricted global rank-one linear cuts on the current \
     All-Green section subspace only; edge-local placement is not characterized";

const RANK_TOL: f64 = BLIND_SPOT_NUMERICAL_TOLERANCE;

/// One kernel subspace per covering edge.
///
/// Each matrix has `carrier.dim` rows; its columns span `K_e`. Columns need not
/// be orthonormal or independent. A `dim x 0` matrix denotes the zero kernel.
#[derive(Debug, Clone, PartialEq)]
pub struct ObserverKernelFamily {
    pub edge_bases: Vec<DMatrix<f64>>,
}

impl ObserverKernelFamily {
    pub fn new(edge_bases: Vec<DMatrix<f64>>) -> Self {
        Self { edge_bases }
    }

    /// The family `K_e = {0}` on every edge.
    pub fn zero(carrier: &CoveringCarrier) -> Self {
        Self {
            edge_bases: (0..carrier.edges.len())
                .map(|_| DMatrix::zeros(carrier.dim, 0))
                .collect(),
        }
    }

    /// The family `K_e = F(a_e)` on every edge.
    pub fn full(carrier: &CoveringCarrier) -> Self {
        Self {
            edge_bases: (0..carrier.edges.len())
                .map(|_| DMatrix::identity(carrier.dim, carrier.dim))
                .collect(),
        }
    }
}

/// Typed failures for blind-spot numerical estimates and replay.
#[derive(Debug, Error, Clone, PartialEq)]
pub enum BlindSpotError {
    #[error("invalid covering carrier: {reason:?}")]
    InvalidCarrier { reason: SolverError },

    #[error("dimension product overflow while assembling {stage}")]
    DimensionOverflow { stage: &'static str },

    #[error("kernel count mismatch: expected {expected}, found {found}")]
    KernelCountMismatch { expected: usize, found: usize },

    #[error("kernel basis row mismatch at edge {edge}: expected {expected}, found {found}")]
    KernelRowMismatch {
        edge: usize,
        expected: usize,
        found: usize,
    },

    #[error("kernel basis contains a non-finite entry at edge {edge}, row {row}, col {col}")]
    NonFiniteKernelEntry { edge: usize, row: usize, col: usize },

    #[error("epsilon must be finite and nonnegative, found {epsilon}")]
    InvalidEpsilon { epsilon: f64 },

    #[error("non-finite numerical output while computing {stage}")]
    NonFiniteNumericalOutput { stage: &'static str },

    #[error("numerical witness extraction failed at {stage}")]
    WitnessExtractionFailed { stage: &'static str },

    #[error("replay metadata mismatch for {field}")]
    EvidenceMetadataMismatch { field: &'static str },

    #[error("replay discrete-field mismatch for {field}")]
    EvidenceDiscreteMismatch { field: &'static str },

    #[error("replay shape mismatch for {field}: expected {expected}, found {found}")]
    EvidenceShapeMismatch {
        field: &'static str,
        expected: usize,
        found: usize,
    },

    #[error("replay numerical mismatch for {field}: difference {difference} exceeds tolerance {tolerance}")]
    EvidenceMismatch {
        field: &'static str,
        difference: f64,
        tolerance: f64,
    },

    #[error("recomputed numerical residual {residual} exceeds replay tolerance {tolerance}")]
    ResidualTooLarge { residual: f64, tolerance: f64 },
}

/// Numerical description of `S_AG = Delta^{-1}(product_e K_e)`.
#[derive(Debug, Clone, PartialEq)]
pub struct AllGreenSubspace {
    /// Orthonormal columns spanning the numerically resolved All-Green space.
    pub basis: DMatrix<f64>,
    /// Stacked constraints `(I - P_K_e) Delta_e`; their null space is `S_AG`.
    pub constraint_matrix: DMatrix<f64>,
    /// Numerically resolved dimension of each `K_e`.
    pub kernel_ranks: Vec<usize>,
    /// Frobenius norm of `constraint_matrix * basis`.
    pub constraint_residual: f64,
    /// Frobenius norm of `basis^T basis - I`.
    pub orthonormality_residual: f64,
}

/// A replayable, residual-disclosed numerical witness.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BlindSpotNumericalWitness {
    /// Unit section when `S_AG` is nonzero; otherwise the zero vector.
    pub section: Vec<f64>,
    /// `Delta * section`, in edge-block row order.
    pub defect: Vec<f64>,
    pub section_l2: f64,
    pub defect_l2: f64,
    /// Coordinate `l1` norm over all `edge_count * dim` defect coordinates.
    pub defect_coordinate_l1: f64,
    pub all_green_residual: f64,
}

/// Residuals disclosed with [`HiddenMassL2Estimate`].
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BlindSpotNumericalResiduals {
    pub all_green_basis: f64,
    pub basis_orthonormality: f64,
    pub witness_all_green: f64,
    pub witness_normalization: f64,
    pub top_singular_equation: f64,
    pub capacity_attainment: f64,
    pub max_residual: f64,
}

/// `f64` numerical estimate of the normalized hidden `l2` mass.
/// This is numerical evidence, not an exact value or a certificate.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HiddenMassL2Estimate {
    pub schema: String,
    pub evidence_kind: String,
    pub authority: String,
    pub value: f64,
    pub all_green_dimension: usize,
    pub kernel_ranks: Vec<usize>,
    /// Descending singular values, padded with domain-zero values.
    pub restricted_singular_values: Vec<f64>,
    pub top_singular_multiplicity: usize,
    pub witness: BlindSpotNumericalWitness,
    pub residuals: BlindSpotNumericalResiduals,
    pub rank_tolerance_used: f64,
    pub residual_acceptance_tolerance: f64,
    pub residuals_within_tolerance: bool,
}

/// Coordinate-`l1` sandwich estimates derived from [`HiddenMassL2Estimate`].
/// With `M = edge_count * dim`, the reported bridge is
/// `H2 <= H1 <= sqrt(M) H2`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HiddenMassBoundsEstimate {
    pub schema: String,
    pub evidence_kind: String,
    pub authority: String,
    pub coordinate_count: usize,
    pub upper_factor: f64,
    pub spectral_lower_estimate: f64,
    pub witnessed_lower_estimate: f64,
    pub coordinate_l1_upper_estimate: f64,
    pub witness_lower_inequality_slack: f64,
    pub witness_upper_inequality_slack: f64,
    pub l2_evidence: HiddenMassL2Estimate,
}

/// Courant--Fischer lower floors for unrestricted global rank-one audit cuts.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AuditBudgetFloorEstimate {
    pub schema: String,
    pub evidence_kind: String,
    pub authority: String,
    pub scope: String,
    pub epsilon: f64,
    /// Estimated count when no singular value lies in the disclosed threshold
    /// band; `None` when the f64 comparison is ambiguous.
    pub rank_one_cut_floor_for_at_most_epsilon: Option<usize>,
    /// `# {sigma_i >= epsilon}` when `epsilon > 0`; `None` at zero because
    /// no nonnegative norm can be strictly below zero.
    pub rank_one_cut_floor_for_strictly_below_epsilon: Option<usize>,
    pub near_threshold_count: usize,
    pub restricted_singular_values: Vec<f64>,
    pub initial_hidden_mass_l2_estimate: f64,
    pub unrestricted_global_rank_one_only: bool,
    pub edge_local_placement_characterized: bool,
}

/// Result of deterministic numerical replay. `accepted` never carries authority.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BlindSpotReplayReport {
    pub evidence_kind: String,
    pub authority: String,
    pub accepted: bool,
    pub max_field_difference: f64,
    pub recomputed_max_residual: f64,
    pub tolerance_used: f64,
}

fn validate_carrier_edge(
    carrier: &CoveringCarrier,
    a: usize,
    b: usize,
    r: &DMatrix<f64>,
) -> Result<(), SolverError> {
    let valid_endpoints = a < carrier.num_vertices && b < carrier.num_vertices && a != b;
    let valid_shape = r.nrows() == carrier.dim && r.ncols() == carrier.dim;
    if !valid_endpoints || !valid_shape {
        return Err(SolverError::Infeasible);
    }
    if r.iter().any(|x| !x.is_finite()) {
        return Err(SolverError::NonFiniteInput);
    }
    Ok(())
}

fn validate(carrier: &CoveringCarrier) -> Result<(), SolverError> {
    if carrier.num_vertices == 0 || carrier.dim == 0 || carrier.edges.is_empty() {
        return Err(SolverError::Infeasible);
    }
    for (a, b, r) in &carrier.edges {
        validate_carrier_edge(carrier, *a, *b, r)?;
    }
    Ok(())
}

/// The stacked defect map `Δ : C⁰ → ∏_e F(a_e)` as a dense matrix
/// (rows blocked by edges, columns by vertices).
pub fn build_delta(carrier: &CoveringCarrier) -> DMatrix<f64> {
    let d = carrier.dim;
    let mut delta = DMatrix::zeros(carrier.edges.len() * d, carrier.num_vertices * d);
    for (i, (a, b, r)) in carrier.edges.iter().enumerate() {
        for row in 0..d {
            for col in 0..d {
                delta[(i * d + row, b * d + col)] += r[(row, col)];
            }
            delta[(i * d + row, a * d + row)] -= 1.0;
        }
    }
    delta
}

/// Orthonormal null-space basis (columns) via Gram–Schmidt against the row
/// space. Deterministic; avoids relying on how many rows a thin SVD returns.
fn null_space(m: &DMatrix<f64>) -> DMatrix<f64> {
    let cols = m.ncols();
    // Orthonormalize the rows of m to get a row-space basis.
    let mut row_basis: Vec<DMatrix<f64>> = Vec::new();
    for i in 0..m.nrows() {
        let mut v = DMatrix::from_iterator(cols, 1, m.row(i).iter().cloned());
        for b in &row_basis {
            let proj = (b.transpose() * &v)[(0, 0)];
            v -= b * proj;
        }
        let n = v.norm();
        if n > RANK_TOL {
            row_basis.push(v / n);
        }
    }
    // Complete to an orthonormal basis of R^cols; the completion spans the null space.
    let mut null_cols: Vec<DMatrix<f64>> = Vec::new();
    let mut all = row_basis.clone();
    for k in 0..cols {
        let mut cand = DMatrix::zeros(cols, 1);
        cand[(k, 0)] = 1.0;
        for b in &all {
            let proj = (b.transpose() * &cand)[(0, 0)];
            cand -= b * proj;
        }
        let n = cand.norm();
        if n > RANK_TOL {
            let unit = cand / n;
            all.push(unit.clone());
            null_cols.push(unit);
        }
    }
    if null_cols.is_empty() {
        return DMatrix::zeros(cols, 0);
    }
    let mut out = DMatrix::zeros(cols, null_cols.len());
    for (j, c) in null_cols.iter().enumerate() {
        out.set_column(j, &c.column(0));
    }
    out
}

fn rank_of(m: &DMatrix<f64>) -> usize {
    if m.ncols() == 0 || m.nrows() == 0 {
        return 0;
    }
    let svd = m.clone().svd(false, false);
    let scale = svd.singular_values.iter().cloned().fold(1.0_f64, f64::max);
    svd.singular_values
        .iter()
        .filter(|s| **s > RANK_TOL * scale)
        .count()
}

/// `dim D_iso(e)` for one edge: the rank of the `e`-block of `Δ` restricted to
/// the joint null space of all other blocks.
pub fn edge_isolation_rank(
    carrier: &CoveringCarrier,
    edge: usize,
) -> Result<EdgeIsolationReport, SolverError> {
    validate(carrier)?;
    if edge >= carrier.edges.len() {
        return Err(SolverError::Infeasible);
    }
    let d = carrier.dim;
    let delta = build_delta(carrier);
    let m = carrier.edges.len();

    let other_rows: Vec<usize> = (0..m)
        .filter(|i| *i != edge)
        .flat_map(|i| (i * d)..((i + 1) * d))
        .collect();
    let mut others = DMatrix::zeros(other_rows.len(), delta.ncols());
    for (k, r) in other_rows.iter().enumerate() {
        others.set_row(k, &delta.row(*r));
    }
    let null = null_space(&others);

    let mut block = DMatrix::zeros(d, delta.ncols());
    for row in 0..d {
        block.set_row(row, &delta.row(edge * d + row));
    }
    let image = block * null;
    Ok(EdgeIsolationReport {
        edge,
        isolation_rank: rank_of(&image),
        fiber_dim: d,
    })
}

/// Theorem 3 check: the carrier forces necessity (NEC) iff every edge's
/// isolation space is full. Returns the verdict with the per-edge report.
pub fn nec_check(
    carrier: &CoveringCarrier,
) -> Result<(bool, Vec<EdgeIsolationReport>), SolverError> {
    validate(carrier)?;
    let mut reports = Vec::with_capacity(carrier.edges.len());
    for e in 0..carrier.edges.len() {
        reports.push(edge_isolation_rank(carrier, e)?);
    }
    let nec = reports.iter().all(|r| r.isolation_rank == r.fiber_dim);
    Ok((nec, reports))
}

const HIDDEN_MASS_SCHEMA: &str = "core.lggr.hidden-mass-l2.v1";
const BOUNDS_SCHEMA: &str = "core.lggr.hidden-mass-bounds.v1";
const BUDGET_SCHEMA: &str = "core.lggr.audit-budget-floor.v1";

pub(crate) fn validate_kernels(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
) -> Result<(usize, usize), BlindSpotError> {
    validate(carrier).map_err(|reason| BlindSpotError::InvalidCarrier { reason })?;
    if kernels.edge_bases.len() != carrier.edges.len() {
        return Err(BlindSpotError::KernelCountMismatch {
            expected: carrier.edges.len(),
            found: kernels.edge_bases.len(),
        });
    }
    for (edge, basis) in kernels.edge_bases.iter().enumerate() {
        if basis.nrows() != carrier.dim {
            return Err(BlindSpotError::KernelRowMismatch {
                edge,
                expected: carrier.dim,
                found: basis.nrows(),
            });
        }
        for row in 0..basis.nrows() {
            for col in 0..basis.ncols() {
                if !basis[(row, col)].is_finite() {
                    return Err(BlindSpotError::NonFiniteKernelEntry { edge, row, col });
                }
            }
        }
    }
    let defect_dim =
        carrier
            .edges
            .len()
            .checked_mul(carrier.dim)
            .ok_or(BlindSpotError::DimensionOverflow {
                stage: "defect space",
            })?;
    let section_dim =
        carrier
            .num_vertices
            .checked_mul(carrier.dim)
            .ok_or(BlindSpotError::DimensionOverflow {
                stage: "section space",
            })?;
    Ok((defect_dim, section_dim))
}

fn column_span(generators: &DMatrix<f64>) -> DMatrix<f64> {
    let scale = generators
        .column_iter()
        .map(|column| column.norm())
        .fold(0.0_f64, f64::max);
    if scale == 0.0 {
        return DMatrix::zeros(generators.nrows(), 0);
    }
    let mut basis: Vec<DVector<f64>> = Vec::new();
    for column in generators.column_iter() {
        let mut candidate = column.into_owned();
        for _ in 0..2 {
            for vector in &basis {
                candidate -= vector * vector.dot(&candidate);
            }
        }
        let norm = candidate.norm();
        if norm > RANK_TOL * scale {
            basis.push(candidate / norm);
        }
    }
    let mut out = DMatrix::zeros(generators.nrows(), basis.len());
    for (index, vector) in basis.iter().enumerate() {
        out.set_column(index, vector);
    }
    out
}

/// Construct the numerically resolved All-Green subspace from edge kernels.
pub fn all_green_subspace(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
) -> Result<AllGreenSubspace, BlindSpotError> {
    let (defect_dim, section_dim) = validate_kernels(carrier, kernels)?;
    let delta = build_delta(carrier);
    let mut constraints = DMatrix::zeros(defect_dim, section_dim);
    let mut kernel_ranks = Vec::with_capacity(carrier.edges.len());
    for (edge, generators) in kernels.edge_bases.iter().enumerate() {
        let basis = column_span(generators);
        kernel_ranks.push(basis.ncols());
        let complement =
            DMatrix::<f64>::identity(carrier.dim, carrier.dim) - &basis * basis.transpose();
        let mut block = DMatrix::zeros(carrier.dim, section_dim);
        for row in 0..carrier.dim {
            block.set_row(row, &delta.row(edge * carrier.dim + row));
        }
        let constrained = complement * block;
        for row in 0..carrier.dim {
            constraints.set_row(edge * carrier.dim + row, &constrained.row(row));
        }
    }
    let basis = null_space(&constraints);
    let constraint_residual = (&constraints * &basis).norm();
    let orthonormality_residual = if basis.ncols() == 0 {
        0.0
    } else {
        (basis.transpose() * &basis - DMatrix::identity(basis.ncols(), basis.ncols())).norm()
    };
    Ok(AllGreenSubspace {
        basis,
        constraint_matrix: constraints,
        kernel_ranks,
        constraint_residual,
        orthonormality_residual,
    })
}

fn restricted_spectrum(
    restricted: &DMatrix<f64>,
) -> Result<(Vec<f64>, DMatrix<f64>, usize), BlindSpotError> {
    let dimension = restricted.ncols();
    if dimension == 0 {
        return Ok((Vec::new(), DMatrix::zeros(0, 0), 0));
    }
    let gram = restricted.transpose() * restricted;
    let eigen = nalgebra::SymmetricEigen::new(gram);
    if eigen.eigenvalues.iter().any(|value| !value.is_finite()) {
        return Err(BlindSpotError::NonFiniteNumericalOutput {
            stage: "restricted spectrum",
        });
    }
    let mut indexed: Vec<(usize, f64)> = eigen
        .eigenvalues
        .iter()
        .enumerate()
        .map(|(index, value)| (index, value.max(0.0).sqrt()))
        .collect();
    indexed.sort_by(|left, right| right.1.total_cmp(&left.1));
    let singular_values: Vec<f64> = indexed.iter().map(|(_, value)| *value).collect();
    let top = singular_values[0];
    let cluster_tolerance = RANK_TOL * top.max(1.0);
    let top_indices: Vec<usize> = indexed
        .iter()
        .take_while(|(_, value)| (top - *value).abs() <= cluster_tolerance)
        .map(|(index, _)| *index)
        .collect();
    let mut projector = DMatrix::zeros(dimension, dimension);
    for index in &top_indices {
        let vector = eigen.eigenvectors.column(*index).into_owned();
        projector += &vector * vector.transpose();
    }
    Ok((singular_values, projector, top_indices.len()))
}

fn deterministic_witness(
    basis: &DMatrix<f64>,
    projector: &DMatrix<f64>,
) -> Result<DVector<f64>, BlindSpotError> {
    if basis.ncols() == 0 {
        return Ok(DVector::zeros(basis.nrows()));
    }
    let lifted = basis * projector * basis.transpose();
    for coordinate in 0..lifted.nrows() {
        let mut candidate = lifted.column(coordinate).into_owned();
        let norm = candidate.norm();
        if norm > RANK_TOL {
            candidate /= norm;
            if candidate
                .iter()
                .find(|value| value.abs() > RANK_TOL)
                .is_some_and(|v| *v < 0.0)
            {
                candidate *= -1.0;
            }
            return Ok(candidate);
        }
    }
    Err(BlindSpotError::WitnessExtractionFailed {
        stage: "top subspace",
    })
}

/// Estimate normalized hidden `l2` mass and extract a deterministic witness.
pub fn hidden_mass_l2(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
) -> Result<HiddenMassL2Estimate, BlindSpotError> {
    let all_green = all_green_subspace(carrier, kernels)?;
    let delta = build_delta(carrier);
    let restricted = &delta * &all_green.basis;
    let (singular_values, projector, top_singular_multiplicity) = restricted_spectrum(&restricted)?;
    let value = singular_values.first().copied().unwrap_or(0.0);
    let section = deterministic_witness(&all_green.basis, &projector)?;
    let defect = &delta * &section;
    let section_l2 = section.norm();
    let defect_l2 = defect.norm();
    let defect_coordinate_l1 =
        core_functional::Phi1Functional::unweighted_l1_diagnostic(defect.as_slice());
    let all_green_residual = (&all_green.constraint_matrix * &section).norm();
    let expected_norm = if all_green.basis.ncols() == 0 {
        0.0
    } else {
        1.0
    };
    let witness_normalization = (section_l2 - expected_norm).abs();
    let coefficient = all_green.basis.transpose() * &section;
    let top_singular_equation = if coefficient.is_empty() {
        0.0
    } else {
        let gram = restricted.transpose() * &restricted;
        (&gram * &coefficient - &coefficient * value.powi(2)).norm()
    };
    let capacity_attainment = (defect_l2 - value).abs();
    let max_residual = [
        all_green.constraint_residual,
        all_green.orthonormality_residual,
        all_green_residual,
        witness_normalization,
        top_singular_equation,
        capacity_attainment,
    ]
    .into_iter()
    .fold(0.0_f64, f64::max);
    if [
        value,
        section_l2,
        defect_l2,
        defect_coordinate_l1,
        max_residual,
    ]
    .into_iter()
    .any(|number| !number.is_finite())
    {
        return Err(BlindSpotError::NonFiniteNumericalOutput {
            stage: "hidden mass estimate",
        });
    }
    Ok(HiddenMassL2Estimate {
        schema: HIDDEN_MASS_SCHEMA.to_string(),
        evidence_kind: BLIND_SPOT_EVIDENCE_KIND.to_string(),
        authority: BLIND_SPOT_AUTHORITY.to_string(),
        value,
        all_green_dimension: all_green.basis.ncols(),
        kernel_ranks: all_green.kernel_ranks,
        restricted_singular_values: singular_values,
        top_singular_multiplicity,
        witness: BlindSpotNumericalWitness {
            section: section.iter().copied().collect(),
            defect: defect.iter().copied().collect(),
            section_l2,
            defect_l2,
            defect_coordinate_l1,
            all_green_residual,
        },
        residuals: BlindSpotNumericalResiduals {
            all_green_basis: all_green.constraint_residual,
            basis_orthonormality: all_green.orthonormality_residual,
            witness_all_green: all_green_residual,
            witness_normalization,
            top_singular_equation,
            capacity_attainment,
            max_residual,
        },
        rank_tolerance_used: BLIND_SPOT_NUMERICAL_TOLERANCE,
        residual_acceptance_tolerance: BLIND_SPOT_REPLAY_TOLERANCE,
        residuals_within_tolerance: max_residual <= BLIND_SPOT_REPLAY_TOLERANCE,
    })
}

/// Report the coordinate-`l1` estimate sandwich with `M = edge_count * dim`.
pub fn hidden_mass_bounds(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
) -> Result<HiddenMassBoundsEstimate, BlindSpotError> {
    let coordinate_count =
        carrier
            .edges
            .len()
            .checked_mul(carrier.dim)
            .ok_or(BlindSpotError::DimensionOverflow {
                stage: "l1 sandwich",
            })?;
    let l2_evidence = hidden_mass_l2(carrier, kernels)?;
    let upper_factor = (coordinate_count as f64).sqrt();
    let witnessed = l2_evidence.witness.defect_coordinate_l1;
    Ok(HiddenMassBoundsEstimate {
        schema: BOUNDS_SCHEMA.to_string(),
        evidence_kind: BLIND_SPOT_EVIDENCE_KIND.to_string(),
        authority: BLIND_SPOT_AUTHORITY.to_string(),
        coordinate_count,
        upper_factor,
        spectral_lower_estimate: l2_evidence.value,
        witnessed_lower_estimate: witnessed,
        coordinate_l1_upper_estimate: upper_factor * l2_evidence.value,
        witness_lower_inequality_slack: witnessed - l2_evidence.witness.defect_l2,
        witness_upper_inequality_slack: upper_factor * l2_evidence.witness.defect_l2 - witnessed,
        l2_evidence,
    })
}

/// Compute necessary Courant--Fischer floors for unrestricted global rank-one cuts.
pub fn audit_budget_floor(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
    epsilon: f64,
) -> Result<AuditBudgetFloorEstimate, BlindSpotError> {
    if !epsilon.is_finite() || epsilon < 0.0 {
        return Err(BlindSpotError::InvalidEpsilon { epsilon });
    }
    let evidence = hidden_mass_l2(carrier, kernels)?;
    let values = evidence.restricted_singular_values.clone();
    let near_threshold_count = values
        .iter()
        .filter(|v| {
            (**v - epsilon).abs() <= BLIND_SPOT_REPLAY_TOLERANCE * v.abs().max(epsilon).max(1.0)
        })
        .count();
    let threshold_ambiguous = near_threshold_count > 0;
    Ok(AuditBudgetFloorEstimate {
        schema: BUDGET_SCHEMA.to_string(),
        evidence_kind: BLIND_SPOT_EVIDENCE_KIND.to_string(),
        authority: BLIND_SPOT_AUTHORITY.to_string(),
        scope: AUDIT_BUDGET_SCOPE.to_string(),
        epsilon,
        rank_one_cut_floor_for_at_most_epsilon: (!threshold_ambiguous)
            .then(|| values.iter().filter(|v| **v > epsilon).count()),
        rank_one_cut_floor_for_strictly_below_epsilon: (epsilon > 0.0 && !threshold_ambiguous)
            .then(|| values.iter().filter(|v| **v >= epsilon).count()),
        near_threshold_count,
        restricted_singular_values: values,
        initial_hidden_mass_l2_estimate: evidence.value,
        unrestricted_global_rank_one_only: true,
        edge_local_placement_characterized: false,
    })
}

fn close(expected: f64, found: f64) -> bool {
    (expected - found).abs()
        <= BLIND_SPOT_REPLAY_TOLERANCE * expected.abs().max(found.abs()).max(1.0)
}

fn verify_replay_metadata_and_discrete(
    expected: &HiddenMassL2Estimate,
    evidence: &HiddenMassL2Estimate,
) -> Result<(), BlindSpotError> {
    let header_ok = [
        evidence.schema == HIDDEN_MASS_SCHEMA,
        evidence.evidence_kind == BLIND_SPOT_EVIDENCE_KIND,
        evidence.authority == BLIND_SPOT_AUTHORITY,
    ]
    .into_iter()
    .all(|b| b);
    if !header_ok {
        return Err(BlindSpotError::EvidenceMetadataMismatch { field: "header" });
    }
    let discrete_ok = [
        evidence.all_green_dimension == expected.all_green_dimension,
        evidence.kernel_ranks == expected.kernel_ranks,
        evidence.top_singular_multiplicity == expected.top_singular_multiplicity,
        evidence.residuals_within_tolerance == expected.residuals_within_tolerance,
    ]
    .into_iter()
    .all(|b| b);
    if !discrete_ok {
        return Err(BlindSpotError::EvidenceDiscreteMismatch {
            field: "dimensions",
        });
    }
    Ok(())
}

fn verify_replay_scalar_fields(
    expected: &HiddenMassL2Estimate,
    evidence: &HiddenMassL2Estimate,
) -> Result<f64, BlindSpotError> {
    let mut max_field_difference = 0.0_f64;
    for (field, left, right) in [
        ("value", expected.value, evidence.value),
        (
            "section_l2",
            expected.witness.section_l2,
            evidence.witness.section_l2,
        ),
        (
            "defect_l2",
            expected.witness.defect_l2,
            evidence.witness.defect_l2,
        ),
        (
            "defect_l1",
            expected.witness.defect_coordinate_l1,
            evidence.witness.defect_coordinate_l1,
        ),
        (
            "witness_all_green_residual",
            expected.witness.all_green_residual,
            evidence.witness.all_green_residual,
        ),
        (
            "all_green_basis_residual",
            expected.residuals.all_green_basis,
            evidence.residuals.all_green_basis,
        ),
        (
            "basis_orthonormality_residual",
            expected.residuals.basis_orthonormality,
            evidence.residuals.basis_orthonormality,
        ),
        (
            "witness_all_green_residual_disclosed",
            expected.residuals.witness_all_green,
            evidence.residuals.witness_all_green,
        ),
        (
            "witness_normalization_residual",
            expected.residuals.witness_normalization,
            evidence.residuals.witness_normalization,
        ),
        (
            "top_singular_equation_residual",
            expected.residuals.top_singular_equation,
            evidence.residuals.top_singular_equation,
        ),
        (
            "capacity_attainment_residual",
            expected.residuals.capacity_attainment,
            evidence.residuals.capacity_attainment,
        ),
        (
            "rank_tolerance_used",
            expected.rank_tolerance_used,
            evidence.rank_tolerance_used,
        ),
        (
            "residual_acceptance_tolerance",
            expected.residual_acceptance_tolerance,
            evidence.residual_acceptance_tolerance,
        ),
        (
            "max_residual",
            expected.residuals.max_residual,
            evidence.residuals.max_residual,
        ),
    ] {
        let difference = (left - right).abs();
        max_field_difference = max_field_difference.max(difference);
        if !close(left, right) {
            return Err(BlindSpotError::EvidenceMismatch {
                field,
                difference,
                tolerance: BLIND_SPOT_REPLAY_TOLERANCE,
            });
        }
    }
    Ok(max_field_difference)
}

fn verify_replay_vector_fields(
    expected: &HiddenMassL2Estimate,
    evidence: &HiddenMassL2Estimate,
    mut max_field_difference: f64,
) -> Result<f64, BlindSpotError> {
    for (field, left, right) in [
        (
            "singular_values",
            &expected.restricted_singular_values,
            &evidence.restricted_singular_values,
        ),
        (
            "section",
            &expected.witness.section,
            &evidence.witness.section,
        ),
        ("defect", &expected.witness.defect, &evidence.witness.defect),
    ] {
        if left.len() != right.len() {
            return Err(BlindSpotError::EvidenceShapeMismatch {
                field,
                expected: left.len(),
                found: right.len(),
            });
        }
        for (left_value, right_value) in left.iter().zip(right) {
            let difference = (*left_value - *right_value).abs();
            max_field_difference = max_field_difference.max(difference);
            if !close(*left_value, *right_value) {
                return Err(BlindSpotError::EvidenceMismatch {
                    field,
                    difference,
                    tolerance: BLIND_SPOT_REPLAY_TOLERANCE,
                });
            }
        }
    }
    Ok(max_field_difference)
}

/// Deterministically recompute evidence; out-of-tolerance field changes fail.
pub fn verify_hidden_mass_l2_replay(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
    evidence: &HiddenMassL2Estimate,
) -> Result<BlindSpotReplayReport, BlindSpotError> {
    let expected = hidden_mass_l2(carrier, kernels)?;
    verify_replay_metadata_and_discrete(&expected, evidence)?;
    let max_scalar_diff = verify_replay_scalar_fields(&expected, evidence)?;
    let max_field_difference =
        verify_replay_vector_fields(&expected, evidence, max_scalar_diff)?;
    if expected.residuals.max_residual > BLIND_SPOT_REPLAY_TOLERANCE {
        return Err(BlindSpotError::ResidualTooLarge {
            residual: expected.residuals.max_residual,
            tolerance: BLIND_SPOT_REPLAY_TOLERANCE,
        });
    }
    Ok(BlindSpotReplayReport {
        evidence_kind: BLIND_SPOT_EVIDENCE_KIND.to_string(),
        authority: BLIND_SPOT_AUTHORITY.to_string(),
        accepted: true,
        max_field_difference,
        recomputed_max_residual: expected.residuals.max_residual,
        tolerance_used: BLIND_SPOT_REPLAY_TOLERANCE,
    })
}

// Origin: engine/crates_rs/core_solvers/src/cert_lggr_soundness.rs
// Claim: urn:core:crates_rs:core-solvers:cert-lggr-soundness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn refuses_malformed_carriers() {
        let empty = CoveringCarrier {
            num_vertices: 0,
            dim: 2,
            edges: vec![],
        };
        assert!(nec_check(&empty).is_err());
        let self_loop = CoveringCarrier {
            num_vertices: 2,
            dim: 1,
            edges: vec![(0, 0, DMatrix::identity(1, 1))],
        };
        assert!(nec_check(&self_loop).is_err());
    }

    #[test]
    fn exact_soundness_delegates_to_omega_epk() {
        use linear_algebra::backend::basic_matrix::BasicMatrix;
        use num_bigint::BigInt;
        use num_rational::BigRational;

        let r = |n: i64, d: i64| BigRational::new(BigInt::from(n), BigInt::from(d));
        let d =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let q = BasicMatrix::from_row_major(1, 2, vec![r(1, 1), r(-1, 1)]).unwrap();

        let report = check_soundness(&d, &q).unwrap();
        assert!(!report.is_sound());
        assert_eq!(report.d_rank, 2);
        assert_eq!(report.qd_rank, 1);
        let witness = report.witness.as_ref().unwrap();
        assert!(verify_unsoundness_witness(&d, &q, witness).unwrap());
    }
}
