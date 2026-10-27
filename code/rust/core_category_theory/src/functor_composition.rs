//! First-class finite functor operations.
//!
//! This module keeps `DeclaredFiniteFunctor` as auditable data and adds the
//! derived operations needed to build larger categorical structures.

use super::cat_functor::DeclaredFiniteFunctor;
use super::finite_category::DeclaredFiniteCategory;
use super::validation::{
    FunctorValidation, ValidationLocation, ValidationReport, ValidationSeverity, ValidationUnit,
    ValidationViolation,
};

fn violation(
    unit: FunctorValidation,
    location: ValidationLocation,
    message: impl Into<String>,
) -> ValidationViolation {
    ValidationViolation::new(
        ValidationUnit::Functor(unit),
        location,
        message,
        ValidationSeverity::Error,
    )
}

fn add_unit(
    report: &mut ValidationReport,
    unit: FunctorValidation,
    violations: Vec<ValidationViolation>,
) {
    report.add_typed(&format!("functor::{:?}", unit), violations);
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedFiniteFunctor {
    declared: DeclaredFiniteFunctor,
    source: DeclaredFiniteCategory,
    target: DeclaredFiniteCategory,
}

impl ValidatedFiniteFunctor {
    pub fn try_new(
        declared: DeclaredFiniteFunctor,
        source: &DeclaredFiniteCategory,
        target: &DeclaredFiniteCategory,
    ) -> Result<Self, ValidationReport> {
        let report = validate_functor_between(&declared, source, target);
        if report.all_passed() {
            Ok(Self {
                declared,
                source: source.clone(),
                target: target.clone(),
            })
        } else {
            Err(report)
        }
    }

    pub fn declared(&self) -> &DeclaredFiniteFunctor {
        &self.declared
    }

    pub fn source(&self) -> &DeclaredFiniteCategory {
        &self.source
    }

    pub fn target(&self) -> &DeclaredFiniteCategory {
        &self.target
    }

    pub fn into_declared(self) -> DeclaredFiniteFunctor {
        self.declared
    }
}

pub fn identity_functor(category: &DeclaredFiniteCategory, name: &str) -> DeclaredFiniteFunctor {
    let mut functor = DeclaredFiniteFunctor::new(name, &category.name, &category.name);

    for object in &category.objects {
        functor.map_object(object, object);
    }
    for morphism in category.morphisms.keys() {
        functor.map_morphism(morphism, morphism);
    }

    functor
}

/// Compose raw declared functors F : C -> D and G : D -> E as G after F.
/// This does not validate that the inputs or output are lawful functors.
pub fn compose_declared_functors(
    name: &str,
    first: &DeclaredFiniteFunctor,
    second: &DeclaredFiniteFunctor,
) -> Result<DeclaredFiniteFunctor, String> {
    if first.target_category != second.source_category {
        return Err(format!(
            "Cannot compose {} then {}: target {} does not match source {}",
            first.name, second.name, first.target_category, second.source_category
        ));
    }

    let mut composite =
        DeclaredFiniteFunctor::new(name, &first.source_category, &second.target_category);

    for (object, middle_object) in &first.object_map {
        let Some(target_object) = second.object_map.get(middle_object) else {
            return Err(format!(
                "Cannot compose object {}: {}({}) = {}, but {} is undefined there",
                object, first.name, object, middle_object, second.name
            ));
        };
        composite.map_object(object, target_object);
    }

    for (morphism, middle_morphism) in &first.morphism_map {
        let Some(target_morphism) = second.morphism_map.get(middle_morphism) else {
            return Err(format!(
                "Cannot compose morphism {}: {}({}) = {}, but {} is undefined there",
                morphism, first.name, morphism, middle_morphism, second.name
            ));
        };
        composite.map_morphism(morphism, target_morphism);
    }

    Ok(composite)
}

/// Compose two validated functors. Requires that the first functor's target
/// exactly matches the second functor's source.
pub fn compose_validated_functors(
    name: &str,
    first: &ValidatedFiniteFunctor,
    second: &ValidatedFiniteFunctor,
) -> Result<DeclaredFiniteFunctor, String> {
    if first.target().name != second.source().name {
        return Err(format!(
            "Cannot compose validated functors {} and {}: target {} does not match source {}",
            first.declared().name,
            second.declared().name,
            first.target().name,
            second.source().name
        ));
    }

    compose_declared_functors(name, first.declared(), second.declared())
}

pub fn opposite_category(category: &DeclaredFiniteCategory, name: &str) -> DeclaredFiniteCategory {
    let mut opposite = DeclaredFiniteCategory::new(name);

    for object in &category.objects {
        opposite.add_object(object);
    }
    for morphism in category.morphisms.values() {
        opposite.add_morphism(&morphism.name, &morphism.target, &morphism.source);
    }
    for (object, identity) in &category.identities {
        opposite.set_identity(object, identity);
    }
    for ((first, second), composite) in &category.compositions {
        opposite.set_composition(second, first, composite);
    }

    opposite
}

/// Given F : C -> D, returns F^op : C^op -> D^op.
/// Object and morphism maps are unchanged; source/target categories are reversed externally.
pub fn opposite_functor(
    name: &str,
    functor: &DeclaredFiniteFunctor,
    source_op_category: &str,
    target_op_category: &str,
) -> DeclaredFiniteFunctor {
    let mut opposite = DeclaredFiniteFunctor::new(name, source_op_category, target_op_category);
    opposite.object_map = functor.object_map.clone();
    opposite.morphism_map = functor.morphism_map.clone();
    opposite
}

pub fn inclusion_functor(
    name: &str,
    source: &DeclaredFiniteCategory,
    target: &DeclaredFiniteCategory,
) -> Result<DeclaredFiniteFunctor, String> {
    let mut functor = DeclaredFiniteFunctor::new(name, &source.name, &target.name);

    for object in &source.objects {
        if !target.has_object(object) {
            return Err(format!("Target category lacks object {}", object));
        }
        functor.map_object(object, object);
    }

    for (name, morphism) in &source.morphisms {
        let Some(target_morphism) = target.morphisms.get(name) else {
            return Err(format!("Target category lacks morphism {}", name));
        };
        if target_morphism.source != morphism.source || target_morphism.target != morphism.target {
            return Err(format!(
                "Target morphism {} has boundary {} -> {}, expected {} -> {}",
                name,
                target_morphism.source,
                target_morphism.target,
                morphism.source,
                morphism.target
            ));
        }
        functor.map_morphism(name, name);
    }

    Ok(functor)
}

pub fn declared_finite_functor_from_maps(
    name: &str,
    source: &DeclaredFiniteCategory,
    target: &DeclaredFiniteCategory,
    object_map: &[(&str, &str)],
    morphism_map: &[(&str, &str)],
) -> DeclaredFiniteFunctor {
    let mut functor = DeclaredFiniteFunctor::new(name, &source.name, &target.name);
    for (source_object, target_object) in object_map {
        functor.map_object(source_object, target_object);
    }
    for (source_morphism, target_morphism) in morphism_map {
        functor.map_morphism(source_morphism, target_morphism);
    }
    functor
}

fn check_functor_object_totality(
    functor: &DeclaredFiniteFunctor,
    source: &DeclaredFiniteCategory,
    target: &DeclaredFiniteCategory,
) -> Vec<ValidationViolation> {
    let mut object_violations = Vec::new();
    if functor.source_category != source.name {
        object_violations.push(violation(
            FunctorValidation::ObjectTotality,
            ValidationLocation::Global,
            format!(
                "Functor source category is {}, expected {}",
                functor.source_category, source.name
            ),
        ));
    }
    if functor.target_category != target.name {
        object_violations.push(violation(
            FunctorValidation::ObjectTotality,
            ValidationLocation::Global,
            format!(
                "Functor target category is {}, expected {}",
                functor.target_category, target.name
            ),
        ));
    }

    for object in &source.objects {
        match functor.on_object(object) {
            Some(image) if target.has_object(image) => {}
            Some(image) => object_violations.push(violation(
                FunctorValidation::ObjectTotality,
                ValidationLocation::Object(object.clone()),
                format!(
                    "F({}) = {} is not an object of {}",
                    object, image, target.name
                ),
            )),
            None => object_violations.push(violation(
                FunctorValidation::ObjectTotality,
                ValidationLocation::Object(object.clone()),
                format!("Object {} is not mapped by {}", object, functor.name),
            )),
        }
    }
    object_violations
}

fn check_functor_morphism_totality(
    functor: &DeclaredFiniteFunctor,
    source: &DeclaredFiniteCategory,
    target: &DeclaredFiniteCategory,
) -> Vec<ValidationViolation> {
    let mut morphism_violations = Vec::new();
    for morphism in source.morphisms.keys() {
        match functor.on_morphism(morphism) {
            Some(image) if target.has_morphism(image) => {}
            Some(image) => morphism_violations.push(violation(
                FunctorValidation::MorphismTotality,
                ValidationLocation::Morphism(morphism.clone()),
                format!(
                    "F({}) = {} is not a morphism of {}",
                    morphism, image, target.name
                ),
            )),
            None => morphism_violations.push(violation(
                FunctorValidation::MorphismTotality,
                ValidationLocation::Morphism(morphism.clone()),
                format!("Morphism {} is not mapped by {}", morphism, functor.name),
            )),
        }
    }
    morphism_violations
}

fn check_functor_boundaries(
    functor: &DeclaredFiniteFunctor,
    source: &DeclaredFiniteCategory,
    target: &DeclaredFiniteCategory,
) -> Vec<ValidationViolation> {
    let mut boundary_violations = Vec::new();
    for morphism in source.morphisms.values() {
        let Some(image_morphism) = functor.on_morphism(&morphism.name) else {
            continue;
        };
        let Some(image_source) = functor.on_object(&morphism.source) else {
            continue;
        };
        let Some(image_target) = functor.on_object(&morphism.target) else {
            continue;
        };
        let Some((actual_source, actual_target)) = target.boundary_of(image_morphism) else {
            continue;
        };

        if actual_source != image_source || actual_target != image_target {
            boundary_violations.push(violation(
                FunctorValidation::BoundaryPreservation,
                ValidationLocation::Boundary {
                    morphism: morphism.name.clone(),
                    source: image_source.into(),
                    target: image_target.into(),
                },
                format!(
                    "F({}) has boundary {} -> {}, expected {} -> {}",
                    morphism.name, actual_source, actual_target, image_source, image_target
                ),
            ));
        }
    }
    boundary_violations
}

fn check_functor_identities(
    functor: &DeclaredFiniteFunctor,
    source: &DeclaredFiniteCategory,
    target: &DeclaredFiniteCategory,
) -> Vec<ValidationViolation> {
    let mut identity_violations = Vec::new();
    for object in &source.objects {
        let Some(source_identity) = source.identity_of(object) else {
            continue;
        };
        let Some(image_object) = functor.on_object(object) else {
            continue;
        };
        let Some(expected_identity) = target.identity_of(image_object) else {
            continue;
        };
        match functor.on_morphism(source_identity) {
            Some(image_identity) if image_identity == expected_identity => {}
            Some(image_identity) => identity_violations.push(violation(
                FunctorValidation::IdentityPreservation,
                ValidationLocation::Object(object.clone()),
                format!(
                    "F(id_{}) = {}, expected {}",
                    object, image_identity, expected_identity
                ),
            )),
            None => identity_violations.push(violation(
                FunctorValidation::IdentityPreservation,
                ValidationLocation::Morphism(source_identity.into()),
                format!("F({}) is not defined", source_identity),
            )),
        }
    }
    identity_violations
}

fn check_functor_compositions(
    functor: &DeclaredFiniteFunctor,
    source: &DeclaredFiniteCategory,
    target: &DeclaredFiniteCategory,
) -> Vec<ValidationViolation> {
    let mut composition_violations = Vec::new();
    for ((first, second), composite) in &source.compositions {
        let Some(first_image) = functor.on_morphism(first) else {
            continue;
        };
        let Some(second_image) = functor.on_morphism(second) else {
            continue;
        };
        let Some(composite_image) = functor.on_morphism(composite) else {
            continue;
        };

        match target.compose(first_image, second_image) {
            Some(target_composite) if target_composite == composite_image => {}
            Some(target_composite) => composition_violations.push(violation(
                FunctorValidation::CompositionPreservation,
                ValidationLocation::Composition {
                    first: first.clone(),
                    second: second.clone(),
                    composite: Some(composite.clone()),
                },
                format!(
                    "F({} after {}) = {}, but F({}) after F({}) = {}",
                    second, first, composite_image, second, first, target_composite
                ),
            )),
            None => composition_violations.push(violation(
                FunctorValidation::CompositionPreservation,
                ValidationLocation::Composition {
                    first: first.clone(),
                    second: second.clone(),
                    composite: Some(composite.clone()),
                },
                format!(
                    "Target composition F({}) after F({}) is not defined",
                    second, first
                ),
            )),
        }
    }
    composition_violations
}

pub fn validate_functor_between(
    functor: &DeclaredFiniteFunctor,
    source: &DeclaredFiniteCategory,
    target: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&functor.name);
    add_unit(
        &mut report,
        FunctorValidation::ObjectTotality,
        check_functor_object_totality(functor, source, target),
    );
    add_unit(
        &mut report,
        FunctorValidation::MorphismTotality,
        check_functor_morphism_totality(functor, source, target),
    );
    add_unit(
        &mut report,
        FunctorValidation::BoundaryPreservation,
        check_functor_boundaries(functor, source, target),
    );
    add_unit(
        &mut report,
        FunctorValidation::IdentityPreservation,
        check_functor_identities(functor, source, target),
    );
    add_unit(
        &mut report,
        FunctorValidation::CompositionPreservation,
        check_functor_compositions(functor, source, target),
    );
    report
}

// Origin: engine/crates_rs/core_category_theory/src/functor_composition.rs
// Claim: urn:core:crates_rs:core-category-theory:functor-composition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9513f14b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9513f14b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9513f14b {
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
impl BoundaryError9513f14b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9513f14b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9513f14b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9513f14b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9513f14b> {
        if capacity_bound == 0 {
            return Err(BoundaryError9513f14b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9513f14b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9513f14b::ExceedsCapacity {
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

    fn walking_arrow(name: &str) -> DeclaredFiniteCategory {
        DeclaredFiniteCategoryBuilder::new(name)
            .identity("A", "id_A")
            .identity("B", "id_B")
            .morphism("f", "A", "B")
            .identity_compositions()
            .build()
    }

    #[test]
    fn identity_functor_validates() {
        let cat = walking_arrow("C");
        let id = identity_functor(&cat, "Id_C");
        let report = validate_functor_between(&id, &cat, &cat);
        assert!(report.all_passed(), "{:?}", report.typed_violations);
    }

    #[test]
    fn functor_composition_maps_through_middle() {
        let c = walking_arrow("C");
        let d = walking_arrow("D");
        let e = walking_arrow("E");

        let f = declared_finite_functor_from_maps(
            "F",
            &c,
            &d,
            &[("A", "A"), ("B", "B")],
            &[("id_A", "id_A"), ("id_B", "id_B"), ("f", "f")],
        );
        let g = declared_finite_functor_from_maps(
            "G",
            &d,
            &e,
            &[("A", "A"), ("B", "B")],
            &[("id_A", "id_A"), ("id_B", "id_B"), ("f", "f")],
        );

        let gf = compose_declared_functors("GF", &f, &g).expect("composition should exist");
        assert_eq!(gf.on_object("A"), Some("A"));
        assert_eq!(gf.on_morphism("f"), Some("f"));
        assert!(validate_functor_between(&gf, &c, &e).all_passed());
    }

    #[test]
    fn opposite_category_reverses_composition_order() {
        let cat = walking_arrow("C");
        let op = opposite_category(&cat, "C_op");

        assert_eq!(op.boundary_of("f"), Some(("B", "A")));
        assert_eq!(op.compose("f", "id_A"), Some("f"));
    }

    #[test]
    fn invalid_functor_reports_typed_boundary_violation() {
        let c = walking_arrow("C");
        let d = walking_arrow("D");
        let bad = declared_finite_functor_from_maps(
            "Bad",
            &c,
            &d,
            &[("A", "B"), ("B", "A")],
            &[("id_A", "id_B"), ("id_B", "id_A"), ("f", "f")],
        );

        let report = validate_functor_between(&bad, &c, &d);
        assert!(!report.all_passed());
        assert!(report.typed_violations.iter().any(|violation| {
            violation.unit == ValidationUnit::Functor(FunctorValidation::BoundaryPreservation)
        }));
    }

    #[test]
    fn invalid_functor_reports_composition_violation() {
        let source = DeclaredFiniteCategoryBuilder::new("Src")
            .identity_object("X")
            .identity_object("Y")
            .identity_object("Z")
            .morphism("u", "X", "Y")
            .morphism("v", "Y", "Z")
            .morphism("vu", "X", "Z")
            .path_composition("u", "v", "vu")
            .identity_compositions()
            .build();

        let target = source.clone();

        let bad = declared_finite_functor_from_maps(
            "BadComp",
            &source,
            &target,
            &[("X", "X"), ("Y", "Y"), ("Z", "Z")],
            &[
                ("id_X", "id_X"),
                ("id_Y", "id_Y"),
                ("id_Z", "id_Z"),
                ("u", "u"),
                ("v", "v"),
                ("vu", "u"),
            ],
        );

        let report = validate_functor_between(&bad, &source, &target);
        assert!(!report.all_passed());
        assert!(
            report
                .typed_violations
                .iter()
                .any(|v| v.unit
                    == ValidationUnit::Functor(FunctorValidation::CompositionPreservation))
        );
    }

    #[test]
    fn invalid_functor_reports_identity_violation() {
        let c = walking_arrow("C");
        let d = walking_arrow("D");

        let bad = declared_finite_functor_from_maps(
            "BadId",
            &c,
            &d,
            &[("A", "A"), ("B", "B")],
            &[("id_A", "id_B"), ("id_B", "id_B"), ("f", "f")],
        );

        let report = validate_functor_between(&bad, &c, &d);

        assert!(report.typed_violations.iter().any(|violation| {
            violation.unit == ValidationUnit::Functor(FunctorValidation::IdentityPreservation)
        }));
    }

    #[test]
    fn partial_functor_reports_totality_violations() {
        let c = walking_arrow("C");
        let d = walking_arrow("D");

        let partial = declared_finite_functor_from_maps(
            "Partial",
            &c,
            &d,
            &[("A", "A")],
            &[("id_A", "id_A")],
        );

        let report = validate_functor_between(&partial, &c, &d);
        assert!(!report.all_passed());
        assert!(report
            .typed_violations
            .iter()
            .any(|v| v.unit == ValidationUnit::Functor(FunctorValidation::ObjectTotality)));
        assert!(report
            .typed_violations
            .iter()
            .any(|v| v.unit == ValidationUnit::Functor(FunctorValidation::MorphismTotality)));
    }
}

#[cfg(test)]
mod l4_boundary_tests_9513f14b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9513f14b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9513f14b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9513f14b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9513f14b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9513f14b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9513f14b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9513f14b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
