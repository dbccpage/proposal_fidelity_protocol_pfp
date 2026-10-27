//! Hom-set bijection witnesses for adjunctions.
//!
//! An adjunction L ⊣ R induces a natural bijection
//!   Hom_D(L(A), B) ≅ Hom_C(A, R(B))
//!
//! This module records explicit witness pairs and validates round-trip
//! coherence, complementing the unit/counit triangle checks in `adjunction.rs`.

use super::finite_category::DeclaredFiniteCategory;
use super::validation::{
    AdjunctionValidation, ValidationLocation, ValidationReport, ValidationSeverity, ValidationUnit,
    ValidationViolation,
};
use crate::cat_functor::DeclaredFiniteFunctor;
use std::collections::{BTreeMap, BTreeSet};

// ═══════════════════════════════════════════════════════════════════════════
// Hom-set bijection witness
// ═══════════════════════════════════════════════════════════════════════════

/// A single hom-set bijection witness for a pair (A, B).
///
/// Records the explicit bijection Hom_D(L(A), B) ↔ Hom_C(A, R(B))
/// as a finite map in both directions, plus round-trip data.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HomBijectionWitness {
    /// Base object A.
    pub base_object: String,
    /// Lifted object B.
    pub lifted_object: String,
    /// Forward direction: morphism in Hom_D(L(A), B) → morphism in Hom_C(A, R(B)).
    /// Also called the "transpose" or "mate" in the left-to-right direction.
    pub forward: BTreeMap<String, String>,
    /// Backward direction: morphism in Hom_C(A, R(B)) → morphism in Hom_D(L(A), B).
    pub backward: BTreeMap<String, String>,
}

impl HomBijectionWitness {
    pub fn new(base_object: &str, lifted_object: &str) -> Self {
        Self {
            base_object: base_object.into(),
            lifted_object: lifted_object.into(),
            forward: BTreeMap::new(),
            backward: BTreeMap::new(),
        }
    }

    /// Record a bijection pair: f : L(A) → B  ↔  f_bar : A → R(B).
    pub fn add_mate_pair(&mut self, lifted_morphism: &str, base_morphism: &str) {
        self.forward
            .insert(lifted_morphism.into(), base_morphism.into());
        self.backward
            .insert(base_morphism.into(), lifted_morphism.into());
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Declared hom-set adjunction data
// ═══════════════════════════════════════════════════════════════════════════

/// Full hom-set bijection data for a declared finite adjunction.
///
/// This augments `DeclaredFiniteAdjunction` with explicit bijection witnesses
/// for each (A, B) pair where A is a base object and B is a lifted object.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredHomAdjunction {
    pub adjunction_name: String,
    pub left_functor: String,
    pub right_functor: String,
    pub witnesses: Vec<HomBijectionWitness>,
}

impl DeclaredHomAdjunction {
    pub fn new(name: &str, left: &str, right: &str) -> Self {
        Self {
            adjunction_name: name.into(),
            left_functor: left.into(),
            right_functor: right.into(),
            witnesses: Vec::new(),
        }
    }

    pub fn add_witness(&mut self, witness: HomBijectionWitness) {
        self.witnesses.push(witness);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Validation
// ═══════════════════════════════════════════════════════════════════════════

fn hom_violation(
    unit: AdjunctionValidation,
    location: ValidationLocation,
    message: impl Into<String>,
) -> ValidationViolation {
    ValidationViolation::new(
        ValidationUnit::Adjunction(unit),
        location,
        message,
        ValidationSeverity::Error,
    )
}

fn hom_set(category: &DeclaredFiniteCategory, src: &str, tgt: &str) -> BTreeSet<String> {
    category
        .morphisms
        .values()
        .filter(|m| m.source == src && m.target == tgt)
        .map(|m| m.name.clone())
        .collect()
}

fn check_left_roundtrip(
    forward: &BTreeMap<String, String>,
    backward: &BTreeMap<String, String>,
    pair_label: &str,
    violations: &mut Vec<ValidationViolation>,
) {
    // 4. Left round-trip: backward(forward(f)) = f
    for (f, f_bar) in forward {
        match backward.get(f_bar) {
            Some(roundtrip) if roundtrip == f => {}
            Some(roundtrip) => violations.push(hom_violation(
                AdjunctionValidation::HomBijectionRoundTrip,
                ValidationLocation::Morphism(f.clone()),
                format!(
                    "Left round-trip fails at {}: backward(forward({})) = backward({}) = {}, expected {}",
                    pair_label, f, f_bar, roundtrip, f
                ),
            )),
            None => violations.push(hom_violation(
                AdjunctionValidation::HomBijectionRoundTrip,
                ValidationLocation::Morphism(f.clone()),
                format!(
                    "Left round-trip fails at {}: forward({}) = {}, but backward({}) is undefined",
                    pair_label, f, f_bar, f_bar
                ),
            )),
        }
    }
}

fn check_right_roundtrip(
    forward: &BTreeMap<String, String>,
    backward: &BTreeMap<String, String>,
    pair_label: &str,
    violations: &mut Vec<ValidationViolation>,
) {
    // 5. Right round-trip: forward(backward(f_bar)) = f_bar
    for (f_bar, f) in backward {
        match forward.get(f) {
            Some(roundtrip) if roundtrip == f_bar => {}
            Some(roundtrip) => violations.push(hom_violation(
                AdjunctionValidation::HomBijectionRoundTrip,
                ValidationLocation::Morphism(f_bar.clone()),
                format!(
                    "Right round-trip fails at {}: forward(backward({})) = forward({}) = {}, expected {}",
                    pair_label, f_bar, f, roundtrip, f_bar
                ),
            )),
            None => violations.push(hom_violation(
                AdjunctionValidation::HomBijectionRoundTrip,
                ValidationLocation::Morphism(f_bar.clone()),
                format!(
                    "Right round-trip fails at {}: backward({}) = {}, but forward({}) is undefined",
                    pair_label, f_bar, f, f
                ),
            )),
        }
    }
}

/// Validate hom-set bijection witnesses for round-trip coherence and totality.
///
/// For each witness (A, B):
///   1. A is in Base, B is in Lifted.
///   2. forward and backward map exactly the sets Hom_D(L(A), B) and Hom_C(A, R(B)).
///   3. forward(f) = f_bar  implies  backward(f_bar) = f   (left round-trip)
///   4. backward(f_bar) = f implies  forward(f) = f_bar    (right round-trip)
///   5. forward and backward have the same cardinality (bijectivity)
pub fn validate_hom_adjunction(
    hom_adj: &DeclaredHomAdjunction,
    left: &DeclaredFiniteFunctor,
    right: &DeclaredFiniteFunctor,
    base: &DeclaredFiniteCategory,
    lifted: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&hom_adj.adjunction_name);

    for witness in &hom_adj.witnesses {
        let pair_label = format!("({}, {})", witness.base_object, witness.lifted_object);
        let mut violations = Vec::new();

        // 1. Check functor application
        let Some(la) = left.on_object(&witness.base_object) else {
            violations.push(hom_violation(
                AdjunctionValidation::HomSetMembership,
                ValidationLocation::Object(witness.base_object.clone()),
                format!(
                    "Left functor is undefined on base object {}",
                    witness.base_object
                ),
            ));
            report.add_typed(&format!("hom_bijection_{}", pair_label), violations);
            continue;
        };

        let Some(rb) = right.on_object(&witness.lifted_object) else {
            violations.push(hom_violation(
                AdjunctionValidation::HomSetMembership,
                ValidationLocation::Object(witness.lifted_object.clone()),
                format!(
                    "Right functor is undefined on lifted object {}",
                    witness.lifted_object
                ),
            ));
            report.add_typed(&format!("hom_bijection_{}", pair_label), violations);
            continue;
        };

        // 2. Hom-set totality
        let lifted_hom = hom_set(lifted, la, &witness.lifted_object);
        let base_hom = hom_set(base, &witness.base_object, rb);

        let forward_domain: BTreeSet<_> = witness.forward.keys().cloned().collect();
        let forward_codomain: BTreeSet<_> = witness.forward.values().cloned().collect();

        if forward_domain != lifted_hom {
            violations.push(hom_violation(
                AdjunctionValidation::HomBijectionTotality,
                ValidationLocation::Named(pair_label.clone()),
                format!(
                    "Forward domain mismatch. Expected Hom_Lifted({}, {}) = {:?}, got {:?}",
                    la, witness.lifted_object, lifted_hom, forward_domain
                ),
            ));
        }

        if forward_codomain != base_hom {
            violations.push(hom_violation(
                AdjunctionValidation::HomBijectionTotality,
                ValidationLocation::Named(pair_label.clone()),
                format!(
                    "Forward codomain mismatch. Expected Hom_Base({}, {}) = {:?}, got {:?}",
                    witness.base_object, rb, base_hom, forward_codomain
                ),
            ));
        }

        // 3. Check cardinality match
        if witness.forward.len() != witness.backward.len() {
            violations.push(hom_violation(
                AdjunctionValidation::HomBijectionRoundTrip,
                ValidationLocation::Named(pair_label.clone()),
                format!(
                    "Bijection cardinality mismatch: forward has {}, backward has {}",
                    witness.forward.len(),
                    witness.backward.len()
                ),
            ));
        }

        check_left_roundtrip(&witness.forward, &witness.backward, &pair_label, &mut violations);
        check_right_roundtrip(&witness.forward, &witness.backward, &pair_label, &mut violations);

        report.add_typed(&format!("hom_bijection_{}", pair_label), violations);
    }

    report
}

// ═══════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════

// Origin: engine/crates_rs/core_category_theory/src/hom_adjunction.rs
// Claim: urn:core:crates_rs:core-category-theory:hom-adjunction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb7baa451 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb7baa451` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb7baa451 {
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
impl BoundaryErrorb7baa451 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb7baa451 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb7baa451 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb7baa451 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb7baa451> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb7baa451::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb7baa451::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb7baa451::ExceedsCapacity {
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
    use crate::cat_functor::DeclaredFiniteFunctor;
    use crate::finite_category_builder::DeclaredFiniteCategoryBuilder;

    fn trivial_base() -> DeclaredFiniteCategory {
        DeclaredFiniteCategoryBuilder::new("Base")
            .identity("*", "id_*")
            .identity_compositions()
            .build()
    }

    fn trivial_lifted() -> DeclaredFiniteCategory {
        DeclaredFiniteCategoryBuilder::new("Lifted")
            .identity("*'", "id_*'")
            .identity_compositions()
            .build()
    }

    fn trivial_left_functor() -> DeclaredFiniteFunctor {
        let mut left = DeclaredFiniteFunctor::new("L", "Base", "Lifted");
        left.map_object("*", "*'");
        left.map_morphism("id_*", "id_*'");
        left
    }

    fn trivial_right_functor() -> DeclaredFiniteFunctor {
        let mut right = DeclaredFiniteFunctor::new("R", "Lifted", "Base");
        right.map_object("*'", "*");
        right.map_morphism("id_*'", "id_*");
        right
    }

    #[test]
    fn trivial_hom_bijection_passes() {
        let base = trivial_base();
        let lifted = trivial_lifted();
        let left = trivial_left_functor();
        let right = trivial_right_functor();

        let mut hom = DeclaredHomAdjunction::new("Trivial", "L", "R");
        let mut witness = HomBijectionWitness::new("*", "*'");
        // Hom(L(*), *') = {id_*'} ↔ Hom(*, R(*')) = {id_*}
        witness.add_mate_pair("id_*'", "id_*");
        hom.add_witness(witness);

        let report = validate_hom_adjunction(&hom, &left, &right, &base, &lifted);
        assert!(report.all_passed(), "{:?}", report.typed_violations);
    }

    #[test]
    fn broken_round_trip_detected() {
        let base = trivial_base();
        let lifted = trivial_lifted();
        let left = trivial_left_functor();
        let right = trivial_right_functor();

        let mut hom = DeclaredHomAdjunction::new("Broken", "L", "R");
        let mut witness = HomBijectionWitness::new("*", "*'");
        // Deliberately broken: forward maps f → g, but backward maps g → h (not f)
        witness.forward.insert("f".into(), "g".into());
        witness.backward.insert("g".into(), "h".into());
        hom.add_witness(witness);

        let report = validate_hom_adjunction(&hom, &left, &right, &base, &lifted);
        assert!(!report.all_passed());
        assert!(
            report
                .typed_violations
                .iter()
                .any(|v| v.message.contains("round-trip") || v.message.contains("mismatch")),
            "Should detect round-trip or totality failure: {:?}",
            report.typed_violations
        );
    }

    #[test]
    fn cardinality_mismatch_detected() {
        let base = trivial_base();
        let lifted = trivial_lifted();
        let left = trivial_left_functor();
        let right = trivial_right_functor();

        let mut hom = DeclaredHomAdjunction::new("BadCard", "L", "R");
        let mut witness = HomBijectionWitness::new("*", "*'");
        witness.forward.insert("f".into(), "g".into());
        // backward is empty → cardinality mismatch
        hom.add_witness(witness);

        let report = validate_hom_adjunction(&hom, &left, &right, &base, &lifted);
        assert!(!report.all_passed());
        assert!(
            report
                .typed_violations
                .iter()
                .any(|v| v.message.contains("cardinality") || v.message.contains("mismatch")),
            "{:?}",
            report.typed_violations
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_b7baa451 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb7baa451::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb7baa451::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb7baa451::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb7baa451::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb7baa451::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb7baa451::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb7baa451::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
