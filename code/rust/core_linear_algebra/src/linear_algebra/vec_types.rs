use thiserror::Error;

/// Errors for symbolic vector-space-shaped objects and morphisms.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum VecSymbolicError {
    #[error("object name cannot be empty")]
    EmptyObjectName,

    #[error("morphism name cannot be empty")]
    EmptyMorphismName,
}

/// Symbolic vector-space-shaped object.
///
/// This records only a dimension and symbolic name. It does not carry:
/// - a scalar field;
/// - a basis;
/// - vectors;
/// - topology;
/// - inner product;
/// - linear structure witness.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct VecOb {
    dim: usize,
    name: String,
}

impl VecOb {
    pub fn new_checked(dim: usize, name: impl Into<String>) -> Result<Self, VecSymbolicError> {
        let name = name.into().trim().to_owned();

        if name.is_empty() {
            return Err(VecSymbolicError::EmptyObjectName);
        }

        Ok(Self { dim, name })
    }

    pub fn new(dim: usize, name: impl Into<String>) -> Result<Self, VecSymbolicError> {
        Self::new_checked(dim, name)
    }

    /// Internal constructor for already-validated symbolic objects.
    ///
    /// Caller must guarantee `name` is nonempty and canonicalized.
    pub(crate) fn new_unchecked(dim: usize, name: impl Into<String>) -> Self {
        Self {
            dim,
            name: name.into(),
        }
    }

    /// Symbolic tensor unit object.
    ///
    /// This is metadata only; it does not certify a concrete ground field.
    pub fn one() -> Self {
        Self::new_unchecked(1, "I")
    }

    pub fn dim(&self) -> usize {
        self.dim
    }

    pub fn name(&self) -> &str {
        &self.name
    }
}

/// Symbolic morphism between vector-space-shaped objects.
///
/// This is a named arrow with source and target only. It is not a certified
/// linear map and does not carry a matrix/function.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VecMor {
    src: VecOb,
    tgt: VecOb,
    name: String,
}

impl VecMor {
    pub fn new_checked(
        src: VecOb,
        tgt: VecOb,
        name: impl Into<String>,
    ) -> Result<Self, VecSymbolicError> {
        let name = name.into().trim().to_owned();

        if name.is_empty() {
            return Err(VecSymbolicError::EmptyMorphismName);
        }

        Ok(Self { src, tgt, name })
    }

    pub fn new(src: VecOb, tgt: VecOb, name: impl Into<String>) -> Result<Self, VecSymbolicError> {
        Self::new_checked(src, tgt, name)
    }

    /// Internal constructor for already-validated symbolic morphisms.
    ///
    /// Caller must guarantee `name` is nonempty and canonicalized.
    pub(crate) fn new_unchecked(src: VecOb, tgt: VecOb, name: impl Into<String>) -> Self {
        Self {
            src,
            tgt,
            name: name.into(),
        }
    }

    pub fn identity(ob: &VecOb) -> Self {
        Self::new_unchecked(ob.clone(), ob.clone(), format!("id_{}", ob.name()))
    }

    pub fn src(&self) -> &VecOb {
        &self.src
    }

    pub fn tgt(&self) -> &VecOb {
        &self.tgt
    }

    pub fn name(&self) -> &str {
        &self.name
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/vec_types.rs
// Claim: urn:core:crates_rs:core-linear-algebra:vec-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn vec_ob_trims_name() -> Result<(), VecSymbolicError> {
        let ob = VecOb::new_checked(3, " V ")?;
        assert_eq!(ob.name(), "V");
        Ok(())
    }

    #[test]
    fn vec_mor_trims_name() -> Result<(), VecSymbolicError> {
        let src = VecOb::new_checked(2, "V")?;
        let tgt = VecOb::new_checked(3, "W")?;

        let mor = VecMor::new_checked(src, tgt, " f ")?;
        assert_eq!(mor.name(), "f");
        Ok(())
    }

    #[test]
    fn zero_dimensional_object_is_allowed() -> Result<(), VecSymbolicError> {
        let ob = VecOb::new_checked(0, "0")?;
        assert_eq!(ob.dim(), 0);
        Ok(())
    }

    #[test]
    fn whitespace_object_name_rejected() {
        assert!(matches!(
            VecOb::new_checked(3, "   "),
            Err(VecSymbolicError::EmptyObjectName)
        ));
    }

    #[test]
    fn whitespace_morphism_name_rejected() {
        let src = VecOb::new_checked(2, "V").unwrap();
        let tgt = VecOb::new_checked(3, "W").unwrap();

        assert!(matches!(
            VecMor::new_checked(src, tgt, "   "),
            Err(VecSymbolicError::EmptyMorphismName)
        ));
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TensorDimWitness {
    product: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TensorDimError {
    Overflow,
    NotAssociative,
}

impl TensorDimWitness {
    pub fn try_associate(a: usize, b: usize, c: usize) -> Result<Self, TensorDimError> {
        let ab = a.checked_mul(b).ok_or(TensorDimError::Overflow)?;
        let left = ab.checked_mul(c).ok_or(TensorDimError::Overflow)?;
        let bc = b.checked_mul(c).ok_or(TensorDimError::Overflow)?;
        let right = a.checked_mul(bc).ok_or(TensorDimError::Overflow)?;
        if left != right {
            return Err(TensorDimError::NotAssociative);
        }
        Ok(Self { product: left })
    }

    pub fn product(&self) -> usize {
        self.product
    }
}

#[cfg(test)]
mod tensor_dim_tests {
    use super::*;

    #[test]
    fn dimension_multiplication_associates() {
        let witness = TensorDimWitness::try_associate(3, 5, 7);
        assert!(matches!(witness, Ok(witness) if witness.product() == 105));
        assert!(matches!(
            TensorDimWitness::try_associate(usize::MAX, 2, 2),
            Err(TensorDimError::Overflow)
        ));
    }
}
