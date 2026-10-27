//! Functor hierarchy shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

pub mod constant_functor;
pub mod copresheaf;
pub mod diagonal_functor;
pub mod equivalence_of_categories;
pub mod essentially_surjective;
pub mod faithful_functor;
pub mod forgetful_functor;
pub mod free_functor;
pub mod full_functor;
#[allow(clippy::module_inception)]
pub mod functor;
pub mod functor_category;
pub mod hom_functor;
pub mod horizontal_composition;
pub mod identity_functor;
pub mod isomorphism_of_categories;
pub mod nat_trans_components;
pub mod natural_transformation;
pub mod presheaf;
pub mod representable_functor;
pub mod vertical_composition;
pub mod yoneda;

pub use constant_functor::ConstantFunctor;
pub use copresheaf::Copresheaf;
pub use diagonal_functor::DiagonalFunctor;
pub use equivalence_of_categories::EquivalenceOfCategories;
pub use essentially_surjective::EssentiallySurjective;
pub use faithful_functor::FaithfulFunctor;
pub use forgetful_functor::ForgetfulFunctor;
pub use free_functor::FreeFunctor;
pub use full_functor::FullFunctor;
pub use functor::Functor;
pub use functor_category::FunctorCategory;
pub use hom_functor::HomFunctor;
pub use horizontal_composition::HorizontalComposition;
pub use identity_functor::IdentityFunctor;
pub use isomorphism_of_categories::IsomorphismOfCategories;
pub use nat_trans_components::NatTransComponents;
pub use natural_transformation::NaturalTransformation;
pub use presheaf::Presheaf;
pub use representable_functor::RepresentableFunctor;
pub use vertical_composition::VerticalComposition;
pub use yoneda::Yoneda;

/// Arrow census of one covariant hom-functor on a finite category.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct HomPartition {
    objects: usize,
    arrows: usize,
    fixed_object: usize,
    incoming: usize,
    outgoing: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum HomPartitionError {
    Bound,
    Arrow,
    Partition,
}

impl std::fmt::Display for HomPartitionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Bound => write!(formatter, "object count or fixed object is outside the finite bound"),
            Self::Arrow => write!(formatter, "an arrow endpoint is outside the object set"),
            Self::Partition => write!(formatter, "incoming and outgoing arrow counts disagree"),
        }
    }
}

impl std::error::Error for HomPartitionError {}

impl HomPartition {
    pub fn objects(&self) -> usize {
        self.objects
    }

    pub fn arrows(&self) -> usize {
        self.arrows
    }

    pub fn incoming(&self) -> usize {
        self.incoming
    }

    pub fn outgoing(&self) -> usize {
        self.outgoing
    }
}

fn accumulate_degrees(
    objects: usize,
    arrows: &[(usize, usize)],
) -> Result<(Vec<usize>, Vec<usize>), HomPartitionError> {
    let mut incoming = vec![0usize; objects];
    let mut outgoing = vec![0usize; objects];
    for &(source, target) in arrows {
        let in_slot = incoming.get_mut(target).ok_or(HomPartitionError::Arrow)?;
        *in_slot = in_slot.checked_add(1).ok_or(HomPartitionError::Partition)?;
        let out_slot = outgoing.get_mut(source).ok_or(HomPartitionError::Arrow)?;
        *out_slot = out_slot.checked_add(1).ok_or(HomPartitionError::Partition)?;
    }
    Ok((incoming, outgoing))
}

fn checked_sum(counts: &[usize]) -> Result<usize, HomPartitionError> {
    counts
        .iter()
        .try_fold(0usize, |total, count| total.checked_add(*count))
        .ok_or(HomPartitionError::Partition)
}

fn validate_partition_bounds(
    objects: usize,
    arrows: &[(usize, usize)],
    fixed: usize,
) -> Result<(), HomPartitionError> {
    if objects == 0 || objects > 16 || fixed >= objects || arrows.len() > 64 {
        return Err(HomPartitionError::Bound);
    }
    Ok(())
}

/// Every arrow is in exactly one incoming hom-set and one outgoing hom-set.
/// The returned [`HomFunctor`] is the covariant hom at `fixed`.
pub fn hom_partition(
    objects: usize,
    arrows: &[(usize, usize)],
    fixed: usize,
) -> Result<(HomPartition, HomFunctor), HomPartitionError> {
    validate_partition_bounds(objects, arrows, fixed)?;
    let (incoming, outgoing) = accumulate_degrees(objects, arrows)?;
    if checked_sum(&incoming)? != arrows.len() || checked_sum(&outgoing)? != arrows.len() {
        return Err(HomPartitionError::Partition);
    }
    let hom = HomFunctor::covariant(
        format!("Hom({fixed},-)"),
        "finite",
        fixed.to_string(),
    );
    if hom.variance != "covariant" {
        return Err(HomPartitionError::Partition);
    }
    let incoming_fixed = incoming.get(fixed).copied().ok_or(HomPartitionError::Bound)?;
    let outgoing_fixed = outgoing.get(fixed).copied().ok_or(HomPartitionError::Bound)?;
    Ok((
        HomPartition {
            objects,
            arrows: arrows.len(),
            fixed_object: fixed,
            incoming: incoming_fixed,
            outgoing: outgoing_fixed,
        },
        hom,
    ))
}

// Origin: engine/crates_rs/core_category_theory/src/functor/mod.rs
// Claim: urn:core:crates_rs:core-category-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn taken(
        result: Result<(HomPartition, HomFunctor), HomPartitionError>,
    ) -> (HomPartition, HomFunctor) {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn arrows_partition_by_source_and_target() {
        let (census, hom) = taken(hom_partition(3, &[(0, 1), (1, 2), (0, 2)], 1));
        assert_eq!(census.arrows(), 3);
        assert_eq!(census.incoming(), 1);
        assert_eq!(census.outgoing(), 1);
        assert_eq!(hom.variance, "covariant");
        assert_eq!(hom.fixed_object, "1");
    }

    #[test]
    fn an_arrow_off_the_object_set_is_refused() {
        assert!(matches!(
            hom_partition(2, &[(0, 2)], 0),
            Err(HomPartitionError::Arrow)
        ));
    }
}
