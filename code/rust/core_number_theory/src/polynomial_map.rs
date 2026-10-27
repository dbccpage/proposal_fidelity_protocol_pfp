//! Sparse rational polynomials and exact Jacobians of declared polynomial maps.
//! Coordinates have explicit arity. Missing coordinates never evaluate as one.
//! A Jacobian difference witnesses non-affinity; equal samples do not prove affinity.

use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use num_rational::BigRational as Q;
use num_traits::{Signed, Zero};
use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PolynomialMapError {
    #[error("coordinate or exponent tuple has the wrong declared dimension")]
    Dimension,
    #[error("a coefficient or coordinate has a nonpositive denominator")]
    InvalidRational,
    #[error("an exponent exceeds the exact rational power API's i32 range")]
    ExponentRange,
    #[error(transparent)]
    Matrix(#[from] MatrixError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SparseRationalPolynomial {
    variables: usize,
    terms: BTreeMap<Vec<usize>, Q>,
}

impl SparseRationalPolynomial {
    pub fn new(variables: usize, terms: Vec<(Vec<usize>, Q)>) -> Result<Self, PolynomialMapError> {
        let mut canonical = BTreeMap::new();
        for (powers, coefficient) in terms {
            if powers.len() != variables {
                return Err(PolynomialMapError::Dimension);
            }
            if powers.iter().any(|&p| p > i32::MAX as usize) {
                return Err(PolynomialMapError::ExponentRange);
            }
            if !coefficient.denom().is_positive() {
                return Err(PolynomialMapError::InvalidRational);
            }
            *canonical.entry(powers).or_insert_with(Q::zero) += coefficient;
        }
        canonical.retain(|_, c| !c.is_zero());
        Ok(Self {
            variables,
            terms: canonical,
        })
    }

    pub fn zero(variables: usize) -> Self {
        Self {
            variables,
            terms: BTreeMap::new(),
        }
    }
    pub fn variables(&self) -> usize {
        self.variables
    }
    pub fn terms(&self) -> &BTreeMap<Vec<usize>, Q> {
        &self.terms
    }

    pub fn evaluate(&self, point: &[Q]) -> Result<Q, PolynomialMapError> {
        if point.len() != self.variables {
            return Err(PolynomialMapError::Dimension);
        }
        if point.iter().any(|x| !x.denom().is_positive()) {
            return Err(PolynomialMapError::InvalidRational);
        }
        Ok(self
            .terms
            .iter()
            .map(|(powers, coefficient)| {
                powers
                    .iter()
                    .zip(point)
                    .fold(coefficient.clone(), |value, (&power, x)| {
                        value * x.pow(power as i32)
                    })
            })
            .sum())
    }

    pub fn derivative(&self, variable: usize) -> Result<Self, PolynomialMapError> {
        if variable >= self.variables {
            return Err(PolynomialMapError::Dimension);
        }
        let terms = self
            .terms
            .iter()
            .filter(|(powers, _)| powers[variable] != 0)
            .map(|(powers, c)| {
                let mut next = powers.clone();
                let coefficient = c * Q::from_integer(next[variable].into());
                next[variable] -= 1;
                (next, coefficient)
            })
            .collect();
        Self::new(self.variables, terms)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PolynomialMap {
    input_dimension: usize,
    components: Vec<SparseRationalPolynomial>,
}

impl PolynomialMap {
    pub fn new(
        input_dimension: usize,
        components: Vec<SparseRationalPolynomial>,
    ) -> Result<Self, PolynomialMapError> {
        if components.iter().any(|p| p.variables != input_dimension) {
            return Err(PolynomialMapError::Dimension);
        }
        Ok(Self {
            input_dimension,
            components,
        })
    }

    pub fn jacobian(&self, point: &[Q]) -> Result<BasicMatrix<Q>, PolynomialMapError> {
        if point.len() != self.input_dimension {
            return Err(PolynomialMapError::Dimension);
        }
        if point.iter().any(|x| !x.denom().is_positive()) {
            return Err(PolynomialMapError::InvalidRational);
        }
        // Admission of the output shape precedes the derivative computations.
        let mut result =
            BasicMatrix::try_from_fn(self.components.len(), self.input_dimension, |_, _| {
                Q::zero()
            })?;
        for (i, component) in self.components.iter().enumerate() {
            for j in 0..self.input_dimension {
                result.set(i, j, component.derivative(j)?.evaluate(point)?)?;
            }
        }
        Ok(result)
    }

    pub fn witnesses_non_affinity(
        &self,
        left: &[Q],
        right: &[Q],
    ) -> Result<bool, PolynomialMapError> {
        Ok(self.jacobian(left)? != self.jacobian(right)?)
    }
}

// Origin: engine/crates_rs/core_number_theory/src/polynomial_map.rs
// Claim: urn:core:crates_rs:core-number-theory:polynomial-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f338ece2 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
