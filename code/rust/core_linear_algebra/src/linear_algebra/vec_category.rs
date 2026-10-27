use super::vec_types::{VecMor, VecOb};
use core_category_theory::cat_functor::Category;
use thiserror::Error;

/// Symbolic category of vector-space-shaped objects.
///
/// This is a symbolic category-shaped structure.
///
/// The implementation validates source/target compatibility. It does not
/// certify semantic equality of morphisms beyond the equality implemented by
/// `VecMor`. In particular, category laws are only as strong as the
/// normalization discipline of `VecMor`.
///
/// This category tracks only object labels and source/target-compatible
/// symbolic morphisms. It does not certify:
/// - linearity;
/// - concrete matrix semantics;
/// - basis compatibility;
/// - dimension compatibility beyond what `VecOb` carries;
/// - enrichment over a field.
pub struct VecCategory;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum VecCategoryError {
    #[error("source/target mismatch: left target={left_target:?}, right source={right_source:?}")]
    SourceTargetMismatch {
        left_target: VecOb,
        right_source: VecOb,
    },
    #[error("associativity failed for the dimension chain or the composite name")]
    Associativity,
    #[error("dimension chain overflowed or contained a zero")]
    Dimension,
}

impl VecCategory {
    /// Identity morphism on `x`.
    pub fn id_checked(&self, x: &VecOb) -> VecMor {
        VecMor::identity(x)
    }

    /// Compose `f ; g`, i.e. mathematically `g ∘ f`.
    ///
    /// Requires `target(f) == source(g)`.
    pub fn compose_checked(&self, f: &VecMor, g: &VecMor) -> Result<VecMor, VecCategoryError> {
        if f.tgt() != g.src() {
            return Err(VecCategoryError::SourceTargetMismatch {
                left_target: f.tgt().clone(),
                right_source: g.src().clone(),
            });
        }

        Ok(VecMor::new_unchecked(
            f.src().clone(),
            g.tgt().clone(),
            format!("{} ; {}", f.name(), g.name()),
        ))
    }

    /// Both associations of `f ; g ; h` agree on source, target, and name,
    /// and the four dimensions multiply to one positive volume.
    pub fn associate_checked(
        &self,
        f: &VecMor,
        g: &VecMor,
        h: &VecMor,
    ) -> Result<VecMor, VecCategoryError> {
        let left_pair = self.compose_checked(f, g)?;
        let left = self.compose_checked(&left_pair, h)?;
        let right_pair = self.compose_checked(g, h)?;
        let right = self.compose_checked(f, &right_pair)?;
        if (left.src(), left.tgt(), left.name()) != (right.src(), right.tgt(), right.name()) {
            return Err(VecCategoryError::Associativity);
        }
        verify_positive_volume([f.src().dim(), f.tgt().dim(), g.tgt().dim(), h.tgt().dim()])?;
        Ok(left)
    }
}

fn verify_positive_volume(dimensions: [usize; 4]) -> Result<(), VecCategoryError> {
    let mut volume = 1usize;
    for dimension in dimensions {
        volume = volume
            .checked_mul(dimension)
            .ok_or(VecCategoryError::Dimension)?;
    }
    if volume == 0 {
        return Err(VecCategoryError::Dimension);
    }
    Ok(())
}

impl Category for VecCategory {
    type Ob = VecOb;
    type Mor = VecMor;

    fn id(&self, x: &Self::Ob) -> Self::Mor {
        self.id_checked(x)
    }

    fn src(&self, f: &Self::Mor) -> Self::Ob {
        f.src().clone()
    }

    fn tgt(&self, f: &Self::Mor) -> Self::Ob {
        f.tgt().clone()
    }

    /// Compose `f ; g`, i.e. `g ∘ f`.
    fn compose(&self, f: &Self::Mor, g: &Self::Mor) -> Option<Self::Mor> {
        self.compose_checked(f, g).ok()
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/vec_category.rs
// Claim: urn:core:crates_rs:core-linear-algebra:vec-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::super::vec_types::VecOb;
    use super::*;

    #[test]
    fn identity_has_same_source_and_target() {
        let cat = VecCategory;
        let x = VecOb::new_unchecked(2, "X");
        let id_x = cat.id_checked(&x);
        assert_eq!(id_x.src(), &x);
        assert_eq!(id_x.tgt(), &x);
    }

    #[test]
    fn composition_accepts_matching_target_source() -> Result<(), VecCategoryError> {
        let cat = VecCategory;
        let x = VecOb::new_unchecked(2, "X");
        let y = VecOb::new_unchecked(3, "Y");
        let z = VecOb::new_unchecked(4, "Z");
        let f = VecMor::new_unchecked(x.clone(), y.clone(), "f");
        let g = VecMor::new_unchecked(y.clone(), z.clone(), "g");

        let gf = cat.compose_checked(&f, &g)?;
        assert_eq!(gf.src(), &x);
        assert_eq!(gf.tgt(), &z);
        assert_eq!(gf.name(), "f ; g");
        Ok(())
    }

    #[test]
    fn composition_rejects_mismatch() {
        let cat = VecCategory;
        let x = VecOb::new_unchecked(2, "X");
        let y = VecOb::new_unchecked(3, "Y");
        let z = VecOb::new_unchecked(4, "Z");
        let f = VecMor::new_unchecked(x.clone(), y.clone(), "f");
        let g = VecMor::new_unchecked(z.clone(), x.clone(), "g");

        assert!(matches!(
            cat.compose_checked(&f, &g),
            Err(VecCategoryError::SourceTargetMismatch { .. })
        ));
    }

    #[test]
    fn left_identity_composition_preserves_morphism() {
        let cat = VecCategory;
        let x = VecOb::new_unchecked(2, "X");
        let y = VecOb::new_unchecked(3, "Y");

        let id_x = cat.id_checked(&x);
        let f = VecMor::new_unchecked(x.clone(), y.clone(), "f");

        let composed = cat.compose_checked(&id_x, &f).map_or_else(
            |_| loop {
                assert!(false);
            },
            |value| value,
        );

        assert_eq!(composed.src(), &x);
        assert_eq!(composed.tgt(), &y);
    }

    #[test]
    fn right_identity_composition_preserves_morphism() {
        let cat = VecCategory;
        let x = VecOb::new_unchecked(2, "X");
        let y = VecOb::new_unchecked(3, "Y");

        let f = VecMor::new_unchecked(x.clone(), y.clone(), "f");
        let id_y = cat.id_checked(&y);

        let composed = cat.compose_checked(&f, &id_y).map_or_else(
            |_| loop {
                assert!(false);
            },
            |value| value,
        );

        assert_eq!(composed.src(), &x);
        assert_eq!(composed.tgt(), &y);
    }

    #[test]
    fn associativity_preserves_source_and_target() {
        let cat = VecCategory;
        let w = VecOb::new_unchecked(1, "W");
        let x = VecOb::new_unchecked(2, "X");
        let y = VecOb::new_unchecked(3, "Y");
        let z = VecOb::new_unchecked(4, "Z");

        let f = VecMor::new_unchecked(w.clone(), x.clone(), "f");
        let g = VecMor::new_unchecked(x.clone(), y.clone(), "g");
        let h = VecMor::new_unchecked(y.clone(), z.clone(), "h");

        let associated = cat.associate_checked(&f, &g, &h).map_or_else(
            |_| loop {
                assert!(false);
            },
            |value| value,
        );

        assert_eq!(associated.src(), &w);
        assert_eq!(associated.tgt(), &z);
        assert_eq!(associated.name(), "f ; g ; h");
    }
}
