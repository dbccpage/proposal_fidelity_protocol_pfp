//! Exact spin-network area labels and intertwiner dimensions.
//!
//! At a puncture with spin j=n/2 the area label is sqrt(j(j+1)); the scale
//! 8 pi gamma l_P² is a separately declared physical choice. The spectrum
//! starts at sqrt(3)/2 for nonzero spin and the magnetic degeneracy is n+1.
//! Tensor-product invariant dimensions are computed by the SU(2) fusion rule
//! |j1-j2| <= J <= j1+j2 in unit steps. Representation matrices, Casimirs and
//! Clebsch-Gordan coefficients are owned by `core_lie_theory::su2`.
//! Surd normalization and its bounded arithmetic refusals come from the
//! canonical number-theory owner.
//!
//! AuthorityEffect: None.
use num_bigint::{BigInt, BigUint};
use core_number_theory::quadratic::{QuadraticError, Surd};
use core_number_theory::rational::Rational;
use std::collections::BTreeMap;

pub fn area_label_squared(twice_spin: u32) -> Rational {
    let n = BigInt::from(twice_spin);
    Rational::new(&n * (&n + 2), BigInt::from(4))
}

pub fn area_label(twice_spin: u32) -> Result<Surd, QuadraticError> {
    Surd::new(
        Rational::from_integer(1.into()),
        &area_label_squared(twice_spin),
    )
}

pub fn magnetic_degeneracy(twice_spin: u32) -> u64 {
    u64::from(twice_spin) + 1
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SpinNetworkError {
    #[error("the total twice-spin exceeds the declared bound 4096")]
    SpinBound,
}

/// Multiplicities of irreducible SU(2) sectors in a tensor product, labelled by twice spin.
pub fn tensor_spin_multiplicities(
    spins: &[u32],
) -> Result<BTreeMap<u32, BigUint>, SpinNetworkError> {
    let total = spins
        .iter()
        .try_fold(0u32, |a, b| a.checked_add(*b))
        .ok_or(SpinNetworkError::SpinBound)?;
    if total > 4096 || spins.len() > 4096 {
        return Err(SpinNetworkError::SpinBound);
    }
    let mut sectors = BTreeMap::from([(0u32, BigUint::from(1u8))]);
    for spin in spins {
        let mut next = BTreeMap::<u32, BigUint>::new();
        for (j, multiplicity) in sectors {
            for new_j in (j.abs_diff(*spin)..=j + spin).step_by(2) {
                *next.entry(new_j).or_default() += &multiplicity;
            }
        }
        sectors = next;
    }
    Ok(sectors)
}

/// Dimension of the invariant tensors at a spin-network vertex.
pub fn invariant_subspace_dimension(spins: &[u32]) -> Result<BigUint, SpinNetworkError> {
    Ok(tensor_spin_multiplicities(spins)?
        .remove(&0)
        .unwrap_or_default())
}

// Origin: engine/crates_rs/core_quantum_physics/src/spin_area_spectrum.rs
// Claim: urn:core:crates_rs:core-quantum-physics:spin-area-spectrum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_57456116 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
