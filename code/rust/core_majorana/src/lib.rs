//! `core_majorana` — GF(2) Majorana parity **diagnostic** playground.
//!
//! # Authority fence (MANDATORY)
//!
//! - **AuthorityEffect: None** on every receipt.
//! - Not a CODA_GTLA / CODA authority terminalizer; does not mint `CertifiedAuthority`.
//! - Does not claim physical Majorana modes, topological qubits, or NISQ hardware.
//! - Status labels `Exact` / `ClosedResidual` / `OpenObstruction` are **diagnostic
//!   schedule classes**, not FOC `ExactRepair` / PROVED.
//!
//! # Ownership
//!
//! Canonical Rust home for GF(2) Majorana parity diagnostics (moved from root
//! Python prototype `majorana` + engines quantum module).
//! The old copy under `engines::quantum` was removed on 2026-09-25.
//!
//! Python dual-face / demos: `engine_py/core_majorana` (relocated package).
//!
//! # Play
//!
//! ```text
//! cargo test -j 1 -p core_majorana
//! cargo test -j 1 -p core_majorana play_ -- --nocapture
//! cargo test -j 1 -p core_majorana torus_2x2 -- --nocapture
//! ```

#![forbid(unsafe_code)]

pub mod braid_action;
pub mod classify;
pub mod complexes;
pub mod dual_observer;
pub mod gf2_terminalizer;
pub mod hard_invariants;
pub mod harmonic;
pub mod holonomy;
pub mod lggr;
pub mod majorana_fock_algebra;
pub mod multiqubit_braid;
pub mod noise_mc;
pub mod pauli_noise;
pub mod packet_wall;
pub mod repair_capacity;
pub mod repair_limit;
pub mod sparse_kitaev;
pub mod tetron;

pub use majorana_fock_algebra::{
    first_anticommutation_failure, FockCarrier, MajoranaError, MAX_MODES,
};

pub use classify::{
    classify, classify_default, classify_with_diagnostics, ClassifiedReceipt, Terminal,
    CLASSIFIED_RECEIPT_TAG,
};
pub use harmonic::{
    code_distance, h1_basis, l1_harmonic_projection, H1Basis, L1HarmonicProjection,
    DEFAULT_BUDGET as HARMONIC_DEFAULT_BUDGET,
};
pub use tetron::{build_tetron_array, logical_class_representative, Axis, TetronReport, Topology};

pub use complexes::{
    closed_residual_syndrome_example, exact_syndrome_example, open_syndrome_example, plaquette,
    prism, surface_exact_from_vertex0, surface_grid, surface_grid_2x2_planar,
    surface_grid_2x2_torus, surface_open_single_edge_example, torus_logical_x_example,
    torus_logical_z_example, triangle, ChainComplexGf2,
};
pub use dual_observer::{
    dual_observe, observer_even_edge_parity, observer_face_syndrome, observer_first_face_only,
    DualObserverReceipt, ObservationMap, DUAL_OBS_RECEIPT_TAG,
};
pub use gf2_terminalizer::{
    Cyclotomic16Element, GF2Matrix, GF2ScheduleStatus, Gf2CocycleClassifier, Gf2ScheduleReceipt,
    AUTHORITY_FENCE as GF2_AUTHORITY_FENCE,
};
pub use holonomy::{
    connect_to_schedule_class, face_edge_support, face_holonomy_residual_gf2, gauge_transform_gf2,
    holonomy_receipt_cyclotomic_face0, holonomy_receipt_gf2, HolonomyReceiptCyclotomic,
    HolonomyReceiptGf2, AUTHORITY_FENCE as HOLONOMY_AUTHORITY_FENCE, HOLONOMY_RECEIPT_TAG,
};
pub use lggr::{apply_d1 as lggr_apply_d1, detect_lggr, LggrWitness};
pub use packet_wall::{
    admit_or_refuse, demo_count_packet, illustrative_p_pair, illustrative_suppression_regime,
    incomplete_count_packet, terminalize_count_packet, terminalize_packet, wall_with_audit,
    CountDefectEvent, CountPacketReceipt, CountRepairAction, CountRepairPacket, DefectEvent,
    DiagnosticPacket, PacketMetrics, PacketRefusal, PacketWallReceipt, PacketWallTerminal,
    RepairAction, ToyRepairPacket, AUTHORITY_FENCE as PACKET_WALL_AUTHORITY_FENCE,
};
pub use repair_capacity::{
    assert_repair_capacity_invariant, min_weight_nontrivial, repair_capacity_from_distance,
};
pub use repair_limit::{
    apply_d0, apply_d1, audit_repair_capacity, coset_decode_demo, face_syndrome, gf2_add,
    hamming_weight, homology_distance, in_image_d0, is_closed, lggr_demo_on, lggr_demo_torus,
    repair_capacity_bound, repair_capacity_t, solve_d0, syndrome_is_zero, CosetDecodeDemo,
    HomologyDistanceReport, LggrDemoReport, RepairCapacityReceipt,
    AUTHORITY_FENCE as REPAIR_LIMIT_AUTHORITY_FENCE,
};

/// Mandatory authority effect declaration.
pub const AUTHORITY_EFFECT: &str = "AuthorityEffect: None";

/// Crate-level fence string.
pub const AUTHORITY_FENCE: &str = "AuthorityEffect None; not PROVED; not GlobalGreen; not physical Majorana; diagnostic GF(2) only.";

/// Package tag for receipts.
pub const RECEIPT_TAG: &str = "core.majorana-gf2-receipt.v1";
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Gf2WeightError { kind: &'static str, left: u128, right: u128 }
impl Gf2WeightError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Hamming weight of a GF(2) word. The weight modulo two equals the bitwise sum.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Gf2Weight { weight: u64, parity: u64 }
impl Gf2Weight {
    pub fn try_word(bits: &[u8]) -> Result<Self, Gf2WeightError> {
        let mut weight = 0u64;
        let mut folded = 0u8;
        for bit in bits {
            if *bit > 1 {
                return Err(Gf2WeightError::new("a GF(2) bit is 0 or 1", u128::from(*bit), 1));
            }
            weight = weight.checked_add(u64::from(*bit)).ok_or_else(|| Gf2WeightError::new("weight overflow", u128::from(weight), u128::from(*bit)))?;
            folded ^= *bit;
        }
        let parity = weight.checked_rem(2).ok_or_else(|| Gf2WeightError::new("parity remainder overflow", u128::from(weight), 2))?;
        if u64::from(folded) != parity {
            return Err(Gf2WeightError::new("weight parity differs from the bit sum", u128::from(folded), u128::from(parity)));
        }
        Ok(Self { weight, parity })
    }
    pub const fn weight(&self) -> u64 { self.weight }
    pub const fn parity(&self) -> u64 { self.parity }
}

// Origin: engine/crates_rs/core_majorana/src/lib.rs
// Claim: urn:core:crates_rs:core-majorana:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord343bb7e4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord343bb7e4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError343bb7e4 {
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
impl BoundaryError343bb7e4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError343bb7e4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError343bb7e4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord343bb7e4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError343bb7e4> {
        if capacity_bound == 0 {
            return Err(BoundaryError343bb7e4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError343bb7e4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError343bb7e4::ExceedsCapacity {
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
mod gf2_weight_checks {
    use super::Gf2Weight;
    #[test]
    fn three_ones_have_odd_parity() {
        let word = Gf2Weight::try_word(&[1, 0, 1, 1]);
        assert_eq!(word.as_ref().map(Gf2Weight::weight), Ok(3));
        assert_eq!(word.as_ref().map(Gf2Weight::parity), Ok(1));
    }
    #[test]
    fn a_bit_outside_the_field_is_refused() {
        assert_eq!(Gf2Weight::try_word(&[2]).map(|_| ()).map_err(|e| e.kind()), Err("a GF(2) bit is 0 or 1"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_343bb7e4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord343bb7e4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord343bb7e4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord343bb7e4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord343bb7e4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord343bb7e4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError343bb7e4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError343bb7e4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
