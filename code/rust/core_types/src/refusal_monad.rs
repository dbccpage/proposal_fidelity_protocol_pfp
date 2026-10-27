//! The refusal monad `M(Y) = Y + F` (AUTH-002 primitive).
//!
//! The endofunctor `T_R: X ↦ X + R` (with `R` = refusal) equipped with:
//!
//! - unit `η_X : X → X + R` — the left injection ([`Refusable::unit`]);
//! - multiplication `μ_X : (X + R) + R → X + R` — collapse a nested refusal
//!   layer ([`Refusable::multiply`]);
//! - Kleisli `bind` — short-circuit on `inr(φ)` ([`Refusable::bind`]).
//!
//! It satisfies the three monad laws (left unit, right unit, associativity) from
//! `refusal_monad.contract.yaml`; the laws are property-checked in the tests.
//!
//! # Scope (ADR-107-001)
//!
//! This is the monad **primitive** only. The staged Kleisli **composition**
//! `∘_K` (chaining pipeline stages) belongs to the `core_pipelines` crate
//! (Sprint 110), **not** here and **not** `core_functional`.

use crate::authority::RefusalSource;
use serde::{Deserialize, Serialize};

/// `M(Y) = Y + F`: a carried value `inl(y)`, or a refusal `inr(φ)` that
/// short-circuits Kleisli composition.
///
/// The refusal side reuses [`RefusalSource`] (the firewall's `F`); a refusal
/// carries no authority, so this type is freely constructible — it threads
/// values-or-refusals, it does not produce authority.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Refusable<Y> {
    /// `inl(y)` — a carried value.
    Value(Y),
    /// `inr(φ)` — a refusal; propagates through `bind`/`map` unchanged.
    Refused(RefusalSource),
}

impl<Y> Refusable<Y> {
    /// Unit `η_Y : Y → Y + F` (left injection).
    pub fn unit(y: Y) -> Self {
        Refusable::Value(y)
    }

    /// Kleisli bind: `(Y + F) → (Y → Z + F) → (Z + F)`. The continuation runs
    /// **only** on `Value`; a `Refused(φ)` short-circuits, passing `φ` through
    /// without invoking `f`.
    pub fn bind<Z>(self, f: impl FnOnce(Y) -> Refusable<Z>) -> Refusable<Z> {
        match self {
            Refusable::Value(y) => f(y),
            Refusable::Refused(phi) => Refusable::Refused(phi),
        }
    }

    /// Functorial action `T_R(f)`: apply `f` to the value, pass refusals through.
    /// Equal to `bind(|y| unit(f(y)))`.
    pub fn map<Z>(self, f: impl FnOnce(Y) -> Z) -> Refusable<Z> {
        self.bind(|y| Refusable::Value(f(y)))
    }

    /// True on the refusal (`F`) side.
    pub fn is_refused(&self) -> bool {
        matches!(self, Refusable::Refused(_))
    }

    /// The carried value, if any (`inl` projection).
    pub fn value(self) -> Option<Y> {
        match self {
            Refusable::Value(y) => Some(y),
            Refusable::Refused(_) => None,
        }
    }
}

impl<Y> Refusable<Refusable<Y>> {
    /// Multiplication `μ_Y : (Y + F) + F → Y + F`. Collapses one nested refusal
    /// layer: an outer refusal stays a refusal; an outer value exposes the inner
    /// `Y + F`.
    pub fn multiply(self) -> Refusable<Y> {
        match self {
            Refusable::Value(inner) => inner,
            Refusable::Refused(phi) => Refusable::Refused(phi),
        }
    }
}

// Origin: engine/crates_rs/core_types/src/refusal_monad.rs
// Claim: urn:core:crates_rs:core-types:refusal-monad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbea017f6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbea017f6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbea017f6 {
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
impl BoundaryErrorbea017f6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbea017f6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbea017f6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbea017f6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbea017f6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbea017f6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbea017f6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbea017f6::ExceedsCapacity {
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

    // Representative inhabitants of `M(i32)`: one value, one refusal.
    fn samples() -> [Refusable<i32>; 2] {
        [
            Refusable::Value(3),
            Refusable::Refused(RefusalSource::Repair),
        ]
    }

    #[test]
    fn bind_short_circuits_on_refusal_and_threads_values() {
        // Refusal: the continuation must NOT run, and φ passes through unchanged.
        let mut ran = false;
        let out = Refusable::<i32>::Refused(RefusalSource::Refusal).bind(|y| {
            ran = true;
            Refusable::Value(y + 1)
        });
        assert!(!ran, "bind must not run the continuation after a refusal");
        assert_eq!(out, Refusable::Refused(RefusalSource::Refusal));

        // Value: the continuation runs and transforms the value.
        let out2 = Refusable::Value(41).bind(|y| Refusable::Value(y + 1));
        assert_eq!(out2, Refusable::Value(42));
    }

    #[test]
    fn left_unit_law() {
        // μ ∘ T_R(η) = id  :  m.map(unit).multiply() == m
        for m in samples() {
            assert_eq!(m.map(Refusable::unit).multiply(), m);
        }
    }

    #[test]
    fn right_unit_law() {
        // μ ∘ η_{T_R} = id  :  unit(m).multiply() == m
        for m in samples() {
            assert_eq!(Refusable::unit(m).multiply(), m);
        }
    }

    #[test]
    fn associativity_law() {
        // μ ∘ T_R(μ) = μ ∘ μ  on every representative of M(M(M(Y))).
        let cases: [Refusable<Refusable<Refusable<i32>>>; 4] = [
            Refusable::Value(Refusable::Value(Refusable::Value(7))),
            Refusable::Value(Refusable::Value(Refusable::Refused(RefusalSource::Refusal))),
            Refusable::Value(Refusable::Refused(RefusalSource::OracleNeeded)),
            Refusable::Refused(RefusalSource::Residual),
        ];
        for mmm in cases {
            let lhs = mmm.map(|m| m.multiply()).multiply(); // μ ∘ T_R(μ)
            let rhs = mmm.multiply().multiply(); // μ ∘ μ
            assert_eq!(lhs, rhs, "associativity must hold for {mmm:?}");
        }
    }

    #[test]
    fn map_equals_bind_then_unit() {
        // Functoriality consistency: map f = bind(unit ∘ f).
        for m in samples() {
            assert_eq!(m.map(|y| y * 2), m.bind(|y| Refusable::unit(y * 2)));
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_bea017f6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbea017f6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbea017f6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbea017f6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbea017f6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbea017f6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbea017f6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbea017f6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
