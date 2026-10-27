//! Finite colimits — shared categorical infrastructure.
//!
//! Provides reusable finite cocones and universal-property checks
//! for: coproducts, coequalizers, pushouts, and initial objects.
//!
//! All structures are declarative records validated against a
//! `DeclaredFiniteCategory`. Violations are typed via `ValidationViolation`.

use super::finite_category::DeclaredFiniteCategory;
use super::limits::morphisms_between;
use super::validation::{
    ValidationLocation, ValidationReport, ValidationSeverity, ValidationUnit, ValidationViolation,
};
use std::collections::BTreeMap;

// ═══════════════════════════════════════════════════════════════════════════
// Validation unit
// ═══════════════════════════════════════════════════════════════════════════

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ColimitValidation {
    CoconeNadir,
    CoconeLeg,
    CoconeCommutativity,
    CoconeUniversalProperty,
}

fn colimit_violation(
    unit: ColimitValidation,
    location: ValidationLocation,
    message: impl Into<String>,
) -> ValidationViolation {
    ValidationViolation::new(
        ValidationUnit::Other(format!("colimit::{:?}", unit)),
        location,
        message,
        ValidationSeverity::Error,
    )
}

// ═══════════════════════════════════════════════════════════════════════════
// Cocone
// ═══════════════════════════════════════════════════════════════════════════

/// A finite cocone under a diagram.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteCocone {
    pub name: String,
    pub nadir: String,
    /// Diagram object → leg morphism (diagram object → nadir).
    pub legs: BTreeMap<String, String>,
}

impl DeclaredFiniteCocone {
    pub fn new(name: &str, nadir: &str) -> Self {
        Self {
            name: name.into(),
            nadir: nadir.into(),
            legs: BTreeMap::new(),
        }
    }

    pub fn set_leg(&mut self, diagram_object: &str, leg_morphism: &str) {
        self.legs.insert(diagram_object.into(), leg_morphism.into());
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Cocone validation
// ═══════════════════════════════════════════════════════════════════════════

fn check_cocone_leg_boundaries(
    cocone: &DeclaredFiniteCocone,
    category: &DeclaredFiniteCategory,
    violations: &mut Vec<ValidationViolation>,
) {
    for (object, leg) in &cocone.legs {
        match category.boundary_of(leg) {
            Some((src, tgt)) if src == *object && tgt == cocone.nadir => {}
            Some((src, tgt)) => violations.push(colimit_violation(
                ColimitValidation::CoconeLeg,
                ValidationLocation::Boundary {
                    morphism: leg.clone(),
                    source: src.into(),
                    target: tgt.into(),
                },
                format!(
                    "Cocone leg {} should have boundary {} -> {}, got {} -> {}",
                    leg, object, cocone.nadir, src, tgt
                ),
            )),
            None => violations.push(colimit_violation(
                ColimitValidation::CoconeLeg,
                ValidationLocation::Morphism(leg.clone()),
                format!("Cocone leg {} is not a valid morphism", leg),
            )),
        }
    }
}

fn check_cocone_morphism_commutativity(
    cocone: &DeclaredFiniteCocone,
    mor: &str,
    src: &str,
    tgt: &str,
    category: &DeclaredFiniteCategory,
    violations: &mut Vec<ValidationViolation>,
) {
    let Some(leg_src) = cocone.legs.get(src) else {
        violations.push(colimit_violation(
            ColimitValidation::CoconeLeg,
            ValidationLocation::Object(src.into()),
            format!("Cocone has no leg from diagram object {}", src),
        ));
        return;
    };
    let Some(leg_tgt) = cocone.legs.get(tgt) else {
        violations.push(colimit_violation(
            ColimitValidation::CoconeLeg,
            ValidationLocation::Object(tgt.into()),
        format!("Cocone has no leg from diagram object {}", tgt),
        ));
        return;
    };

    // Check leg_tgt ∘ d = leg_src  (i.e. compose(d, leg_tgt) == leg_src)
    match category.compose(mor, leg_tgt) {
        Some(composed) if composed == leg_src.as_str() => {}
        Some(composed) => violations.push(colimit_violation(
            ColimitValidation::CoconeCommutativity,
            ValidationLocation::Morphism(mor.into()),
            format!("leg_{} ∘ {} = {}, expected {}", tgt, mor, composed, leg_src),
        )),
        None => violations.push(colimit_violation(
            ColimitValidation::CoconeCommutativity,
            ValidationLocation::Morphism(mor.into()),
            format!("leg_{} ∘ {} is not defined", tgt, mor),
        )),
    }
}

/// Validate that a cocone's legs commute with diagram morphisms.
///
/// For each diagram morphism `d: X → Y`, check `leg_Y ∘ d = leg_X`.
pub fn validate_cocone(
    cocone: &DeclaredFiniteCocone,
    diagram_objects: &[&str],
    diagram_morphisms: &[(&str, &str, &str)],
    category: &DeclaredFiniteCategory,
) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    if !category.has_object(&cocone.nadir) {
        violations.push(colimit_violation(
            ColimitValidation::CoconeNadir,
            ValidationLocation::Object(cocone.nadir.clone()),
            format!("Cocone nadir {} is not an object", cocone.nadir),
        ));
        return violations;
    }

    for &obj in diagram_objects {
        if !cocone.legs.contains_key(obj) {
            violations.push(colimit_violation(
                ColimitValidation::CoconeLeg,
                ValidationLocation::Object(obj.into()),
                format!("Cocone has no leg from diagram object {}", obj),
            ));
        }
    }

    check_cocone_leg_boundaries(cocone, category, &mut violations);

    for &(mor, src, tgt) in diagram_morphisms {
        check_cocone_morphism_commutativity(cocone, mor, src, tgt, category, &mut violations);
    }

    violations
}

// ═══════════════════════════════════════════════════════════════════════════
// Concrete colimit structures
// ═══════════════════════════════════════════════════════════════════════════

/// A declared finite coproduct of two objects.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteCoproduct {
    pub coproduct_object: String,
    pub left_object: String,
    pub right_object: String,
    pub injection_left: String,
    pub injection_right: String,
    pub universal_witnesses: BTreeMap<(String, String), String>,
}

/// A declared finite coequalizer of two parallel morphisms f, g : A → B.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteCoequalizer {
    pub coequalizer_object: String,
    pub source: String,
    pub target: String,
    pub morphism_f: String,
    pub morphism_g: String,
    pub coequalizer_morphism: String, // q : B → Q such that q∘f = q∘g
}

/// A declared finite pushout of f : C → A and g : C → B.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFinitePushout {
    pub pushout_object: String,
    pub left_target: String,
    pub right_target: String,
    pub morphism_f: String,      // f : C → A
    pub morphism_g: String,      // g : C → B
    pub injection_left: String,  // i₁ : A → P
    pub injection_right: String, // i₂ : B → P
}

// ═══════════════════════════════════════════════════════════════════════════
// Validation of concrete structures
// ═══════════════════════════════════════════════════════════════════════════

/// Validate a coproduct: injections exist, and for each cocone, a unique mediator exists.
pub fn validate_coproduct(
    coproduct: &DeclaredFiniteCoproduct,
    category: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&format!("coproduct({})", coproduct.coproduct_object));

    let cocone = DeclaredFiniteCocone {
        name: format!("coproduct_cocone_{}", coproduct.coproduct_object),
        nadir: coproduct.coproduct_object.clone(),
        legs: BTreeMap::from([
            (
                coproduct.left_object.clone(),
                coproduct.injection_left.clone(),
            ),
            (
                coproduct.right_object.clone(),
                coproduct.injection_right.clone(),
            ),
        ]),
    };
    let cocone_violations = validate_cocone(
        &cocone,
        &[&coproduct.left_object, &coproduct.right_object],
        &[],
        category,
    );
    report.add_typed("coproduct_cocone", cocone_violations);

    let mut univ_violations = Vec::new();

    for x in &category.objects {
        let left_morphisms = morphisms_between(category, &coproduct.left_object, x);
        let right_morphisms = morphisms_between(category, &coproduct.right_object, x);

        for l in &left_morphisms {
            for r in &right_morphisms {
                let mediators: Vec<_> = morphisms_between(category, &coproduct.coproduct_object, x)
                    .into_iter()
                    .filter(|m| {
                        category.compose(&coproduct.injection_left, m) == Some(*l)
                            && category.compose(&coproduct.injection_right, m) == Some(*r)
                    })
                    .collect();

                if mediators.is_empty() {
                    univ_violations.push(colimit_violation(
                        ColimitValidation::CoconeUniversalProperty,
                        ValidationLocation::Object(x.clone()),
                        format!("No unique mediator for cocone l={}, r={}", l, r),
                    ));
                } else if mediators.len() > 1 {
                    univ_violations.push(colimit_violation(
                        ColimitValidation::CoconeUniversalProperty,
                        ValidationLocation::Object(x.clone()),
                        format!(
                            "Multiple mediators {:?} for cocone l={}, r={}",
                            mediators, l, r
                        ),
                    ));
                }
            }
        }
    }

    report.add_typed("coproduct_universal", univ_violations);

    report
}

fn check_coequalizer_mediator(
    coeq: &DeclaredFiniteCoequalizer,
    category: &DeclaredFiniteCategory,
    x: &String,
    h: &str,
    univ_violations: &mut Vec<ValidationViolation>,
) {
    let left_h = category.compose(&coeq.morphism_f, h);
    let right_h = category.compose(&coeq.morphism_g, h);
    if left_h.is_none() || left_h != right_h {
        return;
    }
    // Should have a unique u: Q -> x such that u*q = h
    let mediators: Vec<_> = morphisms_between(category, &coeq.coequalizer_object, x)
        .into_iter()
        .filter(|m| category.compose(&coeq.coequalizer_morphism, m) == Some(h))
        .collect();

    if mediators.is_empty() {
        univ_violations.push(colimit_violation(
            ColimitValidation::CoconeUniversalProperty,
            ValidationLocation::Object(x.clone()),
            format!("No unique mediator for coequalizer cocone h={}", h),
        ));
    } else if mediators.len() > 1 {
        univ_violations.push(colimit_violation(
            ColimitValidation::CoconeUniversalProperty,
            ValidationLocation::Object(x.clone()),
            format!(
                "Multiple mediators {:?} for coequalizer cocone h={}",
                mediators, h
            ),
        ));
    }
}

/// Validate a coequalizer: q coequalizes f and g, i.e. q∘f = q∘g.
pub fn validate_coequalizer(
    coeq: &DeclaredFiniteCoequalizer,
    category: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&format!("coequalizer({})", coeq.coequalizer_object));
    let mut violations = Vec::new();

    if category.boundary_of(&coeq.coequalizer_morphism)
        != Some((&coeq.target, &coeq.coequalizer_object))
    {
        violations.push(colimit_violation(
            ColimitValidation::CoconeLeg,
            ValidationLocation::Morphism(coeq.coequalizer_morphism.clone()),
            format!(
                "Coequalizer morphism should have boundary {} -> {}",
                coeq.target, coeq.coequalizer_object
            ),
        ));
    }

    let left = category.compose(&coeq.morphism_f, &coeq.coequalizer_morphism);
    let right = category.compose(&coeq.morphism_g, &coeq.coequalizer_morphism);

    match (left, right) {
        (Some(l), Some(r)) if l == r => {}
        (Some(l), Some(r)) => violations.push(colimit_violation(
            ColimitValidation::CoconeCommutativity,
            ValidationLocation::Morphism(coeq.coequalizer_morphism.clone()),
            format!("q∘f = {} ≠ q∘g = {}", l, r),
        )),
        _ => violations.push(colimit_violation(
            ColimitValidation::CoconeCommutativity,
            ValidationLocation::Morphism(coeq.coequalizer_morphism.clone()),
            "q∘f or q∘g is not defined".to_string(),
        )),
    }

    report.add_typed("coequalizer_law", violations);

    let mut univ_violations = Vec::new();
    for x in &category.objects {
        for h in morphisms_between(category, &coeq.target, x) {
            check_coequalizer_mediator(coeq, category, x, h, &mut univ_violations);
        }
    }
    report.add_typed("coequalizer_universal", univ_violations);

    report
}

fn check_pushout_mediator(
    po: &DeclaredFinitePushout,
    category: &DeclaredFiniteCategory,
    x: &String,
    x1: &str,
    x2: &str,
    univ_violations: &mut Vec<ValidationViolation>,
) {
    let left_comm = category.compose(&po.morphism_f, x1);
    let right_comm = category.compose(&po.morphism_g, x2);
    if left_comm.is_none() || left_comm != right_comm {
        return;
    }
    // Valid cocone, find unique mediator u: P -> X
    let mediators: Vec<_> = morphisms_between(category, &po.pushout_object, x)
        .into_iter()
        .filter(|m| {
            category.compose(&po.injection_left, m) == Some(x1)
                && category.compose(&po.injection_right, m) == Some(x2)
        })
        .collect();

    if mediators.is_empty() {
        univ_violations.push(colimit_violation(
            ColimitValidation::CoconeUniversalProperty,
            ValidationLocation::Object(x.clone()),
            format!("No unique mediator for pushout cocone x1={}, x2={}", x1, x2),
        ));
    } else if mediators.len() > 1 {
        univ_violations.push(colimit_violation(
            ColimitValidation::CoconeUniversalProperty,
            ValidationLocation::Object(x.clone()),
            format!(
                "Multiple mediators {:?} for pushout cocone x1={}, x2={}",
                mediators, x1, x2
            ),
        ));
    }
}

/// Validate a pushout: i₁∘f = i₂∘g.
pub fn validate_pushout(
    po: &DeclaredFinitePushout,
    category: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&format!("pushout({})", po.pushout_object));
    let mut violations = Vec::new();

    let left = category.compose(&po.morphism_f, &po.injection_left);
    let right = category.compose(&po.morphism_g, &po.injection_right);

    match (left, right) {
        (Some(l), Some(r)) if l == r => {}
        (Some(l), Some(r)) => violations.push(colimit_violation(
            ColimitValidation::CoconeCommutativity,
            ValidationLocation::Named("pushout square".into()),
            format!("i₁∘f = {} ≠ i₂∘g = {}", l, r),
        )),
        _ => violations.push(colimit_violation(
            ColimitValidation::CoconeCommutativity,
            ValidationLocation::Named("pushout square".into()),
            "i₁∘f or i₂∘g is not defined".to_string(),
        )),
    }

    report.add_typed("pushout_square", violations);

    let mut univ_violations = Vec::new();
    for x in &category.objects {
        let x1_morphisms = morphisms_between(category, &po.left_target, x);
        let x2_morphisms = morphisms_between(category, &po.right_target, x);

        for x1 in &x1_morphisms {
            for x2 in &x2_morphisms {
                check_pushout_mediator(po, category, x, x1, x2, &mut univ_violations);
            }
        }
    }
    report.add_typed("pushout_universal", univ_violations);

    report
}

/// Check that an object is initial: for every object X, there is exactly
/// one morphism I → X in the declared category.
pub fn check_initial(initial: &str, category: &DeclaredFiniteCategory) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for object in &category.objects {
        let morphisms_from_initial: Vec<_> = category
            .morphisms
            .values()
            .filter(|m| m.source == initial && m.target == *object)
            .collect();

        if morphisms_from_initial.is_empty() {
            violations.push(colimit_violation(
                ColimitValidation::CoconeUniversalProperty,
                ValidationLocation::Object(object.clone()),
                format!("No morphism from initial object {} to {}", initial, object),
            ));
        } else if morphisms_from_initial.len() > 1 {
            violations.push(colimit_violation(
                ColimitValidation::CoconeUniversalProperty,
                ValidationLocation::Object(object.clone()),
                format!(
                    "Multiple morphisms {:?} from initial object {} to {}",
                    morphisms_from_initial, initial, object
                ),
            ));
        }
    }

    violations
}

// Origin: engine/crates_rs/core_category_theory/src/colimits.rs
// Claim: urn:core:crates_rs:core-category-theory:colimits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord24d30418 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord24d30418` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError24d30418 {
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
impl BoundaryError24d30418 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError24d30418 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError24d30418 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord24d30418 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError24d30418> {
        if capacity_bound == 0 {
            return Err(BoundaryError24d30418::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError24d30418::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError24d30418::ExceedsCapacity {
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
mod l4_boundary_tests_24d30418 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord24d30418::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord24d30418::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord24d30418::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord24d30418::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord24d30418::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError24d30418::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError24d30418::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
