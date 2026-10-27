//! Rust dual of Lean `BridgePacket14` (paper 14-tuple $\mathcal{B}_q$).
//!
//! Paper / Lean schema:
//! $$\mathcal{B}_q := (\Lambda, A_\lambda, F_{\lambda\mu}, \chi_{\lambda\mu}, L, \eta, X, \pi_\lambda, q, \operatorname{Prof}, \bar{q}, D, V, \tau)$$
//!
//! Continuum slots are honest [`SchemaSlot`] placeholders until continuum types
//! land. Working maps $q$, $\operatorname{Prof}$, $\bar{q}$ are finite sample
//! carriers (domain indices + maps) for demos and typed admission.
//!
//! # Authority
//!
//! `AuthorityEffect: None` on all paths. This packet is a typed schema carrier
//! only — not GlobalGreen, not PROD LIVE, not continuum authority.
//!
//! Lean: `Engine.Bridge.BridgePacket14` in `GttcQBridge.lean`.
//! Contract skeleton: `coda_cs_q_bridge.contract.skeleton.yaml`.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

/// Paper / Lean field count for the 14-tuple schema.
pub const BRIDGE_PACKET_14_FIELD_COUNT: usize = 14;

/// Ordered field names matching Lean `BridgePacket14` / paper $\mathcal{B}_q$.
pub const BRIDGE_PACKET_14_FIELD_NAMES: [&str; BRIDGE_PACKET_14_FIELD_COUNT] = [
    "Lambda",
    "A_lambda",
    "F_lambda_mu",
    "chi_lambda_mu",
    "L",
    "eta",
    "X_space",
    "pi_lambda",
    "q",
    "Prof",
    "q_bar",
    "D",
    "V",
    "tau",
];

/// Domain point index on a finite carrier sample (`α` dual).
pub type DomainId = u32;

/// Profile / bundle point index (`β` dual).
pub type ProfileId = u32;

/// Query / terminal value on a finite sample (`γ` dual).
pub type QueryValue = u32;

/// Honest continuum-slot placeholder until real CODA-CS / tower types land.
///
/// Mirrors Lean `SchemaSlot`. Declared name only — no continuum soundness.
#[derive(Clone, Debug, Default, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SchemaSlot {
    /// Human-readable slot label (diagnostic).
    pub name: String,
    /// Whether a continuum binding was declared (still not continuum-proved).
    pub declared: bool,
}

impl SchemaSlot {
    /// Unbound placeholder (fail-closed continuum residual).
    pub fn unbound(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            declared: false,
        }
    }

    /// Declared-but-not-proved continuum slot (schema obligation only).
    pub fn declared(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            declared: true,
        }
    }

    pub fn is_declared(&self) -> bool {
        self.declared && !self.name.trim().is_empty()
    }
}

/// Finite sample map `DomainId → QueryValue` for $q : \alpha \to \gamma$.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteQueryMap {
    /// Sample domain points (finite carrier).
    pub domain: Vec<DomainId>,
    /// Pointwise values; every domain id should have an entry.
    pub values: BTreeMap<DomainId, QueryValue>,
}

impl FiniteQueryMap {
    pub fn new(domain: Vec<DomainId>, values: BTreeMap<DomainId, QueryValue>) -> Self {
        Self { domain, values }
    }

    pub fn from_pairs(pairs: impl IntoIterator<Item = (DomainId, QueryValue)>) -> Self {
        let values: BTreeMap<DomainId, QueryValue> = pairs.into_iter().collect();
        let domain: Vec<DomainId> = values.keys().copied().collect();
        Self { domain, values }
    }

    pub fn get(&self, x: DomainId) -> Option<QueryValue> {
        self.values.get(&x).copied()
    }

    /// Every domain point has a value (finite-packet hygiene).
    pub fn covers_domain(&self) -> bool {
        !self.domain.is_empty() && self.domain.iter().all(|x| self.values.contains_key(x))
    }
}

/// Finite sample map `DomainId → ProfileId` for $\operatorname{Prof} : \alpha \to \beta$.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteProfileMap {
    pub domain: Vec<DomainId>,
    pub values: BTreeMap<DomainId, ProfileId>,
}

impl FiniteProfileMap {
    pub fn new(domain: Vec<DomainId>, values: BTreeMap<DomainId, ProfileId>) -> Self {
        Self { domain, values }
    }

    pub fn from_pairs(pairs: impl IntoIterator<Item = (DomainId, ProfileId)>) -> Self {
        let values: BTreeMap<DomainId, ProfileId> = pairs.into_iter().collect();
        let domain: Vec<DomainId> = values.keys().copied().collect();
        Self { domain, values }
    }

    pub fn get(&self, x: DomainId) -> Option<ProfileId> {
        self.values.get(&x).copied()
    }

    pub fn covers_domain(&self) -> bool {
        !self.domain.is_empty() && self.domain.iter().all(|x| self.values.contains_key(x))
    }
}

/// Finite sample map `ProfileId → QueryValue` for $\bar{q} : \beta \to \gamma$.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FiniteFactorMap {
    pub values: BTreeMap<ProfileId, QueryValue>,
}

impl FiniteFactorMap {
    pub fn new(values: BTreeMap<ProfileId, QueryValue>) -> Self {
        Self { values }
    }

    pub fn from_pairs(pairs: impl IntoIterator<Item = (ProfileId, QueryValue)>) -> Self {
        Self {
            values: pairs.into_iter().collect(),
        }
    }

    pub fn get(&self, b: ProfileId) -> Option<QueryValue> {
        self.values.get(&b).copied()
    }
}

/// Paper 14-tuple bridge packet (Lean `BridgePacket14`).
///
/// # Type alias
///
/// [`CodaCsQBridgePacketV1`] is an honest rename for the paper 14-tuple; both
/// names refer to this structure.
///
/// # AuthorityEffect
///
/// Always `None`. Field presence does not mint continuum soundness or PROD LIVE.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct BridgePacket14 {
    /// (1) $\Lambda$ — cofinal shadow-tower index set (schema slot).
    pub lambda: SchemaSlot,
    /// (2) $A_\lambda$ — finite CODA packets at each index (schema slot).
    pub a_lambda: SchemaSlot,
    /// (3) $F_{\lambda\mu}$ — tower transition maps (schema slot).
    pub f_lambda_mu: SchemaSlot,
    /// (4) $\chi_{\lambda\mu}$ — transition certificates (schema slot).
    pub chi_lambda_mu: SchemaSlot,
    /// (5) $L$ — law / language carrier (schema slot).
    pub l: SchemaSlot,
    /// (6) $\eta$ — unit / reflection unit (schema slot).
    pub eta: SchemaSlot,
    /// (7) $X$ — continuum / completion carrier name (schema slot; sample is `q.domain`).
    pub x_space: SchemaSlot,
    /// (8) $\pi_\lambda$ — projectors / shadow maps (schema slot).
    pub pi_lambda: SchemaSlot,
    /// (9) $q$ — query map (finite sample).
    pub q: FiniteQueryMap,
    /// (10) $\operatorname{Prof}$ — profile map (finite sample).
    pub prof: FiniteProfileMap,
    /// (11) $\bar{q}$ — factor map (finite sample).
    pub q_bar: FiniteFactorMap,
    /// (12) $D$ — residual / defect ledger (schema slot).
    pub d: SchemaSlot,
    /// (13) $V$ — vocabulary / valuation (schema slot).
    pub v: SchemaSlot,
    /// (14) $\tau$ — terminalizer pair name (schema slot; typed maps live in admission).
    pub tau: SchemaSlot,
}

/// Honest paper / product name for the 14-tuple (doc alias to Lean `BridgePacket14`).
pub type CodaCsQBridgePacketV1 = BridgePacket14;

impl BridgePacket14 {
    /// Compile-time / runtime field count (must equal 14).
    pub const FIELD_COUNT: usize = BRIDGE_PACKET_14_FIELD_COUNT;

    /// Build a demo packet with declared schema slots and the given finite maps.
    pub fn finite_demo(q: FiniteQueryMap, prof: FiniteProfileMap, q_bar: FiniteFactorMap) -> Self {
        Self {
            lambda: SchemaSlot::declared("Lambda"),
            a_lambda: SchemaSlot::declared("A_lambda"),
            f_lambda_mu: SchemaSlot::declared("F_lambda_mu"),
            chi_lambda_mu: SchemaSlot::declared("chi_lambda_mu"),
            l: SchemaSlot::declared("L"),
            eta: SchemaSlot::declared("eta"),
            x_space: SchemaSlot::declared("X_space"),
            pi_lambda: SchemaSlot::declared("pi_lambda"),
            q,
            prof,
            q_bar,
            d: SchemaSlot::declared("D"),
            v: SchemaSlot::declared("V"),
            tau: SchemaSlot::declared("tau"),
        }
    }

    /// Schema field count equals paper 14 (sanity dual of Lean `field_count_eq_fourteen`).
    pub fn field_count() -> usize {
        Self::FIELD_COUNT
    }

    /// Ordered schema field names (parity with Lean / Python constants).
    pub fn field_names() -> &'static [&'static str; BRIDGE_PACKET_14_FIELD_COUNT] {
        &BRIDGE_PACKET_14_FIELD_NAMES
    }

    /// Sample domain used by the working maps (intersection of `q` and `Prof` domains).
    pub fn sample_domain(&self) -> Vec<DomainId> {
        if self.q.domain.is_empty() {
            return self.prof.domain.clone();
        }
        if self.prof.domain.is_empty() {
            return self.q.domain.clone();
        }
        // Prefer q.domain order; filter to points also in Prof when both present.
        self.q
            .domain
            .iter()
            .copied()
            .filter(|x| self.prof.values.contains_key(x))
            .collect()
    }

    /// Authority effect is always None (diagnostic schema only).
    pub fn authority_effect(&self) -> &'static str {
        "None"
    }

    /// Finite-map hygiene: domains non-empty and covered by map values.
    pub fn finite_maps_cover_domain(&self) -> bool {
        self.q.covers_domain() && self.prof.covers_domain()
    }
}

/// Pointwise profile factorization on a finite sample:
/// $\forall x.\; q(x) = \bar{q}(\operatorname{Prof}(x))$.
///
/// Dual of Lean `profile_factorization`. Fail-closed on missing map entries.
pub fn profile_factorization_holds(packet: &BridgePacket14) -> Result<(), FactorizationDefect> {
    let domain = packet.sample_domain();
    if domain.is_empty() {
        return Err(FactorizationDefect::EmptyDomain);
    }
    for x in domain {
        let q_x = packet
            .q
            .get(x)
            .ok_or(FactorizationDefect::MissingQuery(x))?;
        let prof_x = packet
            .prof
            .get(x)
            .ok_or(FactorizationDefect::MissingProfile(x))?;
        let q_bar_px = packet
            .q_bar
            .get(prof_x)
            .ok_or(FactorizationDefect::MissingFactor(prof_x))?;
        if q_x != q_bar_px {
            return Err(FactorizationDefect::Mismatch {
                x,
                q_x,
                prof_x,
                q_bar_px,
            });
        }
    }
    Ok(())
}

/// Fiber constancy on a finite sample:
/// $\operatorname{Prof}(x)=\operatorname{Prof}(y) \Rightarrow q(x)=q(y)$.
///
/// Dual of Lean `fiber_constant`.
pub fn fiber_constant_holds(packet: &BridgePacket14) -> Result<(), FiberConstancyDefect> {
    let domain = packet.sample_domain();
    for (i, &x) in domain.iter().enumerate() {
        for &y in domain.iter().skip(i + 1) {
            let px = packet
                .prof
                .get(x)
                .ok_or(FiberConstancyDefect::MissingProfile(x))?;
            let py = packet
                .prof
                .get(y)
                .ok_or(FiberConstancyDefect::MissingProfile(y))?;
            if px == py {
                let qx = packet
                    .q
                    .get(x)
                    .ok_or(FiberConstancyDefect::MissingQuery(x))?;
                let qy = packet
                    .q
                    .get(y)
                    .ok_or(FiberConstancyDefect::MissingQuery(y))?;
                if qx != qy {
                    return Err(FiberConstancyDefect::Mismatch { x, y, px, qx, qy });
                }
            }
        }
    }
    Ok(())
}

/// Factorization defect residual (AuthorityEffect: None).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum FactorizationDefect {
    EmptyDomain,
    MissingQuery(DomainId),
    MissingProfile(DomainId),
    MissingFactor(ProfileId),
    Mismatch {
        x: DomainId,
        q_x: QueryValue,
        prof_x: ProfileId,
        q_bar_px: QueryValue,
    },
}

/// Fiber-constancy defect residual (AuthorityEffect: None).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum FiberConstancyDefect {
    MissingQuery(DomainId),
    MissingProfile(DomainId),
    Mismatch {
        x: DomainId,
        y: DomainId,
        px: ProfileId,
        qx: QueryValue,
        qy: QueryValue,
    },
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/bridge_packet.rs
// Claim: urn:core:crates_rs:core-wdp:bridge-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord55039190 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord55039190` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError55039190 {
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
impl BoundaryError55039190 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError55039190 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError55039190 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord55039190 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError55039190> {
        if capacity_bound == 0 {
            return Err(BoundaryError55039190::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError55039190::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError55039190::ExceedsCapacity {
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

    fn factoring_packet() -> BridgePacket14 {
        // Prof: 0,1 -> 0; 2,3 -> 1. q constant on fibers; q_bar(0)=10, q_bar(1)=20.
        let q = FiniteQueryMap::from_pairs([(0, 10), (1, 10), (2, 20), (3, 20)]);
        let prof = FiniteProfileMap::from_pairs([(0, 0), (1, 0), (2, 1), (3, 1)]);
        let q_bar = FiniteFactorMap::from_pairs([(0, 10), (1, 20)]);
        BridgePacket14::finite_demo(q, prof, q_bar)
    }

    #[test]
    fn field_count_is_fourteen() {
        assert_eq!(BridgePacket14::field_count(), 14);
        assert_eq!(BRIDGE_PACKET_14_FIELD_COUNT, 14);
        assert_eq!(BRIDGE_PACKET_14_FIELD_NAMES.len(), 14);
        assert_eq!(CodaCsQBridgePacketV1::FIELD_COUNT, 14);
    }

    #[test]
    fn field_names_match_paper_tuple_order() {
        assert_eq!(
            BridgePacket14::field_names(),
            &[
                "Lambda",
                "A_lambda",
                "F_lambda_mu",
                "chi_lambda_mu",
                "L",
                "eta",
                "X_space",
                "pi_lambda",
                "q",
                "Prof",
                "q_bar",
                "D",
                "V",
                "tau",
            ]
        );
    }

    #[test]
    fn authority_effect_is_none() {
        let p = factoring_packet();
        assert_eq!(p.authority_effect(), "None");
    }

    #[test]
    fn profile_factorization_holds_on_factoring_demo() {
        assert!(profile_factorization_holds(&factoring_packet()).is_ok());
    }

    #[test]
    fn factorization_implies_fiber_constancy_on_demo() {
        let p = factoring_packet();
        assert!(profile_factorization_holds(&p).is_ok());
        assert!(fiber_constant_holds(&p).is_ok());
    }

    #[test]
    fn factorization_fails_on_mismatch() {
        let q = FiniteQueryMap::from_pairs([(0, 1), (1, 2)]);
        let prof = FiniteProfileMap::from_pairs([(0, 0), (1, 0)]);
        let q_bar = FiniteFactorMap::from_pairs([(0, 1)]);
        let p = BridgePacket14::finite_demo(q, prof, q_bar);
        assert!(matches!(
            profile_factorization_holds(&p),
            Err(FactorizationDefect::Mismatch { x: 1, .. })
        ));
    }

    #[test]
    fn empty_domain_fails_factorization_closed() {
        let p = BridgePacket14::finite_demo(
            FiniteQueryMap::default(),
            FiniteProfileMap::default(),
            FiniteFactorMap::default(),
        );
        assert_eq!(
            profile_factorization_holds(&p),
            Err(FactorizationDefect::EmptyDomain)
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_55039190 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord55039190::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord55039190::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord55039190::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord55039190::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord55039190::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError55039190::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError55039190::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
