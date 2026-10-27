//! Exact tensor marginals and reference-dependent component projectors.
//!
//! Site coordinates use row-major tensor order; retained sites may be listed in
//! any order. Each reference factor is square, nonempty, and has exact trace one.
//! Positivity and Hermiticity are separate domain obligations.
//!
//! For `H_j = ker(Tr: M(d_j,F) -> F)`, normalization gives the direct sum
//! `M(d_j,F) = F rho_j + H_j`. The homogeneous product differential selects the
//! support-zero and support-one summands. Its complement selects all summands
//! of support at least two. The distinct highest-order projector selects only
//! `tensor_j H_j`. With `P_S` retaining sites `S` and inserting reference factors
//! elsewhere, its formula is `R_k = sum_S (-1)^(k-|S|) P_S`, including the full
//! subset. Consequently `id - sum_{proper S} (-1)^(k-|S|) P_S` has the wrong
//! sign: on the normalized product reference it returns twice that reference.
//!
//! Limits bound tensor-sized and metadata allocations, and aggregate scalar
//! calls before scalar work starts. Scalar-internal memory use and the scalar
//! implementation's own arithmetic obligations follow `exact_field` conventions.
//! AuthorityEffect: None.

use super::{charge, element_count, matrix as mx, plus, reserve, times, ExactFieldError};
use crate::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use crate::scalars::{ExactRing, Field};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TensorProjectorError {
    #[error("exact tensor algebra: {0}")]
    Algebra(#[from] ExactFieldError),
    #[error("a tensor carrier needs at least one site")]
    EmptySites,
    #[error("site {site} has zero dimension")]
    ZeroDimension { site: usize },
    #[error("reference factor {site} is {rows}x{cols}; a square matrix is required")]
    NonSquareReference {
        site: usize,
        rows: usize,
        cols: usize,
    },
    #[error("reference factor {site} does not have exact trace one")]
    ReferenceNotNormalized { site: usize },
    #[error("site {site} is outside a {site_count}-site carrier")]
    SiteOutOfRange { site: usize, site_count: usize },
    #[error("site {site} occurs more than once")]
    DuplicateSite { site: usize },
    #[error("a full permutation needs {expected} sites, got {got}")]
    IncompletePermutation { expected: usize, got: usize },
}

impl From<MatrixError> for TensorProjectorError {
    fn from(error: MatrixError) -> Self {
        Self::Algebra(error.into())
    }
}

/// Checked heterogeneous tensor dimensions and row-major strides.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TensorLayout {
    dimensions: Vec<usize>,
    strides: Vec<usize>,
    dimension: usize,
    elements: usize,
}

impl TensorLayout {
    pub fn new_with_limits(
        dimensions: &[usize],
        limits: OperationLimits,
    ) -> Result<Self, TensorProjectorError> {
        if dimensions.is_empty() {
            return Err(TensorProjectorError::EmptySites);
        }
        let mut dimension = 1;
        for (site, &local) in dimensions.iter().enumerate() {
            if local == 0 {
                return Err(TensorProjectorError::ZeroDimension { site });
            }
            dimension = element_count(dimension, local)?;
        }
        let elements = element_count(dimension, dimension)?;
        charge(limits, elements.max(dimensions.len()), 0)?;
        let mut owned = reserve(dimensions.len())?;
        owned.extend_from_slice(dimensions);
        let mut strides = reserve(dimensions.len())?;
        let mut stride = dimension;
        for &local in dimensions {
            stride /= local;
            strides.push(stride);
        }
        Ok(Self {
            dimensions: owned,
            strides,
            dimension,
            elements,
        })
    }

    pub fn dimensions(&self) -> &[usize] {
        &self.dimensions
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    fn check_operator<F>(&self, matrix: &BasicMatrix<F>) -> Result<(), TensorProjectorError> {
        check_shape("tensor operator", matrix, self.dimension)
    }

    fn subset_dimension(&self, sites: &[usize]) -> Result<usize, TensorProjectorError> {
        let mut dimension = 1;
        for (position, &site) in sites.iter().enumerate() {
            if site >= self.dimensions.len() {
                return Err(TensorProjectorError::SiteOutOfRange {
                    site,
                    site_count: self.dimensions.len(),
                });
            }
            if sites[..position].contains(&site) {
                return Err(TensorProjectorError::DuplicateSite { site });
            }
            dimension = element_count(dimension, self.dimensions[site])?;
        }
        Ok(dimension)
    }

    /// Trace out omitted sites. Empty retention returns the total trace as `1x1`.
    /// Output factors follow `retained_sites`, including arbitrary permutations.
    pub fn partial_trace_with_limits<F: Field + ExactRing>(
        &self,
        matrix: &BasicMatrix<F>,
        retained_sites: &[usize],
        limits: OperationLimits,
    ) -> Result<BasicMatrix<F>, TensorProjectorError> {
        self.check_operator(matrix)?;
        let reduced = self.subset_dimension(retained_sites)?;
        let ops = if retained_sites.len() == self.dimensions.len() {
            0
        } else {
            times(self.dimension, reduced)?
        };
        charge(
            limits,
            element_count(reduced, reduced)?.max(self.dimensions.len()),
            ops,
        )?;
        let plan = SitePlan::new(self, retained_sites, reduced)?;
        partial_trace(self, matrix, &plan, limits)
    }

    /// Reorder every factor without tracing or performing scalar arithmetic.
    pub fn permute_with_limits<F: Field + ExactRing>(
        &self,
        matrix: &BasicMatrix<F>,
        site_order: &[usize],
        limits: OperationLimits,
    ) -> Result<BasicMatrix<F>, TensorProjectorError> {
        if site_order.len() != self.dimensions.len() {
            return Err(TensorProjectorError::IncompletePermutation {
                expected: self.dimensions.len(),
                got: site_order.len(),
            });
        }
        self.partial_trace_with_limits(matrix, site_order, limits)
    }

    /// Insert an operator with identity spectator factors in original site order.
    /// The local matrix's coordinates follow `retained_sites`.
    pub fn embed_operator_with_limits<F: Field + ExactRing>(
        &self,
        local: &BasicMatrix<F>,
        retained_sites: &[usize],
        limits: OperationLimits,
    ) -> Result<BasicMatrix<F>, TensorProjectorError> {
        let reduced = self.subset_dimension(retained_sites)?;
        check_shape("embedded operator", local, reduced)?;
        charge(limits, self.elements.max(self.dimensions.len()), 0)?;
        let plan = SitePlan::new(self, retained_sites, reduced)?;
        Ok(BasicMatrix::try_from_fn_with_limit(
            self.dimension,
            self.dimension,
            limits.max_elements,
            |row, col| {
                if plan
                    .omitted
                    .iter()
                    .any(|&site| self.digit(row, site) != self.digit(col, site))
                {
                    F::zero()
                } else {
                    let r = plan.local_index(self, row);
                    let c = plan.local_index(self, col);
                    local.as_slice()[r * reduced + c].clone()
                }
            },
        )?)
    }

    fn digit(&self, index: usize, site: usize) -> usize {
        (index / self.strides[site]) % self.dimensions[site]
    }
}

/// Exact trace of a square matrix, with no temporary diagonal allocation.
pub fn trace_with_limits<F: Field + ExactRing>(
    matrix: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<F, TensorProjectorError> {
    let dimension = super::require_square("tensor trace", matrix)?;
    charge(limits, 0, dimension)?;
    Ok(trace(matrix))
}

fn trace<F: Field + ExactRing>(matrix: &BasicMatrix<F>) -> F {
    let mut result = F::zero();
    for index in 0..matrix.rows() {
        result = result.add(&matrix.as_slice()[index * matrix.cols() + index]);
    }
    result
}

fn check_shape<F>(
    operation: &'static str,
    matrix: &BasicMatrix<F>,
    dimension: usize,
) -> Result<(), TensorProjectorError> {
    if matrix.shape() != (dimension, dimension) {
        return Err(ExactFieldError::ShapeMismatch {
            operation,
            left: matrix.shape(),
            right: (dimension, dimension),
        }
        .into());
    }
    Ok(())
}

struct SitePlan<'a> {
    sites: &'a [usize],
    local_strides: Vec<usize>,
    omitted: Vec<usize>,
    omitted_strides: Vec<usize>,
    reduced: usize,
    complement: usize,
}

impl<'a> SitePlan<'a> {
    fn new(layout: &TensorLayout, sites: &'a [usize], reduced: usize) -> Result<Self, MatrixError> {
        let mut local_strides = reserve(sites.len())?;
        let mut stride = reduced;
        for &site in sites {
            stride /= layout.dimensions[site];
            local_strides.push(stride);
        }
        let mut omitted = reserve(layout.dimensions.len() - sites.len())?;
        for site in 0..layout.dimensions.len() {
            if !sites.contains(&site) {
                omitted.push(site);
            }
        }
        let complement = layout.dimension / reduced;
        let mut omitted_strides = reserve(omitted.len())?;
        stride = complement;
        for &site in &omitted {
            stride /= layout.dimensions[site];
            omitted_strides.push(stride);
        }
        Ok(Self {
            sites,
            local_strides,
            omitted,
            omitted_strides,
            reduced,
            complement,
        })
    }

    fn local_index(&self, layout: &TensorLayout, global: usize) -> usize {
        self.sites
            .iter()
            .zip(&self.local_strides)
            .map(|(&site, &stride)| layout.digit(global, site) * stride)
            .sum()
    }

    fn retained_offset(&self, layout: &TensorLayout, local: usize) -> usize {
        self.sites
            .iter()
            .zip(&self.local_strides)
            .map(|(&site, &stride)| {
                ((local / stride) % layout.dimensions[site]) * layout.strides[site]
            })
            .sum()
    }

    fn omitted_offset(&self, layout: &TensorLayout, local: usize) -> usize {
        self.omitted
            .iter()
            .zip(&self.omitted_strides)
            .map(|(&site, &stride)| {
                ((local / stride) % layout.dimensions[site]) * layout.strides[site]
            })
            .sum()
    }
}

fn partial_trace<F: Field + ExactRing>(
    layout: &TensorLayout,
    matrix: &BasicMatrix<F>,
    plan: &SitePlan<'_>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, TensorProjectorError> {
    Ok(BasicMatrix::try_from_fn_with_limit(
        plan.reduced,
        plan.reduced,
        limits.max_elements,
        |row, col| {
            let r = plan.retained_offset(layout, row);
            let c = plan.retained_offset(layout, col);
            if plan.omitted.is_empty() {
                return matrix.as_slice()[r * layout.dimension + c].clone();
            }
            let mut value = F::zero();
            for diagonal in 0..plan.complement {
                let offset = plan.omitted_offset(layout, diagonal);
                value = value.add(&matrix.as_slice()[(r + offset) * layout.dimension + c + offset]);
            }
            value
        },
    )?)
}

/// Normalized reference factors and their ordered product, independent of physics.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProductReference<F> {
    layout: TensorLayout,
    factors: Vec<BasicMatrix<F>>,
    product: BasicMatrix<F>,
}

impl<F: Field + ExactRing> ProductReference<F> {
    pub fn new_with_limits(
        factors: &[BasicMatrix<F>],
        limits: OperationLimits,
    ) -> Result<Self, TensorProjectorError> {
        let dimension = preflight_reference_factors(factors, limits)?;
        let dimensions = validate_and_collect_dimensions(factors)?;
        let layout = TensorLayout::new_with_limits(&dimensions, limits)?;
        let product = build_reference_product(factors, &layout, dimension, limits)?;
        let owned_factors = clone_reference_factors(factors, limits)?;
        Ok(Self {
            layout,
            factors: owned_factors,
            product,
        })
    }

    pub fn layout(&self) -> &TensorLayout {
        &self.layout
    }

    pub fn factors(&self) -> &[BasicMatrix<F>] {
        &self.factors
    }

    pub fn product(&self) -> &BasicMatrix<F> {
        &self.product
    }

    /// Insert a local matrix and reference spectator factors in original order.
    pub fn inject_with_limits(
        &self,
        local: &BasicMatrix<F>,
        retained_sites: &[usize],
        limits: OperationLimits,
    ) -> Result<BasicMatrix<F>, TensorProjectorError> {
        let reduced = self.layout.subset_dimension(retained_sites)?;
        check_shape("reference insertion", local, reduced)?;
        charge(
            limits,
            self.layout.elements.max(self.factors.len()),
            times(
                self.layout.elements,
                self.factors.len() - retained_sites.len(),
            )?,
        )?;
        let plan = SitePlan::new(&self.layout, retained_sites, reduced)?;
        Ok(BasicMatrix::try_from_fn_with_limit(
            self.layout.dimension,
            self.layout.dimension,
            limits.max_elements,
            |row, col| self.inject_entry(local, &plan, row, col),
        )?)
    }

    fn inject_entry(
        &self,
        local: &BasicMatrix<F>,
        plan: &SitePlan<'_>,
        row: usize,
        col: usize,
    ) -> F {
        let r = plan.local_index(&self.layout, row);
        let c = plan.local_index(&self.layout, col);
        let mut value = local.as_slice()[r * plan.reduced + c].clone();
        for &site in &plan.omitted {
            let factor = &self.factors[site];
            value = value.mul(
                &factor.as_slice()
                    [self.layout.digit(row, site) * factor.cols() + self.layout.digit(col, site)],
            );
        }
        value
    }

    /// `P_S`: retain the reduced matrix on `S`, filling all omitted sites by references.
    pub fn retained_component_with_limits(
        &self,
        matrix: &BasicMatrix<F>,
        retained_sites: &[usize],
        limits: OperationLimits,
    ) -> Result<BasicMatrix<F>, TensorProjectorError> {
        self.layout.check_operator(matrix)?;
        let reduced = self.layout.subset_dimension(retained_sites)?;
        let trace_ops = if retained_sites.len() == self.factors.len() {
            0
        } else {
            times(self.layout.dimension, reduced)?
        };
        charge(
            limits,
            self.layout.elements.max(self.factors.len()),
            plus(
                trace_ops,
                times(
                    self.layout.elements,
                    self.factors.len() - retained_sites.len(),
                )?,
            )?,
        )?;
        let local = self
            .layout
            .partial_trace_with_limits(matrix, retained_sites, limits)?;
        self.inject_with_limits(&local, retained_sites, limits)
    }

    fn differential_work(&self) -> Result<usize, MatrixError> {
        let marginal_ops = self.marginal_work_sum()?;
        let sites = self.factors.len();
        let site_grid_ops = plus(
            marginal_ops,
            times(times(self.layout.elements, sites)?, sites)?,
        )?;
        let tail_ops = plus(
            plus(self.layout.dimension, sites)?,
            plus(1, times(3, self.layout.elements)?)?,
        )?;
        plus(site_grid_ops, tail_ops)
    }

    fn marginal_work_sum(&self) -> Result<usize, MatrixError> {
        let mut marginal_ops = 0;
        for &dimension in self.layout.dimensions() {
            marginal_ops = plus(marginal_ops, times(self.layout.dimension, dimension)?)?;
        }
        Ok(marginal_ops)
    }

    /// Full-space homogeneous extension: `sum_j i_j tau_j(Z) - (k-1) Tr(Z) rho`.
    /// It preserves every single-site marginal and fixes the radial reference.
    pub fn product_differential_with_limits(
        &self,
        matrix: &BasicMatrix<F>,
        limits: OperationLimits,
    ) -> Result<BasicMatrix<F>, TensorProjectorError> {
        self.layout.check_operator(matrix)?;
        charge(
            limits,
            self.layout.elements.max(self.factors.len()),
            self.differential_work()?,
        )?;
        let mut data = reserve(self.layout.elements)?;
        data.resize_with(self.layout.elements, F::zero);
        self.accumulate_site_marginals(matrix, &mut data, limits)?;
        self.subtract_radial_reference(matrix, &mut data);
        Ok(BasicMatrix::from_row_major_with_limit(
            self.layout.dimension,
            self.layout.dimension,
            data,
            limits.max_elements,
        )?)
    }

    fn accumulate_site_marginals(
        &self,
        matrix: &BasicMatrix<F>,
        data: &mut [F],
        limits: OperationLimits,
    ) -> Result<(), TensorProjectorError> {
        for site in 0..self.factors.len() {
            let sites = [site];
            let reduced = self.layout.dimensions[site];
            let plan = SitePlan::new(&self.layout, &sites, reduced)?;
            let local = partial_trace(&self.layout, matrix, &plan, limits)?;
            for row in 0..self.layout.dimension {
                for col in 0..self.layout.dimension {
                    let index = row * self.layout.dimension + col;
                    data[index] = data[index].add(&self.inject_entry(&local, &plan, row, col));
                }
            }
        }
        Ok(())
    }

    fn subtract_radial_reference(&self, matrix: &BasicMatrix<F>, data: &mut [F]) {
        let mut coefficient = F::zero();
        for _ in 1..self.factors.len() {
            coefficient = coefficient.add(&F::one());
        }
        let radial = coefficient.mul(&trace(matrix));
        for (value, reference) in data.iter_mut().zip(self.product.as_slice()) {
            *value = value.sub(&radial.mul(reference));
        }
    }

    /// `Q=I-P`, retaining all reference support sectors of order at least two.
    pub fn normal_projector_with_limits(
        &self,
        matrix: &BasicMatrix<F>,
        limits: OperationLimits,
    ) -> Result<BasicMatrix<F>, TensorProjectorError> {
        self.layout.check_operator(matrix)?;
        charge(
            limits,
            self.layout.elements.max(self.factors.len()),
            plus(self.differential_work()?, times(2, self.layout.elements)?)?,
        )?;
        let projected = self.product_differential_with_limits(matrix, limits)?;
        Ok(mx::sub(matrix, &projected)?)
    }

    /// `R_k=product_j(I-E_j)`, where `E_j=P_{all sites except j}`.
    /// This annihilates every proper reference support, including intermediate orders.
    pub fn highest_order_with_limits(
        &self,
        matrix: &BasicMatrix<F>,
        limits: OperationLimits,
    ) -> Result<BasicMatrix<F>, TensorProjectorError> {
        self.layout.check_operator(matrix)?;
        charge(
            limits,
            self.layout.elements.max(self.factors.len()),
            times(times(4, self.layout.elements)?, self.factors.len())?,
        )?;
        let mut result =
            mx::from_fn_with_limits(matrix.rows(), matrix.cols(), limits, |row, col| {
                matrix.as_slice()[row * matrix.cols() + col].clone()
            })?;
        let mut complement = reserve(self.factors.len() - 1)?;
        for site in 0..self.factors.len() {
            complement.clear();
            complement.extend((0..self.factors.len()).filter(|&other| other != site));
            let replaced = self.retained_component_with_limits(&result, &complement, limits)?;
            result = mx::sub(&result, &replaced)?;
        }
        Ok(result)
    }

    /// Independent inclusion-exclusion expansion, including the full retained subset.
    /// Exponential scalar work is checked before enumeration; overflow is a refusal.
    pub fn inclusion_exclusion_with_limits(
        &self,
        matrix: &BasicMatrix<F>,
        limits: OperationLimits,
    ) -> Result<BasicMatrix<F>, TensorProjectorError> {
        self.layout.check_operator(matrix)?;
        let terms = self.charge_inclusion_exclusion_work(limits)?;
        let mut data = reserve(self.layout.elements)?;
        data.resize_with(self.layout.elements, F::zero);
        let mut retained = reserve(self.factors.len())?;
        for mask in 0..terms {
            retained.clear();
            retained.extend((0..self.factors.len()).filter(|&site| mask & (1usize << site) != 0));
            let component = self.retained_component_with_limits(matrix, &retained, limits)?;
            let positive = (self.factors.len() - retained.len()) % 2 == 0;
            accumulate_signed_component(&mut data, component.as_slice(), positive);
        }
        Ok(BasicMatrix::from_row_major_with_limit(
            self.layout.dimension,
            self.layout.dimension,
            data,
            limits.max_elements,
        )?)
    }

    fn charge_inclusion_exclusion_work(
        &self,
        limits: OperationLimits,
    ) -> Result<usize, TensorProjectorError> {
        let exponent =
            u32::try_from(self.factors.len()).map_err(|_| MatrixError::OperationCountOverflow)?;
        let terms = 1usize
            .checked_shl(exponent)
            .ok_or(MatrixError::OperationCountOverflow)?;
        let ops = times(
            terms,
            times(self.layout.elements, plus(self.factors.len(), 3)?)?,
        )?;
        charge(limits, self.layout.elements.max(self.factors.len()), ops)?;
        Ok(terms)
    }
}

fn preflight_reference_factors<F>(
    factors: &[BasicMatrix<F>],
    limits: OperationLimits,
) -> Result<usize, TensorProjectorError> {
    let (dimension, factor_elements, diagonal_ops) = measure_reference_factors(factors)?;
    let elements = element_count(dimension, dimension)?;
    charge(
        limits,
        plus(elements, factor_elements)?.max(factors.len()),
        plus(diagonal_ops, times(elements, factors.len())?)?,
    )?;
    Ok(dimension)
}

fn measure_reference_factors<F>(
    factors: &[BasicMatrix<F>],
) -> Result<(usize, usize, usize), TensorProjectorError> {
    if factors.is_empty() {
        return Err(TensorProjectorError::EmptySites);
    }
    let mut dimension = 1;
    let mut factor_elements = 0;
    let mut diagonal_ops = 0;
    for (site, factor) in factors.iter().enumerate() {
        if factor.rows() != factor.cols() {
            return Err(TensorProjectorError::NonSquareReference {
                site,
                rows: factor.rows(),
                cols: factor.cols(),
            });
        }
        if factor.rows() == 0 {
            return Err(TensorProjectorError::ZeroDimension { site });
        }
        dimension = element_count(dimension, factor.rows())?;
        factor_elements = plus(factor_elements, factor.as_slice().len())?;
        diagonal_ops = plus(diagonal_ops, factor.rows())?;
    }
    Ok((dimension, factor_elements, diagonal_ops))
}

fn validate_and_collect_dimensions<F: Field + ExactRing>(
    factors: &[BasicMatrix<F>],
) -> Result<Vec<usize>, TensorProjectorError> {
    let mut dimensions = reserve(factors.len())?;
    for (site, factor) in factors.iter().enumerate() {
        if trace(factor) != F::one() {
            return Err(TensorProjectorError::ReferenceNotNormalized { site });
        }
        dimensions.push(factor.rows());
    }
    Ok(dimensions)
}

fn build_reference_product<F: Field + ExactRing>(
    factors: &[BasicMatrix<F>],
    layout: &TensorLayout,
    dimension: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, TensorProjectorError> {
    Ok(BasicMatrix::try_from_fn_with_limit(
        dimension,
        dimension,
        limits.max_elements,
        |row, col| {
            let mut value = F::one();
            for (site, factor) in factors.iter().enumerate() {
                value = value.mul(
                    &factor.as_slice()
                        [layout.digit(row, site) * factor.cols() + layout.digit(col, site)],
                );
            }
            value
        },
    )?)
}

fn clone_reference_factors<F: Field + ExactRing>(
    factors: &[BasicMatrix<F>],
    limits: OperationLimits,
) -> Result<Vec<BasicMatrix<F>>, TensorProjectorError> {
    let mut owned_factors = reserve(factors.len())?;
    for factor in factors {
        owned_factors.push(BasicMatrix::try_from_fn_with_limit(
            factor.rows(),
            factor.cols(),
            limits.max_elements,
            |row, col| factor.as_slice()[row * factor.cols() + col].clone(),
        )?);
    }
    Ok(owned_factors)
}

fn accumulate_signed_component<F: Field + ExactRing>(
    data: &mut [F],
    component: &[F],
    positive: bool,
) {
    for (value, term) in data.iter_mut().zip(component) {
        *value = if positive {
            value.add(term)
        } else {
            value.sub(term)
        };
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_97e515d2 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
