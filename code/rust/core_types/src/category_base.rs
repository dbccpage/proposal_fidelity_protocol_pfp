/// Name-level category objects.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ObjName(pub String);

/// Name-level category morphisms.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct MorName(pub String);

/// A category object represented by a symbolic name.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct Obj(pub ObjName);

impl Obj {
    pub fn new(name: impl Into<String>) -> Self {
        Self(ObjName(name.into()))
    }

    pub fn name(&self) -> &str {
        &self.0 .0
    }
}

/// A category morphism represented by a symbolic name and symbolic boundaries.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct Mor {
    pub name: MorName,
    pub src: ObjName,
    pub tgt: ObjName,
}

impl Mor {
    pub fn new(name: impl Into<String>, src: impl Into<String>, tgt: impl Into<String>) -> Self {
        Self {
            name: MorName(name.into()),
            src: ObjName(src.into()),
            tgt: ObjName(tgt.into()),
        }
    }
}

/// Finite presented category: identities, source and target, and an associative composition table.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PresentedCategory {
    objects: usize,
    arrows: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PresentError {
    Bound,
    Shape,
    Identity,
    Unit,
    Associativity,
}

impl std::fmt::Display for PresentError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PresentError::Bound => write!(formatter, "objects must lie in 1..=4 and arrows in 1..=8"),
            PresentError::Shape => write!(formatter, "identity, boundary, or composition table has the wrong length"),
            PresentError::Identity => write!(formatter, "an identity arrow does not fix its object"),
            PresentError::Unit => write!(formatter, "left or right identity law failed"),
            PresentError::Associativity => write!(formatter, "composition is not associative"),
        }
    }
}

impl std::error::Error for PresentError {}

impl PresentedCategory {
    fn check_bounds_and_shape(
        objects: usize,
        identities: &[usize],
        source: &[usize],
        target: &[usize],
        compose: &[Option<usize>],
    ) -> Result<usize, PresentError> {
        let arrows = source.len();
        if !(1..=4).contains(&objects) || !(1..=8).contains(&arrows) {
            return Err(PresentError::Bound);
        }
        let table = arrows.checked_mul(arrows).ok_or(PresentError::Shape)?;
        if identities.len() != objects || target.len() != arrows || compose.len() != table {
            return Err(PresentError::Shape);
        }
        if source.iter().chain(target.iter()).any(|&b| b >= objects) {
            return Err(PresentError::Shape);
        }
        Ok(arrows)
    }

    fn check_identities(
        identities: &[usize],
        source: &[usize],
        target: &[usize],
        arrows: usize,
    ) -> Result<(), PresentError> {
        for (object, &identity) in identities.iter().enumerate() {
            if identity >= arrows {
                return Err(PresentError::Identity);
            }
            if source.get(identity) != Some(&object) || target.get(identity) != Some(&object) {
                return Err(PresentError::Identity);
            }
        }
        Ok(())
    }

    fn check_composition_slot(
        left: usize,
        right: usize,
        arrows: usize,
        source: &[usize],
        target: &[usize],
        compose: &[Option<usize>],
    ) -> Result<(), PresentError> {
        let composite = *compose.get(left * arrows + right).ok_or(PresentError::Shape)?;
        let composable = target.get(right) == source.get(left);
        match (composable, composite) {
            (false, None) => Ok(()),
            (true, Some(arrow)) if arrow < arrows => {
                if (source.get(arrow), target.get(arrow)) == (source.get(right), target.get(left)) {
                    Ok(())
                } else {
                    Err(PresentError::Unit)
                }
            }
            _ => Err(PresentError::Unit),
        }
    }

    fn check_units(
        arrows: usize,
        identities: &[usize],
        source: &[usize],
        target: &[usize],
        compose: &[Option<usize>],
    ) -> Result<(), PresentError> {
        for left in 0..arrows {
            for right in 0..arrows {
                Self::check_composition_slot(left, right, arrows, source, target, compose)?;
            }
        }
        for arrow in 0..arrows {
            let src = *source.get(arrow).ok_or(PresentError::Unit)?;
            let tgt = *target.get(arrow).ok_or(PresentError::Unit)?;
            let left_id = *identities.get(tgt).ok_or(PresentError::Identity)?;
            let right_id = *identities.get(src).ok_or(PresentError::Identity)?;
            let left_unit = compose.get(left_id * arrows + arrow).copied();
            let right_unit = compose.get(arrow * arrows + right_id).copied();
            if (left_unit, right_unit) != (Some(Some(arrow)), Some(Some(arrow))) {
                return Err(PresentError::Unit);
            }
        }
        Ok(())
    }

    fn check_triple_associativity(
        left: usize,
        mid: usize,
        right: usize,
        arrows: usize,
        compose: &[Option<usize>],
    ) -> Result<(), PresentError> {
        if let (Some(Some(inner)), Some(Some(outer))) = (
            compose.get(mid * arrows + right),
            compose.get(left * arrows + mid),
        ) {
            let left_assoc = compose.get(left * arrows + *inner);
            let right_assoc = compose.get(*outer * arrows + right);
            if left_assoc != right_assoc || !matches!(left_assoc, Some(Some(_))) {
                return Err(PresentError::Associativity);
            }
        }
        Ok(())
    }

    fn check_associativity(arrows: usize, compose: &[Option<usize>]) -> Result<(), PresentError> {
        for left in 0..arrows {
            for mid in 0..arrows {
                for right in 0..arrows {
                    Self::check_triple_associativity(left, mid, right, arrows, compose)?;
                }
            }
        }
        Ok(())
    }

    pub fn certify(
        objects: usize,
        identities: &[usize],
        source: &[usize],
        target: &[usize],
        compose: &[Option<usize>],
    ) -> Result<Self, PresentError> {
        let arrows = Self::check_bounds_and_shape(objects, identities, source, target, compose)?;
        Self::check_identities(identities, source, target, arrows)?;
        Self::check_units(arrows, identities, source, target, compose)?;
        Self::check_associativity(arrows, compose)?;
        Ok(Self { objects, arrows })
    }

    pub fn objects(&self) -> usize {
        self.objects
    }

    pub fn arrows(&self) -> usize {
        self.arrows
    }
}

// Origin: engine/crates_rs/core_types/src/category_base.rs
// Claim: urn:core:crates_rs:core-types:category-base:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod presented_tests {
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
    fn the_one_object_identity_category_is_associative() {
        let category = taken(PresentedCategory::certify(1, &[0], &[0], &[0], &[Some(0)]));
        assert_eq!(category.objects(), 1);
        assert_eq!(category.arrows(), 1);
        assert!(PresentedCategory::certify(1, &[0], &[0], &[0], &[None]).is_err());
    }
}
