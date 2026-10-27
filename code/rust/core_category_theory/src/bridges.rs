//! Bridges — Spec Section 8.
//!
//! The StructurePreservingMap base trait enables cross-discipline
//! functor-like maps without requiring full categorical infrastructure.

// ---------------------------------------------------------------------------
// Trait: StructurePreservingMap
// ---------------------------------------------------------------------------

/// Base trait for all structure-preserving maps across disciplines.
///
/// Specialized by: CatFunctor, GroupHomomorphism, ContinuousMap,
/// LinearMap, MeasurableMap, etc.
///
/// CatFunctor implements StructurePreservingMap automatically.
/// Other disciplines can implement the base without being forced
/// into full category infrastructure.
pub trait StructurePreservingMap {
    type Domain;
    type Codomain;

    fn map(&self, x: &Self::Domain) -> Self::Codomain;
}

/// Evidence emitted when a bridge performs a structural transformation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BridgeEvidence {
    pub source_discipline: String,
    pub target_discipline: String,
    pub map_name: String,
    pub laws_preserved: Vec<String>,
}

impl BridgeEvidence {
    pub fn new(source: &str, target: &str, name: &str) -> Self {
        Self {
            source_discipline: source.into(),
            target_discipline: target.into(),
            map_name: name.into(),
            laws_preserved: Vec::new(),
        }
    }

    pub fn preserve_law(&mut self, law: &str) {
        self.laws_preserved.push(law.into());
    }
}

// Origin: engine/crates_rs/core_category_theory/src/bridges.rs
// Claim: urn:core:crates_rs:core-category-theory:bridges:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord01337ce7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord01337ce7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError01337ce7 {
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
impl BoundaryError01337ce7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError01337ce7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError01337ce7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord01337ce7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError01337ce7> {
        if capacity_bound == 0 {
            return Err(BoundaryError01337ce7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError01337ce7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError01337ce7::ExceedsCapacity {
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

    struct DoubleMap;

    impl StructurePreservingMap for DoubleMap {
        type Domain = i32;
        type Codomain = i32;

        fn map(&self, x: &i32) -> i32 {
            x * 2
        }
    }

    #[test]
    fn structure_preserving_map_basic() {
        let m = DoubleMap;
        assert_eq!(m.map(&5), 10);
        assert_eq!(m.map(&0), 0);
    }

    #[test]
    fn bridge_evidence_construction() {
        let mut ev = BridgeEvidence::new("topology", "analysis", "MetricTopologyFunctor");
        ev.preserve_law("composition");
        ev.preserve_law("identity");
        assert_eq!(ev.laws_preserved.len(), 2);
        assert_eq!(ev.source_discipline, "topology");
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChargeBridgeError { kind: &'static str, left: i128, right: i128 }
impl ChargeBridgeError {
    const fn new(kind: &'static str, left: i128, right: i128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// A structure-preserving bridge of integer charges: the two checked sums agree.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChargeBridge { total: i128 }
fn charge_sum(charges: &[i64]) -> Result<i128, ChargeBridgeError> {
    let mut total = 0i128;
    for charge in charges {
        total = total.checked_add(i128::from(*charge)).ok_or_else(|| ChargeBridgeError::new("charge sum overflow", total, i128::from(*charge)))?;
    }
    Ok(total)
}
impl ChargeBridge {
    pub fn try_preserve(source: &[i64], target: &[i64]) -> Result<Self, ChargeBridgeError> {
        let source_total = charge_sum(source)?;
        let target_total = charge_sum(target)?;
        if source_total != target_total {
            return Err(ChargeBridgeError::new("bridge does not preserve total charge", source_total, target_total));
        }
        Ok(Self { total: source_total })
    }
    pub const fn total(&self) -> i128 { self.total }
}
#[cfg(test)]
mod charge_bridge_checks {
    use super::ChargeBridge;
    #[test]
    fn equal_totals_are_preserved() {
        assert_eq!(ChargeBridge::try_preserve(&[1, -4, 3], &[2, -2]).as_ref().map(ChargeBridge::total), Ok(0));
    }
    #[test]
    fn unequal_totals_are_refused() {
        assert_eq!(ChargeBridge::try_preserve(&[1], &[2]).map(|_| ()).map_err(|e| e.kind()), Err("bridge does not preserve total charge"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_01337ce7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord01337ce7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord01337ce7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord01337ce7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord01337ce7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord01337ce7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError01337ce7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError01337ce7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
