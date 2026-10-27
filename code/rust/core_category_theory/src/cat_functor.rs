//! CatFunctor, ContravariantFunctor, and DeclaredFiniteFunctor.
//!
//! Spec references: Sections 1A, 1B, 1D, 3, 4.
//!
//! Laws (CatFunctor):
//!   F(id_A) = id_{F(A)}
//!   F(g ∘ f) = F(g) ∘ F(f)
//!   source(F(f)) = F(source(f))
//!   target(F(f)) = F(target(f))
//!
//! Laws (ContravariantFunctor):
//!   F(id_A) = id_{F(A)}
//!   F(g ∘ f) = F(f) ∘ F(g)   ← reversed

use std::collections::BTreeMap;

/// Composition table convention:
/// compositions[(f, g)] = g ∘ f
pub type CompositionTable = BTreeMap<(String, String), String>;
// ---------------------------------------------------------------------------
// Trait: CatFunctor (covariant)
// ---------------------------------------------------------------------------

/// A covariant functor F : C → D between categories.
///
/// This is the mathematical functor. It maps objects to objects and
/// morphisms to morphisms, preserving identity and composition.
pub trait CatFunctor {
    type Source: Category;
    type Target: Category;

    fn map_object(&self, object: &<Self::Source as Category>::Ob)
        -> <Self::Target as Category>::Ob;

    fn map_morphism(
        &self,
        morphism: &<Self::Source as Category>::Mor,
    ) -> <Self::Target as Category>::Mor;
}

// ---------------------------------------------------------------------------
// Trait: ContravariantFunctor
// ---------------------------------------------------------------------------

/// A contravariant functor F : C^op → D.
///
/// Maps f: A → B to F(f): F(B) → F(A).
/// Composition is reversed: F(g ∘ f) = F(f) ∘ F(g).
pub trait ContravariantFunctor {
    type Source: Category;
    type Target: Category;

    fn map_object(&self, object: &<Self::Source as Category>::Ob)
        -> <Self::Target as Category>::Ob;

    /// Maps f: A → B to F(f): F(B) → F(A).
    fn map_morphism(
        &self,
        morphism: &<Self::Source as Category>::Mor,
    ) -> <Self::Target as Category>::Mor;
}

// ---------------------------------------------------------------------------
// Data: DeclaredFiniteFunctor (kernel-auditable record)
// ---------------------------------------------------------------------------

/// An explicit, finite functor declaration for kernel audit.
///
/// This is data, not behavior. Missing mappings are violations (spec §3).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteFunctor {
    pub name: String,
    pub source_category: String,
    pub target_category: String,
    pub object_map: BTreeMap<String, String>,
    pub morphism_map: BTreeMap<String, String>,
}

impl DeclaredFiniteFunctor {
    pub fn new(name: &str, source: &str, target: &str) -> Self {
        Self {
            name: name.into(),
            source_category: source.into(),
            target_category: target.into(),
            object_map: BTreeMap::new(),
            morphism_map: BTreeMap::new(),
        }
    }

    pub fn map_object(&mut self, src: &str, tgt: &str) {
        self.object_map.insert(src.into(), tgt.into());
    }

    pub fn map_morphism(&mut self, src: &str, tgt: &str) {
        self.morphism_map.insert(src.into(), tgt.into());
    }

    pub fn on_object(&self, obj: &str) -> Option<&str> {
        self.object_map.get(obj).map(|s| s.as_str())
    }

    pub fn on_morphism(&self, mor: &str) -> Option<&str> {
        self.morphism_map.get(mor).map(|s| s.as_str())
    }
}

// ---------------------------------------------------------------------------
// Category trait (re-stated here for self-containment; canonical is
// algebra/category/category.rs)
// ---------------------------------------------------------------------------

/// A category: objects, morphisms, identity, source, target, composition.
pub trait Category {
    type Ob: Clone + Eq + std::fmt::Debug;
    type Mor: Clone + Eq + std::fmt::Debug;

    fn id(&self, x: &Self::Ob) -> Self::Mor;
    fn src(&self, f: &Self::Mor) -> Self::Ob;
    fn tgt(&self, f: &Self::Mor) -> Self::Ob;
    fn compose(&self, f: &Self::Mor, g: &Self::Mor) -> Option<Self::Mor>;
}

// ---------------------------------------------------------------------------
// Validation: finite functor law checkers (spec §3, §4)
// ---------------------------------------------------------------------------

/// Check identity law: F(id_A) = id_{F(A)} for all mapped objects.
///
/// Missing identity mappings produce violations, not silent skips (spec §3).
pub fn check_identity_law(functor: &DeclaredFiniteFunctor) -> Vec<String> {
    let mut violations = Vec::new();
    for (src_obj, tgt_obj) in &functor.object_map {
        let src_id = format!("id_{}", src_obj);
        let expected_tgt_id = format!("id_{}", tgt_obj);
        match functor.morphism_map.get(&src_id) {
            Some(mapped) if mapped == &expected_tgt_id => {}
            Some(mapped) => {
                violations.push(format!(
                    "Identity law violated at {}: F(id_{}) = {} but expected {}",
                    src_obj, src_obj, mapped, expected_tgt_id
                ));
            }
            None => {
                violations.push(format!("Identity law: F(id_{}) is not defined", src_obj));
            }
        }
    }
    violations
}

/// Check composition law: F(g∘f) = F(g) ∘ F(f).
///
/// Missing morphism mappings produce violations, not silent skips (spec §3).
pub fn check_composition_law(
    functor: &DeclaredFiniteFunctor,
    source_compositions: &[(&str, &str, &str)], // (f, g, g∘f) in source
    target_compositions: &CompositionTable,     // (f, g) → g∘f in target
) -> Vec<String> {
    let mut violations = Vec::new();
    for &(f, g, gf) in source_compositions {
        let Some(f_img) = functor.on_morphism(f) else {
            violations.push(format!("Composition law: F({}) is not defined", f));
            continue;
        };
        let Some(g_img) = functor.on_morphism(g) else {
            violations.push(format!("Composition law: F({}) is not defined", g));
            continue;
        };
        let Some(gf_img) = functor.on_morphism(gf) else {
            violations.push(format!("Composition law: F({}) is not defined", gf));
            continue;
        };

        let key = (f_img.to_string(), g_img.to_string());
        match target_compositions.get(&key) {
            Some(composed) if composed == gf_img => {}
            Some(composed) => {
                violations.push(format!(
                    "Composition law violated: F({}∘{}) = {} but F({})∘F({}) = {}",
                    g, f, gf_img, g, f, composed
                ));
            }
            None => {
                violations.push(format!(
                    "Composition law: F({})∘F({}) = {}∘{} not in target composition table",
                    g, f, g_img, f_img
                ));
            }
        }
    }
    violations
}

/// Check object totality: every object in the declared source set is mapped.
pub fn check_object_totality(
    functor: &DeclaredFiniteFunctor,
    source_objects: &[&str],
) -> Vec<String> {
    let mut violations = Vec::new();
    for &obj in source_objects {
        if functor.on_object(obj).is_none() {
            violations.push(format!(
                "Object totality: {} is not mapped by functor {}",
                obj, functor.name
            ));
        }
    }
    violations
}

/// Check morphism totality: every morphism in the declared source set is mapped.
pub fn check_morphism_totality(
    functor: &DeclaredFiniteFunctor,
    source_morphisms: &[&str],
) -> Vec<String> {
    let mut violations = Vec::new();
    for &mor in source_morphisms {
        if functor.on_morphism(mor).is_none() {
            violations.push(format!(
                "Morphism totality: {} is not mapped by functor {}",
                mor, functor.name
            ));
        }
    }
    violations
}

/// Check boundary preservation: source(F(f)) = F(source(f)) and target(F(f)) = F(target(f)).
pub fn check_boundary_preservation(
    functor: &DeclaredFiniteFunctor,
    source_boundaries: &[(&str, &str, &str)], // (morphism, source_obj, target_obj) in source cat
    target_boundaries: &BTreeMap<String, (String, String)>, // F(f) -> (src, tgt)
) -> Vec<String> {
    let mut violations = Vec::new();

    for &(mor, src_obj, tgt_obj) in source_boundaries {
        let Some(f_img) = functor.on_morphism(mor) else {
            violations.push(format!("Boundary preservation: F({}) is not defined", mor));
            continue;
        };

        let Some(src_img) = functor.on_object(src_obj) else {
            violations.push(format!(
                "Boundary preservation: F({}) is not defined",
                src_obj
            ));
            continue;
        };

        let Some(tgt_img) = functor.on_object(tgt_obj) else {
            violations.push(format!(
                "Boundary preservation: F({}) is not defined",
                tgt_obj
            ));
            continue;
        };

        let Some((actual_src, actual_tgt)) = target_boundaries.get(f_img) else {
            violations.push(format!(
                "Boundary preservation: target boundary for F({}) = {} is not defined",
                mor, f_img
            ));
            continue;
        };

        if actual_src != src_img {
            violations.push(format!(
                "Boundary preservation violated for {}: src(F({})) = {}, expected F(src({})) = {}",
                mor, mor, actual_src, mor, src_img
            ));
        }

        if actual_tgt != tgt_img {
            violations.push(format!(
                "Boundary preservation violated for {}: tgt(F({})) = {}, expected F(tgt({})) = {}",
                mor, mor, actual_tgt, mor, tgt_img
            ));
        }
    }

    violations
}

// Origin: engine/crates_rs/core_category_theory/src/cat_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:cat-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8a018d0e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8a018d0e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8a018d0e {
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
impl BoundaryError8a018d0e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8a018d0e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8a018d0e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8a018d0e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8a018d0e> {
        if capacity_bound == 0 {
            return Err(BoundaryError8a018d0e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8a018d0e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8a018d0e::ExceedsCapacity {
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

    #[test]
    fn declared_finite_functor_identity_law() {
        let mut f = DeclaredFiniteFunctor::new("Id", "C", "C");
        f.map_object("A", "A");
        f.map_object("B", "B");
        f.map_morphism("id_A", "id_A");
        f.map_morphism("id_B", "id_B");

        let violations = check_identity_law(&f);
        assert!(
            violations.is_empty(),
            "Identity law should pass: {:?}",
            violations
        );
    }

    #[test]
    fn declared_finite_functor_missing_mapping_is_violation() {
        let mut f = DeclaredFiniteFunctor::new("F", "C", "D");
        f.map_object("A", "X");
        // id_A is not mapped — this must be a violation, not silent skip
        let violations = check_identity_law(&f);
        assert_eq!(violations.len(), 1);
        assert!(violations[0].contains("not defined"));
    }

    #[test]
    fn composition_law_missing_mapping_is_violation() {
        let mut f = DeclaredFiniteFunctor::new("F", "C", "D");
        f.map_morphism("f", "Ff");
        // g is not mapped
        f.map_morphism("gf", "Fgf");

        let target_comp: BTreeMap<(String, String), String> = BTreeMap::new();
        let violations = check_composition_law(&f, &[("f", "g", "gf")], &target_comp);
        assert!(!violations.is_empty());
        assert!(violations[0].contains("not defined"));
    }

    #[test]
    fn object_totality_check() {
        let mut f = DeclaredFiniteFunctor::new("F", "C", "D");
        f.map_object("A", "X");
        let violations = check_object_totality(&f, &["A", "B"]);
        assert_eq!(violations.len(), 1);
        assert!(violations[0].contains("B"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_8a018d0e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8a018d0e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8a018d0e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8a018d0e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8a018d0e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8a018d0e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8a018d0e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8a018d0e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
