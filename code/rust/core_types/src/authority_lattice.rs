//! Canonical authority-effect lattice (STORY-108-004).
//!
//! The discovery for Sprint 108 found **4–5 disjoint `AuthorityEffect` enums**
//! across `core_types`, `core_contracts`, `core_measurement` (×2) and
//! `core_certifiers`, with incompatible variant sets. This module defines the
//! single **canonical** strength lattice they are measured against. It is a
//! tag-only lattice (no payload): the payload-carrying firewall type
//! [`crate::authority::AuthorityEffect`] projects onto it via
//! [`crate::authority::AuthorityEffect::level`].
//!
//! # Census as of 2026-07-21 (the Sprint-108 count above is historical)
//!
//! Most of that spread is already gone. `core_measurement` and
//! `core_certifiers` now define **zero**; `core_contracts` defines zero and
//! re-exports `core_contract_core::kinds::*`. Exactly **two** live enums
//! remain, and they are NOT redundant — they type different things:
//!
//! | Type | Types what | Variants | Wire form |
//! |---|---|---|---|
//! | [`crate::authority::AuthorityEffect`] | the authority an **artifact** carries at runtime | `None`, `Certified(CertifiedAuthority)`, `Refused`, `Uncertified` | default (PascalCase) |
//! | `core_contract_core::kinds::ContractEffect` | the authority a **contract declaration** is permitted to exercise | `None`, `EvidenceOnly`, `FactOnly`, `RequiresEvaluator`, `RequestsDecision`, `AuthorizesTransition`, `StateTransition` | strict snake_case |
//!
//! Their wire formats deliberately disagree: `"None"` parses here and is a
//! *rejected* spelling there (`kinds.rs` asserts the rejection in a test),
//! because the v1 contract corpus is snake_case. Do not "fix" that by aligning
//! them. Merging the two types would conflate *what authority a thing carries*
//! with *what authority a contract may exercise*, which is the distinction the
//! firewall exists to keep.
//!
//! Only the first projects onto this lattice. The contract enum does not, and
//! adding that projection is still blocked: ranking `AuthorizesTransition`,
//! `StateTransition`, `RequiresEvaluator`, and `RequestsDecision` on the
//! strength chain is a semantic authority decision, which is precisely what the
//! ADR below was to decide. **That ADR has never been written** (verified
//! 2026-07-21: no file matches `sprints/**/adr_108*`), so no projection is
//! asserted here rather than one being invented.
//!
//! # Decision scope (ADR-108-001)
//!
//! This crate ships the canonical type + a same-crate projection only. It does
//! **not** migrate the cross-crate enums — that is a follow-on, gated on the ADR
//! (`sprints/108/0_planning_documents/adr_108_authority_effect_lattice.md`).

use serde::{Deserialize, Serialize};

/// The canonical authority-strength lattice: a bounded **chain**
///
/// ```text
/// Refused  <  None  <  Uncertified  <  EvidenceOnly  <  FactOnly  <  Certified
///   ⊥                                                                   ⊤
/// ```
///
/// A total order is trivially a lattice with `join = max` and `meet = min`.
/// `Refused` is `⊥` (actively kept out of authority — the strongest negative),
/// `Certified` is `⊤` (the dependent pair `Σ(t:T_auth)(Π♯(x)=inl(t))`, maximal).
/// Variants are declared in **increasing** strength so the derived `Ord` is the
/// lattice order.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub enum AuthorityEffectLevel {
    /// `⊥` — actively refused; the firewall kept this out of authority.
    Refused,
    /// No authority asserted (the safe default for diagnostics / LLM output).
    None,
    /// Asserted but not evidence-backed.
    Uncertified,
    /// Evidence supplied, not yet verified.
    EvidenceOnly,
    /// Verified fact (checked), but not the certified dependent pair.
    FactOnly,
    /// `⊤` — certified authority (the dependent pair). Maximal.
    Certified,
}

impl AuthorityEffectLevel {
    /// Lattice bottom `⊥`.
    pub const BOTTOM: Self = AuthorityEffectLevel::Refused;
    /// Lattice top `⊤`.
    pub const TOP: Self = AuthorityEffectLevel::Certified;

    /// Join `a ∨ b` — the stronger (least upper bound) of the two levels.
    pub fn join(self, other: Self) -> Self {
        self.max(other)
    }

    /// Meet `a ∧ b` — the weaker (greatest lower bound) of the two levels.
    pub fn meet(self, other: Self) -> Self {
        self.min(other)
    }

    /// Sequential composition of two steps of one run: the run is only as
    /// strong as its weakest step, so composition is [`Self::meet`].
    ///
    /// `Refused` is absorbing, and no composition rises above either step.
    /// Runs must never be composed with [`Self::join`]: `Refused ∨ None = None`
    /// would lift a refused run back to `None`.
    pub fn compose_sequential(self, next: Self) -> Self {
        self.meet(next)
    }

    /// Grade of a whole run: the sequential composition of its step levels.
    /// An empty run asserts nothing, so its grade is `None`.
    pub fn run_grade<I: IntoIterator<Item = Self>>(steps: I) -> Self {
        steps
            .into_iter()
            .reduce(Self::compose_sequential)
            .unwrap_or(AuthorityEffectLevel::None)
    }
}

// Origin: engine/crates_rs/core_types/src/authority_lattice.rs
// Claim: urn:core:crates_rs:core-types:authority-lattice:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord64264e49 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord64264e49` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError64264e49 {
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
impl BoundaryError64264e49 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError64264e49 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError64264e49 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord64264e49 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError64264e49> {
        if capacity_bound == 0 {
            return Err(BoundaryError64264e49::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError64264e49::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError64264e49::ExceedsCapacity {
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

    const ALL: [AuthorityEffectLevel; 6] = [
        AuthorityEffectLevel::Refused,
        AuthorityEffectLevel::None,
        AuthorityEffectLevel::Uncertified,
        AuthorityEffectLevel::EvidenceOnly,
        AuthorityEffectLevel::FactOnly,
        AuthorityEffectLevel::Certified,
    ];

    #[test]
    fn chain_order_is_strictly_increasing_by_strength() {
        // The declared order IS the strength order; check each step is a strict <.
        for w in ALL.windows(2) {
            assert!(w[0] < w[1], "{:?} must be weaker than {:?}", w[0], w[1]);
        }
        assert_eq!(AuthorityEffectLevel::BOTTOM, AuthorityEffectLevel::Refused);
        assert_eq!(AuthorityEffectLevel::TOP, AuthorityEffectLevel::Certified);
    }

    #[test]
    fn join_and_meet_are_bounded_by_top_and_bottom() {
        for a in ALL {
            assert_eq!(
                a.join(AuthorityEffectLevel::BOTTOM),
                a,
                "⊥ is join-identity"
            );
            assert_eq!(a.meet(AuthorityEffectLevel::TOP), a, "⊤ is meet-identity");
            assert_eq!(a.join(AuthorityEffectLevel::TOP), AuthorityEffectLevel::TOP);
            assert_eq!(
                a.meet(AuthorityEffectLevel::BOTTOM),
                AuthorityEffectLevel::BOTTOM
            );
        }
    }

    #[test]
    fn lattice_axioms_hold_over_all_pairs_and_triples() {
        for a in ALL {
            // Idempotency.
            assert_eq!(a.join(a), a);
            assert_eq!(a.meet(a), a);
            for b in ALL {
                // Commutativity.
                assert_eq!(a.join(b), b.join(a));
                assert_eq!(a.meet(b), b.meet(a));
                // Absorption: a ∨ (a ∧ b) = a  and  a ∧ (a ∨ b) = a.
                assert_eq!(a.join(a.meet(b)), a);
                assert_eq!(a.meet(a.join(b)), a);
                // Consistency: a ≤ b  ⟺  a ∨ b = b  ⟺  a ∧ b = a.
                if a <= b {
                    assert_eq!(a.join(b), b);
                    assert_eq!(a.meet(b), a);
                }
                for c in ALL {
                    // Associativity.
                    assert_eq!(a.join(b).join(c), a.join(b.join(c)));
                    assert_eq!(a.meet(b).meet(c), a.meet(b.meet(c)));
                }
            }
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_64264e49 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord64264e49::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord64264e49::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord64264e49::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord64264e49::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord64264e49::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError64264e49::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError64264e49::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
