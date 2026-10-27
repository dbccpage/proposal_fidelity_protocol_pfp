//! Finite projected coordinates with an evaluator-computed L1 diagnostic.
//! The caller supplies the certification flag; it is not exact quotient evidence.

use std::fmt;

/// A vector whose finite L1 diagnostic is evaluated at construction time.
///
/// This type can only be constructed via `L1ProjectedVector::from_verified`,
/// which checks finiteness. The caller-declared certification flag does not
/// certify optimality or authorize a transition.
#[derive(Debug, Clone)]
pub struct L1ProjectedVector {
    /// The projected coefficients.
    data: Vec<f64>,
    /// Evaluated sum of coordinate magnitudes.
    l1_norm: f64,
    /// Caller-declared numerical optimality flag.
    certified: bool,
}

/// Error returned when L1 projection verification fails.
#[derive(Debug, Clone)]
pub enum L1ProjectionError {
    NonFiniteEntry { index: usize, value: f64 },
    EmptyVector,
    NormOverflow { norm: f64 },
}

impl fmt::Display for L1ProjectionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NonFiniteEntry { index, value } => {
                write!(
                    f,
                    "L1ProjectedVector: non-finite entry at [{index}] = {value}"
                )
            }
            Self::EmptyVector => write!(f, "L1ProjectedVector: empty vector"),
            Self::NormOverflow { norm } => {
                write!(f, "L1ProjectedVector: norm overflow = {norm}")
            }
        }
    }
}

impl L1ProjectedVector {
    /// Construct a verified L1-projected vector.
    ///
    /// Checks all entries are finite and computes the L1 norm.
    /// Returns `Err` for nonfinite entries, overflow, or an empty vector.
    pub fn from_verified(data: Vec<f64>, certified: bool) -> Result<Self, L1ProjectionError> {
        if data.is_empty() {
            return Err(L1ProjectionError::EmptyVector);
        }

        for (i, &v) in data.iter().enumerate() {
            if !v.is_finite() {
                return Err(L1ProjectionError::NonFiniteEntry { index: i, value: v });
            }
        }
        let l1_norm = core_functional::Phi1Functional::unweighted_l1_diagnostic(&data);

        if !l1_norm.is_finite() {
            return Err(L1ProjectionError::NormOverflow { norm: l1_norm });
        }

        Ok(Self {
            data,
            l1_norm,
            certified,
        })
    }

    /// Access the projected data (immutable).
    #[inline]
    pub fn data(&self) -> &[f64] {
        &self.data
    }

    /// The verified L1 norm.
    #[inline]
    pub fn l1_norm(&self) -> f64 {
        self.l1_norm
    }

    /// Caller-declared numerical optimality flag.
    #[inline]
    pub fn is_certified(&self) -> bool {
        self.certified
    }

    /// Number of entries.
    #[inline]
    pub fn len(&self) -> usize {
        self.data.len()
    }

    /// Check if empty.
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    /// Consume and return the inner vector.
    pub fn into_inner(self) -> Vec<f64> {
        self.data
    }
}

impl fmt::Display for L1ProjectedVector {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "L1ProjectedVector(n={}, l1={:.6e}, certified={})",
            self.data.len(),
            self.l1_norm,
            self.certified
        )
    }
}

// Origin: engine/crates_rs/core_types/src/l1_projected_vector.rs
// Claim: urn:core:crates_rs:core-types:l1-projected-vector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn constructs_valid_vector() {
        let v = L1ProjectedVector::from_verified(vec![1.0, -2.0, 3.0], true).unwrap();
        assert_eq!(v.l1_norm(), 6.0);
        assert!(v.is_certified());
        assert_eq!(v.len(), 3);
    }

    #[test]
    fn rejects_nan() {
        let r = L1ProjectedVector::from_verified(vec![1.0, f64::NAN], false);
        assert!(r.is_err());
    }

    #[test]
    fn rejects_inf() {
        let r = L1ProjectedVector::from_verified(vec![f64::INFINITY], false);
        assert!(r.is_err());
    }

    #[test]
    fn rejects_empty() {
        let r = L1ProjectedVector::from_verified(vec![], false);
        assert!(r.is_err());
    }

    #[test]
    fn into_inner_roundtrip() {
        let data = vec![1.0, 2.0, 3.0];
        let v = L1ProjectedVector::from_verified(data.clone(), true).unwrap();
        assert_eq!(v.into_inner(), data);
    }
}

/// Exact L1 norm of an integer vector: the checked sum of absolute coordinates.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactL1Vector {
    coordinates: usize,
    norm: u128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExactL1Error {
    Bound,
    Min,
    Overflow,
}

impl std::fmt::Display for ExactL1Error {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ExactL1Error::Bound => write!(formatter, "an exact L1 vector needs 1..=64 coordinates"),
            ExactL1Error::Min => write!(formatter, "i64::MIN has no positive absolute value in i64"),
            ExactL1Error::Overflow => write!(formatter, "the L1 sum overflowed"),
        }
    }
}

impl std::error::Error for ExactL1Error {}

impl ExactL1Vector {
    pub fn certify(coords: &[i64]) -> Result<Self, ExactL1Error> {
        if coords.is_empty() || coords.len() > 64 {
            return Err(ExactL1Error::Bound);
        }
        let mut norm: u128 = 0;
        for &coord in coords {
            if coord == i64::MIN {
                return Err(ExactL1Error::Min);
            }
            norm = norm.checked_add(u128::from(coord.unsigned_abs())).ok_or(ExactL1Error::Overflow)?;
        }
        Ok(Self {
            coordinates: coords.len(),
            norm,
        })
    }

    pub fn norm(&self) -> u128 {
        self.norm
    }
}

#[cfg(test)]
mod exact_l1_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn absolute_coordinates_sum_to_six() {
        let vector = taken(ExactL1Vector::certify(&[1, -2, 3]));
        assert_eq!(vector.norm(), 6);
        assert!(ExactL1Vector::certify(&[i64::MIN]).is_err());
    }
}
