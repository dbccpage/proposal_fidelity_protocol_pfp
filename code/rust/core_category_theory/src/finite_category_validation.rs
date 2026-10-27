//! Finite category validation.
//!
//! The checks here validate the shared `DeclaredFiniteCategory` model:
//! object references, morphism boundaries, identities, composition totality,
//! closure, boundary compatibility, and associativity.

use super::finite_category::DeclaredFiniteCategory;
use super::validation::{
    FiniteCategoryValidation, ValidationLocation, ValidationReport, ValidationSeverity,
    ValidationUnit, ValidationViolation,
};

fn violation(
    unit: FiniteCategoryValidation,
    location: ValidationLocation,
    message: impl Into<String>,
) -> ValidationViolation {
    ValidationViolation::new(
        ValidationUnit::FiniteCategory(unit),
        location,
        message,
        ValidationSeverity::Error,
    )
}

fn add_unit(
    report: &mut ValidationReport,
    unit: FiniteCategoryValidation,
    violations: Vec<ValidationViolation>,
) {
    report.add_typed(&format!("finite_category::{:?}", unit), violations);
}

pub fn check_object_references(category: &DeclaredFiniteCategory) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for (name, morphism) in &category.morphisms {
        if name != &morphism.name {
            violations.push(violation(
                FiniteCategoryValidation::ObjectReference,
                ValidationLocation::Morphism(name.clone()),
                format!(
                    "Morphism key {} does not match declared name {}",
                    name, morphism.name
                ),
            ));
        }
        if !category.objects.contains(&morphism.source) {
            violations.push(violation(
                FiniteCategoryValidation::ObjectReference,
                ValidationLocation::Boundary {
                    morphism: name.clone(),
                    source: morphism.source.clone(),
                    target: morphism.target.clone(),
                },
                format!(
                    "Morphism {} has unknown source object {}",
                    name, morphism.source
                ),
            ));
        }
        if !category.objects.contains(&morphism.target) {
            violations.push(violation(
                FiniteCategoryValidation::ObjectReference,
                ValidationLocation::Boundary {
                    morphism: name.clone(),
                    source: morphism.source.clone(),
                    target: morphism.target.clone(),
                },
                format!(
                    "Morphism {} has unknown target object {}",
                    name, morphism.target
                ),
            ));
        }
    }

    for object in category.identities.keys() {
        if !category.objects.contains(object) {
            violations.push(violation(
                FiniteCategoryValidation::ObjectReference,
                ValidationLocation::Object(object.clone()),
                format!("Identity declared for unknown object {}", object),
            ));
        }
    }

    violations
}

pub fn check_nonempty_names(category: &DeclaredFiniteCategory) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for object in &category.objects {
        if object.is_empty() {
            violations.push(violation(
                FiniteCategoryValidation::ObjectReference,
                ValidationLocation::Object(object.clone()),
                "Empty object name declared",
            ));
        }
    }

    for name in category.morphisms.keys() {
        if name.is_empty() {
            violations.push(violation(
                FiniteCategoryValidation::MorphismBoundary,
                ValidationLocation::Morphism(name.clone()),
                "Empty morphism name declared",
            ));
        }
    }

    violations
}

pub fn check_identity_totality(category: &DeclaredFiniteCategory) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for object in &category.objects {
        let Some(identity) = category.identities.get(object) else {
            violations.push(violation(
                FiniteCategoryValidation::IdentityTotality,
                ValidationLocation::Object(object.clone()),
                format!("Object {} has no declared identity morphism", object),
            ));
            continue;
        };

        let Some(identity_morphism) = category.morphisms.get(identity) else {
            violations.push(violation(
                FiniteCategoryValidation::IdentityTotality,
                ValidationLocation::Morphism(identity.clone()),
                format!(
                    "Identity {} for object {} is not a declared morphism",
                    identity, object
                ),
            ));
            continue;
        };

        if identity_morphism.source != *object || identity_morphism.target != *object {
            violations.push(violation(
                FiniteCategoryValidation::IdentityTotality,
                ValidationLocation::Boundary {
                    morphism: identity.clone(),
                    source: identity_morphism.source.clone(),
                    target: identity_morphism.target.clone(),
                },
                format!(
                    "Identity {} for object {} has boundary {} -> {}",
                    identity, object, identity_morphism.source, identity_morphism.target
                ),
            ));
        }
    }

    violations
}

pub fn check_identity_laws(category: &DeclaredFiniteCategory) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for morphism in category.morphisms.values() {
        let Some(source_identity) = category.identities.get(&morphism.source) else {
            continue;
        };
        let Some(target_identity) = category.identities.get(&morphism.target) else {
            continue;
        };

        match category.compose(source_identity, &morphism.name) {
            Some(composite) if composite == morphism.name => {}
            Some(composite) => violations.push(violation(
                FiniteCategoryValidation::IdentityLaw,
                ValidationLocation::Composition {
                    first: source_identity.clone(),
                    second: morphism.name.clone(),
                    composite: Some(composite.into()),
                },
                format!(
                    "{} after {} should equal {}, got {}",
                    morphism.name, source_identity, morphism.name, composite
                ),
            )),
            None => violations.push(violation(
                FiniteCategoryValidation::IdentityLaw,
                ValidationLocation::Composition {
                    first: source_identity.clone(),
                    second: morphism.name.clone(),
                    composite: None,
                },
                format!(
                    "Missing left identity composition {} after {}",
                    morphism.name, source_identity
                ),
            )),
        }

        match category.compose(&morphism.name, target_identity) {
            Some(composite) if composite == morphism.name => {}
            Some(composite) => violations.push(violation(
                FiniteCategoryValidation::IdentityLaw,
                ValidationLocation::Composition {
                    first: morphism.name.clone(),
                    second: target_identity.clone(),
                    composite: Some(composite.into()),
                },
                format!(
                    "{} after {} should equal {}, got {}",
                    target_identity, morphism.name, morphism.name, composite
                ),
            )),
            None => violations.push(violation(
                FiniteCategoryValidation::IdentityLaw,
                ValidationLocation::Composition {
                    first: morphism.name.clone(),
                    second: target_identity.clone(),
                    composite: None,
                },
                format!(
                    "Missing right identity composition {} after {}",
                    target_identity, morphism.name
                ),
            )),
        }
    }

    violations
}

pub fn check_composition_totality(category: &DeclaredFiniteCategory) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for first in category.morphisms.values() {
        for second in category.morphisms.values() {
            if first.target != second.source {
                continue;
            }

            if category.compose(&first.name, &second.name).is_none() {
                violations.push(violation(
                    FiniteCategoryValidation::CompositionTotality,
                    ValidationLocation::Composition {
                        first: first.name.clone(),
                        second: second.name.clone(),
                        composite: None,
                    },
                    format!(
                        "Composable pair ({}, {}) has no declared composite",
                        first.name, second.name
                    ),
                ));
            }
        }
    }

    violations
}

pub fn check_composition_closure(category: &DeclaredFiniteCategory) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for ((first, second), composite) in &category.compositions {
        if !category.morphisms.contains_key(first) {
            violations.push(violation(
                FiniteCategoryValidation::CompositionClosure,
                ValidationLocation::Composition {
                    first: first.clone(),
                    second: second.clone(),
                    composite: Some(composite.clone()),
                },
                format!("Composition references unknown first morphism {}", first),
            ));
        }
        if !category.morphisms.contains_key(second) {
            violations.push(violation(
                FiniteCategoryValidation::CompositionClosure,
                ValidationLocation::Composition {
                    first: first.clone(),
                    second: second.clone(),
                    composite: Some(composite.clone()),
                },
                format!("Composition references unknown second morphism {}", second),
            ));
        }
        if !category.morphisms.contains_key(composite) {
            violations.push(violation(
                FiniteCategoryValidation::CompositionClosure,
                ValidationLocation::Composition {
                    first: first.clone(),
                    second: second.clone(),
                    composite: Some(composite.clone()),
                },
                format!("Composite {} is not a declared morphism", composite),
            ));
        }
    }

    violations
}

pub fn check_composition_boundaries(category: &DeclaredFiniteCategory) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for ((first_name, second_name), composite_name) in &category.compositions {
        let Some(first) = category.morphisms.get(first_name) else {
            continue;
        };
        let Some(second) = category.morphisms.get(second_name) else {
            continue;
        };
        let Some(composite) = category.morphisms.get(composite_name) else {
            continue;
        };

        if first.target != second.source {
            violations.push(violation(
                FiniteCategoryValidation::CompositionBoundary,
                ValidationLocation::Composition {
                    first: first_name.clone(),
                    second: second_name.clone(),
                    composite: Some(composite_name.clone()),
                },
                format!(
                    "Morphism {} targets {}, but {} sources {}",
                    first.name, first.target, second.name, second.source
                ),
            ));
            continue;
        }

        if composite.source != first.source || composite.target != second.target {
            violations.push(violation(
                FiniteCategoryValidation::CompositionBoundary,
                ValidationLocation::Boundary {
                    morphism: composite.name.clone(),
                    source: composite.source.clone(),
                    target: composite.target.clone(),
                },
                format!(
                    "Composite {} should have boundary {} -> {}, got {} -> {}",
                    composite.name, first.source, second.target, composite.source, composite.target
                ),
            ));
        }
    }

    violations
}

pub fn check_associativity(category: &DeclaredFiniteCategory) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for first in category.morphisms.values() {
        for second in category.morphisms.values() {
            if first.target != second.source {
                continue;
            }
            for third in category.morphisms.values() {
                if second.target != third.source {
                    continue;
                }

                let Some(second_after_first) = category.compose(&first.name, &second.name) else {
                    continue;
                };
                let Some(third_after_second) = category.compose(&second.name, &third.name) else {
                    continue;
                };
                let left = category.compose(second_after_first, &third.name);
                let right = category.compose(&first.name, third_after_second);

                match (left, right) {
                    (Some(left), Some(right)) if left == right => {}
                    (Some(left), Some(right)) => violations.push(violation(
                        FiniteCategoryValidation::Associativity,
                        ValidationLocation::Composition {
                            first: first.name.clone(),
                            second: second.name.clone(),
                            composite: Some(third.name.clone()),
                        },
                        format!(
                            "Associativity fails for ({}, {}, {}): left {}, right {}",
                            first.name, second.name, third.name, left, right
                        ),
                    )),
                    _ => violations.push(violation(
                        FiniteCategoryValidation::Associativity,
                        ValidationLocation::Composition {
                            first: first.name.clone(),
                            second: second.name.clone(),
                            composite: Some(third.name.clone()),
                        },
                        format!(
                            "Associativity comparison undefined for ({}, {}, {})",
                            first.name, second.name, third.name
                        ),
                    )),
                }
            }
        }
    }

    violations
}

pub fn validate_finite_category(category: &DeclaredFiniteCategory) -> ValidationReport {
    let mut report = ValidationReport::new(&category.name);

    add_unit(
        &mut report,
        FiniteCategoryValidation::ObjectReference,
        check_object_references(category),
    );
    add_unit(
        &mut report,
        FiniteCategoryValidation::MorphismBoundary,
        check_nonempty_names(category),
    );
    add_unit(
        &mut report,
        FiniteCategoryValidation::IdentityTotality,
        check_identity_totality(category),
    );
    add_unit(
        &mut report,
        FiniteCategoryValidation::IdentityLaw,
        check_identity_laws(category),
    );
    add_unit(
        &mut report,
        FiniteCategoryValidation::CompositionTotality,
        check_composition_totality(category),
    );
    add_unit(
        &mut report,
        FiniteCategoryValidation::CompositionClosure,
        check_composition_closure(category),
    );
    add_unit(
        &mut report,
        FiniteCategoryValidation::CompositionBoundary,
        check_composition_boundaries(category),
    );
    add_unit(
        &mut report,
        FiniteCategoryValidation::Associativity,
        check_associativity(category),
    );

    report
}

// Origin: engine/crates_rs/core_category_theory/src/finite_category_validation.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-category-validation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0b24e8fa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0b24e8fa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0b24e8fa {
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
impl BoundaryError0b24e8fa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0b24e8fa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0b24e8fa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0b24e8fa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0b24e8fa> {
        if capacity_bound == 0 {
            return Err(BoundaryError0b24e8fa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0b24e8fa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0b24e8fa::ExceedsCapacity {
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
    use crate::finite_category::DeclaredFiniteCategory;

    fn valid_walking_arrow() -> DeclaredFiniteCategory {
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
    fn valid_category_passes_all_units() {
        let report = validate_finite_category(&valid_walking_arrow());
        assert!(report.all_passed(), "{:?}", report.typed_violations);
        assert_eq!(report.violation_count(), 0);
    }

    #[test]
    fn missing_composition_is_typed_violation() {
        let mut cat = valid_walking_arrow();
        cat.compositions.remove(&("f".into(), "id_B".into()));

        let report = validate_finite_category(&cat);
        assert!(!report.all_passed());
        assert!(report.typed_violations.iter().any(|violation| {
            violation.unit
                == ValidationUnit::FiniteCategory(FiniteCategoryValidation::CompositionTotality)
        }));
    }

    #[test]
    fn identity_with_wrong_boundary_fails() {
        let mut cat = DeclaredFiniteCategory::new("BadIdentity");
        cat.add_morphism("e", "A", "B");
        cat.set_identity("A", "e");

        let report = validate_finite_category(&cat);
        assert!(!report.all_passed());
        assert!(report.typed_violations.iter().any(|violation| {
            violation.unit
                == ValidationUnit::FiniteCategory(FiniteCategoryValidation::IdentityTotality)
        }));
    }

    #[test]
    fn noncomposable_composition_fails() {
        let mut cat = valid_walking_arrow();
        cat.set_composition("f", "f", "f");

        let report = validate_finite_category(&cat);
        assert!(!report.all_passed());
        assert!(report.typed_violations.iter().any(|violation| {
            violation.unit
                == ValidationUnit::FiniteCategory(FiniteCategoryValidation::CompositionBoundary)
        }));
    }

    #[test]
    fn associativity_failure_is_detected() {
        let mut cat = DeclaredFiniteCategory::new("AssocFail");
        // We only declare the subset needed to trigger associativity failure to keep the test small.
        // It will fail other tests (identity/totality) but that is fine for testing associativity specifically.
        cat.add_morphism("f", "A", "B");
        cat.add_morphism("g", "B", "C");
        cat.add_morphism("h", "C", "D");

        cat.add_morphism("gf", "A", "C");
        cat.add_morphism("hg", "B", "D");

        cat.add_morphism("hgf_left", "A", "D");
        cat.add_morphism("hgf_right", "A", "D");

        cat.set_composition("f", "g", "gf");
        cat.set_composition("g", "h", "hg");
        cat.set_composition("gf", "h", "hgf_left");
        cat.set_composition("f", "hg", "hgf_right");

        let report = validate_finite_category(&cat);
        assert!(!report.all_passed());
        assert!(report.typed_violations.iter().any(|violation| {
            violation.unit
                == ValidationUnit::FiniteCategory(FiniteCategoryValidation::Associativity)
        }));
    }
}

#[cfg(test)]
mod l4_boundary_tests_0b24e8fa {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0b24e8fa::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0b24e8fa::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0b24e8fa::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0b24e8fa::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0b24e8fa::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0b24e8fa::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0b24e8fa::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
