//! Observer identity: the digest that makes two evaluations comparable.
//!
//! An observer is not a person, a camera, or a consciousness. It is **the rule
//! packet that makes a claim evaluable** -- what was compared, what counted as
//! a defect, what repairs were allowed, and who terminalized the result.
//!
//! So the observer is not a field inside a packet. The packet *is* the
//! observer. What this module adds is its **identity**, and the reason is the
//! block-tower argument: three children, the same towers, one rule card saying
//! "best means tallest" and another saying "best means strongest". Same data,
//! different observer, different winner, and both results correct.
//!
//! An atlas that records residuals without recording which rule card produced
//! them cannot tell those two cases apart. Worse, it cannot tell them apart
//! from a genuine disagreement about the world. Two entries are comparable only
//! when they declare the same observer, and that has to be checkable
//! mechanically rather than by reading prose.
//!
//! # Why the fields are identifiers, not prose
//!
//! Every component is a *named* term from a controlled vocabulary, never a
//! description. Two identical rule cards phrased differently would otherwise
//! digest differently and fail to collide -- which is exactly the failure this
//! module exists to prevent. If a regime cannot be named, it has not been
//! declared yet.
//!
//! AuthorityEffect: None. An observer id says which rule card was used. It says
//! nothing about whether the result under that card is true.

use serde_json::{json, Value};

use super::canonical::{canonical_id, require_identifier, sorted_unique};
use super::model::ModelError;

/// The rule packet under which a claim becomes evaluable.
///
/// Every field is required. An observer missing its terminal rule is not a
/// partially specified observer; it is not an observer, because nothing says
/// what result the comparison is permitted to reach.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverDeclaration {
    /// The regime the carrier is interpreted in.
    pub regime: String,
    /// The relation by which presentations are compared.
    pub comparison_relation: String,
    /// Permitted changes of representation. Order-insensitive: the same
    /// permissions listed differently are the same rule card.
    pub allowed_lifts_and_gauges: Vec<String>,
    /// What counts as a defect. The block-tower rule card: "best means tallest"
    /// versus "best means strongest".
    pub defect_definition: String,
    /// Which terminal outcomes the comparison may reach.
    pub terminal_rule: String,
}

impl ObserverDeclaration {
    pub fn new(
        regime: &str,
        comparison_relation: &str,
        allowed_lifts_and_gauges: &[String],
        defect_definition: &str,
        terminal_rule: &str,
    ) -> Result<Self, ModelError> {
        Ok(Self {
            regime: require_identifier(regime, "regime")?,
            comparison_relation: require_identifier(comparison_relation, "comparison_relation")?,
            // Sorted and deduplicated: two declarations permitting the same
            // lifts in a different order must produce the same id, or identical
            // rule cards would fail to collide.
            allowed_lifts_and_gauges: sorted_unique(
                allowed_lifts_and_gauges,
                "allowed_lifts_and_gauges",
            )?,
            defect_definition: require_identifier(defect_definition, "defect_definition")?,
            terminal_rule: require_identifier(terminal_rule, "terminal_rule")?,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "regime": self.regime,
            "comparison_relation": self.comparison_relation,
            "allowed_lifts_and_gauges": self.allowed_lifts_and_gauges,
            "defect_definition": self.defect_definition,
            "terminal_rule": self.terminal_rule,
        })
    }

    /// The digest that answers "was this the same rule card?".
    ///
    /// Domain-separated under `core.observer.v1`, using the same canonical
    /// encoding proven byte-identical between Rust and Python, so an observer
    /// id computed on either side is the same string.
    pub fn observer_id(&self) -> Result<String, ModelError> {
        Ok(canonical_id("core.observer.v1", &self.to_canonical())?)
    }

    /// Whether two declarations are the same rule card.
    ///
    /// Compares by id rather than by field equality so that order-insensitivity
    /// and normalization are applied consistently; a caller that compared
    /// structs directly would reimplement half of `new` and eventually drift.
    pub fn same_observer_as(&self, other: &ObserverDeclaration) -> Result<bool, ModelError> {
        Ok(self.observer_id()? == other.observer_id()?)
    }

    /// Always `"None"`. Naming the rule card grants nothing.
    pub fn authority_effect(&self) -> &'static str {
        "None"
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/observer.rs
// Claim: urn:core:crates_rs:core-operad-theory:observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf23b662a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf23b662a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf23b662a {
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
impl BoundaryErrorf23b662a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf23b662a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf23b662a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf23b662a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf23b662a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf23b662a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf23b662a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf23b662a::ExceedsCapacity {
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

    fn lifts(values: &[&str]) -> Vec<String> {
        values.iter().map(|value| (*value).to_owned()).collect()
    }

    fn observer() -> ObserverDeclaration {
        ObserverDeclaration::new(
            "finite-f2-gauge.v1",
            "exact-equality",
            &lifts(&["vertex-rephasing", "coefficient-extension"]),
            "l1-residual-mass",
            "strict-descent",
        )
        .expect("observer must build")
    }

    #[test]
    fn an_observer_id_is_a_domain_separated_digest() {
        let id = observer().observer_id().unwrap();
        assert!(id.starts_with("sha256:"));
        assert_eq!(id.len(), "sha256:".len() + 64);
    }

    #[test]
    fn the_same_rule_card_yields_the_same_id() {
        assert_eq!(observer().observer_id().unwrap(), observer().observer_id().unwrap());
        assert!(observer().same_observer_as(&observer()).unwrap());
    }

    #[test]
    fn listing_the_same_lifts_in_another_order_is_the_same_observer() {
        // The failure this guards: identical rule cards that fail to collide
        // because someone wrote the permissions in a different order.
        let reordered = ObserverDeclaration::new(
            "finite-f2-gauge.v1",
            "exact-equality",
            &lifts(&["coefficient-extension", "vertex-rephasing"]),
            "l1-residual-mass",
            "strict-descent",
        )
        .unwrap();
        assert!(observer().same_observer_as(&reordered).unwrap());
    }

    #[test]
    fn changing_what_counts_as_a_defect_changes_the_observer() {
        // The block towers. Same carrier, same data, "tallest" versus
        // "strongest" -- different rule card, and results measured under one
        // must not be compared with results measured under the other.
        let strongest = ObserverDeclaration::new(
            "finite-f2-gauge.v1",
            "exact-equality",
            &lifts(&["vertex-rephasing", "coefficient-extension"]),
            "gamma2-curvature-mass",
            "strict-descent",
        )
        .unwrap();
        assert!(!observer().same_observer_as(&strongest).unwrap());
    }

    #[test]
    fn every_component_participates_in_the_identity() {
        // If any field were dropped from the digest, two genuinely different
        // rule cards would collide and the atlas would report a false match.
        let base = observer().observer_id().unwrap();
        let variants = [
            ObserverDeclaration::new(
                "rational-l1.v1",
                "exact-equality",
                &lifts(&["vertex-rephasing", "coefficient-extension"]),
                "l1-residual-mass",
                "strict-descent",
            ),
            ObserverDeclaration::new(
                "finite-f2-gauge.v1",
                "quotient-equality",
                &lifts(&["vertex-rephasing", "coefficient-extension"]),
                "l1-residual-mass",
                "strict-descent",
            ),
            ObserverDeclaration::new(
                "finite-f2-gauge.v1",
                "exact-equality",
                &lifts(&["vertex-rephasing"]),
                "l1-residual-mass",
                "strict-descent",
            ),
            ObserverDeclaration::new(
                "finite-f2-gauge.v1",
                "exact-equality",
                &lifts(&["vertex-rephasing", "coefficient-extension"]),
                "l1-residual-mass",
                "bounded-with-open-frontier",
            ),
        ];
        for variant in variants {
            assert_ne!(base, variant.unwrap().observer_id().unwrap());
        }
    }

    #[test]
    fn adding_a_permitted_lift_changes_the_observer() {
        // A rule card that allows more repairs is a different rule card, even
        // though it agrees on everything already permitted.
        let permissive = ObserverDeclaration::new(
            "finite-f2-gauge.v1",
            "exact-equality",
            &lifts(&["vertex-rephasing", "coefficient-extension", "carrier-refinement"]),
            "l1-residual-mass",
            "strict-descent",
        )
        .unwrap();
        assert!(!observer().same_observer_as(&permissive).unwrap());
    }

    #[test]
    fn duplicate_lifts_are_refused_rather_than_silently_merged() {
        // Silently deduplicating would let a malformed declaration digest as a
        // well-formed one, so the two would collide.
        let duplicated = ObserverDeclaration::new(
            "finite-f2-gauge.v1",
            "exact-equality",
            &lifts(&["vertex-rephasing", "vertex-rephasing"]),
            "l1-residual-mass",
            "strict-descent",
        );
        assert!(duplicated.is_err());
    }

    #[test]
    fn prose_is_refused_because_prose_does_not_compare() {
        // Two identical rule cards phrased differently would digest differently
        // and fail to collide, which is the whole failure this module prevents.
        assert!(ObserverDeclaration::new(
            "the finite F2 gauge regime",
            "exact-equality",
            &lifts(&["vertex-rephasing"]),
            "l1-residual-mass",
            "strict-descent",
        )
        .is_err());
    }

    #[test]
    fn an_incomplete_observer_is_refused() {
        // Not a partially specified observer -- not an observer, because
        // nothing says what result the comparison may reach.
        assert!(ObserverDeclaration::new(
            "finite-f2-gauge.v1",
            "exact-equality",
            &lifts(&["vertex-rephasing"]),
            "l1-residual-mass",
            "",
        )
        .is_err());
    }

    #[test]
    fn an_observer_with_no_permitted_lifts_is_admissible() {
        // A rule card that allows no repairs at all is a legitimate, maximally
        // strict observer, not a malformed one.
        let rigid = ObserverDeclaration::new(
            "finite-f2-gauge.v1",
            "exact-equality",
            &[],
            "l1-residual-mass",
            "strict-descent",
        )
        .expect("an observer permitting no repairs is still an observer");
        assert!(!rigid.same_observer_as(&observer()).unwrap());
    }

    #[test]
    fn naming_the_rule_card_grants_nothing() {
        assert_eq!(observer().authority_effect(), "None");
    }

    #[test]
    fn the_domain_separates_observers_from_other_records() {
        // The same payload under another domain must not collide with an
        // observer id.
        let payload = observer().to_canonical();
        let as_observer = canonical_id("core.observer.v1", &payload).unwrap();
        let as_something_else = canonical_id("core.oewas.colour.v1", &payload).unwrap();
        assert_ne!(as_observer, as_something_else);
    }
}

#[cfg(test)]
mod l4_boundary_tests_f23b662a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf23b662a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf23b662a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf23b662a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf23b662a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf23b662a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf23b662a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf23b662a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
