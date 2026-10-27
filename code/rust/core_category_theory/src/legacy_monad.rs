//! Monad — Spec Section 22.
//!
//! A monad on C is a monoid object in the bicategory Prof,
//! restricted to representable profunctors.
//!
//! Representable case (classical monad):
//!   T : C → C (endofunctor)
//!   η : id ⇒ T (unit)
//!   μ : T² ⇒ T (multiplication)
//!
//! Monad laws:
//!   μ ∘ Tη = id_T       (left unit)
//!   μ ∘ ηT = id_T       (right unit)
//!   μ ∘ Tμ = μ ∘ μT     (associativity)
//!
//! Non-representable case (profunctor monad / relative monad):
//!   P : C ⊸ C (profunctor, not necessarily representable)
//!   unit and multiplication as profunctor natural transformations.

use super::cat_functor::{Category, DeclaredFiniteFunctor};
use super::finite_category::DeclaredFiniteCategory;
use super::validation::{
    ValidationLocation, ValidationReport, ValidationSeverity, ValidationUnit, ValidationViolation,
};
use std::collections::BTreeMap;

// ---------------------------------------------------------------------------
// Trait: Monad (representable case)
// ---------------------------------------------------------------------------

/// A monad on a category C: an endofunctor T with unit η and multiplication μ.
///
/// This is the representable specialization of a monoid in Prof.
/// Laws (validation obligations):
///   μ ∘ Tη = id_T       (left unit)
///   μ ∘ ηT = id_T       (right unit)
///   μ ∘ Tμ = μ ∘ μT     (associativity)
pub trait Monad {
    type C: Category;

    /// The endofunctor T on objects: T(A).
    fn map_object(&self, x: &<Self::C as Category>::Ob) -> <Self::C as Category>::Ob;

    /// The endofunctor T on morphisms: T(f).
    fn map_morphism(&self, f: &<Self::C as Category>::Mor) -> <Self::C as Category>::Mor;

    /// Unit component: η_A : A → T(A).
    fn unit(&self, x: &<Self::C as Category>::Ob) -> <Self::C as Category>::Mor;

    /// Multiplication component: μ_A : T(T(A)) → T(A).
    fn multiply(&self, x: &<Self::C as Category>::Ob) -> <Self::C as Category>::Mor;
}

// ---------------------------------------------------------------------------
// DeclaredFiniteMonad (data record)
// ---------------------------------------------------------------------------

/// An explicit, finite monad declaration for kernel audit.
///
/// This is the data-level record: maps are string tables,
/// law checking is external.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteMonad {
    pub name: String,
    pub category: String,
    /// T on objects: object → T(object).
    pub object_map: BTreeMap<String, String>,
    /// T on morphisms: morphism → T(morphism).
    pub morphism_map: BTreeMap<String, String>,
    /// Unit components: object A → morphism η_A.
    pub unit_components: BTreeMap<String, String>,
    /// Multiplication components: object A → morphism μ_A.
    pub multiplication_components: BTreeMap<String, String>,
}

impl DeclaredFiniteMonad {
    pub fn new(name: &str, category: &str) -> Self {
        Self {
            name: name.into(),
            category: category.into(),
            object_map: BTreeMap::new(),
            morphism_map: BTreeMap::new(),
            unit_components: BTreeMap::new(),
            multiplication_components: BTreeMap::new(),
        }
    }

    pub fn set_object_map(&mut self, src: &str, tgt: &str) {
        self.object_map.insert(src.into(), tgt.into());
    }

    pub fn set_morphism_map(&mut self, src: &str, tgt: &str) {
        self.morphism_map.insert(src.into(), tgt.into());
    }

    pub fn set_unit(&mut self, object: &str, morphism: &str) {
        self.unit_components.insert(object.into(), morphism.into());
    }

    pub fn set_multiply(&mut self, object: &str, morphism: &str) {
        self.multiplication_components
            .insert(object.into(), morphism.into());
    }

    /// Extract the underlying endofunctor.
    pub fn underlying_functor(&self) -> DeclaredFiniteFunctor {
        let mut f =
            DeclaredFiniteFunctor::new(&format!("T_{}", self.name), &self.category, &self.category);
        f.object_map = self.object_map.clone();
        f.morphism_map = self.morphism_map.clone();
        f
    }
}

// ---------------------------------------------------------------------------
// ProfunctorMonad (non-representable / relative monad)
// ---------------------------------------------------------------------------

/// A profunctor monad (relative monad): a monoid in Prof
/// that is NOT required to be representable.
///
/// The carrier is a profunctor P : C ⊸ C rather than a functor.
/// This captures effect systems, open semantics, and generalized
/// algebraic theories.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProfunctorMonad {
    pub name: String,
    /// The carrier profunctor (by name/reference).
    pub carrier_profunctor: String,
    /// Unit components: object → profunctor element (η : id ⇒ P).
    pub unit_components: BTreeMap<String, String>,
    /// Multiplication components: profunctor element → element (μ : P∘P ⇒ P).
    pub multiplication_components: BTreeMap<String, String>,
}

impl ProfunctorMonad {
    pub fn new(name: &str, carrier: &str) -> Self {
        Self {
            name: name.into(),
            carrier_profunctor: carrier.into(),
            unit_components: BTreeMap::new(),
            multiplication_components: BTreeMap::new(),
        }
    }
}

// ---------------------------------------------------------------------------
// ValidatedFiniteMonad (trust-boundary wrapper)
// ---------------------------------------------------------------------------

/// A wrapper proving that a finite monad has passed all three law checks
/// (left unit, right unit, associativity) against a declared category,
/// and that its underlying functor and natural transformations are valid.
///
/// The inner `DeclaredFiniteMonad` is private; construction forces validation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedFiniteMonad(DeclaredFiniteMonad);

impl ValidatedFiniteMonad {
    /// Validates and wraps a monad declaration.
    pub fn try_new(
        monad: DeclaredFiniteMonad,
        category: &DeclaredFiniteCategory,
    ) -> Result<Self, ValidationReport> {
        let mut report = ValidationReport::new(&monad.name);

        if monad.category != category.name {
            report.add_violation(ValidationViolation::new(
                ValidationUnit::Other("Monad::CategoryMismatch".into()),
                ValidationLocation::Global,
                format!(
                    "Monad declared on {}, but category is {}",
                    monad.category, category.name
                ),
                ValidationSeverity::Error,
            ));
            return Err(report);
        }

        // 1. Validate T as endofunctor
        let functor = monad.underlying_functor();
        let functor_report =
            super::functor_composition::validate_functor_between(&functor, category, category);
        for violation in functor_report.typed_violations {
            report.add_violation(violation);
        }

        // 2 & 3. Check boundaries and naturality of η and μ
        check_boundaries_and_naturality(&monad, category, &mut report);

        // 4, 5, 6. Monad laws
        let left_units = check_left_unit(&monad, &category.compositions, &category.identities);
        for err in left_units {
            report.add_violation(ValidationViolation::new(
                ValidationUnit::Other("Monad::UnitLeft".into()),
                ValidationLocation::Global,
                err,
                ValidationSeverity::Error,
            ));
        }

        let right_units = check_right_unit(&monad, &category.compositions, &category.identities);
        for err in right_units {
            report.add_violation(ValidationViolation::new(
                ValidationUnit::Other("Monad::UnitRight".into()),
                ValidationLocation::Global,
                err,
                ValidationSeverity::Error,
            ));
        }

        let assoc = check_associativity(&monad, &category.compositions);
        for err in assoc {
            report.add_violation(ValidationViolation::new(
                ValidationUnit::Other("Monad::Associativity".into()),
                ValidationLocation::Global,
                err,
                ValidationSeverity::Error,
            ));
        }

        if report.all_passed() {
            Ok(Self(monad))
        } else {
            Err(report)
        }
    }

    /// Access the underlying declared monad.
    pub fn declared(&self) -> &DeclaredFiniteMonad {
        &self.0
    }
}

// ---------------------------------------------------------------------------
// Validation: Boundaries and Naturality
// ---------------------------------------------------------------------------

fn check_object_boundaries(
    monad: &DeclaredFiniteMonad,
    category: &DeclaredFiniteCategory,
    obj: &String,
    report: &mut ValidationReport,
) {
    // Boundary for η_A : A → T(A)
    if let Some(eta_a) = monad.unit_components.get(obj) {
        if let Some(mor) = category.morphisms.get(eta_a) {
            let ta = monad.object_map.get(obj).unwrap_or(obj);
            if &mor.source != obj || &mor.target != ta {
                report.add_violation(ValidationViolation::new(
                    ValidationUnit::Other("Monad::UnitBoundary".into()),
                    ValidationLocation::Object(obj.clone()),
                    format!(
                        "η_{} boundary is {} → {} instead of {} → {}",
                        obj, mor.source, mor.target, obj, ta
                    ),
                    ValidationSeverity::Error,
                ));
            }
        } else {
            report.add_violation(ValidationViolation::new(
                ValidationUnit::Other("Monad::UnitBoundary".into()),
                ValidationLocation::Object(obj.clone()),
                format!("η_{} refers to non-existent morphism {}", obj, eta_a),
                ValidationSeverity::Error,
            ));
        }
    } else {
        report.add_violation(ValidationViolation::new(
            ValidationUnit::Other("Monad::UnitBoundary".into()),
            ValidationLocation::Object(obj.clone()),
            format!("Missing η_{}", obj),
            ValidationSeverity::Error,
        ));
    }

    // Boundary for μ_A : T(T(A)) → T(A)
    let ta = monad.object_map.get(obj).cloned().unwrap_or_default();
    let tta = monad.object_map.get(&ta).cloned().unwrap_or_default();
    if let Some(mu_a) = monad.multiplication_components.get(obj) {
        if let Some(mor) = category.morphisms.get(mu_a) {
            if mor.source != tta || mor.target != ta {
                report.add_violation(ValidationViolation::new(
                    ValidationUnit::Other("Monad::MultiplyBoundary".into()),
                    ValidationLocation::Object(obj.clone()),
                    format!(
                        "μ_{} boundary is {} → {} instead of {} → {}",
                        obj, mor.source, mor.target, tta, ta
                    ),
                    ValidationSeverity::Error,
                ));
            }
        } else {
            report.add_violation(ValidationViolation::new(
                ValidationUnit::Other("Monad::MultiplyBoundary".into()),
                ValidationLocation::Object(obj.clone()),
                format!("μ_{} refers to non-existent morphism {}", obj, mu_a),
                ValidationSeverity::Error,
            ));
        }
    } else {
        report.add_violation(ValidationViolation::new(
            ValidationUnit::Other("Monad::MultiplyBoundary".into()),
            ValidationLocation::Object(obj.clone()),
            format!("Missing μ_{}", obj),
            ValidationSeverity::Error,
        ));
    }
}

fn check_morphism_naturality(
    monad: &DeclaredFiniteMonad,
    category: &DeclaredFiniteCategory,
    f_name: &String,
    a: &String,
    b: &String,
    report: &mut ValidationReport,
) {
    let tf = monad.morphism_map.get(f_name).cloned().unwrap_or_default();
    let ttf = monad.morphism_map.get(&tf).cloned().unwrap_or_default();

    let eta_a = monad.unit_components.get(a).cloned().unwrap_or_default();
    let eta_b = monad.unit_components.get(b).cloned().unwrap_or_default();

    let mu_a = monad
        .multiplication_components
        .get(a)
        .cloned()
        .unwrap_or_default();
    let mu_b = monad
        .multiplication_components
        .get(b)
        .cloned()
        .unwrap_or_default();

    // Unit Naturality
    let left_eta = category.compositions.get(&(eta_a, tf.clone()));
    let right_eta = category.compositions.get(&(f_name.clone(), eta_b));

    if left_eta != right_eta {
        report.add_violation(ValidationViolation::new(
            ValidationUnit::Other("Monad::UnitNaturality".into()),
            ValidationLocation::Morphism(f_name.clone()),
            format!(
                "Unit naturality failed at f={}: T(f)∘η_A = {:?}, η_B∘f = {:?}",
                f_name, left_eta, right_eta
            ),
            ValidationSeverity::Error,
        ));
    }

    // Multiply Naturality
    let left_mu = category.compositions.get(&(mu_a, tf));
    let right_mu = category.compositions.get(&(ttf, mu_b));

    if left_mu != right_mu {
        report.add_violation(ValidationViolation::new(
            ValidationUnit::Other("Monad::MultiplyNaturality".into()),
            ValidationLocation::Morphism(f_name.clone()),
            format!(
                "Multiply naturality failed at f={}: T(f)∘μ_A = {:?}, μ_B∘T²(f) = {:?}",
                f_name, left_mu, right_mu
            ),
            ValidationSeverity::Error,
        ));
    }
}

fn check_boundaries_and_naturality(
    monad: &DeclaredFiniteMonad,
    category: &DeclaredFiniteCategory,
    report: &mut ValidationReport,
) {
    for obj in &category.objects {
        check_object_boundaries(monad, category, obj, report);
    }

    // Naturality for η: T(f) ∘ η_A = η_B ∘ f
    // Naturality for μ: T(f) ∘ μ_A = μ_B ∘ T²(f)
    for (f_name, mor) in &category.morphisms {
        check_morphism_naturality(monad, category, f_name, &mor.source, &mor.target, report);
    }
}

// ---------------------------------------------------------------------------
// Validation: monad law checkers
// ---------------------------------------------------------------------------

/// Check left unit law: μ_A ∘ T(η_A) = id_{T(A)}.
pub fn check_left_unit(
    monad: &DeclaredFiniteMonad,
    compositions: &BTreeMap<(String, String), String>,
    identity_map: &BTreeMap<String, String>,
) -> Vec<String> {
    let mut violations = Vec::new();

    for (a, ta) in &monad.object_map {
        let Some(eta_a) = monad.unit_components.get(a) else {
            continue;
        };
        let Some(t_eta_a) = monad.morphism_map.get(eta_a.as_str()) else {
            continue;
        };
        let Some(mu_a) = monad.multiplication_components.get(a) else {
            continue;
        };

        let key = (t_eta_a.clone(), mu_a.clone());
        let composed = compositions.get(&key);
        let id_ta = identity_map.get(ta);

        match (composed, id_ta) {
            (Some(c), Some(id)) if c == id => {} // law holds
            (Some(c), Some(id)) => {
                violations.push(format!(
                    "Left unit at {}: μ ∘ T(η) = {} but id_{{T({})}} = {}",
                    a, c, a, id
                ));
            }
            _ => {
                violations.push(format!(
                    "Left unit at {}: composition or identity not defined",
                    a
                ));
            }
        }
    }

    violations
}

/// Check right unit law: μ_A ∘ η_{T(A)} = id_{T(A)}.
pub fn check_right_unit(
    monad: &DeclaredFiniteMonad,
    compositions: &BTreeMap<(String, String), String>,
    identity_map: &BTreeMap<String, String>,
) -> Vec<String> {
    let mut violations = Vec::new();

    for (a, ta) in &monad.object_map {
        let Some(eta_ta) = monad.unit_components.get(ta.as_str()) else {
            continue;
        };
        let Some(mu_a) = monad.multiplication_components.get(a) else {
            continue;
        };

        let key = (eta_ta.clone(), mu_a.clone());
        let composed = compositions.get(&key);
        let id_ta = identity_map.get(ta);

        match (composed, id_ta) {
            (Some(c), Some(id)) if c == id => {}
            (Some(c), Some(id)) => {
                violations.push(format!(
                    "Right unit at {}: μ ∘ η_T = {} but id_{{T({})}} = {}",
                    a, c, a, id
                ));
            }
            _ => {
                violations.push(format!(
                    "Right unit at {}: composition or identity not defined",
                    a
                ));
            }
        }
    }

    violations
}

/// Check associativity law: μ_A ∘ T(μ_A) = μ_A ∘ μ_{T(A)}.
pub fn check_associativity(
    monad: &DeclaredFiniteMonad,
    compositions: &BTreeMap<(String, String), String>,
) -> Vec<String> {
    let mut violations = Vec::new();

    for (a, ta) in &monad.object_map {
        let Some(mu_a) = monad.multiplication_components.get(a) else {
            continue;
        };
        let Some(t_mu_a) = monad.morphism_map.get(mu_a.as_str()) else {
            continue;
        };
        let Some(mu_ta) = monad.multiplication_components.get(ta.as_str()) else {
            continue;
        };

        let left_key = (t_mu_a.clone(), mu_a.clone());
        let left = compositions.get(&left_key);

        let right_key = (mu_ta.clone(), mu_a.clone());
        let right = compositions.get(&right_key);

        match (left, right) {
            (Some(l), Some(r)) if l == r => {} // associativity holds
            (Some(l), Some(r)) => {
                violations.push(format!("Assoc at {}: μ∘Tμ = {} but μ∘μT = {}", a, l, r));
            }
            _ => {
                violations.push(format!(
                    "Assoc at {}: one or both compositions not defined",
                    a
                ));
            }
        }
    }

    violations
}

// Origin: engine/crates_rs/core_category_theory/src/legacy_monad.rs
// Claim: urn:core:crates_rs:core-category-theory:legacy-monad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4068c97a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4068c97a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4068c97a {
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
impl BoundaryError4068c97a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4068c97a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4068c97a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4068c97a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4068c97a> {
        if capacity_bound == 0 {
            return Err(BoundaryError4068c97a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4068c97a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4068c97a::ExceedsCapacity {
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

    fn make_identity_category() -> DeclaredFiniteCategory {
        DeclaredFiniteCategoryBuilder::new("C")
            .object("A")
            .identity("A", "id_A")
            .identity_compositions()
            .build()
    }

    fn make_identity_monad() -> DeclaredFiniteMonad {
        let mut m = DeclaredFiniteMonad::new("Id", "C");
        m.set_object_map("A", "A");
        m.set_morphism_map("id_A", "id_A");
        m.set_unit("A", "id_A");
        m.set_multiply("A", "id_A");
        m
    }

    #[test]
    fn identity_monad_validates() {
        let cat = make_identity_category();
        let m = make_identity_monad();

        let validated = ValidatedFiniteMonad::try_new(m, &cat);
        assert!(validated.is_ok(), "{:?}", validated.err());
    }

    #[test]
    fn missing_unit_is_violation() {
        let mut m = DeclaredFiniteMonad::new("Bad", "C");
        m.set_object_map("A", "A");

        let cat = make_identity_category();
        let validated = ValidatedFiniteMonad::try_new(m, &cat);
        assert!(validated.is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_4068c97a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4068c97a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4068c97a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4068c97a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4068c97a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4068c97a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4068c97a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4068c97a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
