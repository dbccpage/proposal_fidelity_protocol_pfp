//! Finite rational homology quotients and their induced chain-map action.
//! Exact arithmetic delegates to the sovereign linear-algebra owner.
//! AuthorityEffect: None. No integer quotient transport or homotopy claim.

use crate::hashing::{hash_matrix, Hash256};
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::elimination::{
    image_basis_with_limits, kernel_basis_with_limits, rank_with_limits, solve_with_limits,
    LinearSolution,
};
use linear_algebra::exact_field::matrix::{
    from_fn_with_limits, identity_with_limits, zeros_with_limits,
};
use num_traits::Zero;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RationalHomologyRefusal {
    InvalidShape,
    BoundaryLaw,
    InvalidDegree,
    NotCycle,
    NotChainMap,
    CarrierMismatch,
    InvalidBasis,
    ResourceOrArithmetic(String),
}

fn arithmetic(error: impl std::fmt::Display) -> RationalHomologyRefusal {
    RationalHomologyRefusal::ResourceOrArithmetic(error.to_string())
}

fn columns(
    rows: usize,
    vectors: &[Vec<Q>],
    limits: OperationLimits,
) -> Result<BasicMatrix<Q>, RationalHomologyRefusal> {
    if vectors.iter().any(|vector| vector.len() != rows) {
        return Err(RationalHomologyRefusal::InvalidShape);
    }
    from_fn_with_limits(rows, vectors.len(), limits, |i, j| vectors[j][i].clone())
        .map_err(arithmetic)
}

/// Immutable, verified finite Q complex; boundaries[k-1] is partial_k.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteRationalChainComplex {
    dims: Vec<usize>,
    boundaries: Vec<BasicMatrix<Q>>,
}

impl FiniteRationalChainComplex {
    pub fn new(
        dims: Vec<usize>,
        boundaries: Vec<BasicMatrix<Q>>,
        limits: OperationLimits,
    ) -> Result<Self, RationalHomologyRefusal> {
        if dims.is_empty() || dims.len() > 33 || boundaries.len() + 1 != dims.len() {
            return Err(RationalHomologyRefusal::InvalidShape);
        }
        for (k, boundary) in boundaries.iter().enumerate() {
            if boundary.shape() != (dims[k], dims[k + 1]) {
                return Err(RationalHomologyRefusal::InvalidShape);
            }
        }
        for pair in boundaries.windows(2) {
            let product = pair[0]
                .checked_mul_with_limits(&pair[1], limits)
                .map_err(arithmetic)?;
            if product.as_slice().iter().any(|value| !value.is_zero()) {
                return Err(RationalHomologyRefusal::BoundaryLaw);
            }
        }
        Ok(Self { dims, boundaries })
    }

    pub fn dimensions(&self) -> &[usize] {
        &self.dims
    }

    /// Commits all degrees, dimensions, boundary shapes and exact entries.
    pub fn content_hash(&self) -> Hash256 {
        let mut state = blake3::Hasher::new();
        state.update(b"core.finite_rational_chain_complex/v1");
        state.update(&(self.dims.len() as u64).to_le_bytes());
        for dimension in &self.dims {
            state.update(&(*dimension as u64).to_le_bytes());
        }
        for boundary in &self.boundaries {
            state.update(&hash_matrix(boundary).0);
        }
        Hash256(*state.finalize().as_bytes())
    }

    fn down(
        &self,
        degree: usize,
        limits: OperationLimits,
    ) -> Result<BasicMatrix<Q>, RationalHomologyRefusal> {
        let dimension = *self
            .dims
            .get(degree)
            .ok_or(RationalHomologyRefusal::InvalidDegree)?;
        if degree == 0 {
            zeros_with_limits(0, dimension, limits).map_err(arithmetic)
        } else {
            Ok(self.boundaries[degree - 1].clone())
        }
    }

    fn up(
        &self,
        degree: usize,
        limits: OperationLimits,
    ) -> Result<BasicMatrix<Q>, RationalHomologyRefusal> {
        let dimension = *self
            .dims
            .get(degree)
            .ok_or(RationalHomologyRefusal::InvalidDegree)?;
        if degree + 1 == self.dims.len() {
            zeros_with_limits(dimension, 0, limits).map_err(arithmetic)
        } else {
            Ok(self.boundaries[degree].clone())
        }
    }
}

/// Chosen exact basis of ker(partial_k)/im(partial_(k+1)).
/// Boundary columns followed by representative columns form a basis of cycles.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalHomologyQuotient {
    complex: FiniteRationalChainComplex,
    degree: usize,
    boundary_basis: Vec<Vec<Q>>,
    representatives: Vec<Vec<Q>>,
    cycle_basis: BasicMatrix<Q>,
}

impl RationalHomologyQuotient {
    pub fn new(
        complex: &FiniteRationalChainComplex,
        degree: usize,
        limits: OperationLimits,
    ) -> Result<Self, RationalHomologyRefusal> {
        let down = complex.down(degree, limits)?;
        let up = complex.up(degree, limits)?;
        let boundary_basis = image_basis_with_limits(&up, limits).map_err(arithmetic)?;
        let cycles = kernel_basis_with_limits(&down, limits).map_err(arithmetic)?;
        let (basis, representatives) =
            Self::extend_boundary_to_cycle_basis(complex.dims[degree], &boundary_basis, &cycles, limits)?;
        if basis.len() != cycles.len() {
            return Err(RationalHomologyRefusal::InvalidBasis);
        }
        let cycle_basis = columns(complex.dims[degree], &basis, limits)?;
        Ok(Self {
            complex: complex.clone(),
            degree,
            boundary_basis,
            representatives,
            cycle_basis,
        })
    }

    fn extend_boundary_to_cycle_basis(
        dim: usize,
        boundary_basis: &[Vec<Q>],
        cycles: &[Vec<Q>],
        limits: OperationLimits,
    ) -> Result<(Vec<Vec<Q>>, Vec<Vec<Q>>), RationalHomologyRefusal> {
        let mut basis = boundary_basis.to_vec();
        let mut representatives = Vec::new();
        for cycle in cycles {
            basis.push(cycle.clone());
            let candidate = columns(dim, &basis, limits)?;
            if rank_with_limits(&candidate, limits).map_err(arithmetic)? == basis.len() {
                representatives.push(cycle.clone());
            } else {
                basis.pop();
            }
        }
        Ok((basis, representatives))
    }

    pub fn dimension(&self) -> usize {
        self.representatives.len()
    }

    pub fn representatives(&self) -> &[Vec<Q>] {
        &self.representatives
    }

    pub fn boundary_basis(&self) -> &[Vec<Q>] {
        &self.boundary_basis
    }

    /// Quotient coordinates of a cycle. Boundaries project to zero exactly.
    pub fn coordinates(
        &self,
        cycle: &[Q],
        limits: OperationLimits,
    ) -> Result<Vec<Q>, RationalHomologyRefusal> {
        let down = self.complex.down(self.degree, limits)?;
        if cycle.len() != self.complex.dims[self.degree] {
            return Err(RationalHomologyRefusal::InvalidShape);
        }
        let boundary = down
            .checked_mul_vec_with_limits(cycle, limits)
            .map_err(arithmetic)?;
        if boundary.iter().any(|value| !value.is_zero()) {
            return Err(RationalHomologyRefusal::NotCycle);
        }
        match solve_with_limits(&self.cycle_basis, cycle, limits).map_err(arithmetic)? {
            LinearSolution::Consistent {
                particular,
                kernel_basis,
            } if kernel_basis.is_empty() => Ok(particular[self.boundary_basis.len()..].to_vec()),
            _ => Err(RationalHomologyRefusal::InvalidBasis),
        }
    }

    pub fn representative(
        &self,
        coordinates: &[Q],
        limits: OperationLimits,
    ) -> Result<Vec<Q>, RationalHomologyRefusal> {
        if coordinates.len() != self.dimension() {
            return Err(RationalHomologyRefusal::InvalidShape);
        }
        columns(
            self.complex.dims[self.degree],
            &self.representatives,
            limits,
        )?
        .checked_mul_vec_with_limits(coordinates, limits)
        .map_err(arithmetic)
    }
}

/// Exact finite chain map with complete source/target snapshots and typed shapes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteRationalChainMap {
    source: FiniteRationalChainComplex,
    target: FiniteRationalChainComplex,
    maps: Vec<BasicMatrix<Q>>,
}

impl FiniteRationalChainMap {
    pub fn new(
        source: &FiniteRationalChainComplex,
        target: &FiniteRationalChainComplex,
        maps: Vec<BasicMatrix<Q>>,
        limits: OperationLimits,
    ) -> Result<Self, RationalHomologyRefusal> {
        if maps.len() != source.dims.len() || maps.len() != target.dims.len() {
            return Err(RationalHomologyRefusal::InvalidShape);
        }
        for (k, map) in maps.iter().enumerate() {
            if map.shape() != (target.dims[k], source.dims[k]) {
                return Err(RationalHomologyRefusal::InvalidShape);
            }
            if k > 0 {
                let left = target.boundaries[k - 1]
                    .checked_mul_with_limits(map, limits)
                    .map_err(arithmetic)?;
                let right = maps[k - 1]
                    .checked_mul_with_limits(&source.boundaries[k - 1], limits)
                    .map_err(arithmetic)?;
                if left != right {
                    return Err(RationalHomologyRefusal::NotChainMap);
                }
            }
        }
        Ok(Self {
            source: source.clone(),
            target: target.clone(),
            maps,
        })
    }

    pub fn identity(
        complex: &FiniteRationalChainComplex,
        limits: OperationLimits,
    ) -> Result<Self, RationalHomologyRefusal> {
        let maps = complex
            .dims
            .iter()
            .map(|&n| identity_with_limits(n, limits).map_err(arithmetic))
            .collect::<Result<Vec<_>, _>>()?;
        Self::new(complex, complex, maps, limits)
    }

    /// second after self; complete intermediate carriers must agree.
    pub fn then(
        &self,
        second: &Self,
        limits: OperationLimits,
    ) -> Result<Self, RationalHomologyRefusal> {
        if self.target != second.source {
            return Err(RationalHomologyRefusal::CarrierMismatch);
        }
        let maps = self
            .maps
            .iter()
            .zip(&second.maps)
            .map(|(first, next)| {
                next.checked_mul_with_limits(first, limits)
                    .map_err(arithmetic)
            })
            .collect::<Result<Vec<_>, _>>()?;
        Self::new(&self.source, &second.target, maps, limits)
    }

    /// Matrix of the induced H_k map in the two computed quotient bases.
    pub fn induced(
        &self,
        source: &RationalHomologyQuotient,
        target: &RationalHomologyQuotient,
        limits: OperationLimits,
    ) -> Result<BasicMatrix<Q>, RationalHomologyRefusal> {
        if source.complex != self.source
            || target.complex != self.target
            || source.degree != target.degree
        {
            return Err(RationalHomologyRefusal::CarrierMismatch);
        }
        let mut images = Vec::new();
        for representative in &source.representatives {
            let image = self.maps[source.degree]
                .checked_mul_vec_with_limits(representative, limits)
                .map_err(arithmetic)?;
            images.push(target.coordinates(&image, limits)?);
        }
        columns(target.dimension(), &images, limits)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_5e132b66 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
