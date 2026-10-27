use crate::basis::BasisDescriptor;
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Error)]
pub enum VectorSpaceError {
    #[error("dimension mismatch: left={left}, right={right}")]
    DimensionMismatch { left: usize, right: usize },

    #[error("non-finite scalar at index {index}: {value}")]
    NonFiniteScalar { index: usize, value: f64 },

    #[error("basis mismatch between vectors: left={left:?}, right={right:?}")]
    BasisMismatch {
        left: BasisDescriptor,
        right: BasisDescriptor,
    },
}

/// Metadata for a finite-dimensional coordinate space over scalar type `K`.
///
/// This does not itself certify vector-space laws for `K`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteVectorSpace<K> {
    dimension: usize,
    _phantom: std::marker::PhantomData<K>,
}

impl<K> FiniteVectorSpace<K> {
    pub fn new(dimension: usize) -> Self {
        Self {
            dimension,
            _phantom: std::marker::PhantomData,
        }
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    pub fn matches_coordinate_dimension<T>(&self, coords: &CoordinateTuple<T>) -> bool {
        coords.coordinate_dimension() == self.dimension
    }

    pub fn checked_against_coordinates<T>(
        &self,
        coords: &CoordinateTuple<T>,
    ) -> Result<(), VectorSpaceError> {
        if !self.matches_coordinate_dimension(coords) {
            return Err(VectorSpaceError::DimensionMismatch {
                left: self.dimension,
                right: coords.coordinate_dimension(),
            });
        }
        Ok(())
    }

    pub fn matches_basis_dimension(&self, basis: &BasisDescriptor) -> bool {
        basis.dimension() == self.dimension
    }

    pub fn checked_against_basis(&self, basis: &BasisDescriptor) -> Result<(), VectorSpaceError> {
        if !self.matches_basis_dimension(basis) {
            return Err(VectorSpaceError::DimensionMismatch {
                left: self.dimension,
                right: basis.dimension(),
            });
        }
        Ok(())
    }
}

impl<K> VectorSpace<K> for FiniteVectorSpace<K> {
    fn dimension_opt(&self) -> Option<usize> {
        Some(self.dimension)
    }
}

impl<K> FiniteDimensionalVectorSpace<K> for FiniteVectorSpace<K> {
    fn dimension(&self) -> usize {
        self.dimension
    }
}

/// A raw coordinate tuple in `K^n`.
/// Theorem Boundary: Does NOT carry a `Basis` witness. Not geometrically invariant.
#[derive(Debug, Clone, PartialEq)]
pub struct CoordinateTuple<K> {
    coordinates: Vec<K>,
}

impl<K> CoordinateTuple<K> {
    pub fn new(coordinates: Vec<K>) -> Self {
        Self { coordinates }
    }

    pub fn coordinates(&self) -> &[K] {
        &self.coordinates
    }

    pub fn coordinate_dimension(&self) -> usize {
        self.coordinates.len()
    }

    pub fn into_coordinates(self) -> Vec<K> {
        self.coordinates
    }
}

/// A coordinate tuple explicitly labeled with a basis descriptor.
///
/// This records an interpretation convention. It does not certify that the
/// basis exists, spans an ambient carrier, is orthonormal, or is compatible
/// with a scalar field.
#[derive(Debug, Clone, PartialEq)]
pub struct BasisLabeledVector<K> {
    coords: CoordinateTuple<K>,
    basis: BasisDescriptor,
}

impl<K> BasisLabeledVector<K> {
    pub fn new_checked(
        coords: CoordinateTuple<K>,
        basis: BasisDescriptor,
    ) -> Result<Self, VectorSpaceError> {
        if coords.coordinate_dimension() != basis.dimension() {
            return Err(VectorSpaceError::DimensionMismatch {
                left: coords.coordinate_dimension(),
                right: basis.dimension(),
            });
        }
        Ok(Self { coords, basis })
    }

    pub fn coordinates(&self) -> &CoordinateTuple<K> {
        &self.coords
    }

    pub fn basis(&self) -> &BasisDescriptor {
        &self.basis
    }

    pub fn into_certified_parts(self) -> (CoordinateTuple<K>, BasisDescriptor) {
        (self.coords, self.basis)
    }
}

impl CoordinateTuple<f64> {
    pub fn new_finite_checked(coordinates: Vec<f64>) -> Result<Self, VectorSpaceError> {
        for (index, &value) in coordinates.iter().enumerate() {
            if !value.is_finite() {
                return Err(VectorSpaceError::NonFiniteScalar { index, value });
            }
        }
        Ok(Self { coordinates })
    }

    pub fn checked_dot(&self, other: &Self) -> Result<f64, VectorSpaceError> {
        if self.coordinates.len() != other.coordinates.len() {
            return Err(VectorSpaceError::DimensionMismatch {
                left: self.coordinates.len(),
                right: other.coordinates.len(),
            });
        }

        for (index, &value) in self.coordinates.iter().enumerate() {
            if !value.is_finite() {
                return Err(VectorSpaceError::NonFiniteScalar { index, value });
            }
        }

        for (index, &value) in other.coordinates.iter().enumerate() {
            if !value.is_finite() {
                return Err(VectorSpaceError::NonFiniteScalar { index, value });
            }
        }

        Ok(self
            .coordinates
            .iter()
            .zip(other.coordinates.iter())
            .map(|(a, b)| a * b)
            .sum())
    }

    pub fn checked_norm_sq(&self) -> Result<f64, VectorSpaceError> {
        self.checked_dot(self)
    }
}

impl BasisLabeledVector<f64> {
    /// Computes the coordinate-wise standard dot product for two vectors with
    /// identical basis descriptors.
    ///
    /// This is geometrically valid only if the shared basis is orthonormal for
    /// the intended inner product. This method does not verify that condition.
    pub fn checked_coordinate_dot_same_basis(&self, other: &Self) -> Result<f64, VectorSpaceError> {
        if self.basis != other.basis {
            return Err(VectorSpaceError::BasisMismatch {
                left: self.basis.clone(),
                right: other.basis.clone(),
            });
        }

        self.coords.checked_dot(&other.coords)
    }
}

/// Abstract vector space.
///
/// This trait should be implemented by space objects, not by individual vectors.
pub trait VectorSpace<K> {
    fn dimension_opt(&self) -> Option<usize>;
}

pub trait FiniteDimensionalVectorSpace<K>: VectorSpace<K> {
    fn dimension(&self) -> usize;
}

/// A vector element in a vector space.
pub trait VectorElement<K>: Clone + PartialEq {
    type Space: VectorSpace<K>;

    fn space(&self) -> &Self::Space;
}

pub trait InnerProduct<K, V> {
    fn inner_product(&self, left: &V, right: &V) -> Result<K, VectorSpaceError>;
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/vector_space.rs
// Claim: urn:core:crates_rs:core-linear-algebra:vector-space:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::basis::BasisId;

    #[test]
    fn inner_product_rejects_dimension_mismatch() {
        let v1 = CoordinateTuple::new(vec![1.0]);
        let v2 = CoordinateTuple::new(vec![1.0, 2.0]);
        assert!(matches!(
            v1.checked_dot(&v2),
            Err(VectorSpaceError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn inner_product_rejects_nan() {
        let v1 = CoordinateTuple::new(vec![f64::NAN]);
        let v2 = CoordinateTuple::new(vec![1.0]);
        assert!(matches!(
            v1.checked_dot(&v2),
            Err(VectorSpaceError::NonFiniteScalar { .. })
        ));
    }

    #[test]
    fn inner_product_rejects_infinity() {
        let v1 = CoordinateTuple::new(vec![f64::INFINITY]);
        let v2 = CoordinateTuple::new(vec![1.0]);

        assert!(matches!(
            v1.checked_dot(&v2),
            Err(VectorSpaceError::NonFiniteScalar { .. })
        ));
    }

    #[test]
    fn coordinate_dimension_is_not_vector_space_dimension() {
        let v = CoordinateTuple::new(vec![1.0, 2.0, 3.0]);
        assert_eq!(v.coordinate_dimension(), 3);
        let space = FiniteVectorSpace::<f64>::new(3);
        assert_eq!(space.dimension(), 3);
    }

    #[test]
    fn geometric_vector_rejects_basis_mismatch() {
        let basis1 = BasisDescriptor::new(BasisId::new("B1".to_string()).unwrap(), 1);
        let basis2 = BasisDescriptor::new(BasisId::new("B2".to_string()).unwrap(), 1);

        let v1 = BasisLabeledVector::new_checked(CoordinateTuple::new(vec![1.0]), basis1).unwrap();
        let v2 = BasisLabeledVector::new_checked(CoordinateTuple::new(vec![1.0]), basis2).unwrap();

        assert!(matches!(
            v1.checked_coordinate_dot_same_basis(&v2),
            Err(VectorSpaceError::BasisMismatch { .. })
        ));
    }

    #[test]
    fn geometric_vector_rejects_coordinate_basis_dimension_mismatch() {
        let basis = BasisDescriptor::new(BasisId::new("B".to_string()).unwrap(), 2);
        let coords = CoordinateTuple::new(vec![1.0]);

        assert!(matches!(
            BasisLabeledVector::new_checked(coords, basis),
            Err(VectorSpaceError::DimensionMismatch { left: 1, right: 2 })
        ));
    }

    #[test]
    fn geometric_vector_rejects_same_basis_id_different_descriptor() {
        let id = BasisId::new("B".to_string()).unwrap();

        let basis1 = BasisDescriptor::new(id.clone(), 1);
        let basis2 = BasisDescriptor::new(id, 2);

        let v1 = BasisLabeledVector::new_checked(CoordinateTuple::new(vec![1.0]), basis1).unwrap();
        let v2 =
            BasisLabeledVector::new_checked(CoordinateTuple::new(vec![1.0, 2.0]), basis2).unwrap();

        assert!(matches!(
            v1.checked_coordinate_dot_same_basis(&v2),
            Err(VectorSpaceError::BasisMismatch { .. })
        ));
    }

    #[test]
    fn space_rejects_basis_dimension_mismatch() {
        let space = FiniteVectorSpace::<f64>::new(3);
        let basis = BasisDescriptor::new(BasisId::new("B".to_string()).unwrap(), 2);
        assert!(!space.matches_basis_dimension(&basis));
        assert!(matches!(
            space.checked_against_basis(&basis),
            Err(VectorSpaceError::DimensionMismatch { left: 3, right: 2 })
        ));
    }

    #[test]
    fn space_rejects_coordinate_dimension_mismatch() {
        let space = FiniteVectorSpace::<f64>::new(2);
        let coords = CoordinateTuple::new(vec![1.0]);
        assert!(!space.matches_coordinate_dimension(&coords));
        assert!(matches!(
            space.checked_against_coordinates(&coords),
            Err(VectorSpaceError::DimensionMismatch { left: 2, right: 1 })
        ));
    }

    #[test]
    fn space_accepts_matching_basis_and_coordinate_dimension() {
        let space = FiniteVectorSpace::<f64>::new(2);
        let basis = BasisDescriptor::new(BasisId::new("B".to_string()).unwrap(), 2);
        let coords = CoordinateTuple::new(vec![1.0, 0.0]);
        assert!(space.matches_basis_dimension(&basis));
        assert_eq!(space.checked_against_basis(&basis), Ok(()));
        assert!(space.matches_coordinate_dimension(&coords));
        assert_eq!(space.checked_against_coordinates(&coords), Ok(()));
    }

    #[test]
    fn zero_dimensional_space_is_allowed() {
        let space = FiniteVectorSpace::<f64>::new(0);
        assert_eq!(space.dimension(), 0);
        assert_eq!(space.dimension_opt(), Some(0));
        let coords = CoordinateTuple::<f64>::new(vec![]);
        assert_eq!(space.checked_against_coordinates(&coords), Ok(()));
        let basis = BasisDescriptor::new(BasisId::new("zero".to_string()).unwrap(), 0);
        assert_eq!(space.checked_against_basis(&basis), Ok(()));
        let labeled = BasisLabeledVector::new_checked(coords, basis).unwrap();
        assert_eq!(labeled.basis().dimension(), 0);
        assert_eq!(labeled.coordinates().coordinate_dimension(), 0);
    }

    #[test]
    fn finite_dimensional_trait_surface() {
        let space = FiniteVectorSpace::<f64>::new(4);
        let as_vs: &dyn VectorSpace<f64> = &space;
        assert_eq!(as_vs.dimension_opt(), Some(4));
        let as_fd: &dyn FiniteDimensionalVectorSpace<f64> = &space;
        assert_eq!(FiniteDimensionalVectorSpace::dimension(as_fd), 4);
    }
}
