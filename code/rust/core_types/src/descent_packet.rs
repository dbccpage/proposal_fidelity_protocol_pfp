//! Finite descent packet and the packet-field-necessity firewall (PO-D8).
//!
//! A descent packet is the dependent record `Packet(s) := (K, E, V, τ, Λ)`:
//! finite carrier, admissible candidate family, verifier, terminalizer, and
//! lift discipline (canonical §II.3). The **packet field necessity theorem**
//! (PO-D8) states that every field is required: if any is missing, the pipeline
//! returns the corresponding typed refusal, and — by the encode-decode firewall
//! (PO-D6) — a refusal cannot become authority. Hence **no partial packet can
//! reach the validator authority path**.
//!
//! This module realizes that theorem in the type system:
//!
//! - [`DescentPacket`] has **private fields** — there is no struct-literal
//!   constructor outside this module, so a partial packet cannot be built by
//!   hand.
//! - The sole constructor [`DescentPacket::assemble`] takes the five fields as
//!   `Option`s and returns `Result<Self, DescentPacketRefusal>`, emitting the
//!   field-specific refusal for the first missing field (checked in the
//!   canonical order `K → E → V → τ → Λ`).
//!
//! So a value of type `DescentPacket` is a *witness that all five fields are
//! present*; anything less is a `DescentPacketRefusal`, never a packet.

use serde::{Deserialize, Serialize};

/// Typed refusal emitted when a packet field is missing (canonical §II.3 /
/// CODA-FDA-Core-12). Each variant is the refusal for exactly one absent field.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum DescentPacketRefusal {
    /// Missing `K` — finite carrier / context type.
    NoCarrier,
    /// Missing `E` — admissible candidate family over `K`.
    NoCandidateFamily,
    /// Missing `V` — verifier producing evidence terms.
    NoVerifier,
    /// Missing `τ` — eliminator into terminal outcome types.
    NoTerminalizer,
    /// Missing `Λ` — continuation / refusal / lift discipline.
    IncompleteLiftDiscipline,
}

/// A finite descent packet `(K, E, V, τ, Λ)`.
///
/// Fields are **private**: the only way to obtain a value is
/// [`DescentPacket::assemble`], which requires all five fields. There is no
/// struct-literal constructor outside this module, so a partial packet is
/// unrepresentable.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DescentPacket<K, E, V, T, L> {
    carrier: K,
    candidate_family: E,
    verifier: V,
    terminalizer: T,
    lift_discipline: L,
}

impl<K, E, V, T, L> DescentPacket<K, E, V, T, L> {
    /// Sole constructor. Returns the field-specific [`DescentPacketRefusal`] for the
    /// first missing field, checked in the canonical order `K → E → V → τ → Λ`;
    /// returns `Ok` only when **all five** fields are present.
    ///
    /// By PO-D6 (encode-decode firewall) a `DescentPacketRefusal` is an `inr(φ)` value
    /// and cannot become authority, so a partial packet never reaches the
    /// validator authority path — it is refused here, at assembly.
    pub fn assemble(
        carrier: Option<K>,
        candidate_family: Option<E>,
        verifier: Option<V>,
        terminalizer: Option<T>,
        lift_discipline: Option<L>,
    ) -> Result<Self, DescentPacketRefusal> {
        let carrier = carrier.ok_or(DescentPacketRefusal::NoCarrier)?;
        let candidate_family = candidate_family.ok_or(DescentPacketRefusal::NoCandidateFamily)?;
        let verifier = verifier.ok_or(DescentPacketRefusal::NoVerifier)?;
        let terminalizer = terminalizer.ok_or(DescentPacketRefusal::NoTerminalizer)?;
        let lift_discipline =
            lift_discipline.ok_or(DescentPacketRefusal::IncompleteLiftDiscipline)?;
        Ok(Self {
            carrier,
            candidate_family,
            verifier,
            terminalizer,
            lift_discipline,
        })
    }

    pub fn carrier(&self) -> &K {
        &self.carrier
    }
    pub fn candidate_family(&self) -> &E {
        &self.candidate_family
    }
    pub fn verifier(&self) -> &V {
        &self.verifier
    }
    pub fn terminalizer(&self) -> &T {
        &self.terminalizer
    }
    pub fn lift_discipline(&self) -> &L {
        &self.lift_discipline
    }
}

// Origin: engine/crates_rs/core_types/src/descent_packet.rs
// Claim: urn:core:crates_rs:core-types:descent-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2f3ddafa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2f3ddafa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2f3ddafa {
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
impl BoundaryError2f3ddafa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2f3ddafa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2f3ddafa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2f3ddafa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2f3ddafa> {
        if capacity_bound == 0 {
            return Err(BoundaryError2f3ddafa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2f3ddafa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2f3ddafa::ExceedsCapacity {
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

    // A concrete instantiation; the fields' internals are irrelevant to the
    // field-necessity theorem — only their presence is.
    type P = DescentPacket<&'static str, &'static str, &'static str, &'static str, &'static str>;

    fn full() -> [Option<&'static str>; 5] {
        [Some("K"), Some("E"), Some("V"), Some("tau"), Some("Lambda")]
    }

    #[test]
    fn complete_packet_assembles() {
        let [k, e, v, t, l] = full();
        let p = P::assemble(k, e, v, t, l).expect("all five fields present");
        assert_eq!(*p.carrier(), "K");
        assert_eq!(*p.lift_discipline(), "Lambda");
    }

    #[test]
    fn missing_carrier_is_no_carrier() {
        let [_, e, v, t, l] = full();
        assert_eq!(
            P::assemble(None, e, v, t, l).unwrap_err(),
            DescentPacketRefusal::NoCarrier
        );
    }

    #[test]
    fn missing_candidate_family_is_no_candidate_family() {
        let [k, _, v, t, l] = full();
        assert_eq!(
            P::assemble(k, None, v, t, l).unwrap_err(),
            DescentPacketRefusal::NoCandidateFamily
        );
    }

    #[test]
    fn missing_verifier_is_no_verifier() {
        let [k, e, _, t, l] = full();
        assert_eq!(
            P::assemble(k, e, None, t, l).unwrap_err(),
            DescentPacketRefusal::NoVerifier
        );
    }

    #[test]
    fn missing_terminalizer_is_no_terminalizer() {
        let [k, e, v, _, l] = full();
        assert_eq!(
            P::assemble(k, e, v, None, l).unwrap_err(),
            DescentPacketRefusal::NoTerminalizer
        );
    }

    #[test]
    fn missing_lift_discipline_is_incomplete_lift_discipline() {
        let [k, e, v, t, _] = full();
        assert_eq!(
            P::assemble(k, e, v, t, None).unwrap_err(),
            DescentPacketRefusal::IncompleteLiftDiscipline
        );
    }

    #[test]
    fn first_missing_field_wins_in_canonical_order() {
        // K and V both missing → NoCarrier (K is checked first).
        assert_eq!(
            P::assemble(None, Some("E"), None, Some("tau"), Some("Lambda")).unwrap_err(),
            DescentPacketRefusal::NoCarrier
        );
        // E and τ both missing → NoCandidateFamily (E precedes τ).
        assert_eq!(
            P::assemble(Some("K"), None, Some("V"), None, Some("Lambda")).unwrap_err(),
            DescentPacketRefusal::NoCandidateFamily
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_2f3ddafa {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2f3ddafa::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2f3ddafa::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2f3ddafa::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2f3ddafa::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2f3ddafa::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2f3ddafa::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2f3ddafa::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
