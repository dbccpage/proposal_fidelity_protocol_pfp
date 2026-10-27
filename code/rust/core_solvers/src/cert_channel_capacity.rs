//! --- Math Contract:
//! Object: `||Delta|_(S_AG ∩ span(D))||_(2 -> 2)` for finite real coordinates.
//! Preconditions: valid covering carrier, observer kernels, and nonzero protected directions.
//! Postconditions: deterministic f64 estimate with full residual disclosure.
//! Authority: None. This is NumericalEvidence, not the open exact BSC-CERT.
//! ---

use nalgebra::{DMatrix, DVector};
use core_types::{
    detector_magnitude_is_in_policy, DetectorAdequacyDtoError, DetectorCapacityEvidence,
    DetectorCapacityResiduals, DetectorCapacityWitness, DetectorDeploymentDeclaration,
    DETECTOR_CAPACITY_RANK_TOLERANCE, DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
};
pub use core_types::{
    DETECTOR_CAPACITY_COMPARISON_TOLERANCE, MAX_DETECTOR_SAFE_MAGNITUDE,
    MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE,
};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::cert_lggr_soundness::{
    all_green_subspace, build_delta, validate_kernels, AllGreenSubspace, BlindSpotError,
    CoveringCarrier, ObserverKernelFamily, BLIND_SPOT_NUMERICAL_TOLERANCE,
};

pub const MAX_DETECTOR_PROTECTED_DIRECTIONS: usize = 4_096;
pub const MAX_DETECTOR_SECTION_DIMENSION: usize = 8_192;
pub const MAX_DETECTOR_MATRIX_CELLS: usize = 16_777_216;
pub const MAX_DETECTOR_CARRIER_RESTRICTION_CELLS: usize = 1_048_576;
pub const MAX_DETECTOR_KERNEL_GENERATOR_CELLS: usize = 1_048_576;
pub const MAX_DETECTOR_PROTECTED_DIRECTION_COORDINATES: usize = 1_048_576;

#[derive(Debug, Clone, PartialEq, Error)]
pub enum DetectorCapacityError {
    #[error(transparent)]
    BlindSpot(#[from] BlindSpotError),
    #[error(transparent)]
    EvidenceDto(#[from] DetectorAdequacyDtoError),
    #[error("protected distinction set D is empty")]
    EmptyProtectedDistinctions,
    #[error("protected direction {distinction_id:?} is empty or exactly all-zero")]
    EmptyProtectedDirection { distinction_id: String },
    #[error(
        "protected direction {distinction_id:?} has {found} rows; section space has {expected}"
    )]
    ProtectedDirectionRowMismatch {
        distinction_id: String,
        expected: usize,
        found: usize,
    },
    #[error("duplicate protected distinction id {distinction_id:?}")]
    DuplicateProtectedDistinction { distinction_id: String },
    #[error("protected direction {distinction_id:?} has a non-finite l2 norm")]
    NonFiniteProtectedDirectionNorm { distinction_id: String },
    #[error(
        "detector capacity resource limit exceeded for {resource}: found {found}, limit {limit}"
    )]
    ResourceLimitExceeded {
        resource: &'static str,
        found: usize,
        limit: usize,
    },
    #[error("dimension product overflow while allocating {resource}")]
    DimensionOverflow { resource: &'static str },
    #[error("non-finite numerical output while computing {stage}")]
    NonFiniteNumericalOutput { stage: &'static str },
    #[error("could not extract a deterministic top-singular witness")]
    WitnessExtractionFailed,
    #[error("capacity-model digest mismatch: declared {declared}, recomputed {recomputed}")]
    CapacityModelDigestMismatch {
        declared: String,
        recomputed: String,
    },
    #[error("non-finite detector-capacity input in {resource}: {value}")]
    NonFiniteInput { resource: &'static str, value: f64 },
    #[error(
        "numerically unsafe finite magnitude in {resource}: {value}; nonzero values must be in [{min_nonzero}, {max}]"
    )]
    NumericallyUnsafeMagnitude {
        resource: &'static str,
        value: f64,
        min_nonzero: f64,
        max: f64,
    },
}

fn digest_usize(hasher: &mut Sha256, value: usize) {
    hasher.update((value as u128).to_le_bytes());
}

fn digest_matrix(hasher: &mut Sha256, matrix: &DMatrix<f64>) {
    digest_usize(hasher, matrix.nrows());
    digest_usize(hasher, matrix.ncols());
    for row in 0..matrix.nrows() {
        for col in 0..matrix.ncols() {
            hasher.update(matrix[(row, col)].to_bits().to_le_bytes());
        }
    }
}

/// Canonical SHA-256 binding for the exact finite carrier and kernel-family bits.
///
/// Edge and kernel order are semantic because kernel `i` belongs to covering edge
/// `i`. Matrix entries are encoded row-major with exact IEEE-754 bit patterns.
pub fn detector_capacity_model_digest(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
) -> Result<String, DetectorCapacityError> {
    validate_raw_capacity_model_limits(carrier, kernels)?;
    validate_capacity_model_magnitudes(carrier, kernels)?;
    validate_kernels(carrier, kernels)?;
    let mut hasher = Sha256::new();
    hasher.update(b"core.epk.detector-capacity-model.v1\0");
    digest_usize(&mut hasher, carrier.num_vertices);
    digest_usize(&mut hasher, carrier.dim);
    digest_usize(&mut hasher, carrier.edges.len());
    for (lower, upper, restriction) in &carrier.edges {
        digest_usize(&mut hasher, *lower);
        digest_usize(&mut hasher, *upper);
        digest_matrix(&mut hasher, restriction);
    }
    digest_usize(&mut hasher, kernels.edge_bases.len());
    for basis in &kernels.edge_bases {
        digest_matrix(&mut hasher, basis);
    }
    let digest = hasher.finalize();
    let mut encoded = String::with_capacity(digest.len() * 2);
    for byte in digest {
        use std::fmt::Write as _;
        let _ = write!(&mut encoded, "{byte:02x}");
    }
    Ok(encoded)
}

fn validate_raw_capacity_model_limits(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
) -> Result<(), DetectorCapacityError> {
    let restriction_cells =
        carrier
            .edges
            .iter()
            .try_fold(0usize, |total, (_, _, restriction)| {
                total.checked_add(restriction.len()).ok_or(
                    DetectorCapacityError::DimensionOverflow {
                        resource: "carrier restriction cells",
                    },
                )
            })?;
    if restriction_cells > MAX_DETECTOR_CARRIER_RESTRICTION_CELLS {
        return Err(DetectorCapacityError::ResourceLimitExceeded {
            resource: "actual carrier restriction cells",
            found: restriction_cells,
            limit: MAX_DETECTOR_CARRIER_RESTRICTION_CELLS,
        });
    }
    let kernel_generator_cells = kernels.edge_bases.iter().try_fold(0usize, |total, basis| {
        let cells = basis.nrows().checked_mul(basis.ncols()).ok_or(
            DetectorCapacityError::DimensionOverflow {
                resource: "kernel generator cells",
            },
        )?;
        total
            .checked_add(cells)
            .ok_or(DetectorCapacityError::DimensionOverflow {
                resource: "kernel generator cells",
            })
    })?;
    if kernel_generator_cells > MAX_DETECTOR_KERNEL_GENERATOR_CELLS {
        return Err(DetectorCapacityError::ResourceLimitExceeded {
            resource: "actual kernel generator cells",
            found: kernel_generator_cells,
            limit: MAX_DETECTOR_KERNEL_GENERATOR_CELLS,
        });
    }
    Ok(())
}

fn validate_capacity_model_magnitudes(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
) -> Result<(), DetectorCapacityError> {
    for (_, _, restriction) in &carrier.edges {
        for value in restriction.iter().copied() {
            validate_safe_magnitude(value, "carrier restriction entry")?;
        }
    }
    for basis in &kernels.edge_bases {
        for value in basis.iter().copied() {
            validate_safe_magnitude(value, "kernel generator entry")?;
        }
    }
    Ok(())
}

fn validate_raw_payload_limits(
    kernels: &ObserverKernelFamily,
    declaration: &DetectorDeploymentDeclaration,
) -> Result<(), DetectorCapacityError> {
    let kernel_generator_cells = kernels.edge_bases.iter().try_fold(0usize, |total, basis| {
        let cells = basis.nrows().checked_mul(basis.ncols()).ok_or(
            DetectorCapacityError::DimensionOverflow {
                resource: "kernel generator cells",
            },
        )?;
        total
            .checked_add(cells)
            .ok_or(DetectorCapacityError::DimensionOverflow {
                resource: "kernel generator cells",
            })
    })?;
    if kernel_generator_cells > MAX_DETECTOR_KERNEL_GENERATOR_CELLS {
        return Err(DetectorCapacityError::ResourceLimitExceeded {
            resource: "actual kernel generator cells",
            found: kernel_generator_cells,
            limit: MAX_DETECTOR_KERNEL_GENERATOR_CELLS,
        });
    }
    let protected_coordinates =
        declaration
            .protected_distinctions()
            .iter()
            .try_fold(0usize, |total, distinction| {
                total
                    .checked_add(distinction.section_direction().len())
                    .ok_or(DetectorCapacityError::DimensionOverflow {
                        resource: "protected direction coordinates",
                    })
            })?;
    if protected_coordinates > MAX_DETECTOR_PROTECTED_DIRECTION_COORDINATES {
        return Err(DetectorCapacityError::ResourceLimitExceeded {
            resource: "actual protected direction coordinates",
            found: protected_coordinates,
            limit: MAX_DETECTOR_PROTECTED_DIRECTION_COORDINATES,
        });
    }
    Ok(())
}

fn validate_safe_magnitude(
    value: f64,
    resource: &'static str,
) -> Result<(), DetectorCapacityError> {
    if !value.is_finite() {
        return Err(DetectorCapacityError::NonFiniteInput { resource, value });
    }
    if !detector_magnitude_is_in_policy(value) {
        return Err(DetectorCapacityError::NumericallyUnsafeMagnitude {
            resource,
            value,
            min_nonzero: MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE,
            max: MAX_DETECTOR_SAFE_MAGNITUDE,
        });
    }
    Ok(())
}

fn validate_model_magnitudes(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
    declaration: &DetectorDeploymentDeclaration,
) -> Result<(), DetectorCapacityError> {
    for (_, _, restriction) in &carrier.edges {
        for value in restriction.iter().copied() {
            validate_safe_magnitude(value, "carrier restriction entry")?;
        }
    }
    for basis in &kernels.edge_bases {
        for value in basis.iter().copied() {
            validate_safe_magnitude(value, "kernel generator entry")?;
        }
    }
    for distinction in declaration.protected_distinctions() {
        for value in distinction.section_direction().iter().copied() {
            validate_safe_magnitude(value, "protected direction coordinate")?;
        }
    }
    Ok(())
}
fn stable_l2(values: &[f64]) -> f64 {
    let scale = values
        .iter()
        .map(|value| value.abs())
        .fold(0.0_f64, f64::max);
    if scale == 0.0 {
        return 0.0;
    }
    scale
        * values
            .iter()
            .map(|value| (value / scale).powi(2))
            .sum::<f64>()
            .sqrt()
}

fn orthonormal_span(generators: &DMatrix<f64>) -> DMatrix<f64> {
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
        if norm > BLIND_SPOT_NUMERICAL_TOLERANCE * scale {
            basis.push(candidate / norm);
        }
    }
    let mut out = DMatrix::zeros(generators.nrows(), basis.len());
    for (index, vector) in basis.iter().enumerate() {
        out.set_column(index, vector);
    }
    out
}

fn null_space(matrix: &DMatrix<f64>) -> DMatrix<f64> {
    let columns = matrix.ncols();
    let mut row_basis: Vec<DVector<f64>> = Vec::new();
    for row in matrix.row_iter() {
        let mut candidate = DVector::from_iterator(columns, row.iter().copied());
        for _ in 0..2 {
            for vector in &row_basis {
                candidate -= vector * vector.dot(&candidate);
            }
        }
        let norm = candidate.norm();
        if norm > BLIND_SPOT_NUMERICAL_TOLERANCE {
            row_basis.push(candidate / norm);
        }
    }
    let mut all = row_basis;
    let mut null_basis = Vec::new();
    for coordinate in 0..columns {
        let mut candidate = DVector::zeros(columns);
        candidate[coordinate] = 1.0;
        for _ in 0..2 {
            for vector in &all {
                candidate -= vector * vector.dot(&candidate);
            }
        }
        let norm = candidate.norm();
        if norm > BLIND_SPOT_NUMERICAL_TOLERANCE {
            let unit = candidate / norm;
            all.push(unit.clone());
            null_basis.push(unit);
        }
    }
    let mut out = DMatrix::zeros(columns, null_basis.len());
    for (index, vector) in null_basis.iter().enumerate() {
        out.set_column(index, vector);
    }
    out
}

fn intersection_basis(all_green: &DMatrix<f64>, protected: &DMatrix<f64>) -> (DMatrix<f64>, f64) {
    if all_green.ncols() == 0 || protected.ncols() == 0 {
        return (DMatrix::zeros(all_green.nrows(), 0), 0.0);
    }
    let mut matching = DMatrix::zeros(all_green.nrows(), all_green.ncols() + protected.ncols());
    matching
        .view_mut((0, 0), (all_green.nrows(), all_green.ncols()))
        .copy_from(all_green);
    matching
        .view_mut(
            (0, all_green.ncols()),
            (protected.nrows(), protected.ncols()),
        )
        .copy_from(&(-protected));
    let relations = null_space(&matching);
    let construction_residual = (&matching * &relations).norm();
    let all_green_coefficients = relations
        .view((0, 0), (all_green.ncols(), relations.ncols()))
        .into_owned();
    let raw = all_green * all_green_coefficients;
    (orthonormal_span(&raw), construction_residual)
}

fn restricted_spectrum(
    restricted: &DMatrix<f64>,
) -> Result<(Vec<f64>, DMatrix<f64>), DetectorCapacityError> {
    if restricted.ncols() == 0 {
        return Ok((Vec::new(), DMatrix::zeros(0, 0)));
    }
    if restricted.iter().any(|value| !value.is_finite()) {
        return Err(DetectorCapacityError::NonFiniteNumericalOutput {
            stage: "restricted matrix",
        });
    }
    let gram = restricted.transpose() * restricted;
    if gram.iter().any(|value| !value.is_finite()) {
        return Err(DetectorCapacityError::NonFiniteNumericalOutput {
            stage: "restricted Gram matrix",
        });
    }
    let eigen = nalgebra::SymmetricEigen::new(gram);
    if eigen.eigenvalues.iter().any(|value| !value.is_finite()) {
        return Err(DetectorCapacityError::NonFiniteNumericalOutput {
            stage: "restricted eigensystem",
        });
    }
    let mut indexed: Vec<_> = eigen
        .eigenvalues
        .iter()
        .enumerate()
        .map(|(index, value)| (index, value.max(0.0).sqrt()))
        .collect();
    indexed.sort_by(|left, right| right.1.total_cmp(&left.1));
    let singular_values: Vec<_> = indexed.iter().map(|(_, value)| *value).collect();
    let top = singular_values[0];
    let cluster_tolerance = BLIND_SPOT_NUMERICAL_TOLERANCE * top.max(1.0);
    let mut projector = DMatrix::zeros(restricted.ncols(), restricted.ncols());
    for (index, value) in indexed {
        if (top - value).abs() <= cluster_tolerance {
            let vector = eigen.eigenvectors.column(index).into_owned();
            projector += &vector * vector.transpose();
        }
    }
    Ok((singular_values, projector))
}

fn deterministic_witness(
    basis: &DMatrix<f64>,
    projector: &DMatrix<f64>,
) -> Result<DVector<f64>, DetectorCapacityError> {
    if basis.ncols() == 0 {
        return Ok(DVector::zeros(basis.nrows()));
    }
    let lifted = basis * projector * basis.transpose();
    for coordinate in 0..lifted.nrows() {
        let mut candidate = lifted.column(coordinate).into_owned();
        let norm = candidate.norm();
        if norm > BLIND_SPOT_NUMERICAL_TOLERANCE {
            candidate /= norm;
            if candidate
                .iter()
                .find(|value| value.abs() > BLIND_SPOT_NUMERICAL_TOLERANCE)
                .is_some_and(|value| *value < 0.0)
            {
                candidate *= -1.0;
            }
            return Ok(candidate);
        }
    }
    Err(DetectorCapacityError::WitnessExtractionFailed)
}

fn check_bounded_product(
    a: usize,
    b: usize,
    overflow_resource: &'static str,
    limit_resource: &'static str,
    limit: usize,
) -> Result<usize, DetectorCapacityError> {
    let prod = a
        .checked_mul(b)
        .ok_or(DetectorCapacityError::DimensionOverflow {
            resource: overflow_resource,
        })?;
    if prod > limit {
        return Err(DetectorCapacityError::ResourceLimitExceeded {
            resource: limit_resource,
            found: prod,
            limit,
        });
    }
    Ok(prod)
}

fn validate_capacity_resource_limits(
    carrier: &CoveringCarrier,
    distinctions_len: usize,
) -> Result<(), DetectorCapacityError> {
    if distinctions_len > MAX_DETECTOR_PROTECTED_DIRECTIONS {
        return Err(DetectorCapacityError::ResourceLimitExceeded {
            resource: "protected direction count",
            found: distinctions_len,
            limit: MAX_DETECTOR_PROTECTED_DIRECTIONS,
        });
    }
    let declared_section_dimension = check_bounded_product(
        carrier.num_vertices,
        carrier.dim,
        "section dimension",
        "section dimension",
        MAX_DETECTOR_SECTION_DIMENSION,
    )?;
    let edge_coordinate_rows = check_bounded_product(
        carrier.edges.len(),
        carrier.dim,
        "edge-coordinate rows",
        "edge-coordinate rows",
        MAX_DETECTOR_MATRIX_CELLS,
    )?;
    check_bounded_product(
        edge_coordinate_rows,
        declared_section_dimension,
        "All-Green constraint matrix",
        "All-Green constraint matrix cells",
        MAX_DETECTOR_MATRIX_CELLS,
    )?;
    check_bounded_product(
        declared_section_dimension,
        declared_section_dimension,
        "section-space square matrix",
        "section-space square matrix cells",
        MAX_DETECTOR_MATRIX_CELLS,
    )?;
    check_bounded_product(
        declared_section_dimension,
        distinctions_len,
        "protected direction matrix",
        "protected direction matrix cells",
        MAX_DETECTOR_MATRIX_CELLS,
    )?;
    Ok(())
}

fn validate_single_distinction_direction<'a>(
    distinction: &'a core_types::ProtectedDistinctionDeclaration,
    section_dimension: usize,
    seen: &mut std::collections::BTreeSet<&'a str>,
) -> Result<(&'a [f64], f64), DetectorCapacityError> {
    if !seen.insert(distinction.distinction_id()) {
        return Err(DetectorCapacityError::DuplicateProtectedDistinction {
            distinction_id: distinction.distinction_id().to_string(),
        });
    }
    let direction = distinction.section_direction();
    if direction.len() != section_dimension {
        return Err(DetectorCapacityError::ProtectedDirectionRowMismatch {
            distinction_id: distinction.distinction_id().to_string(),
            expected: section_dimension,
            found: direction.len(),
        });
    }
    let norm = stable_l2(direction);
    if !norm.is_finite() {
        return Err(DetectorCapacityError::NonFiniteProtectedDirectionNorm {
            distinction_id: distinction.distinction_id().to_string(),
        });
    }
    if direction.iter().all(|value| *value == 0.0) {
        return Err(DetectorCapacityError::EmptyProtectedDirection {
            distinction_id: distinction.distinction_id().to_string(),
        });
    }
    Ok((direction, norm))
}

fn build_protected_directions(
    distinctions: &[core_types::ProtectedDistinctionDeclaration],
    section_dimension: usize,
) -> Result<DMatrix<f64>, DetectorCapacityError> {
    let mut seen = std::collections::BTreeSet::new();
    let mut directions = DMatrix::zeros(section_dimension, distinctions.len());
    for (column, distinction) in distinctions.iter().enumerate() {
        let (direction, norm) =
            validate_single_distinction_direction(distinction, section_dimension, &mut seen)?;
        for (row, value) in direction.iter().enumerate() {
            directions[(row, column)] = *value / norm;
        }
    }
    Ok(orthonormal_span(&directions))
}

fn orthonormality_defect(mat: &DMatrix<f64>) -> f64 {
    if mat.ncols() == 0 {
        0.0
    } else {
        (mat.transpose() * mat - DMatrix::identity(mat.ncols(), mat.ncols())).norm()
    }
}

fn compute_intersection_subspace(
    all_green: &AllGreenSubspace,
    protected: &DMatrix<f64>,
    section_dimension: usize,
) -> Result<(DMatrix<f64>, f64, f64, f64, f64), DetectorCapacityError> {
    let matching_columns = all_green
        .basis
        .ncols()
        .checked_add(protected.ncols())
        .ok_or(DetectorCapacityError::DimensionOverflow {
            resource: "intersection matching columns",
        })?;
    check_bounded_product(
        section_dimension,
        matching_columns,
        "intersection matching matrix",
        "intersection matching matrix cells",
        MAX_DETECTOR_MATRIX_CELLS,
    )?;
    let (intersection, intersection_construction) = intersection_basis(&all_green.basis, protected);
    let identity = DMatrix::identity(section_dimension, section_dimension);
    let all_green_projector = &all_green.basis * all_green.basis.transpose();
    let protected_projector = protected * protected.transpose();
    let intersection_all_green = ((&identity - all_green_projector) * &intersection).norm();
    let intersection_protected = ((&identity - &protected_projector) * &intersection).norm();
    let intersection_orthonormality = orthonormality_defect(&intersection);
    Ok((
        intersection,
        intersection_construction,
        intersection_all_green,
        intersection_protected,
        intersection_orthonormality,
    ))
}

#[allow(clippy::too_many_arguments)]
fn evaluate_capacity_witness(
    carrier: &CoveringCarrier,
    all_green: &AllGreenSubspace,
    protected: &DMatrix<f64>,
    intersection: &DMatrix<f64>,
    protected_span_basis: f64,
    intersection_construction: f64,
    intersection_all_green: f64,
    intersection_protected: f64,
    intersection_orthonormality: f64,
) -> Result<
    (
        f64,
        Vec<f64>,
        DetectorCapacityWitness,
        DetectorCapacityResiduals,
    ),
    DetectorCapacityError,
> {
    let section_dimension = all_green.basis.nrows();
    let identity = DMatrix::identity(section_dimension, section_dimension);
    let protected_projector = protected * protected.transpose();
    let delta = build_delta(carrier);
    let restricted = &delta * intersection;
    let (singular_values, projector) = restricted_spectrum(&restricted)?;
    let value = singular_values.first().copied().unwrap_or(0.0);
    let section = deterministic_witness(intersection, &projector)?;
    let defect = &delta * &section;
    let expected_norm = if intersection.ncols() == 0 { 0.0 } else { 1.0 };
    let witness_normalization = (section.norm() - expected_norm).abs();
    let witness_all_green = (&all_green.constraint_matrix * &section).norm();
    let witness_protected = ((&identity - protected_projector) * &section).norm();
    let coefficient = intersection.transpose() * &section;
    let top_singular_equation = if coefficient.is_empty() {
        0.0
    } else {
        (restricted.transpose() * &restricted * &coefficient - coefficient * value.powi(2)).norm()
    };
    let capacity_attainment = (defect.norm() - value).abs();
    let residuals = DetectorCapacityResiduals::new(
        all_green.constraint_residual,
        all_green.orthonormality_residual,
        protected_span_basis,
        intersection_construction,
        intersection_all_green,
        intersection_protected,
        intersection_orthonormality,
        witness_all_green,
        witness_protected,
        witness_normalization,
        top_singular_equation,
        capacity_attainment,
    )?;
    let witness = DetectorCapacityWitness::new(
        section.iter().copied().collect(),
        defect.iter().copied().collect(),
    )?;
    if !value.is_finite() || !residuals.max_residual().is_finite() {
        return Err(DetectorCapacityError::NonFiniteNumericalOutput {
            stage: "restricted detector capacity",
        });
    }
    Ok((value, singular_values, witness, residuals))
}

fn validate_declaration_and_digest(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
    declaration: &DetectorDeploymentDeclaration,
) -> Result<String, DetectorCapacityError> {
    let distinctions = declaration.protected_distinctions();
    if distinctions.is_empty() {
        return Err(DetectorCapacityError::EmptyProtectedDistinctions);
    }
    validate_raw_payload_limits(kernels, declaration)?;
    let recomputed_model_digest = detector_capacity_model_digest(carrier, kernels)?;
    if declaration.capacity_model_digest() != recomputed_model_digest {
        return Err(DetectorCapacityError::CapacityModelDigestMismatch {
            declared: declaration.capacity_model_digest().to_string(),
            recomputed: recomputed_model_digest,
        });
    }
    validate_model_magnitudes(carrier, kernels, declaration)?;
    validate_capacity_resource_limits(carrier, distinctions.len())?;
    Ok(recomputed_model_digest)
}

/// Estimate hidden l2 mass on the protected All-Green subspace.
pub fn hidden_mass_l2_on_subspace(
    carrier: &CoveringCarrier,
    kernels: &ObserverKernelFamily,
    declaration: &DetectorDeploymentDeclaration,
) -> Result<DetectorCapacityEvidence, DetectorCapacityError> {
    let recomputed_model_digest = validate_declaration_and_digest(carrier, kernels, declaration)?;
    let all_green = all_green_subspace(carrier, kernels)?;
    let section_dimension = all_green.basis.nrows();
    let protected =
        build_protected_directions(declaration.protected_distinctions(), section_dimension)?;
    let protected_span_basis = orthonormality_defect(&protected);
    let (
        intersection,
        intersection_construction,
        intersection_all_green,
        intersection_protected,
        intersection_orthonormality,
    ) = compute_intersection_subspace(&all_green, &protected, section_dimension)?;
    let (value, singular_values, witness, residuals) = evaluate_capacity_witness(
        carrier,
        &all_green,
        &protected,
        &intersection,
        protected_span_basis,
        intersection_construction,
        intersection_all_green,
        intersection_protected,
        intersection_orthonormality,
    )?;
    Ok(DetectorCapacityEvidence::from_f64_numerical_estimate(
        recomputed_model_digest,
        declaration.protected_subspace_digest(),
        value,
        declaration.epsilon(),
        all_green.basis.ncols(),
        protected.ncols(),
        intersection.ncols(),
        singular_values,
        witness,
        residuals,
        DETECTOR_CAPACITY_RANK_TOLERANCE,
        DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
        DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
    )?)
}

// Origin: engine/crates_rs/core_solvers/src/cert_channel_capacity.rs
// Claim: urn:core:crates_rs:core-solvers:cert-channel-capacity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    //! --- Math Contract:
    //! Object: intersection-restricted hidden-mass estimator.
    //! Preconditions: one-edge scalar carriers with explicit protected directions.
    //! Postconditions: expected dimensions, values, and disclosed residuals.
    //! Authority: None.
    //! ---

    use super::*;
    use core_types::{DetectorEvaluatorRole, ProtectedDistinctionDeclaration};

    fn carrier() -> CoveringCarrier {
        CoveringCarrier {
            num_vertices: 2,
            dim: 1,
            edges: vec![(0, 1, DMatrix::identity(1, 1))],
        }
    }

    fn declaration(
        carrier: &CoveringCarrier,
        kernels: &ObserverKernelFamily,
        direction: Vec<f64>,
        epsilon: f64,
    ) -> DetectorDeploymentDeclaration {
        declaration_with_digest(
            direction,
            epsilon,
            detector_capacity_model_digest(carrier, kernels).unwrap(),
        )
    }

    fn declaration_with_digest(
        direction: Vec<f64>,
        epsilon: f64,
        capacity_model_digest: impl Into<String>,
    ) -> DetectorDeploymentDeclaration {
        DetectorDeploymentDeclaration::new(
            "deployment",
            "corpus",
            "B",
            ["middle".to_string()],
            capacity_model_digest,
            epsilon,
            Vec::new(),
            vec![ProtectedDistinctionDeclaration::new(
                "d",
                DetectorEvaluatorRole::Global,
                "positive",
                "negative",
                direction,
            )
            .unwrap()],
        )
        .unwrap()
    }

    #[test]
    fn full_kernel_prices_protected_antidiagonal() {
        let carrier = carrier();
        let kernels = ObserverKernelFamily::full(&carrier);
        let declaration = declaration(&carrier, &kernels, vec![1.0, -1.0], 1.0);
        let evidence = hidden_mass_l2_on_subspace(&carrier, &kernels, &declaration).unwrap();
        assert!((evidence.value() - 2.0_f64.sqrt()).abs() < 1e-9);
        assert_eq!(evidence.restricted_dimension(), 1);
        assert!(evidence.residuals_within_tolerance());
        assert_eq!(
            evidence.authority_effect(),
            core_types::AuthorityEffect::None
        );
        assert_eq!(
            evidence.capacity_model_digest(),
            declaration.capacity_model_digest()
        );
        assert_eq!(
            evidence.rank_tolerance_used().to_bits(),
            DETECTOR_CAPACITY_RANK_TOLERANCE.to_bits()
        );
        assert_eq!(
            evidence.residual_acceptance_tolerance().to_bits(),
            DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE.to_bits()
        );
        assert_eq!(
            evidence.comparison_tolerance().to_bits(),
            DETECTOR_CAPACITY_COMPARISON_TOLERANCE.to_bits()
        );
        let all_green = all_green_subspace(&carrier, &kernels).unwrap();
        assert_eq!(
            evidence.residuals().all_green_constraint().to_bits(),
            all_green.constraint_residual.to_bits()
        );
        assert_eq!(
            evidence.residuals().all_green_orthonormality().to_bits(),
            all_green.orthonormality_residual.to_bits()
        );
    }

    #[test]
    fn zero_kernel_has_zero_intersection_with_antidiagonal() {
        let carrier = carrier();
        let kernels = ObserverKernelFamily::zero(&carrier);
        let declaration = declaration(&carrier, &kernels, vec![1.0, -1.0], 0.1);
        let evidence = hidden_mass_l2_on_subspace(&carrier, &kernels, &declaration).unwrap();
        assert_eq!(evidence.value(), 0.0);
        assert_eq!(evidence.restricted_dimension(), 0);
        assert!(evidence.restricted_singular_values().is_empty());
    }

    #[test]
    fn exact_min_nonzero_direction_is_not_empty() {
        let carrier = carrier();
        let kernels = ObserverKernelFamily::full(&carrier);
        let declaration = declaration(
            &carrier,
            &kernels,
            vec![MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE, 0.0],
            0.1,
        );

        hidden_mass_l2_on_subspace(&carrier, &kernels, &declaration).unwrap();
    }

    #[test]
    fn exact_all_zero_direction_is_empty() {
        let carrier = carrier();
        let kernels = ObserverKernelFamily::full(&carrier);
        let declaration = declaration(&carrier, &kernels, vec![0.0, 0.0], 0.1);

        assert_eq!(
            hidden_mass_l2_on_subspace(&carrier, &kernels, &declaration).unwrap_err(),
            DetectorCapacityError::EmptyProtectedDirection {
                distinction_id: "d".to_string(),
            }
        );
    }

    #[test]
    fn refuses_direction_dimension_mismatch() {
        let carrier = carrier();
        let kernels = ObserverKernelFamily::full(&carrier);
        let declaration = declaration(&carrier, &kernels, vec![1.0], 0.1);
        let error = hidden_mass_l2_on_subspace(&carrier, &kernels, &declaration).unwrap_err();
        assert!(matches!(
            error,
            DetectorCapacityError::ProtectedDirectionRowMismatch {
                expected: 2,
                found: 1,
                ..
            }
        ));
    }

    #[test]
    fn capacity_model_digest_binds_exact_carrier_and_kernel_bits() {
        let mut plus_zero_carrier = carrier();
        plus_zero_carrier.edges[0].2[(0, 0)] = 0.0;
        let plus_zero_kernel = ObserverKernelFamily::new(vec![DMatrix::from_element(1, 1, 0.0)]);
        let base = detector_capacity_model_digest(&plus_zero_carrier, &plus_zero_kernel).unwrap();

        let mut minus_zero_carrier = plus_zero_carrier.clone();
        minus_zero_carrier.edges[0].2[(0, 0)] = -0.0;
        assert_ne!(
            base,
            detector_capacity_model_digest(&minus_zero_carrier, &plus_zero_kernel).unwrap()
        );

        let minus_zero_kernel = ObserverKernelFamily::new(vec![DMatrix::from_element(1, 1, -0.0)]);
        assert_ne!(
            base,
            detector_capacity_model_digest(&plus_zero_carrier, &minus_zero_kernel).unwrap()
        );
    }

    #[test]
    fn solver_refuses_cross_model_declaration_digest() {
        let carrier = carrier();
        let declared_kernels = ObserverKernelFamily::full(&carrier);
        let actual_kernels = ObserverKernelFamily::zero(&carrier);
        let declaration = declaration(&carrier, &declared_kernels, vec![1.0, -1.0], 0.1);
        let declared = declaration.capacity_model_digest().to_string();
        let recomputed = detector_capacity_model_digest(&carrier, &actual_kernels).unwrap();
        let error =
            hidden_mass_l2_on_subspace(&carrier, &actual_kernels, &declaration).unwrap_err();
        assert_eq!(
            error,
            DetectorCapacityError::CapacityModelDigestMismatch {
                declared,
                recomputed,
            }
        );
    }

    #[test]
    fn checked_digest_refuses_shape_and_nonfinite_inputs() {
        let carrier = carrier();
        let bad_shape = ObserverKernelFamily::new(vec![DMatrix::zeros(2, 1)]);
        assert!(matches!(
            detector_capacity_model_digest(&carrier, &bad_shape),
            Err(DetectorCapacityError::BlindSpot(
                BlindSpotError::KernelRowMismatch {
                    expected: 1,
                    found: 2,
                    ..
                }
            ))
        ));

        let mut nonfinite_carrier = carrier.clone();
        nonfinite_carrier.edges[0].2[(0, 0)] = f64::NAN;
        assert!(matches!(
            detector_capacity_model_digest(
                &nonfinite_carrier,
                &ObserverKernelFamily::full(&nonfinite_carrier)
            ),
            Err(DetectorCapacityError::NonFiniteInput {
                resource: "carrier restriction entry",
                ..
            })
        ));

        let nonfinite_kernel =
            ObserverKernelFamily::new(vec![DMatrix::from_element(1, 1, f64::INFINITY)]);
        assert!(matches!(
            detector_capacity_model_digest(&carrier, &nonfinite_kernel),
            Err(DetectorCapacityError::NonFiniteInput {
                resource: "kernel generator entry",
                ..
            })
        ));
    }

    #[test]
    fn unsafe_magnitudes_refuse_but_exact_bounds_are_accepted() {
        for boundary in [
            MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE,
            -MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE,
            MAX_DETECTOR_SAFE_MAGNITUDE,
            -MAX_DETECTOR_SAFE_MAGNITUDE,
        ] {
            assert!(validate_safe_magnitude(boundary, "boundary test").is_ok());
        }

        let mut huge_carrier = carrier();
        huge_carrier.edges[0].2[(0, 0)] = MAX_DETECTOR_SAFE_MAGNITUDE * 10.0;
        assert!(matches!(
            detector_capacity_model_digest(
                &huge_carrier,
                &ObserverKernelFamily::zero(&huge_carrier)
            ),
            Err(DetectorCapacityError::NumericallyUnsafeMagnitude {
                resource: "carrier restriction entry",
                ..
            })
        ));

        let carrier = carrier();
        let tiny_kernel = ObserverKernelFamily::new(vec![DMatrix::from_element(
            1,
            1,
            MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE / 10.0,
        )]);
        assert!(matches!(
            detector_capacity_model_digest(&carrier, &tiny_kernel),
            Err(DetectorCapacityError::NumericallyUnsafeMagnitude {
                resource: "kernel generator entry",
                ..
            })
        ));

        let kernels = ObserverKernelFamily::full(&carrier);
        let declaration = declaration(
            &carrier,
            &kernels,
            vec![MAX_DETECTOR_SAFE_MAGNITUDE * 10.0, -1.0],
            0.1,
        );
        assert!(matches!(
            hidden_mass_l2_on_subspace(&carrier, &kernels, &declaration),
            Err(DetectorCapacityError::NumericallyUnsafeMagnitude {
                resource: "protected direction coordinate",
                ..
            })
        ));

        let mut at_cap_carrier = carrier.clone();
        at_cap_carrier.edges[0].2[(0, 0)] = MAX_DETECTOR_SAFE_MAGNITUDE;
        assert!(detector_capacity_model_digest(
            &at_cap_carrier,
            &ObserverKernelFamily::zero(&at_cap_carrier)
        )
        .is_ok());
        let at_cap_kernel = ObserverKernelFamily::new(vec![DMatrix::from_element(
            1,
            1,
            MAX_DETECTOR_SAFE_MAGNITUDE,
        )]);
        assert!(detector_capacity_model_digest(&carrier, &at_cap_kernel).is_ok());
    }

    #[test]
    fn preflight_caps_actual_carrier_kernel_and_protected_cells() {
        let oversized_carrier = CoveringCarrier {
            num_vertices: 2,
            dim: 1_025,
            edges: vec![(0, 1, DMatrix::zeros(1_025, 1_025))],
        };
        assert!(matches!(
            detector_capacity_model_digest(
                &oversized_carrier,
                &ObserverKernelFamily::zero(&oversized_carrier)
            ),
            Err(DetectorCapacityError::ResourceLimitExceeded {
                resource: "actual carrier restriction cells",
                found,
                limit: MAX_DETECTOR_CARRIER_RESTRICTION_CELLS,
            }) if found > MAX_DETECTOR_CARRIER_RESTRICTION_CELLS
        ));

        let carrier = carrier();
        let oversized_kernel = ObserverKernelFamily::new(vec![DMatrix::zeros(
            1,
            MAX_DETECTOR_KERNEL_GENERATOR_CELLS + 1,
        )]);
        assert_eq!(
            detector_capacity_model_digest(&carrier, &oversized_kernel).unwrap_err(),
            DetectorCapacityError::ResourceLimitExceeded {
                resource: "actual kernel generator cells",
                found: MAX_DETECTOR_KERNEL_GENERATOR_CELLS + 1,
                limit: MAX_DETECTOR_KERNEL_GENERATOR_CELLS,
            }
        );

        let kernels = ObserverKernelFamily::zero(&carrier);
        let declaration = declaration_with_digest(
            vec![1.0; MAX_DETECTOR_PROTECTED_DIRECTION_COORDINATES + 1],
            0.1,
            detector_capacity_model_digest(&carrier, &kernels).unwrap(),
        );
        assert_eq!(
            hidden_mass_l2_on_subspace(&carrier, &kernels, &declaration).unwrap_err(),
            DetectorCapacityError::ResourceLimitExceeded {
                resource: "actual protected direction coordinates",
                found: MAX_DETECTOR_PROTECTED_DIRECTION_COORDINATES + 1,
                limit: MAX_DETECTOR_PROTECTED_DIRECTION_COORDINATES,
            }
        );
    }
}
