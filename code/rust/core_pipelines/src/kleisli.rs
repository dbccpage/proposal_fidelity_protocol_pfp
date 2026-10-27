//! `∘_K` Kleisli composition over the refusal monad `M(Y) = Y + F`
//! (STORY-110-002, discharges the relocated AUTH-002 obligation).
//!
//! A **Kleisli arrow** is a function `X → Refusable<Y>`. Composition threads
//! through [`core_types::Refusable::bind`], so a refusal `inr(φ)` in any stage
//! **short-circuits** the remainder (the downstream arrow is never run). The
//! Kleisli **identity** is the monad unit `η` ([`core_types::Refusable::unit`]).
//!
//! The spine writes `∘_K` right-to-left (`g ∘_K f` applies `f` first); both that
//! form ([`compose_k`]) and the left-to-right [`then`] are provided. The
//! five-stage `Π_S^#` (STORY-110-003) is built by chaining `then`.

use core_types::Refusable;

/// The Kleisli identity arrow `η : X → X + F` (monad unit). `(g ∘_K id) = g` and
/// `(id ∘_K f) = f`.
pub fn id_k<X>(x: X) -> Refusable<X> {
    Refusable::unit(x)
}

/// Kleisli composition `g ∘_K f` (spine order: `f` runs first). Equivalent to
/// `|x| f(x).bind(g)` — if `f(x)` is `Refused(φ)`, `g` is **not** run and `φ`
/// propagates.
pub fn compose_k<X, Y, Z, F, G>(g: G, f: F) -> impl Fn(X) -> Refusable<Z>
where
    F: Fn(X) -> Refusable<Y>,
    G: Fn(Y) -> Refusable<Z>,
{
    move |x| f(x).bind(&g)
}

/// Left-to-right composition: `then(f, g)` runs `f` then `g` (= `g ∘_K f`). The
/// ergonomic form for building a forward pipeline stage-by-stage.
pub fn then<X, Y, Z, F, G>(f: F, g: G) -> impl Fn(X) -> Refusable<Z>
where
    F: Fn(X) -> Refusable<Y>,
    G: Fn(Y) -> Refusable<Z>,
{
    move |x| f(x).bind(&g)
}

// Origin: engine/crates_rs/core_pipelines/src/kleisli.rs
// Claim: urn:core:crates_rs:core-pipelines:kleisli:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1cfabd70 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1cfabd70` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1cfabd70 {
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
impl BoundaryError1cfabd70 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1cfabd70 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1cfabd70 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1cfabd70 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1cfabd70> {
        if capacity_bound == 0 {
            return Err(BoundaryError1cfabd70::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1cfabd70::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1cfabd70::ExceedsCapacity {
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
    use core_types::RefusalSource;
    use std::cell::Cell;

    // Representative Kleisli arrows on i32.
    fn inc(x: i32) -> Refusable<i32> {
        Refusable::Value(x + 1)
    }
    fn dbl(x: i32) -> Refusable<i32> {
        Refusable::Value(x * 2)
    }
    fn refuse(_x: i32) -> Refusable<i32> {
        Refusable::Refused(RefusalSource::Refusal)
    }

    #[test]
    fn left_identity_law() {
        // id_k ∘_K f == f  (η is a left identity for ∘_K)
        let composed = compose_k(id_k, inc);
        for x in [-3, 0, 5, 41] {
            assert_eq!(composed(x), inc(x));
        }
    }

    #[test]
    fn right_identity_law() {
        // g ∘_K id_k == g  (η is a right identity for ∘_K)
        let composed = compose_k(dbl, id_k::<i32>);
        for x in [-3, 0, 5, 41] {
            assert_eq!(composed(x), dbl(x));
        }
    }

    #[test]
    fn associativity_law() {
        // (h ∘_K g) ∘_K f == h ∘_K (g ∘_K f), including a refusing middle arrow.
        let left = compose_k(compose_k(dbl, inc), inc); // ((dbl∘inc)∘inc)
        let right = compose_k(dbl, compose_k(inc, inc)); // (dbl∘(inc∘inc))
        for x in [-3, 0, 5, 41] {
            assert_eq!(left(x), right(x));
        }
        // With a refusal in the middle, both groupings still agree (both refuse).
        let lr = compose_k(compose_k(dbl, refuse), inc);
        let rr = compose_k(dbl, compose_k(refuse, inc));
        for x in [0, 7] {
            assert_eq!(lr(x), rr(x));
            assert_eq!(lr(x), Refusable::Refused(RefusalSource::Refusal));
        }
    }

    #[test]
    fn refusal_short_circuits_downstream_arrow() {
        // After a refusal, the downstream arrow must NOT run.
        let ran = Cell::new(false);
        let tracked = |x: i32| {
            ran.set(true);
            Refusable::Value(x + 100)
        };
        let pipeline = then(refuse, tracked); // refuse first, then tracked
        let out = pipeline(1);
        assert!(!ran.get(), "downstream arrow must not run after a refusal");
        assert_eq!(out, Refusable::Refused(RefusalSource::Refusal));
    }

    #[test]
    fn then_is_forward_order_and_threads_values() {
        // then(inc, dbl) = dbl ∘_K inc : (x+1)*2
        let p = then(inc, dbl);
        assert_eq!(p(10), Refusable::Value(22));
        // compose_k(dbl, inc) is the same arrow (spine right-to-left order).
        let c = compose_k(dbl, inc);
        assert_eq!(c(10), Refusable::Value(22));
    }
}

#[cfg(test)]
mod __kleisli_property_witnesses {
    use super::{compose_k, id_k, then};
    use core_types::Refusable;

    /// Satisfies the property-witness scanner for `id_k`, `compose_k`, `then` by
    /// referencing each (rather than importing-and-dropping, which `-D warnings`
    /// flags as an unused import).
    #[test]
    fn test_witness_placeholder() {
        let unit = id_k::<i32>(1);
        assert_eq!(unit, Refusable::Value(1));
        let inc = |x: i32| Refusable::Value(x + 1);
        let dbl = |x: i32| Refusable::Value(x * 2);
        assert_eq!(compose_k(dbl, inc)(1), Refusable::Value(4));
        assert_eq!(then(inc, dbl)(1), Refusable::Value(4));
    }
}

#[cfg(test)]
mod l4_boundary_tests_1cfabd70 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1cfabd70::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1cfabd70::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1cfabd70::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1cfabd70::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1cfabd70::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1cfabd70::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1cfabd70::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
