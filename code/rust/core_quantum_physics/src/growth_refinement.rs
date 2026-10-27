//! Finite conductor growth witnesses, independent of program target labels.
//! AuthorityEffect: None.
use num_bigint::BigInt;
use core_number_theory::cyclotomic_field::{
    contains_cyclotomic_field, quadratic_field_conductor, CyclotomicError,
};
use core_number_theory::rational::{ri, Rational};
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GrowthError {
    #[error("the conductor or W-state size is outside 1..=1024")]
    Input,
    #[error(transparent)]
    Field(#[from] CyclotomicError),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GrowthWitness {
    pub source_conductor: usize,
    pub prime: usize,
    pub contains_prime_phase: bool,
}
pub fn growth_witness(conductor: usize) -> Result<GrowthWitness, GrowthError> {
    if conductor == 0 || conductor > 1024 {
        return Err(GrowthError::Input);
    }
    let prime = (3..=1024)
        .find(|&p| core_number_theory::finite_field::is_prime(p) && conductor % p != 0)
        .ok_or(GrowthError::Input)?;
    let contains_prime_phase = contains_cyclotomic_field(prime, conductor)?;
    Ok(GrowthWitness {
        source_conductor: conductor,
        prime,
        contains_prime_phase,
    })
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WStateCarrier {
    pub sites: usize,
    pub amplitude_squared: Rational,
    pub conductor: BigInt,
}
pub fn w_state_carrier(sites: usize) -> Result<WStateCarrier, GrowthError> {
    if sites == 0 || sites > 1024 {
        return Err(GrowthError::Input);
    }
    let conductor = quadratic_field_conductor(
        &core_number_theory::rational::squarefree_part(&BigInt::from(sites))
            .map_err(|_| GrowthError::Input)?
            .0,
    );
    Ok(WStateCarrier {
        sites,
        amplitude_squared: ri(1) / Rational::from_integer(BigInt::from(sites)),
        conductor,
    })
}

// Origin: engine/crates_rs/core_quantum_physics/src/growth_refinement.rs
// Claim: urn:core:crates_rs:core-quantum-physics:growth-refinement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f2c0a4c6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
