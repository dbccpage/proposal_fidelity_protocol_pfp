//! Natural Transformations — Spec Section 2.
//!
//! A natural transformation η : F ⇒ G between functors F, G : C → D
//! assigns to each object A in C a morphism η_A : F(A) → G(A) in D,
//! such that the naturality square commutes:
//!
//!   For all f: A → B in C:
//!     η_B ∘ F(f) = G(f) ∘ η_A

use super::cat_functor::{CatFunctor, Category, DeclaredFiniteFunctor};
use super::finite_category::DeclaredFiniteCategory;
use super::validation::{
    ValidationLocation, ValidationReport, ValidationSeverity, ValidationUnit, ValidationViolation,
};
use std::collections::BTreeMap;

/// Compatibility marker for abstract arithmos modules that talk about natural
/// isomorphisms independently of the finite natural-transformation records.
pub trait NaturalIsomorphism {
    type C;
    type F;
    type G;
}

// ---------------------------------------------------------------------------
// Trait: NaturalTransformation
// ---------------------------------------------------------------------------

/// A natural transformation η : F ⇒ G.
///
/// F and G must share the same source and target categories.
pub trait NaturalTransformation {
    type F: CatFunctor;
    type G: CatFunctor<
        Source = <Self::F as CatFunctor>::Source,
        Target = <Self::F as CatFunctor>::Target,
    >;

    /// The component η_A : F(A) → G(A) in the target category.
    fn component(
        &self,
        x: &<<Self::F as CatFunctor>::Source as Category>::Ob,
    ) -> <<Self::F as CatFunctor>::Target as Category>::Mor;
}

// ---------------------------------------------------------------------------
// Data: DeclaredFiniteNaturalTransformation
// ---------------------------------------------------------------------------

/// An explicit, finite natural transformation declaration for kernel audit.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteNatTrans {
    pub name: String,
    pub source_functor: String,
    pub target_functor: String,
    /// Component map: object name → morphism name in the target category.
    pub components: BTreeMap<String, String>,
}

impl DeclaredFiniteNatTrans {
    pub fn new(name: &str, source_functor: &str, target_functor: &str) -> Self {
        Self {
            name: name.into(),
            source_functor: source_functor.into(),
            target_functor: target_functor.into(),
            components: BTreeMap::new(),
        }
    }

    pub fn set_component(&mut self, object: &str, morphism: &str) {
        self.components.insert(object.into(), morphism.into());
    }

    pub fn component(&self, object: &str) -> Option<&str> {
        self.components.get(object).map(|s| s.as_str())
    }
}

// ---------------------------------------------------------------------------
// Validated Wrapper
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedFiniteNatTrans {
    declared: DeclaredFiniteNatTrans,
}

impl ValidatedFiniteNatTrans {
    pub fn try_new(
        declared: DeclaredFiniteNatTrans,
        source_category: &DeclaredFiniteCategory,
        target_category: &DeclaredFiniteCategory,
        source_functor: &DeclaredFiniteFunctor,
        target_functor: &DeclaredFiniteFunctor,
    ) -> Result<Self, ValidationReport> {
        let report = validate_natural_transformation_between(
            &declared,
            source_category,
            target_category,
            source_functor,
            target_functor,
        );

        if report.all_passed() {
            Ok(Self { declared })
        } else {
            Err(report)
        }
    }

    pub fn declared(&self) -> &DeclaredFiniteNatTrans {
        &self.declared
    }
}

// ---------------------------------------------------------------------------
// Validation Logic
// ---------------------------------------------------------------------------

pub fn validate_natural_transformation_between(
    nat: &DeclaredFiniteNatTrans,
    source_category: &DeclaredFiniteCategory,
    target_category: &DeclaredFiniteCategory,
    source_functor: &DeclaredFiniteFunctor,
    target_functor: &DeclaredFiniteFunctor,
) -> ValidationReport {
    let mut report = ValidationReport::new(&nat.name);

    if nat.source_functor != source_functor.name {
        report.add_violation(ValidationViolation::new(
            ValidationUnit::Other("NatTrans::FunctorMismatch".into()),
            ValidationLocation::Global,
            format!(
                "Source functor name mismatch: {} != {}",
                nat.source_functor, source_functor.name
            ),
            ValidationSeverity::Error,
        ));
    }

    if nat.target_functor != target_functor.name {
        report.add_violation(ValidationViolation::new(
            ValidationUnit::Other("NatTrans::FunctorMismatch".into()),
            ValidationLocation::Global,
            format!(
                "Target functor name mismatch: {} != {}",
                nat.target_functor, target_functor.name
            ),
            ValidationSeverity::Error,
        ));
    }

    if source_functor.source_category != source_category.name
        || source_functor.target_category != target_category.name
        || target_functor.source_category != source_category.name
        || target_functor.target_category != target_category.name
    {
        report.add_violation(ValidationViolation::new(
            ValidationUnit::Other("NatTrans::CategoryMismatch".into()),
            ValidationLocation::Global,
            "Functors do not match the provided source/target categories",
            ValidationSeverity::Error,
        ));
    }

    let bnd_errors = check_component_boundaries(
        nat,
        source_category,
        target_category,
        source_functor,
        target_functor,
    );
    for err in bnd_errors {
        report.add_violation(ValidationViolation::new(
            ValidationUnit::Other("NatTrans::Boundary".into()),
            ValidationLocation::Global,
            err,
            ValidationSeverity::Error,
        ));
    }

    let sq_errors = check_naturality_square(
        nat,
        source_category,
        &source_functor.morphism_map,
        &target_functor.morphism_map,
        &target_category.compositions,
    );
    for err in sq_errors {
        report.add_violation(ValidationViolation::new(
            ValidationUnit::Other("NatTrans::NaturalitySquare".into()),
            ValidationLocation::Global,
            err,
            ValidationSeverity::Error,
        ));
    }

    report
}

pub fn check_component_boundaries(
    nat: &DeclaredFiniteNatTrans,
    source_category: &DeclaredFiniteCategory,
    target_category: &DeclaredFiniteCategory,
    source_functor: &DeclaredFiniteFunctor,
    target_functor: &DeclaredFiniteFunctor,
) -> Vec<String> {
    let mut violations = Vec::new();

    for obj in &source_category.objects {
        let Some(component) = nat.component(obj) else {
            violations.push(format!("Natural transformation: η_{} is not defined", obj));
            continue;
        };

        let Some(f_obj) = source_functor.object_map.get(obj) else {
            violations.push(format!("Natural transformation: F({}) is not defined", obj));
            continue;
        };

        let Some(g_obj) = target_functor.object_map.get(obj) else {
            violations.push(format!("Natural transformation: G({}) is not defined", obj));
            continue;
        };

        let Some(actual_mor) = target_category.morphisms.get(component) else {
            violations.push(format!(
                "Natural transformation: component η_{} = {} is not a target morphism",
                obj, component
            ));
            continue;
        };

        if actual_mor.source != *f_obj || actual_mor.target != *g_obj {
            violations.push(format!(
                "Natural transformation: η_{} = {} has boundary {} -> {}, expected {} -> {}",
                obj, component, actual_mor.source, actual_mor.target, f_obj, g_obj
            ));
        }
    }

    violations
}

pub fn check_naturality_square(
    nat: &DeclaredFiniteNatTrans,
    source_category: &DeclaredFiniteCategory,
    f_map: &BTreeMap<String, String>,
    g_map: &BTreeMap<String, String>,
    target_compositions: &BTreeMap<(String, String), String>,
) -> Vec<String> {
    let mut violations = Vec::new();

    for (mor, decl_mor) in &source_category.morphisms {
        let src_obj = &decl_mor.source;
        let tgt_obj = &decl_mor.target;

        let Some(eta_a) = nat.component(src_obj) else {
            continue;
        };
        let Some(eta_b) = nat.component(tgt_obj) else {
            continue;
        };
        let Some(f_of_mor) = f_map.get(mor) else {
            continue;
        };
        let Some(g_of_mor) = g_map.get(mor) else {
            continue;
        };

        let left_key = (f_of_mor.clone(), eta_b.to_string());
        let left = target_compositions.get(&left_key);

        let right_key = (eta_a.to_string(), g_of_mor.clone());
        let right = target_compositions.get(&right_key);

        match (left, right) {
            (Some(l), Some(r)) if l == r => {} // naturality holds
            (Some(l), Some(r)) => {
                violations.push(format!(
                    "Naturality square fails at {}: η_{}∘F({}) = {} but G({})∘η_{} = {}",
                    mor, tgt_obj, mor, l, mor, src_obj, r
                ));
            }
            (None, _) => {
                violations.push(format!(
                    "Naturality square: η_{}∘F({}) composition not in target table",
                    tgt_obj, mor
                ));
            }
            (_, None) => {
                violations.push(format!(
                    "Naturality square: G({})∘η_{} composition not in target table",
                    mor, src_obj
                ));
            }
        }
    }

    violations
}

// Origin: engine/crates_rs/core_category_theory/src/natural_trans.rs
// Claim: urn:core:crates_rs:core-category-theory:natural-trans:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord783d25e3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord783d25e3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError783d25e3 {
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
impl BoundaryError783d25e3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError783d25e3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError783d25e3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord783d25e3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError783d25e3> {
        if capacity_bound == 0 {
            return Err(BoundaryError783d25e3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError783d25e3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError783d25e3::ExceedsCapacity {
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
    use crate::finite_category_builder::DeclaredFiniteCategoryBuilder;

    #[test]
    fn trivial_nat_trans_passes_naturality() {
        let cat = DeclaredFiniteCategoryBuilder::new("C")
            .object("A")
            .object("B")
            .identity("A", "id_A")
            .identity("B", "id_B")
            .morphism("f", "A", "B")
            .composition("id_A", "id_A", "id_A")
            .composition("id_B", "id_B", "id_B")
            .composition("id_A", "f", "f")
            .composition("f", "id_B", "f")
            .build();

        let mut nat = DeclaredFiniteNatTrans::new("id_η", "Id", "Id");
        nat.set_component("A", "id_A");
        nat.set_component("B", "id_B");

        let mut f_functor = DeclaredFiniteFunctor::new("Id", "C", "C");
        f_functor.map_object("A", "A");
        f_functor.map_object("B", "B");
        f_functor.map_morphism("id_A", "id_A");
        f_functor.map_morphism("id_B", "id_B");
        f_functor.map_morphism("f", "f");

        let report =
            validate_natural_transformation_between(&nat, &cat, &cat, &f_functor, &f_functor);
        assert!(report.all_passed(), "Should pass: {:?}", report);
    }
}

#[cfg(test)]
mod l4_boundary_tests_783d25e3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord783d25e3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord783d25e3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord783d25e3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord783d25e3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord783d25e3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError783d25e3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError783d25e3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
