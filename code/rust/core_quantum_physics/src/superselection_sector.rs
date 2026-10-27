//! Superselection by minimal central projections of a finite star-algebra.
//! Rational spectra are computed and replayed; an unsplit number-field center
//! is a typed refusal rather than a fabricated decomposition.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::{
    exact_hermitian::{self, gi},
    local_operator_algebra::{AlgebraError, LocalOperatorAlgebra},
};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::characteristic_polynomial::characteristic_polynomial;
use linear_algebra::exact_field::{involution, matrix};
use num_traits::ToPrimitive;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::polynomial::{rational_roots, Polynomial};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact finite central sectors.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SectorError {
    #[error(transparent)]
    ExactAlgebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error(transparent)]
    Algebra(#[from] AlgebraError),
    #[error("center does not split over the Gaussian rational field")]
    NonsplitCenter,
    #[error("matrix or spectral computation refused: {0}")]
    Matrix(String),
    #[error("sector is not a simple matrix block on its support")]
    NonMatrixBlock,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SuperselectionSector {
    projection: BasicMatrix<GaussianRat>,
    support_dimension: usize,
    block_size: usize,
    multiplicity: usize,
}
impl SuperselectionSector {
    pub fn projection(&self) -> &BasicMatrix<GaussianRat> {
        &self.projection
    }
    pub fn support_dimension(&self) -> usize {
        self.support_dimension
    }
    pub fn block_size(&self) -> usize {
        self.block_size
    }
    pub fn multiplicity(&self) -> usize {
        self.multiplicity
    }
    fn hermitian_components_of_generator(
        b: &BasicMatrix<GaussianRat>,
    ) -> Result<[BasicMatrix<GaussianRat>; 2], SectorError> {
        let adj = involution::adjoint(b)?;
        let real_part = matrix::add(b, &adj)?;
        let imag_part = matrix::scale(&matrix::sub(b, &adj)?, &gi(0, 1))?;
        Ok([real_part, imag_part])
    }
    fn refine_projections_by_hermitian(
        projections: &[BasicMatrix<GaussianRat>],
        h: &BasicMatrix<GaussianRat>,
    ) -> Result<Vec<BasicMatrix<GaussianRat>>, SectorError> {
        let coefficients =
            characteristic_polynomial(h).map_err(|e| SectorError::Matrix(e.to_string()))?;
        if coefficients.iter().any(|c| !c.is_real()) {
            return Err(SectorError::NonsplitCenter);
        }
        let poly =
            Polynomial::from_coefficients(coefficients.iter().map(|c| c.re.clone()).collect());
        let roots = rational_roots(&poly).map_err(|e| SectorError::Matrix(e.to_string()))?;
        let resolution = exact_hermitian::spectral_resolution(h, &roots)
            .map_err(|_| SectorError::NonsplitCenter)?;
        let mut refined = Vec::new();
        for p in projections {
            for q in resolution.projectors() {
                let r = matrix::multiply(p, q)?;
                if !matrix::is_zero_matrix(&r) {
                    refined.push(r);
                }
            }
        }
        Ok(refined)
    }
    fn build_sector_from_projection(
        algebra: &LocalOperatorAlgebra,
        n: usize,
        p: BasicMatrix<GaussianRat>,
    ) -> Result<Self, SectorError> {
        let support_dimension = matrix::trace(&p)?
            .re
            .to_usize()
            .ok_or(SectorError::NonMatrixBlock)?;
        let compressed: Vec<_> = algebra
            .basis()
            .iter()
            .map(|a| matrix::multiply(&p, a))
            .collect::<Result<Vec<_>, _>>()?;
        let block = LocalOperatorAlgebra::from_generators(n, &compressed, 1 << 18)?;
        // from_generators adds I; subtract its extra complementary central direction.
        let block_dimension = block.dimension() - usize::from(support_dimension < n);
        let block_size = (1..=n)
            .find(|&k| k * k == block_dimension)
            .ok_or(SectorError::NonMatrixBlock)?;
        if support_dimension % block_size != 0 {
            return Err(SectorError::NonMatrixBlock);
        }
        let out = Self {
            projection: p,
            support_dimension,
            block_size,
            multiplicity: support_dimension / block_size,
        };
        Ok(out)
    }
    /// Refine commuting central spectral projectors until their count equals
    /// the center dimension; this certifies minimality for a split center.
    pub fn decompose(algebra: &LocalOperatorAlgebra) -> Result<Vec<Self>, SectorError> {
        let center = algebra.center()?;
        let n = algebra.hilbert_dimension();
        let mut projections = vec![matrix::identity(n)?];
        for b in center.basis() {
            for h in Self::hermitian_components_of_generator(b)? {
                projections = Self::refine_projections_by_hermitian(&projections, &h)?;
            }
        }
        if projections.len() != center.dimension() {
            return Err(SectorError::NonsplitCenter);
        }
        let mut sectors = Vec::new();
        for p in projections {
            sectors.push(Self::build_sector_from_projection(algebra, n, p)?);
        }
        Ok(sectors)
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
fn validate_sector_projector_and_orthogonality(
    n: usize,
    s: &SuperselectionSector,
    previous: &[SuperselectionSector],
) -> Result<(), SectorError> {
    if exact_hermitian::square_dim(&s.projection)
        .map_err(|e| SectorError::Matrix(e.to_string()))?
        != n
        || !exact_hermitian::is_hermitian(&s.projection)
        || matrix::multiply(&s.projection, &s.projection)? != s.projection
    {
        return Err(SectorError::NonMatrixBlock);
    }
    for t in previous {
        if !matrix::is_zero_matrix(&matrix::multiply(&s.projection, &t.projection)?) {
            return Err(SectorError::NonMatrixBlock);
        }
    }
    Ok(())
}
fn sandwich_and_accumulate_sector(
    rho: &BasicMatrix<GaussianRat>,
    s: &SuperselectionSector,
    sum: &mut BasicMatrix<GaussianRat>,
    result: &mut BasicMatrix<GaussianRat>,
) -> Result<(), SectorError> {
    *sum = matrix::add(sum, &s.projection)?;
    let left = matrix::multiply(&s.projection, rho)?;
    let pinched_block = matrix::multiply(&left, &s.projection)?;
    *result = matrix::add(result, &pinched_block)?;
    Ok(())
}
/// Nonselective central measurement. Validate all projections, completeness and
/// orthogonality before applying the idempotent pinching channel.
pub fn pinching(
    rho: &BasicMatrix<GaussianRat>,
    sectors: &[SuperselectionSector],
) -> Result<BasicMatrix<GaussianRat>, SectorError> {
    let n = exact_hermitian::square_dim(rho).map_err(|e| SectorError::Matrix(e.to_string()))?;
    let mut sum = matrix::zeros(n, n)?;
    let mut result = matrix::zeros(n, n)?;
    for (i, s) in sectors.iter().enumerate() {
        validate_sector_projector_and_orthogonality(n, s, &sectors[..i])?;
        sandwich_and_accumulate_sector(rho, s, &mut sum, &mut result)?;
    }
    if sum != matrix::identity(n)? {
        return Err(SectorError::NonMatrixBlock);
    }
    Ok(result)
}
pub fn superselection_rule_holds(
    rho: &BasicMatrix<GaussianRat>,
    algebra: &LocalOperatorAlgebra,
) -> Result<bool, SectorError> {
    if rho.rows() != algebra.hilbert_dimension() {
        return Err(SectorError::NonMatrixBlock);
    }
    let dephased = pinching(rho, &SuperselectionSector::decompose(algebra)?)?;
    for a in algebra.basis() {
        if matrix::trace(&matrix::multiply(a, rho)?)?
            != matrix::trace(&matrix::multiply(a, &dephased)?)?
        {
            return Ok(false);
        }
    }
    Ok(true)
}
// Origin: engine/crates_rs/core_quantum_physics/src/superselection_sector.rs
// Claim: urn:core:crates_rs:core-quantum-physics:superselection-sector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::majorana_fock_algebra::FockCarrier;
    #[test]
    fn parity_sectors_are_minimal_central_blocks_and_hide_cross_sector_phase() {
        let f = FockCarrier::new(2).unwrap();
        let g = f.majoranas();
        let products: Vec<_> = (0..4)
            .flat_map(|i| {
                let g = &g;
                (i + 1..4).map(move |j| matrix::multiply(&g[i], &g[j]).unwrap())
            })
            .collect();
        let algebra = LocalOperatorAlgebra::from_generators(4, &products, 4096).unwrap();
        let sectors = SuperselectionSector::decompose(&algebra).unwrap();
        assert_eq!(sectors.len(), 2);
        assert!(sectors
            .iter()
            .all(|s| s.block_size() == 2 && s.multiplicity() == 1));
        assert_eq!(
            sectors
                .iter()
                .map(|s| s.block_size() * s.block_size())
                .sum::<usize>(),
            algebra.dimension()
        );
        let mut rho = matrix::zeros(4, 4).unwrap();
        for i in 0..2 {
            for j in 0..2 {
                rho.set(i, j, crate::exact_hermitian::gq(1, 2, 0, 1))
                    .unwrap();
            }
        }
        assert!(superselection_rule_holds(&rho, &algebra).unwrap());
        let pinched = pinching(&rho, &sectors).unwrap();
        assert_eq!(pinching(&pinched, &sectors).unwrap(), pinched);
        assert_ne!(rho, pinched);
    }
}
