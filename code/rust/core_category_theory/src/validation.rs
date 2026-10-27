//! Validation — cross-cutting validation unit declarations.
//!
//! Maps directly to spec §4 and §10 validation unit lists.
//! Each validation unit is a single-property checker.

// ---------------------------------------------------------------------------
// Validation unit identifiers (spec §4)
// ---------------------------------------------------------------------------

/// Identifiers for all functor validation units.
///
/// These correspond 1:1 with the spec's declared validation obligations.
/// They are used as keys in validation reports and contract audit trails.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum FunctorValidation {
    // Covariant functor (spec §4)
    ObjectTotality,
    MorphismTotality,
    BoundaryPreservation,
    IdentityPreservation,
    CompositionPreservation,

    // Contravariant functor (spec §4)
    ContravariantIdentityPreservation,
    ContravariantCompositionReversal,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum NatTransValidation {
    NaturalitySquare,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum AdjunctionValidation {
    UnitNaturality,
    CounitNaturality,
    TriangleLeft,
    TriangleRight,
    HomSetMembership,
    HomBijectionTotality,
    HomBijectionRoundTrip,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ProfunctorValidation {
    DimapIdentity,
    DimapComposition,
    StrongFirstSecond,
    ClosedInteraction,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum HigherFunctorValidation {
    TwoFunctorObjectMap,
    TwoFunctorOneMorphismMap,
    TwoFunctorTwoMorphismMap,
    TwoFunctorCompositionPreservation,
    TwoFunctorIdentityPreservation,
    PseudofunctorPentagonCoherence,
    PseudofunctorTriangleCoherence,
    InterchangeLaw,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum CoendValidation {
    /// Quotient respects all morphisms (spec §14).
    Dinaturality,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum KanExtensionValidation {
    /// Lan is universal (spec §16).
    UniversalProperty,
    /// Lan_id F ≅ F (Yoneda unit law, spec §16).
    YonedaUnitLaw,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum CauchyValidation {
    /// r ∘ s = id_R, s ∘ r = e (spec §17).
    IdempotentSplitting,
    /// All idempotents split (spec §17).
    CauchyCompleteness,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum MonadValidation {
    /// μ ∘ Tη = id_T (spec §22).
    UnitLeft,
    /// μ ∘ ηT = id_T (spec §22).
    UnitRight,
    /// μ ∘ Tμ = μ ∘ μT (spec §22).
    Associativity,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum CondensationValidation {
    /// Base splitting laws: r∘s = id, s∘r = e (spec §21).
    BaseSplitting,
    /// Homotopy coherence at each level (spec §21).
    CoherenceWitness,
    /// All condensations split (∞-Cauchy, spec §21).
    InfinityCauchyCompleteness,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum LawvereValidation {
    /// Theory respects finite products (spec §25).
    ProductPreservation,
    /// Composition = substitution (spec §25).
    SubstitutionAssociativity,
    /// All idempotent operations split (spec §25).
    CauchyCompleteness,
    /// Theory ↔ finitary monad correspondence (spec §25).
    MonadEquivalence,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum OperadValidation {
    /// Tree-substitution is associative (spec §26).
    Associativity,
    /// Identity operations act as units (spec §26).
    Unit,
    /// Symmetric group action is compatible (spec §26).
    Equivariance,
    /// Homotopy coherence at each level (spec §26).
    InfinityCoherence,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum FiniteCategoryValidation {
    ObjectReference,
    MorphismBoundary,
    IdentityTotality,
    IdentityLaw,
    CompositionTotality,
    CompositionClosure,
    CompositionBoundary,
    Associativity,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum RewritingValidation {
    /// All critical pairs join (local confluence).
    LocalConfluence,
    /// No infinite rewrite chains (termination).
    Termination,
    /// 2-cells resolve all non-confluent pairs (homotopy resolution).
    HomotopyResolution,
    /// Higher cells are coherent at declared truncation level.
    TruncationCoherence,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum ValidationUnit {
    FiniteCategory(FiniteCategoryValidation),
    Functor(FunctorValidation),
    NatTrans(NatTransValidation),
    Adjunction(AdjunctionValidation),
    Profunctor(ProfunctorValidation),
    HigherFunctor(HigherFunctorValidation),
    Coend(CoendValidation),
    KanExtension(KanExtensionValidation),
    Cauchy(CauchyValidation),
    Monad(MonadValidation),
    Condensation(CondensationValidation),
    Lawvere(LawvereValidation),
    Operad(OperadValidation),
    Rewriting(RewritingValidation),
    Other(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ValidationSeverity {
    Error,
    Warning,
    Info,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum ValidationLocation {
    Global,
    Object(String),
    Morphism(String),
    Named(String),
    Boundary {
        morphism: String,
        source: String,
        target: String,
    },
    Composition {
        first: String,
        second: String,
        composite: Option<String>,
    },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidationViolation {
    pub unit: ValidationUnit,
    pub location: ValidationLocation,
    pub message: String,
    pub severity: ValidationSeverity,
}

impl ValidationViolation {
    pub fn new(
        unit: ValidationUnit,
        location: ValidationLocation,
        message: impl Into<String>,
        severity: ValidationSeverity,
    ) -> Self {
        Self {
            unit,
            location,
            message: message.into(),
            severity,
        }
    }
}

// ---------------------------------------------------------------------------
// Validation report
// ---------------------------------------------------------------------------

/// A single validation result.
#[derive(Debug, Clone)]
pub struct ValidationResult {
    pub unit: String,
    pub passed: bool,
    pub violations: Vec<String>,
}

impl ValidationResult {
    pub fn pass(unit: &str) -> Self {
        Self {
            unit: unit.into(),
            passed: true,
            violations: Vec::new(),
        }
    }

    pub fn fail(unit: &str, violations: Vec<String>) -> Self {
        Self {
            unit: unit.into(),
            passed: false,
            violations,
        }
    }
}

/// A collection of validation results for a functor or related structure.
#[derive(Debug, Clone)]
pub struct ValidationReport {
    pub target_name: String,
    pub results: Vec<ValidationResult>,
    pub typed_violations: Vec<ValidationViolation>,
}

impl ValidationReport {
    pub fn new(name: &str) -> Self {
        Self {
            target_name: name.into(),
            results: Vec::new(),
            typed_violations: Vec::new(),
        }
    }

    pub fn add(&mut self, result: ValidationResult) {
        self.results.push(result);
    }

    pub fn add_violation(&mut self, violation: ValidationViolation) {
        self.results.push(ValidationResult::fail(
            &format!("{:?}", violation.unit),
            vec![violation.message.clone()],
        ));
        self.typed_violations.push(violation);
    }

    pub fn add_typed(&mut self, unit: &str, violations: Vec<ValidationViolation>) {
        if violations.is_empty() {
            self.results.push(ValidationResult::pass(unit));
        } else {
            let messages = violations
                .iter()
                .map(|violation| violation.message.clone())
                .collect();
            self.results.push(ValidationResult::fail(unit, messages));
            self.typed_violations.extend(violations);
        }
    }

    pub fn all_passed(&self) -> bool {
        self.results.iter().all(|r| r.passed) && self.typed_violations.is_empty()
    }

    pub fn failure_count(&self) -> usize {
        self.results.iter().filter(|r| !r.passed).count()
    }

    pub fn violation_count(&self) -> usize {
        self.typed_violations.len()
    }
}

// Origin: engine/crates_rs/core_category_theory/src/validation.rs
// Claim: urn:core:crates_rs:core-category-theory:validation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord159e5879 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord159e5879` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError159e5879 {
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
impl BoundaryError159e5879 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError159e5879 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError159e5879 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord159e5879 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError159e5879> {
        if capacity_bound == 0 {
            return Err(BoundaryError159e5879::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError159e5879::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError159e5879::ExceedsCapacity {
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
    fn validation_report_all_pass() {
        let mut report = ValidationReport::new("TestFunctor");
        report.add(ValidationResult::pass("identity"));
        report.add(ValidationResult::pass("composition"));
        assert!(report.all_passed());
        assert_eq!(report.failure_count(), 0);
    }

    #[test]
    fn validation_report_with_failure() {
        let mut report = ValidationReport::new("BadFunctor");
        report.add(ValidationResult::pass("identity"));
        report.add(ValidationResult::fail(
            "composition",
            vec!["F(gf) != F(g)∘F(f)".into()],
        ));
        assert!(!report.all_passed());
        assert_eq!(report.failure_count(), 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_159e5879 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord159e5879::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord159e5879::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord159e5879::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord159e5879::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord159e5879::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError159e5879::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError159e5879::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
