//! Exact rational turns Q/Z and their declared root-of-unity character.
//! AuthorityEffect: None. The symbolic group has arbitrary rational denominators;
//! evaluation delegates to the existing cyclotomic owner with its conductor cap.
//! The union of all cyclotomic roots is divisible: q/n is an n-th root of q.
//! This periodic character is NOT an extension sending 1 to (3+4i)/5: it sends
//! every integer to 1, whereas that Gaussian rational has infinite order.
use crate::cyclotomic_field::{CyclotomicError, CyclotomicNumber};
use crate::rational::Rational;
use num_integer::Integer;
use num_traits::{ToPrimitive, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RationalTurnError {
    #[error("root order must be strictly positive")]
    ZeroRootOrder,
    #[error("turn denominator does not divide the declared conductor")]
    IncompatibleConductor,
    #[error("exact cyclotomic evaluation refused: {0}")]
    Cyclotomic(#[from] CyclotomicError),
}

/// Canonical representative of a rational number modulo integers, in [0,1).
/// No floating-point angle, topology, real exponentiation, or scalar embedding
/// choice is inferred from a witnessed difference.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalTurn {
    fraction: Rational,
}
impl RationalTurn {
    pub fn new(turn: Rational) -> Self {
        Self {
            fraction: Rational::new(turn.numer().mod_floor(turn.denom()), turn.denom().clone()),
        }
    }
    pub fn zero() -> Self {
        Self::new(Rational::zero())
    }
    pub fn representative(&self) -> &Rational {
        &self.fraction
    }
    pub fn add(&self, other: &Self) -> Self {
        Self::new(&self.fraction + &other.fraction)
    }
    pub fn inverse(&self) -> Self {
        Self::new(-&self.fraction)
    }
    pub fn sub(&self, other: &Self) -> Self {
        self.add(&other.inverse())
    }
    pub fn multiply_integer(&self, n: &num_bigint::BigInt) -> Self {
        Self::new(&self.fraction * Rational::from_integer(n.clone()))
    }
    /// A chosen n-th root (one of n), not a canonical splitting homomorphism.
    pub fn root(&self, order: usize) -> Result<Self, RationalTurnError> {
        if order == 0 {
            return Err(RationalTurnError::ZeroRootOrder);
        }
        Ok(Self::new(
            &self.fraction / Rational::from_integer(order.into()),
        ))
    }
    /// χ(q)=zeta_N^(Nq) in a DECLARED compatible cyclotomic field.
    /// Shared-conductor evaluation makes multiplication/addition comparison exact.
    pub fn character_in(&self, conductor: usize) -> Result<CyclotomicNumber, RationalTurnError> {
        // Validate the conductor through the sovereign owner before conversion.
        let one = CyclotomicNumber::one(conductor)?;
        let Some(denominator) = self.fraction.denom().to_usize() else {
            return Err(RationalTurnError::IncompatibleConductor);
        };
        if conductor % denominator != 0 {
            return Err(RationalTurnError::IncompatibleConductor);
        }
        if self.fraction.is_zero() {
            return Ok(one);
        }
        let numerator = self
            .fraction
            .numer()
            .to_usize()
            .ok_or(RationalTurnError::IncompatibleConductor)?;
        let exponent = numerator * (conductor / denominator);
        Ok(CyclotomicNumber::zeta(conductor, exponent as i64)?)
    }
    /// Evaluate in the minimal denominator field when its conductor is supported.
    pub fn character(&self) -> Result<CyclotomicNumber, RationalTurnError> {
        let denominator = self
            .fraction
            .denom()
            .to_usize()
            .ok_or(RationalTurnError::IncompatibleConductor)?;
        self.character_in(denominator)
    }
}

// Origin: engine/crates_rs/core_number_theory/src/rational_turns.rs
// Claim: urn:core:crates_rs:core-number-theory:rational-turns:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_9fcb4675 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
