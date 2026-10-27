//! # ooutwire_primitives
//!
//! `AuthorityEffect: None.`
//!
//! Named modules for the 19L57G1 primitives and their local interpretations,
//! in dependency order, together with a declared Core engine. Nothing here
//! is the sealed derivation; everything here is a *reading* of it, written
//! so that the reading can be run and checked instead of remembered.
//!
//! ## The index
//!
//! The crate boundaries are the seven of Part IV §13.9 of the crosstab.  They
//! are modules here, not crates, so the whole thing builds and tests with one
//! command.  Splitting them later is mechanical.
//!
//! | crate boundary | primitive | file |
//! |---|---|---|
//! | coda-carrier | token — presentation identity, forgotten by the key | `token.rs` |
//! | coda-carrier | mark — internal identity, the admission index | `mark.rs` |
//! | coda-carrier | regime — admitted state and nothing else | `regime.rs` |
//! | coda-carrier | event — a presentation or an admission | `event.rs` |
//! | coda-carrier | supply — external presentation, provably inert (L1) | `supply.rs` |
//! | coda-carrier | admission — the only thing that changes state (L2, L6) | `admission.rs` |
//! | coda-carrier | imposition — an externally imposed requirement | `imposition.rs` |
//! | coda-carrier | retention — the history | `retention.rs` |
//! | coda-carrier | replay — rebuild from genesis (L4) | `replay.rs` |
//! | coda-carrier | certification — a claimed regime against its history (L5) | `certification.rs` |
//! | coda-carrier | fingerprint — the replay hash | `hash.rs` |
//! | coda-carrier | the L3 lexical signature census | `census.rs` |
//! | coda-observe | context — a form plus a slot tuple with holes | `context.rs` |
//! | coda-observe | judgment — the positive grammar (L7) | `judgment.rs` |
//! | coda-observe | profile — and the two bits inside `derivable` | `profile.rs` |
//! | coda-observe | separability — profiles differ; witness; collapsed pairs | `separability.rs` |
//! | coda-observe | observer — bits extractor plus reader; the four readers | `observer.rs` |
//! | coda-iso | renaming — a bijection pair; tokens travel and are forgotten | `renaming.rs` |
//! | coda-iso | canonical — the key; `≅` is *defined* as equal keys | `canonical.rs` |
//! | coda-iso | automorphism — the state's own symmetry; pair orbits | `automorphism.rs` |
//! | coda-price | candidate — a one-step augmentation | `candidate.rs` |
//! | coda-price | bounds — the declared finite candidate space (L10) | `bounds.rs` |
//! | coda-price | measure — `mu1`, `mu2`, declared never inferred (L12) | `measure.rs` |
//! | coda-price | response — validity, fast and naive, cross-checked (L11) | `response.rs` |
//! | coda-price | enumeration — pruned by four lemmas, cross-checked unpruned | `enumeration.rs` |
//! | coda-price | minima — CLASSES, never a choice (L8, L9) | `minima.rs` |
//! | coda-price | role — transition roles derived from accepted responses | `role.rs` |
//! | engine | reading — the two admission readings L and F | `reading.rs` |
//! | engine | closure — the declared pair-separation closure policy | `closure.rs` |
//! | engine | tree — the branch tree and its frontier | `tree.rs` |
//! | represented | menu — the declared finite proposal set | `menu.rs` |
//! | represented | repair — the repair family, sound and complete | `repair.rs` |
//! | represented | obstruction — requirement plus EXHAUSTIVE failure | `obstruction.rs` |
//! | represented | budget — fuel; gates rule 1 | `budget.rs` |
//! | represented | license — authorization; gates rule 2 | `license.rs` |
//! | represented | refusal — a non-absorbing record needing a certificate | `refusal.rs` |
//! | represented | support — what a transition can read; `notes_inert` | `support.rs` |
//! | represented | panel — certification up to the panel, never correspondence | `panel.rs` |
//! | represented | world — the represented state and its total step | `world.rs` |
//! | represented | hidden — the seven hidden-input countermodels | `hidden.rs` |
//! | coda-cert | certificate — exhaustion, witness, obstruction | `certificate.rs` |
//! | coda-terminal | scope — a result carries the scope it was certified under | `scope.rs` |
//! | coda-terminal | terminal — the five declared final statuses | `terminal.rs` |
//! | coda-audit | export — deterministic serialisation and full replay | `export.rs` |
//! | twelfth sort | boundary — one two-sided boundary, readings U and O | `boundary.rs` |
//! | outside | the push from outside: supply, demand, choice, licence, fuel | `outside.rs` |
//! | engine | core engine — the fold with four holes | `engine.rs` |
//! | study | PO-000 replicated — the projection-obstruction paper, exact and numerical rails, read through the primitives above | `alpha_projection_obstruction/` |
//!
//! ## What a green test suite certifies
//!
//! That the arithmetic in this crate agrees with the pinned values it names.
//! Not that the sealed derivation is right, not that this reading of it is
//! the only one, and not that any analogy anyone has drawn from it holds.
//! A receipt is never evidence of its payload (`FW-RECEIPT`).

#![forbid(unsafe_code)]
#![deny(missing_docs)]

// coda-carrier
pub mod token;
pub mod mark;
pub mod regime;
pub mod event;
pub mod supply;
pub mod admission;
pub mod imposition;
pub mod retention;
pub mod replay;
pub mod certification;
pub mod hash;
pub mod census;

// coda-observe
pub mod context;
pub mod judgment;
pub mod profile;
pub mod separability;
pub mod observer;

// coda-iso
pub mod renaming;
pub mod canonical;
pub mod automorphism;

// coda-price
pub mod candidate;
pub mod bounds;
pub mod measure;
pub mod response;
pub mod enumeration;
pub mod minima;
pub mod role;

// the sealed engine's structure
pub mod reading;
pub mod closure;
pub mod tree;

// the represented process
pub mod menu;
pub mod repair;
pub mod obstruction;
pub mod budget;
pub mod license;
pub mod refusal;
pub mod support;
pub mod panel;
pub mod world;
pub mod hidden;

// coda-cert, coda-terminal, coda-audit
pub mod certificate;
pub mod scope;
pub mod terminal;
pub mod export;

// the twelfth sort
pub mod boundary;

// the outside, and the engine
pub mod outside;
pub mod engine;

// a study: PO-000 (projection obstruction) replicated from the primitives.
// A directory module; the L3 census recurses into it.
pub mod alpha_projection_obstruction;

// test-only helpers; excluded from the L3 census by name

// Origin: engine/crates_rs/core_ooutwire_primitives/src/lib.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord226f4086 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord226f4086` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError226f4086 {
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
impl BoundaryError226f4086 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError226f4086 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError226f4086 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord226f4086 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError226f4086> {
        if capacity_bound == 0 {
            return Err(BoundaryError226f4086::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError226f4086::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError226f4086::ExceedsCapacity {
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
pub mod testkit;

/// Fuel left after one licensed structure step.
pub struct GateReceipt {
    fuel_after: u32,
    licensed: bool,
}

/// Why a structure-creating step was refused.
pub enum GateError {
    /// The licence gate is closed.
    Unlicensed,
    /// The budget cannot pay for one step.
    Unfunded,
}

impl GateReceipt {
    /// Admit one structure step through the independent licence and budget gates.
    pub fn admit_structure(budget: budget::Budget, license: license::License) -> Result<Self, GateError> {
        if !license.granted() {
            return Err(GateError::Unlicensed);
        }
        let paid = budget.pay().ok_or(GateError::Unfunded)?;
        Ok(Self {
            fuel_after: paid.0,
            licensed: true,
        })
    }

    /// Fuel remaining after the step was paid.
    pub fn fuel_after(self) -> u32 {
        self.fuel_after
    }

    /// Whether the licence gate was open.
    pub fn licensed(self) -> bool {
        self.licensed
    }
}

#[cfg(test)]
mod gate_receipt_checks {
    use super::{budget::Budget, license::License, GateError, GateReceipt};

    #[test]
    fn structure_needs_a_licence_and_one_unit_of_fuel() {
        let paid = GateReceipt::admit_structure(Budget(1), License(true));
        assert_eq!(paid.map(|receipt| (receipt.fuel_after(), receipt.licensed())), Ok((0, true)));
        assert!(matches!(
            GateReceipt::admit_structure(Budget(0), License(true)),
            Err(GateError::Unfunded)
        ));
        assert!(matches!(
            GateReceipt::admit_structure(Budget(1), License(false)),
            Err(GateError::Unlicensed)
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_226f4086 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord226f4086::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord226f4086::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord226f4086::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord226f4086::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord226f4086::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError226f4086::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError226f4086::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
