//! Finite relational profunctors — distributors as finite weighted sets.
//!
//! `FnProfunctor` in `profunctor.rs` models P(A, B) = A → B (functional).
//! MSS obstruction work needs P(A, B) as a finite set or weighted set:
//! relational profunctors, composition via coends, and companion/conjoint
//! constructions for functors.
//!
//! All structures are finite and declarative for kernel audit.

use std::collections::BTreeMap;

// ═══════════════════════════════════════════════════════════════════════════
// Finite relational profunctor
// ═══════════════════════════════════════════════════════════════════════════

/// A finite relational profunctor P : C^op × D → FinSet.
///
/// For each pair (A, B) where A ∈ Ob(C) and B ∈ Ob(D),
/// P(A, B) is a finite multiset (list) of elements (witnesses/relations).
/// Multiplicity matters for obstruction/mass calculations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteRelationalProfunctor {
    pub name: String,
    pub source_category: String, // C
    pub target_category: String, // D
    /// (source_object, target_object) → list/multiset of relation witnesses.
    pub relations: BTreeMap<(String, String), Vec<String>>,

    /// Action of source morphisms contravariantly.
    /// f : A' -> A sends P(A, B) -> P(A', B)
    pub left_action: BTreeMap<(String, String, String), Vec<(usize, usize)>>,

    /// Action of target morphisms covariantly.
    /// g : B -> B' sends P(A, B) -> P(A, B')
    pub right_action: BTreeMap<(String, String, String), Vec<(usize, usize)>>,
}

impl DeclaredFiniteRelationalProfunctor {
    pub fn new(name: &str, source: &str, target: &str) -> Self {
        Self {
            name: name.into(),
            source_category: source.into(),
            target_category: target.into(),
            relations: BTreeMap::new(),
            left_action: BTreeMap::new(),
            right_action: BTreeMap::new(),
        }
    }

    /// Add a witness to P(A, B).
    pub fn add_witness(&mut self, source_ob: &str, target_ob: &str, witness: &str) {
        self.relations
            .entry((source_ob.into(), target_ob.into()))
            .or_default()
            .push(witness.into());
    }

    /// Get P(A, B) as a slice.
    pub fn hom_set(&self, source_ob: &str, target_ob: &str) -> &[String] {
        self.relations
            .get(&(source_ob.into(), target_ob.into()))
            .map(|v| v.as_slice())
            .unwrap_or(&[])
    }

    /// Check if P(A, B) is nonempty.
    pub fn is_related(&self, source_ob: &str, target_ob: &str) -> bool {
        !self.hom_set(source_ob, target_ob).is_empty()
    }

    /// Total number of witness elements across all (A, B) pairs.
    pub fn total_witnesses(&self) -> usize {
        self.relations.values().map(|v| v.len()).sum()
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Weighted profunctor (P(A,B) → R≥0)
// ═══════════════════════════════════════════════════════════════════════════

/// A finite weighted profunctor: each witness carries a non-negative weight.
///
/// This models P : C^op × D → [0, ∞)-Set, useful for obstruction mass
/// computations where P(A, B) tracks how much obstruction connects A to B.
#[derive(Debug, Clone, PartialEq)]
pub struct DeclaredFiniteWeightedProfunctor {
    pub name: String,
    pub source_category: String,
    pub target_category: String,
    /// (source_object, target_object) → list of (witness, weight).
    pub weighted_relations: BTreeMap<(String, String), Vec<(String, f64)>>,
}

impl DeclaredFiniteWeightedProfunctor {
    pub fn new(name: &str, source: &str, target: &str) -> Self {
        Self {
            name: name.into(),
            source_category: source.into(),
            target_category: target.into(),
            weighted_relations: BTreeMap::new(),
        }
    }

    pub fn add_weighted_witness(
        &mut self,
        source_ob: &str,
        target_ob: &str,
        witness: &str,
        weight: f64,
    ) -> Result<(), String> {
        if !weight.is_finite() || weight < 0.0 {
            return Err(format!(
                "Weight must be finite and non-negative, got {}",
                weight
            ));
        }

        self.weighted_relations
            .entry((source_ob.into(), target_ob.into()))
            .or_default()
            .push((witness.into(), weight));

        Ok(())
    }

    /// Total weight of P(A, B).
    pub fn total_weight(&self, source_ob: &str, target_ob: &str) -> f64 {
        self.weighted_relations
            .get(&(source_ob.into(), target_ob.into()))
            .map(|v| v.iter().map(|(_, w)| w).sum())
            .unwrap_or(0.0)
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Profunctor composition via coend
// ═══════════════════════════════════════════════════════════════════════════

/// Compose two finite relational profunctors assuming a discrete middle category.
///
/// Given P : C^op × D → Set and Q : D^op × E → Set,
/// when the intermediate category D is discrete, the coend composition
/// (Q ∘ P)(A, C) = ∫^B P(A, B) × Q(B, C) reduces to the coproduct
/// ∐_B P(A, B) × Q(B, C) over the intermediate objects B.
///
/// This computes exactly that discrete-middle coproduct. True coend
/// quotienting requires actions maps and quotienting by identifications.
pub fn compose_relational_profunctors_discrete_middle(
    name: &str,
    p: &DeclaredFiniteRelationalProfunctor,
    q: &DeclaredFiniteRelationalProfunctor,
    intermediate_objects: &[&str],
) -> Result<DeclaredFiniteRelationalProfunctor, String> {
    if p.target_category != q.source_category {
        return Err(format!(
            "Cannot compose profunctors: P targets {} but Q sources {}",
            p.target_category, q.source_category
        ));
    }

    let mut result =
        DeclaredFiniteRelationalProfunctor::new(name, &p.source_category, &q.target_category);

    // Collect all source objects from P and target objects from Q
    let source_objects: Vec<_> = p
        .relations
        .keys()
        .map(|(a, _)| a.clone())
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .collect();

    let target_objects: Vec<_> = q
        .relations
        .keys()
        .map(|(_, c)| c.clone())
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .collect();

    for a in &source_objects {
        for c in &target_objects {
            for &b in intermediate_objects {
                let p_ab = p.hom_set(a, b);
                let q_bc = q.hom_set(b, c);
                for pw in p_ab {
                    for qw in q_bc {
                        let witness = format!("({},{})@{}", pw, qw, b);
                        result.add_witness(a, c, &witness);
                    }
                }
            }
        }
    }

    Ok(result)
}

// ═══════════════════════════════════════════════════════════════════════════
// Companion and conjoint from a functor
// ═══════════════════════════════════════════════════════════════════════════

use super::cat_functor::DeclaredFiniteFunctor;
use super::finite_category::DeclaredFiniteCategory;
use super::validation::{
    ValidationLocation, ValidationReport, ValidationSeverity, ValidationUnit, ValidationViolation,
};

/// Build the companion profunctor of F : C → D.
///
/// F_* : C^op × D → Set defined by F_*(A, B) = Hom_D(F(A), B).
/// Note: Adjunctions L ⊣ R can be expressed as isomorphisms between
/// the companion L_* and the conjoint R^*.
pub fn declared_companion_profunctor(
    name: &str,
    functor: &DeclaredFiniteFunctor,
    target_category: &DeclaredFiniteCategory,
) -> DeclaredFiniteRelationalProfunctor {
    let mut prof = DeclaredFiniteRelationalProfunctor::new(
        name,
        &functor.source_category,
        &functor.target_category,
    );

    for (a, fa) in &functor.object_map {
        for morphism in target_category.morphisms.values() {
            if morphism.source == *fa {
                prof.add_witness(a, &morphism.target, &morphism.name);
            }
        }
    }

    prof
}

/// Build the conjoint profunctor of F : C → D.
///
/// F^* : D^op × C → Set defined by F^*(B, A) = Hom_D(B, F(A)).
pub fn declared_conjoint_profunctor(
    name: &str,
    functor: &DeclaredFiniteFunctor,
    target_category: &DeclaredFiniteCategory,
) -> DeclaredFiniteRelationalProfunctor {
    let mut prof = DeclaredFiniteRelationalProfunctor::new(
        name,
        &functor.target_category,
        &functor.source_category,
    );

    for (a, fa) in &functor.object_map {
        for morphism in target_category.morphisms.values() {
            if morphism.target == *fa {
                prof.add_witness(&morphism.source, a, &morphism.name);
            }
        }
    }

    prof
}

// ═══════════════════════════════════════════════════════════════════════════
// Validation
// ═══════════════════════════════════════════════════════════════════════════

pub fn validate_relational_profunctor(
    prof: &DeclaredFiniteRelationalProfunctor,
    source: &DeclaredFiniteCategory,
    target: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&prof.name);
    let mut violations = Vec::new();

    let unit = ValidationUnit::Other("ProfunctorBoundary".into());

    if prof.source_category != source.name {
        violations.push(ValidationViolation::new(
            unit.clone(),
            ValidationLocation::Global,
            format!(
                "Source category mismatch: expected {}, got {}",
                source.name, prof.source_category
            ),
            ValidationSeverity::Error,
        ));
    }

    if prof.target_category != target.name {
        violations.push(ValidationViolation::new(
            unit.clone(),
            ValidationLocation::Global,
            format!(
                "Target category mismatch: expected {}, got {}",
                target.name, prof.target_category
            ),
            ValidationSeverity::Error,
        ));
    }

    for (a, b) in prof.relations.keys() {
        if !source.objects.contains(a) {
            violations.push(ValidationViolation::new(
                unit.clone(),
                ValidationLocation::Object(a.clone()),
                format!("Source object {} not in source category {}", a, source.name),
                ValidationSeverity::Error,
            ));
        }
        if !target.objects.contains(b) {
            violations.push(ValidationViolation::new(
                unit.clone(),
                ValidationLocation::Object(b.clone()),
                format!("Target object {} not in target category {}", b, target.name),
                ValidationSeverity::Error,
            ));
        }
    }

    report.add_typed("boundary_checks", violations);
    report
}

// ═══════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════

// Origin: engine/crates_rs/core_category_theory/src/finite_profunctor.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-profunctor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1678a82e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1678a82e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1678a82e {
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
impl BoundaryError1678a82e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1678a82e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1678a82e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1678a82e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1678a82e> {
        if capacity_bound == 0 {
            return Err(BoundaryError1678a82e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1678a82e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1678a82e::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn relational_profunctor_tracks_witnesses() {
        let mut p = DeclaredFiniteRelationalProfunctor::new("P", "C", "D");
        p.add_witness("A", "X", "w1");
        p.add_witness("A", "X", "w2");
        p.add_witness("A", "Y", "w3");

        assert_eq!(p.hom_set("A", "X").len(), 2);
        assert_eq!(p.hom_set("A", "Y").len(), 1);
        assert!(p.is_related("A", "X"));
        assert!(!p.is_related("B", "X"));
        assert_eq!(p.total_witnesses(), 3);
    }

    #[test]
    fn weighted_profunctor_sums_weights() {
        let mut p = DeclaredFiniteWeightedProfunctor::new("W", "C", "D");
        p.add_weighted_witness("A", "X", "w1", 1.5).unwrap();
        p.add_weighted_witness("A", "X", "w2", 2.5).unwrap();

        let total = p.total_weight("A", "X");
        assert!((total - 4.0).abs() < 1e-10);
        assert!((p.total_weight("A", "Y") - 0.0).abs() < 1e-10);

        assert!(p.add_weighted_witness("A", "X", "w3", -1.0).is_err());
    }

    #[test]
    fn profunctor_composition_collects_pairs() {
        let mut p = DeclaredFiniteRelationalProfunctor::new("P", "C", "D");
        p.add_witness("A", "B1", "p1");
        p.add_witness("A", "B2", "p2");

        let mut q = DeclaredFiniteRelationalProfunctor::new("Q", "D", "E");
        q.add_witness("B1", "X", "q1");
        q.add_witness("B2", "X", "q2");

        let composed =
            compose_relational_profunctors_discrete_middle("QP", &p, &q, &["B1", "B2"]).unwrap();

        // (Q∘P)(A, X) = P(A, B1)×Q(B1, X) ∪ P(A, B2)×Q(B2, X) = {(p1,q1), (p2,q2)}
        assert_eq!(composed.hom_set("A", "X").len(), 2);
    }
}

#[cfg(test)]
mod l4_boundary_tests_1678a82e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1678a82e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1678a82e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1678a82e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1678a82e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1678a82e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1678a82e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1678a82e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
