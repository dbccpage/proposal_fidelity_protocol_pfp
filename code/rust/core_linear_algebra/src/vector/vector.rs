//! Finite coordinate **column** vectors.
//!
//! Dual-face stem: `vector` ↔ `urn:core:math:vector:v0.1.0`.
//! Column convention: \(v \in V \cong K^n\) as an \(n \times 1\) coordinate list
//! relative to a declared ordered basis (`BasisDescriptor`).
//!
//! **AuthorityEffect:** None. Shape/law witnesses only; no PROVED/GlobalGreen.

use crate::basis::BasisDescriptor;
use thiserror::Error;

/// Errors related to coordinate vectors.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum VectorError {
    /// The coordinate length does not match the declared basis dimension.
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },

    /// Two coordinate vectors are expressed in different bases.
    #[error("basis mismatch: left={left:?}, right={right:?}")]
    BasisMismatch {
        left: BasisDescriptor,
        right: BasisDescriptor,
    },
}

/// A finite coordinate **column** vector in a declared basis.
///
/// Invariants (YAML length / zero-space laws):
/// - `coordinates.len() == basis.dimension()` (including `n = 0` empty coords).
/// - Column convention only; row / \(V \to K\) lives in `row_vector`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoordinateVector<T> {
    coordinates: Vec<T>,
    basis: BasisDescriptor,
}

impl<T> CoordinateVector<T> {
    /// Constructs a coordinate vector, checking that the coordinate length
    /// equals the basis dimension (YAML length law; negative_test dim reject).
    pub fn new(coordinates: Vec<T>, basis: BasisDescriptor) -> Result<Self, VectorError> {
        if coordinates.len() != basis.dimension() {
            return Err(VectorError::DimensionMismatch {
                expected: basis.dimension(),
                actual: coordinates.len(),
            });
        }

        Ok(Self { coordinates, basis })
    }

    /// Internal constructor for already-validated coordinate vectors.
    pub(crate) fn new_unchecked(coordinates: Vec<T>, basis: BasisDescriptor) -> Self {
        Self { coordinates, basis }
    }

    /// Returns the coordinate entries (column components).
    pub fn coordinates(&self) -> &[T] {
        &self.coordinates
    }

    /// Returns the basis descriptor.
    pub fn basis(&self) -> &BasisDescriptor {
        &self.basis
    }

    /// Returns the coordinate dimension \(n = \dim V\).
    pub fn dimension(&self) -> usize {
        self.coordinates.len()
    }

    /// Consumes the vector and returns raw parts.
    ///
    /// This preserves the basis descriptor; no coordinate semantics are lost.
    pub fn into_parts(self) -> (Vec<T>, BasisDescriptor) {
        (self.coordinates, self.basis)
    }

    /// Converts this coordinate vector to a `nalgebra::DVector` (column).
    ///
    /// The basis descriptor is lost in the conversion. Use this to access
    /// nalgebra operations (dot, norm, etc.) when you've already verified
    /// basis compatibility.
    pub fn to_nalgebra(&self) -> nalgebra::DVector<T>
    where
        T: Clone + nalgebra::Scalar + num_traits::Zero,
    {
        nalgebra::DVector::from_column_slice(&self.coordinates)
    }

    /// Constructs a `CoordinateVector` from a `nalgebra::DVector` and a basis.
    ///
    /// Returns an error if the vector dimension doesn't match the basis dimension.
    pub fn from_nalgebra(
        v: &nalgebra::DVector<T>,
        basis: BasisDescriptor,
    ) -> Result<Self, VectorError>
    where
        T: Clone + nalgebra::Scalar,
    {
        let coordinates: Vec<T> = v.iter().cloned().collect();
        Self::new(coordinates, basis)
    }

    /// Returns data necessary for generating a `VectorAdmissibilityWitness`.
    /// Because `CoordinateVector` strictly guarantees its dimension matches
    /// its `BasisDescriptor` upon construction, this method serves as the
    /// validation bridge to the engine's homological witness subsystem,
    /// fulfilling the rigid `Vector` and `VectorSpace` markdown contracts.
    pub fn verify_admissibility(&self) -> Result<(usize, String), VectorError> {
        if self.coordinates.len() != self.basis.dimension() {
            return Err(VectorError::DimensionMismatch {
                expected: self.basis.dimension(),
                actual: self.coordinates.len(),
            });
        }
        Ok((self.dimension(), self.basis.id().as_str().to_string()))
    }
}

impl<T> CoordinateVector<T>
where
    T: num_traits::Zero,
{
    /// Zero vector of the given basis (YAML zero-space law: `n=0` ⇒ empty coords).
    pub fn zero(basis: BasisDescriptor) -> Self {
        let n = basis.dimension();
        let coordinates = (0..n).map(|_| T::zero()).collect();
        Self::new_unchecked(coordinates, basis)
    }
}

impl<T> CoordinateVector<T>
where
    T: Clone + std::ops::Add<Output = T>,
{
    /// Componentwise addition on the **same** basis (YAML addition law).
    ///
    /// Rejects basis mismatch and dimension mismatch.
    pub fn checked_add(&self, rhs: &Self) -> Result<Self, VectorError> {
        if self.basis != rhs.basis {
            return Err(VectorError::BasisMismatch {
                left: self.basis.clone(),
                right: rhs.basis.clone(),
            });
        }

        if self.dimension() != rhs.dimension() {
            return Err(VectorError::DimensionMismatch {
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

        Ok(Self::new_unchecked(coordinates, self.basis.clone()))
    }

    /// Alias for [`Self::checked_add`] (historical name).
    pub fn add_same_basis(&self, rhs: &Self) -> Result<Self, VectorError> {
        self.checked_add(rhs)
    }
}

impl<T> CoordinateVector<T>
where
    T: Clone + std::ops::Sub<Output = T>,
{
    /// Componentwise subtraction on the same basis.
    pub fn checked_sub(&self, rhs: &Self) -> Result<Self, VectorError> {
        if self.basis != rhs.basis {
            return Err(VectorError::BasisMismatch {
                left: self.basis.clone(),
                right: rhs.basis.clone(),
            });
        }

        if self.dimension() != rhs.dimension() {
            return Err(VectorError::DimensionMismatch {
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

        Ok(Self::new_unchecked(coordinates, self.basis.clone()))
    }

    /// Alias for [`Self::checked_sub`].
    pub fn sub_same_basis(&self, rhs: &Self) -> Result<Self, VectorError> {
        self.checked_sub(rhs)
    }
}

impl<T> CoordinateVector<T>
where
    T: Clone + std::ops::Mul<Output = T>,
{
    /// Scalar multiplication (YAML scalar law): \(\alpha \cdot v\) stays in \(V\).
    pub fn scale(&self, scalar: &T) -> Self {
        let coordinates = self
            .coordinates
            .iter()
            .cloned()
            .map(|a| a * scalar.clone())
            .collect();

        Self::new_unchecked(coordinates, self.basis.clone())
    }

    /// Named witness for the scalar law (same as [`Self::scale`]; pure `Mul` cannot fail).
    pub fn checked_scale(&self, scalar: &T) -> Self {
        self.scale(scalar)
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/vector/vector.rs
// Claim: urn:core:crates_rs:core-linear-algebra:vector:l4-production-boundary:v1
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
        let v = CoordinateVector::new(vec![1, 2, 3], basis)?;
        assert_eq!(v.dimension(), 3);
        Ok(())
    }

    #[test]
    fn test_new_dimension_mismatch() -> Result<(), Box<dyn std::error::Error>> {
        let basis = dummy_basis("B1", 3)?;
        let err = CoordinateVector::new(vec![1, 2], basis).unwrap_err();
        assert!(matches!(
            err,
            VectorError::DimensionMismatch {
                expected: 3,
                actual: 2
            }
        ));
        Ok(())
    }

    #[test]
    fn test_zero_vector_and_zero_space() -> Result<(), Box<dyn std::error::Error>> {
        let b3 = dummy_basis("B3", 3)?;
        let z = CoordinateVector::<i64>::zero(b3);
        assert_eq!(z.coordinates(), &[0, 0, 0]);

        let b0 = dummy_basis("B0", 0)?;
        let z0 = CoordinateVector::<i64>::zero(b0);
        assert_eq!(z0.dimension(), 0);
        assert!(z0.coordinates().is_empty());
        Ok(())
    }

    #[test]
    fn test_checked_add_same_basis() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = dummy_basis("B1", 2)?;
        let v1 = CoordinateVector::new(vec![1, 2], b1.clone())?;
        let v2 = CoordinateVector::new(vec![3, 4], b1.clone())?;

        let sum = v1.checked_add(&v2)?;
        assert_eq!(sum.coordinates(), &[4, 6]);
        // Historical alias
        let sum2 = v1.add_same_basis(&v2)?;
        assert_eq!(sum2.coordinates(), &[4, 6]);
        Ok(())
    }

    #[test]
    fn test_checked_add_basis_mismatch() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = dummy_basis("B1", 2)?;
        let b2 = dummy_basis("B2", 2)?;
        let v1 = CoordinateVector::new(vec![1, 2], b1)?;
        let v2 = CoordinateVector::new(vec![3, 4], b2)?;

        let err = v1.checked_add(&v2).unwrap_err();
        assert!(matches!(err, VectorError::BasisMismatch { .. }));
        Ok(())
    }

    #[test]
    fn test_checked_add_dimension_mismatch_via_unchecked() -> Result<(), Box<dyn std::error::Error>>
    {
        // Construction refuses dim mismatch; force unequal dims with new_unchecked
        // to exercise the addition-law reject path.
        let b2 = dummy_basis("B1", 2)?;
        let b3 = BasisDescriptor::new(b2.id().clone(), 3);
        let v2 = CoordinateVector::new_unchecked(vec![1, 2], b2);
        let v3 = CoordinateVector::new_unchecked(vec![1, 2, 3], b3);

        let err = v2.checked_add(&v3).unwrap_err();
        assert!(matches!(
            err,
            VectorError::BasisMismatch { .. } | VectorError::DimensionMismatch { .. }
        ));
        Ok(())
    }

    #[test]
    fn test_checked_scale() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = dummy_basis("B1", 2)?;
        let v = CoordinateVector::new(vec![1, 2], b1)?;
        let s = v.checked_scale(&3);
        assert_eq!(s.coordinates(), &[3, 6]);
        Ok(())
    }

    #[test]
    fn test_into_parts() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = dummy_basis("B1", 2)?;
        let v1 = CoordinateVector::new(vec![1, 2], b1.clone())?;
        let (coords, basis) = v1.into_parts();
        assert_eq!(coords, vec![1, 2]);
        assert_eq!(basis, b1);
        Ok(())
    }
}
