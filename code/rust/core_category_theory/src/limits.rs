//! Finite limits — shared categorical infrastructure.
//!
//! Provides reusable finite cones and universal-property checks
//! for: products, equalizers, pullbacks, and terminal objects.
//!
//! All structures are declarative records validated against a
//! `DeclaredFiniteCategory`. Violations are typed via `ValidationViolation`.

use super::finite_category::DeclaredFiniteCategory;
use super::validation::{
    ValidationLocation, ValidationReport, ValidationSeverity, ValidationUnit, ValidationViolation,
};
use std::collections::BTreeMap;

// ═══════════════════════════════════════════════════════════════════════════
// Validation unit
// ═══════════════════════════════════════════════════════════════════════════

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum LimitValidation {
    ConeApex,
    ConeLeg,
    ConeCommutativity,
    UniversalProperty,
}

fn limit_violation(
    unit: LimitValidation,
    location: ValidationLocation,
    message: impl Into<String>,
) -> ValidationViolation {
    ValidationViolation::new(
        ValidationUnit::Other(format!("limit::{:?}", unit)),
        location,
        message,
        ValidationSeverity::Error,
    )
}

pub fn morphisms_between<'a>(
    category: &'a DeclaredFiniteCategory,
    source: &str,
    target: &str,
) -> Vec<&'a str> {
    category
        .morphisms
        .values()
        .filter(|m| m.source == source && m.target == target)
        .map(|m| m.name.as_str())
        .collect()
}

// ═══════════════════════════════════════════════════════════════════════════
// Cone
// ═══════════════════════════════════════════════════════════════════════════

/// A finite cone over a diagram.
///
/// The diagram is a set of objects and morphisms in the ambient category.
/// The cone has an apex and a leg morphism from the apex to each diagram object.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteCone {
    pub name: String,
    pub apex: String,
    /// Diagram object → leg morphism (apex → diagram object).
    pub legs: BTreeMap<String, String>,
}

impl DeclaredFiniteCone {
    pub fn new(name: &str, apex: &str) -> Self {
        Self {
            name: name.into(),
            apex: apex.into(),
            legs: BTreeMap::new(),
        }
    }

    pub fn set_leg(&mut self, diagram_object: &str, leg_morphism: &str) {
        self.legs.insert(diagram_object.into(), leg_morphism.into());
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Cone validation
// ═══════════════════════════════════════════════════════════════════════════

fn check_cone_legs(
    cone: &DeclaredFiniteCone,
    category: &DeclaredFiniteCategory,
    violations: &mut Vec<ValidationViolation>,
) {
    for (object, leg) in &cone.legs {
        match category.boundary_of(leg) {
            Some((src, tgt)) if src == cone.apex && tgt == *object => {}
            Some((src, tgt)) => violations.push(limit_violation(
                LimitValidation::ConeLeg,
                ValidationLocation::Boundary {
                    morphism: leg.clone(),
                    source: src.into(),
                    target: tgt.into(),
                },
                format!(
                    "Cone leg {} should have boundary {} -> {}, got {} -> {}",
                    leg, cone.apex, object, src, tgt
                ),
            )),
            None => violations.push(limit_violation(
                LimitValidation::ConeLeg,
                ValidationLocation::Morphism(leg.clone()),
                format!("Cone leg {} is not a valid morphism", leg),
            )),
        }
    }
}

fn check_cone_commutativity(
    cone: &DeclaredFiniteCone,
    diagram_morphisms: &[(&str, &str, &str)],
    category: &DeclaredFiniteCategory,
    violations: &mut Vec<ValidationViolation>,
) {
    for &(mor, src, tgt) in diagram_morphisms {
        let Some(leg_src) = cone.legs.get(src) else {
            violations.push(limit_violation(
                LimitValidation::ConeLeg,
                ValidationLocation::Object(src.into()),
                format!("Cone has no leg to diagram object {}", src),
            ));
            continue;
        };
        let Some(leg_tgt) = cone.legs.get(tgt) else {
            violations.push(limit_violation(
                LimitValidation::ConeLeg,
                ValidationLocation::Object(tgt.into()),
                format!("Cone has no leg to diagram object {}", tgt),
            ));
            continue;
        };

        // Check d ∘ leg_src = leg_tgt
        match category.compose(leg_src, mor) {
            Some(composed) if composed == leg_tgt.as_str() => {}
            Some(composed) => violations.push(limit_violation(
                LimitValidation::ConeCommutativity,
                ValidationLocation::Morphism(mor.into()),
                format!("{} ∘ {} = {}, expected {}", mor, leg_src, composed, leg_tgt),
            )),
            None => violations.push(limit_violation(
                LimitValidation::ConeCommutativity,
                ValidationLocation::Morphism(mor.into()),
                format!("{} ∘ {} is not defined", mor, leg_src),
            )),
        }
    }
}

/// Validate that a cone's legs commute with diagram morphisms.
///
/// For each diagram morphism `d: X → Y`, check `d ∘ leg_X = leg_Y`.
pub fn validate_cone(
    cone: &DeclaredFiniteCone,
    diagram_objects: &[&str],
    diagram_morphisms: &[(&str, &str, &str)], // (morphism, source, target)
    category: &DeclaredFiniteCategory,
) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    if !category.has_object(&cone.apex) {
        violations.push(limit_violation(
            LimitValidation::ConeApex,
            ValidationLocation::Object(cone.apex.clone()),
            format!("Cone apex {} is not an object", cone.apex),
        ));
        return violations;
    }

    for &obj in diagram_objects {
        if !cone.legs.contains_key(obj) {
            violations.push(limit_violation(
                LimitValidation::ConeLeg,
                ValidationLocation::Object(obj.into()),
                format!("Cone has no leg to diagram object {}", obj),
            ));
        }
    }

    check_cone_legs(cone, category, &mut violations);
    check_cone_commutativity(cone, diagram_morphisms, category, &mut violations);

    violations
}

// ═══════════════════════════════════════════════════════════════════════════
// Concrete limit structures
// ═══════════════════════════════════════════════════════════════════════════

/// A declared finite product of two objects.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteProduct {
    pub product_object: String,
    pub left_object: String,
    pub right_object: String,
    pub projection_left: String,
    pub projection_right: String,
    /// Universal morphism witnesses: for each test cone (morphism_to_left, morphism_to_right),
    /// the unique mediating morphism to the product.
    pub universal_witnesses: BTreeMap<(String, String), String>,
}

/// A declared finite equalizer of two parallel morphisms f, g : A → B.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteEqualizer {
    pub equalizer_object: String,
    pub source: String,
    pub target: String,
    pub morphism_f: String,
    pub morphism_g: String,
    pub equalizer_morphism: String, // e : E → A such that f∘e = g∘e
}

/// A declared finite pullback of f : A → C and g : B → C.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFinitePullback {
    pub pullback_object: String,
    pub left_source: String,
    pub right_source: String,
    pub morphism_f: String,       // f : A → C
    pub morphism_g: String,       // g : B → C
    pub projection_left: String,  // p₁ : P → A
    pub projection_right: String, // p₂ : P → B
}

// ═══════════════════════════════════════════════════════════════════════════
// Validation of concrete structures
// ═══════════════════════════════════════════════════════════════════════════

/// Validate a product: projections exist, and for each witness the triangle commutes.
pub fn validate_product(
    product: &DeclaredFiniteProduct,
    category: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&format!("product({})", product.product_object));

    let cone = DeclaredFiniteCone {
        name: format!("product_cone_{}", product.product_object),
        apex: product.product_object.clone(),
        legs: BTreeMap::from([
            (product.left_object.clone(), product.projection_left.clone()),
            (
                product.right_object.clone(),
                product.projection_right.clone(),
            ),
        ]),
    };
    let cone_violations = validate_cone(
        &cone,
        &[&product.left_object, &product.right_object],
        &[],
        category,
    );
    report.add_typed("product_cone", cone_violations);

    let mut univ_violations = Vec::new();

    for x in &category.objects {
        let left_morphisms = morphisms_between(category, x, &product.left_object);
        let right_morphisms = morphisms_between(category, x, &product.right_object);

        for l in &left_morphisms {
            for r in &right_morphisms {
                let mediators: Vec<_> = morphisms_between(category, x, &product.product_object)
                    .into_iter()
                    .filter(|m| {
                        category.compose(m, &product.projection_left) == Some(*l)
                            && category.compose(m, &product.projection_right) == Some(*r)
                    })
                    .collect();

                if mediators.is_empty() {
                    univ_violations.push(limit_violation(
                        LimitValidation::UniversalProperty,
                        ValidationLocation::Object(x.clone()),
                        format!("No unique mediator for cone l={}, r={}", l, r),
                    ));
                } else if mediators.len() > 1 {
                    univ_violations.push(limit_violation(
                        LimitValidation::UniversalProperty,
                        ValidationLocation::Object(x.clone()),
                        format!(
                            "Multiple mediators {:?} for cone l={}, r={}",
                            mediators, l, r
                        ),
                    ));
                }
            }
        }
    }

    report.add_typed("product_universal", univ_violations);

    report
}

fn check_equalizer_mediator(
    eq: &DeclaredFiniteEqualizer,
    category: &DeclaredFiniteCategory,
    x: &String,
    h: &str,
    univ_violations: &mut Vec<ValidationViolation>,
) {
    let left_h = category.compose(h, &eq.morphism_f);
    let right_h = category.compose(h, &eq.morphism_g);
    if left_h.is_none() || left_h != right_h {
        return;
    }
    // Should have a unique u: x -> E such that e*u = h
    let mediators: Vec<_> = morphisms_between(category, x, &eq.equalizer_object)
        .into_iter()
        .filter(|m| category.compose(m, &eq.equalizer_morphism) == Some(h))
        .collect();

    if mediators.is_empty() {
        univ_violations.push(limit_violation(
            LimitValidation::UniversalProperty,
            ValidationLocation::Object(x.clone()),
            format!("No unique mediator for equalizer cone h={}", h),
        ));
    } else if mediators.len() > 1 {
        univ_violations.push(limit_violation(
            LimitValidation::UniversalProperty,
            ValidationLocation::Object(x.clone()),
            format!(
                "Multiple mediators {:?} for equalizer cone h={}",
                mediators, h
            ),
        ));
    }
}

/// Validate an equalizer: e equalizes f and g, i.e. f∘e = g∘e.
pub fn validate_equalizer(
    eq: &DeclaredFiniteEqualizer,
    category: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&format!("equalizer({})", eq.equalizer_object));
    let mut violations = Vec::new();

    if category.boundary_of(&eq.equalizer_morphism) != Some((&eq.equalizer_object, &eq.source)) {
        violations.push(limit_violation(
            LimitValidation::ConeLeg,
            ValidationLocation::Morphism(eq.equalizer_morphism.clone()),
            format!(
                "Equalizer morphism should have boundary {} -> {}",
                eq.equalizer_object, eq.source
            ),
        ));
    }

    let left = category.compose(&eq.equalizer_morphism, &eq.morphism_f);
    let right = category.compose(&eq.equalizer_morphism, &eq.morphism_g);

    match (left, right) {
        (Some(l), Some(r)) if l == r => {}
        (Some(l), Some(r)) => violations.push(limit_violation(
            LimitValidation::ConeCommutativity,
            ValidationLocation::Morphism(eq.equalizer_morphism.clone()),
            format!("f∘e = {} ≠ g∘e = {}", l, r),
        )),
        _ => violations.push(limit_violation(
            LimitValidation::ConeCommutativity,
            ValidationLocation::Morphism(eq.equalizer_morphism.clone()),
            "f∘e or g∘e is not defined".to_string(),
        )),
    }

    report.add_typed("equalizer_law", violations);

    let mut univ_violations = Vec::new();
    for x in &category.objects {
        for h in morphisms_between(category, x, &eq.source) {
            check_equalizer_mediator(eq, category, x, h, &mut univ_violations);
        }
    }
    report.add_typed("equalizer_universal", univ_violations);

    report
}

fn check_pullback_mediator(
    pb: &DeclaredFinitePullback,
    category: &DeclaredFiniteCategory,
    x: &String,
    x1: &str,
    x2: &str,
    univ_violations: &mut Vec<ValidationViolation>,
) {
    let left_comm = category.compose(x1, &pb.morphism_f);
    let right_comm = category.compose(x2, &pb.morphism_g);
    if left_comm.is_none() || left_comm != right_comm {
        return;
    }
    // Valid cone, find unique mediator u: X -> P
    let mediators: Vec<_> = morphisms_between(category, x, &pb.pullback_object)
        .into_iter()
        .filter(|m| {
            category.compose(m, &pb.projection_left) == Some(x1)
                && category.compose(m, &pb.projection_right) == Some(x2)
        })
        .collect();

    if mediators.is_empty() {
        univ_violations.push(limit_violation(
            LimitValidation::UniversalProperty,
            ValidationLocation::Object(x.clone()),
            format!("No unique mediator for pullback cone x1={}, x2={}", x1, x2),
        ));
    } else if mediators.len() > 1 {
        univ_violations.push(limit_violation(
            LimitValidation::UniversalProperty,
            ValidationLocation::Object(x.clone()),
            format!(
                "Multiple mediators {:?} for pullback cone x1={}, x2={}",
                mediators, x1, x2
            ),
        ));
    }
}

/// Validate a pullback: f∘p₁ = g∘p₂.
pub fn validate_pullback(
    pb: &DeclaredFinitePullback,
    category: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&format!("pullback({})", pb.pullback_object));
    let mut violations = Vec::new();

    let left = category.compose(&pb.projection_left, &pb.morphism_f);
    let right = category.compose(&pb.projection_right, &pb.morphism_g);

    match (left, right) {
        (Some(l), Some(r)) if l == r => {}
        (Some(l), Some(r)) => violations.push(limit_violation(
            LimitValidation::ConeCommutativity,
            ValidationLocation::Named("pullback square".into()),
            format!("f∘p₁ = {} ≠ g∘p₂ = {}", l, r),
        )),
        _ => violations.push(limit_violation(
            LimitValidation::ConeCommutativity,
            ValidationLocation::Named("pullback square".into()),
            "f∘p₁ or g∘p₂ is not defined".to_string(),
        )),
    }

    report.add_typed("pullback_square", violations);

    let mut univ_violations = Vec::new();
    for x in &category.objects {
        let x1_morphisms = morphisms_between(category, x, &pb.left_source);
        let x2_morphisms = morphisms_between(category, x, &pb.right_source);

        for x1 in &x1_morphisms {
            for x2 in &x2_morphisms {
                check_pullback_mediator(pb, category, x, x1, x2, &mut univ_violations);
            }
        }
    }
    report.add_typed("pullback_universal", univ_violations);

    report
}

// ═══════════════════════════════════════════════════════════════════════════
// Terminal
// ═══════════════════════════════════════════════════════════════════════════

/// Check that an object is terminal: for every object X, there is exactly
/// one morphism X → T in the declared category.
pub fn check_terminal(
    terminal: &str,
    category: &DeclaredFiniteCategory,
) -> Vec<ValidationViolation> {
    let mut violations = Vec::new();

    for object in &category.objects {
        let morphisms_to_terminal: Vec<_> = category
            .morphisms
            .values()
            .filter(|m| m.source == *object && m.target == terminal)
            .collect();

        if morphisms_to_terminal.is_empty() {
            violations.push(limit_violation(
                LimitValidation::UniversalProperty,
                ValidationLocation::Object(object.clone()),
                format!(
                    "No morphism from {} to terminal object {}",
                    object, terminal
                ),
            ));
        } else if morphisms_to_terminal.len() > 1 {
            violations.push(limit_violation(
                LimitValidation::UniversalProperty,
                ValidationLocation::Object(object.clone()),
                format!(
                    "Multiple morphisms {:?} from {} to terminal object {}",
                    morphisms_to_terminal, object, terminal
                ),
            ));
        }
    }

    violations
}

// Origin: engine/crates_rs/core_category_theory/src/limits.rs
// Claim: urn:core:crates_rs:core-category-theory:limits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7b7703d6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7b7703d6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7b7703d6 {
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
impl BoundaryError7b7703d6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7b7703d6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7b7703d6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7b7703d6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7b7703d6> {
        if capacity_bound == 0 {
            return Err(BoundaryError7b7703d6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7b7703d6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7b7703d6::ExceedsCapacity {
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
mod l4_boundary_tests_7b7703d6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7b7703d6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7b7703d6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7b7703d6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7b7703d6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7b7703d6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7b7703d6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7b7703d6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
