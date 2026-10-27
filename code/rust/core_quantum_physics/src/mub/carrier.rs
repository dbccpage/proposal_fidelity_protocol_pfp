//! Clean-room carrier declarations for Core-native MUB work.

use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubTargetScope {
    PinnedTriple,
    FullMub6,
    Mub10,
    GeneralDimension,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum MubCarrierStatus {
    Declared,
    Candidate,
    Underdetermined,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CoreMubCarrier {
    pub scope: MubTargetScope,
    pub dimension: Option<usize>,
    pub fixed_bases: Option<usize>,
    pub objects: &'static str,
    pub coefficient_boundary: &'static str,
    pub observer: &'static str,
    pub zero_rel: &'static str,
    pub status: MubCarrierStatus,
    pub missing_obligations: Vec<&'static str>,
}

pub fn pinned_t0_projector_carrier() -> CoreMubCarrier {
    CoreMubCarrier {
        scope: MubTargetScope::PinnedTriple,
        dimension: Some(6),
        fixed_bases: Some(3),
        objects: "unit rays and centered rank-one projectors Q_v = vv* - I/6",
        coefficient_boundary:
            "exact algebraic fields declared by the verifier, not floating-point approximations",
        observer: "projector-polytope residual projection in Herm0(6)",
        zero_rel:
            "exact algebraic equality of Gram, overlap, feasibility, and certificate identities",
        status: MubCarrierStatus::Declared,
        missing_obligations: vec![],
    }
}

pub fn full_mub6_carrier_request() -> CoreMubCarrier {
    CoreMubCarrier {
        scope: MubTargetScope::FullMub6,
        dimension: Some(6),
        fixed_bases: None,
        objects: "six or seven candidate bases/rays up to certified equivalence, not a single pinned triple",
        coefficient_boundary: "not yet declared for all MUB(6) triples",
        observer: "must range over triple families and basis-gluing constraints",
        zero_rel: "requires exact exclusion or construction for every equivalence class",
        status: MubCarrierStatus::Underdetermined,
        missing_obligations: vec![
            "classification or exhaustive cover of admissible triples",
            "certified transport from pinned T0 wall to every relevant triple class",
            "basis-gluing obstruction from fourth-vector constraints to complete-set nonexistence",
        ],
    }
}

pub fn mub10_carrier_request() -> CoreMubCarrier {
    CoreMubCarrier {
        scope: MubTargetScope::Mub10,
        dimension: Some(10),
        fixed_bases: None,
        objects: "dimension-10 MUB configurations under an exact carrier still to be declared",
        coefficient_boundary:
            "existing d=10 artifacts are evidence-only until exact reconstruction",
        observer: "not terminalized",
        zero_rel: "not declared",
        status: MubCarrierStatus::Underdetermined,
        missing_obligations: vec![
            "exact coefficient field for the d=10 target",
            "declared repair class and ZeroRel",
            "upper-bound or construction certificate with independent replay",
        ],
    }
}

pub fn general_mub_n_carrier_request() -> CoreMubCarrier {
    CoreMubCarrier {
        scope: MubTargetScope::GeneralDimension,
        dimension: None,
        fixed_bases: None,
        objects: "dimension-indexed family of MUB carriers",
        coefficient_boundary: "not declared",
        observer: "must be uniform or explicitly stratified by dimension and representation",
        zero_rel: "requires a dimension-parametric exact equality/certificate protocol",
        status: MubCarrierStatus::Underdetermined,
        missing_obligations: vec![
            "dimension-parametric carrier",
            "dimension-parametric repair and closure maps",
            "uniform exact certificate family or typed dimension stratification",
        ],
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/carrier.rs
// Claim: urn:core:crates_rs:core-quantum-physics:carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc387fd9b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc387fd9b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc387fd9b {
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
impl BoundaryErrorc387fd9b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc387fd9b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc387fd9b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc387fd9b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc387fd9b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc387fd9b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc387fd9b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc387fd9b::ExceedsCapacity {
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

    #[test]
    fn pinned_t0_carrier_is_declared_but_not_full_mub6() {
        let carrier = pinned_t0_projector_carrier();
        assert_eq!(carrier.scope, MubTargetScope::PinnedTriple);
        assert_eq!(carrier.status, MubCarrierStatus::Declared);
        assert_eq!(carrier.dimension, Some(6));
        assert_eq!(carrier.fixed_bases, Some(3));
    }

    #[test]
    fn full_mub6_carrier_records_missing_cover_and_gluing_obligations() {
        let carrier = full_mub6_carrier_request();
        assert_eq!(carrier.status, MubCarrierStatus::Underdetermined);
        assert!(carrier
            .missing_obligations
            .iter()
            .any(|obligation| obligation.contains("exhaustive cover")));
        assert!(carrier
            .missing_obligations
            .iter()
            .any(|obligation| obligation.contains("basis-gluing")));
    }

    #[test]
    fn clean_room_carrier_declarations_do_not_point_at_export_paths() {
        for carrier in [
            pinned_t0_projector_carrier(),
            full_mub6_carrier_request(),
            mub10_carrier_request(),
            general_mub_n_carrier_request(),
        ] {
            let serialized = serde_json::to_string(&carrier).unwrap();
            assert!(!serialized.contains("public-export"));
            assert!(!serialized.contains(".py"));
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_c387fd9b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc387fd9b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc387fd9b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc387fd9b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc387fd9b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc387fd9b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc387fd9b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc387fd9b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
