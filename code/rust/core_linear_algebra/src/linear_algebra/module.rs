use crate::scalars::Ring;
use thiserror::Error;

/// Errors for concrete finite module operations.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ModuleError {
    #[error("dimension mismatch: left={left}, right={right}")]
    DimensionMismatch { left: usize, right: usize },
}

/// Abstract module over a ring.
///
/// This trait represents algebraic structure. Implementors are trusted to
/// satisfy the module laws:
///
/// - additive associativity;
/// - additive identity;
/// - additive inverses;
/// - scalar distributivity;
/// - ring-action associativity;
/// - scalar identity.
pub trait Module<R: Ring>: Clone + PartialEq {
    fn zero_module_like(&self) -> Self;
    fn add_mod(&self, rhs: &Self) -> Self;
    fn neg_mod(&self) -> Self;
    fn scale(&self, r: &R) -> Self;

    fn sub_mod(&self, rhs: &Self) -> Self {
        self.add_mod(&rhs.neg_mod())
    }

    fn is_zero_mod(&self) -> bool {
        *self == self.zero_module_like()
    }
}

/// Degree-bearing object.
pub trait Graded {
    type Degree: Copy + Ord + std::fmt::Debug;

    fn degree(&self) -> Self::Degree;
}

/// Anything that is both a module and graded.
pub trait GradedModule<R: Ring>: Module<R> + Graded {}

impl<R, T> GradedModule<R> for T
where
    R: Ring,
    T: Module<R> + Graded,
{
}

/// Coordinate vector implicitly in the standard basis of `R^n`.
///
/// WARNING: L5 certification requires explicit `BasisDescriptor` matching.
/// This struct assumes both operands occupy the exact same vector space.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FreeModuleVector<R> {
    coordinates: Vec<R>,
}

impl<R> FreeModuleVector<R> {
    pub fn new(coordinates: Vec<R>) -> Self {
        Self { coordinates }
    }

    pub fn dimension(&self) -> usize {
        self.coordinates.len()
    }

    pub fn coordinates(&self) -> &[R] {
        &self.coordinates
    }

    pub fn into_coordinates(self) -> Vec<R> {
        self.coordinates
    }
}

impl<R> FreeModuleVector<R>
where
    R: Ring,
{
    pub fn zero_of_dimension(dimension: usize) -> Self {
        Self {
            coordinates: std::iter::repeat_with(R::zero).take(dimension).collect(),
        }
    }

    pub fn checked_add(&self, rhs: &Self) -> Result<Self, ModuleError> {
        if self.dimension() != rhs.dimension() {
            return Err(ModuleError::DimensionMismatch {
                left: self.dimension(),
                right: rhs.dimension(),
            });
        }

        Ok(Self {
            coordinates: self
                .coordinates
                .iter()
                .zip(rhs.coordinates.iter())
                .map(|(a, b)| a.add(b))
                .collect(),
        })
    }

    pub fn neg(&self) -> Self {
        Self {
            coordinates: self.coordinates.iter().map(|x| x.neg()).collect(),
        }
    }

    pub fn checked_sub(&self, rhs: &Self) -> Result<Self, ModuleError> {
        self.checked_add(&rhs.neg())
    }

    pub fn scale(&self, r: &R) -> Self {
        Self {
            coordinates: self.coordinates.iter().map(|x| x.mul(r)).collect(),
        }
    }

    pub fn is_zero(&self) -> bool {
        self.coordinates.iter().all(|x| x.is_zero())
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/module.rs
// Claim: urn:core:crates_rs:core-linear-algebra:module:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    // We use i64 as a valid ring for these tests instead of MockRing to avoid missing imports.

    #[test]
    fn finite_vector_add_rejects_dimension_mismatch() {
        let a = FreeModuleVector::<i64>::new(vec![1, 2]);
        let b = FreeModuleVector::<i64>::new(vec![3, 4, 5]);

        assert!(matches!(
            a.checked_add(&b),
            Err(ModuleError::DimensionMismatch { left: 2, right: 3 })
        ));
    }

    #[test]
    fn finite_vector_zero_has_declared_dimension() {
        let z = FreeModuleVector::<i64>::zero_of_dimension(3);
        assert_eq!(z.coordinates(), &[0, 0, 0]);
        assert!(z.is_zero());
    }

    #[test]
    fn finite_vector_add_works_for_same_dimension() {
        let a = FreeModuleVector::<i64>::new(vec![1, 2]);
        let b = FreeModuleVector::<i64>::new(vec![3, 4]);

        let c = a.checked_add(&b).unwrap();
        assert_eq!(c.coordinates(), &[4, 6]);
    }

    #[test]
    fn finite_vector_scale() {
        let a = FreeModuleVector::<i64>::new(vec![2, 3]);
        let scaled = a.scale(&4);
        assert_eq!(scaled.coordinates(), &[8, 12]);
    }

    #[test]
    fn finite_vector_sub() {
        let a = FreeModuleVector::<i64>::new(vec![5, 6]);
        let b = FreeModuleVector::<i64>::new(vec![2, 3]);
        let sub = a.checked_sub(&b).unwrap();
        assert_eq!(sub.coordinates(), &[3, 3]);
    }

    #[test]
    fn zero_rank_free_module_is_allowed() {
        let z = FreeModuleVector::<i64>::zero_of_dimension(0);
        assert_eq!(z.dimension(), 0);
        let w = FreeModuleVector::<i64>::new(vec![]);
        assert_eq!(z.checked_add(&w).unwrap().coordinates(), &[] as &[i64]);
    }
}
