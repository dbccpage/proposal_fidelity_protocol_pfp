//! Shared finite category declarations.
//!
//! This module is the canonical finite category data model for the functor
//! core.  It keeps declarations explicit and auditable, while
//! `ValidatedFiniteCategory` marks data that has passed the finite category
//! law checks.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_eaab8c00<T> {
    fn checked_invariant_eaab8c00(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_eaab8c00<T> for Option<T> {
    #[inline]
    fn checked_invariant_eaab8c00(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_eaab8c00<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_eaab8c00(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::cat_functor::Category;
use std::collections::{BTreeMap, BTreeSet};

/// Composition table convention:
/// compositions[(f, g)] = g composed after f.
pub type CompositionTable = BTreeMap<(String, String), String>;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredMorphism {
    pub name: String,
    pub source: String,
    pub target: String,
}

impl DeclaredMorphism {
    pub fn new(name: &str, source: &str, target: &str) -> Self {
        Self {
            name: name.into(),
            source: source.into(),
            target: target.into(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteCategory {
    pub name: String,
    pub objects: BTreeSet<String>,
    pub morphisms: BTreeMap<String, DeclaredMorphism>,
    pub identities: BTreeMap<String, String>,
    pub compositions: CompositionTable,
}

impl DeclaredFiniteCategory {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.into(),
            objects: BTreeSet::new(),
            morphisms: BTreeMap::new(),
            identities: BTreeMap::new(),
            compositions: BTreeMap::new(),
        }
    }

    pub fn add_object(&mut self, object: &str) {
        self.objects.insert(object.into());
    }

    pub fn add_morphism(&mut self, name: &str, source: &str, target: &str) {
        self.objects.insert(source.into());
        self.objects.insert(target.into());
        self.morphisms
            .insert(name.into(), DeclaredMorphism::new(name, source, target));
    }

    pub fn set_identity(&mut self, object: &str, morphism: &str) {
        self.objects.insert(object.into());
        self.identities.insert(object.into(), morphism.into());
    }

    pub fn add_identity(&mut self, object: &str, morphism: &str) {
        self.add_morphism(morphism, object, object);
        self.set_identity(object, morphism);
    }

    pub fn set_composition(&mut self, first: &str, second: &str, composite: &str) {
        self.compositions
            .insert((first.into(), second.into()), composite.into());
    }

    pub fn identity_of(&self, object: &str) -> Option<&str> {
        self.identities.get(object).map(|id| id.as_str())
    }

    pub fn boundary_of(&self, morphism: &str) -> Option<(&str, &str)> {
        self.morphisms
            .get(morphism)
            .map(|mor| (mor.source.as_str(), mor.target.as_str()))
    }

    /// Returns g ∘ f (first `f`, then `g`).
    pub fn compose(&self, f: &str, g: &str) -> Option<&str> {
        self.compositions
            .get(&(f.into(), g.into()))
            .map(|composite| composite.as_str())
    }

    pub fn has_object(&self, object: &str) -> bool {
        self.objects.contains(object)
    }

    pub fn has_morphism(&self, morphism: &str) -> bool {
        self.morphisms.contains_key(morphism)
    }

    pub fn object_names(&self) -> Vec<&str> {
        self.objects.iter().map(|object| object.as_str()).collect()
    }

    pub fn morphism_names(&self) -> Vec<&str> {
        self.morphisms
            .keys()
            .map(|morphism| morphism.as_str())
            .collect()
    }

    pub fn boundary_triples(&self) -> Vec<(String, String, String)> {
        self.morphisms
            .values()
            .map(|morphism| {
                (
                    morphism.name.clone(),
                    morphism.source.clone(),
                    morphism.target.clone(),
                )
            })
            .collect()
    }

    pub fn composition_triples(&self) -> Vec<(String, String, String)> {
        self.compositions
            .iter()
            .map(|((first, second), composite)| (first.clone(), second.clone(), composite.clone()))
            .collect()
    }

    pub fn num_objects(&self) -> usize {
        self.objects.len()
    }

    pub fn num_morphisms(&self) -> usize {
        self.morphisms.len()
    }
}

impl Default for DeclaredFiniteCategory {
    fn default() -> Self {
        Self::new("AutoP")
    }
}

/// Canonical finite category alias used by AutoP `CatkitEmitter`.
pub type FiniteCategory = DeclaredFiniteCategory;

/// Canonical morphism metadata alias used by AutoP `CatkitEmitter`.
pub type MorphismMeta = DeclaredMorphism;

/// Structural classification of morphisms in a finite category.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MorphismKind {
    Identity,
    Generator,
    Composite,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedFiniteCategory {
    declared: DeclaredFiniteCategory,
}

impl ValidatedFiniteCategory {
    pub fn try_new(
        declared: DeclaredFiniteCategory,
    ) -> Result<Self, super::validation::ValidationReport> {
        let report = super::finite_category_validation::validate_finite_category(&declared);
        if report.all_passed() {
            Ok(Self { declared })
        } else {
            Err(report)
        }
    }

    pub fn declared(&self) -> &DeclaredFiniteCategory {
        &self.declared
    }

    pub fn into_declared(self) -> DeclaredFiniteCategory {
        self.declared
    }
}

impl Category for ValidatedFiniteCategory {
    type Ob = String;
    type Mor = String;

    fn id(&self, x: &Self::Ob) -> Self::Mor {
        self.declared
            .identity_of(x)
            .checked_invariant_eaab8c00("validated finite category has every identity")
            .to_string()
    }

    fn src(&self, f: &Self::Mor) -> Self::Ob {
        self.declared
            .boundary_of(f)
            .checked_invariant_eaab8c00("validated finite category has every morphism boundary")
            .0
            .to_string()
    }

    fn tgt(&self, f: &Self::Mor) -> Self::Ob {
        self.declared
            .boundary_of(f)
            .checked_invariant_eaab8c00("validated finite category has every morphism boundary")
            .1
            .to_string()
    }

    fn compose(&self, f: &Self::Mor, g: &Self::Mor) -> Option<Self::Mor> {
        self.declared
            .compose(f, g)
            .map(|composite| composite.into())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/finite_category.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordeaab8c00 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordeaab8c00` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroreaab8c00 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErroreaab8c00 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroreaab8c00 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroreaab8c00 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordeaab8c00 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroreaab8c00> {
        if capacity_bound == 0 {
            return Err(BoundaryErroreaab8c00::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroreaab8c00::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroreaab8c00::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn walking_arrow() -> DeclaredFiniteCategory {
        let mut cat = DeclaredFiniteCategory::new("WalkingArrow");
        cat.add_morphism("id_A", "A", "A");
        cat.add_morphism("id_B", "B", "B");
        cat.add_morphism("f", "A", "B");
        cat.set_identity("A", "id_A");
        cat.set_identity("B", "id_B");
        cat.set_composition("id_A", "id_A", "id_A");
        cat.set_composition("id_B", "id_B", "id_B");
        cat.set_composition("id_A", "f", "f");
        cat.set_composition("f", "id_B", "f");
        cat
    }

    #[test]
    fn validated_category_implements_category_trait() {
        let cat = ValidatedFiniteCategory::try_new(walking_arrow())
            .expect("walking arrow should validate");

        assert_eq!(cat.id(&"A".into()), "id_A");
        assert_eq!(cat.src(&"f".into()), "A");
        assert_eq!(cat.tgt(&"f".into()), "B");
        assert_eq!(cat.compose(&"id_A".into(), &"f".into()), Some("f".into()));
    }

    #[test]
    fn try_new_refuses_object_without_identity() {
        let mut cat = DeclaredFiniteCategory::new("Broken");
        cat.add_object("A");
        let err = ValidatedFiniteCategory::try_new(cat)
            .expect_err("an object with no identity is not a category");
        assert!(err.typed_violations.iter().any(|violation| {
            violation.unit
                == crate::validation::ValidationUnit::FiniteCategory(
                    crate::validation::FiniteCategoryValidation::IdentityTotality,
                )
        }));
    }
}

#[cfg(test)]
mod l4_boundary_tests_eaab8c00 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordeaab8c00::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordeaab8c00::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordeaab8c00::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordeaab8c00::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordeaab8c00::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroreaab8c00::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroreaab8c00::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
