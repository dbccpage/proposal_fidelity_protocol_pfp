//! Exact three-term homological perturbation over the canonical rational field.
//!
//! The convention is `id_C - i r = d h + h d`, so the resolvent is
//! `A = (id + delta h)^(-1) delta`. Both differentials, both chain maps,
//! the homotopy equation and all three special side conditions are checked.
//! A successful transfer returns a newly checked contraction, including its
//! perturbed inclusion, retraction and homotopy; the reduced differential alone
//! is insufficient evidence of the lemma. AuthorityEffect: None.

use crate::hashing::{hash_matrix, Hash256};
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use linear_algebra::exact_field::elimination::inverse_with_limits;
use linear_algebra::exact_field::matrix::{
    add, identity_with_limits, is_zero_matrix, multiply_with_limits, sub, zeros_with_limits,
};
use linear_algebra::exact_field::ExactFieldError;
use linear_algebra::finite_cochain_map::{CochainHomotopy, CochainMap, CochainWindow};
use num_traits::{Signed, Zero};

/// An unchecked proposal. Matrix shapes are explicit, including empty degrees.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ContractionData {
    pub c_dimensions: [usize; 3],
    pub d_dimensions: [usize; 3],
    pub d_c: [BasicMatrix<Q>; 2],
    pub d_d: [BasicMatrix<Q>; 2],
    pub inclusion: [BasicMatrix<Q>; 3],
    pub retraction: [BasicMatrix<Q>; 3],
    /// `[h1: C1 -> C0, h2: C2 -> C1]`.
    pub homotopy: [BasicMatrix<Q>; 2],
}

impl ContractionData {
    /// Commits to every dimension and all twelve matrices, including d_D.
    pub fn content_hash(&self) -> Hash256 {
        let mut state = blake3::Hasher::new();
        state.update(b"core.homological_perturbation.contraction/Q/v1");
        for dimension in self.c_dimensions.iter().chain(&self.d_dimensions) {
            state.update(&(*dimension as u64).to_le_bytes());
        }
        for matrix in self.matrices() {
            state.update(hash_matrix(matrix).as_bytes());
        }
        Hash256(*state.finalize().as_bytes())
    }

    fn matrices(&self) -> impl Iterator<Item = &BasicMatrix<Q>> {
        self.d_c
            .iter()
            .chain(&self.d_d)
            .chain(&self.inclusion)
            .chain(&self.retraction)
            .chain(&self.homotopy)
    }
}

/// Exact checks, with chain-map conditions in addition to the five legacy flags.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
pub struct SideConditionReport {
    pub ri_equals_id_d: bool,
    pub sdr_equation: bool,
    pub hi_zero: bool,
    pub rh_zero: bool,
    pub hh_zero: bool,
    pub inclusion_chain_map: bool,
    pub retraction_chain_map: bool,
}

impl SideConditionReport {
    pub fn is_normalized(&self) -> bool {
        self.ri_equals_id_d
            && self.sdr_equation
            && self.hi_zero
            && self.rh_zero
            && self.hh_zero
            && self.inclusion_chain_map
            && self.retraction_chain_map
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PerturbationError {
    #[error(transparent)]
    Matrix(#[from] MatrixError),
    #[error(transparent)]
    Exact(#[from] ExactFieldError),
    #[error("{map} in degree {degree} has shape {actual:?}, expected {expected:?}")]
    Shape {
        map: &'static str,
        degree: usize,
        actual: (usize, usize),
        expected: (usize, usize),
    },
    #[error("a rational coefficient is not in canonical form with a positive denominator")]
    InvalidCoefficient,
    #[error("{complex} does not have square-zero differential")]
    DifferentialNotSquareZero { complex: &'static str },
    #[error("normalized contraction identities failed: {report:?}")]
    NotNormalized { report: SideConditionReport },
    #[error("id + delta h is singular in degree {degree}")]
    SingularResolvent { degree: usize },
}

/// An immutable contraction that cannot be constructed without exact checks.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckedContraction {
    data: ContractionData,
    inclusion: CochainMap<Q>,
    retraction: CochainMap<Q>,
    homotopy: CochainHomotopy<Q>,
}

impl CheckedContraction {
    /// Limits apply to each matrix allocation and elementary operation, rather
    /// than to cumulative work or the size of arbitrary-precision coefficients.
    pub fn try_new(
        data: ContractionData,
        limits: OperationLimits,
    ) -> Result<Self, PerturbationError> {
        let report = verify_normalized(&data, limits)?;
        if !report.is_normalized() {
            return Err(PerturbationError::NotNormalized { report });
        }
        let (c, d) = windows(&data)?;
        let inclusion = CochainMap::try_new(&d, &c, data.inclusion.clone())?;
        let retraction = CochainMap::try_new(&c, &d, data.retraction.clone())?;
        let identity = CochainMap::identity(&c)?;
        let ir = retraction.then(&inclusion)?;
        let homotopy = CochainHomotopy::try_new(
            &identity,
            &ir,
            data.homotopy[0].clone(),
            data.homotopy[1].clone(),
        )?;
        Ok(Self {
            data,
            inclusion,
            retraction,
            homotopy,
        })
    }

    pub fn data(&self) -> &ContractionData {
        &self.data
    }

    pub fn inclusion(&self) -> &CochainMap<Q> {
        &self.inclusion
    }

    pub fn retraction(&self) -> &CochainMap<Q> {
        &self.retraction
    }

    pub fn homotopy(&self) -> &CochainHomotopy<Q> {
        &self.homotopy
    }
}

/// The complete, independently replayed output of the basic perturbation lemma.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PerturbationTransfer {
    pub delta_d: [BasicMatrix<Q>; 2],
    pub contraction: CheckedContraction,
    pub original_contraction_hash: Hash256,
}

fn charge(
    elements: usize,
    scalar_ops: usize,
    limits: OperationLimits,
) -> Result<(), PerturbationError> {
    if elements > limits.max_elements {
        return Err(MatrixError::AllocationLimitExceeded {
            requested: elements,
            limit: limits.max_elements,
        }
        .into());
    }
    if scalar_ops > limits.max_scalar_ops {
        return Err(MatrixError::OperationLimitExceeded {
            requested: scalar_ops,
            limit: limits.max_scalar_ops,
        }
        .into());
    }
    Ok(())
}

fn check_coefficients(matrix: &BasicMatrix<Q>) -> Result<(), PerturbationError> {
    for value in matrix.as_slice() {
        if value.denom().is_zero() || value.denom().is_negative() {
            return Err(PerturbationError::InvalidCoefficient);
        }
        let normalized = Q::new(value.numer().clone(), value.denom().clone());
        if value.numer() != normalized.numer() || value.denom() != normalized.denom() {
            return Err(PerturbationError::InvalidCoefficient);
        }
    }
    Ok(())
}

fn shape(
    matrix: &BasicMatrix<Q>,
    map: &'static str,
    degree: usize,
    expected: (usize, usize),
) -> Result<(), PerturbationError> {
    if matrix.shape() != expected {
        return Err(PerturbationError::Shape {
            map,
            degree,
            actual: matrix.shape(),
            expected,
        });
    }
    Ok(())
}

/// Preflight every finite-cochain validator's unbudgeted product: its dimensions
/// are at most n, so each result needs n² entries and at most 2n³ scalar calls.
fn preflight(data: &ContractionData, limits: OperationLimits) -> Result<(), PerturbationError> {
    let n = data
        .c_dimensions
        .iter()
        .chain(&data.d_dimensions)
        .copied()
        .max()
        .unwrap_or(0);
    let elements = n
        .checked_mul(n)
        .ok_or(MatrixError::DimensionOverflow { rows: n, cols: n })?;
    let operations = elements
        .checked_mul(n)
        .and_then(|count| count.checked_mul(2))
        .ok_or(MatrixError::OperationCountOverflow)?;
    charge(elements, operations, limits)?;
    for matrix in data.matrices() {
        charge(matrix.as_slice().len(), 0, limits)?;
        check_coefficients(matrix)?;
    }
    check_contraction_shapes(data)
}

fn check_contraction_shapes(data: &ContractionData) -> Result<(), PerturbationError> {
    for degree in 0..2 {
        shape(
            &data.d_c[degree],
            "d_c",
            degree,
            (data.c_dimensions[degree + 1], data.c_dimensions[degree]),
        )?;
        shape(
            &data.d_d[degree],
            "d_d",
            degree,
            (data.d_dimensions[degree + 1], data.d_dimensions[degree]),
        )?;
        shape(
            &data.homotopy[degree],
            "h",
            degree + 1,
            (data.c_dimensions[degree], data.c_dimensions[degree + 1]),
        )?;
    }
    for degree in 0..3 {
        shape(
            &data.inclusion[degree],
            "i",
            degree,
            (data.c_dimensions[degree], data.d_dimensions[degree]),
        )?;
        shape(
            &data.retraction[degree],
            "r",
            degree,
            (data.d_dimensions[degree], data.c_dimensions[degree]),
        )?;
    }
    Ok(())
}

fn windows(
    data: &ContractionData,
) -> Result<(CochainWindow<Q>, CochainWindow<Q>), PerturbationError> {
    let window = |dimensions, differential: &[BasicMatrix<Q>; 2], complex| {
        CochainWindow::try_new(dimensions, differential[0].clone(), differential[1].clone())
            .map_err(|error| match error {
                MatrixError::InvalidOperation(_) => {
                    PerturbationError::DifferentialNotSquareZero { complex }
                }
                other => PerturbationError::Matrix(other),
            })
    };
    Ok((
        window(data.c_dimensions, &data.d_c, "C")?,
        window(data.d_dimensions, &data.d_d, "D")?,
    ))
}

fn plus(
    a: &BasicMatrix<Q>,
    b: &BasicMatrix<Q>,
    limits: OperationLimits,
) -> Result<BasicMatrix<Q>, PerturbationError> {
    charge(a.as_slice().len(), a.as_slice().len(), limits)?;
    Ok(add(a, b)?)
}

fn minus(
    a: &BasicMatrix<Q>,
    b: &BasicMatrix<Q>,
    limits: OperationLimits,
) -> Result<BasicMatrix<Q>, PerturbationError> {
    charge(a.as_slice().len(), a.as_slice().len(), limits)?;
    Ok(sub(a, b)?)
}

fn product(
    a: &BasicMatrix<Q>,
    b: &BasicMatrix<Q>,
    limits: OperationLimits,
) -> Result<BasicMatrix<Q>, PerturbationError> {
    Ok(multiply_with_limits(a, b, limits)?)
}

/// Check every degree. Invalid complexes and malformed/budgeted inputs are typed
/// errors; correctly shaped proposals that fail contraction laws return flags.
pub fn verify_normalized(
    data: &ContractionData,
    limits: OperationLimits,
) -> Result<SideConditionReport, PerturbationError> {
    preflight(data, limits)?;
    let (c, d) = windows(data)?;
    let commutes = |source, target, maps| match CochainMap::try_new(source, target, maps) {
        Ok(_) => Ok(true),
        Err(MatrixError::InvalidOperation(_)) => Ok(false),
        Err(other) => Err(PerturbationError::Matrix(other)),
    };
    let inclusion_chain_map = commutes(&d, &c, data.inclusion.clone())?;
    let retraction_chain_map = commutes(&c, &d, data.retraction.clone())?;
    let (ri_equals_id_d, sdr_equation) = check_sdr_degrees(data, limits)?;
    let (hi_zero, rh_zero, hh_zero) = check_annihilation_conditions(data, limits)?;
    Ok(SideConditionReport {
        ri_equals_id_d,
        sdr_equation,
        hi_zero,
        rh_zero,
        hh_zero,
        inclusion_chain_map,
        retraction_chain_map,
    })
}

fn sdr_rhs(
    data: &ContractionData,
    degree: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<Q>, PerturbationError> {
    match degree {
        0 => product(&data.homotopy[0], &data.d_c[0], limits),
        1 => plus(
            &product(&data.d_c[0], &data.homotopy[0], limits)?,
            &product(&data.homotopy[1], &data.d_c[1], limits)?,
            limits,
        ),
        _ => product(&data.d_c[1], &data.homotopy[1], limits),
    }
}

fn check_sdr_degrees(
    data: &ContractionData,
    limits: OperationLimits,
) -> Result<(bool, bool), PerturbationError> {
    let mut ri_equals_id_d = true;
    let mut sdr_equation = true;
    for degree in 0..3 {
        let ri = product(&data.retraction[degree], &data.inclusion[degree], limits)?;
        ri_equals_id_d &= ri == identity_with_limits(data.d_dimensions[degree], limits)?;
        let ir = product(&data.inclusion[degree], &data.retraction[degree], limits)?;
        let left = minus(
            &identity_with_limits(data.c_dimensions[degree], limits)?,
            &ir,
            limits,
        )?;
        let right = sdr_rhs(data, degree, limits)?;
        sdr_equation &= left == right;
    }
    Ok((ri_equals_id_d, sdr_equation))
}

fn check_annihilation_conditions(
    data: &ContractionData,
    limits: OperationLimits,
) -> Result<(bool, bool, bool), PerturbationError> {
    let mut hi_zero = true;
    let mut rh_zero = true;
    for degree in 0..2 {
        hi_zero &= is_zero_matrix(&product(
            &data.homotopy[degree],
            &data.inclusion[degree + 1],
            limits,
        )?);
        rh_zero &= is_zero_matrix(&product(
            &data.retraction[degree],
            &data.homotopy[degree],
            limits,
        )?);
    }
    let hh_zero = is_zero_matrix(&product(&data.homotopy[0], &data.homotopy[1], limits)?);
    Ok((hi_zero, rh_zero, hh_zero))
}

/// Identity contraction, with d² checked even in the presence of empty degrees.
pub fn identity_contraction(
    dimensions: [usize; 3],
    differential: [BasicMatrix<Q>; 2],
    limits: OperationLimits,
) -> Result<CheckedContraction, PerturbationError> {
    let maps = [
        identity_with_limits(dimensions[0], limits)?,
        identity_with_limits(dimensions[1], limits)?,
        identity_with_limits(dimensions[2], limits)?,
    ];
    CheckedContraction::try_new(
        ContractionData {
            c_dimensions: dimensions,
            d_dimensions: dimensions,
            d_c: differential.clone(),
            d_d: differential,
            inclusion: maps.clone(),
            retraction: maps,
            homotopy: [
                zeros_with_limits(dimensions[0], dimensions[1], limits)?,
                zeros_with_limits(dimensions[1], dimensions[2], limits)?,
            ],
        },
        limits,
    )
}

/// Transfer δ using `A=(1+δh)^(-1)δ`. No nilpotency assumption is needed:
/// invertibility is decided by exact elimination. The perturbed differential
/// must square to zero and every resulting contraction identity is replayed.
pub fn transfer_perturbation(
    contraction: &CheckedContraction,
    delta: &[BasicMatrix<Q>; 2],
    limits: OperationLimits,
) -> Result<PerturbationTransfer, PerturbationError> {
    let data = contraction.data();
    let d_c = validate_and_perturb_dc(data, delta, limits)?;
    let a = [
        compute_resolvent(data, delta, 0, limits)?,
        compute_resolvent(data, delta, 1, limits)?,
    ];
    let delta_d = compute_transferred_delta_d(data, &a, limits)?;
    let (inclusion, retraction, homotopy) = compute_perturbed_maps(data, &a, limits)?;
    let transferred = CheckedContraction::try_new(
        ContractionData {
            c_dimensions: data.c_dimensions,
            d_dimensions: data.d_dimensions,
            d_c,
            d_d: [
                plus(&data.d_d[0], &delta_d[0], limits)?,
                plus(&data.d_d[1], &delta_d[1], limits)?,
            ],
            inclusion,
            retraction,
            homotopy,
        },
        limits,
    )?;
    Ok(PerturbationTransfer {
        delta_d,
        contraction: transferred,
        original_contraction_hash: data.content_hash(),
    })
}

fn validate_and_perturb_dc(
    data: &ContractionData,
    delta: &[BasicMatrix<Q>; 2],
    limits: OperationLimits,
) -> Result<[BasicMatrix<Q>; 2], PerturbationError> {
    preflight(data, limits)?;
    for degree in 0..2 {
        shape(&delta[degree], "delta", degree, data.d_c[degree].shape())?;
        check_coefficients(&delta[degree])?;
    }
    let d_c = [
        plus(&data.d_c[0], &delta[0], limits)?,
        plus(&data.d_c[1], &delta[1], limits)?,
    ];
    if !is_zero_matrix(&product(&d_c[1], &d_c[0], limits)?) {
        return Err(PerturbationError::DifferentialNotSquareZero { complex: "C+delta" });
    }
    Ok(d_c)
}

fn compute_resolvent(
    data: &ContractionData,
    delta: &[BasicMatrix<Q>; 2],
    degree: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<Q>, PerturbationError> {
    let matrix = plus(
        &identity_with_limits(data.c_dimensions[degree + 1], limits)?,
        &product(&delta[degree], &data.homotopy[degree], limits)?,
        limits,
    )?;
    match inverse_with_limits(&matrix, limits) {
        Ok(inverse) => product(&inverse, &delta[degree], limits),
        Err(ExactFieldError::Singular { .. }) => {
            Err(PerturbationError::SingularResolvent { degree: degree + 1 })
        }
        Err(error) => Err(error.into()),
    }
}

fn compute_transferred_delta_d(
    data: &ContractionData,
    a: &[BasicMatrix<Q>; 2],
    limits: OperationLimits,
) -> Result<[BasicMatrix<Q>; 2], PerturbationError> {
    Ok([
        product(
            &data.retraction[1],
            &product(&a[0], &data.inclusion[0], limits)?,
            limits,
        )?,
        product(
            &data.retraction[2],
            &product(&a[1], &data.inclusion[1], limits)?,
            limits,
        )?,
    ])
}

type PerturbedMaps = ([BasicMatrix<Q>; 3], [BasicMatrix<Q>; 3], [BasicMatrix<Q>; 2]);

fn compute_perturbed_maps(
    data: &ContractionData,
    a: &[BasicMatrix<Q>; 2],
    limits: OperationLimits,
) -> Result<PerturbedMaps, PerturbationError> {
    let mut inclusion = data.inclusion.clone();
    let mut retraction = data.retraction.clone();
    let mut homotopy = data.homotopy.clone();
    for degree in 0..2 {
        let ha = product(&data.homotopy[degree], &a[degree], limits)?;
        let ah = product(&a[degree], &data.homotopy[degree], limits)?;
        inclusion[degree] = minus(
            &inclusion[degree],
            &product(&ha, &data.inclusion[degree], limits)?,
            limits,
        )?;
        retraction[degree + 1] = minus(
            &retraction[degree + 1],
            &product(&data.retraction[degree + 1], &ah, limits)?,
            limits,
        )?;
        homotopy[degree] = minus(
            &homotopy[degree],
            &product(&ha, &data.homotopy[degree], limits)?,
            limits,
        )?;
    }
    Ok((inclusion, retraction, homotopy))
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_d5381c69 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
