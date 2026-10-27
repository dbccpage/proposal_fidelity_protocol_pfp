//! Finite coordinate **row** vectors (covector dual face).
//!
//! Dual-face stem: `row_vector` ↔ `urn:core:math:row_vector:v0.1.0`.
//! Row convention: \(\omega : V \to K\) as a \(1 \times n\) coordinate list
//! relative to a declared ordered basis of domain \(V\).
//!
//! This is the coordinate dual of [`crate::vector::vector::CoordinateVector`].
//! The older artifact/hash-oriented `covector.contract.yaml` remains a
//! related Matrix-envelope face; **this module is the 1:1 RS stem** for
//! coordinate row objects (see agent-4 receipt).
//!
//! **AuthorityEffect:** None. Shape/law witnesses only; no PROVED/GlobalGreen.

use crate::basis::BasisDescriptor;
use crate::vector::vector::{CoordinateVector, VectorError};
use thiserror::Error;

/// Errors related to coordinate row vectors / covectors.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum RowVectorError {
    /// The coordinate length does not match the declared domain basis dimension.
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },

    /// Two row vectors are expressed in different domain bases.
    #[error("basis mismatch: left={left:?}, right={right:?}")]
    BasisMismatch {
        left: BasisDescriptor,
        right: BasisDescriptor,
    },

    /// Evaluation pairing refused (row domain basis ≠ column basis, or dims differ).
    #[error("pairing mismatch: row={row:?}, column={column:?}")]
    PairingMismatch {
        row: BasisDescriptor,
        column: BasisDescriptor,
    },
}

impl From<VectorError> for RowVectorError {
    fn from(e: VectorError) -> Self {
        match e {
            VectorError::DimensionMismatch { expected, actual } => {
                Self::DimensionMismatch { expected, actual }
            }
            VectorError::BasisMismatch { left, right } => Self::BasisMismatch { left, right },
        }
    }
}

/// A finite coordinate **row** vector: coordinates of a linear functional
/// \(\omega : V \to K\) in the dual of a declared ordered basis of \(V\).
///
/// Invariants:
/// - `coordinates.len() == domain_basis.dimension()` (including `n = 0`).
/// - Row convention (\(1 \times n\)); column objects live in `vector`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoordinateRowVector<T> {
    coordinates: Vec<T>,
    domain_basis: BasisDescriptor,
}

impl<T> CoordinateRowVector<T> {
    /// Constructs a row vector, checking `len(components) = dim(V)`.
    pub fn new(coordinates: Vec<T>, domain_basis: BasisDescriptor) -> Result<Self, RowVectorError> {
        if coordinates.len() != domain_basis.dimension() {
            return Err(RowVectorError::DimensionMismatch {
                expected: domain_basis.dimension(),
                actual: coordinates.len(),
            });
        }

        Ok(Self {
            coordinates,
            domain_basis,
        })
    }

    /// Internal constructor for already-validated row vectors.
    pub(crate) fn new_unchecked(coordinates: Vec<T>, domain_basis: BasisDescriptor) -> Self {
        Self {
            coordinates,
            domain_basis,
        }
    }

    /// Returns the row coordinate entries (\(1 \times n\) layout as a flat list).
    pub fn coordinates(&self) -> &[T] {
        &self.coordinates
    }

    /// Domain basis of \(V\) (the space the functional acts on).
    pub fn domain_basis(&self) -> &BasisDescriptor {
        &self.domain_basis
    }

    /// Alias for [`Self::domain_basis`] (row dual of column `basis()`).
    pub fn basis(&self) -> &BasisDescriptor {
        &self.domain_basis
    }

    /// Dimension \(n = \dim V\) (number of columns of the row).
    pub fn dimension(&self) -> usize {
        self.coordinates.len()
    }

    /// Consumes the row vector and returns raw parts.
    pub fn into_parts(self) -> (Vec<T>, BasisDescriptor) {
        (self.coordinates, self.domain_basis)
    }

    /// Converts to a `nalgebra` **row** vector (`DVector` is column-oriented;
    /// we use `RowDVector` when available via transpose of a column view).
    pub fn to_nalgebra_row(&self) -> nalgebra::RowDVector<T>
    where
        T: Clone + nalgebra::Scalar + num_traits::Zero,
    {
        nalgebra::RowDVector::from_row_slice(&self.coordinates)
    }

    /// Constructs from a nalgebra row vector and domain basis.
    pub fn from_nalgebra_row(
        v: &nalgebra::RowDVector<T>,
        domain_basis: BasisDescriptor,
    ) -> Result<Self, RowVectorError>
    where
        T: Clone + nalgebra::Scalar,
    {
        let coordinates: Vec<T> = v.iter().cloned().collect();
        Self::new(coordinates, domain_basis)
    }

    /// Shape admissibility witness: dim matches domain basis id label.
    pub fn verify_admissibility(&self) -> Result<(usize, String), RowVectorError> {
        if self.coordinates.len() != self.domain_basis.dimension() {
            return Err(RowVectorError::DimensionMismatch {
                expected: self.domain_basis.dimension(),
                actual: self.coordinates.len(),
            });
        }
        Ok((
            self.dimension(),
            self.domain_basis.id().as_str().to_string(),
        ))
    }
}

impl<T> CoordinateRowVector<T>
where
    T: num_traits::Zero,
{
    /// Zero covector on the given domain basis (including `n = 0`).
    pub fn zero(domain_basis: BasisDescriptor) -> Self {
        let n = domain_basis.dimension();
        let coordinates = (0..n).map(|_| T::zero()).collect();
        Self::new_unchecked(coordinates, domain_basis)
    }
}

impl<T> CoordinateRowVector<T>
where
    T: Clone + std::ops::Add<Output = T>,
{
    /// Componentwise addition on the same domain basis (YAML addition law).
    pub fn checked_add(&self, rhs: &Self) -> Result<Self, RowVectorError> {
        if self.domain_basis != rhs.domain_basis {
            return Err(RowVectorError::BasisMismatch {
                left: self.domain_basis.clone(),
                right: rhs.domain_basis.clone(),
            });
        }

        if self.dimension() != rhs.dimension() {
            return Err(RowVectorError::DimensionMismatch {
                expected: self.dimension(),
                actual: rhs.dimension(),
            });
        }

        let coordinates = self
            .coordinates
            .iter()
            .cloned()
            .zip(rhs.coordinates.iter().cloned())
            .map(|(a, b)| a + b)
            .collect();

        Ok(Self::new_unchecked(coordinates, self.domain_basis.clone()))
    }
}

impl<T> CoordinateRowVector<T>
where
    T: Clone + std::ops::Sub<Output = T>,
{
    /// Componentwise subtraction on the same domain basis.
    pub fn checked_sub(&self, rhs: &Self) -> Result<Self, RowVectorError> {
        if self.domain_basis != rhs.domain_basis {
            return Err(RowVectorError::BasisMismatch {
                left: self.domain_basis.clone(),
                right: rhs.domain_basis.clone(),
            });
        }

        if self.dimension() != rhs.dimension() {
            return Err(RowVectorError::DimensionMismatch {
                expected: self.dimension(),
                actual: rhs.dimension(),
            });
        }

        let coordinates = self
            .coordinates
            .iter()
            .cloned()
            .zip(rhs.coordinates.iter().cloned())
            .map(|(a, b)| a - b)
            .collect();

        Ok(Self::new_unchecked(coordinates, self.domain_basis.clone()))
    }
}

impl<T> CoordinateRowVector<T>
where
    T: Clone + std::ops::Mul<Output = T>,
{
    /// Scalar multiplication of the functional: \((\alpha \omega)(v) = \alpha \cdot \omega(v)\).
    pub fn scale(&self, scalar: &T) -> Self {
        let coordinates = self
            .coordinates
            .iter()
            .cloned()
            .map(|a| a * scalar.clone())
            .collect();

        Self::new_unchecked(coordinates, self.domain_basis.clone())
    }

    /// Named witness for the scalar law (pure `Mul` cannot fail).
    pub fn checked_scale(&self, scalar: &T) -> Self {
        self.scale(scalar)
    }
}

impl<T> CoordinateRowVector<T>
where
    T: Clone + num_traits::Zero + std::ops::Add<Output = T> + std::ops::Mul<Output = T>,
{
    /// Evaluation pairing \(\omega(v) = \sum_i \omega_i v_i\).
    ///
    /// Requires matching domain basis identity and dimension; otherwise rejects.
    pub fn evaluate(&self, v: &CoordinateVector<T>) -> Result<T, RowVectorError> {
        if self.domain_basis != *v.basis() {
            return Err(RowVectorError::PairingMismatch {
                row: self.domain_basis.clone(),
                column: v.basis().clone(),
            });
        }

        if self.dimension() != v.dimension() {
            return Err(RowVectorError::DimensionMismatch {
                expected: self.dimension(),
                actual: v.dimension(),
            });
        }

        let mut acc = T::zero();
        for (a, b) in self
            .coordinates
            .iter()
            .cloned()
            .zip(v.coordinates().iter().cloned())
        {
            acc = acc + (a * b);
        }
        Ok(acc)
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/vector/row_vector.rs
// Claim: urn:core:crates_rs:core-linear-algebra:row-vector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::basis::{BasisError, BasisId};

    fn dummy_basis(id: &str, dim: usize) -> Result<BasisDescriptor, BasisError> {
        Ok(BasisDescriptor::new(BasisId::new(id.to_string())?, dim))
    }

    #[test]
    fn test_new_valid() -> Result<(), Box<dyn std::error::Error>> {
        let basis = dummy_basis("B1", 3)?;
        let w = CoordinateRowVector::new(vec![1, 2, 3], basis)?;
        assert_eq!(w.dimension(), 3);
        Ok(())
    }

    #[test]
    fn test_new_dimension_mismatch_reject() -> Result<(), Box<dyn std::error::Error>> {
        let basis = dummy_basis("B1", 3)?;
        let err = CoordinateRowVector::new(vec![1, 2], basis).unwrap_err();
        assert!(matches!(
            err,
            RowVectorError::DimensionMismatch {
                expected: 3,
                actual: 2
            }
        ));
        Ok(())
    }

    #[test]
    fn test_zero_row_including_zero_space() -> Result<(), Box<dyn std::error::Error>> {
        let b0 = dummy_basis("Z", 0)?;
        let w = CoordinateRowVector::<i64>::zero(b0);
        assert_eq!(w.dimension(), 0);
        assert!(w.coordinates().is_empty());
        Ok(())
    }

    #[test]
    fn test_checked_add_and_scale() -> Result<(), Box<dyn std::error::Error>> {
        let b = dummy_basis("B1", 2)?;
        let w1 = CoordinateRowVector::new(vec![1, 2], b.clone())?;
        let w2 = CoordinateRowVector::new(vec![3, 4], b)?;
        let sum = w1.checked_add(&w2)?;
        assert_eq!(sum.coordinates(), &[4, 6]);
        assert_eq!(w1.checked_scale(&2).coordinates(), &[2, 4]);
        Ok(())
    }

    #[test]
    fn test_checked_add_basis_mismatch_reject() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = dummy_basis("B1", 2)?;
        let b2 = dummy_basis("B2", 2)?;
        let w1 = CoordinateRowVector::new(vec![1, 2], b1)?;
        let w2 = CoordinateRowVector::new(vec![3, 4], b2)?;
        let err = w1.checked_add(&w2).unwrap_err();
        assert!(matches!(err, RowVectorError::BasisMismatch { .. }));
        Ok(())
    }

    #[test]
    fn test_evaluate_pairing() -> Result<(), Box<dyn std::error::Error>> {
        let b = dummy_basis("B1", 2)?;
        let w = CoordinateRowVector::new(vec![1, 2], b.clone())?;
        let v = CoordinateVector::new(vec![3, 4], b)?;
        // 1*3 + 2*4 = 11
        assert_eq!(w.evaluate(&v)?, 11);
        Ok(())
    }

    #[test]
    fn test_evaluate_dim_mismatch_reject() -> Result<(), Box<dyn std::error::Error>> {
        let b2 = dummy_basis("B1", 2)?;
        let b3 = dummy_basis("B1", 3)?;
        // Same label different dim ⇒ different BasisDescriptor equality
        let w = CoordinateRowVector::new(vec![1, 2], b2)?;
        let v = CoordinateVector::new(vec![1, 2, 3], b3)?;
        let err = w.evaluate(&v).unwrap_err();
        assert!(matches!(
            err,
            RowVectorError::PairingMismatch { .. } | RowVectorError::DimensionMismatch { .. }
        ));
        Ok(())
    }

    #[test]
    fn test_evaluate_basis_mismatch_reject() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = dummy_basis("B1", 2)?;
        let b2 = dummy_basis("B2", 2)?;
        let w = CoordinateRowVector::new(vec![1, 0], b1)?;
        let v = CoordinateVector::new(vec![5, 6], b2)?;
        let err = w.evaluate(&v).unwrap_err();
        assert!(matches!(err, RowVectorError::PairingMismatch { .. }));
        Ok(())
    }
}
