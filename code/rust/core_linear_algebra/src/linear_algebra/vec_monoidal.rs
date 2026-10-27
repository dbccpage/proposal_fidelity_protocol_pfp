use super::vec_category::VecCategory;
use super::vec_types::{VecMor, VecOb, VecSymbolicError};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum VecMonoidalError {
    #[error("tensor dimension overflow: left={left}, right={right}")]
    DimensionOverflow { left: usize, right: usize },

    #[error("invalid object name: {source}")]
    InvalidObjectName {
        #[source]
        source: VecSymbolicError,
    },

    #[error("invalid morphism name: {source}")]
    InvalidMorphismName {
        #[source]
        source: VecSymbolicError,
    },
}

/// Symbolic monoidal operations for `VecCategory`.
///
/// This is formal source/target bookkeeping only. It does not certify
/// monoidal coherence, naturality, or concrete tensor products of linear maps.
impl VecCategory {
    pub fn tensor_ob_checked(
        &self,
        left: &VecOb,
        right: &VecOb,
    ) -> Result<VecOb, VecMonoidalError> {
        let dim =
            left.dim()
                .checked_mul(right.dim())
                .ok_or(VecMonoidalError::DimensionOverflow {
                    left: left.dim(),
                    right: right.dim(),
                })?;

        VecOb::new_checked(dim, format!("{} tensor {}", left.name(), right.name()))
            .map_err(|source| VecMonoidalError::InvalidObjectName { source })
    }

    pub fn tensor_mor_checked(
        &self,
        left: &VecMor,
        right: &VecMor,
    ) -> Result<VecMor, VecMonoidalError> {
        let src = self.tensor_ob_checked(left.src(), right.src())?;
        let tgt = self.tensor_ob_checked(left.tgt(), right.tgt())?;

        VecMor::new_checked(src, tgt, format!("{} tensor {}", left.name(), right.name()))
            .map_err(|source| VecMonoidalError::InvalidMorphismName { source })
    }

    /// Formal associator `(a ⊗ b) ⊗ c → a ⊗ (b ⊗ c)`.
    ///
    /// This is symbolic. Coherence is not verified here.
    pub fn associator_checked(
        &self,
        a: &VecOb,
        b: &VecOb,
        c: &VecOb,
    ) -> Result<VecMor, VecMonoidalError> {
        let ab = self.tensor_ob_checked(a, b)?;
        let bc = self.tensor_ob_checked(b, c)?;
        let src = self.tensor_ob_checked(&ab, c)?;
        let tgt = self.tensor_ob_checked(a, &bc)?;

        VecMor::new_checked(
            src,
            tgt,
            format!("alpha_({},{},{})", a.name(), b.name(), c.name()),
        )
        .map_err(|source| VecMonoidalError::InvalidMorphismName { source })
    }

    /// Formal left unitor `I ⊗ a → a`.
    ///
    /// This is symbolic. Triangle coherence is not verified here.
    pub fn left_unitor_checked(&self, a: &VecOb) -> Result<VecMor, VecMonoidalError> {
        let src = self.tensor_ob_checked(&VecOb::one(), a)?;

        VecMor::new_checked(src, a.clone(), format!("lambda_{}", a.name()))
            .map_err(|source| VecMonoidalError::InvalidMorphismName { source })
    }

    /// Formal right unitor `a ⊗ I → a`.
    ///
    /// This is symbolic. Triangle coherence is not verified here.
    pub fn right_unitor_checked(&self, a: &VecOb) -> Result<VecMor, VecMonoidalError> {
        let src = self.tensor_ob_checked(a, &VecOb::one())?;

        VecMor::new_checked(src, a.clone(), format!("rho_{}", a.name()))
            .map_err(|source| VecMonoidalError::InvalidMorphismName { source })
    }

    /// Formal braiding `a ⊗ b → b ⊗ a`.
    ///
    /// This is symbolic. Symmetry and hexagon laws are not verified here.
    pub fn braiding_checked(&self, a: &VecOb, b: &VecOb) -> Result<VecMor, VecMonoidalError> {
        let src = self.tensor_ob_checked(a, b)?;
        let tgt = self.tensor_ob_checked(b, a)?;

        VecMor::new_checked(src, tgt, format!("sigma_({},{})", a.name(), b.name()))
            .map_err(|source| VecMonoidalError::InvalidMorphismName { source })
    }
}

/// A localized, strictly fallible trait for symbolic monoidal operations.
///
/// This avoids panicking implementations of upstream infallible category traits.
pub trait FallibleSymbolicMonoidal {
    type Ob;
    type Mor;
    type Error;

    fn try_tensor_ob(&self, left: &Self::Ob, right: &Self::Ob) -> Result<Self::Ob, Self::Error>;
    fn try_tensor_mor(&self, left: &Self::Mor, right: &Self::Mor)
        -> Result<Self::Mor, Self::Error>;
    fn unit_ob(&self) -> Self::Ob;
    fn try_associator(
        &self,
        a: &Self::Ob,
        b: &Self::Ob,
        c: &Self::Ob,
    ) -> Result<Self::Mor, Self::Error>;
    fn try_left_unitor(&self, a: &Self::Ob) -> Result<Self::Mor, Self::Error>;
    fn try_right_unitor(&self, a: &Self::Ob) -> Result<Self::Mor, Self::Error>;
    fn try_braiding(&self, a: &Self::Ob, b: &Self::Ob) -> Result<Self::Mor, Self::Error>;
}

impl FallibleSymbolicMonoidal for VecCategory {
    type Ob = VecOb;
    type Mor = VecMor;
    type Error = VecMonoidalError;

    fn try_tensor_ob(&self, left: &Self::Ob, right: &Self::Ob) -> Result<Self::Ob, Self::Error> {
        self.tensor_ob_checked(left, right)
    }

    fn try_tensor_mor(
        &self,
        left: &Self::Mor,
        right: &Self::Mor,
    ) -> Result<Self::Mor, Self::Error> {
        self.tensor_mor_checked(left, right)
    }

    fn unit_ob(&self) -> Self::Ob {
        VecOb::one()
    }

    fn try_associator(
        &self,
        a: &Self::Ob,
        b: &Self::Ob,
        c: &Self::Ob,
    ) -> Result<Self::Mor, Self::Error> {
        self.associator_checked(a, b, c)
    }

    fn try_left_unitor(&self, a: &Self::Ob) -> Result<Self::Mor, Self::Error> {
        self.left_unitor_checked(a)
    }

    fn try_right_unitor(&self, a: &Self::Ob) -> Result<Self::Mor, Self::Error> {
        self.right_unitor_checked(a)
    }

    fn try_braiding(&self, a: &Self::Ob, b: &Self::Ob) -> Result<Self::Mor, Self::Error> {
        self.braiding_checked(a, b)
    }
}

/// Boundary marker: upstream monoidal traits are intentionally not implemented.
///
/// `MonoidalCategory`, `BraidedMonoidal`, or `SymmetricMonoidalCategory` should
/// not be implemented for `VecCategory` while their APIs require infallible
/// operations. Tensor dimension overflow and invalid generated names are real
/// failure modes, and panicking with `.expect()` is not acceptable verifier code.
pub struct VecMonoidalBoundary;

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/vec_monoidal.rs
// Claim: urn:core:crates_rs:core-linear-algebra:vec-monoidal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tensor_object_multiplies_dimensions() -> Result<(), VecMonoidalError> {
        let cat = VecCategory;
        let x = VecOb::new_checked(2, "X").unwrap();
        let y = VecOb::new_checked(3, "Y").unwrap();

        let xy = cat.tensor_ob_checked(&x, &y)?;

        assert_eq!(xy.dim(), 6);
        assert_eq!(xy.name(), "X tensor Y");
        Ok(())
    }

    #[test]
    fn tensor_object_rejects_dimension_overflow() {
        let cat = VecCategory;
        let x = VecOb::new_checked(usize::MAX, "X").unwrap();
        let y = VecOb::new_checked(2, "Y").unwrap();

        assert!(matches!(
            cat.tensor_ob_checked(&x, &y),
            Err(VecMonoidalError::DimensionOverflow { .. })
        ));
    }

    #[test]
    fn tensor_morphism_has_tensor_source_and_target() -> Result<(), VecMonoidalError> {
        let cat = VecCategory;

        let x = VecOb::new_checked(2, "X").unwrap();
        let y = VecOb::new_checked(3, "Y").unwrap();
        let z = VecOb::new_checked(5, "Z").unwrap();
        let w = VecOb::new_checked(7, "W").unwrap();

        let f = VecMor::new_checked(x.clone(), y.clone(), "f").unwrap();
        let g = VecMor::new_checked(z.clone(), w.clone(), "g").unwrap();

        let fg = cat.tensor_mor_checked(&f, &g)?;

        assert_eq!(fg.src().dim(), 10);
        assert_eq!(fg.tgt().dim(), 21);
        Ok(())
    }

    #[test]
    fn associator_has_expected_source_and_target() -> Result<(), VecMonoidalError> {
        let cat = VecCategory;

        let a = VecOb::new_checked(2, "A").unwrap();
        let b = VecOb::new_checked(3, "B").unwrap();
        let c = VecOb::new_checked(5, "C").unwrap();

        let alpha = cat.associator_checked(&a, &b, &c)?;

        assert_eq!(alpha.src().dim(), 30);
        assert_eq!(alpha.tgt().dim(), 30);
        Ok(())
    }

    #[test]
    fn braiding_swaps_tensor_source_target() -> Result<(), VecMonoidalError> {
        let cat = VecCategory;

        let a = VecOb::new_checked(2, "A").unwrap();
        let b = VecOb::new_checked(3, "B").unwrap();

        let sigma = cat.braiding_checked(&a, &b)?;

        assert_eq!(sigma.src().dim(), 6);
        assert_eq!(sigma.tgt().dim(), 6);
        assert!(sigma.src().name().contains("A tensor B"));
        assert!(sigma.tgt().name().contains("B tensor A"));
        Ok(())
    }
}
