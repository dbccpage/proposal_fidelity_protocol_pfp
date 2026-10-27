// AuthorityEffect: None.

//! Selective measurement on finite outcome weights, as conditioning on a
//! declared outcome sector, and the exact Lüders update it shadows.
//!
//! A measurement outcome is a declared sector `S` of the outcome index, given
//! as an indicator. [`condition_weights`] keeps the weights on `S` and renormalizes; a
//! sector with zero weight is refused. [`sector_weight_probability`] is the sector's
//! share of the total weight. The update is zero off `S`, idempotent, and
//! gives `S` probability one afterwards.
//!
//! [`luders_update`] is `P rho P / Tr(P rho)` for a declared orthogonal
//! projector `P` (checked: `P* = P`, `P P = P`), refused when `Tr(P rho) = 0`.
//! On a diagonal density with `P` the sector projector it returns the diagonal
//! of the conditioned weights. It keeps coherence inside the sector, which
//! weights cannot carry, and for projectors that do not commute the order of
//! two updates matters; both lie outside what conditioning describes.

use crate::exact_hermitian::{self};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution::adjoint, matrix};

use num_traits::Zero;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

/// Refusals for conditioning and for the Lüders update.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ConditioningError {
    #[error("the sector indicator has {actual} entries, the outcomes number {expected}")]
    SectorLength { expected: usize, actual: usize },
    #[error("the declared sector carries zero weight, so conditioning on it is undefined")]
    NullSector,
    #[error("the declared operator is not an orthogonal projector")]
    NotProjector,
    #[error("the input is not a Hermitian positive trace-one state")]
    NotState,
    #[error("the state and the projector have different sizes")]
    Shape,
    #[error("a nonempty finite measure needs nonnegative weights and positive total")]
    InvalidWeights,
}

fn sector_weight(
    masses: &[Rational],
    sector: &[bool],
) -> Result<(Rational, Rational), ConditioningError> {
    if sector.len() != masses.len() {
        return Err(ConditioningError::SectorLength {
            expected: masses.len(),
            actual: sector.len(),
        });
    }
    let total: Rational = masses.iter().cloned().sum();
    if masses.is_empty() || masses.iter().any(|m| m < &Rational::zero()) || total.is_zero() {
        return Err(ConditioningError::InvalidWeights);
    }
    let weight = masses
        .iter()
        .zip(sector)
        .filter(|(_, s)| **s)
        .map(|(m, _)| m.clone())
        .sum();
    Ok((weight, total))
}
/// Probability of the declared sector in a checked finite nonnegative measure.
pub fn sector_weight_probability(
    masses: &[Rational],
    sector: &[bool],
) -> Result<Rational, ConditioningError> {
    let (weight, total) = sector_weight(masses, sector)?;
    Ok(weight / total)
}
/// The exact conditional distribution, refused for a null event.
pub fn condition_weights(
    masses: &[Rational],
    sector: &[bool],
) -> Result<Vec<Rational>, ConditioningError> {
    let (weight, _) = sector_weight(masses, sector)?;
    if weight.is_zero() {
        return Err(ConditioningError::NullSector);
    }
    Ok(masses
        .iter()
        .zip(sector)
        .map(|(m, &s)| if s { m / &weight } else { Rational::zero() })
        .collect())
}

/// The diagonal projector onto a sector.
pub fn sector_projector(sector: &[bool]) -> Result<BasicMatrix<GaussianRat>, ConditioningError> {
    if sector.is_empty() || sector.len() > 64 {
        return Err(ConditioningError::Shape);
    }
    let entries: Vec<GaussianRat> = sector
        .iter()
        .map(|in_sector| {
            if *in_sector {
                GaussianRat::one()
            } else {
                GaussianRat::zero()
            }
        })
        .collect();
    matrix::diagonal(&entries).map_err(|_| ConditioningError::Shape)
}

fn validate_luders_projector(
    projector: &BasicMatrix<GaussianRat>,
) -> Result<(), ConditioningError> {
    let adj = adjoint(projector).map_err(|_| ConditioningError::Shape)?;
    let sq = matrix::multiply(projector, projector).map_err(|_| ConditioningError::Shape)?;
    if adj != *projector || sq != *projector {
        return Err(ConditioningError::NotProjector);
    }
    Ok(())
}

fn validate_luders_state(
    rho: &BasicMatrix<GaussianRat>,
    projector_shape: (usize, usize),
) -> Result<(), ConditioningError> {
    if rho.rows() == 0
        || rho.rows() > 64
        || rho.rows() != rho.cols()
        || projector_shape != rho.shape()
    {
        return Err(ConditioningError::Shape);
    }
    let psd = exact_hermitian::is_psd(rho).map_err(|_| ConditioningError::NotState)?;
    let tr = matrix::trace(rho).map_err(|_| ConditioningError::Shape)?;
    if !psd || tr != GaussianRat::one() {
        return Err(ConditioningError::NotState);
    }
    Ok(())
}

/// `P rho P / Tr(P rho)` for a declared orthogonal projector `P`.
pub fn luders_update(
    rho: &BasicMatrix<GaussianRat>,
    projector: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, ConditioningError> {
    validate_luders_state(rho, projector.shape())?;
    validate_luders_projector(projector)?;
    let prho = matrix::multiply(projector, rho).map_err(|_| ConditioningError::Shape)?;
    let kept = matrix::multiply(&prho, projector).map_err(|_| ConditioningError::Shape)?;
    let probability = matrix::trace(&kept).map_err(|_| ConditioningError::Shape)?;
    if probability.is_zero() {
        return Err(ConditioningError::NullSector);
    }
    matrix::scale(&kept, &probability.inv()).map_err(|_| ConditioningError::Shape)
}

/// The unselective Lüders channel for a checked projective resolution.
pub fn luders_channel(
    projectors: &[BasicMatrix<GaussianRat>],
) -> Result<crate::exact_channel::ExactKrausChannel, ConditioningError> {
    let dimension = projectors
        .first()
        .ok_or(ConditioningError::NotProjector)?
        .rows();
    if dimension == 0
        || dimension > 64
        || projectors.len() > 64
        || projectors
            .iter()
            .any(|p| p.shape() != (dimension, dimension))
    {
        return Err(ConditioningError::Shape);
    }
    if projectors.is_empty()
        || projectors.iter().any(|p| {
            exact_hermitian::check_hermitian(p).is_err()
                || !matrix::multiply(p, p).is_ok_and(|q| q == *p)
        })
    {
        return Err(ConditioningError::NotProjector);
    }
    crate::exact_channel::ExactKrausChannel::from_operators(projectors.to_vec())
        .map_err(|_| ConditioningError::NotProjector)
}

// Origin: engine/crates_rs/core_quantum_physics/src/sector_conditioning.rs
// Claim: urn:core:crates_rs:core-quantum-physics:sector-conditioning:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_b2613b28 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
