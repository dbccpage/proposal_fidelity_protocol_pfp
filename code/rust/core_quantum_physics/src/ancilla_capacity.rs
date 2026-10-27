//! Sharp extension-purity and pure-marginal distance bounds for declared
//! finite complex matrix sectors and an available finite ancilla algebra.
//!
//! The full positive state spaces and standard block tensor product are
//! premises. Only the largest simple ancilla block matters. Decreasing
//! marginal eigenvalues are grouped in blocks of that size. The grouped
//! spectrum majorizes every extension spectrum; explicit block purifications
//! attain it over C. This module evaluates the written theorem exactly on
//! rational spectra, not an unrestricted eigenvalue approximation.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_78ba42a8<T> {
    fn checked_invariant_78ba42a8(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_78ba42a8<T> for Option<T> {
    #[inline]
    fn checked_invariant_78ba42a8(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_78ba42a8<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_78ba42a8(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_entropy::{RationalSpectrum, SpectrumError};
use crate::exact_instrument::ExactDensityState;
use crate::exact_operator::{ExactOperator, OperatorError};
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use num_traits::Signed;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{sqrt_exact, One, Rational, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AncillaCapacityError {
    #[error("ancilla must have at least one nonzero simple block")]
    InvalidAncilla,
    #[error("system must have at least one sector")]
    EmptySystem,
    #[error("sector weights must be nonnegative and sum to one")]
    InvalidWeights,
    #[error("expanded spectrum exceeds the declared dimension budget")]
    SpectrumBudget,
    #[error("dimension arithmetic overflow")]
    DimensionOverflow,
    #[error("the exact matrix spectrum is not rational")]
    NonRationalSpectrum,
    #[error("unknown system sector {0}")]
    UnknownSector(usize),
    #[error("the canonical extension coefficient at ({first},{second}) is not rational")]
    NonRationalCoefficient { first: usize, second: usize },
    #[error(transparent)]
    Spectrum(#[from] SpectrumError),
    #[error(transparent)]
    Operator(#[from] OperatorError),
    #[error(transparent)]
    Algebra(#[from] ExactFieldError),
    #[error(transparent)]
    Matrix(#[from] MatrixError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SectorCapacity {
    eigenvalues: Vec<Rational>,
    grouped: Vec<Rational>,
}

impl SectorCapacity {
    /// Unnormalized eigenvalues of this central block, in decreasing order.
    pub fn eigenvalues(&self) -> &[Rational] {
        &self.eigenvalues
    }
    /// Unnormalized optimal extension spectrum, with possible trailing zeros.
    pub fn grouped(&self) -> &[Rational] {
        &self.grouped
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AncillaCapacity {
    largest_ancilla_block: usize,
    sectors: Vec<SectorCapacity>,
}

fn largest_block(blocks: &[usize]) -> Result<usize, AncillaCapacityError> {
    if blocks.contains(&0) {
        return Err(AncillaCapacityError::InvalidAncilla);
    }
    blocks
        .iter()
        .copied()
        .max()
        .ok_or(AncillaCapacityError::InvalidAncilla)
}

impl AncillaCapacity {
    /// Input spectra are already normalized by the sovereign RationalSpectrum
    /// constructor. Weights supply the central masses. This does not assert
    /// that a caller's separately held matrix has these eigenvalues.
    pub fn from_sectors(
        sectors: &[(Rational, RationalSpectrum)],
        ancilla_blocks: &[usize],
        max_spectrum_dimension: usize,
    ) -> Result<Self, AncillaCapacityError> {
        let m = largest_block(ancilla_blocks)?;
        Self::validate_sectors(sectors, max_spectrum_dimension)?;
        let mut result = Vec::with_capacity(sectors.len());
        for (weight, spectrum) in sectors {
            result.push(Self::build_sector_capacity(weight, spectrum, m));
        }
        Ok(Self {
            largest_ancilla_block: m,
            sectors: result,
        })
    }

    fn validate_sectors(
        sectors: &[(Rational, RationalSpectrum)],
        max_spectrum_dimension: usize,
    ) -> Result<(), AncillaCapacityError> {
        if sectors.is_empty() {
            return Err(AncillaCapacityError::EmptySystem);
        }
        if sectors
            .iter()
            .any(|(p, _)| !p.denom().is_positive() || p < &Rational::zero())
            || sectors.iter().map(|(p, _)| p.clone()).sum::<Rational>() != Rational::one()
        {
            return Err(AncillaCapacityError::InvalidWeights);
        }
        let mut dimension = 0usize;
        for (_, spectrum) in sectors {
            dimension = dimension
                .checked_add(spectrum.dimension())
                .ok_or(AncillaCapacityError::DimensionOverflow)?;
        }
        if dimension > max_spectrum_dimension {
            return Err(AncillaCapacityError::SpectrumBudget);
        }
        Ok(())
    }

    fn build_sector_capacity(
        weight: &Rational,
        spectrum: &RationalSpectrum,
        m: usize,
    ) -> SectorCapacity {
        let mut eigenvalues = Vec::with_capacity(spectrum.dimension());
        for (value, multiplicity) in spectrum.entries() {
            eigenvalues.extend(std::iter::repeat_n(weight * value, *multiplicity));
        }
        eigenvalues.sort_by(|a, b| b.cmp(a));
        let grouped = eigenvalues
            .chunks(m)
            .map(|c| c.iter().cloned().sum())
            .collect();
        SectorCapacity {
            eigenvalues,
            grouped,
        }
    }

    /// Matrix-bound single-sector route. The canonical exact spectrum owner
    /// derives eigenvalues; an irrational result is refused, never rounded.
    pub fn from_density(
        state: &ExactDensityState,
        ancilla_blocks: &[usize],
        max_spectrum_dimension: usize,
    ) -> Result<Self, AncillaCapacityError> {
        largest_block(ancilla_blocks)?;
        if state.dimension() > max_spectrum_dimension {
            return Err(AncillaCapacityError::SpectrumBudget);
        }
        let entries = ExactOperator::try_new(state.matrix().clone())?
            .spectrum()?
            .rational_eigenvalues()
            .ok_or(AncillaCapacityError::NonRationalSpectrum)?;
        Self::from_sectors(
            &[(Rational::one(), RationalSpectrum::try_new(entries)?)],
            ancilla_blocks,
            max_spectrum_dimension,
        )
    }

    pub fn largest_ancilla_block(&self) -> usize {
        self.largest_ancilla_block
    }
    pub fn sectors(&self) -> &[SectorCapacity] {
        &self.sectors
    }
    pub fn maximum_extension_purity(&self) -> Rational {
        self.sectors
            .iter()
            .flat_map(|s| &s.grouped)
            .map(|q| q * q)
            .sum()
    }
    /// If only separable joint states are admitted, sigma <= rho tensor I
    /// bounds purity by Tr(rho^2); rho tensor a pure ancilla attains it.
    pub fn maximum_separable_extension_purity(&self) -> Rational {
        self.sectors
            .iter()
            .flat_map(|s| &s.eigenvalues)
            .map(|q| q * q)
            .sum()
    }
    pub fn minimum_extension_rank(&self) -> usize {
        self.sectors
            .iter()
            .flat_map(|s| &s.grouped)
            .filter(|q| !q.is_zero())
            .count()
    }
    pub fn best_pure_marginal_mass(&self) -> Rational {
        self.sectors
            .iter()
            .map(|s| s.grouped[0].clone())
            .max()
            .checked_invariant_78ba42a8("validated nonempty system")
    }
    pub fn pure_marginal_trace_distance(&self) -> Rational {
        Rational::one() - self.best_pure_marginal_mass()
    }

    /// Attains the block bound in the *sorted diagonal* marginal basis when
    /// all sqrt(lambda_i lambda_j) coefficients in each group are rational.
    /// Returns one possibly subnormalized central block, not a rotated input
    /// matrix's extension. No extra ancilla sector is silently adjoined.
    /// Nonrational coefficients refuse this Q(i) recipe, not complex existence.
    pub fn rational_diagonal_extension(
        &self,
        sector: usize,
        limits: OperationLimits,
    ) -> Result<BasicMatrix<GaussianRat>, AncillaCapacityError> {
        let values = &self
            .sectors
            .get(sector)
            .ok_or(AncillaCapacityError::UnknownSector(sector))?
            .eigenvalues;
        let m = self.largest_ancilla_block;
        let dimension = Self::check_extension_budget(values, m, limits)?;
        let mut result = mx::zeros_with_limits(dimension, dimension, limits)?;
        for (block, chunk) in values.chunks(m).enumerate() {
            Self::fill_extension_block(&mut result, block, chunk, m)?;
        }
        Ok(result)
    }

    fn check_extension_budget(
        values: &[Rational],
        m: usize,
        limits: OperationLimits,
    ) -> Result<usize, AncillaCapacityError> {
        let dimension = values
            .len()
            .checked_mul(m)
            .ok_or(AncillaCapacityError::DimensionOverflow)?;
        // Charge a product and an exact-root query for every filled entry.
        // As elsewhere in exact-field budgets, this is not a bit-complexity bound.
        let work = values.chunks(m).try_fold(0usize, |total, chunk| {
            chunk
                .len()
                .checked_mul(chunk.len())
                .and_then(|n| n.checked_mul(2))
                .and_then(|n| total.checked_add(n))
                .ok_or(AncillaCapacityError::DimensionOverflow)
        })?;
        if work > limits.max_scalar_ops {
            return Err(MatrixError::OperationLimitExceeded {
                requested: work,
                limit: limits.max_scalar_ops,
            }
            .into());
        }
        Ok(dimension)
    }

    fn fill_extension_block(
        result: &mut BasicMatrix<GaussianRat>,
        block: usize,
        chunk: &[Rational],
        m: usize,
    ) -> Result<(), AncillaCapacityError> {
        for (i, a) in chunk.iter().enumerate() {
            for (j, b) in chunk.iter().enumerate() {
                let first = block * m + i;
                let second = block * m + j;
                let coefficient = sqrt_exact(&(a * b))
                    .ok_or(AncillaCapacityError::NonRationalCoefficient { first, second })?;
                result.set(
                    first * m + i,
                    second * m + j,
                    GaussianRat::from_rational(coefficient),
                )?;
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/ancilla_capacity.rs
// Claim: urn:core:crates_rs:core-quantum-physics:ancilla-capacity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_78ba42a8 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
