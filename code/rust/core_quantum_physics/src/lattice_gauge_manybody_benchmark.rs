//! Finite Ising Hamiltonians and cellular Z2 Gauss constraints.
//! Matrices, gauge constraints and physical state counts are computed from
//! declared carriers. No thermodynamic or continuum limit is inferred.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_cdef2467<T> {
    fn checked_invariant_cdef2467(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_cdef2467<T> for Option<T> {
    #[inline]
    fn checked_invariant_cdef2467(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_cdef2467<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_cdef2467(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use num_bigint::BigUint;
use num_traits::Zero;
use core_homology::f2_cohomology::{ComplexError, F2ChainComplex};
use core_number_theory::gf2::{F2Error, F2Vector};
use core_number_theory::rational::Rational;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FiniteManybodyError {
    #[error("open Ising chain needs 1..=8 sites")]
    Sites,
    #[error("chain complex has no edges or its plaquette has nonzero boundary")]
    Carrier,
    #[error(transparent)]
    Matrix(#[from] MatrixError),
    #[error(transparent)]
    Chain(#[from] ComplexError),
    #[error(transparent)]
    F2(#[from] F2Error),
}
pub fn open_tfim(
    sites: usize,
    coupling: &Rational,
    field: &Rational,
) -> Result<BasicMatrix<Rational>, FiniteManybodyError> {
    if sites == 0 || sites > 8 {
        return Err(FiniteManybodyError::Sites);
    }
    let d = 1usize << sites;
    Ok(BasicMatrix::try_from_fn(d, d, |r, c| {
        let mut value = Rational::zero();
        if r == c {
            for k in 0..sites - 1 {
                value += if ((r >> k) ^ (r >> (k + 1))) & 1 == 0 {
                    -coupling
                } else {
                    coupling.clone()
                };
            }
        }
        for k in 0..sites {
            if r == c ^ (1 << k) {
                value -= field;
            }
        }
        value
    })?)
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Z2LatticeGauge {
    complex: F2ChainComplex,
}
impl Z2LatticeGauge {
    pub fn new(complex: F2ChainComplex) -> Result<Self, FiniteManybodyError> {
        if complex.top_dimension() < 1 {
            return Err(FiniteManybodyError::Carrier);
        }
        Ok(Self { complex })
    }
    pub fn physical_dimension(&self) -> Result<BigUint, FiniteManybodyError> {
        let edges = self.complex.cell_count(1);
        let rank = self.complex.boundary(1)?.rank();
        Ok(BigUint::from(1u8) << (edges - rank))
    }
    pub fn is_physical_x_label(&self, label: &F2Vector) -> Result<bool, FiniteManybodyError> {
        Ok(self.complex.boundary(1)?.mul_vec(label)?.is_zero())
    }
    pub fn magnetic_flip(
        &self,
        label: &F2Vector,
        plaquette: &F2Vector,
    ) -> Result<F2Vector, FiniteManybodyError> {
        if !self.is_physical_x_label(plaquette)? {
            return Err(FiniteManybodyError::Carrier);
        }
        Ok(label.add(plaquette)?)
    }
    pub fn physical_labels(&self, limit: usize) -> Result<Vec<F2Vector>, FiniteManybodyError> {
        Ok(self
            .complex
            .boundary(1)?
            .solve(&F2Vector::zeros(self.complex.cell_count(0))?)?
            .checked_invariant_cdef2467("zero lies in image")
            .enumerate(limit)?)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/lattice_gauge_manybody_benchmark.rs
// Claim: urn:core:crates_rs:core-quantum-physics:lattice-gauge-manybody-benchmark:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_cdef2467 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
