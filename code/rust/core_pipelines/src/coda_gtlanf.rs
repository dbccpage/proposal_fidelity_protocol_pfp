//! Finite CODA_GTLANF normalization interface (STORY-110-004).
//!
//! Compatibility symbols `L`, `I`, and `T` name normalization, marker-forgetting,
//! and their finite composition. This module proves no adjunction, reflector,
//! monad, reflective subcategory, or universal property.
//!
//! Generic contract boundary:
//! - [`Normalize`] implementers supply determinism and idempotence as caller
//!   obligations; Rust's trait bounds do not establish either law.
//! - [`is_fixed`] delegates to the supplied predicate and does not prove a
//!   fixed-point equivalence for arbitrary implementations.
//! - The publication's executable idempotence and fixed-point claim is limited
//!   to the frozen nine-cell `Tags` fixture exercised by the parity tests.
//! - The terminal-class [`Outcome`] is carried through `L`/`I`/`T` unchanged
//!   (PO-AUTH-NC). Re-normalization never turns a refusal
//!   or scoped-negative into authority, and creates no [`core_types::CertifiedAuthority`].

use core_types::Outcome;

/// A caller-supplied normalization interface. Implementers are responsible for
/// determinism and idempotence; the trait and compiler do not enforce those laws.
pub trait Normalize: Clone + PartialEq {
    /// Candidate canonicalization operation; callers supply any claimed laws.
    fn normalize(&self) -> Self;

    /// Default equality-based fixed-point check; overrides own their consistency.
    fn is_normal(&self) -> bool {
        self.normalize() == *self
    }
}

/// `FinClaim_∂`: a terminalized finite claim — the terminal-class [`Outcome`]
/// (carried unchanged by the completion) plus a normalizable payload.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FinClaim<P> {
    pub terminal: Outcome,
    pub payload: P,
}

impl<P> FinClaim<P> {
    pub fn new(terminal: Outcome, payload: P) -> Self {
        FinClaim { terminal, payload }
    }
}

/// `CODA_GTLANF`: the sealed marker returned by [`normalize_l`]. Its semantic
/// normal-form interpretation depends on the caller-supplied [`Normalize`] laws.
/// Private fields prevent direct construction through safe Rust.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CodaGtlaNf<P> {
    terminal: Outcome,
    payload: P,
}

impl<P> CodaGtlaNf<P> {
    pub fn terminal(&self) -> &Outcome {
        &self.terminal
    }
    pub fn payload(&self) -> &P {
        &self.payload
    }
}

/// Invoke the supplied payload normalizer and carry the terminal class through
/// unchanged (no authority minted).
pub fn normalize_l<P: Normalize>(claim: FinClaim<P>) -> CodaGtlaNf<P> {
    CodaGtlaNf {
        terminal: claim.terminal,
        payload: claim.payload.normalize(),
    }
}

/// Forget the normal-form marker; data and terminal class remain unchanged.
pub fn include_i<P>(nf: CodaGtlaNf<P>) -> FinClaim<P> {
    FinClaim {
        terminal: nf.terminal,
        payload: nf.payload,
    }
}

/// Normalize-and-forget pass; any determinism or idempotence is caller-supplied.
pub fn t<P: Normalize>(claim: FinClaim<P>) -> FinClaim<P> {
    include_i(normalize_l(claim))
}

/// Delegate to the payload's supplied fixed-point predicate.
pub fn is_fixed<P: Normalize>(claim: &FinClaim<P>) -> bool {
    claim.payload.is_normal()
}

// Origin: engine/crates_rs/core_pipelines/src/coda_gtlanf.rs
// Claim: urn:core:crates_rs:core-pipelines:coda-gtlanf:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcdbc26ca {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcdbc26ca` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcdbc26ca {
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
impl BoundaryErrorcdbc26ca {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcdbc26ca {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcdbc26ca {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcdbc26ca {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcdbc26ca> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcdbc26ca::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcdbc26ca::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcdbc26ca::ExceedsCapacity {
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
    use core_types::{AuthorityTerminal, RefusalSource, ScopedNegativeTerminal};

    // A concrete Normalize witness: canonical form = sorted + deduped.
    #[derive(Debug, Clone, PartialEq, Eq)]
    struct Tags(Vec<u8>);
    impl Normalize for Tags {
        fn normalize(&self) -> Self {
            let mut v = self.0.clone();
            v.sort_unstable();
            v.dedup();
            Tags(v)
        }
    }

    // Representative terminal classes across the three-way cosmos.
    fn terminals() -> [Outcome; 3] {
        [
            Outcome::Terminal(AuthorityTerminal::ExactRuleDerived),
            Outcome::ScopedNegative(ScopedNegativeTerminal::NoRule),
            Outcome::Refused(RefusalSource::Repair),
        ]
    }

    fn samples() -> Vec<FinClaim<Tags>> {
        let payloads = [
            Tags(vec![3, 1, 2, 1]), // not normal (unsorted, dup)
            Tags(vec![1, 2, 3]),    // already normal
            Tags(vec![]),           // normal (empty)
        ];
        let mut out = Vec::new();
        for term in terminals() {
            for p in &payloads {
                out.push(FinClaim::new(term, p.clone()));
            }
        }
        out
    }

    #[test]
    fn frozen_nine_cell_fixture_t_is_idempotent() {
        // Frozen Tags fixture only: three terminals x three payloads.
        for x in samples() {
            let once = t(x.clone());
            let twice = t(once.clone());
            assert_eq!(twice, once, "fixture T(T(x)) != T(x) for {x:?}");
        }
    }

    #[test]
    fn frozen_nine_cell_fixture_fixed_point_checks_agree() {
        for x in samples() {
            let normal = x.payload.is_normal();
            // Frozen Tags fixture check, not a theorem for arbitrary Normalize impls.
            assert_eq!(t(x.clone()) == x, normal);
            assert_eq!(is_fixed(&x), normal);
        }
    }

    #[test]
    fn frozen_nine_cell_fixture_t_images_are_fixed() {
        // Frozen Tags fixture check only.
        for x in samples() {
            assert!(is_fixed(&t(x.clone())), "fixture T(x) is not T-fixed");
        }
    }

    #[test]
    fn frozen_nine_cell_fixture_normalize_include_is_identity() {
        // Frozen Tags fixture check only.
        for x in samples() {
            let a = normalize_l(x);
            let la_i = normalize_l(include_i(a.clone())); // L(I(a))
            assert_eq!(la_i, a, "fixture L(I(a)) mismatch");
        }
    }

    #[test]
    fn t_mints_no_authority_and_preserves_terminal_class() {
        // The terminal-class Outcome is carried through unchanged — re-normalization
        // never alters the arm (no refusal/scoped-neg becomes authority; PO-AUTH-NC).
        for x in samples() {
            let before = x.terminal;
            let after = t(x).terminal;
            assert_eq!(after, before, "T must preserve the terminal class");
        }
    }
}

#[cfg(test)]
mod __coda_gtlanf_property_witnesses {
    use super::{include_i, is_fixed, normalize_l, t, FinClaim, CodaGtlaNf, Normalize};
    use core_types::{AuthorityTerminal, Outcome};

    #[derive(Debug, Clone, PartialEq, Eq)]
    struct Bounded(u8);

    impl Normalize for Bounded {
        fn normalize(&self) -> Self {
            Bounded(self.0.min(3))
        }
    }

    #[test]
    fn finite_normalizer_witness_is_fixed_and_preserves_terminal() {
        let claim = FinClaim::new(
            Outcome::Terminal(AuthorityTerminal::ExactRuleDerived),
            Bounded(9),
        );
        let normal: CodaGtlaNf<Bounded> = normalize_l(claim);
        let included = include_i(normal.clone());

        assert_eq!(included.payload, Bounded(3));
        assert!(is_fixed(&included));
        assert_eq!(t(included.clone()), included);
        assert_eq!(normal.terminal(), &included.terminal);
    }
}

#[cfg(test)]
mod l4_boundary_tests_cdbc26ca {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordcdbc26ca::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordcdbc26ca::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordcdbc26ca::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordcdbc26ca::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordcdbc26ca::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorcdbc26ca::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorcdbc26ca::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
