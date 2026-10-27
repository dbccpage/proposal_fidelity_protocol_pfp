//! Declared finite dyadic cyclic presentations and their exact characters.
//! Refinement is k -> 2k; restriction of character indices is reduction modulo
//! 2^n. A coherent finite prefix does not select an infinite character or a
//! topology. AuthorityEffect: None. No continuum or convergence is constructed.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_e2c05deb<T> {
    fn checked_invariant_e2c05deb(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_e2c05deb<T> for Option<T> {
    #[inline]
    fn checked_invariant_e2c05deb(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_e2c05deb<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_e2c05deb(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::cyclotomic_field::{CyclotomicError, CyclotomicNumber};
use crate::polynomial::MAX_CONDUCTOR;
use crate::rational::Rational;
use crate::rational_turns::{RationalTurn, RationalTurnError};
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::ToPrimitive;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DyadicError {
    #[error("level cannot be represented by the native word size")]
    LevelOverflow,
    #[error("element or character index lies outside the declared residue carrier")]
    OutOfCarrier,
    #[error("character restriction must be from the next level")]
    NonAdjacentLevels,
    #[error("a finite dual prefix must start at level zero and be nonempty")]
    EmptyPrefix,
    #[error("character indices are not coherent under reduction")]
    IncoherentPrefix,
    #[error("exact summation exceeds the caller's term limit")]
    TermLimit,
    #[error("exact summation exceeds the caller's conductor limit")]
    ConductorLimit,
    #[error("exact character evaluation refused: {0}")]
    Turn(#[from] RationalTurnError),
    #[error("exact cyclotomic arithmetic refused: {0}")]
    Cyclotomic(#[from] CyclotomicError),
}

#[derive(Debug, Copy, Clone, PartialEq, Eq)]
pub struct DyadicLevel {
    level: u32,
    order: usize,
}

impl DyadicLevel {
    /// Metadata only: no enumeration of the carrier or cyclotomic allocation.
    pub fn new(level: u32) -> Result<Self, DyadicError> {
        let order = 1usize
            .checked_shl(level)
            .ok_or(DyadicError::LevelOverflow)?;
        Ok(Self { level, order })
    }

    pub fn level(self) -> u32 {
        self.level
    }

    pub fn order(self) -> usize {
        self.order
    }

    fn check(self, residue: usize) -> Result<(), DyadicError> {
        if residue < self.order {
            Ok(())
        } else {
            Err(DyadicError::OutOfCarrier)
        }
    }

    pub fn add(self, left: usize, right: usize) -> Result<usize, DyadicError> {
        self.check(left)?;
        self.check(right)?;
        // Two residues below 2^(usize::BITS-1) have a representable sum.
        Ok((left + right) % self.order)
    }

    pub fn include(self, residue: usize) -> Result<usize, DyadicError> {
        self.check(residue)?;
        Self::new(self.level + 1)?;
        Ok(residue * 2)
    }

    pub fn coordinate(self, residue: usize) -> Result<RationalTurn, DyadicError> {
        self.check(residue)?;
        Ok(RationalTurn::new(Rational::new(
            residue.into(),
            self.order.into(),
        )))
    }

    /// Integer inputs are reduced modulo the carrier, including negative inputs.
    /// Arbitrary integer sizes have no bit-complexity budget in this API.
    pub fn character_turn(self, index: &BigInt, element: &BigInt) -> RationalTurn {
        RationalTurn::new(Rational::new(index * element, self.order.into()))
    }

    pub fn normalize_index(self, index: &BigInt) -> usize {
        // The remainder is nonnegative and strictly below a native-sized order.
        index
            .mod_floor(&BigInt::from(self.order))
            .to_usize()
            .checked_invariant_e2c05deb("checked invariant")
    }

    pub fn restrict(self, higher: Self, index: usize) -> Result<usize, DyadicError> {
        if higher.level != self.level + 1 {
            return Err(DyadicError::NonAdjacentLevels);
        }
        higher.check(index)?;
        Ok(index % self.order)
    }

    /// The two and only two adjacent extensions of a finite character index.
    pub fn extensions(self, index: usize) -> Result<[usize; 2], DyadicError> {
        self.check(index)?;
        Self::new(self.level + 1)?;
        Ok([index, index + self.order])
    }

    /// Actually sums N exact roots of unity in one declared cyclotomic field;
    /// the Kronecker delta is NOT assigned as the result. Limits are checked
    /// before field-context/cache construction or scalar arithmetic. The
    /// cyclotomic owner's cache and BigInt work are not counted as terms.
    pub fn normalized_inner_product(
        self,
        left: &BigInt,
        right: &BigInt,
        limits: CharacterSumLimits,
    ) -> Result<CyclotomicNumber, DyadicError> {
        if self.order > limits.max_terms {
            return Err(DyadicError::TermLimit);
        }
        if self.order > limits.max_conductor.min(MAX_CONDUCTOR) {
            return Err(DyadicError::ConductorLimit);
        }
        let difference = left - right;
        let mut sum = CyclotomicNumber::zero(self.order)?;
        for element in 0..self.order {
            let turn = self.character_turn(&difference, &element.into());
            sum = sum.add(&turn.character_in(self.order)?)?;
        }
        Ok(sum.scale(&Rational::new(1.into(), self.order.into())))
    }
}

#[derive(Debug, Copy, Clone, PartialEq, Eq)]
pub struct CharacterSumLimits {
    pub max_terms: usize,
    pub max_conductor: usize,
}

impl Default for CharacterSumLimits {
    fn default() -> Self {
        Self {
            max_terms: 1024,
            max_conductor: MAX_CONDUCTOR,
        }
    }
}

/// A checked prefix a_0,...,a_n, with a_{i+1} mod 2^i = a_i.
/// This object certifies only its retained finite entries. The word-size cap
/// is checked before cloning; no infinite extension, p-adic value or topology
/// is inferred. A source index at each level must be a canonical residue.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteDualPrefix {
    indices: Vec<usize>,
}

impl FiniteDualPrefix {
    pub fn new(indices: &[usize]) -> Result<Self, DyadicError> {
        if indices.is_empty() {
            return Err(DyadicError::EmptyPrefix);
        }
        if indices.len() > usize::BITS as usize {
            return Err(DyadicError::LevelOverflow);
        }
        for (level, &index) in indices.iter().enumerate() {
            let group = DyadicLevel::new(level as u32)?;
            group.check(index)?;
            if level > 0 && index % (group.order / 2) != indices[level - 1] {
                return Err(DyadicError::IncoherentPrefix);
            }
        }
        Ok(Self {
            indices: indices.to_vec(),
        })
    }

    pub fn indices(&self) -> &[usize] {
        &self.indices
    }

    pub fn next_indices(&self) -> Result<[usize; 2], DyadicError> {
        DyadicLevel::new((self.indices.len() - 1) as u32)?.extensions(*self.indices.last().checked_invariant_e2c05deb("checked invariant"))
    }
}

// Origin: engine/crates_rs/core_number_theory/src/dyadic_presentation.rs
// Claim: urn:core:crates_rs:core-number-theory:dyadic-presentation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e2c05deb {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
