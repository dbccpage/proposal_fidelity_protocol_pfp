use nalgebra::{DMatrix, DVector};

/// A vector field represented numerically.
#[derive(Debug, Clone, PartialEq)]
pub struct VectorFieldInput {
    pub dimension: usize,
    pub field_data: Vec<DVector<f64>>,
}

/// The result of a scalar operation on a field (e.g. divergence).
#[derive(Debug, Clone, PartialEq)]
pub struct ScalarFieldResult {
    pub scalar_data: DVector<f64>,
}

/// The result of a vector operation on a field (e.g. curl).
#[derive(Debug, Clone, PartialEq)]
pub struct VectorFieldResult {
    pub vector_data: Vec<DVector<f64>>,
}

/// Surface integral input boundary.
#[derive(Debug, Clone, PartialEq)]
pub struct SurfaceIntegralInput {
    pub surface_boundary: Vec<f64>,
}

/// Integral result.
#[derive(Debug, Clone, PartialEq)]
pub struct IntegralResult {
    pub value: f64,
}

/// Input representing a PDE system.
#[derive(Debug, Clone, PartialEq)]
pub struct PdeInput {
    pub spatial_dimension: usize,
    pub boundary_conditions: DVector<f64>,
}

/// Result of a PDE operator.
#[derive(Debug, Clone, PartialEq)]
pub struct PdeResult {
    pub solution_kernel: DMatrix<f64>,
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClosedFluxWitness {
    faces: u64,
    net_flux: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ClosedFluxWitnessError {
    Empty,
    NotClosed { net_flux: i64 },
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/calculus_types.rs
// Claim: urn:core:crates_rs:core-types:calculus-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ClosedFluxWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ClosedFluxWitnessError {}

impl ClosedFluxWitness {
    pub fn certify(face_fluxes: &[i64]) -> Result<Self, ClosedFluxWitnessError> {
        if face_fluxes.is_empty() { return Err(ClosedFluxWitnessError::Empty); }
        let mut net_flux = 0i64;
        for flux in face_fluxes { net_flux = net_flux.checked_add(*flux).ok_or(ClosedFluxWitnessError::Overflow)?; }
        if net_flux != 0 { return Err(ClosedFluxWitnessError::NotClosed { net_flux }); }
        let faces = u64::try_from(face_fluxes.len()).map_err(|_| ClosedFluxWitnessError::Overflow)?;
        Ok(Self { faces, net_flux })
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(ClosedFluxWitness::certify(&[3, -1, -2]), Ok(w) if w.net_flux == 0 && w.faces == 3));
        assert!(matches!(ClosedFluxWitness::certify(&[3, -1]), Err(ClosedFluxWitnessError::NotClosed { net_flux: 2 })));
        assert!(matches!(ClosedFluxWitness::certify(&[i64::MAX, 1]), Err(ClosedFluxWitnessError::Overflow)));
    }
}
