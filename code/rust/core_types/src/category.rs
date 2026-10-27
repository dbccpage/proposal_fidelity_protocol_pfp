/// Identifier-level category objects.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ObjId(pub u128);

/// Identifier-level category morphisms.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct MorId(pub u128);

/// A category object represented only by its stable identifier.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Obj {
    pub id: ObjId,
}

impl Obj {
    pub fn new(id: ObjId) -> Self {
        Self { id }
    }
}

/// A category morphism represented only by its stable identifier and boundaries.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Mor {
    pub uuid: MorId,
    pub src: ObjId,
    pub tgt: ObjId,
}

impl Mor {
    pub fn new(uuid: MorId, src: ObjId, tgt: ObjId) -> Self {
        Self { uuid, src, tgt }
    }

    pub fn id(&self) -> MorId {
        self.uuid
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_types/src/category.rs
// Claim: urn:core:types:category:finite-presentation:v1
// AuthorityEffect: None

use std::collections::BTreeMap;

const MAX_ARROWS: usize = 32;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PresentedCategory {
    identities: usize,
    arrows: usize,
    composites: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PresentationError {
    Empty,
    TooManyArrows { count: usize },
    IdentityNotEndomorphism { id: u128 },
    DuplicateIdentity { object: u128 },
    MissingIdentity { object: u128 },
    DuplicateArrow { id: u128 },
    UnknownArrow { id: u128 },
    DuplicateComposite { left: u128, right: u128 },
    CompositionBoundary { left: u128, right: u128 },
    CompositeShape { id: u128 },
    Associativity { left: u128, right: u128 },
}

// Origin: engine/crates_rs/core_types/src/category.rs
// Claim: urn:core:crates_rs:core-types:category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PresentationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PresentationError {}

fn index_identities_and_arrows(
    identities: &[Mor],
    arrows: &[Mor],
) -> Result<(BTreeMap<u128, Mor>, BTreeMap<u128, u128>), PresentationError> {
    let mut by_id: BTreeMap<u128, Mor> = BTreeMap::new();
    let mut identity_of: BTreeMap<u128, u128> = BTreeMap::new();
    for identity in identities {
        if identity.src != identity.tgt {
            return Err(PresentationError::IdentityNotEndomorphism { id: identity.uuid.0 });
        }
        if identity_of.insert(identity.src.0, identity.uuid.0).is_some() {
            return Err(PresentationError::DuplicateIdentity { object: identity.src.0 });
        }
        if by_id.insert(identity.uuid.0, *identity).is_some() {
            return Err(PresentationError::DuplicateArrow { id: identity.uuid.0 });
        }
    }
    for arrow in arrows {
        if by_id.insert(arrow.uuid.0, *arrow).is_some() {
            return Err(PresentationError::DuplicateArrow { id: arrow.uuid.0 });
        }
    }
    Ok((by_id, identity_of))
}

fn ensure_all_objects_have_identities(
    by_id: &BTreeMap<u128, Mor>,
    identity_of: &BTreeMap<u128, u128>,
) -> Result<(), PresentationError> {
    let mut objects = BTreeMap::<u128, ()>::new();
    for arrow in by_id.values() {
        objects.insert(arrow.src.0, ());
        objects.insert(arrow.tgt.0, ());
    }
    for object in objects.keys() {
        if !identity_of.contains_key(object) {
            return Err(PresentationError::MissingIdentity { object: *object });
        }
    }
    Ok(())
}

fn index_composites(
    by_id: &BTreeMap<u128, Mor>,
    composites: &[(u128, u128, u128)],
) -> Result<BTreeMap<(u128, u128), u128>, PresentationError> {
    let mut composed: BTreeMap<(u128, u128), u128> = BTreeMap::new();
    for &(left_id, right_id, result_id) in composites {
        let left = by_id.get(&left_id).ok_or(PresentationError::UnknownArrow { id: left_id })?;
        let right = by_id.get(&right_id).ok_or(PresentationError::UnknownArrow { id: right_id })?;
        let result = by_id.get(&result_id).ok_or(PresentationError::UnknownArrow { id: result_id })?;
        if left.tgt != right.src {
            return Err(PresentationError::CompositionBoundary {
                left: left_id,
                right: right_id,
            });
        }
        if (result.src, result.tgt) != (left.src, right.tgt) {
            return Err(PresentationError::CompositeShape { id: result_id });
        }
        if composed.insert((left_id, right_id), result_id).is_some() {
            return Err(PresentationError::DuplicateComposite {
                left: left_id,
                right: right_id,
            });
        }
    }
    Ok(composed)
}

fn check_composed_associativity(
    composed: &BTreeMap<(u128, u128), u128>,
) -> Result<(), PresentationError> {
    let pairs: Vec<((u128, u128), u128)> = composed.iter().map(|(key, value)| (*key, *value)).collect();
    for ((f_id, g_id), fg_id) in &pairs {
        for ((g2_id, h_id), gh_id) in &pairs {
            if g_id == g2_id {
                let left = composed.get(&(*fg_id, *h_id));
                let right = composed.get(&(*f_id, *gh_id));
                if let (Some(left_id), Some(right_id)) = (left, right) {
                    if left_id != right_id {
                        return Err(PresentationError::Associativity {
                            left: *left_id,
                            right: *right_id,
                        });
                    }
                }
            }
        }
    }
    Ok(())
}

pub fn try_finite_presentation(
    identities: &[Mor],
    arrows: &[Mor],
    composites: &[(u128, u128, u128)],
) -> Result<PresentedCategory, PresentationError> {
    if identities.is_empty() && arrows.is_empty() {
        return Err(PresentationError::Empty);
    }
    let total = identities
        .len()
        .checked_add(arrows.len())
        .ok_or(PresentationError::TooManyArrows { count: usize::MAX })?;
    if total > MAX_ARROWS {
        return Err(PresentationError::TooManyArrows { count: total });
    }
    let (by_id, identity_of) = index_identities_and_arrows(identities, arrows)?;
    ensure_all_objects_have_identities(&by_id, &identity_of)?;
    let composed = index_composites(&by_id, composites)?;
    check_composed_associativity(&composed)?;
    Ok(PresentedCategory {
        identities: identities.len(),
        arrows: arrows.len(),
        composites: composites.len(),
    })
}

impl PresentedCategory {
    pub fn arrows(&self) -> usize {
        self.arrows
    }

    pub fn composites(&self) -> usize {
        self.composites
    }

    pub fn identities(&self) -> usize {
        self.identities
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod finite_presentation_tests {
    use super::*;

    fn mor(id: u128, src: u128, tgt: u128) -> Mor {
        Mor::new(MorId(id), ObjId(src), ObjId(tgt))
    }

    #[test]
    fn composes_only_along_matching_boundaries() {
        let identities = [mor(11, 1, 1), mor(22, 2, 2), mor(33, 3, 3)];
        let arrows = [mor(101, 1, 2), mor(102, 2, 3), mor(103, 1, 3)];
        let composites = [(101, 102, 103), (101, 22, 101), (11, 101, 101)];
        let witness = try_finite_presentation(&identities, &arrows, &composites);
        assert!(matches!(
            witness,
            Ok(ref presented) if presented.arrows() == 3 && presented.composites() == 3 && presented.identities() == 3
        ));
    }

    #[test]
    fn refuses_a_composite_whose_boundaries_do_not_meet() {
        let identities = [mor(11, 1, 1), mor(22, 2, 2)];
        let arrows = [mor(101, 1, 2)];
        let composites = [(101, 101, 101)];
        let wrong = try_finite_presentation(&identities, &arrows, &composites);
        assert!(matches!(
            wrong,
            Err(PresentationError::CompositionBoundary { left: 101, right: 101 })
        ));
    }
}
